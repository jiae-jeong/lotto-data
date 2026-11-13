#!/usr/bin/env python3
"""Freeze a weekly purchase file only by copying a current STRICT_PASS_READY artifact."""
import argparse
import csv
import hashlib
import json
import sys
from datetime import date as date_type, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
STRICT_GATE_VERSION = "V2_MAX_ANY2_ANY3_COVERAGE_ADJUSTED_CI_AND_ANY2_50_BLOCK_STABILITY"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def safe_repo_path(root: Path, raw: str) -> Path:
    path = Path(raw)
    if not path.is_absolute():
        path = root / path
    resolved = path.resolve()
    root_resolved = root.resolve()
    if resolved != root_resolved and root_resolved not in resolved.parents:
        raise ValueError(f"path escapes repository: {raw}")
    return resolved


def validate_lines(lines):
    if not isinstance(lines, list) or len(lines) != 5:
        raise ValueError("strict-ready portfolio must contain exactly five lines")
    normalized = []
    for index, line in enumerate(lines, 1):
        if not isinstance(line, list) or len(line) != 6:
            raise ValueError(f"line {index} must contain exactly six numbers")
        if any(type(n) is not int or not 1 <= n <= 45 for n in line):
            raise ValueError(f"line {index} contains a non-integer or out-of-range number")
        if line != sorted(line) or len(set(line)) != 6:
            raise ValueError(f"line {index} must be sorted and contain six unique numbers")
        normalized.append(tuple(line))
    if len(set(normalized)) != 5:
        raise ValueError("the five lines must be distinct")
    return [list(line) for line in normalized]


