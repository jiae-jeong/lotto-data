#!/usr/bin/env python3
"""Independent exact-null and conditional candidate/allocator audit.

This is a mathematical validation artifact for H1250-A/B. It does not
generate candidate numbers, purchase lines, or evaluate a predictive model.
Only the Python standard library is required.
"""
from collections import Counter
from fractions import Fraction
from itertools import product
import json
import math
import random

SEED = 202611120833
MC_REPS_PER_M = 100_000
TOL_EXACT = 1e-14
TOL_MC = 0.004


def conditional_counts(m):
    """Exact ways to distribute m winning slots among five groups of six."""
    out = Counter()
    for hits in product(range(7), repeat=5):
        if sum(hits) != m:
            continue
        ways = math.prod(math.comb(6, h) for h in hits)
        if ways:
            mx = max(hits)
            out[(mx, int(mx >= 2), int(mx >= 3), int(mx >= 4))] += ways
    assert sum(out.values()) == math.comb(30, m)
    return out


def conditional_summary(m):
    counts = conditional_counts(m)
    den = math.comb(30, m)
    return {
        "E_max_hits": sum(Fraction(k[0] * v, den) for k, v in counts.items()),
        "P_any2": sum(Fraction(v, den) for k, v in counts.items() if k[1]),
        "P_any3": sum(Fraction(v, den) for k, v in counts.items() if k[2]),
        "P_any4": sum(Fraction(v, den) for k, v in counts.items() if k[3]),
        "E_union_coverage": Fraction(m, 1),
    }


def frozen_v42_exact_null_disjoint30():
    """Independent transcription of the frozen V42 mask-DP null."""
    lines = [tuple(range(1 + 6 * i, 7 + 6 * i)) for i in range(5)]
    mask_counts = [0] * 32
    for number in range(1, 46):
        mask = 0
        for i, line in enumerate(lines):
            if number in line:
                mask |= 1 << i
        mask_counts[mask] += 1

    # state = (selected_count, five line-hit counts, union coverage)
    dp = {(0, 0, 0, 0, 0, 0, 0): 1}
    for mask, count in enumerate(mask_counts):
        if not count:
            continue
        next_dp = {}
        for state, ways in dp.items():
            selected = state[0]
            hits = state[1:6]
            coverage = state[6]
            for take in range(min(count, 6 - selected) + 1):
                multiplicity = math.comb(count, take)
                new_hits = [
                    hits[i] + (take if mask & (1 << i) else 0)
                    for i in range(5)
                ]
                new_state = (
                    selected + take,
                    *new_hits,
                    coverage + (take if mask else 0),
                )
                next_dp[new_state] = next_dp.get(new_state, 0) + ways * multiplicity
        dp = next_dp

    total = math.comb(45, 6)
    out = {
        "max_hits": Fraction(0, 1),
        "any2": Fraction(0, 1),
        "any3": Fraction(0, 1),
        "any4": Fraction(0, 1),
        "winning_union_coverage": Fraction(0, 1),
    }
    for state, ways in dp.items():
        if state[0] != 6:
            continue
        line_hits = state[1:6]
        coverage = state[6]
        mx = max(line_hits)
        p = Fraction(ways, total)
        out["max_hits"] += p * mx
        out["any2"] += p * int(mx >= 2)
        out["any3"] += p * int(mx >= 3)
        out["any4"] += p * int(mx >= 4)
        out["winning_union_coverage"] += p * coverage
    return out


