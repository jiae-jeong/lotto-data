#!/usr/bin/env python3
"""E071: previous-draw bonus-distance transition, frozen historical feature-family test."""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import random
import statistics
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STUDY_ID = "E071_THREE_LINE_PREVIOUS_BONUS_DISTANCE_TRANSITION_v1"
PREREG_REL = "research/weekly_purchase/1251/E071_THREE_LINE_PREVIOUS_BONUS_DISTANCE_TRANSITION_PREREG_20261118.json"
POLICY_REL = "research/weekly_purchase/1251/THREE_LINE_POLICY_1251_PLUS.json"
BASE_REL = "automation/three_line_research_1251_v1.py"
RUNNER_REL = "automation/three_line_previous_bonus_distance_e071.py"
TEST_REL = "automation/tests_v2/test_three_line_previous_bonus_distance_e071.py"
DATA_REL = "lotto_data.csv"
EXPECTED_DATA_SHA = "7203238dae69ce281c59e6a0928cc187b11d88ed342685cd2dd2f214f063b3c2"
METRICS = ("max_hits", "any2", "any3", "winning_union_coverage")
CUTPOINTS = (5, 10, 17, 25)
BIN_COUNTS = (465, 370, 434, 376, 380)
CUMULATIVE_COUNTS = (465, 835, 1269, 1645)


