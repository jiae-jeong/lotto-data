#!/usr/bin/env python3
"""Prepare the generic daily-research queue without treating failed attempts as completions."""
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

import daily_research_v2 as daily
import research_engine_v2 as engine

TERMINAL_DEDICATED_STATUSES = {"COMPLETE", "BLOCKED"}
EXPLICIT_BAD_VERIFICATION_STATUSES = {"FAIL", "FAILED", "ERROR", "INVALID", "CORRUPT"}


def _safe_manifest_path(output: Path, value: str) -> Path:
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"Unsafe evidence manifest path: {value}")
    path = output / relative
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"Missing or unsafe evidence file: {value}")
    return path


def _verify_manifest(output: Path) -> None:
    manifest_path = output / "SHA256_MANIFEST.csv"
    if not manifest_path.is_file():
        raise ValueError(f"Missing SHA256 manifest for terminal study: {output}")
    rows = engine.readcsv(manifest_path)
    if not rows:
        raise ValueError(f"Empty SHA256 manifest for terminal study: {output}")
    name_field = "path" if "path" in rows[0] else "file" if "file" in rows[0] else None
    if not name_field or "sha256" not in rows[0]:
        raise ValueError(f"Unsupported SHA256 manifest schema: {manifest_path}")
    seen = set()
    for row in rows:
        name = row[name_field]
        if name in seen:
            raise ValueError(f"Duplicate manifest entry: {name}")
        seen.add(name)
        path = _safe_manifest_path(output, name)
        expected_hash = row["sha256"]
        expected_bytes = row.get("bytes")
        raw_ok = engine.raw_digest(path) == expected_hash
        portable_ok = engine.digest(path) == expected_hash
        if expected_bytes not in (None, ""):
            size = int(expected_bytes)
            raw_ok = raw_ok and engine.raw_size(path) == size
            portable_ok = portable_ok and engine.portable_size(path) == size
        if not (raw_ok or portable_ok):
            raise ValueError(f"Evidence hash mismatch: {path}")
    for required in ("COMPLETION.json", "VERIFICATION.json"):
        if required not in seen:
            raise ValueError(f"Terminal study manifest does not cover {required}: {output}")


def _validate_dedicated_completion(output: Path, task_id: str, record: dict) -> dict:
    if record.get("study_id") != task_id or record.get("status") not in TERMINAL_DEDICATED_STATUSES:
        raise ValueError(f"Invalid dedicated completion identity/status: {output}")
    verification_path = output / "VERIFICATION.json"
    if not verification_path.is_file():
        raise ValueError(f"Missing dedicated verification: {output}")
    verification = json.loads(verification_path.read_text(encoding="utf-8"))

    # Dedicated workflows use study-specific terminal vocabulary (PASS, CALIBRATED, or no generic
    # status field at all). Reject only explicit failure states; completion identity + immutable
    # manifest + leakage/future guards remain mandatory.
    verification_status = verification.get("status")
    if verification_status is not None and str(verification_status).upper() in EXPLICIT_BAD_VERIFICATION_STATUSES:
        raise ValueError(f"Dedicated verification explicitly failed: {output}")
    if verification.get("study_id") not in (None, task_id):
        raise ValueError(f"Dedicated verification identity mismatch: {output}")
    for field in ("leakage_failures", "future_predictions"):
        value = verification.get(field)
        if value is not None and int(value) != 0:
            raise ValueError(f"Dedicated {field} violation: {output}")
    _verify_manifest(output)
    return record


