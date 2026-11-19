#!/usr/bin/env python3
"""E070: E069 preregistration/implementation conformance and two-stage audit.

This is a historical, exploratory correction audit only. It does not create
purchase lines, promote a model, or constitute prospective confirmation.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
PREREG_REL = "research/weekly_purchase/1251/E070_E069_IMPLEMENTATION_AND_CANDIDATE_STAGE_AUDIT_PREREG_20261118.json"
DATA_REL = "lotto_data.csv"
E069_RUNNER_REL = "automation/three_line_previous_draw_membership_e069.py"
BASE_REL = "automation/three_line_research_1251_v1.py"
E069_PREDICTIONS_REL = "analysis/2026-11-18/gha_44131681250_1/E069_THREE_LINE_PREVIOUS_DRAW_MEMBERSHIP_TRANSITION_v1/PREDICTIONS.csv"
EXPECTED_DATA_SHA = "7203238dae69ce281c59e6a0928cc187b11d88ed342685cd2dd2f214f063b3c2"
EXPECTED_DATA_BLOB = "66431d711919f179e4cb1349e2f7295c68a8735e"
EXPECTED_E069_RUNNER_BLOB = "0d3790f9031b23367dc3c9f25438d1089b8f8329"
EXPECTED_BASE_BLOB = "ea74fb93f9e5704810a0d51b9a08b49f29fa3513"
TARGETS = range(401, 1251)
KS = (10, 15, 20, 25, 30)
BLOCK = 50
REPLICATES = 4000
CANDIDATE_ALPHA = 0.01
PORTFOLIO_ALPHA = 0.0125
SEED_CANDIDATE = 20261118070
SEED_PORTFOLIO = 20261118071
EXACT_NULL = {
    "max_hits": 1.514256248572755,
    "any2": 0.47497624326892623,
    "any3": 0.07135490714617204,
    "winning_union_coverage": 2.4,
}


def git_blob(path: str) -> str:
    return subprocess.check_output(
        ["git", "rev-parse", f"HEAD:{path}"], cwd=ROOT, text=True
    ).strip()


def load_base():
    spec = importlib.util.spec_from_file_location("e070_base", ROOT / BASE_REL)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot import the frozen E045 base selector")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_draws(path: Path):
    raw = path.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    if sha != EXPECTED_DATA_SHA:
        raise ValueError(f"Canonical CSV SHA mismatch: {sha}")
    rows = []
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            if not row or not row.get("round"):
                continue
            round_no = int(row["round"])
            nums = tuple(int(row[f"no{i}"]) for i in range(1, 7))
            bonus = int(row["bonus"])
            if len(set(nums)) != 6 or any(n < 1 or n > 45 for n in nums):
                raise ValueError(f"Invalid main numbers at round {round_no}")
            if bonus < 1 or bonus > 45 or bonus in nums:
                raise ValueError(f"Invalid bonus at round {round_no}")
            rows.append({"round": round_no, "nums": nums, "bonus": bonus})
    if len(rows) != 1250 or [r["round"] for r in rows] != list(range(1, 1251)):
        raise ValueError("Expected exactly 1,250 contiguous rounds")
    return rows, sha


def xorshift32(seed: int):
    state = seed & 0xFFFFFFFF
    while True:
        state = (state ^ ((state << 13) & 0xFFFFFFFF)) & 0xFFFFFFFF
        state = (state ^ (state >> 17)) & 0xFFFFFFFF
        state = (state ^ ((state << 5) & 0xFFFFFFFF)) & 0xFFFFFFFF
        yield state / 4294967296.0


def moving_block_ci(values, alpha: float, seed: int):
    if not values:
        raise ValueError("Empty bootstrap input")
    sizes = [BLOCK] * (len(values) // BLOCK)
    remainder = len(values) % BLOCK
    if remainder:
        sizes.append(remainder)
    rng = xorshift32(seed)
    boot = []
    for _ in range(REPLICATES):
        sample = []
        for size in sizes:
            start = int(next(rng) * (len(values) - size + 1))
            sample.extend(values[start : start + size])
        if len(sample) != len(values):
            raise AssertionError("Bootstrap sample length mismatch")
        boot.append(mean(sample))
    boot.sort()
    lo = int((alpha / 2) * (REPLICATES - 1))
    hi = int((1 - alpha / 2) * (REPLICATES - 1))
    return [boot[lo], boot[hi]]


def nonoverlap_block_share(values):
    blocks = [values[i : i + BLOCK] for i in range(0, len(values), BLOCK)]
    deltas = [mean(block) for block in blocks]
    return {
        "positive_blocks": sum(x > 0 for x in deltas),
        "block_count": len(blocks),
        "positive_share": sum(x > 0 for x in deltas) / len(blocks),
        "block_deltas": deltas,
    }


def score_target(draws, target_round):
    """Return registered and as-built E069 scores using draws 1..t-1 only."""
    exposures = [[0] * 46 for _ in range(2)]
    successes = [[0] * 46 for _ in range(2)]
    for outcome_round in range(2, target_round):
        previous = set(draws[outcome_round - 2]["nums"])
        outcome = set(draws[outcome_round - 1]["nums"])
        for number in range(1, 46):
            state = int(number in previous)
            exposures[state][number] += 1
            successes[state][number] += int(number in outcome)

    history = draws[: target_round - 1]
    global_counts = [sum(number in d["nums"] for d in history) for number in range(1, 46)]
    previous_nums = set(draws[target_round - 2]["nums"])
    registered, as_built = {}, {}
    for number in range(1, 46):
        state = int(number in previous_nums)
        exposure = exposures[state][number]
        success = successes[state][number]
        # Exact preregistered prior: 45 * (6/45) = 6.
        registered[number] = (success + 6.0) / (exposure + 45.0)
        # Literal E069 implementation: per-number historical frequency prior.
        global_rate = global_counts[number - 1] / (target_round - 1)
        as_built[number] = (success + 45.0 * global_rate) / (exposure + 45.0)
    return registered, as_built, exposures, successes


def rank_scores(scores):
    return sorted(range(1, 46), key=lambda n: (-scores[n], n))


def candidate_summary(draws, rows, label, alpha, seed, inferential=True):
    output = {}
    for k in KS:
        per_target_hits = [r[f"{label}_hits_at_{k}"] for r in rows]
        values = [hits / 6.0 for hits in per_target_hits]
        expected = k / 45.0
        deltas = [v - expected for v in values]
        block = nonoverlap_block_share(deltas)
        output[str(k)] = {
            "candidate_recall": sum(per_target_hits) / (6.0 * len(per_target_hits)),
            "mean_winner_hits": mean(per_target_hits),
            "exact_random_expected_recall": expected,
            "delta_vs_exact_random": mean(deltas),
            "positive_nonoverlap_50_target_blocks": block["positive_blocks"],
            "nonoverlap_50_target_blocks": block["block_count"],
            "positive_block_share": block["positive_share"],
            "adjusted_moving_block_ci": moving_block_ci(deltas, alpha, seed + k) if inferential else None,
            "ci_lower_strictly_gt_zero": (
                moving_block_ci(deltas, alpha, seed + k)[0] > 0 if inferential else None
            ),
        }
    return output


def verify_e069_predictions(path: Path):
    rows = []
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            if row.get("target_round"):
                rows.append(row)
    if len(rows) != 850:
        raise ValueError(f"E069 predictions row count mismatch: {len(rows)}")
    violations = 0
    for row in rows:
        t = int(row["target_round"])
        if int(row["training_through_round"]) != t - 1 or int(row["previous_draw_round"]) != t - 1:
            violations += 1
    if violations:
        raise ValueError(f"E069 output cutoff violations: {violations}")
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=ROOT / DATA_REL)
    parser.add_argument("--e069-predictions", type=Path, default=ROOT / E069_PREDICTIONS_REL)
    parser.add_argument(
        "--outdir",
        type=Path,
        default=ROOT / "analysis/2026-11-18/E070_E069_IMPLEMENTATION_AND_CANDIDATE_STAGE_AUDIT_v1",
    )
    args = parser.parse_args()

    prereg = json.loads((ROOT / PREREG_REL).read_text(encoding="utf-8"))
    frozen = prereg["frozen_blobs"]
    actual_blobs = {
        "audit_runner_blob_sha": git_blob("automation/e070_e069_candidate_stage_audit_v1.py"),
        "e069_runner_blob_sha": git_blob(E069_RUNNER_REL),
        "base_runner_blob_sha": git_blob(BASE_REL),
        "data_blob_sha": git_blob(DATA_REL),
    }
    expected_blobs = {
        "audit_runner_blob_sha": frozen["audit_runner_blob_sha"],
        "e069_runner_blob_sha": EXPECTED_E069_RUNNER_BLOB,
        "base_runner_blob_sha": EXPECTED_BASE_BLOB,
        "data_blob_sha": EXPECTED_DATA_BLOB,
    }
    if actual_blobs != expected_blobs:
        raise ValueError(f"Frozen input blob mismatch: {actual_blobs} != {expected_blobs}")

    e069_source = (ROOT / E069_RUNNER_REL).read_text(encoding="utf-8")
    if "global_rate = float(global_counts[number - 1]) / global_draws" not in e069_source:
        raise ValueError("Expected as-built E069 global-frequency prior was not found")
    if "(success[k,n] + 45*(6/45))/(exposure[k,n]+45)" not in json.dumps(prereg["registered_estimator"]):
        raise ValueError("Registered estimator formula changed")

    draws, data_sha = load_draws(args.data)
    base = load_base()
    e069_existing = verify_e069_predictions(args.e069_predictions)

    rows = []
    misses = []
    topk_overlap = {str(k): [] for k in KS}
    uniform_portfolio_metrics = {m: [] for m in EXACT_NULL}
    any4_values = []
    geometry_violations = 0

    for target_round in TARGETS:
        registered, as_built, exposures, successes = score_target(draws, target_round)
        registered_rank = rank_scores(registered)
        as_built_rank = rank_scores(as_built)
        actual = set(draws[target_round - 1]["nums"])
        previous = set(draws[target_round - 2]["nums"])
        row = {"target_round": target_round}
        for k in KS:
            row[f"registered_hits_at_{k}"] = sum(n in actual for n in registered_rank[:k])
            row[f"as_built_hits_at_{k}"] = sum(n in actual for n in as_built_rank[:k])
            overlap = len(set(registered_rank[:k]) & set(as_built_rank[:k])) / k
            topk_overlap[str(k)].append(overlap)

        rank_map = {n: i + 1 for i, n in enumerate(registered_rank)}
        for number in actual:
            rank = rank_map[number]
            if rank > 30:
                state = int(number in previous)
                misses.append({
                    "target_round": target_round,
                    "winning_number": number,
                    "rank_under_registered_formula": rank,
                    "previous_draw_member": state,
                    "transition_exposure": exposures[state][number],
                    "transition_success": successes[state][number],
                    "registered_score": registered[number],
                    "reason": "rank_below_top30_candidate_cutoff",
                })

        # Registered-formula portfolio stage; same frozen E045 selector, no variants.
        used, lines = set(), []
        for _ in range(3):
            line = base.choose_disjoint_ticket(registered, registered, used)
            lines.append(tuple(line))
            used.update(line)
        if len(lines) != 3 or len(used) != 18 or any(
            set(a) & set(b) for i, a in enumerate(lines) for b in lines[i + 1:]
        ):
            geometry_violations += 1
            raise AssertionError(f"Union18 geometry violation at target {target_round}")
        metrics = base.portfolio_metrics(lines, actual)
        for metric in EXACT_NULL:
            uniform_portfolio_metrics[metric].append(float(metrics[metric]))
        any4_values.append(int(metrics["max_hits"] >= 4))
        rows.append(row)

    candidate_registered = candidate_summary(
        draws, rows, "registered", CANDIDATE_ALPHA, SEED_CANDIDATE, True
    )
    candidate_as_built = candidate_summary(
        draws, rows, "as_built", CANDIDATE_ALPHA, SEED_CANDIDATE + 1000, False
    )

    portfolio = {}
    for metric, expected in EXACT_NULL.items():
        observed = uniform_portfolio_metrics[metric]
        deltas = [x - expected for x in observed]
        ci = moving_block_ci(deltas, PORTFOLIO_ALPHA, SEED_PORTFOLIO + len(portfolio))
        portfolio[metric] = {
            "observed_mean": mean(observed),
            "exact_geometry_matched_null": expected,
            "delta_mean": mean(deltas),
            "adjusted_moving_block_ci": ci,
            "lower_bound_strictly_gt_zero": ci[0] > 0,
            "positive_nonoverlap_50_target_blocks": nonoverlap_block_share(deltas)["positive_blocks"],
            "nonoverlap_50_target_block_count": nonoverlap_block_share(deltas)["block_count"],
        }
    any2_blocks = nonoverlap_block_share([
        x - EXACT_NULL["any2"] for x in uniform_portfolio_metrics["any2"]
    ])
    strict_historical_gate = (
        all(x["lower_bound_strictly_gt_zero"] for x in portfolio.values())
        and any2_blocks["positive_share"] >= 0.65
    )

    original_metrics = {
        "max_hits": mean(float(r["max_hits"]) for r in e069_existing),
        "any2": mean(float(r["any2"]) for r in e069_existing),
        "any3": mean(float(r["any3"]) for r in e069_existing),
        "winning_union_coverage": mean(float(r["winning_union_coverage"]) for r in e069_existing),
    }

    result = {
        "study_id": prereg["study_id"],
        "evidence_class": "HISTORICAL_EXPLORATORY_IMPLEMENTATION_CORRECTION_NOT_PROSPECTIVE_CONFIRMATION",
        "data_cutoff": 1250,
        "data_rows": len(draws),
        "data_sha256": data_sha,
        "target_range": [401, 1250],
        "target_count": len(rows),
        "e069_preregistration_conformance": {
            "registered_prior": "fixed uniform 6/45 prior, strength 45",
            "actual_runner_prior": "number-specific historical frequency prior, strength 45",
            "formula_match": False,
            "reason": "E069 score_numbers uses 45 * global_counts[number-1] / global_draws rather than 45 * (6/45).",
            "existing_e069_verification_status": "PASS",
            "verification_gap": "The E069 preflight validated metadata and frozen blobs but did not assert score_numbers implements the registered prior; its unit tests also omitted a prior-formula conformance assertion.",
            "original_e069_artifacts_preserved": True,
        },
        "cutoff_and_integrity": {
            "training_cutoff_rule": "For every target t, use draws 1..t-1 only; score before reading target outcome.",
            "candidate_stage_cutoff_violations": 0,
            "e069_output_rows": len(e069_existing),
            "e069_output_cutoff_violations": 0,
            "portfolio_geometry_violations": geometry_violations,
            "future_leakage": False,
        },
        "candidate_stage_registered_formula": {
            "formula": "(success + 45*(6/45)) / (exposure + 45)",
            "rank_tiebreak": "score descending, number ascending",
            "recall_at_k": candidate_registered,
            "missed_winner_count_below_top30": len(misses),
            "missed_winners_by_previous_draw_membership": {
                "member": sum(x["previous_draw_member"] == 1 for x in misses),
                "non_member": sum(x["previous_draw_member"] == 0 for x in misses),
            },
            "missed_winners_by_rank_band": {
                "31_35": sum(31 <= x["rank_under_registered_formula"] <= 35 for x in misses),
                "36_40": sum(36 <= x["rank_under_registered_formula"] <= 40 for x in misses),
                "41_45": sum(41 <= x["rank_under_registered_formula"] <= 45 for x in misses),
            },
            "mean_topk_overlap_with_as_built_formula": {
                k: mean(v) for k, v in topk_overlap.items()
            },
            "bonferroni_family_alpha": 0.05,
            "bonferroni_per_metric_alpha": CANDIDATE_ALPHA,
            "bootstrap_replicates": REPLICATES,
            "bootstrap_block_length": BLOCK,
            "nonoverlap_blocks": len(rows) // BLOCK,
            "residual_targets": len(rows) % BLOCK,
        },
        "candidate_stage_as_built_formula_diagnostic_only": {
            "formula": "(success + 45*per_number_global_frequency_rate) / (exposure + 45)",
            "recall_at_k": candidate_as_built,
            "promotion_eligible": False,
        },
        "portfolio_stage_registered_formula": {
            "metrics": portfolio,
            "any2_positive_nonoverlap_50_target_blocks": any2_blocks,
            "historical_strict_gate_pass": strict_historical_gate,
            "prospective_confirmation_required": True,
            "prospective_confirmation_status": "UNSPECIFIED_IN_POLICY",
            "promotion_eligible": False,
            "any4_rate_supplemental_only": mean(any4_values),
        },
        "portfolio_stage_original_e069_as_built_formula": {
            "observed_means_from_preserved_predictions": original_metrics,
            "promotion_eligible": False,
            "note": "These preserved metrics are from the implementation-mismatched E069 run and are not evidence for the registered fixed-prior estimator.",
        },
        "no_model_selection_or_tuning": True,
        "no_purchase_lines_generated": True,
        "no_freeze_or_seal_created": True,
    }

    args.outdir.mkdir(parents=True, exist_ok=True)
    (args.outdir / "RESULTS.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    with (args.outdir / "MISS_TRACE_TOP30.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        fields = [
            "target_round", "winning_number", "rank_under_registered_formula",
            "previous_draw_member", "transition_exposure", "transition_success",
            "registered_score", "reason",
        ]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(misses)
    print(json.dumps({
        "status": "COMPLETE",
        "target_count": len(rows),
        "candidate_recall_at_k": candidate_registered,
        "portfolio_stage": portfolio,
        "strict_historical_gate_pass": strict_historical_gate,
        "missed_winner_count_below_top30": len(misses),
        "output_dir": str(args.outdir),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
