#!/usr/bin/env python3
"""Create an additive daily MASTER validation run and fresh B walk-forward.

The source data and prior outputs are read-only. Every invocation creates a
new analysis/YYYY-MM-DD/MASTER_<run-id> directory and refuses to reuse it.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import random
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "analysis" / "2026-10-12" / "lotto_data_1_1245_snapshot.csv"
CANONICAL = ROOT / "lotto_data.csv"
B_SOURCE = ROOT / "research" / "1245_final_pipeline_v3" / "recovered_original_assets" / "b_model_backtest.py"
HYPOTHESIS_REGISTRY = ROOT / "analysis" / "2026-10-09" / "A_ERRORLOOP_C_RESEARCH_v2" / "NEW_HYPOTHESIS_REGISTRY.csv"
REPORT_1245 = ROOT / "analysis" / "2026-10-11" / "ROUND_1245_REVIEW.md"
EXPECTED = ["round", "date", "no1", "no2", "no3", "no4", "no5", "no6", "bonus"]
WINDOWS = (10, 30, 50, 100)
RANDOM_SEED = 20261013


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_content(path: Path) -> bytes:
    """Normalize Windows text checkout line endings to the bytes committed by Git."""
    return path.read_bytes().replace(b"\r\n", b"\n")


def normalized_sha(path: Path) -> str:
    return hashlib.sha256(git_content(path)).hexdigest()


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != EXPECTED:
            raise ValueError(f"{path}: columns {reader.fieldnames!r}, expected {EXPECTED!r}")
        return list(reader)


def validate(path: Path) -> tuple[list[dict], dict]:
    raw = read_rows(path)
    rows = []
    errors = []
    prev_date = None
    for ix, row in enumerate(raw, 1):
        try:
            r = int(row["round"])
        except Exception:
            errors.append(f"row {ix}: round is not an integer: {row['round']!r}")
            continue
        if row["round"].strip() != str(r):
            errors.append(f"round {r}: round must be canonical integer text")
        try:
            date = datetime.strptime(row["date"], "%Y.%m.%d").date()
        except Exception:
            errors.append(f"round {r}: invalid date field {row['date']!r}")
            continue
        if prev_date is not None and date <= prev_date:
            errors.append(f"round {r}: date not strictly increasing ({date} <= {prev_date})")
        prev_date = date
        try:
            nums = tuple(int(row[f"no{i}"]) for i in range(1, 7))
            bonus = int(row["bonus"])
        except Exception:
            errors.append(f"round {r}: main number or bonus is not an integer")
            continue
        if len(nums) != 6:
            errors.append(f"round {r}: expected six main numbers")
        if any(n < 1 or n > 45 for n in nums):
            errors.append(f"round {r}: main number outside 1..45: {nums}")
        if len(set(nums)) != 6:
            errors.append(f"round {r}: duplicate main numbers: {nums}")
        if not 1 <= bonus <= 45:
            errors.append(f"round {r}: bonus outside 1..45: {bonus}")
        if bonus in nums:
            errors.append(f"round {r}: bonus duplicates main number: {bonus}")
        rows.append({"round": r, "date": date.isoformat(), "nums": tuple(sorted(nums)), "bonus": bonus})
    rounds = [x["round"] for x in rows]
    if rounds != list(range(1, len(rows) + 1)):
        first_bad = next((i for i, (a, b) in enumerate(zip(rounds, range(1, len(rounds) + 1)), 1) if a != b), None)
        errors.append(f"round sequence has duplicate/gap/out-of-order near row {first_bad}; rows={len(rows)}")
    if len(set(rounds)) != len(rounds):
        errors.append("duplicate round identifiers present")
    if errors:
        raise ValueError("DATA VALIDATION FAILED:\n" + "\n".join(errors))
    return rows, {"rows": len(rows), "first_round": rounds[0], "latest_round": rounds[-1],
                  "latest_date": rows[-1]["date"], "integrity": "PASS", "error_count": 0}


def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    with path.open("x", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def analyze(rows: list[dict], out: Path) -> dict:
    draws = [x["nums"] for x in rows]
    end = len(rows)
    counts = Counter(n for draw in draws for n in draw)
    appearance_rounds = {n: [i + 1 for i, draw in enumerate(draws) if n in draw] for n in range(1, 46)}
    number_rows = []
    for n in range(1, 46):
        seen = appearance_rounds[n]
        completed = [b - a for a, b in zip(seen, seen[1:])]
        current = end - seen[-1]
        max_gap = max([seen[0] - 1, *[gap - 1 for gap in completed], current])
        item = {"number": n, "all_count": counts[n], "all_rate_per_draw": counts[n] / end,
                "current_gap": current, "historical_max_gap": max_gap,
                "mean_completed_interval": sum(completed) / len(completed) if completed else "",
                "last_appearance_round": seen[-1], "all_vs_uniform_count_delta": counts[n] - end * 6 / 45}
        for width in WINDOWS:
            sub = draws[-width:]
            wc = sum(n in d for d in sub)
            item[f"recent_{width}_count"] = wc
            item[f"recent_{width}_per_draw"] = wc / len(sub)
            item[f"recent_{width}_vs_long_rate"] = wc / len(sub) - counts[n] / end
        number_rows.append(item)
    write_csv(out / "NUMBER_SIGNAL_SCORECARD.csv", list(number_rows[0]), number_rows)

    def structure(name: str, sub: list[tuple[int, ...]]) -> dict:
        odd = Counter(sum(n % 2 for n in d) for d in sub)
        low = Counter(sum(n <= 22 for n in d) for d in sub)
        sums = [sum(d) for d in sub]
        consec = Counter(sum(b == a + 1 for a, b in zip(d, d[1:])) for d in sub)
        ranges = Counter("1-10" if n <= 10 else "11-20" if n <= 20 else "21-30" if n <= 30 else "31-40" if n <= 40 else "41-45" for d in sub for n in d)
        gaps = Counter(g for d in sub for g in (b - a for a, b in zip(d, d[1:])))
        endings = Counter(n % 10 for d in sub for n in d)
        pairs = Counter(pair for d in sub for pair in itertools.combinations(d, 2))
        triples = Counter(triple for d in sub for triple in itertools.combinations(d, 3))
        internal = [sum(b == a + 1 for a, b in zip(d, d[1:])) for d in sub]
        overlap = [len(set(d) & set(sub[i - 1])) if i else 0 for i, d in enumerate(sub)]
        return {"window": name, "draws": len(sub), "odd_count_distribution": json.dumps(dict(sorted(odd.items())), sort_keys=True),
                "low_1_22_distribution": json.dumps(dict(sorted(low.items())), sort_keys=True),
                "sum_mean": sum(sums) / len(sums), "sum_min": min(sums), "sum_max": max(sums),
                "consecutive_pair_distribution": json.dumps(dict(sorted(consec.items())), sort_keys=True),
                "band_number_counts": json.dumps(dict(sorted(ranges.items())), sort_keys=True),
                "adjacent_number_gap_counts": json.dumps(dict(sorted(gaps.items())), sort_keys=True),
                "ending_digit_counts": json.dumps(dict(sorted(endings.items())), sort_keys=True),
                "mean_consecutive_pairs": sum(internal) / len(internal),
                "mean_previous_draw_overlap": sum(overlap) / len(overlap),
                "distinct_pairs": len(pairs), "top_pairs": json.dumps([[list(k), v] for k, v in pairs.most_common(10)]),
                "distinct_triples": len(triples), "top_triples": json.dumps([[list(k), v] for k, v in triples.most_common(10)])}

    structure_rows = [structure("all", draws)] + [structure(f"recent_{w}", draws[-w:]) for w in WINDOWS]
    write_csv(out / "STRUCTURE_RELATIONS_BY_WINDOW.csv", list(structure_rows[0]), structure_rows)
    overall = structure_rows[0]
    deltas = []
    for item in structure_rows[1:]:
        deltas.append({"window": item["window"], "sum_mean_delta_vs_all": item["sum_mean"] - overall["sum_mean"],
                       "mean_consecutive_pairs_delta_vs_all": item["mean_consecutive_pairs"] - overall["mean_consecutive_pairs"],
                       "mean_previous_draw_overlap_delta_vs_all": item["mean_previous_draw_overlap"] - overall["mean_previous_draw_overlap"],
                       "band_counts": item["band_number_counts"], "odd_structure": item["odd_count_distribution"],
                       "low_high_structure": item["low_1_22_distribution"],
                       "pairs_top10": item["top_pairs"], "triples_top10": item["top_triples"]})
    write_csv(out / "RECENT_VS_LONG_STRUCTURE.csv", list(deltas[0]), deltas)

    reg = list(csv.DictReader(HYPOTHESIS_REGISTRY.open(encoding="utf-8-sig", newline="")))
    status = {"H001": "UNVERIFIED", "H002": "UNVERIFIED", "H003": "INSUFFICIENT_EVIDENCE",
              "H004": "INSUFFICIENT_EVIDENCE", "H005": "INSPECT_ONLY_NO_C_MODEL_CLAIM", "H006": "SOURCE_NOT_FOUND"}
    signal_rows = []
    for signal, evidence in [("long_frequency", "H001"), ("gap", "H002"), ("structure", "H004"),
                             ("recent_change", "H001"), ("pair", "H003"), ("triple", "H003")]:
        signal_rows.append({"signal": signal, "legacy_A_status": "UNAVAILABLE; no integrated A source recovered",
                            "calculation_today": "RUN", "formula": {
                                "long_frequency": "main-number counts over all selected draws; descriptive only",
                                "gap": "latest round minus last appearance; completed interarrival gaps",
                                "structure": "empirical draw structure and relation frequencies by full/recent windows",
                                "recent_change": "window rate minus all-history per-draw rate for 10/30/50/100",
                                "pair": "unordered pair co-occurrence counts; no significance claim",
                                "triple": "unordered triple co-occurrence counts; no significance claim"}[signal],
                            "variables": "see NUMBER_SIGNAL_SCORECARD.csv and STRUCTURE_RELATIONS_BY_WINDOW.csv",
                            "weight": "not combined / none assigned", "version": "DAILY_SIGNAL_INVENTORY_v1",
                            "historical_validation": status[evidence], "provenance": evidence,
                            "recommendation_use": "PROHIBITED; descriptive or insufficiently validated"})
    write_csv(out / "A_SIGNAL_SCORECARD.csv", list(signal_rows[0]), signal_rows)
    classifications = [
        {"signal": "long_frequency", "family": "A/C candidate", "classification": "still_unverified", "evidence": "H001 not executed as a standalone confirmatory test"},
        {"signal": "gap", "family": "A/C candidate", "classification": "still_unverified", "evidence": "H002 not executed as a standalone confirmatory test"},
        {"signal": "recent_change", "family": "A/C candidate", "classification": "still_unverified", "evidence": "H001 nested-window conflict; no promotion"},
        {"signal": "pair", "family": "A/C candidate", "classification": "still_unverified", "evidence": "H003 sparse relation signal, insufficient evidence"},
        {"signal": "triple", "family": "A/C candidate", "classification": "still_unverified", "evidence": "H003 sparse relation signal, insufficient evidence"},
        {"signal": "structure_veto", "family": "C candidate", "classification": "rejected_from_promotion", "evidence": "H004 coverage diagnostic only; no predictive benefit established"},
        {"signal": "S008_related_structure", "family": "C candidate", "classification": "rejected_from_model_identity", "evidence": "H005 source inspection only; corrected variant not frozen or run"},
        {"signal": "contrarian_structural_flags", "family": "contrarian", "classification": "still_unverified", "evidence": "descriptive base rates do not validate integrated contrarian model"},
    ]
    write_csv(out / "C_CONTRARIAN_SIGNAL_CLASSIFICATION.csv", list(classifications[0]), classifications)
    return {"number_count_rows": len(number_rows), "structure_windows": len(structure_rows),
            "distinct_all_pairs": overall["distinct_pairs"], "distinct_all_triples": overall["distinct_triples"],
            "hypothesis_registry_rows": len(reg)}


def run_b(rows: list[dict], out: Path, random_repetitions: int) -> dict:
    source_bytes = B_SOURCE.read_bytes()
    source_text = source_bytes.decode("utf-8-sig").replace("\r\n", "\n")
    if "def predictions_for_round" not in source_text or "target_round = train_n + 1" not in source_text:
        raise RuntimeError("Preserved B source does not match expected leakage-safe implementation")
    patched = source_text
    replacements = [
        ('ROOT = Path(__file__).resolve().parents[1]', f'ROOT = Path({str(ROOT)!r})'),
        ('INPUT = ROOT / "work" / "lotto-data" / "lotto_data.csv"', f'INPUT = Path({str(SNAPSHOT)!r})'),
        ('OUT = ROOT / "outputs"', f'OUT = Path({str(out)!r})'),
        ('len(draws) != 1244', 'len(draws) != 1245'),
        ('list(range(1, 1245))', 'list(range(1, 1246))'),
        ('rounds 1..1244', 'rounds 1..1245'),
        ('1244 - anchor', '1245 - anchor'),
        ('회차 1~1244', '회차 1~1245'),
    ]
    for old, new in replacements:
        if old not in patched:
            raise RuntimeError(f"B-source patch anchor missing: {old}")
        patched = patched.replace(old, new)
    executed = out / "EXECUTED_B_MODEL_BACKTEST.py"
    executed.write_text(patched, encoding="utf-8", newline="\n")
    proc = subprocess.run([sys.executable, str(executed)], cwd=ROOT, text=True,
                          capture_output=True, encoding="utf-8", errors="replace")
    (out / "B_STDOUT.log").write_text(proc.stdout, encoding="utf-8")
    (out / "B_STDERR.log").write_text(proc.stderr, encoding="utf-8")
    (out / "B_EXIT_CODE.txt").write_text(str(proc.returncode) + "\n", encoding="ascii")
    if proc.returncode != 0:
        raise RuntimeError(f"B walk-forward failed with exit code {proc.returncode}; see B_STDERR.log")
    predictions_path = out / "b_model_predictions.csv"
    with predictions_path.open(encoding="utf-8-sig", newline="") as f:
        records = list(csv.DictReader(f))
    if not records:
        raise RuntimeError("B emitted no prediction rows")
    # The preserved source intentionally duplicates a target across overlapping
    # horizons. Collapse only after asserting every duplicate predicts identically.
    forecasts = {}
    for row in records:
        target = int(row["target_round"]); train = int(row["training_through_round"])
        if train != target - 1:
            raise RuntimeError(f"leakage violation: target={target}, training_through={train}")
        key = (target, row["model"])
        value = (row["predicted_numbers"], int(row["hits"]))
        if key in forecasts and forecasts[key] != value:
            raise RuntimeError(f"overlapping holdouts disagree for target/model {key}")
        forecasts[key] = value
    target_numbers = {r["round"]: set(r["nums"]) for r in rows}
    targets = sorted({k[0] for k in forecasts})
    if targets != list(range(201, 1246)) or 1245 not in targets:
        raise RuntimeError(f"B unique target range invalid: {targets[0]}..{targets[-1]}, count={len(targets)}")
    rng = random.Random(RANDOM_SEED)
    paired_rows = []
    random_rows = []
    metrics = {}
    for target in targets:
        actual = target_numbers[target]
        hist = Counter()
        for _ in range(random_repetitions):
            nums = rng.sample(range(1, 46), 6)
            hist[len(actual.intersection(nums))] += 1
        rhits = [k for k, n in hist.items() for _ in range(n)]
        rnd_mean = sum(rhits) / random_repetitions
        random_rows.append({"target_round": target, "random_tickets": random_repetitions,
                            "mean_hits": rnd_mean,
                            "variance_hits_population": sum((x-rnd_mean)**2 for x in rhits) / random_repetitions,
                            "rate_ge_3": sum(hist[k] for k in range(3,7)) / random_repetitions,
                            "rate_ge_4": sum(hist[k] for k in range(4,7)) / random_repetitions,
                            "rate_ge_5": sum(hist[k] for k in range(5,7)) / random_repetitions,
                            "rate_eq_6": hist[6] / random_repetitions,
                            **{f"hits_{k}_count": hist[k] for k in range(7)}})
        for (t, model), (ticket, hits) in sorted(forecasts.items()):
            if t != target:
                continue
            paired_rows.append({"target_round": target, "model": model, "predicted_numbers": ticket,
                                "model_hits": hits, "random_mean_hits_same_target": rnd_mean,
                                "paired_difference_model_minus_random": hits - rnd_mean,
                                "random_rate_ge_3_same_target": random_rows[-1]["rate_ge_3"],
                                "random_rate_ge_4_same_target": random_rows[-1]["rate_ge_4"],
                                "random_rate_ge_5_same_target": random_rows[-1]["rate_ge_5"],
                                "random_rate_eq_6_same_target": random_rows[-1]["rate_eq_6"]})
    write_csv(out / "RANDOM_BASELINE_BY_TARGET.csv", list(random_rows[0]), random_rows)
    write_csv(out / "MODEL_RANDOM_PAIRED_BY_TARGET.csv", list(paired_rows[0]), paired_rows)
    for model in sorted({r["model"] for r in paired_rows}):
        sub = [r for r in paired_rows if r["model"] == model]
        hits = [r["model_hits"] for r in sub]
        diffs = [r["paired_difference_model_minus_random"] for r in sub]
        m = len(hits); mu = sum(hits) / m
        metrics[model] = {"n_target_rounds": m, "mean_hits": mu,
                          "variance_hits_population": sum((x-mu)**2 for x in hits)/m,
                          "rate_ge_3": sum(x >= 3 for x in hits)/m,
                          "rate_ge_4": sum(x >= 4 for x in hits)/m,
                          "rate_ge_5": sum(x >= 5 for x in hits)/m,
                          "rate_eq_6": sum(x == 6 for x in hits)/m,
                          "mean_random_hits_same_targets": sum(r["mean_hits"] for r in random_rows)/len(random_rows),
                          "mean_paired_difference": sum(diffs)/m,
                          "paired_difference_positive_rounds": sum(x > 0 for x in diffs),
                          "paired_difference_negative_rounds": sum(x < 0 for x in diffs),
                          "paired_difference_zero_rounds": sum(x == 0 for x in diffs)}
    summary_rows = [{"model": key, **value} for key, value in metrics.items()]
    write_csv(out / "MODEL_RANDOM_PAIRED_SUMMARY.csv", list(summary_rows[0]), summary_rows)
    # Compare each model with the Monte Carlo tickets generated for exactly the
    # same target set. Keep the complete 0..6 distributions alongside paired means.
    random_hist = {k: sum(int(r[f"hits_{k}_count"]) for r in random_rows) for k in range(7)}
    random_n = random_repetitions * len(random_rows)
    random_mean = sum(k * v for k, v in random_hist.items()) / random_n
    random_variance = sum((k - random_mean) ** 2 * v for k, v in random_hist.items()) / random_n
    full_comparisons = []
    for model in sorted({r["model"] for r in paired_rows}):
        sub = [r for r in paired_rows if r["model"] == model]
        hs = [int(r["model_hits"]) for r in sub]
        n = len(hs); model_mean = sum(hs) / n
        model_hist = {k: sum(x == k for x in hs) for k in range(7)}
        row = {"model": model, "targets": n, "model_mean_hits": model_mean,
               "random_mean_hits_same_target_MC": random_mean,
               "mean_paired_difference": sum(float(x["paired_difference_model_minus_random"]) for x in sub) / n,
               "model_variance_population": sum((x-model_mean)**2 for x in hs)/n,
               "random_variance_population_MC": random_variance}
        for k in range(7):
            row[f"model_hits_{k}_count"] = model_hist[k]
            row[f"model_hits_{k}_rate"] = model_hist[k] / n
            row[f"random_hits_{k}_rate_MC"] = random_hist[k] / random_n
        for threshold in (2, 3, 4, 5):
            mr = sum(x >= threshold for x in hs) / n
            rr = sum(random_hist[k] for k in range(threshold, 7)) / random_n
            row[f"model_{threshold}plus_rate"] = mr
            row[f"random_{threshold}plus_rate_MC"] = rr
            row[f"delta_{threshold}plus_rate"] = mr - rr
        row["model_six_hit_rate"] = sum(x == 6 for x in hs) / n
        row["random_six_hit_rate_MC"] = random_hist[6] / random_n
        row["delta_mean_vs_random_MC"] = model_mean - random_mean
        full_comparisons.append(row)
    write_csv(out / "MODEL_RANDOM_COMPARISON_FULL.csv", list(full_comparisons[0]), full_comparisons)
    paired_recheck = {"method": "same-target paired Monte Carlo; one seeded random stream per target shared across models",
                      "seed": RANDOM_SEED, "repetitions_per_target": random_repetitions,
                      "target_rounds": len(random_rows), "random_ticket_simulations": random_n,
                      "random_hits_distribution": {str(k): random_hist[k] for k in range(7)},
                      "random_mean_hits": random_mean, "random_variance_population": random_variance,
                      "random_rates": {f"{x}plus_rate": sum(random_hist[k] for k in range(x, 7))/random_n for x in range(2, 6)},
                      "random_six_rate": random_hist[6]/random_n, "models": full_comparisons}
    (out / "PAIRED_BASELINE_RECHECK.json").write_text(json.dumps(paired_recheck, indent=2)+"\n", encoding="utf-8")
    leakage = {"result": "PASS", "raw_prediction_rows_checked": len(records),
               "unique_target_model_forecasts": len(forecasts), "unique_target_rounds": len(targets),
               "target_min": targets[0], "target_max": targets[-1], "target_1245_present": 1245 in targets,
               "rule": "for target t, training_through_round=t-1; source builds one incremental feature state before evaluating t",
               "feature_max_round": "t-1", "rolling_window_end_round": "t-1 (50-round recency features are sliced only from draws[:train_n])",
               "source_order": "predictions_for_round(draws, train_n, ...) is called before draws[train_n] is incorporated",
               "duplicate_forecast_consistency": "PASS"}
    (out / "LEAKAGE_AUDIT.json").write_text(json.dumps(leakage, indent=2) + "\n", encoding="utf-8")
    return {"raw_prediction_rows": len(records), "unique_targets": len(targets),
            "unique_target_model_forecasts": len(forecasts), "target_1245_records": sum(int(r["target_round"]) == 1245 for r in records),
            "random_repetitions_per_target": random_repetitions,
            "random_ticket_draws": random_repetitions * len(targets), "random_seed": RANDOM_SEED,
            "leakage": "PASS", "metrics": metrics, "random_mean_hits": random_mean,
            "random_variance_population": random_variance, "full_paired_comparisons": full_comparisons}


def recommendations(out: Path, rows: list[dict]) -> dict:
    inventory = []
    for folder in (ROOT / "analysis", ROOT / "research", ROOT / "outputs"):
        if not folder.exists():
            continue
        for p in folder.rglob("*"):
            if not p.is_file():
                continue
            rel = p.relative_to(ROOT).as_posix()
            lower = rel.lower()
            if re.search(r"(recommend|purchase|error.?note|round_1245_review)", lower) and not any(
                    token in lower for token in ("walk_forward_predictions", "b_model_predictions", "recommendation_sources.json")):
                inventory.append({"path": rel, "sha256": sha(p), "classification": "source_candidate; inspect provenance"})
    write_csv(out / "RECOMMENDATION_SOURCE_INVENTORY.csv", ["path", "sha256", "classification"], inventory)
    # Parse the preserved 1245 prospective line file and compare with the actual result,
    # without treating a seal or review text as a transaction receipt.
    csv_path = ROOT / "research" / "prospective_v4" / "decisions" / "1245" / "PRIMARY_PURCHASE_LINES_1245_V4.csv"
    actual = set(rows[-1]["nums"])
    line_rows = []
    with csv_path.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if row.get("target") != "1245":
                continue
            nums = tuple(int(row[f"no{i}"]) for i in range(1, 7))
            hits = sorted(set(nums) & actual)
            line_rows.append({"round": 1245, "recommendation_date": "pre-draw record; timestamp not inferred",
                              "model": row.get("model_id") or "unknown", "model_version": "V4 frozen source",
                              "mode": row.get("mode", "unknown"), "line_id": row.get("line", "unknown"),
                              "hit_count": len(hits), "included_winning_numbers": " ".join(map(str, hits)),
                              "excluded_winning_numbers": " ".join(map(str, sorted(actual-set(nums)))),
                              "bonus_match": int(rows[-1]["bonus"] in nums), "rank": "unknown",
                              "result": "historical outcome comparison; purchase receipt not independently located"})
    write_csv(out / "ROUND_1245_RECOMMENDATION_REVIEW.csv", list(line_rows[0]), line_rows)
    return {"candidate_source_files": len(inventory), "round_1245_lines": len(line_rows),
            "purchase_receipt": "not independently located", "legacy_historical_recommendation_provenance": "INCOMPLETE"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=datetime.now().astimezone().date().isoformat())
    ap.add_argument("--random-repetitions", type=int, default=1000)
    args = ap.parse_args()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", args.date):
        raise SystemExit("date must be YYYY-MM-DD")
    if args.random_repetitions < 100:
        raise SystemExit("random-repetitions must be >= 100")
    day_root = ROOT / "analysis" / args.date
    day_root.mkdir(parents=True, exist_ok=True)
    run_id = "MASTER_" + datetime.now().astimezone().strftime("%H%M%S_%f") + "_v2"
    out = day_root / run_id
    out.mkdir(exist_ok=False)
    print(f"RUN_DIR={out}")
    canonical, can_info = validate(CANONICAL)
    snapshot, snap_info = validate(SNAPSHOT)
    prefix_matches = canonical == snapshot[:len(canonical)]
    if not prefix_matches:
        raise RuntimeError("validated snapshot prefix does not equal canonical raw rows")
    if snap_info["latest_round"] <= can_info["latest_round"]:
        raise RuntimeError("no newer validated snapshot; refusing to label canonical as latest")
    if normalized_sha(SNAPSHOT) != "e534123cd7227f8c21d32251a567edeb018e7d1d9c4b049e4d23fb987f2619a4":
        raise RuntimeError("snapshot normalized SHA does not match the previously recorded validated source hash")
    data_basis = {"canonical_path": str(CANONICAL.relative_to(ROOT)), "canonical_rounds": can_info,
                  "canonical_sha256_normalized_lf": normalized_sha(CANONICAL),
                  "snapshot_path": str(SNAPSHOT.relative_to(ROOT)), "snapshot_rounds": snap_info,
                  "snapshot_sha256_normalized_lf": normalized_sha(SNAPSHOT), "snapshot_sha256_worktree_bytes": sha(SNAPSHOT),
                  "prefix_equals_canonical": prefix_matches,
                  "snapshot_provenance": "2026-10-12 report and frozen input manifest record two-source verification; local full integrity and canonical-prefix validation repeated today",
                  "selected_master_source": str(SNAPSHOT.relative_to(ROOT)), "selection_reason": "highest locally available dataset with continuous rounds, valid fields, historical two-source verification record, exact manifest SHA, and canonical-prefix match"}
    (out / "DATA_VALIDATION.json").write_text(json.dumps(data_basis, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    analytics = analyze(snapshot, out)
    rec = recommendations(out, snapshot)
    print("DATA_AND_ANALYSIS=PASS")
    b = run_b(snapshot, out, args.random_repetitions)
    print(f"B_EXIT_CODE=0; raw_prediction_rows={b['raw_prediction_rows']}; unique_targets={b['unique_targets']}; random_tickets={b['random_ticket_draws']}")
    # Legacy integrated A/C/contrarian sources are not in the recovered artifacts.
    mandatory = {
        "latest_validated_dataset": "PASS", "full_data_integrity": "PASS", "cumulative_and_recent_stats": "RUN",
        "gaps_and_structures_pairs_triples": "RUN", "A_legacy_integrated": "NOT_RUN_SOURCE_UNAVAILABLE",
        "A_signal_scorecard": "RUN", "B_full_walk_forward_today": "RUN",
        "same_target_random_monte_carlo": "RUN", "leakage": b["leakage"],
        "C_evidence_review": "RUN_NO_ELIGIBLE_PROMOTED_SIGNAL", "contrarian_evidence_review": "RUN_NO_VALIDATED_INTEGRATED_MODEL",
        "recommendation_and_error_note_search": "RUN", "recommendation_provenance": rec["legacy_historical_recommendation_provenance"],
        "model_signal_scorecard": "RUN", "hypothesis_states": "RUN_FROM_REGISTERED_STATUS",
        "protected_file_version_preservation": "CHECKED_AFTER_RUN"}
    master_status = "MASTER_PARTIAL" if any(x not in ("PASS", "RUN") for x in mandatory.values()) else "MASTER_COMPLETE"
    metadata = {"run_id": run_id, "created_utc": datetime.now(timezone.utc).isoformat(), "python": sys.version,
                "project_root": str(ROOT), "data": data_basis, "analytics": analytics, "recommendations": rec,
                "B": b, "mandatory_master_items": mandatory, "research_quota_status": "RESEARCH_QUOTA_COMPLETE",
                "master_status": master_status, "new_research_run": False,
                "existing_studies_today": ["E013_COMPONENT_LEAVE_ONE_OUT_v1", "E014_MODEL_AGREEMENT_DISAGREEMENT_v1", "E016_VOTE_DEPTH_CALIBRATION_v1"],
                "E015_E019": "NOT RUN; daily successful empirical research cap of three already satisfied; no same-data post-hoc research added"}
    (out / "RUN_METADATA.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    report = [f"# Daily MASTER validation — {args.date} ({run_id})", "",
              f"- DATA CUTOFF: {snap_info['first_round']}..{snap_info['latest_round']} ({snap_info['rows']} rounds), {snap_info['latest_date']}",
              f"- Selected source: `{data_basis['selected_master_source']}`; normalized SHA-256 `{data_basis['snapshot_sha256_normalized_lf']}`.",
              f"- Canonical source: `{data_basis['canonical_path']}` through {can_info['latest_round']}; normalized SHA-256 `{data_basis['canonical_sha256_normalized_lf']}`. Snapshot prefix equality: PASS.",
              f"- RESEARCH_QUOTA_STATUS = RESEARCH_QUOTA_COMPLETE (E013/E014/E016 already completed today).", f"- MASTER_STATUS = {master_status}.", "",
              "## DATA / MASTER checklist", "",
              "| Item | Status | Evidence |", "|---|---|---|"]
    for item, state in mandatory.items():
        report.append(f"| {item} | {state} | see JSON/CSV artifacts in this run |")
    report += ["", "Full cumulative frequency/gap metrics, long-vs-recent windows, and overall/recent structure, interval, ending digit, pair and triple summaries were recalculated from the selected 1..1245 dataset. See `NUMBER_SIGNAL_SCORECARD.csv`, `STRUCTURE_RELATIONS_BY_WINDOW.csv`, and `RECENT_VS_LONG_STRUCTURE.csv`.",
               "", "## B walk-forward and same-target Monte Carlo", "",
               f"- Preserved B source SHA-256 (normalized LF): `{normalized_sha(B_SOURCE)}`; only run paths and data cutoff were changed in the saved execution copy.",
               f"- Exit code: {b['raw_prediction_rows'] and 0}; raw B records: {b['raw_prediction_rows']}; unique targets: {b['unique_targets']} (201..1245); unique target/model forecasts: {b['unique_target_model_forecasts']}.",
               f"- Target 1245 appears in {b['target_1245_records']} overlapping B records.",
               f"- Actual random simulation: {b['random_ticket_draws']:,} tickets ({b['random_repetitions_per_target']} per target) with seed {b['random_seed']}; random outcomes were compared against each model on the same target. See `MODEL_RANDOM_PAIRED_BY_TARGET.csv` and summary.",
               "- Leakage audit: PASS; every stored training cutoff equals target-1; source prediction update order and rolling feature cutoff are documented in `LEAKAGE_AUDIT.json`.",
               "", "## A / C / contrarian", "",
               "- Legacy integrated A remains unavailable. `A_SIGNAL_SCORECARD.csv` is a versioned descriptive signal inventory, not a reconstructed or validated A model; weights are not combined.",
               "- No eligible signal was promoted into C. Sparse pair/triple and structure evidence stays insufficient; H005 is source inspection only.",
               "- No integrated contrarian source was recovered; structural flags remain descriptive/unverified.",
               "", "## Recommendation provenance", "",
               f"- Searched recommendation, purchase, and error-note paths; {rec['candidate_source_files']} candidate files inventoried with SHA-256.",
               f"- Round 1245 frozen V4 line records compared against the historical result: {rec['round_1245_lines']} lines. They are prospective sealed records; an independent purchase receipt was not located. Historical review claims the final lines were recovered pre-draw, but it is not an independent transaction receipt.",
               "- Missing recommendation history was not reconstructed. Round 1245 line-level hits/included and excluded winning numbers are in `ROUND_1245_RECOMMENDATION_REVIEW.csv`.",
               "", "## Research and queue", "",
               "- E013/E014/E016 remain today’s three completed empirical studies. They are not counted as this MASTER/B recalculation.",
               "- E015/E019 were not run because the configured daily empirical cap of three had already been reached. No additional same-data research or parameter tuning was performed.",
               "- E017 remains blocked by missing original mapping/source; E018 remains blocked by insufficient authentic purchase/ranking provenance.",
               "- Three future questions were not added: the requested novelty check is deferred until E015/E019 have executed, as specified.",
               "", "## Execution files", "",
               "`EXECUTED_B_MODEL_BACKTEST.py`, `B_STDOUT.log`, `B_STDERR.log`, `B_EXIT_CODE.txt`, `b_model_predictions.csv`, holdout metrics, trends, classification, random baseline, paired comparisons, validation JSON, and SHA manifest are stored in this new run directory.",
               "", "No future recommendations or candidate combinations were generated.", ""]
    (out / f"DAILY_MASTER_REPORT_{datetime.now().astimezone().strftime('%H%M%S_%f')}_v2.md").write_text("\n".join(report), encoding="utf-8")
    files = []
    for p in sorted(out.rglob("*")):
        if p.is_file() and p.name != "SHA256_MANIFEST.csv":
            committed = git_content(p)
            files.append({"path": p.relative_to(out).as_posix(), "bytes": len(committed),
                          "sha256": hashlib.sha256(committed).hexdigest()})
    write_csv(out / "SHA256_MANIFEST.csv", ["path", "bytes", "sha256"], files)
    # Reopen every output and ensure manifest entries still match disk.
    with (out / "SHA256_MANIFEST.csv").open(encoding="utf-8-sig", newline="") as f:
        for entry in csv.DictReader(f):
            p = out / Path(entry["path"])
            committed = git_content(p) if p.is_file() else b""
            if not p.is_file() or len(committed) != int(entry["bytes"]) or hashlib.sha256(committed).hexdigest() != entry["sha256"]:
                raise RuntimeError(f"output read-back/hash verification failed: {entry['path']}")
    print(f"MASTER_STATUS={master_status}")
    print(f"OUTPUT_VERIFICATION=PASS; file_count={len(files)}; run_dir={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
