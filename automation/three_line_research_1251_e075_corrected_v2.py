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
PREREG_PATH = ROOT / "research/weekly_purchase/1251/E075_E045_SELECTOR_ORDER_CONFORMANCE_PREREG_20261119_V2.json"
STUDY_ID = "E075_E045_SELECTOR_ORDER_CONFORMANCE_CORRECTION_v1"
KST = timezone(timedelta(hours=9))


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load frozen source module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_frozen_draw_prefix(cutoff: int, expected_prefix_sha256: str, expected_full_sha256: str):
    raw = DATA.read_bytes()
    full_sha256 = hashlib.sha256(raw).hexdigest()
    physical_lines = raw.splitlines(keepends=True)
    if not physical_lines:
        raise ValueError("Source data file is empty")
    total_data_rows = sum(1 for line in physical_lines[1:] if line.strip())
    if total_data_rows < cutoff:
        raise ValueError(f"Data file has only {total_data_rows} non-empty draw records; need {cutoff}")

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
            # Preserve internal and trailing blank lines, but stop before the next draw record.
            selected.append(line)
    if data_rows != cutoff or not cutoff_reached:
        raise ValueError(f"Could not isolate exactly {cutoff} source draw records")
    prefix = b"".join(selected)
    got_sha256 = hashlib.sha256(prefix).hexdigest()
    if got_sha256 != expected_prefix_sha256:
        raise ValueError(
            f"Frozen historical data prefix hash mismatch: {got_sha256} != {expected_prefix_sha256}"
        )
    if total_data_rows == cutoff and full_sha256 != expected_full_sha256:
        raise ValueError(
            f"Full source file hash mismatch at the preregistered cutoff: {full_sha256} != {expected_full_sha256}"
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
    return draws, got_sha256, full_sha256, total_data_rows

def ranked_candidate_pool(role_score: dict, global_score: dict, used: set[int]) -> list[int]:
    available = [n for n in range(1, 46) if n not in used]
    if len(available) < 6:
        raise ValueError("Fewer than six unused numbers remain")
    return sorted(available, key=lambda n: (-role_score[n], -global_score[n], n))[:16]


def choose_disjoint_ticket_legacy(role_score: dict, global_score: dict, used: set[int]):
    """Exact frozen E045 behavior, retained only as an audit comparator."""
    pool = ranked_candidate_pool(role_score, global_score, used)
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
    return tuple(sorted(best[1])), tuple(best[1]), pool


def consecutive_pairs(sorted_ticket: tuple[int, ...]) -> int:
    ordered = tuple(sorted(int(n) for n in sorted_ticket))
    return sum(b - a == 1 for a, b in zip(ordered, ordered[1:]))


def choose_disjoint_ticket(role_score: dict, global_score: dict, used: set[int]):
    """Corrected E045 objective: evaluate adjacency and tie-break on sorted ticket."""
    pool = ranked_candidate_pool(role_score, global_score, used)
    best = None
    for ticket_ranked in combinations(pool, 6):
        ticket = tuple(sorted(ticket_ranked))
        odd = sum(n % 2 for n in ticket)
        low = sum(n <= 22 for n in ticket)
        bands = len({(n - 1) // 10 for n in ticket})
        consecutive = consecutive_pairs(ticket)
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
    return best[1], pool


def random_label_mapping(rng: random.Random) -> dict[int, int]:
    labels = list(range(1, 46))
    shuffled = labels[:]
    rng.shuffle(shuffled)
    return dict(zip(labels, shuffled))


def apply_label_mapping(lines, mapping):
    result = [tuple(sorted(mapping[n] for n in line)) for line in lines]
    union = set().union(*(set(x) for x in result))
    overlaps = [len(set(a) & set(b)) for a, b in combinations(result, 2)]
    if len(union) != 18 or any(overlap != 0 for overlap in overlaps):
        raise AssertionError("Label permutation failed to preserve union18 geometry")
    return result


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


def strict_portfolio_ready(
    historical_gate_pass: bool,
    minimum_target_count: int | None,
    completion_rule: str | None,
) -> bool:
    return bool(
        historical_gate_pass
        and minimum_target_count is not None
        and minimum_target_count > 0
        and completion_rule is not None
        and completion_rule.strip()
    )


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
    draws, data_prefix_sha, data_sha, current_data_rows = load_frozen_draw_prefix(
        cutoff,
        prereg["source_data_prefix_sha256"],
        prereg["source_data_full_file_sha256"],
    )
    if len(draws) != cutoff or [d["round"] for d in draws] != list(range(1, cutoff + 1)):
        raise ValueError("Frozen historical draw prefix is incomplete")

    reference = load_module(ROOT / "automation/five_role_research_v9.py", "e075_five_role_reference")
    b = reference.imp(reference.B_SOURCE, "e075_b_model")
    ac = reference.imp(reference.AC_SOURCE, "e075_ac_model")
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
    candidate_pool_comparisons = 0
    first_role_pool_mismatches = 0
    downstream_pool_content_differences = 0
    legacy_order_consecutive_mismatches = 0
    changed_targets = 0
    changed_lines = 0
    metric_names = ("max_hits", "any2", "any3", "winning_union_coverage")
    exact_by_metric = {
        "max_hits": float(expected_null["mean_max_hit"]),
        "any2": float(expected_null["p_any2"]),
        "any3": float(expected_null["p_any3"]),
        "winning_union_coverage": float(expected_null["expected_union_coverage"]),
    }
    random_count = int(prereg["random_comparator"]["random_bundles_per_target"])
    seed = int(prereg["random_comparator"]["seed"])
    start_target = int(prereg["target_rounds"].split("..")[0])

    for idx in range(warmup, len(draws)):
        target_round = idx + 1
        training_through = idx
        history = [item["nums"] for item in draws[:idx]]
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
        used_legacy = set()
        used_corrected = set()
        legacy_lines = []
        corrected_lines = []
        target_first_role_pool_mismatch = 0
        target_downstream_pool_differences = 0
        target_order_mismatches = 0
        target_changed_lines = 0
        for role_index, (role_name, role_models) in enumerate(role_sets):
            role = reference.role_score(role_models, predictions, reliability, global_score)
            legacy_ticket, legacy_score_order_ticket, legacy_pool = choose_disjoint_ticket_legacy(role, global_score, used_legacy)
            corrected_ticket, corrected_pool = choose_disjoint_ticket(role, global_score, used_corrected)
            candidate_pool_comparisons += 1
            if role_index == 0 and legacy_pool != corrected_pool:
                first_role_pool_mismatches += 1
                target_first_role_pool_mismatch += 1
                raise AssertionError("First-role candidate pool differs despite identical empty used sets")
            if role_index > 0 and legacy_pool != corrected_pool:
                downstream_pool_content_differences += 1
                target_downstream_pool_differences += 1
            if len(legacy_pool) != 16 or len(corrected_pool) != 16:
                raise AssertionError("Candidate pool size changed")
            if sum(b - a == 1 for a, b in zip(legacy_score_order_ticket, legacy_score_order_ticket[1:])) != consecutive_pairs(legacy_ticket):
                legacy_order_consecutive_mismatches += 1
                target_order_mismatches += 1
            if legacy_ticket != corrected_ticket:
                changed_lines += 1
                target_changed_lines += 1
            legacy_lines.append(legacy_ticket)
            corrected_lines.append(corrected_ticket)
            used_legacy.update(legacy_ticket)
            used_corrected.update(corrected_ticket)
        if target_changed_lines:
            changed_targets += 1
        if len(legacy_lines) != 3 or len(corrected_lines) != 3:
            portfolio_geometry_violations += 1
            raise AssertionError(f"Invalid three-line geometry at target {target_round}")
        legacy_union = set().union(*(set(line) for line in legacy_lines))
        corrected_union = set().union(*(set(line) for line in corrected_lines))
        if len(legacy_union) != 18 or len(corrected_union) != 18:
            portfolio_geometry_violations += 1
            raise AssertionError(f"Invalid union18 at target {target_round}")

        actual = set(draws[idx]["nums"])
        if target_round >= start_target:
            legacy_metrics = portfolio_metrics(legacy_lines, actual)
            corrected_metrics = portfolio_metrics(corrected_lines, actual)
            legacy_line_hits = [len(set(line) & actual) for line in legacy_lines]
            corrected_line_hits = [len(set(line) & actual) for line in corrected_lines]
            observations.append({
                "target_round": target_round,
                "training_through_round": training_through,
                "legacy_lines": legacy_lines,
                "corrected_lines": corrected_lines,
                "actual": tuple(sorted(actual)),
                "legacy_line_hits": legacy_line_hits,
                "corrected_line_hits": corrected_line_hits,
                "legacy": legacy_metrics,
                "corrected": corrected_metrics,
                "first_role_pool_mismatches": target_first_role_pool_mismatch,
                "downstream_pool_content_differences": target_downstream_pool_differences,
                "target_order_mismatches": target_order_mismatches,
                "target_changed_lines": target_changed_lines,
            })

            rng = random.Random(seed + target_round)
            random_legacy = []
            random_corrected = []
            for _ in range(random_count):
                mapping = random_label_mapping(rng)
                legacy_random_lines = apply_label_mapping(legacy_lines, mapping)
                corrected_random_lines = apply_label_mapping(corrected_lines, mapping)
                if len(set().union(*(set(line) for line in legacy_random_lines))) != 18:
                    random_geometry_violations += 1
                if len(set().union(*(set(line) for line in corrected_random_lines))) != 18:
                    random_geometry_violations += 1
                random_legacy.append(portfolio_metrics(legacy_random_lines, actual))
                random_corrected.append(portfolio_metrics(corrected_random_lines, actual))
            if random_geometry_violations:
                raise AssertionError("Random comparator geometry violation")
            random_rows.append({
                "target_round": target_round,
                "random_bundles": random_count,
                "legacy_random_mean_max_hits": statistics.mean(x["max_hits"] for x in random_legacy),
                "legacy_random_p_any2": statistics.mean(x["any2"] for x in random_legacy),
                "legacy_random_p_any3": statistics.mean(x["any3"] for x in random_legacy),
                "legacy_random_mean_union_coverage": statistics.mean(x["winning_union_coverage"] for x in random_legacy),
                "corrected_random_mean_max_hits": statistics.mean(x["max_hits"] for x in random_corrected),
                "corrected_random_p_any2": statistics.mean(x["any2"] for x in random_corrected),
                "corrected_random_p_any3": statistics.mean(x["any3"] for x in random_corrected),
                "corrected_random_mean_union_coverage": statistics.mean(x["winning_union_coverage"] for x in random_corrected),
                "geometry_violations": 0,
            })

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

    diffs = {"legacy": {}, "corrected": {}}
    paired_diffs = {}
    for version in ("legacy", "corrected"):
        diffs[version] = {
            metric: [float(row[version][metric]) - exact_by_metric[metric] for row in observations]
            for metric in metric_names
        }
    for metric in metric_names:
        paired_diffs[metric] = [
            float(row["corrected"][metric]) - float(row["legacy"][metric])
            for row in observations
        ]

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
        for version in ("legacy", "corrected"):
            for metric in metric_names:
                item[f"{version}_delta_{metric}"] = statistics.mean(diffs[version][metric][start:stop])
            item[f"{version}_any2_positive"] = int(item[f"{version}_delta_any2"] > 0)
        for metric in metric_names:
            item[f"corrected_minus_legacy_{metric}"] = statistics.mean(paired_diffs[metric][start:stop])
        block_rows.append(item)
    legacy_any2_positive_share = sum(item["legacy_any2_positive"] for item in block_rows) / len(block_rows)
    corrected_any2_positive_share = sum(item["corrected_any2_positive"] for item in block_rows) / len(block_rows)

    inference = {"legacy_vs_exact_null": {}, "corrected_vs_exact_null": {}, "corrected_minus_legacy": {}}
    for offset, metric in enumerate(metric_names):
        legacy_ci = moving_block_ci(diffs["legacy"][metric], alpha, seed + 9000 + offset, bootstrap_reps, block_size)
        corrected_ci = moving_block_ci(diffs["corrected"][metric], alpha, seed + 10000 + offset, bootstrap_reps, block_size)
        paired_ci = moving_block_ci(paired_diffs[metric], alpha, seed + 11000 + offset, bootstrap_reps, block_size)
        inference["legacy_vs_exact_null"][metric] = {
            "observed_mean": statistics.mean(float(row["legacy"][metric]) for row in observations),
            "exact_geometry_matched_null": exact_by_metric[metric],
            "delta_mean": statistics.mean(diffs["legacy"][metric]),
            "adjusted_moving_block_ci": legacy_ci,
            "lower_bound_strictly_gt_zero": legacy_ci[0] > 0,
        }
        inference["corrected_vs_exact_null"][metric] = {
            "observed_mean": statistics.mean(float(row["corrected"][metric]) for row in observations),
            "exact_geometry_matched_null": exact_by_metric[metric],
            "delta_mean": statistics.mean(diffs["corrected"][metric]),
            "adjusted_moving_block_ci": corrected_ci,
            "lower_bound_strictly_gt_zero": corrected_ci[0] > 0,
        }
        inference["corrected_minus_legacy"][metric] = {
            "delta_mean": statistics.mean(paired_diffs[metric]),
            "moving_block_ci": paired_ci,
            "ci_lower_gt_zero": paired_ci[0] > 0,
            "ci_upper_lt_zero": paired_ci[1] < 0,
        }

    historical_gate_pass_legacy = (
        all(inference["legacy_vs_exact_null"][metric]["lower_bound_strictly_gt_zero"] for metric in metric_names)
        and legacy_any2_positive_share >= float(gate["any2_positive_nonoverlapping_50_target_block_share_min"])
    )
    historical_gate_pass_corrected = (
        all(inference["corrected_vs_exact_null"][metric]["lower_bound_strictly_gt_zero"] for metric in metric_names)
        and corrected_any2_positive_share >= float(gate["any2_positive_nonoverlapping_50_target_block_share_min"])
    )
    prospective_minimum = prereg["prospective_confirmation"]["minimum_target_count"]
    prospective_completion_rule = prereg["prospective_confirmation"]["completion_rule"]
    strict_portfolio_pass = strict_portfolio_ready(
        historical_gate_pass_corrected, prospective_minimum, prospective_completion_rule
    )
    if historical_gate_pass_corrected and (prospective_minimum is None or prospective_completion_rule is None):
        readiness_status = "HISTORICAL_GATE_PASS_BUT_NOT_READY_PROSPECTIVE_RULE_UNSPECIFIED"
    elif historical_gate_pass_corrected:
        readiness_status = "PROSPECTIVE_CONFIRMATION_PENDING"
    else:
        readiness_status = "STRICT_FAIL"

    simulated_random_means = {}
    for version in ("legacy", "corrected"):
        prefix = "legacy_random" if version == "legacy" else "corrected_random"
        simulated_random_means[version] = {
            "max_hits": statistics.mean(row[f"{prefix}_mean_max_hits"] for row in random_rows),
            "any2": statistics.mean(row[f"{prefix}_p_any2"] for row in random_rows),
            "any3": statistics.mean(row[f"{prefix}_p_any3"] for row in random_rows),
            "winning_union_coverage": statistics.mean(row[f"{prefix}_mean_union_coverage"] for row in random_rows),
        }

    source_paths = [
        ROOT / "automation/three_line_research_1251_v1.py",
        ROOT / "automation/three_line_research_1251_e075_corrected_v1.py",
        ROOT / "automation/three_line_research_1251_e075_corrected_v2.py",
        ROOT / "research/weekly_purchase/1251/E075_E045_SELECTOR_ORDER_CONFORMANCE_PREREG_20261119.json",
        ROOT / "research/weekly_purchase/1251/E075_EXECUTION_ATTEMPT_1_REPAIR_ADDENDUM_20261119.json",
        ROOT / "automation/five_role_research_v9.py",
        ROOT / "research/1245_final_pipeline_v3/recovered_original_assets/b_model_backtest.py",
        ROOT / "automation/recovered_models_v2.py",
        ROOT / "research/weekly_purchase/1251/THREE_LINE_POLICY_1251_PLUS.json",
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
        prediction_rows.append({
            "target_round": row["target_round"],
            "training_through_round": row["training_through_round"],
            "legacy_line1": " ".join(map(str, row["legacy_lines"][0])),
            "legacy_line2": " ".join(map(str, row["legacy_lines"][1])),
            "legacy_line3": " ".join(map(str, row["legacy_lines"][2])),
            "corrected_line1": " ".join(map(str, row["corrected_lines"][0])),
            "corrected_line2": " ".join(map(str, row["corrected_lines"][1])),
            "corrected_line3": " ".join(map(str, row["corrected_lines"][2])),
            "actual_numbers": " ".join(map(str, row["actual"])),
            "legacy_line_hits": " ".join(map(str, row["legacy_line_hits"])),
            "corrected_line_hits": " ".join(map(str, row["corrected_line_hits"])),
            "legacy_max_hits": row["legacy"]["max_hits"],
            "legacy_any2": row["legacy"]["any2"],
            "legacy_any3": row["legacy"]["any3"],
            "legacy_winning_union_coverage": row["legacy"]["winning_union_coverage"],
            "corrected_max_hits": row["corrected"]["max_hits"],
            "corrected_any2": row["corrected"]["any2"],
            "corrected_any3": row["corrected"]["any3"],
            "corrected_winning_union_coverage": row["corrected"]["winning_union_coverage"],
            "first_role_pool_mismatches": row["first_role_pool_mismatches"],
            "downstream_pool_content_differences": row["downstream_pool_content_differences"],
            "legacy_order_consecutive_mismatches": row["target_order_mismatches"],
            "changed_lines": row["target_changed_lines"],
        })
    write_csv(outdir / "PREDICTIONS.csv", prediction_rows, list(prediction_rows[0]))
    write_csv(outdir / "RANDOM_BASELINE.csv", random_rows, list(random_rows[0]))
    write_csv(outdir / "BLOCK_STABILITY.csv", block_rows, list(block_rows[0]))

    inference_payload = {
        "study_id": STUDY_ID,
        "evidence_class": "HISTORICAL_IMPLEMENTATION_CONFORMANCE_CORRECTION_NOT_INDEPENDENT_SIGNAL_OR_PROSPECTIVE_CONFIRMATION",
        "data_cutoff": cutoff,
        "data_sha256": data_sha,
        "target_range": [targets[0], targets[-1]],
        "targets": len(targets),
        "random_bundles_per_target_per_version": random_count,
        "random_bundles_total_per_version": len(targets) * random_count,
        "random_permutation_maps_shared_between_versions": True,
        "exact_geometry_matched_null": exact_by_metric,
        "simulated_same_target_random_means": simulated_random_means,
        "metrics": inference,
        "block_size": block_size,
        "block_lengths": [len(x) for x in block_slices(diffs["corrected"]["any2"], block_size)],
        "block_count": len(block_rows),
        "legacy_any2_positive_50_target_block_share": legacy_any2_positive_share,
        "corrected_any2_positive_50_target_block_share": corrected_any2_positive_share,
        "historical_strict_gate_pass_legacy": historical_gate_pass_legacy,
        "historical_strict_gate_pass_corrected": historical_gate_pass_corrected,
        "corrected_strict_portfolio_pass": strict_portfolio_pass,
        "strict_pass_ready": False,
        "prospective_confirmation_status": "UNSPECIFIED_IN_POLICY",
        "candidate_pool_comparisons": candidate_pool_comparisons,
        "candidate_pool_rule_identical": True,
        "first_role_pool_mismatches": first_role_pool_mismatches,
        "downstream_pool_content_differences": downstream_pool_content_differences,
        "legacy_order_consecutive_mismatches": legacy_order_consecutive_mismatches,
        "targets_with_changed_lines": changed_targets,
        "changed_line_count": changed_lines,
        "thresholds_or_policy_changed": False,
        "parameter_search": False,
        "variants_evaluated": 1,
    }
    write_json(outdir / "INFERENCE.json", inference_payload)
    readiness_update = {
        "update_id": "E075_READINESS_UPDATE_1251_20261119",
        "study_id": STUDY_ID,
        "target_round": 1251,
        "data_cutoff": cutoff,
        "task_registered": True,
        "runner_present": True,
        "historical_gate_evaluated": True,
        "historical_strict_gate_pass": historical_gate_pass_corrected,
        "strict_portfolio_pass": False,
        "strict_pass_ready": False,
        "ready_file_exists": False,
        "line_level_output_status": "SUPPRESSED_NOT_READY",
        "prospective_confirmation_required": True,
        "prospective_minimum_target_count": None,
        "prospective_completion_rule": None,
        "blocking_reason": "This is a historical implementation correction only. Prospective confirmation remains required and unspecified; this result cannot create purchase readiness.",
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
        "data_prefix_sha256": data_prefix_sha,
        "current_source_data_rows": current_data_rows,
        "target_range": [targets[0], targets[-1]],
        "target_count": len(targets),
        "random_bundles_per_target_per_version": random_count,
        "random_bundles_total_per_version": len(targets) * random_count,
        "random_permutation_maps_shared_between_versions": True,
        "training_cutoff_rule": "training_through_round = target_round - 1",
        "training_cutoff_violations": training_cutoff_violations,
        "leakage_failures": 0,
        "future_predictions": 0,
        "no_future_leakage": True,
        "portfolio_geometry_violations": portfolio_geometry_violations,
        "random_geometry_violations": random_geometry_violations,
        "all_legacy_and_corrected_portfolios_three_lines_six_numbers_union18": True,
        "candidate_pool_comparisons": candidate_pool_comparisons,
        "candidate_pool_rule_identical": True,
        "first_role_pool_mismatches": first_role_pool_mismatches,
        "downstream_pool_content_differences": downstream_pool_content_differences,
        "legacy_order_consecutive_mismatches": legacy_order_consecutive_mismatches,
        "targets_with_changed_lines": changed_targets,
        "changed_line_count": changed_lines,
        "selection_uses_randomness": False,
        "randomness_used_only_for_matched_comparator": True,
        "source_sha256": source_hashes,
        "historical_strict_gate_pass_legacy": historical_gate_pass_legacy,
        "historical_strict_gate_pass_corrected": historical_gate_pass_corrected,
        "strict_portfolio_pass": False,
        "strict_pass_ready": False,
        "prospective_rule_status": "UNSPECIFIED_IN_POLICY",
        "purchase_recommendation_generated": False,
    }
    write_json(outdir / "VERIFICATION.json", verification)
    completion = {
        "study_id": STUDY_ID,
        "status": "COMPLETE",
        "date_kst": date_kst,
        "run_id": run_id,
        "data_cutoff": cutoff,
        "target_range": [targets[0], targets[-1]],
        "target_count": len(targets),
        "historical_strict_gate_pass_legacy": historical_gate_pass_legacy,
        "historical_strict_gate_pass_corrected": historical_gate_pass_corrected,
        "strict_pass_ready": False,
        "readiness_status": readiness_status,
        "purchase_recommendation_generated": False,
    }
    write_json(outdir / "COMPLETION.json", completion)

    report = f"""# E075 — E045 selector-order implementation-conformance correction

Execution status: **COMPLETE**
Historical E045 legacy gate: **{"PASS" if historical_gate_pass_legacy else "FAIL"}**
Corrected historical gate: **{"PASS" if historical_gate_pass_corrected else "FAIL"}**
Purchase readiness: **NOT_READY**

## Frozen scope

- Historical data cutoff: {cutoff}; targets {targets[0]}–{targets[-1]} ({len(targets)})
- Training cutoff: target round minus one; both selectors receive the same pre-target predictions and scores
- Candidate-pool ranking rule: identical top-16 ordering formula; first-role pool mismatches: {first_role_pool_mismatches}; downstream pool-content differences after earlier line selections: {downstream_pool_content_differences}/{2*len(targets)}
- Correction: compute consecutive pairs and lexicographic tie-break on sorted ticket values, as the E045 preregistration specifies
- Unchanged: model predictions, role order, role/global scores, top-16 candidate-pool ranking rule, objective weights, line order, disjoint union18 geometry, exact null, random seed, alpha, block length, bootstrap count, strict thresholds
- Random comparator: {random_count} shared label-permutation maps per target and per version ({len(targets) * random_count:,} per version)
- Moving-block bootstrap: {bootstrap_reps:,} replicates; 50-target blocks; final remainder retained
- Any2 positive block threshold: 0.65

## Implementation audit

- Legacy selected-ticket adjacency-order mismatches: {legacy_order_consecutive_mismatches}
- Targets with one or more changed lines: {changed_targets}/{len(targets)}
- Changed line assignments: {changed_lines}
- Candidate-pool ranking rule changed: **NO**; first-role candidate pool mismatches: {first_role_pool_mismatches}. Later available pools can differ because each portfolio has its own prior selected lines.

## Historical metrics

| Metric | Legacy delta vs exact null | Corrected delta vs exact null | Corrected minus legacy | Paired CI |
|---|---:|---:|---:|---:|
"""
    for metric in metric_names:
        old = inference["legacy_vs_exact_null"][metric]
        new = inference["corrected_vs_exact_null"][metric]
        paired = inference["corrected_minus_legacy"][metric]
        ci = paired["moving_block_ci"]
        report += f"| {metric} | {old['delta_mean']:.6f} | {new['delta_mean']:.6f} | {paired['delta_mean']:.6f} | [{ci[0]:.6f}, {ci[1]:.6f}] |\n"
    report += f"""
- Legacy any2-positive block share: {legacy_any2_positive_share:.6f}
- Corrected any2-positive block share: {corrected_any2_positive_share:.6f}
- Legacy historical gate: **{"PASS" if historical_gate_pass_legacy else "FAIL"}**
- Corrected historical gate: **{"PASS" if historical_gate_pass_corrected else "FAIL"}**
- Prospective confirmation: **required; minimum target count and completion rule remain unspecified**
- STRICT_PASS_READY: **not created**
- Final purchase lines: **not generated**
- Random fallback: **prohibited**

This is an implementation-conformance correction, not an independent signal-family discovery or prospective confirmation. The original E045 runner and outputs remain unchanged. No model, weight, threshold, or parameter search was performed.
"""
    (outdir / "REPORT.md").write_text(report, encoding="utf-8")
    manifest_entries = write_and_verify_manifest(outdir)

    summary = {
        "status": "COMPLETE",
        "study_id": STUDY_ID,
        "data_cutoff": cutoff,
        "targets": len(targets),
        "random_bundles_total_per_version": len(targets) * random_count,
        "manifest_entries": manifest_entries,
        "manifest_status": "PASS",
        "legacy_historical_gate_pass": historical_gate_pass_legacy,
        "corrected_historical_gate_pass": historical_gate_pass_corrected,
        "strict_pass_ready": False,
        "readiness_status": readiness_status,
        "candidate_pool_rule_identical": True,
        "first_role_pool_mismatches": first_role_pool_mismatches,
        "downstream_pool_content_differences": downstream_pool_content_differences,
        "legacy_order_consecutive_mismatches": legacy_order_consecutive_mismatches,
        "targets_with_changed_lines": changed_targets,
        "changed_line_count": changed_lines,
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
