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

    runnable = []
    skipped_completed = []
    skipped_blocked = []
    skipped_dedicated = []
    for task in tasks:
        task_id = task["id"]
        if task_id in completed:
            skipped_completed.append(task_id)
            continue

        spec = task.get("spec") if isinstance(task.get("spec"), dict) else {}
        if spec.get("execution_mode") == "dedicated_workflow":
            skipped_dedicated.append(task_id)
            continue
        if spec.get("study_class") == "blocked":
            skipped_blocked.append(task_id)
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
        "generic_runnable_tasks": [task["id"] for task in runnable],
        "skipped_completed": skipped_completed,
        "skipped_blocked": skipped_blocked,
        "skipped_dedicated_workflow": skipped_dedicated,
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
