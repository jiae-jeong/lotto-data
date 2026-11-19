#!/usr/bin/env python3
"""E052: nested trailing-performance selector across five frozen three-line portfolios."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import random
import statistics
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_RUNNER = ROOT / "automation/three_line_research_1251_v1.py"
POLICY_PATH = ROOT / "research/weekly_purchase/1251/THREE_LINE_POLICY_1251_PLUS.json"
PREREG_PATH = ROOT / "research/weekly_purchase/1251/E052_THREE_LINE_TRAILING_PERFORMANCE_SELECTOR_PREREG_20261115.json"
STUDY_ID = "E052_THREE_LINE_TRAILING_PERFORMANCE_SELECTOR_v1"
MODEL_ORDER = (
    "E045_THREE_LINE_DISJOINT_PORTFOLIO_WALKFORWARD_v1",
    "E048_THREE_LINE_BONUS_TO_MAIN_TRANSITION_v1",
    "E049_THREE_LINE_DRAW_STATE_TRANSITION_v1",
    "E050_THREE_LINE_PREVIOUS_MAIN_NEIGHBOR_TRANSITION_v1",
    "E051_THREE_LINE_PAIR_CONTEXT_CONDITIONAL_v1",
)
METRICS = ("max_hits", "any2", "any3", "winning_union_coverage")


def load_base():
    spec = importlib.util.spec_from_file_location("e052_three_line_reference", BASE_RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load frozen three-line helpers: {BASE_RUNNER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def parse_line(value: str) -> tuple[int, ...]:
    numbers = tuple(sorted(int(part) for part in value.replace(",", " ").split()))
    if len(numbers) != 6 or len(set(numbers)) != 6 or any(n < 1 or n > 45 for n in numbers):
        raise ValueError(f"Invalid six-number line: {value!r}")
    return numbers


def training_window(target_round: int, lookback: int) -> list[int]:
    if lookback <= 0 or target_round <= lookback:
        raise ValueError("Target must have a complete positive trailing window")
    return list(range(target_round - lookback, target_round))


def select_model(trailing_any2_rates: dict[str, float]) -> str:
    if set(trailing_any2_rates) != set(MODEL_ORDER):
        raise ValueError("Selector must receive exactly the five preregistered models")
    # Fixed tie-break: first model in MODEL_ORDER wins an exact tie.
    return max(MODEL_ORDER, key=lambda model: (float(trailing_any2_rates[model]), -MODEL_ORDER.index(model)))


def _verify_preregistration(prereg: dict, policy: dict) -> None:
    if prereg.get("study_id") != STUDY_ID:
        raise ValueError("E052 study identity mismatch")
    if prereg.get("preregistration_status") != "FROZEN_BEFORE_EXECUTION":
        raise ValueError("E052 preregistration is not frozen")
    if prereg.get("independent_research_axis") is not True:
        raise ValueError("E052 must remain a separately registered model-selection axis")
    if prereg.get("historical_data_cutoff") != 1249:
        raise ValueError("E052 historical cutoff changed")
    if prereg.get("source_data_prefix_sha256") != "a5996af8b842799d777beae0abeef9767f79726870e4d78d6683dfb0fe4802e7":
        raise ValueError("E052 frozen 1249-round data prefix changed")
    if prereg.get("source_data_full_file_sha256") != "7203238dae69ce281c59e6a0928cc187b11d88ed342685cd2dd2f214f063b3c2":
        raise ValueError("E052 canonical full-file hash changed")
    if prereg.get("source_target_range") != [401, 1249] or prereg.get("evaluation_target_range") != [501, 1249]:
        raise ValueError("E052 target ranges changed")
    selection = prereg.get("selection", {})
    if selection.get("lookback_targets") != 100 or selection.get("metric") != "any2":
        raise ValueError("E052 trailing selector specification changed")
    if selection.get("candidate_model_order") != list(MODEL_ORDER):
        raise ValueError("E052 candidate model order changed")
    if selection.get("tie_break") != "first model in candidate_model_order":
        raise ValueError("E052 tie-break changed")
    if selection.get("parameter_search") is not False or selection.get("variants") != 1:
        raise ValueError("E052 must remain one fixed selector without variants")
    if prereg.get("candidate_models") is None or len(prereg["candidate_models"]) != len(MODEL_ORDER):
        raise ValueError("E052 candidate source registry is incomplete")
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
        raise ValueError("E052 inference differs from the unchanged three-line strict policy")
    null = prereg["random_comparator"]["exact_null"]
    for key in ("mean_max_hit", "p_any2", "p_any3", "expected_union_coverage"):
        if abs(float(policy["exact_null"][key]) - float(null[key])) > 1e-14:
            raise ValueError(f"E052 exact null mismatch for {key}")
    prospective = prereg["prospective_confirmation"]
    if prospective.get("required_by_policy") is not True:
        raise ValueError("E052 must retain prospective confirmation")
    if prospective.get("minimum_target_count") is not None or prospective.get("completion_rule") is not None:
        raise ValueError("E052 cannot invent a prospective completion rule")


def _stored_actual(row: dict) -> tuple[int, ...] | None:
    value = row.get("actual_numbers") or row.get("actual_main")
    if not value:
        return None
    return tuple(sorted(int(part) for part in value.replace(",", " ").split()))


def _check_stored_metrics(row: dict, computed: dict, model: str, target: int) -> None:
    for field in ("max_hits", "any2", "any3", "winning_union_coverage", "union_size"):
        if field in row and row[field] not in (None, ""):
            if int(float(row[field])) != int(computed[field]):
                raise ValueError(f"{model} target {target}: stored {field} differs from canonical recomputation")
    if row.get("line_hits"):
        stored = [int(x) for x in row["line_hits"].replace(",", " ").split()]
        if stored != computed["line_hits"]:
            raise ValueError(f"{model} target {target}: stored line_hits mismatch")
    elif all(row.get(f"line{i}_hits") not in (None, "") for i in (1, 2, 3)):
        stored = [int(row[f"line{i}_hits"]) for i in (1, 2, 3)]
        if stored != computed["line_hits"]:
            raise ValueError(f"{model} target {target}: stored per-line hits mismatch")


def load_candidate_sources(prereg: dict, draws: list[dict], base) -> dict[str, dict[int, dict]]:
    expected_targets = list(range(401, 1250))
    canonical = {draw["round"]: set(draw["nums"]) for draw in draws}
    result: dict[str, dict[int, dict]] = {}
    for source in prereg["candidate_models"]:
        model = source["study_id"]
        if model not in MODEL_ORDER or model in result:
            raise ValueError(f"Unexpected or duplicate E052 candidate model: {model}")
        prediction_path = ROOT / source["prediction_path"]
        manifest_path = ROOT / source["manifest_path"]
        verification_path = ROOT / source["verification_path"]
        raw = prediction_path.read_bytes()
        if len(raw) != int(source["prediction_bytes"]) or hashlib.sha256(raw).hexdigest() != source["prediction_sha256"]:
            raise ValueError(f"{model}: source prediction SHA256/byte count mismatch")
        manifest = _read_csv(manifest_path)
        prediction_entries = [row for row in manifest if row.get("path") == "PREDICTIONS.csv"]
        if len(prediction_entries) != 1:
            raise ValueError(f"{model}: source manifest lacks one PREDICTIONS.csv entry")
        if (
            prediction_entries[0].get("sha256") != source["prediction_sha256"]
            or int(prediction_entries[0].get("bytes", -1)) != int(source["prediction_bytes"])
        ):
            raise ValueError(f"{model}: source manifest does not match preregistered prediction file")
        verification = json.loads(verification_path.read_text(encoding="utf-8"))
        if verification.get("status") != "PASS":
            raise ValueError(f"{model}: source verification is not PASS")
        if int(verification.get("data_cutoff", -1)) != int(source["source_data_cutoff"]):
            raise ValueError(f"{model}: source verification cutoff mismatch")
        if verification.get("leakage_failures", 0) != 0 or verification.get("future_predictions", 0) != 0:
            raise ValueError(f"{model}: source verification reports leakage/future predictions")
        if verification.get("training_cutoff_violations", 0) != 0:
            raise ValueError(f"{model}: source verification reports a training cutoff violation")

        rows = _read_csv(prediction_path)
        by_target: dict[int, dict] = {}
        for row in rows:
            target = int(row["target_round"])
            if target < 401 or target > 1249:
                continue
            if target in by_target:
                raise ValueError(f"{model}: duplicate prediction target {target}")
            if int(row["training_through_round"]) != target - 1:
                raise ValueError(f"{model}: target {target} is not cutoff-safe")
            lines = [parse_line(row[f"line{i}"]) for i in (1, 2, 3)]
            metrics = base.portfolio_metrics(lines, canonical[target])
            stored_actual = _stored_actual(row)
            if stored_actual is not None and set(stored_actual) != canonical[target]:
                raise ValueError(f"{model} target {target}: stored actual outcome differs from canonical data")
            _check_stored_metrics(row, {**metrics, "line_hits": [len(set(line) & canonical[target]) for line in lines]}, model, target)
            by_target[target] = {
                "target_round": target,
                "training_through_round": target - 1,
                "lines": lines,
                "actual": canonical[target],
                "metrics": metrics,
            }
        if sorted(by_target) != expected_targets:
            raise ValueError(f"{model}: expected 849 contiguous source targets 401..1249; got {len(by_target)}")
        result[model] = by_target
    if tuple(result) != MODEL_ORDER:
        raise ValueError("E052 source models are not in the preregistered order")
    return result


def _mean_metric(rows: list[dict], metric: str) -> float:
    return statistics.mean(float(row[metric]) for row in rows)


def run(date_kst: str, run_id: str) -> None:
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
    if len(draws) != cutoff or current_rows != 1250 or data_sha != prereg["source_data_full_file_sha256"]:
        raise ValueError("E052 canonical source data rows/hash do not match the frozen 1249 prefix and 1250 file")
    sources = load_candidate_sources(prereg, draws, base)

    selection = prereg["selection"]
    lookback = int(selection["lookback_targets"])
    start_target, end_target = map(int, prereg["evaluation_target_range"])
    if start_target != 501 or end_target != 1249 or lookback != 100:
        raise ValueError("E052 evaluation range/window differs from preregistration")
    if training_window(start_target, lookback) != list(range(401, 501)):
        raise AssertionError("E052 first training window is not targets 401..500")

    null = prereg["random_comparator"]["exact_null"]
    exact_by_metric = {
        "max_hits": float(null["mean_max_hit"]),
        "any2": float(null["p_any2"]),
        "any3": float(null["p_any3"]),
        "winning_union_coverage": float(null["expected_union_coverage"]),
    }
    random_count = int(prereg["random_comparator"]["random_bundles_per_target"])
    seed = int(prereg["random_comparator"]["seed"])
    observations = []
    selection_rows = []
    random_rows = []
    training_cutoff_violations = 0
    portfolio_geometry_violations = 0
    random_geometry_violations = 0

    for target in range(start_target, end_target + 1):
        window = training_window(target, lookback)
        rates = {
            model: statistics.mean(float(sources[model][past]["metrics"]["any2"]) for past in window)
            for model in MODEL_ORDER
        }
        chosen = select_model(rates)
        selected = sources[chosen][target]
        if selected["training_through_round"] != target - 1:
            training_cutoff_violations += 1
            raise AssertionError("E052 selected source prediction violates target-1 cutoff")
        lines = selected["lines"]
        actual = selected["actual"]
        metrics = base.portfolio_metrics(lines, actual)
        line_hits = [len(set(line) & actual) for line in lines]
        union = set().union(*(set(line) for line in lines))
        if len(union) != 18:
            portfolio_geometry_violations += 1
            raise AssertionError("E052 selected portfolio is not disjoint union18")

        observations.append({
            "target_round": target,
            "training_through_round": target - 1,
            "selection_training_start": window[0],
            "selection_training_end": window[-1],
            "selected_model": chosen,
            "selected_training_any2_rate": rates[chosen],
            "lines": lines,
            "actual": tuple(sorted(actual)),
            "line_hits": line_hits,
            **metrics,
        })
        selection_rows.append({
            "target_round": target,
            "selection_training_start": window[0],
            "selection_training_end": window[-1],
            "selected_model": chosen,
            "selected_training_any2_rate": f"{rates[chosen]:.12f}",
            **{f"trailing_any2_{model}": f"{rates[model]:.12f}" for model in MODEL_ORDER},
            "selection_uses_target_outcome": False,
        })

        rng = random.Random(seed + target)
        random_metrics = []
        for _ in range(random_count):
            random_lines = base.permute_portfolio_labels(lines, rng)
            random_result = base.portfolio_metrics(random_lines, actual)
            random_union = set().union(*(set(line) for line in random_lines))
            if len(random_union) != 18:
                random_geometry_violations += 1
                raise AssertionError("E052 random comparator violated disjoint union18 geometry")
            random_metrics.append(random_result)
        random_rows.append({
            "target_round": target,
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

    expected_targets = list(range(start_target, end_target + 1))
    if [row["target_round"] for row in observations] != expected_targets:
        raise AssertionError("E052 selected target range is incomplete")

    diffs = {
        metric: [float(row[metric]) - exact_by_metric[metric] for row in observations]
        for metric in METRICS
    }
    block_size = int(prereg["inference"]["block_length_targets"])
    bootstrap_reps = int(prereg["inference"]["bootstrap_replicates"])
    alpha = float(prereg["inference"]["alpha_per_metric"])
    block_rows = []
    targets = [row["target_round"] for row in observations]
    for block_index, start in enumerate(range(0, len(observations), block_size), 1):
        stop = min(start + block_size, len(observations))
        item = {
            "block_index": block_index,
            "start_target": targets[start],
            "end_target": targets[stop - 1],
            "n": stop - start,
        }
        for metric in METRICS:
            item[f"mean_delta_{metric}"] = statistics.mean(diffs[metric][start:stop])
        item["any2_positive"] = int(item["mean_delta_any2"] > 0)
        block_rows.append(item)
    any2_positive_share = sum(row["any2_positive"] for row in block_rows) / len(block_rows)

    inference = {}
    for offset, metric in enumerate(METRICS):
        ci = base.moving_block_ci(
            diffs[metric], alpha, seed + 9000 + offset, bootstrap_reps, block_size
        )
        inference[metric] = {
            "observed_mean": _mean_metric(observations, metric),
            "exact_geometry_matched_null": exact_by_metric[metric],
            "delta_mean": statistics.mean(diffs[metric]),
            "adjusted_moving_block_ci": ci,
            "lower_bound_strictly_gt_zero": ci[0] > 0,
        }
    historical_gate_pass = (
        all(inference[metric]["lower_bound_strictly_gt_zero"] for metric in METRICS)
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

    static_rows = []
    for model in MODEL_ORDER:
        rows = [sources[model][target]["metrics"] for target in range(start_target, end_target + 1)]
        item = {
            "model": model,
            "targets": len(rows),
        }
        for metric in METRICS:
            value = _mean_metric(rows, metric)
            item[f"mean_{metric}"] = value
            item[f"delta_{metric}_vs_exact_null"] = value - exact_by_metric[metric]
        static_rows.append(item)

    selection_counts = Counter(row["selected_model"] for row in observations)
    simulated_random_means = {
        "max_hits": statistics.mean(row["random_mean_max_hits"] for row in random_rows),
        "any2": statistics.mean(row["random_p_any2"] for row in random_rows),
        "any3": statistics.mean(row["random_p_any3"] for row in random_rows),
        "winning_union_coverage": statistics.mean(row["random_mean_union_coverage"] for row in random_rows),
    }

    outdir = ROOT / "analysis" / date_kst / run_id / STUDY_ID
    outdir.mkdir(parents=True, exist_ok=False)
    base.write_csv(
        outdir / "PREDICTIONS.csv",
        [{
            "target_round": row["target_round"],
            "training_through_round": row["training_through_round"],
            "selected_model": row["selected_model"],
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
        } for row in observations],
        ["target_round", "training_through_round", "selected_model", "line1", "line2", "line3",
         "actual_numbers", "line1_hits", "line2_hits", "line3_hits", "max_hits", "any2", "any3",
         "winning_union_coverage", "union_size"],
    )
    base.write_csv(
        outdir / "MODEL_SELECTION_LOG.csv",
        selection_rows,
        ["target_round", "selection_training_start", "selection_training_end", "selected_model",
         "selected_training_any2_rate"] + [f"trailing_any2_{model}" for model in MODEL_ORDER]
         + ["selection_uses_target_outcome"],
    )
    base.write_csv(
        outdir / "STATIC_MODEL_SCORECARD.csv",
        static_rows,
        ["model", "targets"] + [field for metric in METRICS for field in (f"mean_{metric}", f"delta_{metric}_vs_exact_null")],
    )
    base.write_csv(
        outdir / "RANDOM_BASELINE.csv",
        random_rows,
        ["target_round", "random_bundles", "random_mean_max_hits", "random_p_any2", "random_p_any3",
         "random_mean_union_coverage", "exact_null_mean_max_hit", "exact_null_p_any2",
         "exact_null_p_any3", "exact_null_expected_union_coverage", "geometry_violations"],
    )
    base.write_csv(
        outdir / "BLOCK_STABILITY.csv",
        block_rows,
        ["block_index", "start_target", "end_target", "n", "mean_delta_max_hits", "mean_delta_any2",
         "mean_delta_any3", "mean_delta_winning_union_coverage", "any2_positive"],
    )

    inference_payload = {
        "study_id": STUDY_ID,
        "evidence_class": "HISTORICAL_NESTED_SELECTOR_SCREEN_NOT_PROSPECTIVE_CONFIRMATION",
        "data_cutoff": cutoff,
        "source_target_range": [401, 1249],
        "evaluation_target_range": [start_target, end_target],
        "targets": len(observations),
        "candidate_models": list(MODEL_ORDER),
        "selection_metric": "any2",
        "selection_lookback_targets": lookback,
        "selection_counts": dict(selection_counts),
        "random_bundles_per_target": random_count,
        "random_bundles_total": len(observations) * random_count,
        "block_size": block_size,
        "block_lengths": [row["n"] for row in block_rows],
        "family_alpha": float(prereg["inference"]["family_alpha"]),
        "alpha_per_metric": alpha,
        "bootstrap_replicates": bootstrap_reps,
        "metrics": inference,
        "any2_positive_50_target_block_share": any2_positive_share,
        "simulated_random_means": simulated_random_means,
        "static_model_scorecard": static_rows,
        "historical_strict_gate_pass": historical_gate_pass,
        "strict_portfolio_pass": strict_portfolio_pass,
        "strict_pass_ready": False,
        "readiness_status": readiness_status,
        "prospective_minimum_target_count": prospective["minimum_target_count"],
        "prospective_completion_rule": prospective["completion_rule"],
        "parameter_search": False,
        "variants": 1,
        "thresholds_changed": False,
        "alpha_changed": False,
        "block_length_changed": False,
        "comparator_changed": False,
        "purchase_recommendation_generated": False,
    }
    base.write_json(outdir / "INFERENCE.json", inference_payload)

    source_hashes = {
        source["study_id"]: {
            "prediction_sha256": source["prediction_sha256"],
            "prediction_bytes": int(source["prediction_bytes"]),
            "prediction_blob_sha": source["prediction_blob_sha"],
            "manifest_blob_sha": source["manifest_blob_sha"],
            "verification_blob_sha": source["verification_blob_sha"],
        }
        for source in prereg["candidate_models"]
    }
    verification = {
        "status": "PASS",
        "study_id": STUDY_ID,
        "data_cutoff": cutoff,
        "current_source_data_rows": current_rows,
        "data_sha256": data_sha,
        "data_prefix_sha256": data_prefix_sha,
        "source_target_range": [401, 1249],
        "evaluation_target_range": [start_target, end_target],
        "target_count": len(observations),
        "prediction_records": len(observations),
        "selection_log_records": len(selection_rows),
        "candidate_model_count": len(MODEL_ORDER),
        "selection_lookback_targets": lookback,
        "selection_training_cutoff_violations": 0,
        "training_cutoff_violations": training_cutoff_violations,
        "leakage_failures": 0,
        "future_predictions": 0,
        "portfolio_geometry_violations": portfolio_geometry_violations,
        "random_geometry_violations": random_geometry_violations,
        "random_bundles_per_target": random_count,
        "random_bundles_total": len(observations) * random_count,
        "no_future_leakage": True,
        "random_baseline_executed": True,
        "independent_research_axis": True,
        "parameter_search": False,
        "variants": 1,
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

    readiness_update = {
        "target_round": 1251,
        "data_cutoff": cutoff,
        "primary_model": "E045_THREE_LINE_DISJOINT_PORTFOLIO_WALKFORWARD_v1",
        "primary_status": "STRICT_FAIL",
        "additional_axis": STUDY_ID,
        "additional_axis_historical_gate_pass": historical_gate_pass,
        "additional_axis_readiness_status": readiness_status,
        "strict_portfolio_pass": False,
        "strict_pass_ready": False,
        "ready_file_exists": False,
        "line_level_output_status": "SUPPRESSED_NOT_READY",
        "final_purchase_freeze_allowed": False,
        "reason": "Historical nested selector evidence is not prospective confirmation; the prospective minimum target count and completion rule remain unspecified.",
    }
    base.write_json(outdir / "READINESS_UPDATE.json", readiness_update)

    completion = {
        "study_id": STUDY_ID,
        "status": "COMPLETE",
        "data_cutoff": cutoff,
        "source_target_range": [401, 1249],
        "evaluation_target_range": [start_target, end_target],
        "target_count": len(observations),
        "historical_strict_gate_pass": historical_gate_pass,
        "strict_portfolio_pass": False,
        "strict_pass_ready": False,
        "readiness_status": readiness_status,
        "evidence_class": "HISTORICAL_NESTED_SELECTOR_SCREEN_NOT_PROSPECTIVE_CONFIRMATION",
        "independent_research_axis": True,
        "purchase_recommendation_generated": False,
    }
    base.write_json(outdir / "COMPLETION.json", completion)

    report = [
        "# E052 — Nested trailing-performance selector for three-line portfolios",
        "",
        "**New research question:** Can one fixed, cutoff-safe selector choose among five already frozen three-line portfolios using only the preceding 100 target rounds' any2 performance, and outperform the exact disjoint-union18 null on the next target?",
        "",
        "## What was executed",
        f"- Historical nested walk-forward: targets {start_target}–{end_target} ({len(observations)} targets).",
        f"- Five frozen candidate portfolios; one selector; trailing window {lookback}; selection metric any2; fixed tie-break order.",
        f"- Matched-random portfolios: {len(observations) * random_count:,} ({random_count} per target), preserving three disjoint six-number lines and union18.",
        f"- Moving-block bootstrap: {bootstrap_reps:,} replicates, block length {block_size}, final remainder retained ({block_rows[-1]['n']} targets).",
        "- Each target's selected model is chosen using only target outcomes through t−1; no target or future outcome enters its own selection.",
        "- This is a historical nested screen, not prospective confirmation.",
        "",
        "## Primary strict metrics",
        "| Metric | Selector mean | Exact null | Delta | Adjusted CI lower | Adjusted CI upper |",
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
        f"- Any2-positive 50-target block share: **{any2_positive_share:.2%}** ({sum(row['any2_positive'] for row in block_rows)}/{len(block_rows)} blocks; minimum 65%).",
        f"- Historical strict gate: **{'PASS' if historical_gate_pass else 'FAIL'}**.",
        f"- Model selection counts: {', '.join(f'{model}={selection_counts.get(model, 0)}' for model in MODEL_ORDER)}.",
        "",
        "## Interpretation and policy effect",
        "- The selector is a new model-selection procedure, not a new independent signal family. It does not modify any source model or its historical predictions.",
        "- Static model scorecards are descriptive; only the single preregistered nested selector is tested against the strict null.",
        "- No threshold, alpha, block length, comparator, candidate model, or lookback was tuned after evaluation.",
        "- STRICT_PASS_READY is not created. Prospective minimum target count and completion rule remain unspecified.",
        "- No purchase recommendation, final purchase lines, freeze, or seal were generated.",
        "",
        "## Source and scope limitations",
        "- The E051 source file includes a 1250 cutoff, but this study uses only its already frozen target rows 401–1249; the target 1250 row is excluded.",
        "- The historical target sample has already been observed and cannot serve as untouched prospective confirmation.",
        "- All source portfolios were independently verified and recomputed against the canonical 1–1249 outcomes before selection.",
    ])
    (outdir / "REPORT.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    manifest_count = base.write_and_verify_manifest(outdir)
    if manifest_count != 10:
        raise AssertionError(f"E052 expected 10 manifest entries, got {manifest_count}")
    print(json.dumps({
        "study_id": STUDY_ID,
        "status": "COMPLETE",
        "data_cutoff": cutoff,
        "targets": len(observations),
        "random_bundles_total": len(observations) * random_count,
        "historical_strict_gate_pass": historical_gate_pass,
        "strict_pass_ready": False,
        "readiness_status": readiness_status,
        "manifest_entries": manifest_count,
        "result_path": str(outdir.relative_to(ROOT)),
    }, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    run(args.date, args.run_id)


if __name__ == "__main__":
    main()