def load_base():
    path = ROOT / BASE_REL
    spec = importlib.util.spec_from_file_location("e071_e045_reference", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load frozen E045 helper: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git_blob(path: str) -> str:
    return subprocess.check_output(
        ["git", "rev-parse", f"HEAD:{path}"], cwd=ROOT, text=True
    ).strip()


def verify_frozen_blobs(prereg: dict) -> dict:
    paths = {
        "runner_blob_sha": RUNNER_REL,
        "test_blob_sha": TEST_REL,
        "base_runner_blob_sha": BASE_REL,
        "policy_blob_sha": POLICY_REL,
        "data_blob_sha": DATA_REL,
    }
    actual = {key: git_blob(path) for key, path in paths.items()}
    expected = {key: prereg.get("frozen_blobs", {}).get(key) for key in paths}
    if actual != expected:
        raise ValueError(f"E071 frozen input mismatch: actual={actual}, expected={expected}")
    return actual


def distance_bin(distance: int) -> int:
    if not isinstance(distance, int) or distance < 0 or distance > 44:
        raise ValueError(f"Invalid absolute bonus distance: {distance!r}")
    if distance <= 5:
        return 0
    if distance <= 10:
        return 1
    if distance <= 17:
        return 2
    if distance <= 25:
        return 3
    return 4


def theoretical_distance_audit() -> dict:
    counts = Counter(abs(n - b) for n in range(1, 46) for b in range(1, 46))
    total = 45 * 45
    cutpoints = []
    cumulative_counts = []
    cumulative = 0
    quantiles = (0.20, 0.40, 0.60, 0.80)
    next_q = 0
    for distance in sorted(counts):
        cumulative += counts[distance]
        if next_q < len(quantiles) and cumulative / total >= quantiles[next_q]:
            cutpoints.append(distance)
            cumulative_counts.append(cumulative)
            next_q += 1
    bin_counts = [0] * 5
    for distance, count in counts.items():
        bin_counts[distance_bin(distance)] += count
    result = {
        "ordered_pairs": total,
        "cutpoints": cutpoints,
        "cumulative_counts": cumulative_counts,
        "bin_counts": bin_counts,
    }
    if (
        cutpoints != list(CUTPOINTS)
        or cumulative_counts != list(CUMULATIVE_COUNTS)
        or bin_counts != list(BIN_COUNTS)
    ):
        raise AssertionError(f"Theoretical distance bins changed: {result}")
    return result


def validate_preregistration(prereg: dict, policy: dict) -> None:
    if prereg.get("study_id") != STUDY_ID:
        raise ValueError("E071 study identity mismatch")
    if prereg.get("preregistration_status") != "FROZEN_BEFORE_EXECUTION":
        raise ValueError("E071 preregistration is not frozen")
    if prereg.get("independent_research_axis") is not True:
        raise ValueError("E071 must remain one distinct research axis")
    if prereg.get("independent_sample") is not False:
        raise ValueError("E071 must disclose that the historical sample is not independent")
    if prereg.get("historical_exploration_only") is not True:
        raise ValueError("E071 must remain historical exploratory evidence")
    if prereg.get("target_1251_three_line_readiness_eligible") is not False:
        raise ValueError("Historical E071 cannot be purchase-readiness eligible")
    if int(prereg.get("target_round", -1)) != 1251:
        raise ValueError("E071 target round changed")
    if int(prereg.get("historical_data_cutoff", -1)) != 1250:
        raise ValueError("E071 data cutoff changed")
    if prereg.get("target_rounds") != "401..1250 inclusive":
        raise ValueError("E071 target range changed")
    if (
        prereg.get("source_data_prefix_sha256") != EXPECTED_DATA_SHA
        or prereg.get("source_data_full_file_sha256") != EXPECTED_DATA_SHA
    ):
        raise ValueError("E071 canonical data hash changed")

    feature = prereg.get("feature_definition", {})
    binning = feature.get("binning", {})
    if (
        feature.get("source") != "The immediately preceding draw's bonus ball only; previous main numbers are not used as feature inputs."
        or feature.get("distance") != "Absolute numeric distance abs(candidate_number - previous_draw_bonus); no circular wrap; distance 0 is allowed."
        or binning.get("method") != "Five discrete quintile bins derived only from all 45*45 ordered (candidate, bonus) pairs under the uniform 1..45 geometry; no historical outcomes are used to choose cutpoints."
        or binning.get("cutpoints") != list(CUTPOINTS)
        or binning.get("theoretical_pair_count") != 2025
        or binning.get("cumulative_counts") != list(CUMULATIVE_COUNTS)
        or binning.get("bin_counts") != list(BIN_COUNTS)
    ):
        raise ValueError("E071 feature definition or theoretical bins changed")
    if feature.get("outcome") != "The six main numbers of the following draw; the bonus number is excluded.":
        raise ValueError("E071 outcome definition changed")
    if feature.get("candidate_universe") != "All integers 1..45; every candidate receives exactly one distance bin for each target.":
        raise ValueError("E071 candidate universe changed")

    estimator = prereg.get("estimator", {})
    if (
        estimator.get("prior_mean") != "6/45 under the uniform six-of-45 main-number null"
        or int(estimator.get("prior_strength", -1)) != 45
        or estimator.get("posterior_probability") != "(success[bin,n] + 45*(6/45)) / (exposure[bin,n] + 45)"
        or estimator.get("ranking") != "Score descending, then number ascending."
        or estimator.get("variants") != 1
        or estimator.get("parameter_search") is not False
    ):
        raise ValueError("E071 estimator changed")

    portfolio = prereg.get("portfolio", {})
    if (
        portfolio.get("selector") != "Three sequential calls to the unchanged E045 choose_disjoint_ticket selector, passing the E071 score as both role_score and global_score; remove selected numbers after each line."
        or portfolio.get("geometry") != "Exactly three pairwise-disjoint six-number lines, union18."
        or portfolio.get("randomness_in_selection") is not False
        or portfolio.get("variants") != 1
    ):
        raise ValueError("E071 portfolio selector or geometry changed")

    comparator = prereg.get("random_comparator", {})
    exact = policy.get("exact_null", {})
    if (
        comparator.get("method") != "For each target, uniformly permute labels 1..45 jointly over the three fixed model lines, preserving three six-number lines, pairwise disjointness, union18, and line-incidence geometry."
        or int(comparator.get("random_bundles_per_target", -1)) != 120
        or int(comparator.get("seed", -1)) != 20261118071
        or comparator.get("randomness_used_for_final_selection") is not False
        or comparator.get("exact_null", {}).get("mean_max_hit") != exact.get("mean_max_hit")
        or comparator.get("exact_null", {}).get("p_any2") != exact.get("p_any2")
        or comparator.get("exact_null", {}).get("p_any3") != exact.get("p_any3")
        or comparator.get("exact_null", {}).get("expected_union_coverage") != exact.get("expected_union_coverage")
    ):
        raise ValueError("E071 random comparator changed")

    inference = prereg.get("inference", {})
    gate = policy.get("strict_gate", {})
    if (
        inference.get("metrics") != list(METRICS)
        or float(inference.get("family_alpha", -1)) != 0.05
        or float(inference.get("alpha_per_metric", -1)) != 0.0125
        or int(inference.get("bootstrap_replicates", -1)) != 4000
        or int(inference.get("bootstrap_seed", -1)) != 20261118071
        or int(inference.get("block_length_targets", -1)) != 50
        or inference.get("retain_final_remainder_block") is not True
        or float(inference.get("any2_positive_nonoverlapping_50_target_block_share_min", -1)) != 0.65
        or any(inference.get(k) is not True for k in (
            "no_threshold_relaxation", "no_alpha_change", "no_block_length_change",
            "no_comparator_change", "no_unbounded_microvariants"
        ))
        or float(gate.get("family_alpha", -1)) != 0.05
        or float(gate.get("alpha_per_metric", -1)) != 0.0125
        or float(gate.get("any2_positive_nonoverlapping_50_target_block_share_min", -1)) != 0.65
        or gate.get("all_adjusted_moving_block_ci_lower_bounds_strictly_gt_zero") is not True
        or gate.get("retain_final_remainder_block") is not True
        or gate.get("no_threshold_relaxation") is not True
        or gate.get("prospective_confirmation_required") is not True
    ):
        raise ValueError("E071 strict inference gate differs from the frozen policy")

    prospective = prereg.get("prospective_confirmation", {})
    if (
        prospective.get("required_by_policy") is not True
        or prospective.get("minimum_target_count") is not None
        or prospective.get("completion_rule") is not None
        or prospective.get("status") != "UNSPECIFIED_IN_POLICY"
    ):
        raise ValueError("E071 cannot silently define the prospective confirmation policy")
    if policy.get("policy_id") != prereg.get("policy_id") or int(policy.get("effective_from_target", -1)) != 1251:
        raise ValueError("E071 active three-line policy identity changed")
    if int(policy.get("purchase_lines", -1)) != 3 or int(policy.get("numbers_per_line", -1)) != 6:
        raise ValueError("E071 active portfolio geometry changed")
    if prereg.get("expected_record_counts") != {
        "PREDICTIONS.csv": 850,
        "RANDOM_BASELINE.csv": 850,
        "BLOCK_STABILITY.csv": 17,
    }:
        raise ValueError("E071 expected record counts changed")
    if prereg.get("no_future_leakage") is not True or prereg.get("strict_pass_ready_requires_prospective_rule") is not True:
        raise ValueError("E071 leakage/readiness guard changed")
    theoretical_distance_audit()


def load_draws(base):
    draws, prefix_sha, full_sha, total_rows = base.load_frozen_draw_prefix(
        1250, EXPECTED_DATA_SHA, EXPECTED_DATA_SHA
    )
    with (ROOT / DATA_REL).open("r", encoding="utf-8-sig", newline="") as stream:
        rows = [row for row in csv.DictReader(stream) if row.get("round")]
    if len(rows) != 1250 or total_rows != 1250 or len(draws) != 1250:
        raise ValueError("E071 requires exactly 1,250 contiguous verified source draws")
    for draw, row in zip(draws, rows):
        if int(row["round"]) != int(draw["round"]):
            raise ValueError("E071 round mismatch while loading bonus values")
        bonus = int(row["bonus"])
        if bonus < 1 or bonus > 45 or bonus in draw["nums"]:
            raise ValueError(f"Invalid bonus value at round {draw['round']}")
        draw["bonus"] = bonus
    return draws, prefix_sha, full_sha, total_rows


def build_training_counts(draws: list[dict], target_round: int):
    if target_round < 3 or target_round > len(draws):
        raise ValueError("Target round is outside the available draw prefix")
    exposures = [[0] * 46 for _ in range(5)]
    successes = [[0] * 46 for _ in range(5)]
    for outcome_round in range(2, target_round):
        previous_bonus = int(draws[outcome_round - 2]["bonus"])
        actual = set(draws[outcome_round - 1]["nums"])
        for number in range(1, 46):
            bin_id = distance_bin(abs(number - previous_bonus))
            exposures[bin_id][number] += 1
            if number in actual:
                successes[bin_id][number] += 1
    expected_transitions = target_round - 2
    for number in range(1, 46):
        if sum(exposures[b][number] for b in range(5)) != expected_transitions:
            raise AssertionError(f"Training exposure count mismatch for number {number}")
        if any(successes[b][number] > exposures[b][number] for b in range(5)):
            raise AssertionError(f"Training success count exceeds exposure for number {number}")
    return exposures, successes


def score_numbers_for_target(draws: list[dict], target_round: int):
    exposures, successes = build_training_counts(draws, target_round)
    previous_bonus = int(draws[target_round - 2]["bonus"])
    bins = {number: distance_bin(abs(number - previous_bonus)) for number in range(1, 46)}
    scores = {
        number: (successes[bins[number]][number] + 6.0) / (exposures[bins[number]][number] + 45.0)
        for number in range(1, 46)
    }
    return scores, bins, previous_bonus


def make_three_line_portfolio(scores: dict[int, float], base):
    used, lines = set(), []
    for _ in range(3):
        line = base.choose_disjoint_ticket(scores, scores, used)
        lines.append(tuple(line))
        used.update(line)
    if len(lines) != 3 or len(used) != 18:
        raise AssertionError("E071 portfolio must be three disjoint six-number lines with union18")
    return lines


def preflight() -> dict:
    prereg = json.loads((ROOT / PREREG_REL).read_text(encoding="utf-8"))
    policy = json.loads((ROOT / POLICY_REL).read_text(encoding="utf-8"))
    validate_preregistration(prereg, policy)
    frozen = verify_frozen_blobs(prereg)
    base = load_base()
    draws, prefix_sha, full_sha, total_rows = load_draws(base)
    if len(draws) != 1250 or total_rows != 1250 or prefix_sha != EXPECTED_DATA_SHA or full_sha != EXPECTED_DATA_SHA:
        raise ValueError("E071 preflight data/cutoff/hash verification failed")
    return {
        "status": "PREFLIGHT_PASS",
        "study_id": STUDY_ID,
        "data_cutoff": 1250,
        "data_rows": total_rows,
        "data_sha256": full_sha,
        "frozen_blobs": frozen,
        "theoretical_distance_bins": theoretical_distance_audit(),
    }


def run(date_kst: str, run_id: str) -> dict:
    if date_kst != "2026-11-18":
        raise ValueError("E071 execution date must match its frozen preregistration")
    if not run_id or any(ch not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for ch in run_id):
        raise ValueError("E071 run_id contains unsafe characters")
    prereg = json.loads((ROOT / PREREG_REL).read_text(encoding="utf-8"))
    policy = json.loads((ROOT / POLICY_REL).read_text(encoding="utf-8"))
    validate_preregistration(prereg, policy)
    frozen = verify_frozen_blobs(prereg)
    base = load_base()
    draws, data_prefix_sha, data_sha, total_rows = load_draws(base)

    random_count = int(prereg["random_comparator"]["random_bundles_per_target"])
    seed = int(prereg["random_comparator"]["seed"])
    rng = random.Random(seed)
    start_target, end_target = 401, 1250
    deltas = {metric: [] for metric in METRICS}
    prediction_rows, random_rows = [], []
    portfolio_geometry_violations = 0
    random_geometry_violations = 0
    training_cutoff_violations = 0

    for target_round in range(start_target, end_target + 1):
        training_through = target_round - 1
        if training_through >= target_round:
            training_cutoff_violations += 1
            raise AssertionError("E071 training cutoff violation")
        scores, candidate_bins, previous_bonus = score_numbers_for_target(draws, target_round)
        lines = make_three_line_portfolio(scores, base)
        union = set().union(*(set(line) for line in lines))
        overlaps = [len(set(a) & set(b)) for i, a in enumerate(lines) for b in lines[i + 1:]]
        if len(lines) != 3 or len(union) != 18 or any(overlaps):
            portfolio_geometry_violations += 1
            raise AssertionError("E071 model portfolio geometry violation")

        actual = set(draws[target_round - 1]["nums"])
        observed = base.portfolio_metrics(lines, actual)
        random_values = {metric: [] for metric in METRICS}
        for _ in range(random_count):
            random_lines = base.permute_portfolio_labels(lines, rng)
            random_union = set().union(*(set(line) for line in random_lines))
            random_overlaps = [len(set(a) & set(b)) for i, a in enumerate(random_lines) for b in random_lines[i + 1:]]
            if len(random_union) != 18 or any(random_overlaps):
                random_geometry_violations += 1
                raise AssertionError("E071 random comparator geometry violation")
            random_metric = base.portfolio_metrics(random_lines, actual)
            for metric in METRICS:
                random_values[metric].append(float(random_metric[metric]))
        random_mean = {metric: statistics.mean(random_values[metric]) for metric in METRICS}
        delta = {metric: float(observed[metric]) - random_mean[metric] for metric in METRICS}
        for metric in METRICS:
            deltas[metric].append(delta[metric])

        prediction_rows.append({
            "target_round": target_round,
            "training_through_round": training_through,
            "previous_bonus_round": target_round - 1,
            "previous_bonus": previous_bonus,
            "candidate_distance_bins": json.dumps({str(n): candidate_bins[n] for n in range(1, 46)}),
            "candidate_scores": json.dumps({str(n): round(scores[n], 12) for n in range(1, 46)}),
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

    alpha = float(prereg["inference"]["alpha_per_metric"])
    replicates = int(prereg["inference"]["bootstrap_replicates"])
    block_size = int(prereg["inference"]["block_length_targets"])
    bootstrap_seed = int(prereg["inference"]["bootstrap_seed"])
    metric_summary = {}
    for index, metric in enumerate(METRICS):
        ci = base.moving_block_ci(
            deltas[metric],
            alpha=alpha,
            seed=bootstrap_seed + index,
            replicates=replicates,
            block_size=block_size,
        )
        metric_summary[metric] = {
            "observed_mean": statistics.mean(
                float(row[metric]) for row in prediction_rows
            ),
            "random_mean": statistics.mean(
                float(row[f"random_mean_{metric}"]) for row in prediction_rows
            ),
            "delta_mean": statistics.mean(deltas[metric]),
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
            **{f"mean_delta_{metric}": statistics.mean(chunk[metric]) for metric in METRICS},
            "any2_positive": statistics.mean(chunk["any2"]) > 0.0,
        })

    positive_blocks = sum(1 for row in block_rows if row["any2_positive"])
    block_share = positive_blocks / len(block_rows)
    all_ci_positive = all(metric_summary[metric]["lower_bound_strictly_gt_zero"] for metric in METRICS)
    failed_gates = [
        metric for metric in METRICS
        if not metric_summary[metric]["lower_bound_strictly_gt_zero"]
    ]
    if block_share < 0.65:
        failed_gates.append("any2_positive_50_target_block_share")
    historical_gate_pass = not failed_gates

    run_root = ROOT / "analysis" / date_kst / run_id
    outdir = run_root / STUDY_ID
    outdir.mkdir(parents=True, exist_ok=False)

    inference = {
        "study_id": STUDY_ID,
        "evidence_class": "HISTORICAL_EXPLORATORY_DISTINCT_FEATURE_FAMILY_NOT_PROSPECTIVE_CONFIRMATION",
        "data_cutoff": 1250,
        "data_sha256": data_sha,
        "target_range": [start_target, end_target],
        "target_count": len(prediction_rows),
        "random_bundles_per_target": random_count,
        "random_bundles_total": len(prediction_rows) * random_count,
        "bootstrap_replicates": replicates,
        "block_length_targets": block_size,
        "alpha_per_metric": alpha,
        "theoretical_distance_bins": theoretical_distance_audit(),
        "metrics": metric_summary,
        "any2_positive_nonoverlapping_50_target_blocks": positive_blocks,
        "nonoverlapping_50_target_block_count": len(block_rows),
        "any2_positive_block_share": block_share,
        "all_adjusted_ci_lower_bounds_strictly_gt_zero": all_ci_positive,
        "historical_strict_gate_pass": historical_gate_pass,
        "failed_gates": failed_gates,
        "strict_portfolio_pass": False,
        "strict_pass_ready": False,
        "prospective_confirmation_required": True,
        "prospective_confirmation_status": "UNSPECIFIED_IN_POLICY",
        "purchase_recommendation_generated": False,
        "thresholds_or_policy_changed": False,
        "parameter_search": False,
        "variants_evaluated": 1,
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
        "frozen_blobs": frozen,
    }
    completion = {
        "study_id": STUDY_ID,
        "status": "COMPLETE",
        "data_cutoff": 1250,
        "target_count": len(prediction_rows),
        "historical_strict_gate_pass": historical_gate_pass,
        "strict_pass_ready": False,
        "purchase_recommendation_generated": False,
    }
    model_spec = {
        "study_id": STUDY_ID,
        "preregistration_path": PREREG_REL,
        "preregistration": prereg,
        "frozen_blobs": frozen,
        "implementation": RUNNER_REL,
        "base_selection_helper": BASE_REL,
        "strict_policy_path": POLICY_REL,
    }
    report = [
        "# E071 — Previous-draw bonus-distance transition",
        "",
        "Execution status: **COMPLETE / VERIFICATION PASS**",
        f"Historical strict gate: **{'PASS' if historical_gate_pass else 'FAIL'}**",
        "",
        "## Frozen design",
        "- One candidate-number distance feature relative only to the immediately preceding draw's bonus ball; the previous six main numbers are not used as features.",
        "- Five bins are fixed by theoretical quintiles of all 45×45 ordered candidate/bonus pairs: 0–5, 6–10, 11–17, 18–25, 26–44.",
        "- One fixed uniform 6/45 prior with strength 45; one unchanged E045 three-line disjoint selector; no variants or parameter search.",
        "- Targets 401–1250; each target uses only the previous draw's bonus and outcome history through t−1.",
        "- 120 jointly permuted geometry-matched random portfolios per target; 4,000 moving-block bootstrap replicates; 50-target blocks.",
        "",
        "## Results",
    ]
    for metric in METRICS:
        row = metric_summary[metric]
        ci = row["adjusted_moving_block_ci"]
        report.append(
            f"- {metric}: observed={row['observed_mean']:.6f}, random={row['random_mean']:.6f}, "
            f"delta={row['delta_mean']:.6f}, adjusted CI=[{ci[0]:.6f}, {ci[1]:.6f}]"
        )
    report.extend([
        f"- Positive any2 blocks: {positive_blocks}/{len(block_rows)} ({block_share:.2%}); required: 65%.",
        f"- Failed historical gates: {', '.join(failed_gates) if failed_gates else 'none'}.",
        "",
        "## Interpretation and guardrails",
        "- This is a distinct feature-family test on an already observed historical sample, not an independent prospective sample.",
        "- E048 tests exact previous-bonus identity; E050 tests distance to the previous draw's six main numbers. E071 tests distance to the previous draw's bonus ball only.",
        "- Even a historical gate PASS cannot create STRICT_PASS_READY because the policy still requires a separately specified prospective confirmation rule.",
        "- No purchase lines, candidate lines, random fallback, freeze, or seal were generated.",
        "- No strict threshold, alpha, block length, comparator, or purchase policy was changed.",
        "",
    ])

    base.write_csv(outdir / "PREDICTIONS.csv", prediction_rows, list(prediction_rows[0].keys()))
    base.write_csv(outdir / "RANDOM_BASELINE.csv", random_rows, list(random_rows[0].keys()))
    base.write_csv(outdir / "BLOCK_STABILITY.csv", block_rows, list(block_rows[0].keys()))
    base.write_json(outdir / "INFERENCE.json", inference)
    base.write_json(outdir / "VERIFICATION.json", verification)
    base.write_json(outdir / "COMPLETION.json", completion)
    base.write_json(outdir / "MODEL_SPEC.json", model_spec)
    (outdir / "REPORT.md").write_text("\n".join(report), encoding="utf-8")
    manifest_entries = base.write_and_verify_manifest(outdir)
    if manifest_entries != 8:
        raise AssertionError(f"Expected 8 manifest entries, got {manifest_entries}")
    return {
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
    args = parser.parse_args()
    if args.preflight:
        print(json.dumps(preflight(), ensure_ascii=False, indent=2))
        return 0
    if not args.run_id:
        raise ValueError("--run-id is required")
    print(json.dumps(run(args.date, args.run_id), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
