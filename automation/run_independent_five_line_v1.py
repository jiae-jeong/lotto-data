#!/usr/bin/env python3
"""Run only the newly registered E025-E029 studies, preserving every attempt."""
from __future__ import annotations

import argparse
import json
import os
import tempfile
import traceback
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import daily_research_v2 as daily
import research_engine_v2 as engine

TASK_IDS = [
    "E025_INDEPENDENT_SIGNAL_DISCOVERY_v1",
    "E026_INDEPENDENT_MODEL_WALKFORWARD_v1",
    "E027_FIVE_LINE_CANDIDATE_BANK_v1",
    "E028_FIVE_LINE_PORTFOLIO_SELECTOR_v2",
    "E029_FIVE_LINE_PROMOTION_GATE_v2",
]


def run(root: Path, queue_path: Path, run_date: str | None = None) -> dict:
    root = root.resolve()
    date = run_date or datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()
    datetime.strptime(date, "%Y-%m-%d")
    queue = json.loads(queue_path.read_text(encoding="utf-8"))
    all_tasks = {task["id"]: task for task in queue["tasks"]}
    if not all(task_id in all_tasks for task_id in TASK_IDS):
        raise ValueError("E025-E029 are not all registered in research_queue_v2.json")
    tasks = [all_tasks[task_id] for task_id in TASK_IDS]
    if [task["id"] for task in tasks] != TASK_IDS:
        raise ValueError("E025-E029 dispatch order mismatch")
    data = root / engine.DATA
    cache = root / engine.CACHE
    if engine.digest(data) != engine.DATA_SHA:
        raise ValueError("Canonical 1..1245 snapshot SHA mismatch")
    draws, actual, _ = __import__("independent_signal_five_line_v1")._load_inputs(root)
    if len(draws) != 1245 or len(actual) != 1245:
        raise ValueError("Data validation did not produce 1..1245")

    date_root = root / "analysis" / date
    date_root.mkdir(parents=True, exist_ok=True)
    attempts_root = date_root / ".attempts"
    attempts_root.mkdir(parents=True, exist_ok=True)
    protected = engine.protect(root)
    results = {"date": date, "status": "RUNNING", "base_study_ids": TASK_IDS,
        "canonical_source_commit": "69426c16711d7d6c43f82da601249fb108f5f2b6",
        "canonical_snapshot_sha256": engine.digest(data), "b_cache_sha256": engine.raw_digest(cache),
        "draw_rows": len(draws), "first_round": 1, "latest_round": 1245,
        "run_id": datetime.now(ZoneInfo("Asia/Seoul")).strftime("%H%M%S_%f"),
        "studies": [], "failures": [], "old_research_rerun": False}
    for task in tasks:
        destination = date_root / task["id"]
        if destination.exists():
            try:
                record = daily.validate_completion(destination, task["id"])
                results["studies"].append({"task_id": task["id"], "status": "ALREADY_VALIDATED",
                    "executed_cases": record["executed_cases"], "path": str(destination.relative_to(root))})
                continue
            except Exception as error:
                raise FileExistsError(f"Existing study is protected and failed validation: {destination}: {error}")
        attempt = Path(tempfile.mkdtemp(prefix=task["id"] + "-", dir=attempts_root))
        stage = attempt / "study"
        stage_name = "engine_execution"
        try:
            engine.run(root, stage, task)
            stage_name = "completion_validation"
            record = daily.validate_completion(stage, task["id"])
            if destination.exists(): raise FileExistsError("Refuse to replace an existing study directory")
            stage_name = "publication_promotion"
            os.rename(stage, destination)
            attempt.rmdir()
            results["studies"].append({"task_id": task["id"], "status": "COMPLETE",
                "executed_cases": record["executed_cases"], "path": str(destination.relative_to(root))})
        except Exception as error:
            engine.check_protection(root, protected)
            failure = {"task_id": task["id"], "status": "FAILED", "stage": stage_name,
                "error_type": type(error).__name__, "reason": str(error), "traceback": traceback.format_exc(),
                "protected_files_unchanged": True, "recovery_attempted": "Preserved exact attempt and continued to the next registered study",
                "attempt_path": str(attempt.relative_to(root))}
            (attempt / "FAILURE.json").write_text(json.dumps(failure, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            results["failures"].append(failure)
    engine.check_protection(root, protected)
    all_valid = len(results["studies"]) == 5 and not results["failures"]
    all_fresh = all(item["status"] == "COMPLETE" for item in results["studies"])
    results["status"] = ("ALL_FIVE_EXECUTED" if all_valid and all_fresh else
                          "ALL_FIVE_VALIDATED" if all_valid else "PARTIAL_OR_FAILED")
    summary_path = date_root / f"E025_E029_EXECUTION_SUMMARY_{results['run_id']}.json"
    if summary_path.exists(): raise FileExistsError("Refuse to overwrite E025-E029 execution summary")
    manifest_path = date_root / f"E025_E029_SHA256_MANIFEST_{results['run_id']}.csv"
    results["sha256_manifest"] = str(manifest_path.relative_to(root))
    summary_path.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    files = []
    for study_id in TASK_IDS:
        study_dir = date_root / study_id
        if study_dir.exists(): files.extend(p for p in study_dir.rglob("*") if p.is_file())
    if attempts_root.exists(): files.extend(p for p in attempts_root.rglob("*") if p.is_file())
    files.append(summary_path)
    manifest_rows = [{"path": p.relative_to(date_root).as_posix(),
        "bytes": engine.portable_size(p), "sha256": engine.digest(p)} for p in sorted(set(files))]
    engine.csvfile(manifest_path, manifest_rows)
    for row in engine.readcsv(manifest_path):
        p = date_root / row["path"]
        if engine.portable_size(p) != int(row["bytes"]) or engine.digest(p) != row["sha256"]:
            raise ValueError("Execution bundle manifest read-back failed: " + row["path"])
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--queue", type=Path, default=Path(__file__).with_name("research_queue_v2.json"))
    parser.add_argument("--run-date")
    args = parser.parse_args()
    result = run(args.repository, args.queue, args.run_date)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] in {"ALL_FIVE_EXECUTED", "ALL_FIVE_VALIDATED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
