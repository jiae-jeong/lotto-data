#!/usr/bin/env python3
"""Prepare a generic daily-research queue without revalidating completed legacy registrations.

Completed evidence remains validated through daily_research_v2.completed_tasks(). Queue entries
that are already complete, blocked, or explicitly owned by a dedicated workflow are excluded
before the current task validator is applied. This prevents historical queue-contract drift from
blocking future generic daily runs while preserving evidence-integrity checks.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import daily_research_v2 as daily
import research_engine_v2 as engine


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

    # Validate immutable completed evidence first. Do not apply today's queue-schema validator to
    # a historical registration that already has validated completion evidence.
    completed = daily.completed_tasks(repository, archive)

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

        # Only work that the generic daily runner may actually execute must satisfy the current
        # registration contract.
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
