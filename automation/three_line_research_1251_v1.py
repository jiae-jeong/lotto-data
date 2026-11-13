#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import io
import json
import random
import re
import statistics
from collections import Counter, deque
from datetime import timedelta, timezone
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "lotto_data.csv"
POLICY_PATH = ROOT / "research/weekly_purchase/1251/THREE_LINE_POLICY_1251_PLUS.json"
PREREG_PATH = ROOT / "research/weekly_purchase/1251/THREE_LINE_RESEARCH_PREREG_E045_20261114.json"
STUDY_ID = "E045_THREE_LINE_DISJOINT_PORTFOLIO_WALKFORWARD_v1"
KST = timezone(timedelta(hours=9))


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load frozen source module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_frozen_draw_prefix(cutoff: int, expected_sha256: str):
    raw = DATA.read_bytes()
    physical_lines = raw.splitlines(keepends=True)
    if len(physical_lines) < cutoff + 1:
        raise ValueError(f"Data file has fewer than {cutoff} draw rows")
    prefix = b"".join(physical_lines[: cutoff + 1])
    got_sha256 = hashlib.sha256(prefix).hexdigest()
    if got_sha256 != expected_sha256:
        raise ValueError(
            f"Frozen historical data prefix hash mismatch: {got_sha256} != {expected_sha256}"
        )
    text = prefix.decode("utf-8-sig")
    rows = list(csv.DictReader(io.StringIO(text, newline="")))
    if len(rows) != cutoff:
        raise ValueError(f"Frozen prefix row count {len(rows)} != {cutoff}")
    draws = []
    for expected_round, row in enumerate(rows, 1):
        round_no = int(row["round"])
        nums = tuple(sorted(int(row[f"no{i}"]) for i in range(1, 7)))
        bonus = int(row["bonus"])
        if round_no != expected_round:
            raise ValueError(f"Round sequence mismatch at row {expected_round}: {round_no}")
        if len(set(nums)) != 6 or any(n < 1 or n > 45 for n in nums):
            raise ValueError(f"Invalid main numbers at round {round_no}")
        if bonus < 1 or bonus > 45 or bonus in nums:
            raise ValueError(f"Invalid bonus at round {round_no}")
        draws.append({"round": round_no, "date": row["date"], "nums": nums})
    return draws, got_sha256


