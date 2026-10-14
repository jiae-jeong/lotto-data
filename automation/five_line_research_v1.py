"""Five-line lotto portfolio research v1.

Historical research only. Uses the frozen cutoff-safe B component cache and evaluates
five-ticket portfolio construction without producing a future recommendation.
"""
from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import random
import statistics
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "lotto_data.csv"
CACHE = ROOT / "analysis/2026-10-12/REGIME_DYNAMIC_NESTED_v1/base_predictions_reused.csv"
PLAN = ROOT / "automation/five_line_research_plan_v1.json"
COMPONENTS = (
    "long_frequency",
    "current_gap",
    "frequency_plus_gap",
    "recent_momentum",
    "structure_profile",
    "pair_association",
    "triple_association",
)
TARGET_START = 601
FROZEN_END = 1245
SELECTOR_LOOKBACK = 200
RANDOM_REPEATS = 100
SEED = 20261014


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def readcsv(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows):
    rows = list(rows)
    if not rows:
        raise ValueError(f"Refuse empty CSV: {path.name}")
    with path.open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, obj):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(obj, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def parse_numbers(text: str):
    return tuple(sorted(int(x) for x in text.split()))


def load_panel():
    draws = readcsv(DATA)
    if [int(r["round"]) for r in draws[:FROZEN_END]] != list(range(1, FROZEN_END + 1)):
        raise ValueError("Canonical draw data is not continuous through frozen cutoff 1245")
    actual = {
        int(r["round"]): tuple(sorted(int(r[f"no{i}"]) for i in range(1, 7)))
        for r in draws if int(r["round"]) <= FROZEN_END
    }
    if actual[FROZEN_END] != (4, 5, 25, 28, 32, 42):
        raise ValueError("Frozen draw 1245 mismatch")

    cache = readcsv(CACHE)
    lookup = {}
    leakage_failures = 0
    for row in cache:
        t = int(row["target_round"])
        if not (201 <= t <= FROZEN_END):
            continue
        model = row["model"]
        if model not in COMPONENTS:
            continue
        training = int(row["training_through_round"])
        if training != t - 1:
            leakage_failures += 1
        ticket = parse_numbers(row["predicted_numbers"])
        if len(ticket) != 6 or len(set(ticket)) != 6 or not all(1 <= n <= 45 for n in ticket):
            raise ValueError(f"Invalid component ticket {t}/{model}")
        if parse_numbers(row["actual_numbers"]) != actual[t]:
            raise ValueError(f"Outcome mismatch {t}/{model}")
        if (t, model) in lookup:
            raise ValueError(f"Duplicate component forecast {t}/{model}")
        lookup[t, model] = ticket
    expected = {(t, m) for t in range(201, FROZEN_END + 1) for m in COMPONENTS}
    if set(lookup) != expected:
        missing = sorted(expected - set(lookup))[:5]
        raise ValueError(f"Missing frozen component forecasts, examples={missing}")
    if leakage_failures:
        raise ValueError(f"Future-data leakage detected in {leakage_failures} cached forecasts")
    return actual, lookup


def pair_overlap_mean(tickets):
    pairs = list(itertools.combinations(tickets, 2))
    return statistics.mean(len(set(a) & set(b)) for a, b in pairs)


def bundle_row(tickets, winning):
    hits = [len(set(q) & winning) for q in tickets]
    union = set().union(*(set(q) for q in tickets))
    return {
        "max_hits": max(hits),
        "any_2plus": int(max(hits) >= 2),
        "any_3plus": int(max(hits) >= 3),
        "any_4plus": int(max(hits) >= 4),
        "any_5plus": int(max(hits) >= 5),
        "any_6": int(max(hits) == 6),
        "unique_number_coverage": len(union),
        "winning_union_coverage": len(union & winning),
        "mean_pairwise_overlap": pair_overlap_mean(tickets),
    }


def aggregate(rows, name, target_count=None, simulated_bundles=None):
    rows = list(rows)
    n = len(rows)
    if not n:
        raise ValueError(f"No rows to aggregate for {name}")
    return {
        "strategy": name,
        "target_rounds": target_count if target_count is not None else n,
        "simulated_bundles": simulated_bundles if simulated_bundles is not None else n,
        "mean_bundle_max_hits": statistics.mean(float(r["max_hits"]) for r in rows),
        "mean_unique_number_coverage": statistics.mean(float(r["unique_number_coverage"]) for r in rows),
        "mean_winning_union_coverage": statistics.mean(float(r["winning_union_coverage"]) for r in rows),
        "mean_pairwise_overlap": statistics.mean(float(r["mean_pairwise_overlap"]) for r in rows),
        "rate_any_2plus": statistics.mean(float(r["any_2plus"]) for r in rows),
        "rate_any_3plus": statistics.mean(float(r["any_3plus"]) for r in rows),
        "rate_any_4plus": statistics.mean(float(r["any_4plus"]) for r in rows),
        "rate_any_5plus": statistics.mean(float(r["any_5plus"]) for r in rows),
        "rate_any_6": statistics.mean(float(r["any_6"]) for r in rows),
    }


def random_bundle(target, size, repeat, winning):
    rng = random.Random(SEED + target * 1_000_000 + size * 10_000 + repeat)
    tickets = [tuple(sorted(rng.sample(range(1, 46), 6))) for _ in range(size)]
    return bundle_row(tickets, winning)


def moving_block_ci(diffs, seed, reps=4000, block=20):
    n = len(diffs)
    observed = statistics.mean(diffs)
    rng = random.Random(seed)
    boot = []
    centered = []
    for _ in range(reps):
        sample = []
        while len(sample) < n:
            start = rng.randrange(n)
            sample.extend(diffs[(start + j) % n] for j in range(block))
        estimate = statistics.mean(sample[:n])
        boot.append(estimate)
        centered.append(estimate - observed)
    boot.sort()
    lo = boot[int(.025 * (reps - 1))]
    hi = boot[int(.975 * (reps - 1))]
    p = (1 + sum(abs(v) >= abs(observed) - 1e-15 for v in centered)) / (reps + 1)
    return observed, lo, hi, p


def summarize_by_target(random_target_means, size, targets):
    selected = [r for r in random_target_means if int(r["ticket_count"]) == size and int(r["target_round"]) in targets]
    metrics = [
        "max_hits",
        "any_2plus",
        "any_3plus",
        "any_4plus",
        "any_5plus",
        "any_6",
        "unique_number_coverage",
        "winning_union_coverage",
        "mean_pairwise_overlap",
    ]
    result = {}
    for metric in metrics:
        result[metric] = statistics.mean(float(r[metric]) for r in selected)
    return result


def main():
    run_date = datetime.now().strftime("%Y-%m-%d")
    out = ROOT / "analysis" / run_date / "FIVE_LINE_RESEARCH_v1"
    if out.exists():
        verification = out / "VERIFICATION.json"
        if verification.exists():
            prior = json.loads(verification.read_text(encoding="utf-8"))
            if prior.get("data_cutoff") == FROZEN_END and prior.get("status") == "PASS":
                print("FIVE_LINE_RESEARCH_ALREADY_COMPLETE_FOR_CUTOFF_1245")
                return 0
        raise FileExistsError(f"Existing incomplete output directory: {out}")
    out.mkdir(parents=True)

    actual, lookup = load_panel()
    targets = list(range(TARGET_START, FROZEN_END + 1))
    winning_sets = {t: set(actual[t]) for t in targets}
    bundles = list(itertools.combinations(COMPONENTS, 5))
    if len(bundles) != 21:
        raise AssertionError("Expected C(7,5)=21 component bundles")

    # E020: random three-line vs five-line baseline, including per-target expectations.
    random_target_means = []
    random_summary = []
    for size in (3, 5):
        all_rows = []
        for t in targets:
            target_rows = []
            for repeat in range(1, RANDOM_REPEATS + 1):
                row = random_bundle(t, size, repeat, winning_sets[t])
                target_rows.append(row)
                all_rows.append(row)
            mean_row = {"target_round": t, "ticket_count": size}
            for key in target_rows[0]:
                mean_row[key] = statistics.mean(float(r[key]) for r in target_rows)
            random_target_means.append(mean_row)
        random_summary.append(
            aggregate(all_rows, f"RANDOM_{size}_LINES", len(targets), len(all_rows))
        )
    three = random_summary[0]
    five = random_summary[1]
    delta = {"strategy": "RANDOM_5_MINUS_3", "target_rounds": len(targets), "simulated_bundles": 0}
    for key in (
        "mean_bundle_max_hits", "mean_unique_number_coverage", "mean_winning_union_coverage",
        "mean_pairwise_overlap", "rate_any_2plus", "rate_any_3plus", "rate_any_4plus",
        "rate_any_5plus", "rate_any_6"
    ):
        delta[key] = five[key] - three[key]
    random_summary.append(delta)
    write_csv(out / "E020_RANDOM_3_VS_5_SUMMARY.csv", random_summary)
    write_csv(out / "E020_RANDOM_BY_TARGET.csv", random_target_means)

    # Compute every five-component portfolio on every target.
    bundle_target_rows = []
    by_bundle = defaultdict(list)
    by_target = defaultdict(list)
    for t in targets:
        for bundle in bundles:
            tickets = [lookup[t, m] for m in bundle]
            stats = bundle_row(tickets, winning_sets[t])
            row = {
                "target_round": t,
                "training_through_round": t - 1,
                "bundle": ";".join(bundle),
                **stats,
                "leakage_check": True,
            }
            bundle_target_rows.append(row)
            by_bundle[bundle].append(row)
            by_target[t].append(row)

    # E021: low/mid/high overlap strata defined within each target without target outcomes.
    strata_rows = []
    strata_values = defaultdict(list)
    for t in targets:
        ordered = sorted(by_target[t], key=lambda r: (float(r["mean_pairwise_overlap"]), r["bundle"]))
        for rank, row in enumerate(ordered):
            stratum = "LOW_OVERLAP" if rank < 7 else "MID_OVERLAP" if rank < 14 else "HIGH_OVERLAP"
            tagged = {"target_round": t, "stratum": stratum, **{k: row[k] for k in (
                "max_hits", "any_2plus", "any_3plus", "any_4plus", "any_5plus", "any_6",
                "unique_number_coverage", "winning_union_coverage", "mean_pairwise_overlap"
            )}}
            strata_rows.append(tagged)
            strata_values[stratum].append(tagged)
    strata_summary = [aggregate(strata_values[s], s, len(targets), len(strata_values[s]))
                      for s in ("LOW_OVERLAP", "MID_OVERLAP", "HIGH_OVERLAP")]
    write_csv(out / "E021_OVERLAP_STRATA_BY_TARGET.csv", strata_rows)
    write_csv(out / "E021_OVERLAP_STRATA_SUMMARY.csv", strata_summary)

    # E022: all 21 fixed five-component bundles plus outcome-free min/max overlap strategies.
    bundle_summary = [aggregate(rows, "FIXED_" + ";".join(bundle), len(targets), len(rows))
                      for bundle, rows in by_bundle.items()]
    dynamic_rows = []
    min_rows = []
    max_rows = []
    for t in targets:
        ordered = sorted(by_target[t], key=lambda r: (float(r["mean_pairwise_overlap"]), r["bundle"]))
        for strategy, source in (("MIN_OVERLAP_5", ordered[0]), ("MAX_OVERLAP_5", ordered[-1])):
            row = {"target_round": t, "strategy": strategy, "selected_bundle": source["bundle"],
                   **{k: source[k] for k in (
                       "max_hits", "any_2plus", "any_3plus", "any_4plus", "any_5plus", "any_6",
                       "unique_number_coverage", "winning_union_coverage", "mean_pairwise_overlap"
                   )}}
            dynamic_rows.append(row)
            (min_rows if strategy == "MIN_OVERLAP_5" else max_rows).append(row)
    strategy_summary = [
        aggregate(min_rows, "MIN_OVERLAP_5", len(targets), len(min_rows)),
        aggregate(max_rows, "MAX_OVERLAP_5", len(targets), len(max_rows)),
    ]
    strategy_summary.extend(bundle_summary)
    random5_for_compare = {
        "strategy": "RANDOM_5_LINES",
        "target_rounds": five["target_rounds"],
        "simulated_bundles": five["simulated_bundles"],
        **{k: five[k] for k in five if k.startswith("mean_") or k.startswith("rate_")},
    }
    strategy_summary.append(random5_for_compare)
    write_csv(out / "E022_ALL_FIVE_LINE_BUNDLE_SUMMARY.csv", strategy_summary)
    write_csv(out / "E022_DYNAMIC_OVERLAP_STRATEGIES.csv", dynamic_rows)

    # E023: nested selector. At target t, pick the five-component bundle using only t-200..t-1.
    selector_targets = list(range(TARGET_START + SELECTOR_LOOKBACK, FROZEN_END + 1))
    selector_trace = []
    selector_eval = []
    bundle_lookup = {(int(r["target_round"]), r["bundle"]): r for r in bundle_target_rows}
    for t in selector_targets:
        history = range(t - SELECTOR_LOOKBACK, t)
        scored = []
        for bundle in bundles:
            name = ";".join(bundle)
            past = [bundle_lookup[h, name] for h in history]
            objective = (
                sum(int(r["any_3plus"]) for r in past),
                sum(int(r["any_4plus"]) for r in past),
                statistics.mean(int(r["max_hits"]) for r in past),
                -statistics.mean(float(r["mean_pairwise_overlap"]) for r in past),
            )
            scored.append((objective, name))
        best_objective, best_name = max(scored, key=lambda x: (x[0], tuple(-COMPONENTS.index(m) for m in x[1].split(";"))))
        current = bundle_lookup[t, best_name]
        selector_trace.append({
            "target_round": t,
            "training_start_round": t - SELECTOR_LOOKBACK,
            "training_end_round": t - 1,
            "selected_bundle": best_name,
            "past_any_3plus_count": best_objective[0],
            "past_any_4plus_count": best_objective[1],
            "past_mean_max_hits": best_objective[2],
            "past_mean_pairwise_overlap": -best_objective[3],
            "target_max_hits": current["max_hits"],
            "target_any_2plus": current["any_2plus"],
            "target_any_3plus": current["any_3plus"],
            "target_any_4plus": current["any_4plus"],
            "target_any_5plus": current["any_5plus"],
            "target_any_6": current["any_6"],
            "target_unique_number_coverage": current["unique_number_coverage"],
            "target_winning_union_coverage": current["winning_union_coverage"],
            "target_mean_pairwise_overlap": current["mean_pairwise_overlap"],
            "leakage_check": (t - 1) < t,
        })
        selector_eval.append({
            "max_hits": current["max_hits"],
            "any_2plus": current["any_2plus"],
            "any_3plus": current["any_3plus"],
            "any_4plus": current["any_4plus"],
            "any_5plus": current["any_5plus"],
            "any_6": current["any_6"],
            "unique_number_coverage": current["unique_number_coverage"],
            "winning_union_coverage": current["winning_union_coverage"],
            "mean_pairwise_overlap": current["mean_pairwise_overlap"],
        })
    selector_summary = [aggregate(selector_eval, "NESTED_200_ANY3_SELECTOR", len(selector_targets), len(selector_eval))]
    random5_selector = summarize_by_target(random_target_means, 5, set(selector_targets))
    selector_summary.append({
        "strategy": "RANDOM_5_LINES_TARGET_MEAN",
        "target_rounds": len(selector_targets),
        "simulated_bundles": len(selector_targets) * RANDOM_REPEATS,
        "mean_bundle_max_hits": random5_selector["max_hits"],
        "mean_unique_number_coverage": random5_selector["unique_number_coverage"],
        "mean_winning_union_coverage": random5_selector["winning_union_coverage"],
        "mean_pairwise_overlap": random5_selector["mean_pairwise_overlap"],
        "rate_any_2plus": random5_selector["any_2plus"],
        "rate_any_3plus": random5_selector["any_3plus"],
        "rate_any_4plus": random5_selector["any_4plus"],
        "rate_any_5plus": random5_selector["any_5plus"],
        "rate_any_6": random5_selector["any_6"],
    })
    write_csv(out / "E023_NESTED_SELECTOR_TRACE.csv", selector_trace)
    write_csv(out / "E023_NESTED_SELECTOR_SUMMARY.csv", selector_summary)

    # E024: promotion gate against same-target random-five expectations, using paired block bootstrap.
    random5_by_t = {int(r["target_round"]): r for r in random_target_means if int(r["ticket_count"]) == 5}
    tests = []
    metric_map = {
        "max_hits": "target_max_hits",
        "any_3plus": "target_any_3plus",
        "any_4plus": "target_any_4plus",
        "winning_union_coverage": "target_winning_union_coverage",
    }
    for i, (baseline_metric, selector_metric) in enumerate(metric_map.items()):
        diffs = [float(r[selector_metric]) - float(random5_by_t[int(r["target_round"])][baseline_metric])
                 for r in selector_trace]
        observed, lo, hi, p = moving_block_ci(diffs, SEED + 900 + i)
        tests.append({
            "metric": baseline_metric,
            "selector_minus_random5": observed,
            "ci95_low": lo,
            "ci95_high": hi,
            "p_two_sided_block_bootstrap": p,
            "targets": len(diffs),
            "block": 20,
            "reps": 4000,
        })

    any3_test = next(r for r in tests if r["metric"] == "any_3plus")
    max_test = next(r for r in tests if r["metric"] == "max_hits")
    any4_test = next(r for r in tests if r["metric"] == "any_4plus")
    block_signs = []
    for start in range(0, len(selector_trace), 100):
        block_rows = selector_trace[start:start + 100]
        if not block_rows:
            continue
        diffs = [float(r["target_any_3plus"]) - float(random5_by_t[int(r["target_round"])] ["any_3plus"])
                 for r in block_rows]
        block_signs.append({
            "block": f"{block_rows[0]['target_round']}..{block_rows[-1]['target_round']}",
            "any3_delta": statistics.mean(diffs),
            "positive": statistics.mean(diffs) > 0,
        })
    stable_positive_blocks = sum(bool(r["positive"]) for r in block_signs)
    gate_pass = (
        any3_test["ci95_low"] > 0
        and max_test["ci95_low"] > 0
        and any4_test["ci95_low"] >= 0
        and stable_positive_blocks >= max(3, math.ceil(len(block_signs) * 0.6))
    )
    gate = {
        "status": "PASS",
        "data_cutoff": FROZEN_END,
        "operational_ticket_count": 5,
        "candidate_portfolio_count": len(bundles),
        "selector_lookback": SELECTOR_LOOKBACK,
        "selector_targets": len(selector_targets),
        "future_predictions": 0,
        "leakage_failures": 0,
        "tests": tests,
        "temporal_any3_blocks": block_signs,
        "promotion_status": "PROMOTE_FOR_PROSPECTIVE_CONFIRMATION" if gate_pass else "DO_NOT_PROMOTE",
        "promotion_rule": (
            "Require lower 95% block-bootstrap bound >0 for any3 and max_hits, "
            "nonnegative lower bound for any4, and positive any3 delta in at least 60% "
            "of ~100-target blocks (minimum three)."
        ),
        "interpretation": (
            "This gate may reject the historical five-line selector. Rejection means retain research status "
            "and do not use the selector as a validated purchase rule."
        ),
    }
    write_json(out / "E024_PROMOTION_GATE.json", gate)

    verification = {
        "status": "PASS",
        "data_cutoff": FROZEN_END,
        "targets_601_1245": len(targets),
        "nested_selector_targets": len(selector_targets),
        "five_component_bundle_count": len(bundles),
        "random_repeats_per_target_per_size": RANDOM_REPEATS,
        "random_three_bundle_count": len(targets) * RANDOM_REPEATS,
        "random_five_bundle_count": len(targets) * RANDOM_REPEATS,
        "bundle_target_records": len(bundle_target_rows),
        "leakage_failures": 0,
        "future_predictions": 0,
        "current_operational_standard": "FIVE_LINES",
        "legacy_three_line_E019": "PRESERVED_AS_HISTORICAL_ONLY",
        "plan_sha256": sha256(PLAN),
        "data_sha256": sha256(DATA),
        "cache_sha256": sha256(CACHE),
        "code_sha256": sha256(Path(__file__)),
    }
    write_json(out / "VERIFICATION.json", verification)

    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    write_json(out / "FROZEN_SPEC.json", {
        "plan": plan,
        "verification_basis": verification,
        "created_local_date": run_date,
    })

    report = f"""# Five-line portfolio research v1 — {run_date}

## Operational change

The current practical purchase/recommendation standard is **5 lines**, not 3.
E019 remains preserved as a historical three-line experiment and is not treated as the current portfolio standard.

## E020 — Random 3 vs 5 baseline

Random baselines were simulated on the same 645 historical targets with {RANDOM_REPEATS} deterministic bundles per target and size.
The purpose is to separate the mechanical benefit of buying two extra lines from any model benefit.

## E021 — Five-line overlap structure

All 21 C(7,5) component portfolios were ranked by pre-outcome pairwise overlap inside each target.
LOW/MID/HIGH overlap strata were evaluated without using the target outcome to assign the stratum.

## E022 — Five-line construction strategies

All 21 fixed five-component portfolios were evaluated, together with outcome-free MIN_OVERLAP_5 and MAX_OVERLAP_5 selectors.
Full-sample rankings are exploratory only and are not promoted into a future rule.

## E023 — Nested 200-target selector

For each target from {selector_targets[0]} through {selector_targets[-1]}, the selected five-component portfolio was chosen using only the prior {SELECTOR_LOOKBACK} targets.
Primary historical selection objective: prior count of at-least-3-hit portfolio events, then at-least-4-hit events, mean bundle max hits, and lower overlap.

## E024 — Promotion gate

Promotion status: **{gate['promotion_status']}**.

The gate compares the nested selector with same-target random-five expectations using moving-block bootstrap and temporal stability.
No future ticket is generated by this research job.

## Verification

```json
{json.dumps(verification, ensure_ascii=False, indent=2)}
```

## Rule for weekly work

Any current weekly portfolio analysis must report **5 lines**. A three-line result can be cited only as a legacy experiment.
The five lines must be evaluated as one portfolio: individual-line quality, line-to-line overlap, unique-number coverage, and 3+/4+ tail performance versus a random-five baseline.
"""
    (out / "REPORT.md").write_text(report, encoding="utf-8")

    # Manifest last so it covers all published evidence except itself.
    manifest = []
    for path in sorted(out.iterdir()):
        if path.is_file():
            manifest.append({"file": path.name, "bytes": path.stat().st_size, "sha256": sha256(path)})
    write_csv(out / "SHA256_MANIFEST.csv", manifest)

    print(json.dumps({
        "status": "PASS",
        "output": str(out.relative_to(ROOT)),
        "promotion_status": gate["promotion_status"],
        "files": [p.name for p in sorted(out.iterdir())],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
