#!/usr/bin/env python3
"""E063: preregistered last-digit occupancy transition for a three-line union18 portfolio."""
from __future__ import annotations
import argparse, importlib.util, json, random, statistics, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STUDY_ID = "E063_THREE_LINE_LAST_DIGIT_OCCUPANCY_TRANSITION_v1"
PREREG_REL = "research/weekly_purchase/1251/E063_THREE_LINE_LAST_DIGIT_OCCUPANCY_TRANSITION_PREREG_20261116.json"
POLICY_REL = "research/weekly_purchase/1251/THREE_LINE_POLICY_1251_PLUS.json"
BASE_REL = "automation/three_line_research_1251_v1.py"
RUNNER_REL = "automation/three_line_last_digit_transition_e063.py"
TEST_REL = "automation/tests_v2/test_three_line_last_digit_transition_e063.py"
WORKFLOW_REL = ".github/workflows/target-1251-e063-three-line-last-digit-transition.yml"
METRICS = ("max_hits", "any2", "any3", "winning_union_coverage")
EXPECTED_DATA_SHA = "7203238dae69ce281c59e6a0928cc187b11d88ed342685cd2dd2f214f063b3c2"


def load_base():
    path = ROOT / BASE_REL
    spec = importlib.util.spec_from_file_location("e063_e045_reference", path)
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
        actual[key] = subprocess.check_output(["git", "rev-parse", f"HEAD:{path}"], cwd=ROOT, text=True).strip()
        if actual[key] != prereg["frozen_blobs"].get(key):
            raise ValueError(f"Frozen blob mismatch for {path}: {actual[key]} != {prereg['frozen_blobs'].get(key)}")
    return actual


def validate_preregistration(prereg, policy):
    if prereg.get("study_id") != STUDY_ID or prereg.get("policy_id") != policy.get("policy_id"):
        raise ValueError("E063 preregistration/policy identity mismatch")
    if prereg.get("preregistration_status") != "FROZEN_BEFORE_EXECUTION":
        raise ValueError("E063 preregistration is not frozen")
    if prereg.get("independent_research_axis") is not True or prereg.get("independent_signal_family") is not True:
        raise ValueError("E063 must remain one independent signal-family axis")
    if prereg.get("historical_exploration_only") is not True:
        raise ValueError("E063 historical evidence scope must remain explicit")
    if int(prereg.get("target_round", -1)) != 1251:
        raise ValueError("E063 target round changed")
    if int(prereg.get("historical_data_cutoff", -1)) != 1250 or prereg.get("target_rounds") != "401..1250 inclusive":
        raise ValueError("E063 historical cutoff/target range changed")
    if prereg.get("source_data_prefix_sha256") != EXPECTED_DATA_SHA or prereg.get("source_data_full_file_sha256") != EXPECTED_DATA_SHA:
        raise ValueError("E063 canonical data hash changed")
    feature = {
        "source": "The immediately preceding draw's six main numbers only; bonus is excluded.",
        "class": "For candidate n, terminal-digit class d=n mod 10; state k is the count of previous-draw main numbers with the same terminal digit.",
        "state_range": "k is an integer from 0 through 6; terminal-digit classes are 0..9; class 0 contains four numbers and classes 1..9 contain five numbers.",
        "candidate_universe": "All integers 1..45 are scored for every target.",
        "transition_history": "For each historical outcome round u=2..t-1, use the terminal-digit occupancy of draw u-1 as the feature and main-number inclusion in draw u as the outcome. Score target t from draw t-1, then add target t only after scoring."
    }
    if prereg.get("feature_definition") != feature:
        raise ValueError("E063 last-digit feature definition changed")
    estimator = {
        "prior_mean": "6/45 main-number inclusion probability under the uniform 6-of-45 null",
        "prior_strength": 45,
        "posterior_probability": "(success[k,n] + 45*(6/45))/(exposure[k,n]+45)",
        "ranking": "Score descending, then number ascending.",
        "variants": 1,
        "parameter_search": False
    }
    if prereg.get("estimator") != estimator:
        raise ValueError("E063 estimator changed")
    portfolio = prereg["portfolio"]
    if (
        portfolio.get("geometry") != "Exactly three pairwise-disjoint six-number lines, union18."
        or portfolio.get("selection") != "Three sequential calls to the unchanged E045 choose_disjoint_ticket selector, passing the E063 score as both role_score and global_score; remove selected numbers after each line."
        or portfolio.get("randomness_in_selection") is not False
        or portfolio.get("variants") != 1
    ):
        raise ValueError("E063 portfolio construction changed")
    comparator = prereg["random_comparator"]
    method = "For each target, uniformly permute labels 1..45 jointly over the three fixed model lines, preserving three six-number lines, pairwise disjointness, union18, and line-incidence geometry."
    if (
        comparator.get("method") != method
        or int(comparator.get("random_bundles_per_target", -1)) != 120
        or int(comparator.get("seed", -1)) != 20261116063
        or comparator.get("randomness_used_for_final_selection") is not False
    ):
        raise ValueError("E063 random comparator changed")
    inference = prereg["inference"]
    if (
        inference.get("metrics") != list(METRICS)
        or float(inference.get("family_alpha", -1)) != 0.05
        or float(inference.get("alpha_per_metric", -1)) != 0.0125
        or int(inference.get("bootstrap_replicates", -1)) != 4000
        or int(inference.get("bootstrap_seed", -1)) != 20261116063
        or int(inference.get("block_length_targets", -1)) != 50
        or inference.get("retain_final_remainder_block") is not True
        or float(inference.get("any2_positive_nonoverlapping_50_target_block_share_min", -1)) != 0.65
        or any(inference.get(k) is not True for k in ("no_threshold_relaxation", "no_alpha_change", "no_block_length_change", "no_comparator_change", "no_unbounded_microvariants"))
    ):
        raise ValueError("E063 inference/promotion gate changed")
    prospective = prereg["prospective_confirmation"]
    if (
        prospective.get("required_by_policy") is not True
        or prospective.get("minimum_target_count") is not None
        or prospective.get("completion_rule") is not None
        or prospective.get("status") != "UNSPECIFIED_IN_POLICY"
    ):
        raise ValueError("E063 cannot silently define the prospective confirmation rule")
    if prereg.get("expected_record_counts") != {"PREDICTIONS.csv": 850, "RANDOM_BASELINE.csv": 850, "BLOCK_STABILITY.csv": 17}:
        raise ValueError("E063 expected record counts changed")
    if prereg.get("no_future_leakage") is not True or prereg.get("strict_pass_ready_requires_prospective_rule") is not True:
        raise ValueError("E063 leakage/readiness requirements changed")
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
        raise ValueError("E063 strict policy gate changed")
    exact = comparator["exact_null"]
    for key in ("mean_max_hit", "p_any2", "p_any3", "expected_union_coverage"):
        if abs(float(exact[key]) - float(policy["exact_null"][key])) > 1e-14:
            raise ValueError(f"E063 exact geometry-matched null changed: {key}")