def _validate_registered_execution(repository: Path, task: dict, current_cutoff: int) -> str:
    """Verify queue-recorded code-mode evidence before treating an EXECUTED task as terminal.

    Some code-mode studies preserve a compact result JSON + report + SHA256 manifest rather
    than the generic COMPLETION/VERIFICATION pair. Their queue status must never cause a
    blind rerun: validate the immutable evidence and cutoff, or fail closed.
    """
    task_id = task["id"]
    spec = task.get("spec") if isinstance(task.get("spec"), dict) else {}
    execution = task.get("execution_result")
    if not isinstance(execution, dict):
        raise ValueError(f"Executed task has no registered execution_result: {task_id}")

    raw_cutoff = execution.get("data_cutoff", task.get("data_cutoff", spec.get("data_cutoff")))
    try:
        recorded_cutoff = int(raw_cutoff)
    except (TypeError, ValueError):
        raise ValueError(f"Executed task has no valid registered data cutoff: {task_id}")
    if recorded_cutoff != current_cutoff:
        raise ValueError(
            f"Executed task cutoff mismatch for {task_id}: {recorded_cutoff} != {current_cutoff}"
        )

    result_value = task.get("result_path") or execution.get("result_path")
    if not isinstance(result_value, str) or not result_value:
        raise ValueError(f"Executed task has no registered result_path: {task_id}")
    relative = Path(result_value)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"Unsafe registered result path for {task_id}: {result_value}")
    candidate = repository / relative
    if candidate.is_symlink() or not candidate.is_dir():
        raise ValueError(f"Missing or unsafe registered result directory for {task_id}: {result_value}")
    output = candidate.resolve()
    analysis_root = (repository / "analysis").resolve()
    if not output.is_relative_to(analysis_root):
        raise ValueError(f"Registered result path is outside analysis/: {task_id}")

    if execution.get("verification_status") != "PASS" or execution.get("manifest_status") != "PASS":
        raise ValueError(f"Registered execution is not verified: {task_id}")
    manifest_path = output / "SHA256_MANIFEST.csv"
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise ValueError(f"Missing or unsafe registered manifest for {task_id}")
    rows = engine.readcsv(manifest_path)
    if not rows:
        raise ValueError(f"Empty registered manifest for {task_id}")
    name_field = "path" if "path" in rows[0] else "file" if "file" in rows[0] else None
    if not name_field or "sha256" not in rows[0]:
        raise ValueError(f"Unsupported registered manifest schema for {task_id}")

    seen = set()
    for row in rows:
        name = row[name_field]
        if name in seen:
            raise ValueError(f"Duplicate registered manifest entry for {task_id}: {name}")
        seen.add(name)
        path = _safe_manifest_path(output, name)
        expected_hash = row["sha256"]
        expected_bytes = row.get("bytes")
        raw_ok = engine.raw_digest(path) == expected_hash
        portable_ok = engine.digest(path) == expected_hash
        if expected_bytes not in (None, ""):
            size = int(expected_bytes)
            raw_ok = raw_ok and engine.raw_size(path) == size
            portable_ok = portable_ok and engine.portable_size(path) == size
        if not (raw_ok or portable_ok):
            raise ValueError(f"Evidence hash mismatch for registered execution: {path}")

    if "REPORT.md" not in seen:
        raise ValueError(f"Registered execution report is not covered by manifest: {task_id}")
    if int(execution.get("manifest_entries", -1)) != len(rows):
        raise ValueError(f"Registered manifest entry count mismatch for {task_id}")

    result_record = None
    for name in sorted(seen):
        if not name.lower().endswith(".json"):
            continue
        payload = json.loads(_safe_manifest_path(output, name).read_text(encoding="utf-8"))
        if payload.get("study_id") == task_id:
            result_record = payload
            break
    if result_record is None:
        raise ValueError(f"Registered result JSON is missing or has the wrong study_id: {task_id}")

    canonical = result_record.get("canonical_data") or {}
    verification = result_record.get("verification") or {}
    completion = result_record.get("completion") or {}
    rounds = canonical.get("rounds")
    if (
        int(canonical.get("rows", -1)) != current_cutoff
        or rounds != [1, current_cutoff]
    ):
        raise ValueError(f"Registered result canonical cutoff mismatch for {task_id}")
    expected_data_sha = (
        execution.get("data_sha256")
        or execution.get("canonical_data_sha256")
        or task.get("data_sha256")
        or spec.get("data_sha256")
    )
    if not expected_data_sha or canonical.get("sha256") != expected_data_sha:
        raise ValueError(f"Registered result data hash mismatch for {task_id}")
    if verification.get("status") != "PASS":
        raise ValueError(f"Registered result verification failed for {task_id}")
    for field in ("training_cutoff_violations", "missing_rows", "duplicate_rows"):
        if int(verification.get(field, -1)) != 0:
            raise ValueError(f"Registered result {field} is not zero for {task_id}")
    if verification.get("future_outcomes_used") is not False:
        raise ValueError(f"Registered result does not prove future-outcome exclusion: {task_id}")
    if verification.get("random_baseline_executed") is not True:
        raise ValueError(f"Registered result has no executed random baseline: {task_id}")
    if (
        verification.get("manifest_status") != "PASS"
        or int(verification.get("manifest_entries", -1)) != len(rows)
    ):
        raise ValueError(f"Registered result manifest metadata mismatch for {task_id}")

    target_count = int(result_record.get("target_count", 0))
    targets = result_record.get("evaluation_targets")
    if not isinstance(targets, list) or len(targets) != 2:
        raise ValueError(f"Registered result target range is missing for {task_id}")
    start, end = map(int, targets)
    if target_count < 1 or end - start + 1 != target_count:
        raise ValueError(f"Registered result target count mismatch for {task_id}")
    if int(execution.get("target_count", -1)) != target_count:
        raise ValueError(f"Queue/result target count mismatch for {task_id}")
    predictions = result_record.get("predictions")
    if not isinstance(predictions, list) or len(predictions) != target_count:
        raise ValueError(f"Registered result predictions are incomplete for {task_id}")
    observed_targets = []
    for prediction in predictions:
        target = int(prediction["target"])
        training_through = int(prediction["training_through"])
        window_end = int(prediction.get("window_end", training_through))
        if training_through != target - 1 or window_end > training_through:
            raise ValueError(f"Future-data leakage in registered result for {task_id}, target {target}")
        observed_targets.append(target)
    if observed_targets != list(range(start, end + 1)):
        raise ValueError(f"Registered result target sequence is incomplete for {task_id}")

    if not str(completion.get("status", "")).startswith("COMPLETE"):
        raise ValueError(f"Registered result is not terminal for {task_id}")
    if completion.get("purchase_recommendation_generated") is not False:
        raise ValueError(f"Registered daily research generated a purchase recommendation: {task_id}")
    if completion.get("strict_pass_ready") is not False:
        raise ValueError(f"Registered diagnostic unexpectedly claims strict readiness: {task_id}")
    if execution.get("purchase_recommendation_generated", False) is not False:
        raise ValueError(f"Queue metadata claims a purchase recommendation for {task_id}")
    if execution.get("strict_pass_ready", False) is not False:
        raise ValueError(f"Queue metadata claims strict readiness for {task_id}")

    source = result_record.get("source") or {}
    if execution.get("source_git_blob_sha") and source.get("git_blob_sha") != execution["source_git_blob_sha"]:
        raise ValueError(f"Registered source blob mismatch for {task_id}")
    if execution.get("source_sha256") and source.get("sha256") != execution["source_sha256"]:
        raise ValueError(f"Registered source hash mismatch for {task_id}")
    return str(output)


