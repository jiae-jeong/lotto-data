#!/usr/bin/env python3
"""Reproduce the preregistered whole-draw row-order dependence diagnostic."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "lotto_data.csv"
OUTPUT = ROOT / "research/strict_gate/ROUND_ORDER_DEPENDENCE_AUDIT_2026-11-13.json"
EXPECTED_DATA_SHA256 = "a5996af8b842799d777beae0abeef9767f79726870e4d78d6683dfb0fe4802e7"
EXPECTED_GIT_BLOB_SHA = "d012ac7f2395e70466f0c50b71b949515dea1def"
SEED = 2026111302
REPS = 9999
LAGS = tuple(range(1, 11))


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def main() -> dict:
    raw = DATA.read_bytes()
    source_sha256 = hashlib.sha256(raw).hexdigest()
    source_blob_sha = git_blob_sha(raw)
    assert source_sha256 == EXPECTED_DATA_SHA256
    assert source_blob_sha == EXPECTED_GIT_BLOB_SHA

    with DATA.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        rows = [row for row in reader if row.get("round")]
    draws = []
    for expected_round, row in enumerate(rows, start=1):
        numbers = tuple(int(row[f"no{i}"]) for i in range(1, 7))
        assert int(row["round"]) == expected_round
        assert len(set(numbers)) == 6
        assert all(1 <= number <= 45 for number in numbers)
        draws.append(sum(1 << (number - 1) for number in numbers))
    assert len(draws) == 1249
    n = len(draws)

    def lag_means(order: list[int]) -> list[float]:
        values = [0.0] * (max(LAGS) + 1)
        for lag in LAGS:
            total = 0
            for i in range(lag, n):
                total += (draws[order[i]] & draws[order[i - lag]]).bit_count()
            values[lag] = total / (n - lag)
        return values

    identity = list(range(n))
    observed = lag_means(identity)

    state = SEED

    def rand01() -> float:
        nonlocal state
        state = (1664525 * state + 1013904223) & 0xFFFFFFFF
        return state / 4294967296.0

    samples = [[0.0] * REPS for _ in range(max(LAGS) + 1)]
    for b in range(REPS):
        order = list(identity)
        for i in range(n - 1, 0, -1):
            j = int(rand01() * (i + 1))
            order[i], order[j] = order[j], order[i]
        values = lag_means(order)
        for lag in LAGS:
            samples[lag][b] = values[lag]

    null_mean = [0.0] * (max(LAGS) + 1)
    null_sd = [0.0] * (max(LAGS) + 1)
    z_observed = [0.0] * (max(LAGS) + 1)
    for lag in LAGS:
        vals = samples[lag]
        mean = sum(vals) / REPS
        variance = sum((value - mean) ** 2 for value in vals) / (REPS - 1)
        sd = variance ** 0.5
        null_mean[lag], null_sd[lag] = mean, sd
        z_observed[lag] = abs((observed[lag] - mean) / sd)

    observed_max_t = max(z_observed[lag] for lag in LAGS)
    max_t_exceedances = 0
    unadjusted_exceedances = {lag: 0 for lag in LAGS}
    for b in range(REPS):
        permuted_max_t = 0.0
        for lag in LAGS:
            z = abs((samples[lag][b] - null_mean[lag]) / null_sd[lag])
            permuted_max_t = max(permuted_max_t, z)
            if z >= z_observed[lag]:
                unadjusted_exceedances[lag] += 1
        if permuted_max_t >= observed_max_t:
            max_t_exceedances += 1

    lag_results = []
    for lag in LAGS:
        lag_results.append({
            "lag": lag,
            "observed_mean_overlap": observed[lag],
            "conditional_null_mean": null_mean[lag],
            "conditional_null_sd": null_sd[lag],
            "absolute_standardized_departure": z_observed[lag],
            "unadjusted_two_sided_mc_p_descriptive_only":
                (unadjusted_exceedances[lag] + 1) / (REPS + 1),
        })

    adjusted_p = (max_t_exceedances + 1) / (REPS + 1)
    result = {
        "study_id": "ROUND_ORDER_DEPENDENCE_AUDIT_2026-11-13",
        "classification": "RETROSPECTIVE_EXPLORATORY_CONDITIONAL_PERMUTATION",
        "preregistration": {
            "path": "research/strict_gate/ROUND_ORDER_DEPENDENCE_PREREGISTRATION_2026-11-13.md",
            "frozen_before_evaluation": True,
            "permutations": REPS,
            "seed": SEED,
            "lag_family": list(LAGS),
            "familywise_method": "two-sided max-T permutation",
        },
        "data": {
            "source": "lotto_data.csv",
            "rows": n,
            "round_start": 1,
            "round_end": 1249,
            "validation": "PASS",
            "sha256": source_sha256,
            "git_blob_sha": source_blob_sha,
        },
        "reference": {
            "independent_uniform_expected_overlap_per_lag_pair": 0.8,
            "null": "uniform permutation of whole draw rows; each draw's six-number set and full-history number totals are preserved",
        },
        "lag_results": lag_results,
        "max_t": {
            "observed_max_absolute_standardized_departure": observed_max_t,
            "exceedances": max_t_exceedances,
            "adjusted_familywise_mc_p": adjusted_p,
        },
        "decision": (
            "NO_TEMPORAL_ORDER_SIGNAL_DETECTED"
            if adjusted_p > 0.05 else
            "TEMPORAL_ORDER_SIGNAL_SCREEN_POSITIVE_REQUIRES_SEPARATE_PROSPECTIVE_TEST"
        ),
        "limitations": [
            "Retrospective diagnostic; not an untouched prospective validation.",
            "A non-significant result does not prove every possible dependence is absent.",
            "This test does not evaluate or certify a five-line portfolio.",
            "No strict PASS, candidate promotion, or ticket recommendation is produced.",
        ],
    }
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "REPRODUCED",
        "output": str(OUTPUT.relative_to(ROOT)),
        "max_t_adjusted_familywise_mc_p": adjusted_p,
        "decision": result["decision"],
    }, ensure_ascii=False))
    return result


if __name__ == "__main__":
    main()