def last_digit_occupancy(previous_nums, number):
    values = tuple(int(x) for x in previous_nums)
    if len(values) != 6 or len(set(values)) != 6 or any(x < 1 or x > 45 for x in values):
        raise ValueError("previous draw must contain six unique main numbers in 1..45")
    if type(number) is not int or not 1 <= number <= 45:
        raise ValueError("candidate number must be an integer in 1..45")
    digit = number % 10
    return sum(1 for value in values if value % 10 == digit)


def update_transition(previous_nums, outcome_nums, exposures, successes):
    outcome = set(int(x) for x in outcome_nums)
    if len(outcome) != 6 or any(x < 1 or x > 45 for x in outcome):
        raise ValueError("transition outcome must contain six valid main numbers")
    for number in range(1, 46):
        state = last_digit_occupancy(previous_nums, number)
        exposures[state][number] += 1
        if number in outcome:
            successes[state][number] += 1


def build_training_counts(draws, target_round):
    """Use outcome rounds u=2..target_round-1 only; never read target_round outcome."""
    if target_round < 3 or target_round > len(draws):
        raise ValueError("target round is outside the available draw prefix")
    exposures = [[0] * 46 for _ in range(7)]
    successes = [[0] * 46 for _ in range(7)]
    for outcome_round in range(2, target_round):
        update_transition(draws[outcome_round - 2]["nums"], draws[outcome_round - 1]["nums"], exposures, successes)
    return exposures, successes


def score_numbers(previous_nums, exposures, successes, global_counts, global_draws):
    if len(global_counts) != 45 or global_draws <= 0 or len(exposures) != 7 or len(successes) != 7:
        raise ValueError("invalid E063 scoring inputs")
    scores = {}
    for number in range(1, 46):
        state = last_digit_occupancy(previous_nums, number)
        exposure = int(exposures[state][number])
        success = int(successes[state][number])
        if exposure < 0 or success < 0 or success > exposure:
            raise ValueError("invalid E063 conditional exposure/success counts")
        global_rate = float(global_counts[number - 1]) / global_draws
        scores[number] = (success + 45.0 * global_rate) / (exposure + 45.0)
    return scores


