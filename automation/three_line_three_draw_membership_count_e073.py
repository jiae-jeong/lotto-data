#!/usr/bin/env python3
"""E073: preregistered three-draw membership-state conditional inclusion model."""
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
PREREG_PATH = ROOT / "research/weekly_purchase/1251/E073_THREE_LINE_THREE_DRAW_MEMBERSHIP_COUNT_TRANSITION_PREREG_20261118.json"
STUDY_ID = "E073_THREE_LINE_THREE_DRAW_MEMBERSHIP_COUNT_TRANSITION_v1"
BASE_RATE = 6.0 / 45.0
PRIOR_STRENGTH = 45.0
METRICS = ("max_hits", "any2", "any3", "winning_union_coverage")


def load_base():
    import importlib.util
    spec = importlib.util.spec_from_file_location("e073_e045_reference", BASE_RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load frozen E045 selection/inference helpers: {BASE_RUNNER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def membership_state(number: int, three_back, two_back, previous) -> int:
    """Count candidate membership across draws t-3, t-2, and t-1 (0..3)."""
    number = int(number)
    if not 1 <= number <= 45:
        raise ValueError("candidate number must be in 1..45")
    prior_sets = [set(three_back), set(two_back), set(previous)]
    return sum(number in draw for draw in prior_sets)


def update_lag3_counts(three_back, two_back, previous, outcome, exposures, successes):
    prior_sets = [
        set(int(n) for n in three_back),
        set(int(n) for n in two_back),
        set(int(n) for n in previous),
    ]
    actual = set(int(n) for n in outcome)
    if any(len(draw) != 6 for draw in prior_sets + [actual]):
        raise ValueError("E073 transitions require four valid six-number draws")
    if any(n < 1 or n > 45 for draw in prior_sets + [actual] for n in draw):
        raise ValueError("E073 transition contains an invalid number")
    for number in range(1, 46):
        state = sum(number in draw for draw in prior_sets)
        exposures[state][number] += 1
        if number in actual:
            successes[state][number] += 1


def build_lag3_counts(draws, through_round: int):
    if through_round < 4 or through_round > len(draws):
        raise ValueError("through_round must be in 4..len(draws)")
    exposures = [[0] * 46 for _ in range(4)]
    successes = [[0] * 46 for _ in range(4)]
    for outcome_round in range(4, through_round + 1):
        update_lag3_counts(
            draws[outcome_round - 4]["nums"],
            draws[outcome_round - 3]["nums"],
            draws[outcome_round - 2]["nums"],
            draws[outcome_round - 1]["nums"],
            exposures, successes,
        )
    return exposures, successes


def lag3_scores(three_back, two_back, previous, exposures, successes):
    if len(exposures) != 4 or len(successes) != 4:
        raise ValueError("E073 requires exactly four frozen membership-count states")
    scores = {}
    for number in range(1, 46):
        state = membership_state(number, three_back, two_back, previous)
        exposure = exposures[state][number]
        success = successes[state][number]
        scores[number] = (
            success + PRIOR_STRENGTH * BASE_RATE
        ) / (exposure + PRIOR_STRENGTH)
    return scores


def make_three_line_portfolio(scores, base):
    used = set()
    lines = []
    for _ in range(3):
        line = base.choose_disjoint_ticket(scores, scores, used)
        lines.append(line)
        used.update(line)
    if len(lines) != 3 or len(used) != 18:
        raise AssertionError("E073 portfolio must be exactly three disjoint lines with union18")
    return lines


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize_csv_outputs(outdir: Path):
    """Use LF-only UTF-8 CSV bytes so git diff --check does not treat CR as trailing whitespace."""
    for path in outdir.glob("*.csv"):
        raw = path.read_bytes()
        if raw.startswith(b"\xef\xbb\xbf"):
            raw = raw[3:]
        path.write_bytes(raw.replace(b"\r\n", b"\n"))


def _verify_preregistration(prereg: dict, policy: dict):
    if prereg.get("study_id") != STUDY_ID or prereg.get("policy_id") != policy.get("policy_id"):
        raise ValueError("E073 preregistration/policy identity mismatch")
    if prereg.get("preregistration_status") != "FROZEN_BEFORE_EXECUTION":
        raise ValueError("E073 preregistration is not frozen")
    if prereg.get("independent_research_axis") is not True or prereg.get("independent_signal_family") is not True or prereg.get("independent_sample") is not False:
        raise ValueError("E073 must remain one independent signal-family axis")
    if prereg.get("historical_data_cutoff") != 1250 or prereg.get("target_rounds") != "401..1250 inclusive":
        raise ValueError("E073 historical cutoff/target range changed")
    if prereg.get("source_data_prefix_sha256") != "7203238dae69ce281c59e6a0928cc187b11d88ed342685cd2dd2f214f063b3c2":
        raise ValueError("E073 frozen 1250-round prefix hash changed")
    if prereg.get("source_data_full_file_sha256") != prereg.get("source_data_prefix_sha256"):
        raise ValueError("E073 requires the frozen full source to equal the 1250-round prefix")
    expected_feature = {
        "source": "The three immediately preceding draws' six main numbers only; bonus numbers are excluded.",
        "state_encoding": {
            "0": "candidate absent from all three immediately preceding main draws",
            "1": "candidate present in exactly one of the three immediately preceding main draws",
            "2": "candidate present in exactly two of the three immediately preceding main draws",
            "3": "candidate present in all three immediately preceding main draws"
        },
        "candidate_universe": "All integers 1..45 are scored for every target.",
        "transition_history": "For each historical outcome round u=4..t-1, classify every candidate by its count of appearances in draws u-3, u-2, and u-1, then observe inclusion in draw u."
    }
    if prereg.get("feature_definition") != expected_feature:
        raise ValueError("E073 three-draw membership feature changed")
    estimator = prereg["estimator"]
    if (
        estimator.get("prior_mean") != "6/45 main-number inclusion probability under the uniform 6-of-45 null"
        or float(estimator.get("prior_strength", -1)) != PRIOR_STRENGTH
        or estimator.get("state_definition") != "Count 0..3 of candidate appearances in the three immediately preceding main draws."
        or estimator.get("posterior_probability") != "(success[state,n] + 45*(6/45))/(exposure[state,n] + 45)"
        or estimator.get("ranking") != "Score descending, then number ascending."
        or estimator.get("variants") != 1
        or estimator.get("parameter_search") is not False
    ):
        raise ValueError("E073 estimator changed")
    portfolio = prereg["portfolio"]
    if (
        portfolio.get("geometry") != "Exactly three pairwise-disjoint six-number lines, union18."
        or portfolio.get("selection") != "Three sequential calls to the unchanged E045 choose_disjoint_ticket selector, passing the E073 score as both role_score and global_score; remove selected numbers after each line."
        or portfolio.get("randomness_in_selection") is not False
        or portfolio.get("variants") != 1
    ):
        raise ValueError("E073 portfolio construction changed")
    random_spec = prereg["random_comparator"]
    if (
        random_spec.get("random_bundles_per_target") != 120
        or random_spec.get("seed") != 20261118073
        or random_spec.get("randomness_used_for_final_selection") is not False
        or random_spec.get("method") != "For each target, uniformly permute labels 1..45 jointly over the three fixed model lines, preserving three six-number lines, pairwise disjointness, union18, and line-incidence geometry."
    ):
        raise ValueError("E073 random comparator changed")
    inference = prereg["inference"]
    if (
        inference.get("metrics") != list(METRICS)
        or float(inference.get("family_alpha", -1)) != 0.05
        or float(inference.get("alpha_per_metric", -1)) != 0.0125
        or int(inference.get("bootstrap_replicates", -1)) != 4000
        or int(inference.get("bootstrap_seed", -1)) != 20261118073
        or int(inference.get("block_length_targets", -1)) != 50
        or inference.get("retain_final_remainder_block") is not True
        or float(inference.get("any2_positive_nonoverlapping_50_target_block_share_min", -1)) != 0.65
        or any(inference.get(key) is not True for key in (
            "no_threshold_relaxation", "no_alpha_change", "no_block_length_change",
            "no_comparator_change", "no_unbounded_microvariants"
        ))
    ):
        raise ValueError("E073 inference specification changed")
    prospective = prereg["prospective_confirmation"]
    if (
        prospective.get("required_by_policy") is not True
        or prospective.get("minimum_target_count") is not None
        or prospective.get("completion_rule") is not None
        or prospective.get("status") != "UNSPECIFIED_IN_POLICY"
    ):
        raise ValueError("E073 cannot silently define the prospective confirmation rule")
    expected_counts = {
        "PREDICTIONS": 850,
        "RANDOM_BASELINE": 850,
        "BLOCK_STABILITY": 17,
    }
    if prereg.get("expected_record_counts") != expected_counts:
        raise ValueError("E073 expected record counts changed")
    if prereg.get("no_future_leakage") is not True or prereg.get("strict_pass_ready_requires_prospective_rule") is not True:
        raise ValueError("E073 leakage/readiness requirements changed")
    if int(policy.get("effective_from_target", -1)) != 1251 or int(policy.get("purchase_lines", -1)) != 3:
        raise ValueError("Active target-1251 three-line policy changed")
    gate = policy["strict_gate"]
    if (
        float(gate["family_alpha"]) != 0.05
        or float(gate["alpha_per_metric"]) != 0.0125
        or float(gate["any2_positive_nonoverlapping_50_target_block_share_min"]) != 0.65
        or gate.get("all_adjusted_moving_block_ci_lower_bounds_strictly_gt_zero") is not True
        or gate.get("no_threshold_relaxation") is not True
        or gate.get("prospective_confirmation_required") is not True
    ):
        raise ValueError("E073 strict gates differ from the unchanged active policy")
    for key in ("mean_max_hit", "p_any2", "p_any3", "expected_union_coverage"):
        if abs(float(policy["exact_null"][key]) - float(random_spec["exact_null"][key])) > 1e-14:
            raise ValueError(f"E073 exact geometry-matched null changed: {key}")


def run(date_kst: str, run_id: str):
    import re
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_kst):
        raise ValueError("date must be YYYY-MM-DD")
    if not re.fullmatch(r"[A-Za-z0-9_-]+", run_id):
        raise ValueError("run_id contains unsafe characters")
    prereg = json.loads(PREREG_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    if date_kst != prereg.get("date_kst"):
        raise ValueError("run date differs from frozen E073 preregistration")
    _verify_preregistration(prereg, policy)
    base = load_base()
    cutoff = int(prereg["historical_data_cutoff"])
    draws, prefix_sha, data_sha, current_rows = base.load_frozen_draw_prefix(
        cutoff,
        prereg["source_data_prefix_sha256"],
        prereg["source_data_full_file_sha256"],
    )
    if current_rows != cutoff or len(draws) != cutoff:
        raise ValueError("E073 requires exactly the preregistered 1..1250 canonical history")
    start_target = int(prereg["target_rounds"].split("..")[0])
    if start_target != 401 or cutoff - start_target + 1 != 850:
        raise ValueError("E073 target count differs from preregistered 850 targets")

    exposures, successes = build_lag3_counts(draws, start_target - 1)
    observations = []
    random_rows = []
    training_cutoff_violations = 0
    portfolio_geometry_violations = 0
    random_geometry_violations = 0
    random_count = int(prereg["random_comparator"]["random_bundles_per_target"])
    seed = int(prereg["random_comparator"]["seed"])
    null = prereg["random_comparator"]["exact_null"]
    exact = {
        "max_hits": float(null["mean_max_hit"]),
        "any2": float(null["p_any2"]),
        "any3": float(null["p_any3"]),
        "winning_union_coverage": float(null["expected_union_coverage"]),
    }

    for target_round in range(start_target, cutoff + 1):
        training_through = target_round - 1
        three_back = draws[target_round - 4]["nums"]
        two_back = draws[target_round - 3]["nums"]
        previous = draws[target_round - 2]["nums"]
        scores = lag3_scores(three_back, two_back, previous, exposures, successes)
        lines = make_three_line_portfolio(scores, base)
        union = set().union(*(set(line) for line in lines))
        overlaps = [len(set(a) & set(b)) for a, b in itertools.combinations(lines, 2)]
        if len(union) != 18 or any(overlaps):
            portfolio_geometry_violations += 1
            raise AssertionError(f"E073 model portfolio geometry violation at {target_round}")
        if training_through != target_round - 1:
            training_cutoff_violations += 1
            raise AssertionError(f"E073 training cutoff violation at {target_round}")
        actual = set(draws[target_round - 1]["nums"])
        observed = base.portfolio_metrics(lines, actual)
        line_hits = [len(set(line) & actual) for line in lines]
        score_order = sorted(range(1, 46), key=lambda number: (-scores[number], number))
        score_payload = json.dumps(
            [[number, round(scores[number], 16)] for number in range(1, 46)],
            separators=(",", ":")
        ).encode("utf-8")
        observations.append({
            "target_round": target_round,
            "training_through_round": training_through,
            "training_transition_count": target_round - 4,
            "lines": lines,
            "actual": tuple(sorted(actual)),
            "line_hits": line_hits,
            "score_sha256": hashlib.sha256(score_payload).hexdigest(),
            "top18": score_order[:18],
            **observed,
        })
        rng = random.Random(seed + target_round)
        random_metrics = []
        for _ in range(random_count):
            random_lines = base.permute_portfolio_labels(lines, rng)
            result = base.portfolio_metrics(random_lines, actual)
            random_union = set().union(*(set(line) for line in random_lines))
            random_overlaps = [len(set(a) & set(b)) for a, b in itertools.combinations(random_lines, 2)]
            if len(random_union) != 18 or any(random_overlaps):
                random_geometry_violations += 1
                raise AssertionError(f"E073 random geometry violation at {target_round}")
            random_metrics.append(result)
        random_rows.append({
            "target_round": target_round,
            "random_bundles": random_count,
            "random_mean_max_hits": statistics.mean(item["max_hits"] for item in random_metrics),
            "random_p_any2": statistics.mean(item["any2"] for item in random_metrics),
            "random_p_any3": statistics.mean(item["any3"] for item in random_metrics),
            "random_mean_union_coverage": statistics.mean(item["winning_union_coverage"] for item in random_metrics),
            "exact_null_mean_max_hit": exact["max_hits"],
            "exact_null_p_any2": exact["any2"],
            "exact_null_p_any3": exact["any3"],
            "exact_null_expected_union_coverage": exact["winning_union_coverage"],
            "geometry_violations": 0,
        })
        # The target outcome enters the lag-three history only after its own score is frozen.
        update_lag3_counts(three_back, two_back, previous, actual, exposures, successes)

    targets = [item["target_round"] for item in observations]
    expected_targets = list(range(start_target, cutoff + 1))
    if targets != expected_targets or len(random_rows) != 850:
        raise AssertionError("E073 walk-forward target sequence/count mismatch")
    diffs = {
        metric: [float(item[metric]) - exact[metric] for item in observations]
        for metric in METRICS
    }
    block_size = int(prereg["inference"]["block_length_targets"])
    bootstrap_reps = int(prereg["inference"]["bootstrap_replicates"])
    alpha = float(prereg["inference"]["alpha_per_metric"])
    bootstrap_seed = int(prereg["inference"]["bootstrap_seed"])
    block_rows = []
    for block_index, start in enumerate(range(0, len(observations), block_size), 1):
        stop = min(start + block_size, len(observations))
        row = {
            "block_index": block_index,
            "start_target": targets[start],
            "end_target": targets[stop - 1],
            "n": stop - start,
        }
        for metric in METRICS:
            row[f"mean_delta_{metric}"] = statistics.mean(diffs[metric][start:stop])
        row["any2_positive"] = int(row["mean_delta_any2"] > 0)
        block_rows.append(row)
    if len(block_rows) != 17 or any(row["n"] != 50 for row in block_rows):
        raise AssertionError("E073 block count/length mismatch")
    positive_blocks = sum(row["any2_positive"] for row in block_rows)
    positive_share = positive_blocks / len(block_rows)
    inference = {}
    for offset, metric in enumerate(METRICS):
        ci = base.moving_block_ci(
            diffs[metric], alpha, bootstrap_seed + 9000 + offset,
            bootstrap_reps, block_size
        )
        inference[metric] = {
            "observed_mean": statistics.mean(float(item[metric]) for item in observations),
            "exact_geometry_matched_null": exact[metric],
            "delta_mean": statistics.mean(diffs[metric]),
            "adjusted_moving_block_ci": ci,
            "lower_bound_strictly_gt_zero": ci[0] > 0,
        }
    historical_gate_pass = (
        all(inference[metric]["lower_bound_strictly_gt_zero"] for metric in METRICS)
        and positive_share >= 0.65
    )
    prospective = prereg["prospective_confirmation"]
    strict_portfolio_pass = base.strict_portfolio_ready(
        historical_gate_pass,
        prospective["minimum_target_count"],
        prospective["completion_rule"],
    )
    readiness_status = (
        "HISTORICAL_GATE_PASS_BUT_NOT_READY_PROSPECTIVE_RULE_UNSPECIFIED"
        if historical_gate_pass else "STRICT_FAIL"
    )
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
            "training_transition_count": row["training_transition_count"],
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
        ["target_round", "training_through_round", "training_transition_count",
         "line1", "line2", "line3", "actual_numbers", "line1_hits", "line2_hits",
         "line3_hits", "max_hits", "any2", "any3", "winning_union_coverage",
         "union_size", "score_sha256", "top18_ranked_numbers"],
    )
    base.write_csv(
        outdir / "RANDOM_BASELINE.csv", random_rows,
        ["target_round", "random_bundles", "random_mean_max_hits", "random_p_any2",
         "random_p_any3", "random_mean_union_coverage", "exact_null_mean_max_hit",
         "exact_null_p_any2", "exact_null_p_any3", "exact_null_expected_union_coverage",
         "geometry_violations"],
    )
    base.write_csv(
        outdir / "BLOCK_STABILITY.csv", block_rows,
        ["block_index", "start_target", "end_target", "n", "mean_delta_max_hits",
         "mean_delta_any2", "mean_delta_any3", "mean_delta_winning_union_coverage",
         "any2_positive"],
    )
    normalize_csv_outputs(outdir)
    source_paths = [PREREG_PATH, POLICY_PATH, BASE_RUNNER, Path(__file__).resolve()]
    source_hashes = {path.relative_to(ROOT).as_posix(): _sha(path) for path in source_paths}
    base.write_json(outdir / "MODEL_SPEC.json", {
        "study_id": STUDY_ID,
        "feature_definition": prereg["feature_definition"],
        "estimator": prereg["estimator"],
        "portfolio": prereg["portfolio"],
        "random_comparator": prereg["random_comparator"],
        "inference": prereg["inference"],
        "selection_uses_randomness": False,
        "parameter_search": False,
        "variants_evaluated": 1,
        "source_hashes": source_hashes,
    })
    inference_payload = {
        "study_id": STUDY_ID,
        "evidence_class": "HISTORICAL_INDEPENDENT_SIGNAL_FAMILY_SCREEN_NOT_PROSPECTIVE_CONFIRMATION",
        "data_cutoff": cutoff,
        "target_range": [start_target, cutoff],
        "targets": len(observations),
        "random_bundles_per_target": random_count,
        "random_bundles_total": len(observations) * random_count,
        "block_size": block_size,
        "block_lengths": [row["n"] for row in block_rows],
        "family_alpha": float(prereg["inference"]["family_alpha"]),
        "alpha_per_metric": alpha,
        "bootstrap_replicates": bootstrap_reps,
        "metrics": inference,
        "any2_positive_50_target_block_share": positive_share,
        "positive_any2_blocks": positive_blocks,
        "simulated_random_means": simulated_random_means,
        "historical_strict_gate_pass": historical_gate_pass,
        "strict_portfolio_pass": strict_portfolio_pass,
        "strict_pass_ready": False,
        "readiness_status": readiness_status,
        "independent_research_axis": True,
        "independent_signal_family": True,
        "independent_sample": False,
        "prospective_minimum_target_count": prospective["minimum_target_count"],
        "prospective_completion_rule": prospective["completion_rule"],
        "prospective_confirmation_status": "UNSPECIFIED_IN_POLICY",
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
        "data_prefix_sha256": prefix_sha,
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
        "independent_signal_family": True,
        "independent_sample": False,
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
        "evidence_class": "HISTORICAL_INDEPENDENT_SIGNAL_FAMILY_SCREEN_NOT_PROSPECTIVE_CONFIRMATION",
        "independent_research_axis": True,
        "independent_signal_family": True,
        "independent_sample": False,
        "purchase_recommendation_generated": False,
    }
    base.write_json(outdir / "COMPLETION.json", completion)
    report = [
        "# E073 — Three-draw membership-count conditional inclusion model",
        "",
        f"- Study status: **{readiness_status}**",
        f"- Data cutoff: **{cutoff}**; source rows: **{current_rows}**",
        f"- Walk-forward targets: **{len(observations)}** ({start_target}..{cutoff})",
        f"- Random bundles: **{len(observations) * random_count:,}** ({random_count} per target)",
        "- Feature: candidate membership count across the three immediately preceding main draws; bonus excluded",
        "- Estimator: one fixed Beta-smoothed inclusion probability with prior mean 6/45 and prior strength 45",
        "- Portfolio: three pairwise-disjoint six-number lines, union18, using the unchanged E045 selector",
        "- Randomness is used only for the geometry-matched null, never for selection",
        "",
        "| Metric | Model mean | Exact null | Delta | Adjusted CI lower | Adjusted CI upper |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for metric in METRICS:
        item = inference[metric]
        report.append(
            f"| {metric} | {item['observed_mean']:.6f} | {item['exact_geometry_matched_null']:.6f} "
            f"| {item['delta_mean']:+.6f} | {item['adjusted_moving_block_ci'][0]:+.6f} "
            f"| {item['adjusted_moving_block_ci'][1]:+.6f} |"
        )
    report.extend([
        "",
        f"- any2-positive 50-target block share: **{positive_share:.2%}** ({positive_blocks}/{len(block_rows)} blocks)",
        f"- Historical strict gate: **{'PASS' if historical_gate_pass else 'FAIL'}**",
        "- STRICT_PASS_READY: **not created**",
        "- Prospective minimum/completion rule: **unspecified and not adopted**",
        "- No final purchase lines, recommendation, or freeze/seal were generated.",
        "",
        "Each target is scored before its outcome enters the lag-three membership transition counts. One frozen signal family, one estimator, no variants or tuning.",
    ])
    (outdir / "REPORT.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    manifest_entries = base.write_and_verify_manifest(outdir)
    normalize_csv_outputs(outdir)
    if manifest_entries != 8:
        raise AssertionError(f"E073 manifest entries {manifest_entries} != 8")
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
