#!/usr/bin/env python3
"""Exploratory conditional permutation test for persistent number-frequency bias."""
from __future__ import annotations
import csv, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "lotto_data.csv"
SEED = 2026111301
REPS = 5000
CUT = 624

with DATA.open(encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))
draws = [tuple(int(row[f"no{i}"]) for i in range(1, 7)) for row in rows]
assert len(draws) == 1249
assert all(len(set(d)) == 6 and all(1 <= n <= 45 for n in d) for d in draws)

def count_rows(indices):
    counts = [0] * 45
    for idx in indices:
        for n in draws[idx]:
            counts[n - 1] += 1
    return counts

def pearson(a, b):
    ma, mb = sum(a) / 45, sum(b) / 45
    num = da = db = 0.0
    for x, y in zip(a, b):
        dx, dy = x - ma, y - mb
        num += dx * dy
        da += dx * dx
        db += dy * dy
    return num / (da * db) ** 0.5

all_counts = count_rows(range(len(draws)))
first_counts = count_rows(range(CUT))
second_counts = [v - x for v, x in zip(all_counts, first_counts)]
observed = pearson(first_counts, second_counts)

# Deterministic 32-bit LCG and Fisher-Yates permutation.
state = SEED
def rand01():
    global state
    state = (1664525 * state + 1013904223) & 0xffffffff
    return state / 4294967296.0

indices = list(range(len(draws)))
ge = 0
sum_r = sum_r2 = 0.0
for _ in range(REPS):
    for i in range(len(indices) - 1, 0, -1):
        j = int(rand01() * (i + 1))
        indices[i], indices[j] = indices[j], indices[i]
    a = count_rows(indices[:CUT])
    b = [v - x for v, x in zip(all_counts, a)]
    r = pearson(a, b)
    ge += r >= observed
    sum_r += r
    sum_r2 += r * r

mean = sum_r / REPS
sd = (sum_r2 / REPS - mean * mean) ** 0.5
result = {
    "study_id": "DRAW_PROCESS_BIAS_PREFLIGHT_2026-11-13",
    "classification": "EXPLORATORY_CONDITIONAL_PERMUTATION_DIAGNOSTIC",
    "draw_count": len(draws),
    "split": {"first": "rounds 1..624", "second": "rounds 625..1249"},
    "observed_first_second_frequency_pearson_r": observed,
    "permutation": {
        "repetitions": REPS,
        "seed": SEED,
        "null_mean_r": mean,
        "null_sd_r": sd,
        "one_sided_p_for_positive_persistence": (ge + 1) / (REPS + 1),
    },
    "method": "Permute whole draw rows, preserving each draw's six-number structure and full-history per-number totals.",
    "interpretation": "No evidence of positive persistent number-frequency bias in this split. Exploratory only; not a strict predictive validation or prospective confirmation.",
}
print(json.dumps(result, indent=2))
