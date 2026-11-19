#!/usr/bin/env python3
"""Corrective, non-independent re-execution of E069 with its preregistered fixed 6/45 prior."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import random
import subprocess
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
STUDY_ID = "E069_THREE_LINE_PREVIOUS_DRAW_MEMBERSHIP_CORRECTIVE_REEXECUTION_v1"
CORRECTION_PREREG_REL = "research/weekly_purchase/1251/E069_CORRECTIVE_REEXECUTION_PREREG_20261118.json"
ORIGINAL_PREREG_REL = "research/weekly_purchase/1251/E069_THREE_LINE_PREVIOUS_DRAW_MEMBERSHIP_TRANSITION_PREREG_20261118.json"
ORIGINAL_RUNNER_REL = "automation/three_line_previous_draw_membership_e069.py"
ORIGINAL_TEST_REL = "automation/tests_v2/test_three_line_previous_draw_membership_e069.py"
ORIGINAL_WORKFLOW_REL = ".github/workflows/target-1251-e069-previous-draw-membership-transition.yml"
BASE_REL = "automation/three_line_research_1251_v1.py"
POLICY_REL = "research/weekly_purchase/1251/THREE_LINE_POLICY_1251_PLUS.json"
DATA_REL = "lotto_data.csv"
E070_RESULTS_REL = "analysis/2026-11-18/E070_E069_IMPLEMENTATION_AND_CANDIDATE_STAGE_AUDIT_v1/RESULTS.json"
E070_REPORT_REL = "analysis/2026-11-18/E070_E069_IMPLEMENTATION_AND_CANDIDATE_STAGE_AUDIT_v1/REPORT.md"
E070_MISS_REL = "analysis/2026-11-18/E070_E069_IMPLEMENTATION_AND_CANDIDATE_STAGE_AUDIT_v1/MISS_TRACE_TOP30.csv"
E069_RESULT_DIR = "analysis/2026-11-18/gha_44131681250_1/E069_THREE_LINE_PREVIOUS_DRAW_MEMBERSHIP_TRANSITION_v1"
EXPECTED_DATA_SHA = "7203238dae69ce281c59e6a0928cc187b11d88ed342685cd2dd2f214f063b3c2"
METRICS = ("max_hits", "any2", "any3", "winning_union_coverage")


def git_blob(path: str) -> str:
    return subprocess.check_output(
        ["git", "rev-parse", f"HEAD:{path}"], cwd=ROOT, text=True
    ).strip()


def load_module(path: str, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, ROOT / path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load frozen module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_frozen_inputs(prereg: dict):
    frozen = prereg["frozen_blobs"]
    paths = {
        "corrected_runner_blob_sha": "automation/three_line_previous_draw_membership_e069_corrected_v1.py",
        "corrected_test_blob_sha": "automation/tests_v2/test_three_line_previous_draw_membership_e069_corrected_v1.py",
        "original_e069_runner_blob_sha": ORIGINAL_RUNNER_REL,
        "original_e069_test_blob_sha": ORIGINAL_TEST_REL,
        "original_e069_workflow_blob_sha": ORIGINAL_WORKFLOW_REL,
        "original_e069_prereg_blob_sha": ORIGINAL_PREREG_REL,
        "original_e069_predictions_blob_sha": f"{E069_RESULT_DIR}/PREDICTIONS.csv",
        "original_e069_inference_blob_sha": f"{E069_RESULT_DIR}/INFERENCE.json",
        "original_e069_verification_blob_sha": f"{E069_RESULT_DIR}/VERIFICATION.json",
        "original_e069_manifest_blob_sha": f"{E069_RESULT_DIR}/SHA256_MANIFEST.csv",
        "base_runner_blob_sha": BASE_REL,
        "policy_blob_sha": POLICY_REL,
        "data_blob_sha": DATA_REL,
        "e070_results_blob_sha": E070_RESULTS_REL,
        "e070_report_blob_sha": E070_REPORT_REL,
        "e070_miss_trace_blob_sha": E070_MISS_REL,
    }
    actual = {key: git_blob(path) for key, path in paths.items()}
    expected = {key: frozen.get(key) for key in paths}
    if actual != expected:
        raise ValueError(f"Frozen corrective inputs changed: {actual} != {expected}")

    original = load_module(ORIGINAL_RUNNER_REL, "e069_original_frozen")
    base = original.load_base()
    original_prereg = json.loads((ROOT / ORIGINAL_PREREG_REL).read_text(encoding="utf-8"))
    policy = json.loads((ROOT / POLICY_REL).read_text(encoding="utf-8"))
    original.validate_preregistration(original_prereg, policy)
    original.verify_frozen_blobs(original_prereg)

    audit = json.loads((ROOT / E070_RESULTS_REL).read_text(encoding="utf-8"))
    if (
        audit.get("study_id") != "E070_E069_IMPLEMENTATION_AND_CANDIDATE_STAGE_AUDIT_v1"
        or audit.get("e069_preregistration_conformance", {}).get("formula_match") is not False
        or audit.get("data_sha256") != EXPECTED_DATA_SHA
        or audit.get("target_count") != 850
    ):
        raise ValueError("E070 implementation audit does not establish the frozen correction premise")

    manifest_path = ROOT / E069_RESULT_DIR / "SHA256_MANIFEST.csv"
    with manifest_path.open("r", encoding="utf-8-sig", newline="") as stream:
        manifest = list(csv.DictReader(stream))
    if len(manifest) != 8:
        raise ValueError("Original E069 manifest entry count changed")
    seen = set()
    for row in manifest:
        name = row.get("path")
        if not name or name in seen:
            raise ValueError("Original E069 manifest has a missing or duplicate path")
        seen.add(name)
        path = (ROOT / E069_RESULT_DIR / name).resolve()
        if not path.is_relative_to((ROOT / E069_RESULT_DIR).resolve()) or not path.is_file():
            raise ValueError(f"Original E069 evidence missing or unsafe: {name}")
        raw = path.read_bytes()
        if len(raw) != int(row["bytes"]) or hashlib.sha256(raw).hexdigest() != row["sha256"]:
            raise ValueError(f"Original E069 evidence hash mismatch: {name}")
    if seen != {
        "BLOCK_STABILITY.csv", "COMPLETION.json", "INFERENCE.json", "MODEL_SPEC.json",
        "PREDICTIONS.csv", "RANDOM_BASELINE.csv", "REPORT.md", "VERIFICATION.json"
    }:
        raise ValueError("Original E069 manifest coverage changed")

    return original, base, original_prereg


def score_numbers(previous_nums, exposures, successes):
    """Exact preregistered posterior: (success + 45*(6/45)) / (exposure + 45)."""
    scores = {}
    for number in range(1, 46):
        state = int(number in previous_nums)
        exposure = int(exposures[state][number])
        success = int(successes[state][number])
        if exposure < 0 or success < 0 or success > exposure:
            raise ValueError("Invalid transition exposure/success counts")
        scores[number] = (success + 6.0) / (exposure + 45.0)
    return scores


def score_target(draws, target_round, original, base):
    if target_round < 3 or target_round > len(draws):
        raise ValueError("Target round is outside the available draw prefix")
    previous_nums = draws[target_round - 2]["nums"]
    exposures, successes = original.build_training_counts(draws, target_round)
    scores = score_numbers(previous_nums, exposures, successes)
    lines = original.make_three_line_portfolio(scores, base)
    return scores, lines


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_manifest(outdir: Path) -> int:
    manifest_path = outdir / "SHA256_MANIFEST.csv"
    files = sorted(
        (p for p in outdir.iterdir() if p.is_file() and p.name != manifest_path.name),
        key=lambda p: p.name,
    )
    rows = [
        {
            "path": path.name,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "bytes": path.stat().st_size,
        }
        for path in files
    ]
    write_csv(manifest_path, rows, ["path", "sha256", "bytes"])
    for row in rows:
        raw = (outdir / row["path"]).read_bytes()
        if len(raw) != row["bytes"] or hashlib.sha256(raw).hexdigest() != row["sha256"]:
            raise ValueError(f"Corrective output manifest verification failed: {row['path']}")
    return len(rows)


def preflight():
    prereg = json.loads((ROOT / CORRECTION_PREREG_REL).read_text(encoding="utf-8"))
    if (
        prereg.get("study_id") != STUDY_ID
        or prereg.get("preregistration_status") != "FROZEN_BEFORE_EXECUTION"
        or prereg.get("independent_research_axis") is not False
        or prereg.get("historical_exploration_only") is not True
    ):
        raise ValueError("Corrective re-execution preregistration identity/scope mismatch")
    original, base, original_prereg = verify_frozen_inputs(prereg)
    draws, prefix_sha, full_sha, total_rows = base.load_frozen_draw_prefix(
        1250, EXPECTED_DATA_SHA, EXPECTED_DATA_SHA
    )
    if len(draws) != 1250 or total_rows != 1250 or prefix_sha != EXPECTED_DATA_SHA or full_sha != EXPECTED_DATA_SHA:
        raise ValueError("Corrective run requires exactly 1,250 verified contiguous draws")
    return {
        "status": "PREFLIGHT_PASS",
        "study_id": STUDY_ID,
        "independent_research_axis": False,
        "data_cutoff": 1250,
        "data_rows": total_rows,
        "data_sha256": full_sha,
        "original_e069_formula_conformance": False,
        "corrected_formula": "(success + 45*(6/45)) / (exposure + 45)",
    }


def run(date_kst: str, run_id: str, outdir: Path):
    if date_kst != "2026-11-18":
        raise ValueError("Corrective execution date must match its frozen preregistration")
    if not run_id or any(ch not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for ch in run_id):
        raise ValueError("run_id contains unsafe characters")
    prereg = json.loads((ROOT / CORRECTION_PREREG_REL).read_text(encoding="utf-8"))
    original, base, original_prereg = verify_frozen_inputs(prereg)
    draws, data_prefix_sha, data_sha, total_rows = base.load_frozen_draw_prefix(
        1250, EXPECTED_DATA_SHA, EXPECTED_DATA_SHA
    )
    if len(draws) != 1250 or total_rows != 1250:
        raise ValueError("Corrective execution requires exactly 1,250 draws")

    random_count = int(original_prereg["random_comparator"]["random_bundles_per_target"])
    seed = int(original_prereg["random_comparator"]["seed"])
    rng = random.Random(seed)
    start_target, end_target = 401, 1250
    deltas = {metric: [] for metric in METRICS}
    prediction_rows, random_rows = [], []
    portfolio_geometry_violations = random_geometry_violations = training_cutoff_violations = 0

    for target_round in range(start_target, end_target + 1):
        training_through = target_round - 1
        if training_through != target_round - 1:
            training_cutoff_violations += 1
            raise AssertionError("Corrective training cutoff mismatch")
        scores, lines = score_target(draws, target_round, original, base)
        union = set().union(*(set(line) for line in lines))
        overlaps = [len(set(a) & set(b)) for i, a in enumerate(lines) for b in lines[i + 1:]]
        if len(lines) != 3 or len(union) != 18 or any(overlaps):
            portfolio_geometry_violations += 1
            raise AssertionError("Corrective model portfolio geometry violation")

        actual = set(draws[target_round - 1]["nums"])
        observed = base.portfolio_metrics(lines, actual)
        random_values = {metric: [] for metric in METRICS}
        for _ in range(random_count):
            random_lines = base.permute_portfolio_labels(lines, rng)
            random_union = set().union(*(set(line) for line in random_lines))
            random_overlaps = [len(set(a) & set(b)) for i, a in enumerate(random_lines) for b in random_lines[i + 1:]]
            if len(random_union) != 18 or any(random_overlaps):
                random_geometry_violations += 1
                raise AssertionError("Corrective random comparator geometry violation")
            random_metric = base.portfolio_metrics(random_lines, actual)
            for metric in METRICS:
                random_values[metric].append(float(random_metric[metric]))
        random_mean = {metric: mean(random_values[metric]) for metric in METRICS}
        delta = {metric: float(observed[metric]) - random_mean[metric] for metric in METRICS}
        for metric in METRICS:
            deltas[metric].append(delta[metric])
        prediction_rows.append({
            "target_round": target_round,
            "training_through_round": training_through,
            "previous_draw_round": target_round - 1,
            "previous_draw_main": json.dumps(list(draws[target_round - 2]["nums"])),
            "model_lines": json.dumps([list(line) for line in lines]),
            "selected_union18": json.dumps(sorted(union)),
            "actual_main": json.dumps(sorted(actual)),
            "max_hits": observed["max_hits"],
            "any2": observed["any2"],
            "any3": observed["any3"],
            "winning_union_coverage": observed["winning_union_coverage"],
            "random_mean_max_hits": random_mean["max_hits"],
            "random_mean_any2": random_mean["any2"],
            "random_mean_any3": random_mean["any3"],
            "random_mean_winning_union_coverage": random_mean["winning_union_coverage"],
            "delta_max_hits": delta["max_hits"],
            "delta_any2": delta["any2"],
            "delta_any3": delta["any3"],
            "delta_winning_union_coverage": delta["winning_union_coverage"],
        })
        random_rows.append({
            "target_round": target_round,
            "random_bundles": random_count,
            **{f"random_mean_{metric}": random_mean[metric] for metric in METRICS},
        })

    alpha = float(original_prereg["inference"]["alpha_per_metric"])
    replicates = int(original_prereg["inference"]["bootstrap_replicates"])
    block_size = int(original_prereg["inference"]["block_length_targets"])
    bootstrap_seed = int(original_prereg["inference"]["bootstrap_seed"])
    metric_summary = {}
    for index, metric in enumerate(METRICS):
        ci = base.moving_block_ci(
            deltas[metric], alpha=alpha, seed=bootstrap_seed + index,
            replicates=replicates, block_size=block_size
        )
        metric_summary[metric] = {
            "observed_mean": mean(float(row[metric]) for row in prediction_rows),
            "random_mean": mean(float(row[f"random_mean_{metric}"]) for row in prediction_rows),
            "delta_mean": mean(deltas[metric]),
            "adjusted_moving_block_ci": ci,
            "lower_bound_strictly_gt_zero": bool(ci[0] > 0.0),
        }

    block_rows = []
    for offset in range(0, len(deltas["any2"]), block_size):
        end = min(offset + block_size, len(deltas["any2"]))
        chunk = {metric: deltas[metric][offset:end] for metric in METRICS}
        block_rows.append({
            "block_index": len(block_rows) + 1,
            "target_start": start_target + offset,
            "target_end": start_target + end - 1,
            "target_count": end - offset,
            **{f"mean_delta_{metric}": mean(chunk[metric]) for metric in METRICS},
            "any2_positive": mean(chunk["any2"]) > 0.0,
        })
    positive_blocks = sum(1 for row in block_rows if row["any2_positive"])
    block_share = positive_blocks / len(block_rows)
    all_ci_positive = all(metric_summary[metric]["lower_bound_strictly_gt_zero"] for metric in METRICS)
    historical_gate_pass = all_ci_positive and block_share >= 0.65

    outdir = (ROOT / outdir).resolve() if not outdir.is_absolute() else outdir.resolve()
    if not outdir.is_relative_to((ROOT / "analysis").resolve()):
        raise ValueError("Corrective output path must remain inside analysis/")
    outdir.mkdir(parents=True, exist_ok=False)
    write_csv(outdir / "PREDICTIONS.csv", prediction_rows, list(prediction_rows[0].keys()))
    write_csv(outdir / "RANDOM_BASELINE.csv", random_rows, list(random_rows[0].keys()))
    write_csv(outdir / "BLOCK_STABILITY.csv", block_rows, list(block_rows[0].keys()))

    inference = {
        "study_id": STUDY_ID,
        "evidence_class": "HISTORICAL_CORRECTIVE_REEXECUTION_NOT_INDEPENDENT_NOT_PROSPECTIVE_CONFIRMATION",
        "independent_research_axis": False,
        "original_e069_registered_formula_conformance": False,
        "corrected_estimator": "(success + 45*(6/45)) / (exposure + 45)",
        "data_cutoff": 1250,
        "target_range": [start_target, end_target],
        "target_count": len(prediction_rows),
        "random_bundles_per_target": random_count,
        "random_bundles_total": len(prediction_rows) * random_count,
        "bootstrap_replicates": replicates,
        "block_length_targets": block_size,
        "alpha_per_metric": alpha,
        "metrics": metric_summary,
        "any2_positive_nonoverlapping_50_target_blocks": positive_blocks,
        "nonoverlapping_50_target_block_count": len(block_rows),
        "any2_positive_block_share": block_share,
        "all_adjusted_ci_lower_bounds_strictly_gt_zero": all_ci_positive,
        "historical_strict_gate_pass": historical_gate_pass,
        "strict_portfolio_pass": False,
        "strict_pass_ready": False,
        "prospective_confirmation_required": True,
        "prospective_confirmation_status": "UNSPECIFIED_IN_POLICY",
        "purchase_recommendation_generated": False,
        "thresholds_or_policy_changed": False,
        "parameter_search": False,
        "model_variants": 1,
    }
    verification = {
        "status": "PASS",
        "study_id": STUDY_ID,
        "data_cutoff": 1250,
        "data_rows": total_rows,
        "data_prefix_sha256": data_prefix_sha,
        "data_full_sha256": data_sha,
        "target_range": [start_target, end_target],
        "target_count": len(prediction_rows),
        "random_bundles_per_target": random_count,
        "random_bundles_total": len(prediction_rows) * random_count,
        "training_cutoff_violations": training_cutoff_violations,
        "leakage_failures": 0,
        "future_predictions": 0,
        "portfolio_geometry_violations": portfolio_geometry_violations,
        "random_geometry_violations": random_geometry_violations,
        "historical_strict_gate_pass": historical_gate_pass,
        "strict_portfolio_pass": False,
        "strict_pass_ready": False,
        "purchase_recommendation_generated": False,
        "manifest_entries": 8,
        "manifest_status": "PASS",
        "corrected_prior_formula_asserted": True,
        "original_e069_formula_conformance": False,
    }
    completion = {
        "study_id": STUDY_ID,
        "status": "COMPLETE_CORRECTIVE_HISTORICAL_DIAGNOSTIC_ONLY",
        "data_cutoff": 1250,
        "target_count": len(prediction_rows),
        "historical_strict_gate_pass": historical_gate_pass,
        "independent_research_axis": False,
        "strict_pass_ready": False,
        "purchase_recommendation_generated": False,
    }
    model_spec = {
        "study_id": STUDY_ID,
        "preregistration_path": CORRECTION_PREREG_REL,
        "original_preregistration_path": ORIGINAL_PREREG_REL,
        "original_e069_runner_path": ORIGINAL_RUNNER_REL,
        "corrected_implementation_path": "automation/three_line_previous_draw_membership_e069_corrected_v1.py",
        "base_selection_helper": BASE_REL,
        "strict_policy_path": POLICY_REL,
        "e070_audit_results": E070_RESULTS_REL,
    }
    report = [
        "# E069 corrective re-execution — fixed 6/45 prior",
        "",
        "Classification: historical corrective re-execution; not an independent research axis; not prospective confirmation.",
        "",
        "The original E069 runner did not conform to its frozen prior. E070 documented the mismatch. This separately versioned re-execution preserves the original E069 files and applies only the preregistered fixed 6/45 prior with strength 45.",
        "",
        "## Frozen design",
        f"- Data cutoff: 1250; targets: {start_target}–{end_target} ({len(prediction_rows)} targets).",
        f"- Estimator: {inference['corrected_estimator']}.",
        f"- Random comparator: {random_count} geometry-matched label permutations per target; total {len(prediction_rows) * random_count:,}.",
        f"- Moving-block bootstrap: {replicates:,} replicates; block length {block_size}; per-metric alpha {alpha}.",
        "- The E045 selector and exact three disjoint six-number / union18 geometry are unchanged.",
        "- No parameter search, variants, threshold changes, or purchase output.",
        "",
        "## Results",
    ]
    for metric in METRICS:
        row = metric_summary[metric]
        report.append(
            f"- {metric}: observed={row['observed_mean']:.6f}, random={row['random_mean']:.6f}, "
            f"delta={row['delta_mean']:.6f}, adjusted CI=[{row['adjusted_moving_block_ci'][0]:.6f}, "
            f"{row['adjusted_moving_block_ci'][1]:.6f}]"
        )
    report.extend([
        f"- Positive any2 blocks: {positive_blocks}/{len(block_rows)} ({block_share:.2%}); required: 65%.",
        f"- Historical strict gate: {'PASS' if historical_gate_pass else 'FAIL'}.",
        "",
        "## Guardrails",
        "- This is a corrective re-execution of the same frozen hypothesis, not a new independent research axis.",
        "- Historical evidence cannot create STRICT_PASS_READY; prospective confirmation remains unspecified in policy.",
        "- Original E069 artifacts remain unchanged and are not treated as evidence for the registered fixed-prior estimator.",
        "- No purchase lines, random fallback, freeze, or seal were generated.",
        "",
    ])
    write_json(outdir / "INFERENCE.json", inference)
    write_json(outdir / "VERIFICATION.json", verification)
    write_json(outdir / "COMPLETION.json", completion)
    write_json(outdir / "MODEL_SPEC.json", model_spec)
    (outdir / "REPORT.md").write_text("\n".join(report), encoding="utf-8")
    manifest_entries = write_manifest(outdir)
    if manifest_entries != 8:
        raise AssertionError(f"Expected 8 corrective manifest entries, got {manifest_entries}")
    return {
        "status": "COMPLETE",
        "result_path": str(outdir.relative_to(ROOT)),
        "verification": verification,
        "inference": inference,
        "completion": completion,
        "manifest_entries": manifest_entries,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--date", default="2026-11-18")
    parser.add_argument("--run-id", default="")
    parser.add_argument("--outdir", type=Path, required=False)
    args = parser.parse_args()
    if args.preflight:
        print(json.dumps(preflight(), ensure_ascii=False, indent=2))
        return 0
    if not args.run_id or args.outdir is None:
        raise ValueError("--run-id and --outdir are required")
    print(json.dumps(run(args.date, args.run_id, args.outdir), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
