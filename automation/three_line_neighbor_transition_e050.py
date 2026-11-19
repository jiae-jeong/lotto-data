#!/usr/bin/env python3
"""E050: preregistered previous-main-number neighborhood to next-main transition."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import statistics
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from automation import three_line_bonus_transition_e048 as shared

STUDY_ID = "E050_THREE_LINE_PREVIOUS_MAIN_NEIGHBOR_TRANSITION_v1"
PREREG_REL = "research/weekly_purchase/1251/E050_THREE_LINE_NEIGHBOR_TRANSITION_PREREG_20261114.json"
PREREG_PATH = ROOT / PREREG_REL
POLICY_REL = "research/weekly_purchase/1251/THREE_LINE_POLICY_1251_PLUS.json"
POLICY_PATH = ROOT / POLICY_REL
HELPER_REL = "automation/three_line_bonus_transition_e048.py"
METRICS = ("max_hits", "any2", "any3", "winning_union_coverage")
RUNNER_REL = "automation/three_line_neighbor_transition_e050.py"
TEST_REL = "automation/tests_v2/test_three_line_neighbor_transition_e050.py"
WORKFLOW_REL = ".github/workflows/target-1251-e050-three-line-neighbor-transition.yml"


def git_blob(path: str) -> str:
    return subprocess.check_output(["git", "rev-parse", f"HEAD:{path}"], cwd=ROOT, text=True).strip()


def verify_frozen_blobs(prereg: dict) -> dict:
    expected = prereg["frozen_blobs"]
    paths = {
        "runner_blob_sha": RUNNER_REL,
        "test_blob_sha": TEST_REL,
        "workflow_blob_sha": WORKFLOW_REL,
        "shared_helper_blob_sha": HELPER_REL,
        "policy_blob_sha": POLICY_REL,
    }
    actual = {}
    for key, path in paths.items():
        actual[key] = git_blob(path)
        if actual[key] != expected.get(key):
            raise ValueError(f"frozen blob mismatch for {path}: {actual[key]} != {expected.get(key)}")
    return actual


def distance_bin(previous_nums, number: int) -> int:
    """0=exact repeat, 1=adjacent, 2=distance two, 3=distance three or more."""
    values = tuple(int(x) for x in previous_nums)
    if len(values) != 6 or len(set(values)) != 6 or any(x < 1 or x > 45 for x in values):
        raise ValueError("previous draw must contain six unique main numbers in 1..45")
    if type(number) is not int or not 1 <= number <= 45:
        raise ValueError("candidate number must be an integer in 1..45")
    distance = min(abs(number - x) for x in values)
    return 0 if distance == 0 else 1 if distance == 1 else 2 if distance == 2 else 3


def add_transition(previous_nums, outcome_nums, exposures, hits) -> None:
    outcome = set(int(x) for x in outcome_nums)
    if len(outcome) != 6 or any(x < 1 or x > 45 for x in outcome):
        raise ValueError("transition outcome must contain six valid main numbers")
    for number in range(1, 46):
        bucket = distance_bin(previous_nums, number)
        exposures[bucket][number - 1] += 1
        if number in outcome:
            hits[bucket][number - 1] += 1


def build_training_counts(draws, target_round: int):
    """Use transitions u=2..target_round-1 only; never use target_round outcome."""
    if target_round < 3 or target_round > len(draws):
        raise ValueError("target round is outside the available draw prefix")
    exposures = [[0] * 45 for _ in range(4)]
    hits = [[0] * 45 for _ in range(4)]
    for transition_round in range(2, target_round):
        add_transition(draws[transition_round - 2]["nums"], draws[transition_round - 1]["nums"], exposures, hits)
    return exposures, hits


def score_numbers(previous_nums, exposures, hits, global_counts, global_draws: int, alpha: float):
    if len(global_counts) != 45 or global_draws <= 0 or alpha <= 0:
        raise ValueError("invalid E050 scoring inputs")
    if len(exposures) != 4 or len(hits) != 4:
        raise ValueError("E050 requires four fixed distance bins")
    scores = []
    for number in range(1, 46):
        bucket = distance_bin(previous_nums, number)
        exposure = int(exposures[bucket][number - 1])
        hit_count = int(hits[bucket][number - 1])
        if exposure < 0 or hit_count < 0 or hit_count > exposure:
            raise ValueError("invalid conditional exposure/hit counts")
        global_rate = float(global_counts[number - 1]) / global_draws
        scores.append((hit_count + alpha * global_rate) / (exposure + alpha))
    return scores


def distance_bin_counts(previous_nums) -> list[int]:
    counts = [0, 0, 0, 0]
    for number in range(1, 46):
        counts[distance_bin(previous_nums, number)] += 1
    if sum(counts) != 45:
        raise AssertionError("distance bins must partition all 45 numbers")
    return counts


def validate_preregistration(prereg: dict, policy: dict) -> None:
    if prereg.get("study_id") != STUDY_ID or prereg.get("policy_id") != policy.get("policy_id"):
        raise ValueError("E050 study/policy identity mismatch")
    if prereg.get("date_kst") != "2026-11-14" or int(prereg.get("target_round", -1)) != 1251:
        raise ValueError("E050 target/date changed")
    if int(prereg.get("historical_data_cutoff", -1)) != 1249 or prereg.get("target_rounds") != "401..1249 inclusive":
        raise ValueError("E050 historical cutoff/target range changed")
    expected_feature = {
        "source": "The immediately preceding draw's six main numbers only; bonus is excluded.",
        "distance": "Minimum absolute numeric distance from candidate n to any of the previous draw's six main numbers; no circular wrap.",
        "bins": {
            "0": "distance exactly 0 (number is one of the previous six main numbers)",
            "1": "minimum distance exactly 1",
            "2": "minimum distance exactly 2",
            "3": "minimum distance at least 3",
        },
        "candidate_universe": "All integers 1..45 are assigned to exactly one bin for each target.",
    }
    if prereg.get("feature_definition") != expected_feature:
        raise ValueError("E050 feature definition changed")
    expected_estimator = {
        "conditional_exposure": "For each historical transition and candidate number, increment the exposure for the candidate's distance bin relative to the previous draw's six main numbers.",
        "conditional_hits": "Increment the matching bin/number hit count when that candidate is in the following draw's six main numbers.",
        "global_rate": "Count of each main number in draws 1..t-1 divided by t-1.",
        "smoothing_alpha": 60,
        "score_formula": "(conditional_hits[bin,n] + 60 * global_main_inclusion_rate[n]) / (conditional_exposures[bin,n] + 60).",
        "ranking": "Score descending, then number ascending.",
    }
    if prereg.get("estimator") != expected_estimator:
        raise ValueError("E050 estimator changed")
    portfolio = prereg["portfolio"]
    if (
        portfolio.get("selected_union") != "Top 18 ranked numbers."
        or portfolio.get("line_assignment") != "Deterministic rank interleaving: line 1 uses ranks 1,4,7,10,13,16; line 2 uses ranks 2,5,8,11,14,17; line 3 uses ranks 3,6,9,12,15,18."
        or portfolio.get("geometry") != "Exactly three pairwise-disjoint six-number lines, union18."
        or portfolio.get("randomness_in_selection") is not False
        or portfolio.get("parameter_tuning") is not False
        or int(portfolio.get("variants", -1)) != 1
    ):
        raise ValueError("E050 portfolio specification changed")
    comparator = prereg["random_comparator"]
    expected_method = "For each target, uniformly permute labels 1..45 jointly over the three fixed model lines, preserving three six-number lines, pairwise disjointness, union18, and line incidence geometry."
    if (
        comparator.get("method") != expected_method
        or int(comparator.get("random_bundles_per_target", -1)) != 120
        or int(comparator.get("seed", -1)) != 2026111405
        or comparator.get("randomness_used_for_final_selection") is not False
    ):
        raise ValueError("E050 random comparator/seed/count changed")
    exact_policy = policy["exact_null"]
    exact = comparator["exact_null"]
    for key, policy_key in (
        ("max_hits", "mean_max_hit"),
        ("any2", "p_any2"),
        ("any3", "p_any3"),
        ("winning_union_coverage", "expected_union_coverage"),
    ):
        if abs(float(exact[key]) - float(exact_policy[policy_key])) > 1e-14:
            raise ValueError(f"E050 exact geometry-matched null changed: {key}")
    inference = prereg["inference"]
    if (
        inference.get("metrics") != list(METRICS)
        or float(inference.get("family_alpha", -1)) != 0.05
        or float(inference.get("alpha_per_metric", -1)) != 0.0125
        or int(inference.get("bootstrap_replicates", -1)) != 4000
        or int(inference.get("bootstrap_seed", -1)) != 2026111405
        or int(inference.get("block_length_targets", -1)) != 50
        or inference.get("retain_final_remainder_block") is not True
        or float(inference.get("any2_positive_nonoverlapping_50_target_block_share_min", -1)) != 0.65
        or any(inference.get(key) is not True for key in (
            "no_threshold_relaxation", "no_alpha_change", "no_block_length_change",
            "no_comparator_change", "no_unbounded_microvariants"
        ))
    ):
        raise ValueError("E050 inference/promotion gate changed")
    prospective = prereg["prospective_confirmation"]
    if (
        prospective.get("required_by_policy") is not True
        or prospective.get("minimum_target_count") is not None
        or prospective.get("completion_rule") is not None
        or prospective.get("status") != "UNSPECIFIED_IN_POLICY"
    ):
        raise ValueError("E050 prospective rule must remain unspecified")
    if prereg.get("expected_record_counts") != {
        "PREDICTIONS.csv": 849, "RANDOM_BASELINE.csv": 849, "BLOCK_STABILITY.csv": 17
    }:
        raise ValueError("E050 expected record counts changed")
    expected_sha = "a5996af8b842799d777beae0abeef9767f79726870e4d78d6683dfb0fe4802e7"
    if prereg.get("source_data_prefix_sha256") != expected_sha or prereg.get("source_data_full_file_sha256") != expected_sha:
        raise ValueError("E050 frozen data hash changed")
    if prereg.get("no_future_leakage") is not True or prereg.get("strict_pass_ready_requires_prospective_rule") is not True:
        raise ValueError("E050 leakage/readiness policy changed")
    if int(policy.get("effective_from_target", -1)) != 1251 or int(policy.get("purchase_lines", -1)) != 3 or int(policy.get("numbers_per_line", -1)) != 6:
        raise ValueError("active three-line policy changed")
    gate = policy["strict_gate"]
    if (
        float(gate["family_alpha"]) != 0.05
        or float(gate["alpha_per_metric"]) != 0.0125
        or float(gate["any2_positive_nonoverlapping_50_target_block_share_min"]) != 0.65
        or gate.get("all_adjusted_moving_block_ci_lower_bounds_strictly_gt_zero") is not True
        or gate.get("no_threshold_relaxation") is not True
        or gate.get("prospective_confirmation_required") is not True
    ):
        raise ValueError("strict gate differs from active policy")
    frozen = prereg.get("frozen_blobs", {})
    required_blobs = {
        "runner_blob_sha", "test_blob_sha", "workflow_blob_sha",
        "shared_helper_blob_sha", "policy_blob_sha"
    }
    if set(frozen) != required_blobs:
        raise ValueError("E050 frozen blob registry incomplete")


def preflight():
    raw = PREREG_PATH.read_bytes()
    prereg = json.loads(raw.decode("utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    validate_preregistration(prereg, policy)
    frozen = verify_frozen_blobs(prereg)
    cutoff = int(prereg["historical_data_cutoff"])
    draws, prefix_sha, data_sha, total_rows = shared.read_frozen_prefix(
        cutoff, prereg["source_data_prefix_sha256"], prereg["source_data_full_file_sha256"]
    )
    if len(draws) != cutoff or total_rows != cutoff or prefix_sha != data_sha:
        raise ValueError("E050 frozen data prefix/full-file validation failed")
    return prereg, policy, frozen, draws, prefix_sha, data_sha, total_rows, hashlib.sha256(raw).hexdigest()


def run(date_kst: str, run_id: str, run_attempt: str):
    prereg, policy, frozen, draws, prefix_sha, data_sha, total_rows, prereg_sha = preflight()
    if date_kst != prereg["date_kst"]:
        raise ValueError("run date differs from frozen E050 preregistration")
    cutoff = int(prereg["historical_data_cutoff"])
    start = int(prereg["target_rounds"].split("..")[0])
    alpha = float(prereg["estimator"]["smoothing_alpha"])
    repeats = int(prereg["random_comparator"]["random_bundles_per_target"])
    seed = int(prereg["random_comparator"]["seed"])
    exact_record = prereg["random_comparator"]["exact_null"]
    exact = {
        "max_hits": float(exact_record["max_hits"]),
        "any2": float(exact_record["any2"]),
        "any3": float(exact_record["any3"]),
        "winning_union_coverage": float(exact_record["winning_union_coverage"]),
    }

    global_counts = [0] * 45
    for draw in draws[:start - 1]:
        for number in draw["nums"]:
            global_counts[number - 1] += 1
    exposures, hits = build_training_counts(draws, start)
    predictions, random_rows = [], []
    portfolio_geometry_violations = random_geometry_violations = 0

    for target in range(start, cutoff + 1):
        if sum(sum(row) for row in exposures) != 45 * (target - 2):
            raise AssertionError(f"training transition exposure count mismatch at {target}")
        previous_nums = draws[target - 2]["nums"]
        scores = score_numbers(previous_nums, exposures, hits, global_counts, target - 1, alpha)
        lines = shared.build_portfolio(scores)
        if len(lines) != 3 or any(len(line) != 6 for line in lines) or len(set().union(*(set(x) for x in lines))) != 18:
            portfolio_geometry_violations += 1
            raise AssertionError(f"model portfolio geometry violation at target {target}")
        actual = set(draws[target - 1]["nums"])
        observed = shared.portfolio_metrics(lines, actual)
        line_hits = [len(set(line) & actual) for line in lines]
        predictions.append({
            "target_round": target,
            "training_through_round": target - 1,
            "previous_draw_main": " ".join(map(str, sorted(previous_nums))),
            "distance_bin_counts_0_1_2_3plus": " ".join(map(str, distance_bin_counts(previous_nums))),
            "historical_transition_count": target - 2,
            "line1": " ".join(map(str, lines[0])),
            "line2": " ".join(map(str, lines[1])),
            "line3": " ".join(map(str, lines[2])),
            "actual_main": " ".join(map(str, sorted(actual))),
            "line_hits": " ".join(map(str, line_hits)),
            **observed,
        })
        rng = random.Random(seed + target)
        random_metrics = []
        for _ in range(repeats):
            randomized = shared.permute_portfolio_labels(lines, rng)
            if len(randomized) != 3 or any(len(line) != 6 for line in randomized) or len(set().union(*(set(x) for x in randomized))) != 18:
                random_geometry_violations += 1
                raise AssertionError(f"random comparator geometry violation at target {target}")
            random_metrics.append(shared.portfolio_metrics(randomized, actual))
        random_rows.append({
            "target_round": target,
            "random_bundles": repeats,
            "random_mean_max_hits": statistics.mean(x["max_hits"] for x in random_metrics),
            "random_p_any2": statistics.mean(x["any2"] for x in random_metrics),
            "random_p_any3": statistics.mean(x["any3"] for x in random_metrics),
            "random_mean_union_coverage": statistics.mean(x["winning_union_coverage"] for x in random_metrics),
            "exact_null_mean_max_hit": exact["max_hits"],
            "exact_null_p_any2": exact["any2"],
            "exact_null_p_any3": exact["any3"],
            "exact_null_expected_union_coverage": exact["winning_union_coverage"],
            "geometry_violations": 0,
        })
        for number in actual:
            global_counts[number - 1] += 1
        add_transition(previous_nums, draws[target - 1]["nums"], exposures, hits)

    targets = list(range(start, cutoff + 1))
    if [int(x["target_round"]) for x in predictions] != targets or len(predictions) != 849 or len(random_rows) != 849:
        raise AssertionError("E050 walk-forward target/count mismatch")
    diffs = {metric: [float(row[metric]) - exact[metric] for row in predictions] for metric in METRICS}
    block_length = int(prereg["inference"]["block_length_targets"])
    bootstrap_reps = int(prereg["inference"]["bootstrap_replicates"])
    bootstrap_seed = int(prereg["inference"]["bootstrap_seed"])
    alpha_ci = float(prereg["inference"]["alpha_per_metric"])
    blocks = []
    for index, begin in enumerate(range(0, len(predictions), block_length), 1):
        end = min(begin + block_length, len(predictions))
        block = {"block_index": index, "start_target": targets[begin], "end_target": targets[end - 1], "n": end - begin}
        for metric in METRICS:
            block[f"mean_delta_{metric}"] = statistics.mean(diffs[metric][begin:end])
        block["any2_positive"] = int(block["mean_delta_any2"] > 0)
        blocks.append(block)
    if len(blocks) != 17 or blocks[-1]["n"] != 49:
        raise AssertionError("E050 50-target block/remainder contract changed")
    positive_blocks = sum(row["any2_positive"] for row in blocks)
    positive_share = positive_blocks / len(blocks)
    inference = {}
    for offset, metric in enumerate(METRICS):
        ci = shared.moving_block_ci(diffs[metric], alpha_ci, bootstrap_seed + 9000 + offset, bootstrap_reps, block_length)
        inference[metric] = {
            "observed_mean": statistics.mean(float(row[metric]) for row in predictions),
            "exact_geometry_matched_null": exact[metric],
            "delta_mean": statistics.mean(diffs[metric]),
            "adjusted_moving_block_ci": ci,
            "lower_bound_strictly_gt_zero": ci[0] > 0,
        }
    historical_pass = all(inference[m]["lower_bound_strictly_gt_zero"] for m in METRICS) and positive_share >= 0.65
    prospective = prereg["prospective_confirmation"]
    prospective_defined = prospective["minimum_target_count"] is not None and prospective["completion_rule"] is not None
    strict_pass = bool(historical_pass and prospective_defined)
    readiness = (
        "HISTORICAL_GATE_PASS_BUT_NOT_READY_PROSPECTIVE_RULE_UNSPECIFIED"
        if historical_pass and not prospective_defined else
        "PROSPECTIVE_CONFIRMATION_PENDING" if historical_pass else "STRICT_FAIL"
    )

    output = ROOT / "analysis" / date_kst / f"gha_{run_id}_{run_attempt}" / STUDY_ID
    output.mkdir(parents=True, exist_ok=False)
    shared.write_csv(output / "PREDICTIONS.csv", predictions, [
        "target_round", "training_through_round", "previous_draw_main", "distance_bin_counts_0_1_2_3plus",
        "historical_transition_count", "line1", "line2", "line3", "actual_main", "line_hits",
        "max_hits", "any2", "any3", "winning_union_coverage"
    ])
    shared.write_csv(output / "RANDOM_BASELINE.csv", random_rows, [
        "target_round", "random_bundles", "random_mean_max_hits", "random_p_any2", "random_p_any3",
        "random_mean_union_coverage", "exact_null_mean_max_hit", "exact_null_p_any2",
        "exact_null_p_any3", "exact_null_expected_union_coverage", "geometry_violations"
    ])
    shared.write_csv(output / "BLOCK_STABILITY.csv", blocks, [
        "block_index", "start_target", "end_target", "n", "mean_delta_max_hits", "mean_delta_any2",
        "mean_delta_any3", "mean_delta_winning_union_coverage", "any2_positive"
    ])
    shared.write_json(output / "MODEL_SPEC.json", {
        "study_id": STUDY_ID, "feature_definition": prereg["feature_definition"],
        "estimator": prereg["estimator"], "portfolio": prereg["portfolio"],
        "random_comparator": prereg["random_comparator"], "inference": prereg["inference"],
        "frozen_blobs": frozen, "selection_uses_randomness": False,
        "parameter_tuning": False, "variants_evaluated": 1,
    })
    shared.write_json(output / "INFERENCE.json", {
        "study_id": STUDY_ID, "data_cutoff": cutoff, "target_range": [start, cutoff],
        "target_count": len(predictions), "exact_geometry_matched_null": exact, "metrics": inference,
        "block_stability": {
            "block_length_targets": block_length, "total_blocks_including_remainder": len(blocks),
            "positive_any2_blocks": positive_blocks, "any2_positive_block_share": positive_share,
            "required_minimum": 0.65, "remainder_block": blocks[-1],
        },
        "historical_strict_gate_pass": historical_pass,
        "prospective_confirmation": {
            "required": True, "minimum_target_count": prospective["minimum_target_count"],
            "completion_rule": prospective["completion_rule"], "status": "UNSPECIFIED_IN_POLICY",
            "minimum_count_adopted": False,
        },
        "strict_portfolio_pass": strict_pass, "strict_pass_ready": False, "readiness_status": readiness,
    })
    report = [
        "# E050 — Previous-main-number neighborhood transition", "",
        f"- Study status: **{readiness}**",
        f"- Data cutoff: **{cutoff}**; source rows: **{total_rows}**",
        f"- Walk-forward targets: **{len(predictions)}** ({start}..{cutoff})",
        f"- Random bundles: **{len(random_rows) * repeats:,}** ({repeats} per target)",
        "- Feature: each candidate's minimum absolute distance to the previous draw's six main numbers; bonus excluded",
        "- Fixed bins: exact repeat / distance 1 / distance 2 / distance 3+",
        "- Portfolio: exactly three pairwise-disjoint six-number lines, union18",
        "- Randomness is used only for the geometry-matched null, never for selection", "",
        "| Metric | Model mean | Exact null | Delta | Adjusted CI lower | Adjusted CI upper |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for metric in METRICS:
        item = inference[metric]
        ci = item["adjusted_moving_block_ci"]
        report.append(f"| {metric} | {item['observed_mean']:.6f} | {item['exact_geometry_matched_null']:.6f} | {item['delta_mean']:+.6f} | {ci[0]:+.6f} | {ci[1]:+.6f} |")
    report += [
        "", f"- any2-positive 50-target block share: **{positive_share:.2%}** ({positive_blocks}/{len(blocks)} blocks)",
        f"- Historical strict gate: **{'PASS' if historical_pass else 'FAIL'}**",
        "- STRICT_PASS_READY: **not created**",
        "- Prospective minimum/completion rule: **unspecified and not adopted**",
        "- No final purchase lines or freeze/seal were generated.", "",
        "Each target is scored before its outcome enters the global counts and transition history. One frozen specification; no variants or tuning.", "",
    ]
    (output / "REPORT.md").write_text("\n".join(report), encoding="utf-8")
    verification = {
        "study_id": STUDY_ID, "status": "PASS", "date_kst": date_kst, "run_id": run_id,
        "run_attempt": run_attempt, "target_round": 1251, "data_cutoff": cutoff,
        "source_data_rows": total_rows, "data_sha256": data_sha, "data_prefix_sha256": prefix_sha,
        "target_range": [start, cutoff], "target_count": len(predictions), "prediction_records": len(predictions),
        "random_bundles_per_target": repeats, "random_bundles_total": len(random_rows) * repeats,
        "training_cutoff_rule": "training_through_round = target_round - 1",
        "training_cutoff_violations": 0, "leakage_failures": 0, "future_predictions": 0,
        "no_future_leakage": True, "portfolio_geometry_violations": portfolio_geometry_violations,
        "random_geometry_violations": random_geometry_violations,
        "all_portfolios_three_lines_six_numbers_union18": True,
        "all_random_comparators_preserve_union18_geometry": True,
        "selection_uses_randomness": False, "randomness_used_only_for_comparator": True,
        "source_code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "preregistration_sha256": prereg_sha, "preregistration_blob_sha": git_blob(PREREG_REL),
        "policy_blob_sha": frozen["policy_blob_sha"], "shared_helper_git_blob_sha": frozen["shared_helper_blob_sha"],
        "frozen_blobs": frozen, "historical_strict_gate_pass": historical_pass,
        "strict_portfolio_pass": strict_pass, "strict_pass_ready": False, "readiness_status": readiness,
        "purchase_lines_generated": False, "final_purchase_freeze_allowed": False,
        "prospective_minimum_count_adopted": False, "manifest_entries": 8, "manifest_status": "PENDING",
    }
    shared.write_json(output / "VERIFICATION.json", verification)
    shared.write_json(output / "COMPLETION.json", {
        "study_id": STUDY_ID, "status": "COMPLETE", "data_cutoff": cutoff,
        "target_count": len(predictions), "random_bundles_total": len(random_rows) * repeats,
        "historical_strict_gate_pass": historical_pass, "strict_portfolio_pass": strict_pass,
        "strict_pass_ready": False, "computation_complete": True, "promotion_to_purchase_policy": False,
    })
    entries = shared.write_and_verify_manifest(output)
    verification["manifest_entries"] = entries
    verification["manifest_status"] = "PASS"
    shared.write_json(output / "VERIFICATION.json", verification)
    entries = shared.write_and_verify_manifest(output)
    if entries != 8:
        raise AssertionError(f"E050 manifest count {entries} != 8")
    result = {
        "status": "PASS", "study_id": STUDY_ID, "output": str(output.relative_to(ROOT)),
        "data_cutoff": cutoff, "target_count": len(predictions), "random_bundles_total": len(random_rows) * repeats,
        "historical_strict_gate_pass": historical_pass, "strict_portfolio_pass": strict_pass,
        "strict_pass_ready": False, "readiness_status": readiness, "manifest_entries": entries,
    }
    print(json.dumps(result, ensure_ascii=False))
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date")
    parser.add_argument("--run-id")
    parser.add_argument("--run-attempt", default=os.environ.get("GITHUB_RUN_ATTEMPT", "1"))
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()
    if args.preflight:
        prereg, policy, frozen, draws, prefix_sha, data_sha, rows, prereg_sha = preflight()
        print(json.dumps({
            "status": "PREFLIGHT_PASS", "study_id": STUDY_ID, "data_cutoff": len(draws),
            "data_sha256": data_sha, "preregistration_sha256": prereg_sha, "frozen_blobs": frozen,
        }, ensure_ascii=False))
        return
    if not args.date or not args.run_id:
        parser.error("--date and --run-id are required unless --preflight is used")
    run(args.date, args.run_id, str(args.run_attempt))


if __name__ == "__main__":
    main()