def verified_completed_tasks(root: Path, archive: Path | None = None) -> dict[str, str]:
    """Return terminal study IDs while preserving strict evidence checks.

    `.attempts` directories are failure evidence by definition and are never completion candidates.
    Generic daily studies keep the original strict completion validator. Dedicated-workflow studies
    use their own terminal schema plus immutable SHA256 evidence and leakage/future guards.
    """
    completed: dict[str, str] = {}
    locations = [Path(root) / "analysis"]
    if archive:
        locations.append(Path(archive))
    for location in locations:
        if not location.exists():
            continue
        for path in location.rglob("COMPLETION.json"):
            try:
                relative_parts = path.relative_to(location).parts
            except ValueError:
                continue
            if ".attempts" in relative_parts:
                continue
            record = json.loads(path.read_text(encoding="utf-8"))
            generic_id = record.get("task_id", "")
            dedicated_id = record.get("study_id", "")
            if re.fullmatch(r"E\d{3}_[A-Za-z0-9_]+", generic_id):
                daily.validate_completion(path.parent, generic_id)
                completed[generic_id] = str(path.parent)
            elif re.fullmatch(r"E\d{3}_[A-Za-z0-9_]+", dedicated_id) and record.get("status") in TERMINAL_DEDICATED_STATUSES:
                _validate_dedicated_completion(path.parent, dedicated_id, record)
                completed[dedicated_id] = str(path.parent)
    return completed