def build_freeze(root: Path, date_kst: str):
    data_path = root / "lotto_data.csv"
    with data_path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    rounds = [int(row["round"]) for row in rows]
    if not rounds or rounds != list(range(1, len(rounds) + 1)):
        raise ValueError("lotto_data.csv is empty, duplicated, or non-contiguous")
    cutoff = rounds[-1]
    target = cutoff + 1
    policy_path = root / "research" / "weekly_purchase" / "1251" / "THREE_LINE_POLICY_1251_PLUS.json"
    if policy_path.is_file():
        policy = load_json(policy_path)
        effective_from = int(policy.get("effective_from_target", 10**9))
        required_lines = int(policy.get("purchase_lines", 5))
        if target >= effective_from and required_lines != 5:
            raise ValueError(
                f"active target {target} policy requires {required_lines} lines; "
                "the legacy five-line STRICT_PASS_READY finalizer is blocked"
            )
    data_sha = sha256(data_path)
    date_stamp = date_kst.replace("-", "")
    outdir = root / "research" / "weekly_purchase" / str(target)

    status_path = outdir / f"STRICT_PASS_STATUS_{target}_{date_stamp}.json"
    if not status_path.is_file():
        raise FileNotFoundError(f"daily strict status is missing: {status_path.relative_to(root)}")
    status = load_json(status_path)
    if status.get("status") != "STRICT_PASS_READY":
        raise ValueError(f"current daily status is not STRICT_PASS_READY: {status.get('status')}")
    if status.get("date_kst") != date_kst:
        raise ValueError("strict status date does not match the requested KST date")
    if int(status.get("target_round", -1)) != target or int(status.get("data_cutoff", -1)) != cutoff:
        raise ValueError("strict status target/cutoff does not match current source data")
    if status.get("data_sha256") != data_sha:
        raise ValueError("strict status data hash does not match lotto_data.csv")
    status_models = status.get("validated_models")
    if status.get("strict_model_validation_pass") is not True or not isinstance(status_models, list) or not status_models:
        raise ValueError("strict status does not confirm at least one model passed strict validation")
    if status.get("strict_pass_ready") is not True or status.get("strict_portfolio_pass") is not True:
        raise ValueError("strict status does not confirm both model and portfolio PASS")
    if status.get("ready_file_exists") is not True or status.get("failed_gates") != []:
        raise ValueError("strict status is missing a current ready file or has failed gates")
    if not status.get("ready_file"):
        raise ValueError("strict status does not identify its STRICT_PASS_READY artifact")

    ready_path = safe_repo_path(root, status["ready_file"])
    if not ready_path.is_file() or not ready_path.name.startswith(f"STRICT_PASS_READY_{target}_"):
        raise FileNotFoundError("the current STRICT_PASS_READY artifact is missing or mis-scoped")
    ready = load_json(ready_path)
    if ready.get("status") != "STRICT_PASS_READY":
        raise ValueError("ready artifact status is not STRICT_PASS_READY")
    if ready.get("target_round") != target or ready.get("date_kst") != date_kst:
        raise ValueError("ready artifact target/date mismatch")
    if ready.get("data_cutoff") != cutoff or ready.get("data_sha256") != data_sha:
        raise ValueError("ready artifact data cutoff/hash mismatch")
    ready_models = ready.get("validated_models")
    if not isinstance(ready_models, list) or not ready_models or set(ready_models) != set(status_models):
        raise ValueError("ready artifact does not attest to the same non-empty strict-passing model set")
    if ready.get("model_verdict") != status.get("model_verdict"):
        raise ValueError("ready artifact model verdict differs from current strict status")
    if ready.get("strict_portfolio_pass") is not True or ready.get("failed_gates") != []:
        raise ValueError("ready artifact does not contain a clean strict portfolio PASS")
    if ready.get("strict_gate_version") != STRICT_GATE_VERSION:
        raise ValueError("ready artifact was produced under an unexpected strict gate version")
    if ready.get("no_future_leakage") is not True:
        raise ValueError("ready artifact does not attest to a passed no-future-leakage check")
    if ready.get("selection_uses_randomness") is not False or ready.get("random_fallback_allowed") is not False:
        raise ValueError("random selection or fallback is not permitted for finalization")

    model_code = root / "automation" / "model_validation_v5_all_models_fast.py"
    portfolio_code = root / "automation" / "five_role_research_v9.py"
    if ready.get("model_validation_code_sha256") != sha256(model_code):
        raise ValueError("model-validation code hash differs from the ready artifact")
    if ready.get("five_role_code_sha256") != sha256(portfolio_code):
        raise ValueError("portfolio code hash differs from the ready artifact")

    model_report = safe_repo_path(root, ready["model_validation_report"])
    research_report = safe_repo_path(root, ready["five_role_research_report"])
    if not model_report.is_file() or sha256(model_report) != ready.get("model_validation_sha256"):
        raise ValueError("model-validation report is missing or its hash changed")
    if not research_report.is_file() or sha256(research_report) != ready.get("five_role_research_sha256"):
        raise ValueError("five-role research report is missing or its hash changed")

    model = load_json(model_report)
    model_models = model.get("validated_models")
    if not isinstance(model_models, list) or not model_models or set(model_models) != set(status_models):
        raise ValueError("model-validation report does not confirm the same non-empty strict-passing model set")
    if model.get("verdict") != status.get("model_verdict"):
        raise ValueError("model-validation report verdict differs from current strict status")
    if model.get("data_cutoff") != cutoff or model.get("data_sha256") != data_sha:
        raise ValueError("model-validation report cutoff/hash mismatch")
    if model.get("target_range") != [201, cutoff]:
        raise ValueError("model-validation report target range mismatch")
    if model.get("training_cutoff_rule") != "training_through_round = target_round - 1":
        raise ValueError("model-validation report lacks the target-1 training cutoff rule")

    research = load_json(research_report)
    if research.get("data_cutoff") != cutoff or research.get("target_round") != target:
        raise ValueError("portfolio research report target/cutoff mismatch")
    if research.get("no_future_leakage") is not True:
        raise ValueError("portfolio research report does not pass the no-future-leakage gate")
    if research.get("strict_gate_version") != STRICT_GATE_VERSION:
        raise ValueError("portfolio research report uses a different strict gate version")
    if research.get("inference", {}).get("strict_portfolio_pass") is not True:
        raise ValueError("portfolio research report does not pass strict_portfolio_pass")
    if research.get("failed_gates") != []:
        raise ValueError("portfolio research report contains failed strict gates")
    integrity = research.get("integrity", {})
    if integrity.get("five_distinct_lines") is not True or integrity.get("five_distinct_roles") is not True:
        raise ValueError("portfolio research integrity checks did not pass")
    if integrity.get("selection_uses_randomness") is not False or integrity.get("random_fallback_allowed") is not False:
        raise ValueError("portfolio research used randomness or allowed fallback")

    lines = validate_lines(ready.get("final_lines"))
    if lines != research.get("final_lines"):
        raise ValueError("ready artifact lines differ from the underlying portfolio research report")

    freeze_payload = {
        "status": "FINAL_PURCHASE_FROZEN",
        "freeze_policy": "COPY_ONLY_FROM_STRICT_PASS_READY",
        "freeze_date_kst": date_kst,
        "target_round": target,
        "data_cutoff": cutoff,
        "data_sha256": data_sha,
        "strict_gate_version": STRICT_GATE_VERSION,
        "strict_portfolio_pass": True,
        "strict_pass_ready": True,
        "failed_gates": [],
        "strict_ready_file": str(ready_path.relative_to(root)),
        "strict_ready_sha256": sha256(ready_path),
        "model_validation_report": str(model_report.relative_to(root)),
        "model_validation_sha256": sha256(model_report),
        "five_role_research_report": str(research_report.relative_to(root)),
        "five_role_research_sha256": sha256(research_report),
        "model_validation_code_sha256": sha256(model_code),
        "five_role_code_sha256": sha256(portfolio_code),
        "final_lines": lines,
        "no_future_leakage": True,
        "selection_uses_randomness": False,
        "random_fallback_allowed": False,
    }
    freeze_path = outdir / f"FINAL_PURCHASE_5_LINES_{target}_{date_stamp}_STRICT_READY.json"
    text_path = outdir / f"FINAL_PURCHASE_5_LINES_{target}_{date_stamp}_STRICT_READY.txt"
    text_content = "\n".join(
        f"{index}. " + " ".join(str(number) for number in line)
        for index, line in enumerate(lines, 1)
    ) + "\n"
    return freeze_path, text_path, freeze_payload, text_content, target, cutoff, ready_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("date_kst", nargs="?", default=datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat())
    parser.add_argument("--freeze-not-before", default="2026-11-12")
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    date_kst = date_type.fromisoformat(args.date_kst).isoformat()
    if not args.verify_only and date_type.fromisoformat(date_kst) < date_type.fromisoformat(args.freeze_not_before):
        raise SystemExit(f"freeze is not permitted before {args.freeze_not_before}; no final file was written")

    freeze_path, text_path, payload, text_content, target, cutoff, ready_path = build_freeze(ROOT, date_kst)
    if args.verify_only:
        if not freeze_path.is_file() or not text_path.is_file():
            raise FileNotFoundError("the final strict-ready freeze is missing")
        if load_json(freeze_path) != payload:
            raise ValueError("the frozen JSON differs from the current strict-ready source")
        if text_path.read_text(encoding="utf-8") != text_content:
            raise ValueError("the frozen text differs from the current strict-ready source")
        action = "VERIFIED_EXISTING_STRICT_READY_FREEZE"
    else:
        if freeze_path.exists():
            if load_json(freeze_path) != payload:
                raise ValueError("append-only freeze collision; refusing to overwrite an existing final")
        else:
            freeze_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if text_path.exists():
            if text_path.read_text(encoding="utf-8") != text_content:
                raise ValueError("append-only text freeze collision; refusing to overwrite an existing final")
        else:
            text_path.write_text(text_content, encoding="utf-8")
        action = "FINAL_PURCHASE_FROZEN_FROM_STRICT_PASS_READY"

    print(json.dumps({
        "status": action,
        "target_round": target,
        "data_cutoff": cutoff,
        "strict_ready_file": str(ready_path.relative_to(ROOT)),
        "final_file": str(freeze_path.relative_to(ROOT)),
        "final_text_file": str(text_path.relative_to(ROOT)),
        "final_line_count": 5,
        "random_fallback_allowed": False,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
