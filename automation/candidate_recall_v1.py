#!/usr/bin/env python3
"""Cutoff-safe candidate-recall diagnostics for the daily lotto research loop.

No purchase lines are generated. For every target, rankings are built from prior
rounds only. Candidate recall is measured separately from five-ticket allocation.
"""
from __future__ import annotations

import csv
import json
import random
import statistics
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path

KST = timezone(timedelta(hours=9))
KS = (10, 15, 20, 25, 30)
SIGNALS = ("recent30", "gap", "momentum", "balanced", "contrarian", "consensus")
RANDOM_SEED = 2026110201
RANDOM_REPS_PER_TARGET = 200


def zscore(vals):
    xs = list(vals.values())
    m = statistics.mean(xs)
    sd = statistics.pstdev(xs) or 1.0
    return {k: (v - m) / sd for k, v in vals.items()}


def features(draws):
    f30 = Counter(n for d in draws[-30:] for n in d)
    f10 = Counter(n for d in draws[-10:] for n in d)
    fprev20 = Counter(n for d in draws[-30:-10] for n in d)
    gaps = {}
    for n in range(1, 46):
        g = 0
        for d in reversed(draws):
            if n in d:
                break
            g += 1
        gaps[n] = g
    recent30 = zscore({n: f30[n] for n in range(1, 46)})
    gap = zscore(gaps)
    momentum = zscore({n: f10[n] / 10 - fprev20[n] / 20 for n in range(1, 46)})
    balanced = {n: (recent30[n] + gap[n]) / 2 for n in range(1, 46)}
    contrarian = {n: (-recent30[n] + gap[n]) / 2 for n in range(1, 46)}
    consensus = {
        n: statistics.mean((recent30[n], gap[n], momentum[n], balanced[n], contrarian[n]))
        for n in range(1, 46)
    }
    return {
        "recent30": recent30,
        "gap": gap,
        "momentum": momentum,
        "balanced": balanced,
        "contrarian": contrarian,
        "consensus": consensus,
    }


def ranked(score):
    return sorted(range(1, 46), key=lambda n: (-score[n], n))


def write_csv(path, rows):
    rows = list(rows)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def rate(arr, threshold):
    return sum(x >= threshold for x in arr) / len(arr)


def build_candidate_recall(rows, dated: Path):
    draws = [r["nums"] for r in rows]
    rounds = [r["round"] for r in rows]
    start = 200
    signal_hits = {s: {k: [] for k in KS} for s in SIGNALS}
    random_hits = {k: [] for k in KS}
    latest_trace = None

    for idx in range(start, len(draws)):
        hist = draws[:idx]
        actual = set(draws[idx])
        fs = features(hist)
        per_target_trace = {"target_round": rounds[idx], "signals": {}}
        for s in SIGNALS:
            order = ranked(fs[s])
            rank_map = {n: j + 1 for j, n in enumerate(order)}
            per_target_trace["signals"][s] = {
                "winning_number_ranks": {str(n): rank_map[n] for n in sorted(actual)},
                "recall_at_k": {},
            }
            for k in KS:
                h = len(set(order[:k]) & actual)
                signal_hits[s][k].append(h)
                per_target_trace["signals"][s]["recall_at_k"][str(k)] = h / 6

        rng = random.Random(RANDOM_SEED + rounds[idx])
        for _ in range(RANDOM_REPS_PER_TARGET):
            order = rng.sample(range(1, 46), 45)
            for k in KS:
                random_hits[k].append(len(set(order[:k]) & actual))
        latest_trace = per_target_trace

    score_rows = []
    for s in SIGNALS:
        for k in KS:
            hs = signal_hits[s][k]
            rnd = random_hits[k]
            mean_hits = statistics.mean(hs)
            random_mean_hits = statistics.mean(rnd)
            s3, s4, s6 = rate(hs, 3), rate(hs, 4), rate(hs, 6)
            r3, r4, r6 = rate(rnd, 3), rate(rnd, 4), rate(rnd, 6)
            score_rows.append({
                "signal": s,
                "k": k,
                "targets": len(hs),
                "mean_candidate_hits": mean_hits,
                "mean_recall": mean_hits / 6,
                "random_mean_candidate_hits": random_mean_hits,
                "random_mean_recall": random_mean_hits / 6,
                "delta_recall_vs_random": (mean_hits - random_mean_hits) / 6,
                "rate_capture_3plus_of_6": s3,
                "random_rate_capture_3plus_of_6": r3,
                "delta_3plus_vs_random": s3 - r3,
                "rate_capture_4plus_of_6": s4,
                "random_rate_capture_4plus_of_6": r4,
                "delta_4plus_vs_random": s4 - r4,
                "rate_capture_all_6": s6,
                "random_rate_capture_all_6": r6,
                "delta_all6_vs_random": s6 - r6,
                "status": "MEASURED_CUTOFF_SAFE_NOT_AUTO_PROMOTED",
            })

    write_csv(dated / "CANDIDATE_RECALL_SCORECARD.csv", score_rows)
    payload = {
        "generated_kst": datetime.now(KST).isoformat(),
        "data_cutoff": rounds[-1],
        "walkforward_start_round": rounds[start] if len(rounds) > start else None,
        "targets": len(draws) - start,
        "k_values": list(KS),
        "signals": list(SIGNALS),
        "matched_random_sets_per_target": RANDOM_REPS_PER_TARGET,
        "matched_random_sets_total": (len(draws) - start) * RANDOM_REPS_PER_TARGET,
        "no_future_leakage": True,
        "latest_completed_target_trace": latest_trace,
        "interpretation_rule": "Candidate recall is evaluated before ticket construction. A portfolio failure must not be blamed on candidate ranking when the winning numbers were already inside the fixed candidate set.",
        "scorecard": str((dated / "CANDIDATE_RECALL_SCORECARD.csv").name),
    }
    (dated / "CANDIDATE_RECALL_STATUS.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return payload