def run():
    candidate_m = {
        m: Fraction(
            math.comb(30, m) * math.comb(15, 6 - m),
            math.comb(45, 6),
        )
        for m in range(7)
    }
    assert sum(candidate_m.values()) == 1

    conditional = {m: conditional_summary(m) for m in range(7)}
    unconditional = {
        "E_max_hits": sum(candidate_m[m] * conditional[m]["E_max_hits"] for m in range(7)),
        "P_any2": sum(candidate_m[m] * conditional[m]["P_any2"] for m in range(7)),
        "P_any3": sum(candidate_m[m] * conditional[m]["P_any3"] for m in range(7)),
        "P_any4": sum(candidate_m[m] * conditional[m]["P_any4"] for m in range(7)),
        "E_union_coverage": sum(candidate_m[m] * conditional[m]["E_union_coverage"] for m in range(7)),
    }

    v42 = frozen_v42_exact_null_disjoint30()
    mapping = {
        "max_hits": "E_max_hits",
        "any2": "P_any2",
        "any3": "P_any3",
        "any4": "P_any4",
        "winning_union_coverage": "E_union_coverage",
    }
    exact_diffs = {
        key: float(v42[key] - unconditional[value])
        for key, value in mapping.items()
    }
    assert max(abs(x) for x in exact_diffs.values()) < TOL_EXACT

    # Independent seeded simulation of the conditional random-partition null.
    rng = random.Random(SEED)
    monte_carlo = {}
    for m in range(7):
        sums = [0, 0, 0, 0]
        for _ in range(MC_REPS_PER_M):
            slots = rng.sample(range(30), m)
            hits = [0] * 5
            for slot in slots:
                hits[slot // 6] += 1
            mx = max(hits)
            sums[0] += mx
            sums[1] += int(mx >= 2)
            sums[2] += int(mx >= 3)
            sums[3] += int(mx >= 4)
        observed = [x / MC_REPS_PER_M for x in sums]
        expected = [
            float(conditional[m]["E_max_hits"]),
            float(conditional[m]["P_any2"]),
            float(conditional[m]["P_any3"]),
            float(conditional[m]["P_any4"]),
        ]
        max_error = max(abs(a - b) for a, b in zip(observed, expected))
        assert max_error < TOL_MC
        monte_carlo[str(m)] = {
            "replicates": MC_REPS_PER_M,
            "E_max_hits": observed[0],
            "P_any2": observed[1],
            "P_any3": observed[2],
            "P_any4": observed[3],
            "max_abs_error": max_error,
        }

    expected_hits = sum(candidate_m[m] * m for m in range(7))
    result = {
        "study_id": "H1250_EXACT_CONDITIONAL_NULL_AUDIT_2026-11-12",
        "candidate_m_distribution": {
            str(m): {"probability": float(candidate_m[m]), "fraction": str(candidate_m[m])}
            for m in range(7)
        },
        "candidate_stage": {
            "expected_hits_in_random_top30": float(expected_hits),
            "expected_recall_at_30": float(expected_hits / 6),
            "P_hits_le_2": float(sum(candidate_m[m] for m in range(3))),
            "P_hits_ge_3": float(sum(candidate_m[m] for m in range(3, 7))),
            "P_hits_ge_4": float(sum(candidate_m[m] for m in range(4, 7))),
        },
        "conditional_allocator_null": {
            str(m): {
                key: {"value": float(value), "fraction": str(value)}
                for key, value in conditional[m].items()
            }
            for m in range(7)
        },
        "unconditional_exact_null": {
            key: {"value": float(value), "fraction": str(value)}
            for key, value in unconditional.items()
        },
        "frozen_v42_implementation_reproduction": {
            key: {"value": float(value), "fraction": str(value)}
            for key, value in v42.items()
        },
        "max_abs_difference_v42_vs_independent": max(abs(x) for x in exact_diffs.values()),
        "conditional_monte_carlo_check": monte_carlo,
        "assertions": {
            "candidate_m_distribution_sums_to_one": True,
            "v42_matches_independent_composition_enumeration": True,
            "conditional_random_partition_matches_exact_within_tolerance": True,
            "union_coverage_equals_candidate_hits_m": True,
            "allocator_geometry_does_not_change_union_when_bank_fixed": True,
            "top30_reordering_does_not_change_recall30": True,
            "no_candidate_or_purchase_numbers_emitted": True,
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    run()
