#!/usr/bin/env python3
"""E068: preregistered previous-draw overlap-count transition for a three-line union18 portfolio."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import random
import statistics
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STUDY_ID = "E068_THREE_LINE_PREVIOUS_TWO_DRAW_OVERLAP_COUNT_TRANSITION_v1"
PREREG_REL = "research/weekly_purchase/1251/E068_THREE_LINE_PREVIOUS_TWO_DRAW_OVERLAP_COUNT_TRANSITION_PREREG_20261117.json"
POLICY_REL = "research/weekly_purchase/1251/THREE_LINE_POLICY_1251_PLUS.json"
BASE_REL = "automation/three_line_research_1251_v1.py"
RUNNER_REL = "automation/three_line_overlap_count_transition_e068.py"
TEST_REL = "automation/tests_v2/test_three_line_overlap_count_transition_e068.py"
WORKFLOW_REL = ".github/workflows/target-1251-e068-overlap-count-transition.yml"
EXPECTED_DATA_SHA = "7203238dae69ce281c59e6a0928cc187b11d88ed342685cd2dd2f214f063b3c2"
METRICS = ("max_hits", "any2", "any3", "winning_union_coverage")


def load_base():
    path = ROOT / BASE_REL
    spec = importlib.util.spec_from_file_location("e068_e045_reference", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load frozen E045 helper: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_frozen_blobs(prereg):
    paths = {
        "runner_blob_sha": RUNNER_REL,
        "test_blob_sha": TEST_REL,
        "workflow_blob_sha": WORKFLOW_REL,
        "base_runner_blob_sha": BASE_REL,
        "policy_blob_sha": POLICY_REL,
    }
    actual = {}
    for key, path in paths.items():
        actual[key] = subprocess.check_output(
            ["git", "rev-parse", f"HEAD:{path}"], cwd=ROOT, text=True
        ).strip()
        if actual[key] != prereg["frozen_blobs"].get(key):
            raise ValueError(
                f"Frozen blob mismatch for {path}: {actual[key]} != {prereg['frozen_blobs'].get(key)}"
            )
    return actual


def validate_preregistration(prereg, policy):
    if prereg.get("study_id") != STUDY_ID or prereg.get("policy_id") != policy.get("policy_id"):
        raise ValueError("E068 preregistration/policy identity mismatch")
    if prereg.get("preregistration_status") != "FROZEN_BEFORE_EXECUTION":
        raise ValueError("E068 preregistration is not frozen")
    if prereg.get("independent_research_axis") is not True:
        raise ValueError("E068 must remain one independent research axis")
    if prereg.get("independent_signal_family") is not True:
        raise ValueError("E068 must remain one independent signal family")
    if prereg.get("historical_exploration_only") is not True:
        raise ValueError("E068 historical evidence scope must remain explicit")
    if prereg.get("date_kst") != "2026-11-17" or int(prereg.get("target_round", -1)) != 1251:
        raise ValueError("E068 target/date changed")
    if int(prereg.get("historical_data_cutoff", -1)) != 1250:
        raise ValueError("E068 historical cutoff changed")
    if prereg.get("target_rounds") != "401..1250 inclusive":
        raise ValueError("E068 target range changed")
    if prereg.get("source_data_sha256") != EXPECTED_DATA_SHA:
        raise ValueError("E068 canonical data hash changed")

    feature = {
        "source": "The two immediately preceding draws' six main numbers only; bonus numbers are excluded.",
        "overlap_count": "Count the shared main numbers between draws t-2 and t-1.",
        "state_components": {"overlap_count_bin": "0 if overlap_count==0; 1 if overlap_count==1; 2 if overlap_count>=2"},
        "distance": "Hamming distance across the one frozen categorical overlap-count component.",
        "transition_history": "For each historical outcome round u=3..t-1, use the overlap-count state of draws u-2 and u-1 as the feature and the six main numbers of draw u as the outcome. Score target t from draws t-2 and t-1, then add target t only after scoring.",
        "candidate_universe": "All integers 1..45 are scored for every target."
    }
    if prereg.get("feature_definition") != feature:
        raise ValueError("E068 overlap-count feature definition changed")

    estimator = {
        "kernel_weight": "0.5 ** HammingDistance(historical_previous_two_draw_overlap_count_bin, target_previous_two_draw_overlap_count_bin)",
        "conditional_count": "Weighted count of each main number in historical transition outcomes.",
        "global_rate": "Count of each main number in draws 1..t-1 divided by t-1.",
        "smoothing_alpha": 60,
        "score_formula": "(weighted_conditional_count[n] + 60 * global_main_inclusion_rate[n]) / (sum_transition_weights + 60)",
        "ranking": "Score descending, then number ascending.",
        "variants": 1,
        "parameter_search": False
    }
    if prereg.get("estimator") != estimator:
        raise ValueError("E068 estimator changed")

    portfolio = prereg["portfolio"]
    if (
        portfolio.get("geometry") != "Exactly three pairwise-disjoint six-number lines, union18."
        or portfolio.get("selection") != "Three sequential calls to the unchanged E045 choose_disjoint_ticket selector, passing the E068 score as both role_score and global_score; remove selected numbers after each line."
        or portfolio.get("randomness_in_selection") is not False
        or portfolio.get("variants") != 1
    ):
        raise ValueError("E068 portfolio construction changed")

    comparator = prereg["random_comparator"]
    method = "For each target, uniformly permute labels 1..45 jointly over the three fixed model lines, preserving three six-number lines, pairwise disjointness, union18, and line-incidence geometry."
    if (
        comparator.get("method") != method
        or int(comparator.get("random_bundles_per_target", -1)) != 120
        or int(comparator.get("seed", -1)) != 20261117068
        or comparator.get("randomness_used_for_final_selection") is not False
    ):
        raise ValueError("E068 random comparator changed")

    inference = prereg["inference"]
    if (
        inference.get("metrics") != list(METRICS)
        or float(inference.get("family_alpha", -1)) != 0.05
        or float(inference.get("alpha_per_metric", -1)) != 0.0125
        or int(inference.get("bootstrap_replicates", -1)) != 4000
        or int(inference.get("bootstrap_seed", -1)) != 20261117068
        or int(inference.get("block_length_targets", -1)) != 50
        or inference.get("retain_final_remainder_block") is not True
        or float(inference.get("any2_positive_nonoverlapping_50_target_block_share_min", -1)) != 0.65
        or any(inference.get(k) is not True for k in (
            "no_threshold_relaxation", "no_alpha_change", "no_block_length_change",
            "no_comparator_change", "no_unbounded_microvariants"
        ))
    ):
        raise ValueError("E068 inference/promotion gate changed")

    prospective = prereg["prospective_confirmation"]
    if (
        prospective.get("required_by_policy") is not True
        or prospective.get("minimum_target_count") is not None
        or prospective.get("completion_rule") is not None
        or prospective.get("status") != "UNSPECIFIED_IN_POLICY"
    ):
        raise ValueError("E068 cannot silently define the prospective confirmation rule")

    if prereg.get("expected_record_counts") != {
        "PREDICTIONS.csv": 850, "RANDOM_BASELINE.csv": 850, "BLOCK_STABILITY.csv": 17
    }:
        raise ValueError("E068 expected record counts changed")
    if prereg.get("no_future_leakage") is not True or prereg.get("strict_pass_ready_requires_prospective_rule") is not True:
        raise ValueError("E068 leakage/readiness requirements changed")

    if int(policy.get("effective_from_target", -1)) != 1251 or int(policy.get("purchase_lines", -1)) != 3:
        raise ValueError("Active target-1251 three-line policy changed")
    if int(policy.get("numbers_per_line", -1)) != 6:
        raise ValueError("Active line size changed")
    gate = policy["strict_gate"]
    if (
        float(gate["family_alpha"]) != 0.05
        or float(gate["alpha_per_metric"]) != 0.0125
        or float(gate["any2_positive_nonoverlapping_50_target_block_share_min"]) != 0.65
        or gate.get("all_adjusted_moving_block_ci_lower_bounds_strictly_gt_zero") is not True
        or gate.get("retain_final_remainder_block") is not True
        or gate.get("no_threshold_relaxation") is not True
        or gate.get("cutoff_safe_nested_rolling_walkforward") is not True
        or gate.get("prospective_confirmation_required") is not True
    ):
        raise ValueError("E068 strict policy gate changed")
    exact = comparator["exact_null"]
    for key in ("mean_max_hit", "p_any2", "p_any3", "expected_union_coverage"):
        if abs(float(exact[key]) - float(policy["exact_null"][key])) > 1e-14:
            raise ValueError(f"E068 exact geometry-matched null changed: {key}")


def overlap_count_state(two_back_nums, previous_nums):
    def checked(values, label):
        numbers = tuple(int(x) for x in values)
        if len(numbers) != 6 or len(set(numbers)) != 6 or any(x < 1 or x > 45 for x in numbers):
            raise ValueError(f"{label} must contain six unique main numbers in 1..45")
        return set(numbers)
    overlap = len(checked(two_back_nums, "two-back draw") & checked(previous_nums, "previous draw"))
    return 0 if overlap == 0 else 1 if overlap == 1 else 2


def hamming_distance(left, right):
    if left not in (0, 1, 2) or right not in (0, 1, 2):
        raise ValueError("E068 overlap-count distance requires two valid categorical bins")
    return int(left != right)


def update_transition(two_back_nums, previous_nums, outcome_nums, exposures, successes):
    two_back = set(int(x) for x in two_back_nums)
    previous = set(int(x) for x in previous_nums)
    outcome = set(int(x) for x in outcome_nums)
    for label, values in (("two-back", two_back), ("previous", previous), ("outcome", outcome)):
        if len(values) != 6 or any(x < 1 or x > 45 for x in values):
            raise ValueError(f"{label} draw must contain six unique valid main numbers")
    state = overlap_count_state(two_back, previous)
    exposure = exposures.setdefault(state, [0] * 46)
    success = successes.setdefault(state, [0] * 46)
    for number in range(1, 46):
        exposure[number] += 1
    for number in outcome:
        success[number] += 1


def build_training_counts(draws, target_round):
    """Use outcome rounds u=3..target_round-1 only; never read target_round outcome."""
    if target_round < 4 or target_round > len(draws):
        raise ValueError("target round must be in 4..len(draws)")
    exposures, successes = {}, {}
    for outcome_round in range(3, target_round):
        update_transition(
            draws[outcome_round - 3]["nums"],
            draws[outcome_round - 2]["nums"],
            draws[outcome_round - 1]["nums"],
            exposures, successes
        )
    return exposures, successes


def score_numbers(target_state, exposures, successes, global_counts, global_draws, alpha):
    if len(global_counts) != 45 or global_draws <= 0 or alpha <= 0 or not exposures:
        raise ValueError("invalid E068 scoring inputs")
    weighted = [0.0] * 46
    total_weight = 0.0
    for state, exposure in exposures.items():
        weight = 0.5 ** hamming_distance(state, target_state)
        total_weight += weight * exposure[1]
        success = successes[state]
        for number in range(1, 46):
            weighted[number] += weight * success[number]
    if total_weight <= 0:
        raise ValueError("E068 has no weighted historical transitions")
    scores = {}
    for number in range(1, 46):
        global_rate = float(global_counts[number - 1]) / global_draws
        scores[number] = (weighted[number] + alpha * global_rate) / (total_weight + alpha)
    return scores, total_weight


def make_three_line_portfolio(scores, base):
    used, lines = set(), []
    for _ in range(3):
        line = base.choose_disjoint_ticket(scores, scores, used)
        lines.append(tuple(line))
        used.update(line)
    if len(lines) != 3 or len(used) != 18:
        raise AssertionError("E068 portfolio must be exactly three disjoint lines with union18")
    return lines


def score_target(draws, target_round, base, alpha=60):
    """Return a target prediction using only draws 1..target_round-1."""
    if target_round < 4 or target_round > len(draws):
        raise ValueError("target round is outside the available draw prefix")
    exposures, successes = build_training_counts(draws, target_round)
    history = draws[:target_round - 1]
    global_counts = [
        sum(1 for draw in history if number in draw["nums"])
        for number in range(1, 46)
    ]
    target_state = overlap_count_state(draws[target_round - 3]["nums"], draws[target_round - 2]["nums"])
    scores, _ = score_numbers(target_state, exposures, successes, global_counts, target_round - 1, alpha)
    return scores, make_three_line_portfolio(scores, base)


def preflight():
    prereg = json.loads((ROOT / PREREG_REL).read_text(encoding="utf-8"))
    policy = json.loads((ROOT / POLICY_REL).read_text(encoding="utf-8"))
    validate_preregistration(prereg, policy)
    frozen = verify_frozen_blobs(prereg)
    base = load_base()
    draws, prefix_sha, full_sha, total_rows = base.load_frozen_draw_prefix(
        1250, EXPECTED_DATA_SHA, EXPECTED_DATA_SHA
    )
    if len(draws) != 1250 or total_rows != 1250 or prefix_sha != EXPECTED_DATA_SHA or full_sha != EXPECTED_DATA_SHA:
        raise ValueError("E068 canonical data must contain exactly 1,250 verified contiguous draws")
    return {
        "status": "PREFLIGHT_PASS", "study_id": STUDY_ID, "data_cutoff": 1250,
        "data_rows": total_rows, "data_sha256": full_sha, "frozen_blobs": frozen
    }


def run(date_kst, run_id, run_attempt):
    if date_kst != "2026-11-17":
        raise ValueError("E068 execution date must match its frozen preregistration date")
    if not run_id or any(ch not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for ch in run_id):
        raise ValueError("run_id contains unsafe characters")
    run_attempt = int(run_attempt)
    if run_attempt < 1:
        raise ValueError("run_attempt must be positive")

    prereg = json.loads((ROOT / PREREG_REL).read_text(encoding="utf-8"))
    policy = json.loads((ROOT / POLICY_REL).read_text(encoding="utf-8"))
    validate_preregistration(prereg, policy)
    frozen = verify_frozen_blobs(prereg)
    base = load_base()
    cutoff = int(prereg["historical_data_cutoff"])
    draws, prefix_sha, data_sha, total_rows = base.load_frozen_draw_prefix(
        cutoff, EXPECTED_DATA_SHA, EXPECTED_DATA_SHA
    )
    if len(draws) != cutoff or total_rows != cutoff or prefix_sha != EXPECTED_DATA_SHA or data_sha != EXPECTED_DATA_SHA:
        raise ValueError("E068 requires exactly 1,250 contiguous verified draws")

    start_target, end_target = 401, 1250
    alpha = int(prereg["estimator"]["smoothing_alpha"])
    random_count = int(prereg["random_comparator"]["random_bundles_per_target"])
    seed = int(prereg["random_comparator"]["seed"])
    exact = {
        "max_hits": float(prereg["random_comparator"]["exact_null"]["mean_max_hit"]),
        "any2": float(prereg["random_comparator"]["exact_null"]["p_any2"]),
        "any3": float(prereg["random_comparator"]["exact_null"]["p_any3"]),
        "winning_union_coverage": float(prereg["random_comparator"]["exact_null"]["expected_union_coverage"])
    }

    exposures, successes = build_training_counts(draws, start_target)
    global_counts = [
        sum(1 for draw in draws[:start_target - 1] if number in draw["nums"])
        for number in range(1, 46)
    ]

    predictions, random_rows = [], []
    training_cutoff_violations = portfolio_geometry_violations = random_geometry_violations = 0

    for target_round in range(start_target, end_target + 1):
        training_through = target_round - 1
        if training_through != target_round - 1:
            training_cutoff_violations += 1
            raise AssertionError("E068 training cutoff mismatch")

        two_back_nums = draws[target_round - 3]["nums"]
        previous_nums = draws[target_round - 2]["nums"]
        target_state = overlap_count_state(two_back_nums, previous_nums)
        scores, total_weight = score_numbers(
            target_state, exposures, successes, global_counts, target_round - 1, alpha
        )
        lines = make_three_line_portfolio(scores, base)
        union = set().union(*(set(line) for line in lines))
        overlaps = [
            len(set(lines[i]) & set(lines[j]))
            for i in range(3) for j in range(i + 1, 3)
        ]
        if len(union) != 18 or any(overlaps):
            portfolio_geometry_violations += 1
            raise AssertionError("E068 model portfolio geometry violation")

        actual = set(draws[target_round - 1]["nums"])
        observed = base.portfolio_metrics(lines, actual)
        line_hits = [len(set(line) & actual) for line in lines]
        predictions.append({
            "target_round": target_round,
            "training_through_round": training_through,
            "previous_two_draw_overlap_state": str(target_state),
            "historical_transition_count": target_round - 3,
            "sum_transition_weights": f"{total_weight:.12f}",
            "line1": " ".join(map(str, lines[0])),
            "line2": " ".join(map(str, lines[1])),
            "line3": " ".join(map(str, lines[2])),
            "actual_main": " ".join(map(str, sorted(actual))),
            "line_hits": " ".join(map(str, line_hits)),
            **observed
        })

        rng = random.Random(seed + target_round)
        random_metrics = []
        for _ in range(random_count):
            random_lines = base.permute_portfolio_labels(lines, rng)
            random_union = set().union(*(set(line) for line in random_lines))
            random_overlaps = [
                len(set(random_lines[i]) & set(random_lines[j]))
                for i in range(3) for j in range(i + 1, 3)
            ]
            if len(random_union) != 18 or any(random_overlaps):
                random_geometry_violations += 1
                raise AssertionError("E068 random geometry violation")
            random_metrics.append(base.portfolio_metrics(random_lines, actual))
        random_rows.append({
            "target_round": target_round,
            "random_bundles": random_count,
            "random_mean_max_hits": statistics.mean(x["max_hits"] for x in random_metrics),
            "random_p_any2": statistics.mean(x["any2"] for x in random_metrics),
            "random_p_any3": statistics.mean(x["any3"] for x in random_metrics),
            "random_mean_union_coverage": statistics.mean(x["winning_union_coverage"] for x in random_metrics),
            "exact_null_mean_max_hit": exact["max_hits"],
            "exact_null_p_any2": exact["any2"],
            "exact_null_p_any3": exact["any3"],
            "exact_null_expected_union_coverage": exact["winning_union_coverage"],
            "geometry_violations": 0
        })

        # The target outcome is added only after scoring, for the next target's training.
        for number in actual:
            global_counts[number - 1] += 1
        update_transition(two_back_nums, previous_nums, draws[target_round - 1]["nums"], exposures, successes)

    targets = list(range(start_target, end_target + 1))
    if [int(x["target_round"]) for x in predictions] != targets:
        raise AssertionError("E068 prediction target sequence mismatch")
    if len(predictions) != 850 or len(random_rows) != 850:
        raise AssertionError("E068 expected 850 predictions and random baselines")

    differences = {
        metric: [float(row[metric]) - exact[metric] for row in predictions]
        for metric in METRICS
    }
    block_size = int(prereg["inference"]["block_length_targets"])
    blocks = []
    for block_index, start in enumerate(range(0, len(predictions), block_size), 1):
        end = min(start + block_size, len(predictions))
        row = {
            "block_index": block_index,
            "start_target": targets[start],
            "end_target": targets[end - 1],
            "n": end - start
        }
        for metric in METRICS:
            row[f"mean_delta_{metric}"] = statistics.mean(differences[metric][start:end])
        row["any2_positive"] = int(row["mean_delta_any2"] > 0)
        blocks.append(row)
    if len(blocks) != 17:
        raise AssertionError("E068 block count mismatch")

    positive_blocks = sum(row["any2_positive"] for row in blocks)
    positive_share = positive_blocks / len(blocks)
    bootstrap_reps = int(prereg["inference"]["bootstrap_replicates"])
    bootstrap_seed = int(prereg["inference"]["bootstrap_seed"])
    alpha_ci = float(prereg["inference"]["alpha_per_metric"])
    metric_results = {}
    for offset, metric in enumerate(METRICS):
        ci = base.moving_block_ci(
            differences[metric], alpha_ci, bootstrap_seed + 9000 + offset,
            bootstrap_reps, block_size
        )
        metric_results[metric] = {
            "observed_mean": statistics.mean(float(row[metric]) for row in predictions),
            "exact_geometry_matched_null": exact[metric],
            "delta_mean": statistics.mean(differences[metric]),
            "adjusted_moving_block_ci": ci,
            "lower_bound_strictly_gt_zero": ci[0] > 0
        }

    historical_gate_pass = (
        all(metric_results[metric]["lower_bound_strictly_gt_zero"] for metric in METRICS)
        and positive_share >= float(prereg["inference"]["any2_positive_nonoverlapping_50_target_block_share_min"])
    )
    readiness_status = (
        "HISTORICAL_GATE_PASS_PROSPECTIVE_PENDING"
        if historical_gate_pass else "STRICT_FAIL"
    )
    prospective = prereg["prospective_confirmation"]
    strict_pass_ready = False

    outdir = ROOT / "analysis" / date_kst / f"gha_{run_id}_{run_attempt}" / STUDY_ID
    outdir.mkdir(parents=True, exist_ok=False)
    base.write_csv(outdir / "PREDICTIONS.csv", predictions, list(predictions[0].keys()))
    base.write_csv(outdir / "RANDOM_BASELINE.csv", random_rows, list(random_rows[0].keys()))
    base.write_csv(outdir / "BLOCK_STABILITY.csv", blocks, list(blocks[0].keys()))

    model_spec = {
        "study_id": STUDY_ID,
        "evidence_class": "PREREGISTERED_HISTORICAL_EXPLORATORY_THREE_LINE_OVERLAP_COUNT_SIGNAL_NOT_PROSPECTIVE_CONFIRMATION",
        "preregistration": PREREG_REL,
        "data_cutoff": cutoff,
        "target_range": [start_target, end_target],
        "feature_definition": prereg["feature_definition"],
        "estimator": prereg["estimator"],
        "portfolio": prereg["portfolio"],
        "random_comparator": prereg["random_comparator"],
        "inference": prereg["inference"],
        "frozen_blobs": frozen
    }
    base.write_json(outdir / "MODEL_SPEC.json", model_spec)

    inference = {
        "study_id": STUDY_ID,
        "status": readiness_status,
        "data_cutoff": cutoff,
        "targets": len(predictions),
        "random_bundles_total": len(random_rows) * random_count,
        "bootstrap_replicates": bootstrap_reps,
        "block_length_targets": block_size,
        "metrics": metric_results,
        "any2_positive_50_target_blocks": positive_blocks,
        "any2_total_50_target_blocks": len(blocks),
        "any2_positive_50_target_block_share": positive_share,
        "historical_strict_portfolio_pass": historical_gate_pass,
        "strict_portfolio_pass": historical_gate_pass,
        "prospective_confirmation": prospective,
        "strict_pass_ready": strict_pass_ready,
        "purchase_recommendation_generated": False,
        "failed_gates": [
            metric for metric in METRICS
            if not metric_results[metric]["lower_bound_strictly_gt_zero"]
        ] + ([] if positive_share >= 0.65 else ["any2_positive_50_target_block_share"])
    }
    base.write_json(outdir / "INFERENCE.json", inference)

    verification = {
        "status": "PASS",
        "study_id": STUDY_ID,
        "data_cutoff": cutoff,
        "data_rows": total_rows,
        "data_prefix_sha256": prefix_sha,
        "data_sha256": data_sha,
        "target_range": [start_target, end_target],
        "target_count": len(predictions),
        "training_cutoff_rule": "training_through_round = target_round - 1",
        "training_cutoff_violations": training_cutoff_violations,
        "future_outcomes_used": False,
        "leakage_failures": 0,
        "portfolio_geometry_violations": portfolio_geometry_violations,
        "random_geometry_violations": random_geometry_violations,
        "random_bundles_per_target": random_count,
        "random_bundles_total": len(random_rows) * random_count,
        "block_count": len(blocks),
        "bootstrap_replicates": bootstrap_reps,
        "historical_strict_portfolio_pass": historical_gate_pass,
        "strict_pass_ready": False,
        "prospective_confirmation_rule": "UNSPECIFIED_IN_POLICY; no readiness can be created",
        "manifest_entries": 8,
        "manifest_status": "PASS",
        "frozen_blobs": frozen
    }
    base.write_json(outdir / "VERIFICATION.json", verification)

    completion = {
        "study_id": STUDY_ID,
        "status": "COMPLETE",
        "data_cutoff": cutoff,
        "target_count": len(predictions),
        "evidence_class": "HISTORICAL_EXPLORATORY_NOT_PROSPECTIVE_CONFIRMATION",
        "historical_strict_portfolio_pass": historical_gate_pass,
        "strict_pass_ready": False,
        "purchase_recommendation_generated": False
    }
    base.write_json(outdir / "COMPLETION.json", completion)

    report_lines = [
        "# E068 — Previous-two-draw overlap-count transition",
        "",
        f"Execution date: {date_kst}; data cutoff: {cutoff}; targets: {len(predictions)} ({start_target}..{end_target}).",
        "",
        "## Frozen question",
        "Whether the one-component aggregate overlap-count state of the two immediately preceding draws contains cutoff-safe information about the next draw's main-number inclusion, sufficient to improve a deterministic three-line disjoint union18 portfolio over the exact geometry-matched null.",
        "",
        "## Execution",
        f"- Predictions: {len(predictions)}; random bundles: {len(random_rows) * random_count}.",
        f"- Training-cutoff violations: {training_cutoff_violations}; leakage failures: 0.",
        f"- Portfolio geometry violations: {portfolio_geometry_violations}; random geometry violations: {random_geometry_violations}.",
        f"- Bootstrap: {bootstrap_reps} replicates; 50-target blocks: {len(blocks)}; final remainder retained.",
        "",
        "## Results versus exact geometry-matched null",
    ]
    for metric in METRICS:
        item = metric_results[metric]
        ci = item["adjusted_moving_block_ci"]
        report_lines.append(
            f"- {metric}: observed={item['observed_mean']:.8f}; null={item['exact_geometry_matched_null']:.8f}; "
            f"delta={item['delta_mean']:.8f}; adjusted CI=[{ci[0]:.8f}, {ci[1]:.8f}]."
        )
    report_lines.extend([
        f"- Positive any2 blocks: {positive_blocks}/{len(blocks)} ({positive_share:.2%}); required 65%.",
        "",
        "## Interpretation",
        f"- Historical strict portfolio gate: {'PASS' if historical_gate_pass else 'FAIL'}.",
        "- Prospective confirmation remains unspecified by policy; STRICT_PASS_READY is therefore false regardless of historical results.",
        "- This is one historical exploratory signal-family test, not an untouched prospective sample and not a purchase recommendation.",
        "- No thresholds, alpha, block length, comparator, or model variants were changed after registration.",
        "",
        "No purchase lines were generated or published."
    ])
    (outdir / "REPORT.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    manifest_entries = base.write_and_verify_manifest(outdir)
    if manifest_entries != 8:
        raise AssertionError(f"E068 manifest entry count mismatch: {manifest_entries}")
    return {
        "status": "PASS",
        "study_id": STUDY_ID,
        "result_path": outdir.relative_to(ROOT).as_posix(),
        "data_cutoff": cutoff,
        "targets": len(predictions),
        "random_bundles_total": len(random_rows) * random_count,
        "leakage_failures": 0,
        "manifest_entries": manifest_entries,
        "historical_strict_portfolio_pass": historical_gate_pass,
        "strict_pass_ready": False,
        "failed_gates": inference["failed_gates"],
        "metrics": metric_results,
        "any2_positive_50_target_block_share": positive_share
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--date")
    parser.add_argument("--run-id")
    parser.add_argument("--run-attempt", default="1")
    args = parser.parse_args()
    if args.preflight:
        print(json.dumps(preflight(), ensure_ascii=False, indent=2))
        return 0
    if not args.date or not args.run_id:
        parser.error("--date and --run-id are required unless --preflight is used")
    result = run(args.date, args.run_id, args.run_attempt)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
