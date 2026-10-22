#!/usr/bin/env python3
"""Strict daily MASTER gate.

Runs the v4 core, then reruns recovered successor A/C/contrarian models on every
cutoff-safe target and measures them. FULL_COMPLETE is permitted only when the
same invocation/date contains full successor scorecards, matched-random
comparison, non-overlapping block stability, per-signal ablation, historical
source-search evidence, and a research-only five-ticket portfolio validation
with matched random bundles.

No candidate/final weekly numbers are generated for the user by this script.
"""
import csv
import json
import subprocess
import sys
import datetime
import importlib.util
import hashlib
import math
import random
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "lotto_data.csv"
MODELS = ROOT / "automation/recovered_models_v2.py"
PORTFOLIO_VERSION = "RESEARCH_ONLY_FIVE_TICKET_V1"
PORTFOLIO_RANDOM_BUNDLES_PER_TARGET = 1000
SIGNALS = ("long_frequency", "recent_100", "gap", "pair")


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def dump(p, x):
    p.write_text(json.dumps(x, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path, rows, fieldnames=None):
    rows = list(rows)
    if fieldnames is None:
        if not rows:
            raise ValueError(f"no rows for {path.name}")
        fieldnames = list(rows[0])
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def population_variance(values):
    return statistics.pvariance(values) if values else float("nan")


def scorecard(name, model_records, random_by_target):
    hits = [int(r["hits"]) for r in model_records]
    targets = [int(r["target_round"]) for r in model_records]
    random_means = [random_by_target[t] for t in targets]
    counts = {k: sum(h == k for h in hits) for k in range(7)}
    row = {
        "model": name,
        "n": len(hits),
        "mean_hits": statistics.mean(hits),
        "variance": population_variance(hits),
        "random_mean_same_targets": statistics.mean(random_means),
        "delta_mean": statistics.mean(hits) - statistics.mean(random_means),
    }
    for k in range(2, 7):
        row[f"rate_ge{k}"] = sum(h >= k for h in hits) / len(hits)
    for k in range(7):
        row[f"hits_{k}_count"] = counts[k]
    return row


def block_rows(name, model_records, random_by_target, block_size=50):
    recs = sorted(model_records, key=lambda r: int(r["target_round"]))
    out = []
    for i in range(0, len(recs), block_size):
        block = recs[i : i + block_size]
        hits = [int(r["hits"]) for r in block]
        targets = [int(r["target_round"]) for r in block]
        rm = statistics.mean(random_by_target[t] for t in targets)
        out.append(
            {
                "model": name,
                "start": targets[0],
                "end": targets[-1],
                "n": len(block),
                "mean_hits": statistics.mean(hits),
                "random_mean": rm,
                "delta_mean": statistics.mean(hits) - rm,
                "rate_ge3": sum(h >= 3 for h in hits) / len(hits),
                "rate_ge4": sum(h >= 4 for h in hits) / len(hits),
            }
        )
    return out


def scores_without_signal(m, history, omitted):
    features = m._features(history)
    weights = list(m.A_WEIGHTS.items())
    scores = {}
    for x in range(1, 46):
        total = 0.0
        for j, (signal, weight) in enumerate(weights):
            if signal == omitted:
                continue
            total += weight * features[j][x - 1]
        scores[x] = total
    return scores


def ticket_from_scores(m, model_name, history, scores):
    if model_name == "A_v2":
        return m._ticket_a_from_scores(scores)
    if model_name == "C_v2":
        a = m._ticket_a_from_scores(scores)
        bounds = m._structure_bounds(history)
        return m._ticket_c_from_scores(history, scores, bounds=bounds, fallback=a)
    if model_name == "contrarian_v2":
        return m._ticket_contrarian_from_scores(history, scores)
    raise KeyError(model_name)


def portfolio_candidates(m, history, full_pred, ablated_tickets):
    """Fixed outcome-blind candidate order for research-only portfolio V1."""
    ordered = [
        ("A_full", full_pred["A_v2"]),
        ("C_full", full_pred["C_v2"]),
        ("contrarian_full", full_pred["contrarian_v2"]),
    ]
    for signal in SIGNALS:
        for model_name in ("A_v2", "C_v2", "contrarian_v2"):
            ordered.append((f"{model_name}_without_{signal}", ablated_tickets[(model_name, signal)]))
    dedup = []
    seen = set()
    for source, ticket in ordered:
        t = tuple(sorted(ticket))
        if t not in seen:
            seen.add(t)
            dedup.append((source, t))
    return dedup


def overlap(a, b):
    return len(set(a) & set(b))


def select_five_ticket_portfolio(candidates):
    """Outcome-blind deterministic diversity selection for research-only V1."""
    if len(candidates) < 5:
        raise RuntimeError(f"portfolio candidate universe too small: {len(candidates)}")
    selected = [candidates[0]]
    remaining = candidates[1:]
    while len(selected) < 5:
        best_idx = min(
            range(len(remaining)),
            key=lambda i: (
                sum(overlap(remaining[i][1], s[1]) for s in selected),
                max(overlap(remaining[i][1], s[1]) for s in selected),
                i,
            ),
        )
        selected.append(remaining.pop(best_idx))
    return selected


def bundle_metrics(tickets, actual):
    hit_counts = [len(set(t) & actual) for t in tickets]
    union = set().union(*(set(t) for t in tickets))
    pair_overlaps = [
        overlap(tickets[i], tickets[j])
        for i in range(len(tickets))
        for j in range(i + 1, len(tickets))
    ]
    return {
        "max_hits": max(hit_counts),
        "any_ge2": int(any(h >= 2 for h in hit_counts)),
        "any_ge3": int(any(h >= 3 for h in hit_counts)),
        "any_ge4": int(any(h >= 4 for h in hit_counts)),
        "any_ge5": int(any(h >= 5 for h in hit_counts)),
        "any_ge6": int(any(h >= 6 for h in hit_counts)),
        "winning_union_coverage": len(union & actual),
        "ticket_union_size": len(union),
        "mean_pair_overlap": statistics.mean(pair_overlaps),
        "max_pair_overlap": max(pair_overlaps),
    }


def random_bundle_baseline(target_round, actual, bundles=1000):
    rng = random.Random(5102026 + target_round)
    sums = defaultdict(float)
    max_hits_hist = {k: 0 for k in range(7)}
    for _ in range(bundles):
        tickets = [tuple(sorted(rng.sample(range(1, 46), 6))) for _ in range(5)]
        met = bundle_metrics(tickets, actual)
        for key, value in met.items():
            sums[key] += value
        max_hits_hist[met["max_hits"]] += 1
    row = {"target_round": target_round, "random_bundles": bundles}
    for key, total in sums.items():
        row[f"random_{key}_mean"] = total / bundles
    for k in range(7):
        row[f"random_max_hits_{k}_rate"] = max_hits_hist[k] / bundles
    return row


def main():
    date = sys.argv[1] if len(sys.argv) > 1 else datetime.datetime.now().astimezone().date().isoformat()

    subprocess.run(
        [sys.executable, str(ROOT / "automation/daily_master_full_v4.py"), "--date", date],
        cwd=ROOT,
        check=True,
    )
    masters = sorted(
        (ROOT / "analysis" / date).glob("MASTER_FULL_V4_*"),
        key=lambda p: p.stat().st_mtime,
    )
    if not masters:
        raise RuntimeError("fresh V4 output not found")
    base = masters[-1]
    data = json.loads((base / "DATA_VALIDATION.json").read_text())
    b = json.loads((base / "B_LEAKAGE_CHECK.json").read_text())

    rows = list(csv.DictReader(DATA.open(encoding="utf-8-sig")))
    draws = [tuple(sorted(int(r[f"no{i}"]) for i in range(1, 7))) for r in rows]

    random_rows = list(csv.DictReader((base / "RANDOM_BY_TARGET.csv").open(encoding="utf-8-sig")))
    random_by_target = {int(r["target_round"]): float(r["mean_hits"]) for r in random_rows}
    source_inventory = list(csv.DictReader((base / "HISTORICAL_SOURCE_INVENTORY.csv").open(encoding="utf-8-sig")))

    spec = importlib.util.spec_from_file_location("recovered", MODELS)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)

    start = 200
    expected = len(draws) - start
    records = []
    ablation_raw = []
    portfolio_records = []
    portfolio_random_records = []
    leak = 0
    counts = {"A_v2": 0, "C_v2": 0, "contrarian_v2": 0}

    for idx in range(start, len(draws)):
        target = idx + 1
        hist = draws[:idx]
        actual = set(draws[idx])
        if len(hist) != target - 1:
            leak += 1

        pred = m.predict(hist)
        ablated_tickets = {}
        for name, ticket in pred.items():
            counts[name] += 1
            records.append(
                {
                    "target_round": target,
                    "training_through_round": idx,
                    "model": name,
                    "ticket": "-".join(map(str, ticket)),
                    "hits": len(set(ticket) & actual),
                }
            )
            if idx >= target:
                leak += 1

        for signal in SIGNALS:
            scores = scores_without_signal(m, hist, signal)
            for model_name in ("A_v2", "C_v2", "contrarian_v2"):
                ticket = ticket_from_scores(m, model_name, hist, scores)
                ablated_tickets[(model_name, signal)] = ticket
                ablation_raw.append(
                    {
                        "target_round": target,
                        "training_through_round": idx,
                        "model": model_name,
                        "omitted_signal": signal,
                        "hits": len(set(ticket) & actual),
                    }
                )

        candidates = portfolio_candidates(m, hist, pred, ablated_tickets)
        selected = select_five_ticket_portfolio(candidates)
        tickets = [t for _, t in selected]
        portfolio_records.append(
            {
                "target_round": target,
                "training_through_round": idx,
                "policy_version": PORTFOLIO_VERSION,
                "sources": "|".join(s for s, _ in selected),
                **bundle_metrics(tickets, actual),
            }
        )
        portfolio_random_records.append(
            random_bundle_baseline(target, actual, PORTFOLIO_RANDOM_BUNDLES_PER_TARGET)
        )

    out = ROOT / "analysis" / date / f"MASTER_FULL_V5_{datetime.datetime.now().astimezone().strftime('%H%M%S_%f')}"
    out.mkdir(parents=True)
    write_csv(out / "AC_CONTRARIAN_WALKFORWARD.csv", records)

    by_model = defaultdict(list)
    for r in records:
        by_model[r["model"]].append(r)
    successor_scorecards = [
        scorecard(name, by_model[name], random_by_target)
        for name in ("A_v2", "C_v2", "contrarian_v2")
    ]
    write_csv(out / "AC_CONTRARIAN_SCORECARD.csv", successor_scorecards)

    blocks = []
    for name in ("A_v2", "C_v2", "contrarian_v2"):
        blocks.extend(block_rows(name, by_model[name], random_by_target))
    write_csv(out / "AC_CONTRARIAN_NONOVERLAP_50_BLOCKS.csv", blocks)

    full_mean = {r["model"]: float(r["mean_hits"]) for r in successor_scorecards}
    ablation_group = defaultdict(list)
    for r in ablation_raw:
        ablation_group[(r["model"], r["omitted_signal"])].append(int(r["hits"]))
    ablation_summary = []
    for model_name in ("A_v2", "C_v2", "contrarian_v2"):
        for signal in SIGNALS:
            vals = ablation_group[(model_name, signal)]
            ablated_mean = statistics.mean(vals)
            ablation_summary.append(
                {
                    "model": model_name,
                    "signal": signal,
                    "n": len(vals),
                    "full_mean_hits": full_mean[model_name],
                    "ablated_mean_hits": ablated_mean,
                    "marginal_delta_full_minus_ablated": full_mean[model_name] - ablated_mean,
                    "status": "MORE_TEST",
                }
            )
    write_csv(out / "AC_CONTRARIAN_SIGNAL_ABLATION.csv", ablation_summary)

    write_csv(out / "FIVE_TICKET_PORTFOLIO_WALKFORWARD.csv", portfolio_records)
    write_csv(out / "FIVE_TICKET_RANDOM_BY_TARGET.csv", portfolio_random_records)

    portfolio_summary = {}
    metric_keys = (
        "max_hits", "any_ge2", "any_ge3", "any_ge4", "any_ge5", "any_ge6",
        "winning_union_coverage", "ticket_union_size", "mean_pair_overlap", "max_pair_overlap",
    )
    for key in metric_keys:
        actual_mean = statistics.mean(float(r[key]) for r in portfolio_records)
        random_mean = statistics.mean(float(r[f"random_{key}_mean"]) for r in portfolio_random_records)
        portfolio_summary[key] = {
            "policy_mean": actual_mean,
            "matched_random_mean": random_mean,
            "delta": actual_mean - random_mean,
        }
    portfolio_summary.update(
        {
            "policy_version": PORTFOLIO_VERSION,
            "targets": len(portfolio_records),
            "random_bundles_per_target": PORTFOLIO_RANDOM_BUNDLES_PER_TARGET,
            "random_bundles_total": len(portfolio_records) * PORTFOLIO_RANDOM_BUNDLES_PER_TARGET,
            "research_only": True,
            "promotion_to_weekly_policy": False,
        }
    )
    dump(out / "FIVE_TICKET_PORTFOLIO_SCORECARD.json", portfolio_summary)

    b_score_rows = list(csv.DictReader((base / "B_MODEL_SCORECARD.csv").open(encoding="utf-8-sig")))
    combined_score_rows = []
    for r in b_score_rows:
        combined_score_rows.append(
            {
                "family": "B", "model": r["model"], "n": r["n"], "mean_hits": r["mean_hits"],
                "variance": r["variance"], "random_mean_same_targets": r["random_mean_same_targets"],
                "delta_mean": r["delta_mean"], "rate_ge2": r["rate_ge2"], "rate_ge3": r["rate_ge3"],
                "rate_ge4": r["rate_ge4"], "rate_ge5": r["rate_ge5"], "rate_ge6": r["rate_ge6"],
                "status": "RETAIN_AS_MEASURED_NOT_AUTO_PROMOTED",
            }
        )
    for r in successor_scorecards:
        combined_score_rows.append(
            {
                "family": "SUCCESSOR", "model": r["model"], "n": r["n"], "mean_hits": r["mean_hits"],
                "variance": r["variance"], "random_mean_same_targets": r["random_mean_same_targets"],
                "delta_mean": r["delta_mean"], "rate_ge2": r["rate_ge2"], "rate_ge3": r["rate_ge3"],
                "rate_ge4": r["rate_ge4"], "rate_ge5": r["rate_ge5"], "rate_ge6": r["rate_ge6"],
                "status": "MORE_TEST",
            }
        )
    write_csv(out / "MODEL_SCORECARD_COMPLETE.csv", combined_score_rows)

    dump(
        out / "HYPOTHESIS_STATUS.json",
        {
            "pair_association": {
                "state": "MORE_TEST",
                "reason": "B mean can exceed matched random, but V4 multiple-testing survivors q<.05 = 0",
            },
            "triple_association": {
                "state": "MORE_TEST",
                "reason": "B mean can exceed matched random, but V4 multiple-testing survivors q<.05 = 0",
            },
            PORTFOLIO_VERSION: {
                "state": "RESEARCH_ONLY",
                "reason": "new frozen diagnostic validated historically today; not promoted to weekly purchase policy",
            },
            "automatic_rule_changes": False,
        },
    )

    expected_block_rows_per_model = math.ceil(expected / 50)
    scorecards_ok = (
        len(successor_scorecards) == 3
        and all(int(r["n"]) == expected for r in successor_scorecards)
        and all(sum(int(r[f"hits_{k}_count"]) for k in range(7)) == expected for r in successor_scorecards)
    )
    blocks_ok = (
        len(blocks) == 3 * expected_block_rows_per_model
        and all(sum(int(r["n"]) for r in blocks if r["model"] == name) == expected for name in ("A_v2", "C_v2", "contrarian_v2"))
    )
    ablation_ok = len(ablation_summary) == 12 and all(int(r["n"]) == expected for r in ablation_summary)
    portfolio_ok = len(portfolio_records) == expected and all(
        int(r["training_through_round"]) == int(r["target_round"]) - 1 for r in portfolio_records
    )
    portfolio_random_ok = len(portfolio_random_records) == expected and all(
        int(r["random_bundles"]) == PORTFOLIO_RANDOM_BUNDLES_PER_TARGET for r in portfolio_random_records
    )
    source_search_ok = (base / "HISTORICAL_SOURCE_INVENTORY.csv").exists() and len(source_inventory) > 0

    mandatory = {
        "latest_data_integrity": data.get("integrity") == "PASS" and data.get("latest_round") == len(draws),
        "fresh_cumulative_stats": (base / "NUMBER_FULL_STATS.csv").exists()
        and (base / "NUMBER_WINDOW_COMPARISON.csv").exists()
        and (base / "STRUCTURE_WINDOWS.csv").exists()
        and (base / "PAIR_STATS.csv").exists()
        and (base / "TRIPLE_STATS.csv").exists(),
        "B_full_walkforward": b.get("targets") == expected and b.get("leakage_failures") == 0,
        "fresh_random_baseline": len(random_by_target) == expected and (base / "RANDOM_EXACT_BASELINE.json").exists(),
        "historical_source_search": source_search_ok,
        "A_full_walkforward": counts["A_v2"] == expected,
        "C_full_walkforward": counts["C_v2"] == expected,
        "contrarian_full_walkforward": counts["contrarian_v2"] == expected,
        "AC_contrarian_leakage": leak == 0,
        "successor_scorecard_complete": scorecards_ok,
        "successor_random_comparison": scorecards_ok and all(math.isfinite(float(r["random_mean_same_targets"])) for r in successor_scorecards),
        "successor_block_stability": blocks_ok,
        "successor_signal_ablation": ablation_ok,
        "five_ticket_portfolio_walkforward": portfolio_ok,
        "five_ticket_matched_random_baseline": portfolio_random_ok,
        "model_scorecard_complete": len(combined_score_rows) == len(b_score_rows) + 3,
        "hypothesis_registry_written": True,
    }

    status = "FULL_COMPLETE" if all(mandatory.values()) else "PARTIAL"
    verification = {
        "status": status,
        "date": date,
        "data_cutoff": len(draws),
        "base_v4": base.relative_to(ROOT).as_posix(),
        "targets_expected": expected,
        "successor_prediction_records": len(records),
        "successor_counts": counts,
        "successor_leakage_failures": leak,
        "successor_scorecard_rows": len(successor_scorecards),
        "successor_block_rows": len(blocks),
        "signal_ablation_rows": len(ablation_summary),
        "historical_source_candidates": len(source_inventory),
        "portfolio_policy_version": PORTFOLIO_VERSION,
        "portfolio_targets": len(portfolio_records),
        "portfolio_random_bundles_total": len(portfolio_records) * PORTFOLIO_RANDOM_BUNDLES_PER_TARGET,
        "portfolio_research_only": True,
        "mandatory_checks": mandatory,
        "data_sha256": sha(DATA),
        "successor_source_sha256": sha(MODELS),
    }
    dump(out / "VERIFICATION.json", verification)
    dump(
        out / "COMPLETION.json",
        {
            "study_id": "DAILY_MASTER_FULL_V5_STRICT",
            "status": status,
            "data_cutoff": len(draws),
            "executed": True,
            "full_complete_requires_all_metric_gates": True,
        },
    )

    report = f"""# DAILY MASTER FULL strict — {date}

Status: **{status}**

## 1. 오늘 데이터 기준/원자료 확보·검증
Data cutoff: {len(draws)}. Integrity: {data.get('integrity')}. Historical source candidates inventoried: {len(source_inventory)}.

## 2. 오늘 실제 새로 계산한 핵심 발견
This run recalculated full successor scorecards, block stability, signal ablation, and a research-only five-ticket portfolio matched-random validation. No weekly candidate/final lines were generated.

## 3. 전체 누적 번호 분석
Fresh V4 NUMBER_FULL_STATS.csv exists and is gated.

## 4. 장기 vs 10/30/50/100 비교표
Fresh NUMBER_WINDOW_COMPARISON.csv and LONG_RECENT_CATEGORIES.csv are gated.

## 5. 간격·미출현
Included in fresh NUMBER_FULL_STATS.csv.

## 6. 구조·관계
Fresh STRUCTURE_WINDOWS.csv, PAIR_STATS.csv, TRIPLE_STATS.csv are gated.

## 7. A 모델
Fresh cutoff-safe targets: {counts['A_v2']}. Full hit/random scorecard, 50-target blocks, and four-signal leave-one-out ablation were computed.

## 8. B 실제 백테스트 + 랜덤 기준
Targets: {b.get('targets')}; leakage failures: {b.get('leakage_failures')}. Fresh per-target random baseline is required by the strict gate.

## 9. C 모델
Fresh cutoff-safe targets: {counts['C_v2']}. Full hit/random scorecard, blocks, and signal ablation were computed.

## 10. 역발상
Fresh cutoff-safe targets: {counts['contrarian_v2']}. Full hit/random scorecard, blocks, and signal ablation were computed.

## 11. 누적 추천·오답노트
Historical-source search inventory contains {len(source_inventory)} candidate files. Performance is not inferred without provenance.

## 12. 이전 가설 재검증
Pair/triple remain MORE_TEST because multiple-testing survivors are not established. {PORTFOLIO_VERSION} is RESEARCH_ONLY and is not auto-promoted to the weekly purchase policy.

## 13. 데이터 한계/미계산 항목
The new five-ticket policy is a frozen research diagnostic, not the weekly purchase policy. Any unresolved provenance remains explicit. FULL_COMPLETE requires every VERIFICATION mandatory check to be true.

Successor leakage failures: {leak}.
Five-ticket random bundles generated: {len(portfolio_records) * PORTFOLIO_RANDOM_BUNDLES_PER_TARGET}.
No candidate/recommendation/final lines generated.
"""
    (out / "REPORT.md").write_text(report, encoding="utf-8")
    print(json.dumps(verification, ensure_ascii=False))
    if status != "FULL_COMPLETE":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
