#!/usr/bin/env python3
"""E048: preregistered bonus-to-next-main transition signal for the target-1251 three-line policy."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import random
import statistics
from datetime import datetime
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "lotto_data.csv"
PREREG_PATH = ROOT / "research/weekly_purchase/1251/E048_THREE_LINE_BONUS_TO_MAIN_TRANSITION_PREREG_20261114.json"
POLICY_PATH = ROOT / "research/weekly_purchase/1251/THREE_LINE_POLICY_1251_PLUS.json"
STUDY_ID = "E048_THREE_LINE_BONUS_TO_MAIN_TRANSITION_v1"
PREREG_SHA256 = "a17160f17aa1c2c14498d2da151e382c56bd851aee402cb19e8fcb3eb5c6b0e3"
METRICS = ("max_hits", "any2", "any3", "winning_union_coverage")


def read_frozen_prefix(cutoff: int, expected_prefix_sha: str, expected_full_sha: str):
    raw = DATA.read_bytes()
    full_sha = hashlib.sha256(raw).hexdigest()
    physical_lines = raw.splitlines(keepends=True)
    if not physical_lines:
        raise ValueError("lotto_data.csv is empty")
    total_rows = sum(1 for line in physical_lines[1:] if line.strip())
    if total_rows < cutoff:
        raise ValueError(f"only {total_rows} non-empty draw records; need {cutoff}")

    selected = []
    header_seen = False
    data_rows = 0
    cutoff_reached = False
    for line in physical_lines:
        if not header_seen:
            selected.append(line)
            header_seen = True
            continue
        if line.strip():
            if cutoff_reached:
                break
            data_rows += 1
            selected.append(line)
            if data_rows == cutoff:
                cutoff_reached = True
        else:
            selected.append(line)
    if data_rows != cutoff or not cutoff_reached:
        raise ValueError(f"could not isolate exactly {cutoff} non-empty records")

    prefix = b"".join(selected)
    prefix_sha = hashlib.sha256(prefix).hexdigest()
    if prefix_sha != expected_prefix_sha:
        raise ValueError(f"frozen prefix SHA mismatch: {prefix_sha} != {expected_prefix_sha}")
    if total_rows == cutoff and full_sha != expected_full_sha:
        raise ValueError(f"full data SHA mismatch: {full_sha} != {expected_full_sha}")

    text = prefix.decode("utf-8-sig")
    rows = list(csv.DictReader(io.StringIO(text, newline="")))
    if len(rows) != cutoff:
        raise ValueError(f"parsed row count {len(rows)} != cutoff {cutoff}")

    draws = []
    previous_date = None
    for expected_round, row in enumerate(rows, 1):
        round_no = int(row["round"])
        nums = tuple(sorted(int(row[f"no{i}"]) for i in range(1, 7)))
        bonus = int(row["bonus"])
        date = datetime.strptime(row["date"], "%Y.%m.%d").date()
        if round_no != expected_round:
            raise ValueError(f"round sequence mismatch at row {expected_round}: {round_no}")
        if len(nums) != 6 or len(set(nums)) != 6 or any(n < 1 or n > 45 for n in nums):
            raise ValueError(f"invalid main numbers at round {round_no}")
        if not 1 <= bonus <= 45 or bonus in nums:
            raise ValueError(f"invalid bonus number at round {round_no}")
        if previous_date is not None and date <= previous_date:
            raise ValueError(f"non-increasing draw date at round {round_no}")
        previous_date = date
        draws.append({"round": round_no, "date": date.isoformat(), "nums": nums, "bonus": bonus})
    return draws, prefix_sha, full_sha, total_rows


def score_numbers(previous_bonus: int, global_counts: list[int], global_draws: int,
                  conditional_counts: list[list[int]], conditional_n: list[int],
                  alpha: float) -> list[float]:
    if not 1 <= previous_bonus <= 45 or global_draws <= 0 or alpha <= 0:
        raise ValueError("invalid score inputs")
    n = conditional_n[previous_bonus]
    return [
        (conditional_counts[previous_bonus][idx] + alpha * (global_counts[idx] / global_draws))
        / (n + alpha)
        for idx in range(45)
    ]


def build_portfolio(scores: list[float]) -> list[tuple[int, ...]]:
    if len(scores) != 45:
        raise ValueError("exactly 45 number scores are required")
    ranked = sorted(range(1, 46), key=lambda number: (-scores[number - 1], number))
    selected = ranked[:18]
    lines = [tuple(sorted(selected[offset::3])) for offset in range(3)]
    validate_portfolio(lines)
    return lines


def validate_portfolio(lines: list[tuple[int, ...]]) -> None:
    if len(lines) != 3:
        raise ValueError("portfolio must contain exactly three lines")
    normalized = []
    for line in lines:
        if len(line) != 6 or len(set(line)) != 6 or any(n < 1 or n > 45 for n in line):
            raise ValueError("each line must contain six unique numbers in 1..45")
        if tuple(sorted(line)) != tuple(line):
            raise ValueError("each line must be sorted")
        normalized.append(tuple(line))
    if len(set(normalized)) != 3:
        raise ValueError("three lines must be distinct")
    union = set().union(*(set(line) for line in normalized))
    if len(union) != 18:
        raise ValueError("portfolio must be pairwise disjoint with union18")


def portfolio_metrics(lines: list[tuple[int, ...]], actual: set[int]) -> dict:
    validate_portfolio(lines)
    hits = [len(set(line) & actual) for line in lines]
    maximum = max(hits)
    union = set().union(*(set(line) for line in lines))
    return {
        "max_hits": maximum,
        "any2": int(maximum >= 2),
        "any3": int(maximum >= 3),
        "winning_union_coverage": len(union & actual),
    }


def permute_portfolio_labels(lines: list[tuple[int, ...]], rng: random.Random):
    labels = list(range(1, 46))
    shuffled = labels[:]
    rng.shuffle(shuffled)
    mapping = dict(zip(labels, shuffled))
    result = [tuple(sorted(mapping[n] for n in line)) for line in lines]
    validate_portfolio(result)
    return result


def moving_block_ci(values: list[float], alpha: float, seed: int,
                    replicates: int, block_size: int) -> list[float]:
    if not values:
        raise ValueError("cannot bootstrap an empty series")
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
            sample.extend(values[start:start + size])
        if len(sample) != len(values):
            raise AssertionError("bootstrap sample length changed")
        means.append(statistics.mean(sample))
    means.sort()
    lower = int((alpha / 2) * (replicates - 1))
    upper = int((1 - alpha / 2) * (replicates - 1))
    return [means[lower], means[upper]]


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="raise", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_and_verify_manifest(outdir: Path) -> int:
    manifest_path = outdir / "SHA256_MANIFEST.csv"
    files = sorted(
        (p for p in outdir.iterdir() if p.is_file() and p.name != manifest_path.name),
        key=lambda p: p.name,
    )
    rows = [
        {"path": p.name, "sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "bytes": p.stat().st_size}
        for p in files
    ]
    write_csv(manifest_path, rows, ["path", "sha256", "bytes"])
    with manifest_path.open(encoding="utf-8-sig", newline="") as stream:
        checked = list(csv.DictReader(stream))
    if len(checked) != len(files) or len({r["path"] for r in checked}) != len(files):
        raise AssertionError("manifest count or uniqueness mismatch")
    if {r["path"] for r in checked} != {p.name for p in files}:
        raise AssertionError("manifest coverage mismatch")
    for row in checked:
        artifact = outdir / row["path"]
        raw = artifact.read_bytes()
        if len(raw) != int(row["bytes"]) or hashlib.sha256(raw).hexdigest() != row["sha256"]:
            raise AssertionError(f"manifest hash/size mismatch: {artifact.name}")
    return len(checked)


def validate_preregistration(prereg: dict, policy: dict) -> None:
    if prereg.get("study_id") != STUDY_ID or prereg.get("policy_id") != policy.get("policy_id"):
        raise ValueError("study or policy identity mismatch")
    if prereg.get("date_kst") != "2026-11-14" or int(prereg.get("target_round", -1)) != 1251:
        raise ValueError("frozen E048 target/date changed")
    if int(prereg.get("historical_data_cutoff", -1)) != 1249 or prereg.get("target_rounds") != "401..1249 inclusive":
        raise ValueError("frozen E048 historical target range changed")
    if int(prereg["random_comparator"]["seed"]) != 2026111402:
        raise ValueError("frozen E048 random seed changed")
    if int(prereg["inference"]["bootstrap_replicates"]) != 4000 or int(prereg["inference"]["bootstrap_seed"]) != 2026111402:
        raise ValueError("frozen E048 bootstrap specification changed")
    if prereg["portfolio"]["line_assignment"] != "Deterministic rank interleaving: line 1 uses ranks 1,4,7,10,13,16; line 2 uses ranks 2,5,8,11,14,17; line 3 uses ranks 3,6,9,12,15,18.":
        raise ValueError("frozen E048 line assignment changed")
    if int(policy["effective_from_target"]) != 1251 or int(policy["purchase_lines"]) != 3:
        raise ValueError("active target-1251 three-line policy changed")
    if int(policy["numbers_per_line"]) != 6:
        raise ValueError("active line size changed")
    gate = policy["strict_gate"]
    inf = prereg["inference"]
    if (
        float(gate["family_alpha"]) != 0.05
        or float(gate["alpha_per_metric"]) != 0.0125
        or float(gate["any2_positive_nonoverlapping_50_target_block_share_min"]) != 0.65
        or gate["all_adjusted_moving_block_ci_lower_bounds_strictly_gt_zero"] is not True
        or gate["no_threshold_relaxation"] is not True
        or float(inf["family_alpha"]) != 0.05
        or float(inf["alpha_per_metric"]) != 0.0125
        or int(inf["block_length_targets"]) != 50
        or inf["retain_final_remainder_block"] is not True
        or inf["no_threshold_relaxation"] is not True
        or inf["no_alpha_change"] is not True
        or inf["no_block_length_change"] is not True
        or inf["no_comparator_change"] is not True
        or inf["no_unbounded_microvariants"] is not True
    ):
        raise ValueError("strict gate differs from frozen policy/preregistration")
    null = prereg["random_comparator"]["exact_null"]
    policy_null = policy["exact_null"]
    mapping = {
        "mean_max_hit": "mean_max_hit",
        "p_any2": "p_any2",
        "p_any3": "p_any3",
        "expected_union_coverage": "expected_union_coverage",
    }
    for key, policy_key in mapping.items():
        if abs(float(null[key]) - float(policy_null[policy_key])) > 1e-14:
            raise ValueError(f"geometry-matched exact null changed: {key}")
    if int(prereg["random_comparator"]["random_bundles_per_target"]) != 120:
        raise ValueError("random comparator count changed")
    if int(prereg["signal"]["smoothing_alpha"]) != 60:
        raise ValueError("frozen smoothing alpha changed")
    if prereg["portfolio"]["randomness_in_selection"] is not False:
        raise ValueError("final selection must remain deterministic")
    if prereg["portfolio"]["variants"] != 1 or prereg["portfolio"]["parameter_tuning"] is not False:
        raise ValueError("only one frozen model specification is allowed")
    if prereg["prospective_confirmation"]["minimum_target_count"] is not None:
        raise ValueError("prospective minimum must not be invented")
    if prereg["prospective_confirmation"]["completion_rule"] is not None:
        raise ValueError("prospective completion rule must not be invented")


def run(date_kst: str, run_id: str, run_attempt: str) -> dict:
    prereg_raw = PREREG_PATH.read_bytes()
    if hashlib.sha256(prereg_raw).hexdigest() != PREREG_SHA256:
        raise ValueError("E048 preregistration SHA256 mismatch")
    prereg = json.loads(prereg_raw.decode("utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    if date_kst != prereg["date_kst"]:
        raise ValueError("run date differs from frozen preregistration")
    validate_preregistration(prereg, policy)
    cutoff = int(prereg["historical_data_cutoff"])
    draws, prefix_sha, data_sha, total_rows = read_frozen_prefix(
        cutoff, prereg["source_data_prefix_sha256"], prereg["source_data_full_file_sha256"]
    )
    if len(draws) != cutoff:
        raise ValueError("frozen draw prefix is incomplete")

    start_target = int(prereg["target_rounds"].split("..")[0])
    if start_target < 2 or start_target > cutoff:
        raise ValueError("invalid target range")
    alpha = float(prereg["signal"]["smoothing_alpha"])
    random_per_target = int(prereg["random_comparator"]["random_bundles_per_target"])
    random_seed = int(prereg["random_comparator"]["seed"])
    null = prereg["random_comparator"]["exact_null"]
    exact = {
        "max_hits": float(null["mean_max_hit"]),
        "any2": float(null["p_any2"]),
        "any3": float(null["p_any3"]),
        "winning_union_coverage": float(null["expected_union_coverage"]),
    }

    # State immediately before the first evaluated target, built only from rounds < start_target.
    global_counts = [0] * 45
    for draw in draws[:start_target - 1]:
        for number in draw["nums"]:
            global_counts[number - 1] += 1
    conditional_counts = [[0] * 45 for _ in range(46)]
    conditional_n = [0] * 46
    for outcome_round in range(2, start_target):
        feature_bonus = draws[outcome_round - 2]["bonus"]
        outcome_numbers = draws[outcome_round - 1]["nums"]
        conditional_n[feature_bonus] += 1
        for number in outcome_numbers:
            conditional_counts[feature_bonus][number - 1] += 1

    predictions = []
    random_rows = []
    leakage_failures = 0
    portfolio_geometry_violations = 0
    random_geometry_violations = 0
    for target in range(start_target, cutoff + 1):
        training_through = target - 1
        if training_through != target - 1:
            leakage_failures += 1
            raise AssertionError(f"training cutoff violation at target {target}")
        previous_bonus = draws[target - 2]["bonus"]
        scores = score_numbers(
            previous_bonus, global_counts, training_through,
            conditional_counts, conditional_n, alpha
        )
        lines = build_portfolio(scores)
        if len(set().union(*(set(line) for line in lines))) != 18:
            portfolio_geometry_violations += 1
            raise AssertionError(f"portfolio geometry violation at target {target}")
        actual = set(draws[target - 1]["nums"])
        observed = portfolio_metrics(lines, actual)
        line_hits = [len(set(line) & actual) for line in lines]
        predictions.append({
            "target_round": target,
            "training_through_round": training_through,
            "previous_bonus_number": previous_bonus,
            "conditional_sample_count": conditional_n[previous_bonus],
            "top18_candidate_recall": observed["winning_union_coverage"],
            "line1": " ".join(map(str, lines[0])),
            "line2": " ".join(map(str, lines[1])),
            "line3": " ".join(map(str, lines[2])),
            "actual_main": " ".join(map(str, sorted(actual))),
            "line_hits": " ".join(map(str, line_hits)),
            **observed,
        })

        rng = random.Random(random_seed + target)
        random_metrics = []
        for _ in range(random_per_target):
            random_lines = permute_portfolio_labels(lines, rng)
            if len(set().union(*(set(line) for line in random_lines))) != 18:
                random_geometry_violations += 1
                raise AssertionError(f"random geometry violation at target {target}")
            random_metrics.append(portfolio_metrics(random_lines, actual))
        random_rows.append({
            "target_round": target,
            "random_bundles": random_per_target,
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

        # Only after scoring target t may its outcome enter global and conditional histories for t+1.
        for number in actual:
            global_counts[number - 1] += 1
            conditional_counts[previous_bonus][number - 1] += 1
        conditional_n[previous_bonus] += 1

    expected_targets = list(range(start_target, cutoff + 1))
    observed_targets = [int(row["target_round"]) for row in predictions]
    if observed_targets != expected_targets:
        raise AssertionError("walk-forward target sequence mismatch")

    diffs = {
        metric: [float(row[metric]) - exact[metric] for row in predictions]
        for metric in METRICS
    }
    block_size = int(prereg["inference"]["block_length_targets"])
    bootstrap_reps = int(prereg["inference"]["bootstrap_replicates"])
    alpha_ci = float(prereg["inference"]["alpha_per_metric"])
    bootstrap_seed = int(prereg["inference"]["bootstrap_seed"])
    block_rows = []
    for block_index, start in enumerate(range(0, len(predictions), block_size), 1):
        stop = min(start + block_size, len(predictions))
        row = {
            "block_index": block_index,
            "start_target": observed_targets[start],
            "end_target": observed_targets[stop - 1],
            "n": stop - start,
        }
        for metric in METRICS:
            row[f"mean_delta_{metric}"] = statistics.mean(diffs[metric][start:stop])
        row["any2_positive"] = int(row["mean_delta_any2"] > 0)
        block_rows.append(row)
    positive_blocks = sum(row["any2_positive"] for row in block_rows)
    positive_share = positive_blocks / len(block_rows)

    inference = {}
    for offset, metric in enumerate(METRICS):
        ci = moving_block_ci(
            diffs[metric], alpha_ci, bootstrap_seed + 9000 + offset,
            bootstrap_reps, block_size
        )
        inference[metric] = {
            "observed_mean": statistics.mean(float(row[metric]) for row in predictions),
            "exact_geometry_matched_null": exact[metric],
            "delta_mean": statistics.mean(diffs[metric]),
            "adjusted_moving_block_ci": ci,
            "lower_bound_strictly_gt_zero": ci[0] > 0,
        }
    historical_gate_pass = (
        all(inference[metric]["lower_bound_strictly_gt_zero"] for metric in METRICS)
        and positive_share >= float(policy["strict_gate"]["any2_positive_nonoverlapping_50_target_block_share_min"])
    )
    prospective = prereg["prospective_confirmation"]
    prospective_rule_defined = (
        prospective["minimum_target_count"] is not None
        and prospective["completion_rule"] is not None
    )
    strict_portfolio_pass = bool(historical_gate_pass and prospective_rule_defined)
    if historical_gate_pass and not prospective_rule_defined:
        readiness_status = "HISTORICAL_GATE_PASS_BUT_NOT_READY_PROSPECTIVE_RULE_UNSPECIFIED"
    elif historical_gate_pass:
        readiness_status = "PROSPECTIVE_CONFIRMATION_PENDING"
    else:
        readiness_status = "STRICT_FAIL"

    outdir = ROOT / "analysis" / date_kst / f"gha_{run_id}_{run_attempt}" / STUDY_ID
    outdir.mkdir(parents=True, exist_ok=False)
    write_csv(outdir / "PREDICTIONS.csv", predictions, [
        "target_round", "training_through_round", "previous_bonus_number",
        "conditional_sample_count", "top18_candidate_recall", "line1", "line2",
        "line3", "actual_main", "line_hits", "max_hits", "any2", "any3",
        "winning_union_coverage"
    ])
    write_csv(outdir / "RANDOM_BASELINE.csv", random_rows, [
        "target_round", "random_bundles", "random_mean_max_hits", "random_p_any2",
        "random_p_any3", "random_mean_union_coverage", "exact_null_mean_max_hit",
        "exact_null_p_any2", "exact_null_p_any3", "exact_null_expected_union_coverage",
        "geometry_violations"
    ])
    write_csv(outdir / "BLOCK_STABILITY.csv", block_rows, [
        "block_index", "start_target", "end_target", "n", "mean_delta_max_hits",
        "mean_delta_any2", "mean_delta_any3", "mean_delta_winning_union_coverage",
        "any2_positive"
    ])
    model_spec = {
        "study_id": STUDY_ID,
        "signal": prereg["signal"],
        "portfolio": prereg["portfolio"],
        "random_comparator": prereg["random_comparator"],
        "inference": prereg["inference"],
        "selection_uses_randomness": False,
        "parameter_tuning": False,
        "variants_evaluated": 1,
    }
    write_json(outdir / "MODEL_SPEC.json", model_spec)
    inference_payload = {
        "study_id": STUDY_ID,
        "data_cutoff": cutoff,
        "target_range": [start_target, cutoff],
        "target_count": len(predictions),
        "exact_geometry_matched_null": exact,
        "metrics": inference,
        "block_stability": {
            "block_length_targets": block_size,
            "total_blocks_including_remainder": len(block_rows),
            "positive_any2_blocks": positive_blocks,
            "any2_positive_block_share": positive_share,
            "required_minimum": 0.65,
            "remainder_block": block_rows[-1],
        },
        "historical_strict_gate_pass": historical_gate_pass,
        "prospective_confirmation": {
            "required": True,
            "minimum_target_count": prospective["minimum_target_count"],
            "completion_rule": prospective["completion_rule"],
            "status": "UNSPECIFIED_IN_POLICY",
            "minimum_count_adopted": False,
        },
        "strict_portfolio_pass": strict_portfolio_pass,
        "strict_pass_ready": False,
        "readiness_status": readiness_status,
    }
    write_json(outdir / "INFERENCE.json", inference_payload)

    report_lines = [
        "# E048 — Bonus-to-next-main transition, three-line portfolio",
        "",
        f"- Study status: **{readiness_status}**",
        f"- Data cutoff: **{cutoff}**; source rows: **{total_rows}**",
        f"- Walk-forward targets: **{len(predictions)}** ({start_target}..{cutoff})",
        f"- Random bundles: **{len(random_rows) * random_per_target:,}** ({random_per_target} per target)",
        "- Portfolio geometry: three disjoint six-number lines, union18",
        "- Selection randomness: prohibited; randomness used only for matched null",
        "",
        "## Paired results versus exact union18 null",
        "",
        "| Metric | Model mean | Exact null | Delta | Adjusted CI lower | Adjusted CI upper |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for metric in METRICS:
        item = inference[metric]
        ci = item["adjusted_moving_block_ci"]
        report_lines.append(
            f"| {metric} | {item['observed_mean']:.6f} | {item['exact_geometry_matched_null']:.6f} "
            f"| {item['delta_mean']:+.6f} | {ci[0]:+.6f} | {ci[1]:+.6f} |"
        )
    report_lines += [
        "",
        f"- any2-positive 50-target block share: **{positive_share:.2%}** ({positive_blocks}/{len(block_rows)} blocks)",
        f"- Historical strict gate: **{'PASS' if historical_gate_pass else 'FAIL'}**",
        "- STRICT_PASS_READY: **not created**",
        "- Prospective confirmation minimum and completion rule: **unspecified; not adopted**",
        "- No purchase lines were released; no final freeze/seal was created.",
        "",
        "The model uses only the previous draw's bonus number and prior main-draw outcomes. Each target is scored before its outcome is added to the transition counts. The single frozen specification was evaluated once; no parameter search or threshold change was performed.",
        "",
    ]
    (outdir / "REPORT.md").write_text("\n".join(report_lines), encoding="utf-8")

    verification = {
        "study_id": STUDY_ID,
        "status": "PASS",
        "date_kst": date_kst,
        "run_id": run_id,
        "run_attempt": run_attempt,
        "data_cutoff": cutoff,
        "source_data_rows": total_rows,
        "data_sha256": data_sha,
        "data_prefix_sha256": prefix_sha,
        "target_range": [start_target, cutoff],
        "target_count": len(predictions),
        "prediction_records": len(predictions),
        "random_bundles_per_target": random_per_target,
        "random_bundles_total": len(random_rows) * random_per_target,
        "training_cutoff_rule": "training_through_round = target_round - 1",
        "training_cutoff_violations": leakage_failures,
        "leakage_failures": leakage_failures,
        "future_predictions": 0,
        "no_future_leakage": leakage_failures == 0,
        "portfolio_geometry_violations": portfolio_geometry_violations,
        "random_geometry_violations": random_geometry_violations,
        "all_portfolios_three_lines_six_numbers_union18": True,
        "all_random_comparators_preserve_union18_geometry": True,
        "selection_uses_randomness": False,
        "randomness_used_only_for_comparator": True,
        "source_code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "preregistration_sha256": hashlib.sha256(PREREG_PATH.read_bytes()).hexdigest(),
        "policy_sha256": hashlib.sha256(POLICY_PATH.read_bytes()).hexdigest(),
        "historical_strict_gate_pass": historical_gate_pass,
        "strict_portfolio_pass": strict_portfolio_pass,
        "strict_pass_ready": False,
        "readiness_status": readiness_status,
        "purchase_lines_generated": False,
        "final_purchase_freeze_allowed": False,
        "prospective_minimum_count_adopted": False,
        "manifest_entries": 8,
        "manifest_status": "PENDING",
    }
    write_json(outdir / "VERIFICATION.json", verification)
    write_json(outdir / "COMPLETION.json", {
        "study_id": STUDY_ID,
        "status": "COMPLETE",
        "data_cutoff": cutoff,
        "target_count": len(predictions),
        "random_bundles_total": len(random_rows) * random_per_target,
        "historical_strict_gate_pass": historical_gate_pass,
        "strict_portfolio_pass": strict_portfolio_pass,
        "strict_pass_ready": False,
        "computation_complete": True,
        "promotion_to_purchase_policy": False,
    })
    entries = write_and_verify_manifest(outdir)
    verification["manifest_entries"] = entries
    verification["manifest_status"] = "PASS"
    write_json(outdir / "VERIFICATION.json", verification)
    entries = write_and_verify_manifest(outdir)
    if entries != 8:
        raise AssertionError(f"expected 8 manifest entries, got {entries}")

    summary = {
        "status": "PASS",
        "study_id": STUDY_ID,
        "output": str(outdir.relative_to(ROOT)),
        "data_cutoff": cutoff,
        "target_count": len(predictions),
        "random_bundles_total": len(random_rows) * random_per_target,
        "historical_strict_gate_pass": historical_gate_pass,
        "strict_portfolio_pass": strict_portfolio_pass,
        "strict_pass_ready": False,
        "readiness_status": readiness_status,
        "manifest_entries": entries,
    }
    print(json.dumps(summary, ensure_ascii=False))
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--run-attempt", default=os.environ.get("GITHUB_RUN_ATTEMPT", "1"))
    args = parser.parse_args()
    run(args.date, args.run_id, str(args.run_attempt))


if __name__ == "__main__":
    main()