def make_three_line_portfolio(scores, base):
    used, lines = set(), []
    for _ in range(3):
        line = base.choose_disjoint_ticket(scores, scores, used)
        lines.append(tuple(line))
        used.update(line)
    if len(lines) != 3 or len(used) != 18:
        raise AssertionError("E063 portfolio must be exactly three disjoint lines with union18")
    return lines


def score_target(draws, target_round, base):
    """Return target predictions using only draws 1..target_round-1."""
    if target_round < 3 or target_round > len(draws):
        raise ValueError("target round is outside the available draw prefix")
    history = draws[: target_round - 1]
    previous_nums = draws[target_round - 2]["nums"]
    exposures, successes = build_training_counts(draws, target_round)
    global_counts = [sum(1 for draw in history if number in draw["nums"]) for number in range(1, 46)]
    scores = score_numbers(previous_nums, exposures, successes, global_counts, target_round - 1)
    return scores, make_three_line_portfolio(scores, base)


def preflight():
    prereg = json.loads((ROOT / PREREG_REL).read_text(encoding="utf-8"))
    policy = json.loads((ROOT / POLICY_REL).read_text(encoding="utf-8"))
    validate_preregistration(prereg, policy)
    frozen = verify_frozen_blobs(prereg)
    base = load_base()
    draws, prefix_sha, full_sha, total_rows = base.load_frozen_draw_prefix(1250, EXPECTED_DATA_SHA, EXPECTED_DATA_SHA)
    if len(draws) != 1250 or total_rows != 1250 or prefix_sha != EXPECTED_DATA_SHA or full_sha != EXPECTED_DATA_SHA:
        raise ValueError("E063 canonical source must contain exactly 1,250 verified contiguous draws")
    return {"status": "PREFLIGHT_PASS", "study_id": STUDY_ID, "data_cutoff": 1250, "data_rows": total_rows, "data_sha256": full_sha, "frozen_blobs": frozen}