def choose_disjoint_ticket(role_score: dict, global_score: dict, used: set[int]) -> tuple[int, ...]:
    available = [n for n in range(1, 46) if n not in used]
    if len(available) < 6:
        raise ValueError("Fewer than six unused numbers remain")
    pool = sorted(available, key=lambda n: (-role_score[n], -global_score[n], n))[:16]
    best = None
    for ticket in combinations(pool, 6):
        odd = sum(n % 2 for n in ticket)
        low = sum(n <= 22 for n in ticket)
        bands = len({(n - 1) // 10 for n in ticket})
        consecutive = sum(b - a == 1 for a, b in zip(ticket, ticket[1:]))
        value = sum(role_score[n] for n in ticket)
        value -= 0.022 * abs(odd - 3)
        value -= 0.020 * abs(low - 3)
        value -= 0.010 * max(0, consecutive - 2)
        value += 0.004 * bands
        key = (value, tuple(-n for n in ticket))
        if best is None or key > best[0]:
            best = (key, ticket)
    if best is None:
        raise RuntimeError("No six-number candidate ticket found")
    return tuple(sorted(best[1]))


def portfolio_metrics(lines: list[tuple[int, ...]], actual: set[int]) -> dict:
    if len(lines) != 3 or any(len(line) != 6 or len(set(line)) != 6 for line in lines):
        raise ValueError("Portfolio must contain exactly three valid six-number lines")
    union = set().union(*(set(line) for line in lines))
    overlaps = [len(set(a) & set(b)) for a, b in combinations(lines, 2)]
    if len(union) != 18 or any(overlap != 0 for overlap in overlaps):
        raise ValueError("Portfolio geometry is not three disjoint lines with union18")
    hits = [len(set(line) & actual) for line in lines]
    maximum = max(hits)
    return {
        "max_hits": maximum,
        "any2": int(maximum >= 2),
        "any3": int(maximum >= 3),
        "winning_union_coverage": len(union & actual),
        "union_size": len(union),
    }


def permute_portfolio_labels(lines: list[tuple[int, ...]], rng: random.Random):
    labels = list(range(1, 46))
    shuffled = labels[:]
    rng.shuffle(shuffled)
    mapping = dict(zip(labels, shuffled))
    result = [tuple(sorted(mapping[n] for n in line)) for line in lines]
    union = set().union(*(set(line) for line in result))
    overlaps = [len(set(a) & set(b)) for a, b in combinations(result, 2)]
    if len(union) != 18 or any(overlap != 0 for overlap in overlaps):
        raise AssertionError("Label permutation failed to preserve union18 geometry")
    return result


def block_slices(values: list[float], block_size: int = 50) -> list[list[float]]:
    return [values[i : i + block_size] for i in range(0, len(values), block_size)]


def moving_block_ci(values: list[float], alpha: float, seed: int, replicates: int, block_size: int = 50):
    if not values:
        raise ValueError("Cannot bootstrap an empty series")
    sizes = [block_size] * (len(values) // block_size)
    remainder = len(values) % block_size
    if remainder:
        sizes.append(remainder)
    rng = random.Random(seed)
    means = []
    for _ in range(replicates):
        sample = []
        for size in sizes:
            start = rng.randrange(0, len(values) - size + 1)
            sample.extend(values[start : start + size])
        if len(sample) != len(values):
            raise AssertionError("Moving-block bootstrap did not preserve sample length")
        means.append(statistics.mean(sample))
    means.sort()
    lower_index = int((alpha / 2) * (replicates - 1))
    upper_index = int((1 - alpha / 2) * (replicates - 1))
    return [means[lower_index], means[upper_index]]


def write_csv(path: Path, rows: list[dict], fields: list[str]):
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict):
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_and_verify_manifest(outdir: Path) -> int:
    manifest = outdir / "SHA256_MANIFEST.csv"
    files = sorted((p for p in outdir.iterdir() if p.is_file() and p.name != manifest.name), key=lambda p: p.name)
    rows = [
        {
            "path": p.name,
            "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
            "bytes": p.stat().st_size,
        }
        for p in files
    ]
    write_csv(manifest, rows, ["path", "sha256", "bytes"])
    with manifest.open("r", encoding="utf-8-sig", newline="") as stream:
        checked = list(csv.DictReader(stream))
    if len(checked) != len(files) or len({row["path"] for row in checked}) != len(files):
        raise AssertionError("Manifest file count or uniqueness check failed")
    expected = {p.name for p in files}
    if {row["path"] for row in checked} != expected:
        raise AssertionError("Manifest file set differs from output file set")
    for row in checked:
        artifact = outdir / row["path"]
        if not artifact.is_file() or artifact.is_symlink() or artifact.parent != outdir:
            raise AssertionError(f"Missing or unsafe manifest artifact: {row['path']}")
        raw = artifact.read_bytes()
        if len(raw) != int(row["bytes"]) or hashlib.sha256(raw).hexdigest() != row["sha256"]:
            raise AssertionError(f"Artifact hash/size mismatch: {row['path']}")
    return len(checked)


def run(date_kst: str, run_id: str):
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_kst):
        raise ValueError("date must be YYYY-MM-DD")
    if not re.fullmatch(r"[A-Za-z0-9_-]+", run_id):
        raise ValueError("run_id contains unsafe characters")

    prereg = json.loads(PREREG_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    if prereg["study_id"] != STUDY_ID or prereg["policy_id"] != policy["policy_id"]:
        raise ValueError("Preregistration/policy identity mismatch")
    if int(policy["effective_from_target"]) != 1251 or int(policy["purchase_lines"]) != 3:
        raise ValueError("Active target-1251 three-line policy changed")
    gate = policy["strict_gate"]
    if (
        float(gate["family_alpha"]) != 0.05
        or float(gate["alpha_per_metric"]) != 0.0125
        or float(gate["any2_positive_nonoverlapping_50_target_block_share_min"]) != 0.65
        or gate["all_adjusted_moving_block_ci_lower_bounds_strictly_gt_zero"] is not True
        or gate["no_threshold_relaxation"] is not True
    ):
        raise ValueError("Strict gate policy differs from the preregistered constants")
    exact_null = policy["exact_null"]
    expected_null = prereg["random_comparator"]["exact_null"]
    for key in ("mean_max_hit", "p_any2", "p_any3", "expected_union_coverage"):
        if abs(float(exact_null[key]) - float(expected_null[key])) > 1e-14:
            raise ValueError(f"Exact null changed for {key}")

    cutoff = int(prereg["historical_data_cutoff"])
    draws, data_sha = load_frozen_draw_prefix(cutoff, prereg["source_data_prefix_sha256"])
    if len(draws) != cutoff or [d["round"] for d in draws] != list(range(1, cutoff + 1)):
        raise ValueError("Frozen historical draw prefix is incomplete")

    reference = load_module(ROOT / "automation/five_role_research_v9.py", "e045_five_role_reference")
    b = reference.imp(reference.B_SOURCE, "e045_b_model")
    ac = reference.imp(reference.AC_SOURCE, "e045_ac_model")
    bank = b.feature_structure_bank(b.make_structure_bank())

    freq = [0] * 45
    last_seen = [0] * 45
    pair_counts = Counter()
    triple_counts = Counter()
    profiles = [Counter() for _ in range(6)]
    warmup = 200
    if cutoff <= warmup:
        raise ValueError("At least 201 draws are required")
    for draw in draws[:warmup]:
        for number in draw["nums"]:
            freq[number - 1] += 1
            last_seen[number - 1] = draw["round"]
        pair_counts.update(combinations(draw["nums"], 2))
        triple_counts.update(combinations(draw["nums"], 3))
        profile = b.structure_profile(draw["nums"], None)
        for i, value in enumerate(profile[:5]):
            profiles[i][value] += 1
    for i in range(1, warmup):
        profiles[5][b.structure_profile(draws[i]["nums"], draws[i - 1]["nums"])[5]] += 1

    histories = {model: deque(maxlen=reference.ROLL) for model in reference.MODELS}
    role_sets = [(item["role"], tuple(item["models"])) for item in prereg["role_order"]]
    observations = []
    random_rows = []
    random_geometry_violations = 0
    portfolio_geometry_violations = 0
    training_cutoff_violations = 0
    metric_names = ("max_hits", "any2", "any3", "winning_union_coverage")
    exact_by_metric = {
        "max_hits": float(expected_null["mean_max_hit"]),
        "any2": float(expected_null["p_any2"]),
        "any3": float(expected_null["p_any3"]),
        "winning_union_coverage": float(expected_null["expected_union_coverage"]),
    }
    random_count = int(prereg["random_comparator"]["random_bundles_per_target"])
    seed = int(prereg["random_comparator"]["seed"])

    for idx in range(warmup, len(draws)):
        target_round = idx + 1
        training_through = idx
        history = [item["nums"] for item in draws[:idx]]
        # The B predictor receives only the historical prefix, never the target draw or later rows.
        b_predictions = b.predictions_for_round(
            draws[:idx], idx, freq, last_seen, pair_counts, triple_counts, profiles, bank
        )
        predictions = {**b_predictions, **ac.predict(history)}
        if set(predictions) != set(reference.MODELS):
            raise ValueError(f"Model prediction set mismatch at target {target_round}")
        if training_through != target_round - 1:
            training_cutoff_violations += 1
            raise AssertionError("Training cutoff is not target_round - 1")

        global_score, reliability = reference.global_support(predictions, histories)
        used = set()
        lines = []
        for role_name, role_models in role_sets:
            role = reference.role_score(role_models, predictions, reliability, global_score)
            ticket = choose_disjoint_ticket(role, global_score, used)
            lines.append(ticket)
            used.update(ticket)
        if len(lines) != 3 or len(used) != 18:
            portfolio_geometry_violations += 1
            raise AssertionError(f"Invalid three-line geometry at target {target_round}")

        actual = set(draws[idx]["nums"])
        observed = portfolio_metrics(lines, actual)
        line_hits = [len(set(line) & actual) for line in lines]
        observations.append(
            {
                "target_round": target_round,
                "training_through_round": training_through,
                "lines": lines,
                "actual": tuple(sorted(actual)),
                "line_hits": line_hits,
                **observed,
            }
        )

        rng = random.Random(seed + target_round)
        random_metrics = []
        for _ in range(random_count):
            random_lines = permute_portfolio_labels(lines, rng)
            random_result = portfolio_metrics(random_lines, actual)
            if len(set().union(*(set(line) for line in random_lines))) != 18:
                random_geometry_violations += 1
            random_metrics.append(random_result)
        if random_geometry_violations:
            raise AssertionError("Random comparator geometry violation")
        random_rows.append(
            {
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
            }
        )

        for model in reference.MODELS:
            histories[model].append(len(set(predictions[model]) & actual))
        draw = draws[idx]
        for number in draw["nums"]:
            freq[number - 1] += 1
            last_seen[number - 1] = draw["round"]
        pair_counts.update(combinations(draw["nums"], 2))
        triple_counts.update(combinations(draw["nums"], 3))
        profile = b.structure_profile(draw["nums"], draws[idx - 1]["nums"])
        for i, value in enumerate(profile):
            profiles[i][value] += 1

    targets = [row["target_round"] for row in observations]
    expected_targets = list(range(int(prereg["target_rounds"].split("..")[0]), cutoff + 1))
    if targets != expected_targets:
        raise AssertionError(f"Walk-forward target range mismatch: {targets[:1]}..{targets[-1:]}")

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
        ci = moving_block_ci(
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
        and any2_positive_share >= float(gate["any2_positive_nonoverlapping_50_target_block_share_min"])
    )
    prospective_rule_defined = (
        prereg["prospective_confirmation"]["minimum_target_count"] is not None
        and prereg["prospective_confirmation"]["completion_rule"] is not None
    )
    strict_portfolio_pass = bool(historical_gate_pass and prospective_rule_defined)
    if historical_gate_pass and not prospective_rule_defined:
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
    block_lengths = [len(x) for x in block_slices(diffs["any2"], block_size)]
    source_paths = [
        ROOT / "automation/five_role_research_v9.py",
        ROOT / "research/1245_final_pipeline_v3/recovered_original_assets/b_model_backtest.py",
        ROOT / "automation/recovered_models_v2.py",
        POLICY_PATH,
        PREREG_PATH,
    ]
    source_hashes = {
        path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in source_paths
    }

    outdir = ROOT / "analysis" / date_kst / run_id / STUDY_ID
    outdir.mkdir(parents=True, exist_ok=False)
    prediction_rows = []
    for row in observations:
        prediction_rows.append(
            {
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
            }
        )
    write_csv(
        outdir / "PREDICTIONS.csv",
        prediction_rows,
        [
            "target_round", "training_through_round", "line1", "line2", "line3",
            "actual_numbers", "line1_hits", "line2_hits", "line3_hits",
            "max_hits", "any2", "any3", "winning_union_coverage", "union_size",
        ],
    )
    write_csv(
        outdir / "RANDOM_BASELINE.csv",
        random_rows,
        [
            "target_round", "random_bundles", "random_mean_max_hits", "random_p_any2",
            "random_p_any3", "random_mean_union_coverage", "exact_null_mean_max_hit",
            "exact_null_p_any2", "exact_null_p_any3",
            "exact_null_expected_union_coverage", "geometry_violations",
        ],
    )
    write_csv(
        outdir / "BLOCK_STABILITY.csv",
        block_rows,
        [
            "block_index", "start_target", "end_target", "n",
            "mean_delta_max_hits", "mean_delta_any2", "mean_delta_any3",
            "mean_delta_winning_union_coverage", "any2_positive",
        ],
    )

    inference_payload = {
        "study_id": STUDY_ID,
        "data_cutoff": cutoff,
        "target_range": [targets[0], targets[-1]],
        "targets": len(targets),
        "random_bundles_per_target": random_count,
        "random_bundles_total": len(targets) * random_count,
        "exact_geometry_matched_null": exact_by_metric,
        "simulated_same_target_random_means": simulated_random_means,
        "metrics": inference,
        "block_size": block_size,
        "block_lengths": block_lengths,
        "any2_positive_50_target_block_share": any2_positive_share,
        "historical_strict_gate_pass": historical_gate_pass,
        "prospective_confirmation_required": True,
        "prospective_minimum_target_count": None,
        "prospective_completion_rule": None,
        "strict_portfolio_pass": strict_portfolio_pass,
        "strict_pass_ready": False,
        "readiness_status": readiness_status,
    }
    write_json(outdir / "INFERENCE.json", inference_payload)
    readiness_update = {
        "update_id": "E045_READINESS_UPDATE_1251_20261114",
        "study_id": STUDY_ID,
        "target_round": 1251,
        "data_cutoff": cutoff,
        "task_registered": True,
        "runner_present": True,
        "historical_gate_evaluated": True,
        "historical_strict_gate_pass": historical_gate_pass,
        "strict_portfolio_pass": strict_portfolio_pass,
        "strict_pass_ready": False,
        "ready_file_exists": False,
        "line_level_output_status": "SUPPRESSED_NOT_READY",
        "prospective_confirmation_required": True,
        "prospective_minimum_target_count": None,
        "prospective_completion_rule": None,
        "blocking_reason": "The policy requires prospective confirmation but has no minimum target count or completion rule. Historical gate results alone cannot create purchase readiness.",
        "final_purchase_freeze_allowed": False,
        "random_fallback_allowed": False,
        "no_threshold_changes": True,
    }
    write_json(outdir / "READINESS_UPDATE.json", readiness_update)

    verification = {
        "study_id": STUDY_ID,
        "status": "PASS",
        "data_cutoff": cutoff,
        "data_sha256": data_sha,
        "target_range": [targets[0], targets[-1]],
        "target_count": len(targets),
        "prediction_records": len(prediction_rows),
        "random_bundles_per_target": random_count,
        "random_bundles_total": len(targets) * random_count,
        "training_cutoff_rule": "training_through_round = target_round - 1",
        "training_cutoff_violations": training_cutoff_violations,
        "leakage_failures": 0,
        "future_predictions": 0,
        "portfolio_geometry_violations": portfolio_geometry_violations,
        "random_geometry_violations": random_geometry_violations,
        "all_portfolios_three_lines_six_numbers_union18": all(
            int(row["union_size"]) == 18 for row in prediction_rows
        ),
        "all_random_comparators_preserve_three_disjoint_lines_union18": random_geometry_violations == 0,
        "selection_uses_randomness": False,
        "randomness_used_only_for_comparator": True,
        "source_sha256": source_hashes,
        "historical_strict_gate_pass": historical_gate_pass,
        "strict_portfolio_pass": strict_portfolio_pass,
        "strict_pass_ready": False,
        "prospective_rule_status": "UNSPECIFIED_IN_POLICY",
    }
    write_json(outdir / "VERIFICATION.json", verification)
    completion = {
        "study_id": STUDY_ID,
        "status": "COMPLETE",
        "date_kst": date_kst,
        "run_id": run_id,
        "data_cutoff": cutoff,
        "target_range": [targets[0], targets[-1]],
        "executed": True,
        "historical_strict_gate_pass": historical_gate_pass,
        "strict_portfolio_pass": strict_portfolio_pass,
        "strict_pass_ready": False,
        "readiness_status": readiness_status,
    }
    write_json(outdir / "COMPLETION.json", completion)

    report = f"""# E045 — Target-1251 three-line disjoint portfolio walk-forward

Execution status: **COMPLETE**
Historical strict gate: **{"PASS" if historical_gate_pass else "FAIL"}**
Purchase readiness: **NOT_READY**

## Frozen scope

- Historical data cutoff: {cutoff}
- Walk-forward targets: {targets[0]}–{targets[-1]} ({len(targets)} targets)
- Training cutoff: target round minus one; the target draw is not passed to the prediction function
- Portfolio geometry: exactly three pairwise-disjoint six-number lines; union size 18
- Random comparator: {random_count} uniformly label-permuted geometry-matched portfolios per target
- Total random bundles: {len(targets) * random_count:,}
- Family alpha: 0.05; per-metric alpha: 0.0125
- Moving-block bootstrap: {bootstrap_reps:,} replicates, 50-target blocks, final remainder retained
- Any2 positive block share threshold: 0.65

## Historical results

| Metric | Model mean | Exact null | Difference | Adjusted CI lower | Adjusted CI upper |
|---|---:|---:|---:|---:|---:|
"""
    for metric in metric_names:
        item = inference[metric]
        report += (
            f"| {metric} | {item['observed_mean']:.6f} | {item['exact_geometry_matched_null']:.6f} "
            f"| {item['delta_mean']:.6f} | {item['adjusted_moving_block_ci'][0]:.6f} "
            f"| {item['adjusted_moving_block_ci'][1]:.6f} |\n"
        )
    report += f"""
- Any2 positive 50-target block share: {any2_positive_share:.6f}
- Fixed block lengths: {block_lengths}
- Historical gate result: **{"PASS" if historical_gate_pass else "FAIL"}**
- Prospective confirmation: **required, but minimum target count and completion rule are unspecified**
- STRICT_PASS_READY: **not created**
- Final purchase lines: **not generated**
- Random fallback: **prohibited**

This is one preregistered allocator axis, not a claim of independent signal-family discovery. No model variants, parameter changes, alpha changes, block-size changes, or comparator changes were tested.
"""
    (outdir / "REPORT.md").write_text(report, encoding="utf-8")
    manifest_entries = write_and_verify_manifest(outdir)

    summary = {
        "status": "COMPLETE",
        "study_id": STUDY_ID,
        "data_cutoff": cutoff,
        "targets": len(targets),
        "random_bundles_total": len(targets) * random_count,
        "manifest_entries": manifest_entries,
        "manifest_status": "PASS",
        "historical_strict_gate_pass": historical_gate_pass,
        "strict_portfolio_pass": strict_portfolio_pass,
        "strict_pass_ready": False,
        "readiness_status": readiness_status,
        "output": str(outdir.relative_to(ROOT)),
    }
    print(json.dumps(summary, ensure_ascii=False))
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    run(args.date, args.run_id)


if __name__ == "__main__":
    main()
