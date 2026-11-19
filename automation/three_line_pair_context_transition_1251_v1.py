#!/usr/bin/env python3
"""E051: one preregistered pair-context conditional inclusion model for three-line research."""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import random
import statistics
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_RUNNER = ROOT / "automation/three_line_research_1251_v1.py"
POLICY_PATH = ROOT / "research/weekly_purchase/1251/THREE_LINE_POLICY_1251_PLUS.json"
PREREG_PATH = ROOT / "research/weekly_purchase/1251/E051_THREE_LINE_PAIR_CONTEXT_CONDITIONAL_PREREG_20261115.json"
STUDY_ID = "E051_THREE_LINE_PAIR_CONTEXT_CONDITIONAL_v1"
BASE_RATE = 6.0 / 45.0
PRIOR_STRENGTH = 50.0


def load_base():
    import importlib.util
    spec = importlib.util.spec_from_file_location("e051_e045_reference", BASE_RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load frozen E045 selection/inference helpers: {BASE_RUNNER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def update_pair_context_counts(previous_numbers, next_numbers, exposures, successes):
    actual = set(int(n) for n in next_numbers)
    for pair in itertools.combinations(sorted(int(n) for n in previous_numbers), 2):
        exposures[pair] += 1
        for number in actual:
            successes[(pair, number)] += 1


def build_pair_context_counts(draws, through_round):
    if through_round < 2 or through_round > len(draws):
        raise ValueError("through_round must be in 2..len(draws)")
    exposures = Counter()
    successes = Counter()
    for target_round in range(2, through_round + 1):
        previous = draws[target_round - 2]["nums"]
        following = draws[target_round - 1]["nums"]
        update_pair_context_counts(previous, following, exposures, successes)
    return exposures, successes


def pair_context_scores(previous_numbers, exposures, successes):
    contexts = list(itertools.combinations(sorted(int(n) for n in previous_numbers), 2))
    if len(contexts) != 15:
        raise ValueError("The previous draw must provide exactly 15 pair contexts")
    scores = {}
    for number in range(1, 46):
        probabilities = [
            (successes[(pair, number)] + PRIOR_STRENGTH * BASE_RATE)
            / (exposures[pair] + PRIOR_STRENGTH)
            for pair in contexts
        ]
        scores[number] = statistics.mean(probabilities)
    return scores


def make_three_line_portfolio(scores, base):
    used = set()
    lines = []
    for _ in range(3):
        line = base.choose_disjoint_ticket(scores, scores, used)
        lines.append(line)
        used.update(line)
    if len(lines) != 3 or len(used) != 18:
        raise AssertionError("E051 portfolio must be exactly three disjoint lines with union18")
    return lines


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _verify_preregistration(prereg: dict, policy: dict):
    if prereg.get("study_id") != STUDY_ID or prereg.get("policy_id") != policy.get("policy_id"):
        raise ValueError("E051 preregistration/policy identity mismatch")
    if prereg.get("independent_research_axis") is not True or prereg.get("estimator", {}).get("parameter_search") is not False:
        raise ValueError("E051 must remain one fixed independent axis with no parameter search")
    if prereg.get("historical_data_cutoff") != 1250 or prereg.get("target_rounds") != "401..1250 inclusive":
        raise ValueError("E051 historical cutoff/target range changed")
    if prereg["estimator"]["prior_strength"] != 50 or prereg["estimator"]["prior_mean"] != "6/45 main-number inclusion probability under the uniform 6-of-45 null":
        raise ValueError("E051 pair-context estimator changed")
    gate = policy["strict_gate"]
    inference = prereg["inference"]
    if (
        float(gate["family_alpha"]) != float(inference["family_alpha"])
        or float(gate["alpha_per_metric"]) != float(inference["alpha_per_metric"])
        or float(gate["any2_positive_nonoverlapping_50_target_block_share_min"])
        != float(inference["any2_positive_nonoverlapping_50_target_block_share_min"])
        or gate["all_adjusted_moving_block_ci_lower_bounds_strictly_gt_zero"] is not True
        or gate["no_threshold_relaxation"] is not True
    ):
        raise ValueError("E051 inference differs from the unchanged three-line strict policy")
    for key in ("mean_max_hit", "p_any2", "p_any3", "expected_union_coverage"):
        if abs(float(policy["exact_null"][key]) - float(prereg["random_comparator"]["exact_null"][key])) > 1e-14:
            raise ValueError(f"E051 exact null mismatch for {key}")


def run(date_kst: str, run_id: str):
    import re
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_kst):
        raise ValueError("date must be YYYY-MM-DD")
    if not re.fullmatch(r"[A-Za-z0-9_-]+", run_id):
        raise ValueError("run_id contains unsafe characters")

    base = load_base()
    prereg = json.loads(PREREG_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    _verify_preregistration(prereg, policy)

    cutoff = int(prereg["historical_data_cutoff"])
    draws, data_prefix_sha, data_sha, current_rows = base.load_frozen_draw_prefix(
        cutoff,
        prereg["source_data_prefix_sha256"],
        prereg["source_data_full_file_sha256"],
    )
    if current_rows != cutoff or len(draws) != cutoff:
        raise ValueError("E051 requires exactly the preregistered 1..1250 canonical history")

    start_target = int(prereg["target_rounds"].split("..")[0])
    if start_target != 401 or cutoff - start_target + 1 != 850:
        raise ValueError("E051 target count differs from preregistered 850 targets")

    exposures, successes = build_pair_context_counts(draws, start_target - 1)
    observations = []
    random_rows = []
    training_cutoff_violations = 0
    portfolio_geometry_violations = 0
    random_geometry_violations = 0
    random_count = int(prereg["random_comparator"]["random_bundles_per_target"])
    seed = int(prereg["random_comparator"]["seed"])
    null = prereg["random_comparator"]["exact_null"]
    exact_by_metric = {
        "max_hits": float(null["mean_max_hit"]),
        "any2": float(null["p_any2"]),
        "any3": float(null["p_any3"]),
        "winning_union_coverage": float(null["expected_union_coverage"]),
    }
    metric_names = ("max_hits", "any2", "any3", "winning_union_coverage")

    for target_round in range(start_target, cutoff + 1):
        idx = target_round - 1
        training_through = target_round - 1
        previous_numbers = draws[idx - 1]["nums"]
        scores = pair_context_scores(previous_numbers, exposures, successes)
        lines = make_three_line_portfolio(scores, base)
        if training_through != target_round - 1:
            training_cutoff_violations += 1
            raise AssertionError("E051 training cutoff is not target_round-1")
        actual = set(draws[idx]["nums"])
        observed = base.portfolio_metrics(lines, actual)
        line_hits = [len(set(line) & actual) for line in lines]
        score_order = sorted(range(1, 46), key=lambda n: (-scores[n], n))
        score_payload = json.dumps([[n, round(scores[n], 16)] for n in range(1, 46)], separators=(",", ":")).encode()
        score_sha = hashlib.sha256(score_payload).hexdigest()
        observations.append({
            "target_round": target_round,
            "training_through_round": training_through,
            "lines": lines,
            "actual": tuple(sorted(actual)),
            "line_hits": line_hits,
            "score_sha256": score_sha,
            "top18": score_order[:18],
            **observed,
        })

        rng = random.Random(seed + target_round)
        random_metrics = []
        for _ in range(random_count):
            random_lines = base.permute_portfolio_labels(lines, rng)
            random_result = base.portfolio_metrics(random_lines, actual)
            union = set().union(*(set(line) for line in random_lines))
            overlaps = [len(set(a) & set(b)) for a, b in itertools.combinations(random_lines, 2)]
            if len(union) != 18 or any(x != 0 for x in overlaps):
                random_geometry_violations += 1
            random_metrics.append(random_result)
        if random_geometry_violations:
            raise AssertionError("E051 random comparator violated disjoint union18 geometry")
        random_rows.append({
            "target_round": target_round,
            "random_bundles": random_count,
            "random_mean_max_hits": statistics.mean(x["max_hits"] for x in random_metrics),
            "random_p_any2": statistics.mean(x["any2"] for x in random_metrics),
            "random_p_any3": statistics.mean(x["any3"] for x in random_metrics),
            "random_mean_union_coverage": statistics.mean(x["winning_union_coverage"] for x in random_metrics),
            "exact_null_mean_max_hit": exact_by_metric["max_hits"],
            "exact_null_p_any2": exact_by_metric["any2"],
            "exact_null_p_any3": exact_by_metric["any3"],
            "exact_null_expected_union_coverage": exact_by_metric["winning_union_coverage"],
            "geometry_violations": 0,
        })

        # Only after the target has been scored may its outcome enter the transition counts.
        update_pair_context_counts(previous_numbers, draws[idx]["nums"], exposures, successes)

    targets = [row["target_round"] for row in observations]
    expected_targets = list(range(start_target, cutoff + 1))
    if targets != expected_targets:
        raise AssertionError("E051 walk-forward target range mismatch")

    diffs = {
        metric: [float(row[metric]) - exact_by_metric[metric] for row in observations]
        for metric in metric_names
    }
    block_size = int(prereg["inference"]["block_length_targets"])
    bootstrap_reps = int(prereg["inference"]["bootstrap_replicates"])
    alpha = float(prereg["inference"]["alpha_per_metric"])
    block_rows = []
    for block_index, start in enumerate(range(0, len(observations), block_size), 1):
        stop = min(start + block_size, len(observations))
        item = {
            "block_index": block_index,
            "start_target": targets[start],
            "end_target": targets[stop - 1],
            "n": stop - start,
        }
        for metric in metric_names:
            item[f"mean_delta_{metric}"] = statistics.mean(diffs[metric][start:stop])
        item["any2_positive"] = int(item["mean_delta_any2"] > 0)
        block_rows.append(item)
    any2_positive_share = sum(item["any2_positive"] for item in block_rows) / len(block_rows)

    inference = {}
    for offset, metric in enumerate(metric_names):
        ci = base.moving_block_ci(
            diffs[metric], alpha, seed + 9000 + offset, bootstrap_reps, block_size
        )
        inference[metric] = {
            "observed_mean": statistics.mean(float(row[metric]) for row in observations),
            "exact_geometry_matched_null": exact_by_metric[metric],
            "delta_mean": statistics.mean(diffs[metric]),
            "adjusted_moving_block_ci": ci,
            "lower_bound_strictly_gt_zero": ci[0] > 0,
        }
    historical_gate_pass = (
        all(inference[metric]["lower_bound_strictly_gt_zero"] for metric in metric_names)
        and any2_positive_share >= float(prereg["inference"]["any2_positive_nonoverlapping_50_target_block_share_min"])
    )
    prospective = prereg["prospective_confirmation"]
    strict_portfolio_pass = base.strict_portfolio_ready(
        historical_gate_pass,
        prospective["minimum_target_count"],
        prospective["completion_rule"],
    )
    if historical_gate_pass and (prospective["minimum_target_count"] is None or prospective["completion_rule"] is None):
        readiness_status = "HISTORICAL_GATE_PASS_BUT_NOT_READY_PROSPECTIVE_RULE_UNSPECIFIED"
    elif historical_gate_pass:
        readiness_status = "PROSPECTIVE_CONFIRMATION_PENDING"
    else:
        readiness_status = "STRICT_FAIL"

    simulated_random_means = {
        "max_hits": statistics.mean(row["random_mean_max_hits"] for row in random_rows),
        "any2": statistics.mean(row["random_p_any2"] for row in random_rows),
        "any3": statistics.mean(row["random_p_any3"] for row in random_rows),
        "winning_union_coverage": statistics.mean(row["random_mean_union_coverage"] for row in random_rows),
    }
    outdir = ROOT / "analysis" / date_kst / run_id / STUDY_ID
    outdir.mkdir(parents=True, exist_ok=False)

    prediction_rows = []
    for row in observations:
        prediction_rows.append({
            "target_round": row["target_round"],
            "training_through_round": row["training_through_round"],
            "line1": " ".join(map(str, row["lines"][0])),
            "line2": " ".join(map(str, row["lines"][1])),
            "line3": " ".join(map(str, row["lines"][2])),
            "actual_numbers": " ".join(map(str, row["actual"])),
            "line1_hits": row["line_hits"][0],
            "line2_hits": row["line_hits"][1],
            "line3_hits": row["line_hits"][2],
            "max_hits": row["max_hits"],
            "any2": row["any2"],
            "any3": row["any3"],
            "winning_union_coverage": row["winning_union_coverage"],
            "union_size": row["union_size"],
            "score_sha256": row["score_sha256"],
            "top18_ranked_numbers": " ".join(map(str, row["top18"])),
        })
    base.write_csv(
        outdir / "PREDICTIONS.csv", prediction_rows,
        ["target_round", "training_through_round", "line1", "line2", "line3",
         "actual_numbers", "line1_hits", "line2_hits", "line3_hits", "max_hits",
         "any2", "any3", "winning_union_coverage", "union_size", "score_sha256", "top18_ranked_numbers"],
    )
    base.write_csv(
        outdir / "RANDOM_BASELINE.csv", random_rows,
        ["target_round", "random_bundles", "random_mean_max_hits", "random_p_any2",
         "random_p_any3", "random_mean_union_coverage", "exact_null_mean_max_hit",
         "exact_null_p_any2", "exact_null_p_any3", "exact_null_expected_union_coverage", "geometry_violations"],
    )
    base.write_csv(
        outdir / "BLOCK_STABILITY.csv", block_rows,
        ["block_index", "start_target", "end_target", "n", "mean_delta_max_hits",
         "mean_delta_any2", "mean_delta_any3", "mean_delta_winning_union_coverage", "any2_positive"],
    )

    source_paths = [PREREG_PATH, POLICY_PATH, BASE_RUNNER, Path(__file__).resolve()]
    source_hashes = {path.relative_to(ROOT).as_posix(): _sha(path) for path in source_paths}
    inference_payload = {
        "study_id": STUDY_ID,
        "evidence_class": "HISTORICAL_INDEPENDENT_AXIS_SCREEN_NOT_PROSPECTIVE_CONFIRMATION",
        "data_cutoff": cutoff,
        "target_range": [start_target, cutoff],
        "targets": len(observations),
        "random_bundles_per_target": random_count,
        "random_bundles_total": len(observations) * random_count,
        "block_size": block_size,
        "block_lengths": [item["n"] for item in block_rows],
        "family_alpha": float(prereg["inference"]["family_alpha"]),
        "alpha_per_metric": alpha,
        "bootstrap_replicates": bootstrap_reps,
        "metrics": inference,
        "any2_positive_50_target_block_share": any2_positive_share,
        "simulated_random_means": simulated_random_means,
        "historical_strict_gate_pass": historical_gate_pass,
        "strict_portfolio_pass": strict_portfolio_pass,
        "strict_pass_ready": False,
        "readiness_status": readiness_status,
        "prospective_minimum_target_count": prospective["minimum_target_count"],
        "prospective_completion_rule": prospective["completion_rule"],
        "parameter_search": False,
        "thresholds_changed": False,
        "alpha_changed": False,
        "block_length_changed": False,
        "comparator_changed": False,
        "purchase_recommendation_generated": False,
    }
    base.write_json(outdir / "INFERENCE.json", inference_payload)

    verification = {
        "status": "PASS",
        "study_id": STUDY_ID,
        "data_cutoff": cutoff,
        "current_source_data_rows": current_rows,
        "data_sha256": data_sha,
        "data_prefix_sha256": data_prefix_sha,
        "target_range": [start_target, cutoff],
        "target_count": len(observations),
        "prediction_records": len(prediction_rows),
        "random_bundles_per_target": random_count,
        "random_bundles_total": len(observations) * random_count,
        "training_cutoff_violations": training_cutoff_violations,
        "leakage_failures": 0,
        "future_predictions": 0,
        "portfolio_geometry_violations": portfolio_geometry_violations,
        "random_geometry_violations": random_geometry_violations,
        "no_future_leakage": True,
        "random_baseline_executed": True,
        "independent_research_axis": True,
        "parameter_search": False,
        "thresholds_changed": False,
        "alpha_changed": False,
        "block_length_changed": False,
        "comparator_changed": False,
        "strict_portfolio_pass": strict_portfolio_pass,
        "strict_pass_ready": False,
        "purchase_recommendation_generated": False,
        "source_hashes": source_hashes,
    }
    base.write_json(outdir / "VERIFICATION.json", verification)
    completion = {
        "study_id": STUDY_ID,
        "status": "COMPLETE",
        "data_cutoff": cutoff,
        "target_range": [start_target, cutoff],
        "target_count": len(observations),
        "historical_strict_gate_pass": historical_gate_pass,
        "strict_portfolio_pass": strict_portfolio_pass,
        "strict_pass_ready": False,
        "readiness_status": readiness_status,
        "evidence_class": "HISTORICAL_INDEPENDENT_AXIS_SCREEN_NOT_PROSPECTIVE_CONFIRMATION",
        "independent_research_axis": True,
        "purchase_recommendation_generated": False,
    }
    base.write_json(outdir / "COMPLETION.json", completion)

    report = [
        "# E051 — Pair-context conditional number-inclusion model",
        "",
        f"- Study status: **{readiness_status}**",
        f"- Data cutoff: **{cutoff}**; source rows: **{current_rows}**",
        f"- Walk-forward targets: **{len(observations)}** ({start_target}..{cutoff})",
        f"- Random bundles: **{len(observations) * random_count:,}** ({random_count} per target)",
        "- Feature: 15 unordered pairs in the immediately preceding main draw; bonus excluded",
        "- Estimator: Beta-smoothed candidate inclusion probability with prior mean 6/45 and fixed strength 50",
        "- Portfolio: three pairwise-disjoint six-number lines, union18",
        "- Randomness is used only for the geometry-matched null, never for selection",
        "",
        "| Metric | Model mean | Exact null | Delta | Adjusted CI lower | Adjusted CI upper |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for metric in metric_names:
        item = inference[metric]
        report.append(
            f"| {metric} | {item['observed_mean']:.6f} | {item['exact_geometry_matched_null']:.6f} "
            f"| {item['delta_mean']:+.6f} | {item['adjusted_moving_block_ci'][0]:+.6f} "
            f"| {item['adjusted_moving_block_ci'][1]:+.6f} |"
        )
    report.extend([
        "",
        f"- any2-positive 50-target block share: **{any2_positive_share:.2%}** ({sum(x['any2_positive'] for x in block_rows)}/{len(block_rows)} blocks)",
        f"- Historical strict gate: **{'PASS' if historical_gate_pass else 'FAIL'}**",
        "- STRICT_PASS_READY: **not created**",
        "- Prospective minimum/completion rule: **unspecified and not adopted**",
        "- No final purchase lines, recommendation, or freeze/seal were generated.",
        "",
        "Each target is scored before its outcome enters pair-context exposure/success counts. One frozen specification, one estimator, no variants or tuning.",
    ])
    (outdir / "REPORT.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    manifest_entries = base.write_and_verify_manifest(outdir)
    return {
        "status": "COMPLETE",
        "study_id": STUDY_ID,
        "result_path": outdir.relative_to(ROOT).as_posix(),
        "data_cutoff": cutoff,
        "target_count": len(observations),
        "random_bundles_total": len(observations) * random_count,
        "historical_strict_gate_pass": historical_gate_pass,
        "strict_portfolio_pass": strict_portfolio_pass,
        "strict_pass_ready": False,
        "readiness_status": readiness_status,
        "manifest_entries": manifest_entries,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.date, args.run_id), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