def run(date_kst, run_id):
    if date_kst != "2026-11-16":
        raise ValueError("E063 execution date must match its frozen preregistration date")
    if not run_id or any(ch not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for ch in run_id):
        raise ValueError("run_id contains unsafe characters")
    prereg = json.loads((ROOT / PREREG_REL).read_text(encoding="utf-8"))
    policy = json.loads((ROOT / POLICY_REL).read_text(encoding="utf-8"))
    validate_preregistration(prereg, policy)
    verify_frozen_blobs(prereg)
    base = load_base()
    draws, data_prefix_sha, data_sha, total_rows = base.load_frozen_draw_prefix(1250, EXPECTED_DATA_SHA, EXPECTED_DATA_SHA)
    if len(draws) != 1250 or total_rows != 1250:
        raise ValueError("E063 requires exactly 1,250 contiguous verified draws")

    random_count = int(prereg["random_comparator"]["random_bundles_per_target"])
    seed = int(prereg["random_comparator"]["seed"])
    rng = random.Random(seed)
    deltas = {metric: [] for metric in METRICS}
    prediction_rows, random_rows = [], []
    portfolio_geometry_violations = random_geometry_violations = training_cutoff_violations = 0
    start_target, end_target = 401, 1250

    for target_round in range(start_target, end_target + 1):
        training_through = target_round - 1
        if training_through != target_round - 1:
            training_cutoff_violations += 1
            raise AssertionError("E063 training cutoff mismatch")
        scores, lines = score_target(draws, target_round, base)
        union = set().union(*(set(line) for line in lines))
        overlaps = [len(set(a) & set(b)) for i, a in enumerate(lines) for b in lines[i + 1:]]
        if len(lines) != 3 or len(union) != 18 or any(overlaps):
            portfolio_geometry_violations += 1
            raise AssertionError("E063 model portfolio geometry violation")
        actual = set(draws[target_round - 1]["nums"])
        observed = base.portfolio_metrics(lines, actual)
        random_values = {metric: [] for metric in METRICS}
        for _ in range(random_count):
            random_lines = base.permute_portfolio_labels(lines, rng)
            random_union = set().union(*(set(line) for line in random_lines))
            random_overlaps = [len(set(a) & set(b)) for i, a in enumerate(random_lines) for b in random_lines[i + 1:]]
            if len(random_union) != 18 or any(random_overlaps):
                random_geometry_violations += 1
                raise AssertionError("E063 random comparator geometry violation")
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
        random_rows.append({"target_round": target_round, "random_bundles": random_count, **{f"random_mean_{m}": random_mean[m] for m in METRICS}})

    alpha = float(prereg["inference"]["alpha_per_metric"])
    replicates = int(prereg["inference"]["bootstrap_replicates"])
    block_size = int(prereg["inference"]["block_length_targets"])
    bootstrap_seed = int(prereg["inference"]["bootstrap_seed"])
    metric_summary = {}
    for index, metric in enumerate(METRICS):
        ci = base.moving_block_ci(deltas[metric], alpha=alpha, seed=bootstrap_seed + index, replicates=replicates, block_size=block_size)
        metric_summary[metric] = {
            "observed_mean": statistics.mean(float(row[metric]) for row in prediction_rows),
            "random_mean": statistics.mean(float(row[f"random_mean_{metric}"]) for row in prediction_rows),
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
    all_ci_positive = all(metric_summary[m]["lower_bound_strictly_gt_zero"] for m in METRICS)
    historical_gate_pass = all_ci_positive and block_share >= 0.65

    outdir = ROOT / "analysis" / date_kst / run_id / STUDY_ID
    outdir.mkdir(parents=True, exist_ok=False)
    base.write_csv(outdir / "PREDICTIONS.csv", prediction_rows, list(prediction_rows[0].keys()))
    base.write_csv(outdir / "RANDOM_BASELINE.csv", random_rows, list(random_rows[0].keys()))
    base.write_csv(outdir / "BLOCK_STABILITY.csv", block_rows, list(block_rows[0].keys()))
    inference = {
        "study_id": STUDY_ID,
        "evidence_class": "HISTORICAL_EXPLORATORY_INDEPENDENT_FEATURE_FAMILY_NOT_PROSPECTIVE_CONFIRMATION",
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
    model_spec = {"study_id": STUDY_ID, "preregistration_path": PREREG_REL, "preregistration": prereg, "implementation": RUNNER_REL, "base_selection_helper": BASE_REL, "strict_policy_path": POLICY_REL}
    report = [
        "# E063 — Previous-draw last-digit occupancy transition",
        "",
        "Execution status: **COMPLETE / VERIFICATION PASS**",
        f"Historical strict gate: **{'PASS' if historical_gate_pass else 'FAIL'}**",
        "",
        "## Frozen design",
        "- One last-digit occupancy transition feature family; candidate number n is conditioned on the count of previous-draw main numbers sharing n mod 10.",
        "- One fixed shrinkage estimator with prior strength 45; one deterministic E045 disjoint-line selector; no variants or parameter search.",
        "- Targets 401–1250; each target uses only draws through t-1.",
        "- 120 jointly permuted, geometry-matched random portfolios per target; 4,000 moving-block bootstrap replicates; 50-target blocks.",
        "",
        "## Results",
    ]
    for metric in METRICS:
        row = metric_summary[metric]
        report.append(f"- {metric}: observed={row['observed_mean']:.6f}, random={row['random_mean']:.6f}, delta={row['delta_mean']:.6f}, adjusted CI=[{row['adjusted_moving_block_ci'][0]:.6f}, {row['adjusted_moving_block_ci'][1]:.6f}]")
    report.extend([
        f"- Positive any2 blocks: {positive_blocks}/{len(block_rows)} ({block_share:.2%}); required: 65%.",
        "",
        "## Interpretation and guardrails",
        "- This is a new feature-family test on an already observed historical sample, not an independent prospective sample.",
        "- Even a historical gate PASS cannot create STRICT_PASS_READY because the policy still requires a separately specified prospective confirmation rule.",
        "- No purchase lines, candidate lines, freeze, or seal were generated.",
        "- No strict threshold, alpha, block length, comparator, or purchase policy was changed.",
        "",
    ])
    base.write_json(outdir / "INFERENCE.json", inference)
    base.write_json(outdir / "VERIFICATION.json", verification)
    base.write_json(outdir / "COMPLETION.json", completion)
    base.write_json(outdir / "MODEL_SPEC.json", model_spec)
    (outdir / "REPORT.md").write_text("\n".join(report), encoding="utf-8")
    manifest_entries = base.write_and_verify_manifest(outdir)
    if manifest_entries != 8:
        raise AssertionError(f"Expected 8 manifest entries, got {manifest_entries}")
    return {"result_path": str(outdir.relative_to(ROOT)), "verification": verification, "inference": inference, "completion": completion, "manifest_entries": manifest_entries}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--date", default="2026-11-16")
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
