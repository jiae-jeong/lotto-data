#!/usr/bin/env python3
"""Three-line Thursday seal / Friday verify-only finalizer.

It copies only a current, independently validated three-line STRICT_PASS_READY
artifact. It never searches for or generates purchase numbers.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date, timedelta
from pathlib import Path

from three_line_readiness_guard_v1 import (
    ROOT,
    build_status,
    read_source,
    validate_lines,
    validate_ready_artifact,
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe_repo_path(root: Path, raw: str) -> Path:
    path = Path(raw)
    if not path.is_absolute():
        path = root / path
    resolved = path.resolve()
    base = root.resolve()
    if resolved != base and base not in resolved.parents:
        raise ValueError(f"path escapes repository: {raw}")
    return resolved


def canonical_sha(payload: dict) -> str:
    body = {key: value for key, value in payload.items() if key != "freeze_payload_sha256"}
    raw = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def freeze(root: Path, date_kst: str) -> dict:
    seal_date = date.fromisoformat(date_kst)
    if seal_date.weekday() != 3:
        raise ValueError("three-line freeze is allowed only on Thursday; Friday is verify-only")
    cutoff_raw, data_sha, _ = read_source(root)
    cutoff = int(cutoff_raw)
    target = cutoff + 1
    policy = json.loads((root / "research/weekly_purchase/1251/THREE_LINE_POLICY_1251_PLUS.json").read_text(encoding="utf-8"))
    if target < int(policy["effective_from_target"]) or int(policy["purchase_lines"]) != 3:
        raise ValueError("three-line finalizer is not active for the current target")
    status = build_status(root, date_kst)
    if status.get("status") != "STRICT_PASS_READY" or status.get("strict_pass_ready") is not True:
        raise ValueError(f"no current three-line STRICT_PASS_READY artifact: {status.get('status')}")
    ready_path = safe_repo_path(root, status["ready_file"])
    ready, lines = validate_ready_artifact(ready_path, target, date_kst, cutoff, data_sha)
    outdir = root / "research" / "weekly_purchase" / str(target)
    outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / f"FINAL_THREE_LINES_{target}_{date_kst.replace('-', '')}.json"
    payload = {
        "status": "THURSDAY_VERIFIED_3_LINE_READY",
        "policy_id": policy["policy_id"],
        "target_round": target,
        "seal_date_kst": date_kst,
        "data_cutoff": cutoff,
        "data_sha256": data_sha,
        "source_ready_file": str(ready_path.relative_to(root)),
        "source_ready_sha256": sha256(ready_path),
        "strict_gate_version": ready["strict_gate_version"],
        "final_lines": lines,
        "inference": ready["inference"],
        "prospective_confirmation": ready["prospective_confirmation"],
        "no_future_leakage": True,
        "final_selection_randomness": False,
        "random_fallback_allowed": False,
        "final_purchase_freeze_allowed": True,
        "freeze_payload_sha256": None,
    }
    payload["freeze_payload_sha256"] = canonical_sha(payload)
    if out.exists():
        existing = json.loads(out.read_text(encoding="utf-8"))
        if existing != payload:
            raise ValueError(f"write-once seal collision: {out}")
    else:
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "status": payload["status"],
        "target_round": target,
        "seal_date_kst": date_kst,
        "data_cutoff": cutoff,
        "source_ready_sha256": payload["source_ready_sha256"],
        "seal_file": str(out.relative_to(root)),
        "seal_sha256": sha256(out),
    }


def verify(root: Path, date_kst: str, seal_date_kst: str | None = None) -> dict:
    run_date = date.fromisoformat(date_kst)
    if seal_date_kst is None:
        if run_date.weekday() == 4:
            seal_date = run_date - timedelta(days=1)
        else:
            seal_date = run_date
        seal_date_kst = seal_date.isoformat()
    seal_date = date.fromisoformat(seal_date_kst)
    if seal_date.weekday() != 3:
        raise ValueError("the source seal must be dated Thursday")
    cutoff_raw, data_sha, _ = read_source(root)
    cutoff = int(cutoff_raw)
    target = cutoff + 1
    out = root / "research" / "weekly_purchase" / str(target) / f"FINAL_THREE_LINES_{target}_{seal_date_kst.replace('-', '')}.json"
    if not out.is_file():
        raise FileNotFoundError(f"Thursday three-line seal is missing: {out.relative_to(root)}")
    payload = json.loads(out.read_text(encoding="utf-8"))
    if payload.get("status") != "THURSDAY_VERIFIED_3_LINE_READY":
        raise ValueError("seal status is not THURSDAY_VERIFIED_3_LINE_READY")
    if int(payload.get("target_round", -1)) != target or payload.get("seal_date_kst") != seal_date_kst:
        raise ValueError("seal target/date mismatch")
    if int(payload.get("data_cutoff", -1)) != cutoff or payload.get("data_sha256") != data_sha:
        raise ValueError("current source cutoff/hash differs from Thursday seal")
    if payload.get("no_future_leakage") is not True or payload.get("final_selection_randomness") is not False:
        raise ValueError("seal leakage or deterministic-selection attestation failed")
    if payload.get("random_fallback_allowed") is not False or payload.get("final_purchase_freeze_allowed") is not True:
        raise ValueError("seal fallback/freeze policy mismatch")
    if payload.get("freeze_payload_sha256") != canonical_sha(payload):
        raise ValueError("seal payload SHA256 mismatch")
    lines = validate_lines(payload.get("final_lines"))
    ready_path = safe_repo_path(root, payload["source_ready_file"])
    if not ready_path.is_file() or sha256(ready_path) != payload.get("source_ready_sha256"):
        raise ValueError("source STRICT_PASS_READY artifact missing or changed")
    ready, ready_lines = validate_ready_artifact(ready_path, target, seal_date_kst, cutoff, data_sha)
    if lines != ready_lines or ready["strict_gate_version"] != payload.get("strict_gate_version"):
        raise ValueError("Thursday seal differs from its validated STRICT_PASS_READY source")
    return {
        "status": "THURSDAY_SEAL_REVALIDATED",
        "target_round": target,
        "seal_date_kst": seal_date_kst,
        "data_cutoff": cutoff,
        "seal_file": str(out.relative_to(root)),
        "seal_sha256": sha256(out),
        "source_ready_sha256": sha256(ready_path),
        "line_count": 3,
        "numbers_per_line": 6,
        "union_size": 18,
        "line_level_output_status": "UNCHANGED_THURSDAY_SEAL",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("date_kst")
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--seal-date")
    args = parser.parse_args()
    result = verify(ROOT, args.date_kst, args.seal_date) if args.verify_only else freeze(ROOT, args.date_kst)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