def prepare(repository: Path, queue: Path, filtered_queue: Path, status_file: Path, archive: Path | None = None) -> dict:
    repository = repository.resolve()
    payload = json.loads(queue.read_text(encoding="utf-8"))
    tasks = payload.get("tasks")
    if not isinstance(tasks, list):
        raise ValueError("Research queue must contain a tasks list")

    identifiers = [task.get("id") for task in tasks]
    if any(not isinstance(task_id, str) for task_id in identifiers):
        raise ValueError("Every research task must have a string id")
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("Duplicate research IDs")

    completed = verified_completed_tasks(repository, archive)

    data_path = repository / "lotto_data.csv"
    data_rows = engine.readcsv(data_path)
    rounds = [int(row["round"]) for row in data_rows]
    if not rounds or rounds != list(range(1, len(rounds) + 1)):
        raise ValueError("Canonical lotto_data.csv is missing, duplicated, or non-contiguous")
    current_cutoff = rounds[-1]

    runnable = []
    skipped_completed = []
    skipped_blocked = []
    skipped_dedicated = []
    skipped_superseded = []
    skipped_stale_cutoff = []
    skipped_registered_execution = []
    for task in tasks:
        task_id = task["id"]
        if task_id in completed:
            skipped_completed.append(task_id)
            continue

        spec = task.get("spec") if isinstance(task.get("spec"), dict) else {}
        superseded_by = task.get("superseded_by") or spec.get("superseded_by")
        execution_status = str(spec.get("execution_status", task.get("execution_status", ""))).upper()
        if superseded_by or execution_status.startswith("SUPERSEDED"):
            skipped_superseded.append(task_id)
            continue
        if spec.get("execution_mode") == "dedicated_workflow":
            skipped_dedicated.append(task_id)
            continue
        if spec.get("study_class") == "blocked":
            skipped_blocked.append(task_id)
            continue

        raw_cutoff = spec.get("data_cutoff", task.get("data_cutoff"))
        try:
            task_cutoff = int(raw_cutoff) if raw_cutoff not in (None, "") else None
        except (TypeError, ValueError):
            task_cutoff = None
        if task_cutoff != current_cutoff:
            skipped_stale_cutoff.append({
                "task_id": task_id,
                "registered_cutoff": raw_cutoff,
                "current_cutoff": current_cutoff,
                "reason": "missing_or_stale_registered_data_cutoff",
            })
            continue

        if execution_status.startswith("EXECUTED_"):
            _validate_registered_execution(repository, task, current_cutoff)
            skipped_registered_execution.append(task_id)
            continue

        daily._validate_task(task)
        runnable.append(task)

    signatures = [engine.experiment_signature(task) for task in runnable]
    if len(set(signatures)) != len(signatures):
        raise ValueError("Same generic experiment registered under different names")

    filtered_queue.parent.mkdir(parents=True, exist_ok=True)
    filtered_queue.write_text(json.dumps({"tasks": runnable}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    result = {
        "status": "GENERIC_WORK_AVAILABLE" if runnable else "NO_GENERIC_RESEARCH_PENDING",
        "has_work": bool(runnable),
        "total_registered_tasks": len(tasks),
        "current_data_cutoff": current_cutoff,
        "generic_runnable_tasks": [task["id"] for task in runnable],
        "skipped_stale_cutoff": skipped_stale_cutoff,
        "skipped_registered_execution": skipped_registered_execution,
        "skipped_completed": skipped_completed,
        "skipped_blocked": skipped_blocked,
        "skipped_dedicated_workflow": skipped_dedicated,
        "skipped_superseded": skipped_superseded,
        "completed_evidence_count": len(completed),
        "filtered_queue": str(filtered_queue),
    }
    status_file.parent.mkdir(parents=True, exist_ok=True)
    status_file.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as stream:
            stream.write(f"has_work={'true' if runnable else 'false'}\n")
            stream.write(f"status={result['status']}\n")

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--queue", type=Path, default=Path(__file__).with_name("research_queue_v2.json"))
    parser.add_argument("--filtered-queue", type=Path, required=True)
    parser.add_argument("--status-file", type=Path, required=True)
    parser.add_argument("--archive", type=Path)
    args = parser.parse_args()
    prepare(args.repository, args.queue, args.filtered_queue, args.status_file, args.archive)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
