#!/usr/bin/env python3
"""Fail-closed daily readiness guard for the three-line policy (target 1251+).

This module never generates ticket numbers. It only validates an independently
created, target-specific STRICT_PASS_READY artifact or records NOT_READY.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "lotto_data.csv"
POLICY = ROOT / "research/weekly_purchase/1251/THREE_LINE_POLICY_1251_PLUS.json"


def read_source(root: Path):
    data_path = root / "lotto_data.csv"
    raw = data_path.read_bytes()
    text = raw.decode("utf-8-sig")
    rows = list(csv.DictReader(text.splitlines()))
    if not rows:
        raise ValueError("lotto_data.csv has no draw records")
    rounds = [int(row["round"]) for row in rows]
    if rounds != list(range(1, len(rows) + 1)):
        raise ValueError("lotto_data.csv rounds are missing, duplicated, or non-contiguous")
    for expected, row in enumerate(rows, 1):
        nums = [int(row[f"no{i}"]) for i in range(1, 7)]
        bonus = int(row["bonus"])
        if len(set(nums)) != 6 or any(n < 1 or n > 45 for n in nums):
            raise ValueError(f"invalid main numbers at round {expected}")
        if not 1 <= bonus <= 45 or bonus in nums:
            raise ValueError(f"invalid bonus at round {expected}")
    return rows[-1]["round"], hashlib.sha256(raw).hexdigest(), len(rows)


def validate_lines(lines):
    if not isinstance(lines, list) or len(lines) != 3:
        raise ValueError("three-line STRICT_PASS_READY must contain exactly three lines")
    normalized = []
    for index, line in enumerate(lines, 1):
        if not isinstance(line, list) or len(line) != 6:
            raise ValueError(f"line {index} must contain exactly six numbers")
        if any(type(n) is not int or not 1 <= n <= 45 for n in line):
            raise ValueError(f"line {index} contains an invalid number")
        if line != sorted(line) or len(set(line)) != 6:
            raise ValueError(f"line {index} must be sorted and unique")
        normalized.append(tuple(line))
    if len(set(normalized)) != 3:
        raise ValueError("the three lines must be distinct")
    union = set().union(*(set(line) for line in normalized))
    if len(union) != 18:
        raise ValueError("the three lines must be pairwise disjoint with union18")
    return [list(line) for line in normalized]


def adjusted_lower(metric):
    if not isinstance(metric, dict):
        raise ValueError("missing strict metric inference")
    if "adjusted_ci_lower" in metric:
        return float(metric["adjusted_ci_lower"])
    delta = metric.get("adjusted_ci_delta")
    if isinstance(delta, list) and len(delta) == 2:
        return float(delta[0])
    moving = metric.get("adjusted_moving_block_ci")
    if isinstance(moving, list) and len(moving) == 2:
        return float(moving[0])
    raise ValueError("strict metric has no adjusted CI lower bound")


def validate_ready_artifact(path: Path, target: int, date_kst: str, cutoff: int, data_sha: str):
    ready = json.loads(path.read_text(encoding="utf-8"))
    if ready.get("status") != "STRICT_PASS_READY":
        raise ValueError(f"ready artifact status is not STRICT_PASS_READY: {path}")
    if int(ready.get("target_round", -1)) != target or ready.get("date_kst") != date_kst:
        raise ValueError("ready artifact target/date mismatch")
    if int(ready.get("data_cutoff", -1)) != cutoff or ready.get("data_sha256") != data_sha:
        raise ValueError("ready artifact cutoff/hash mismatch")
    if ready.get("strict_model_validation_pass") is not True:
        raise ValueError("ready artifact does not attest to a validated three-line model")
    models = ready.get("validated_models")
    if not isinstance(models, list) or not models:
        raise ValueError("ready artifact has no validated model identifiers")
    if ready.get("strict_portfolio_pass") is not True or ready.get("strict_pass_ready") is not True:
        raise ValueError("ready artifact does not attest to strict portfolio PASS")
    if ready.get("historical_strict_gate_pass") is not True:
        raise ValueError("ready artifact lacks a historical strict-gate PASS")
    if ready.get("no_future_leakage") is not True:
        raise ValueError("ready artifact does not attest to zero future leakage")
    if ready.get("final_selection_randomness") is not False:
        raise ValueError("final selection must be deterministic")
    if ready.get("random_fallback_allowed") is not False:
        raise ValueError("random fallback must remain prohibited")
    if not ready.get("strict_gate_version"):
        raise ValueError("ready artifact has no strict gate version")
    lines = validate_lines(ready.get("final_lines"))
    inference = ready.get("inference")
    if not isinstance(inference, dict):
        raise ValueError("ready artifact has no inference block")
    metric_block = inference.get("metrics", inference)
    for metric_name in ("max_hits", "any2", "any3", "winning_union_coverage"):
        lower = adjusted_lower(metric_block.get(metric_name))
        if not lower > 0:
            raise ValueError(f"{metric_name} adjusted CI lower bound is not > 0")
    block_share = float(inference.get(
        "any2_positive_50_target_block_share",
        metric_block.get("any2_positive_50_target_block_share", -1),
    ))
    if block_share < 0.65:
        raise ValueError("any2 positive 50-target block share is below 0.65")
    prospective = ready.get("prospective_confirmation")
    if not isinstance(prospective, dict) or prospective.get("required") is not True:
        raise ValueError("prospective confirmation evidence is missing")
    minimum = prospective.get("minimum_target_count")
    observed = prospective.get("observed_target_count")
    rule = prospective.get("completion_rule")
    if type(minimum) is not int or minimum <= 0 or type(observed) is not int or observed < minimum:
        raise ValueError("prospective confirmation target count is incomplete")
    if prospective.get("complete") is not True or not isinstance(rule, str) or not rule.strip():
        raise ValueError("prospective confirmation completion rule is incomplete")
    return ready, lines


def load_e045_evidence(root: Path, expected_cutoff: int, expected_data_sha: str):
    audit_path = root / "research/weekly_purchase/1251/THREE_LINE_READINESS_AUDIT_20261114.json"
    if not audit_path.is_file():
        return {"status": "NOT_AVAILABLE"}
    audit = json.loads(audit_path.read_text(encoding="utf-8"))

    # Prefer the latest append-only cutoff refresh. The original E045 execution
    # remains immutable historical provenance, but must not mask a newer cutoff.
    refresh = audit.get("e045_cutoff_refresh")
    if isinstance(refresh, dict):
        execution = refresh
        evidence_class = execution.get(
            "evidence_class", "APPEND_ONLY_HISTORICAL_CUTOFF_REFRESH_NOT_INDEPENDENT"
        )
        independent_research_axis = bool(execution.get("independent_research_axis", False))
    else:
        execution = audit.get("e045_execution") or {}
        evidence_class = "ORIGINAL_HISTORICAL_EVIDENCE"
        independent_research_axis = False

    rel = execution.get("result_path")
    if not rel:
        return {"status": "NOT_AVAILABLE", "reason": "E045 result path missing"}
    if refresh and execution.get("workflow_run_conclusion") != "success":
        raise ValueError("Latest E045 cutoff refresh workflow did not succeed")
    folder = (root / rel).resolve()
    if root.resolve() not in folder.parents:
        raise ValueError("E045 evidence path escapes repository")
    verification_path = folder / "VERIFICATION.json"
    completion_path = folder / "COMPLETION.json"
    inference_path = folder / "INFERENCE.json"
    manifest_path = folder / "SHA256_MANIFEST.csv"
    if not all(p.is_file() for p in (verification_path, completion_path, inference_path, manifest_path)):
        raise ValueError("E045 immutable evidence is incomplete")

    verification = json.loads(verification_path.read_text(encoding="utf-8"))
    completion = json.loads(completion_path.read_text(encoding="utf-8"))
    inference = json.loads(inference_path.read_text(encoding="utf-8"))
    if completion.get("status") != "COMPLETE" or completion.get("strict_pass_ready") is not False:
        raise ValueError("E045 completion evidence is inconsistent")
    if verification.get("status") != "PASS" or verification.get("no_future_leakage") is not True:
        raise ValueError("E045 verification or leakage evidence failed")
    cutoff = int(verification["data_cutoff"])
    data_sha = verification["data_sha256"]
    if int(completion.get("data_cutoff", -1)) != cutoff:
        raise ValueError("E045 completion/verification cutoff mismatch")
    if execution.get("data_cutoff") is not None and int(execution["data_cutoff"]) != cutoff:
        raise ValueError("E045 audit/verification cutoff mismatch")
    if execution.get("data_sha256") is not None and execution["data_sha256"] != data_sha:
        raise ValueError("E045 audit/verification data hash mismatch")
    if int(verification.get("leakage_failures", -1)) != 0:
        raise ValueError("E045 leakage failures are nonzero")
    if int(verification.get("training_cutoff_violations", -1)) != 0:
        raise ValueError("E045 training cutoff violations are nonzero")
    if verification.get("historical_strict_gate_pass") is not inference.get("historical_strict_gate_pass"):
        raise ValueError("E045 inference/verification historical gate mismatch")
    if verification.get("strict_portfolio_pass") is not False:
        raise ValueError("E045 verification must not claim portfolio PASS")
    if verification.get("strict_pass_ready") is not False or inference.get("strict_pass_ready") is not False:
        raise ValueError("E045 must remain not ready")

    with manifest_path.open(encoding="utf-8-sig", newline="") as stream:
        manifest = list(csv.DictReader(stream))
    if len(manifest) != 8 or len({row["path"] for row in manifest}) != 8:
        raise ValueError("E045 manifest count or uniqueness mismatch")
    expected = {p.name for p in folder.iterdir() if p.is_file() and p.name != manifest_path.name}
    if {row["path"] for row in manifest} != expected:
        raise ValueError("E045 manifest coverage mismatch")
    for row in manifest:
        artifact = folder / row["path"]
        raw = artifact.read_bytes()
        if len(raw) != int(row["bytes"]) or hashlib.sha256(raw).hexdigest() != row["sha256"]:
            raise ValueError(f"E045 artifact hash mismatch: {artifact.name}")

    # Re-check the frozen data prefix against the current source bytes.
    import importlib.util
    runner_path = root / "automation/three_line_research_1251_v1.py"
    spec = importlib.util.spec_from_file_location("e045_frozen_runner", runner_path)
    if spec is None or spec.loader is None:
        raise ValueError("E045 frozen runner cannot be loaded")
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    _, prefix_sha, _, _ = runner.load_frozen_draw_prefix(
        cutoff,
        verification["data_prefix_sha256"],
        verification["data_sha256"],
    )
    if prefix_sha != verification["data_prefix_sha256"]:
        raise ValueError("E045 frozen source prefix hash mismatch")

    metric_payload = inference.get("metrics")
    if not isinstance(metric_payload, dict):
        raise ValueError("E045 inference metrics are missing")
    failed_gates = []
    for metric_name in ("max_hits", "any2", "any3", "winning_union_coverage"):
        metric = metric_payload.get(metric_name)
        ci = metric.get("adjusted_moving_block_ci") if isinstance(metric, dict) else None
        if not isinstance(ci, list) or len(ci) != 2:
            raise ValueError(f"E045 adjusted CI is missing for {metric_name}")
        if not float(ci[0]) > 0:
            failed_gates.append(metric_name)
    block_share = float(inference.get("any2_positive_50_target_block_share", -1))
    if block_share < 0.65:
        failed_gates.append("any2_positive_50_target_block_share")

    historical_pass = inference.get("historical_strict_gate_pass") is True
    if historical_pass and failed_gates:
        raise ValueError("E045 historical PASS conflicts with failed strict gates")
    if not historical_pass and not failed_gates:
        raise ValueError("E045 historical FAIL has no failed strict gate")
    if refresh and sorted(execution.get("failed_gates", [])) != sorted(failed_gates):
        raise ValueError("E045 cutoff-refresh audit failed gates differ from inference")
    if inference.get("strict_portfolio_pass") is not False:
        raise ValueError("E045 historical evidence must not claim portfolio PASS")

    prospective_status = (
        "UNSPECIFIED_IN_POLICY"
        if inference.get("prospective_minimum_target_count") is None
        or not inference.get("prospective_completion_rule")
        else "SPECIFIED"
    )
    current_cutoff_match = cutoff == int(expected_cutoff) and data_sha == expected_data_sha
    status = (
        "STALE_CUTOFF" if not current_cutoff_match else
        "VERIFIED_HISTORICAL_STRICT_PASS" if historical_pass else
        "VERIFIED_HISTORICAL_STRICT_FAIL"
    )
    return {
        "status": status,
        "study_id": verification["study_id"],
        "base_study_id": execution.get("base_study_id"),
        "evidence_class": evidence_class,
        "independent_research_axis": independent_research_axis,
        "workflow_run_id": execution.get("workflow_run_id"),
        "run_url": execution.get("run_url"),
        "result_path": rel,
        "data_cutoff": cutoff,
        "data_sha256": data_sha,
        "target_count": int(verification["target_count"]),
        "random_bundles_total": int(verification["random_bundles_total"]),
        "prefix_sha256": prefix_sha,
        "manifest_entries": len(manifest),
        "manifest_status": "PASS",
        "leakage_failures": int(verification["leakage_failures"]),
        "historical_strict_gate_pass": historical_pass,
        "failed_gates": failed_gates,
        "metrics": metric_payload,
        "any2_positive_50_target_block_share": block_share,
        "prospective_confirmation_status": prospective_status,
        "prospective_minimum_target_count": inference.get("prospective_minimum_target_count"),
        "prospective_completion_rule": inference.get("prospective_completion_rule"),
        "strict_portfolio_pass": False,
        "strict_pass_ready": False,
    }

def build_status(root: Path, date_kst: str):
    cutoff_raw, data_sha, row_count = read_source(root)
    cutoff = int(cutoff_raw)
    target = cutoff + 1
    policy_path = root / "research/weekly_purchase/1251/THREE_LINE_POLICY_1251_PLUS.json"
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    effective_from = int(policy["effective_from_target"])
    if target < effective_from:
        raise ValueError(f"three-line guard is only active from target {effective_from}; current target is {target}")
    if int(policy["purchase_lines"]) != 3 or int(policy["numbers_per_line"]) != 6:
        raise ValueError("active three-line policy has unexpected geometry")

    e045 = load_e045_evidence(root, cutoff, data_sha)
    outdir = root / "research" / "weekly_purchase" / str(target)
    outdir.mkdir(parents=True, exist_ok=True)
    ready_files = sorted(outdir.glob(f"STRICT_PASS_READY_{target}_*.json"))
    if len(ready_files) > 1:
        raise ValueError("multiple current-target STRICT_PASS_READY artifacts require reconciliation")

    ready = None
    ready_lines = None
    if ready_files:
        ready, ready_lines = validate_ready_artifact(ready_files[0], target, date_kst, cutoff, data_sha)
        readiness = "STRICT_PASS_READY"
        failed_gates = []
        unevaluated_gates = []
        ready_file = str(ready_files[0].relative_to(root))
        strict_gate_evaluation = "VALIDATED_THREE_LINE_READY_ARTIFACT"
    elif (
        e045.get("status") == "VERIFIED_HISTORICAL_STRICT_FAIL"
        and int(e045.get("data_cutoff", -1)) == cutoff
    ):
        # The current-cutoff historical gates were actually evaluated and failed.
        # Do not label them "unevaluated" merely because no ready artifact exists.
        readiness = "STRICT_FAIL"
        failed_gates = list(e045["failed_gates"])
        unevaluated_gates = (
            ["prospective_confirmation"]
            if e045.get("prospective_confirmation_status") == "UNSPECIFIED_IN_POLICY"
            else []
        )
        ready_file = None
        strict_gate_evaluation = f"E045_HISTORICAL_STRICT_FAIL_AT_CUTOFF_{cutoff}"
    elif (
        e045.get("status") == "VERIFIED_HISTORICAL_STRICT_PASS"
        and int(e045.get("data_cutoff", -1)) == cutoff
    ):
        readiness = "NOT_READY"
        failed_gates = []
        unevaluated_gates = (
            ["prospective_confirmation"]
            if e045.get("prospective_confirmation_status") == "UNSPECIFIED_IN_POLICY"
            else []
        )
        ready_file = None
        strict_gate_evaluation = f"E045_HISTORICAL_PASS_PROSPECTIVE_PENDING_AT_CUTOFF_{cutoff}"
    else:
        readiness = "NOT_READY"
        failed_gates = (
            ["latest_e045_evidence_cutoff_mismatch"]
            if e045.get("status") == "STALE_CUTOFF"
            else ["no_eligible_three_line_portfolio_candidate"]
        )
        unevaluated_gates = [
            "max_hits_adjusted_ci",
            "any2_adjusted_ci",
            "any3_adjusted_ci",
            "winning_union_coverage_adjusted_ci",
            "any2_positive_50_target_block_share",
            "prospective_confirmation",
        ]
        ready_file = None
        strict_gate_evaluation = (
            f"E045_EVIDENCE_STALE_CURRENT_CUTOFF_{cutoff}"
            if e045.get("status") == "STALE_CUTOFF"
            else "NO_ELIGIBLE_THREE_LINE_READY_ARTIFACT"
        )

    status = {
        "status": readiness,
        "target_round": target,
        "date_kst": date_kst,
        "data_cutoff": cutoff,
        "data_rows": row_count,
        "data_sha256": data_sha,
        "purchase_lines_required": 3,
        "numbers_per_line": 6,
        "strict_model_validation_pass": bool(ready),
        "validated_models": ready.get("validated_models", []) if ready else [],
        "strict_portfolio_pass": bool(ready),
        "strict_pass_ready": bool(ready),
        "strict_gate_version": ready.get("strict_gate_version") if ready else None,
        "strict_gate_evaluation": strict_gate_evaluation,
        "ready_file": ready_file,
        "ready_file_exists": bool(ready),
        "line_level_output_status": "PUBLISHED_IN_STRICT_PASS_READY" if ready else "SUPPRESSED_NOT_READY",
        "failed_gates": failed_gates,
        "unevaluated_gates": unevaluated_gates,
        "no_future_leakage": True if not ready else ready["no_future_leakage"],
        "final_selection_randomness": False,
        "random_fallback_allowed": False,
        "final_purchase_freeze_allowed": False,
        "e045_historical_evidence": e045,
        "single_ticket_model_validation_is_not_three_line_evidence": True,
        "note": "This guard never generates purchase lines. It prefers the latest cutoff-matched E045 refresh, treats append-only refreshes as maintenance rather than independent research, and requires a separately validated target-specific STRICT_PASS_READY artifact with exact disjoint union18 geometry, all frozen strict gates, and completed prospective confirmation.",
    }
    status_path = outdir / f"STRICT_PASS_STATUS_{target}_{date_kst.replace('-', '')}.json"
    gate_path = outdir / f"MODEL_GATE_{target}_{date_kst.replace('-', '')}.json"
    status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    gate = {
        **status,
        "purchase_model_status": "STRICT_PASS_READY" if ready else "NO_ELIGIBLE_THREE_LINE_PORTFOLIO_CONTINUE_INDEPENDENT_RESEARCH",
    }
    gate_path.write_text(json.dumps(gate, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return status


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("date_kst")
    args = parser.parse_args()
    status = build_status(ROOT, args.date_kst)
    print(json.dumps({
        "status": status["status"],
        "target_round": status["target_round"],
        "data_cutoff": status["data_cutoff"],
        "strict_portfolio_pass": status["strict_portfolio_pass"],
        "strict_pass_ready": status["strict_pass_ready"],
        "failed_gates": status["failed_gates"],
        "unevaluated_gates": status["unevaluated_gates"],
        "ready_file_exists": status["ready_file_exists"],
        "line_level_output_status": status["line_level_output_status"],
        "e045_historical_evidence": status["e045_historical_evidence"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
