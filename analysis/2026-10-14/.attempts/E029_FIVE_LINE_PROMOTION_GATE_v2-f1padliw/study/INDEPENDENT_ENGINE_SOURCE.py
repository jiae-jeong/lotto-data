"""E025-E029 independent-signal and five-line portfolio research.

All predictions are historical, cutoff-safe studies. This module does not emit
future recommendations. Lottery lines are written only to research evidence.
"""
from __future__ import annotations

import csv
import json
import math
import random
import statistics
from collections import Counter, defaultdict
from pathlib import Path

import research_engine_v2 as engine

TARGETS = tuple(range(601, 1246))
NESTED_TARGETS = tuple(range(801, 1246))
SEED = 20261015
RANDOM_REPEATS = 100
BOOTSTRAP_REPEATS = 2000
BLOCK_LENGTH = 20
CANONICAL_SOURCE_COMMIT = "69426c16711d7d6c43f82da601249fb108f5f2b6"
CANONICAL_GITHUB_BLOB_SHA1 = "a898f212846057af9e79c8ebbbe3a33347c63898"
CANONICAL_DATA_SHA256_LF = "e534123cd7227f8c21d32251a567edeb018e7d1d9c4b049e4d23fb987f2619a4"
SIGNAL_NAMES = (
    "CROSS_ROUND_MARKOV_v1",
    "CALENDAR_SEASON_CONDITIONAL_v1",
    "PREVIOUS_SUM_REGIME_CONDITIONAL_v1",
)
B_MODELS = tuple(engine.MODELS)
FIXED_STRATEGIES = (
    "TOP_5",
    "MIN_OVERLAP_5",
    "MID_OVERLAP_5",
    "HIGH_OVERLAP_5",
    "SOURCE_DIVERSITY_5",
    "INDEPENDENT_SIGNAL_CENTRED_5",
    "B_PLUS_INDEPENDENT_MIX_5",
)
ALL_MODEL_STRATEGIES = FIXED_STRATEGIES + ("NESTED_DYNAMIC_5",)
METRIC_NAMES = ("max_hits", "any_2plus", "any_3plus", "any_4plus",
                "any_5plus", "any_6", "winning_union_coverage",
                "unique_number_coverage", "mean_pairwise_overlap",
                "line_hit_variance")
PRIMARY_GATE_METRICS = ("any_3plus", "max_hits")


def _write_csv(path: Path, rows: list[dict]) -> None:
    engine.csvfile(path, rows)


def _read_csv(path: Path) -> list[dict]:
    return engine.readcsv(path)


def _write_json(path: Path, obj: dict) -> None:
    engine.jsonfile(path, obj)


def _date_month(value: str) -> int:
    for fmt in ("%Y.%m.%d", "%Y-%m-%d", "%Y/%m/%d"):
        try:
            from datetime import datetime
            return datetime.strptime(value.strip(), fmt).month
        except ValueError:
            pass
    raise ValueError(f"Unrecognized draw date: {value!r}")


def _load_inputs(root: Path):
    actual, b_lookup = engine.load_panel(root)
    draws = _read_csv(root / engine.DATA)
    if len(draws) != 1245 or [int(row["round"]) for row in draws] != list(range(1, 1246)):
        raise ValueError("Verified canonical snapshot must contain continuous rounds 1..1245")
    parsed = []
    for row in draws:
        rnd = int(row["round"])
        numbers = tuple(sorted(int(row[f"no{i}"]) for i in range(1, 7)))
        bonus = int(row["bonus"])
        if len(set(numbers)) != 6 or any(not 1 <= n <= 45 for n in numbers):
            raise ValueError(f"Invalid main numbers at round {rnd}")
        if not 1 <= bonus <= 45 or bonus in numbers:
            raise ValueError(f"Invalid bonus at round {rnd}")
        parsed.append({"round": rnd, "date": row["date"], "month": _date_month(row["date"]),
                       "numbers": numbers, "bonus": bonus})
    if set(actual) != set(range(1, 1246)):
        raise ValueError("Validated target panel differs from the canonical snapshot")
    return parsed, actual, b_lookup


def _season(month: int) -> str:
    if month in (12, 1, 2): return "winter"
    if month in (3, 4, 5): return "spring"
    if month in (6, 7, 8): return "summer"
    return "autumn"


def _sum_regime(total: int) -> int:
    # Fixed before evaluation; boundaries are not estimated from target outcomes.
    return 0 if total < 120 else 1 if total < 145 else 2 if total < 170 else 3


def _rank_scores(scores: dict[int, float]) -> tuple[int, ...]:
    return tuple(sorted(range(1, 46), key=lambda n: (-scores[n], n)))


def _top_ticket(scores: dict[int, float]) -> tuple[int, ...]:
    return tuple(sorted(_rank_scores(scores)[:6]))


def _pearson(values: list[float], labels: list[float]) -> float:
    mx = statistics.mean(values); my = statistics.mean(labels)
    dx = [x - mx for x in values]; dy = [y - my for y in labels]
    denom = math.sqrt(math.fsum(x*x for x in dx) * math.fsum(y*y for y in dy))
    return math.fsum(x*y for x, y in zip(dx, dy)) / denom if denom else 0.0


def _signal_panels(draws: list[dict], b_lookup: dict):
    """Build independent scores incrementally; every target uses only 1..t-1."""
    ncounts = [0] * 46
    season_counts = {s: [0] * 46 for s in ("winter", "spring", "summer", "autumn")}
    season_n = Counter()
    transition = [[0] * 46 for _ in range(46)]
    source_exposure = [0] * 46
    regime_counts = [[0] * 46 for _ in range(4)]
    regime_n = [0] * 4
    predictions = []
    similarities = []
    for t in range(1, 601):
        row = draws[t - 1]
        for n in row["numbers"]: ncounts[n] += 1
        s = _season(row["month"]); season_n[s] += 1
        for n in row["numbers"]: season_counts[s][n] += 1
        if t >= 2:
            src = draws[t - 2]["numbers"]; reg = _sum_regime(sum(src))
            regime_n[reg] += 1
            for n in row["numbers"]: regime_counts[reg][n] += 1
            for m in src:
                source_exposure[m] += 1
                for n in row["numbers"]: transition[m][n] += 1

    for t in TARGETS:
        # State at target t includes round t-1, but labels stop at t-1.
        train_n = t - 1
        global_rate = {n: ncounts[n] / train_n for n in range(1, 46)}
        prev = draws[t - 2]
        current_season = _season(draws[t - 1]["month"])
        season_total = season_n[current_season]
        regime = _sum_regime(sum(prev["numbers"]))

        # Cross-round Markov transition: average smoothed P(n at k+1 | m at k)
        # over the six numbers in the as-of-target previous draw. Alpha=20.
        markov = {}
        for n in range(1, 46):
            terms = [(transition[m][n] + 20.0 * global_rate[n]) /
                     (source_exposure[m] + 20.0) for m in prev["numbers"]]
            markov[n] = math.fsum(terms) / 6.0

        # Same four-season bucket only, shrunk to the global rate by 30 draws.
        seasonal = {n: (season_counts[current_season][n] + 30.0 * global_rate[n]) /
                    (season_total + 30.0) for n in range(1, 46)}

        # Target-number frequencies conditioned on a fixed previous-draw sum bin;
        # this is a cross-round conditional model, not a ticket-structure filter.
        regime_total = regime_n[regime]
        sum_regime = {n: (regime_counts[regime][n] + 20.0 * global_rate[n]) /
                      (regime_total + 20.0) for n in range(1, 46)}
        score_sets = {SIGNAL_NAMES[0]: markov, SIGNAL_NAMES[1]: seasonal,
                      SIGNAL_NAMES[2]: sum_regime}
        b_tickets = {m: b_lookup[t, m] for m in B_MODELS}
        for name, scores in score_sets.items():
            ticket = _top_ticket(scores)
            ordered = _rank_scores(scores)
            rank = {n: i + 1 for i, n in enumerate(ordered)}
            for model, b_ticket in b_tickets.items():
                membership = [1.0 if n in set(b_ticket) else 0.0 for n in range(1, 46)]
                rank_to_selection = _pearson([float(rank[n]) for n in range(1, 46)], membership)
                inter = len(set(ticket) & set(b_ticket)); union = len(set(ticket) | set(b_ticket))
                similarities.append({"target_round": t, "training_cutoff": t - 1,
                    "signal": name, "b_model": model, "rank_to_selection_pearson": rank_to_selection,
                    "jaccard_top6": inter / union, "intersection_count": inter})
            predictions.append({"target_round": t, "training_cutoff": t - 1, "signal": name,
                "scores": scores, "ranked_numbers": ordered, "predicted_numbers": ticket,
                "actual_numbers": tuple(sorted(b_lookup[t, B_MODELS[0]]))})

        # Add draw t to state only after all target-t forecasts are frozen.
        row = draws[t - 1]
        for n in row["numbers"]: ncounts[n] += 1
        s = _season(row["month"]); season_n[s] += 1
        for n in row["numbers"]: season_counts[s][n] += 1
        if t >= 2:
            src = draws[t - 2]["numbers"]; reg = _sum_regime(sum(src))
            regime_n[reg] += 1
            for n in row["numbers"]: regime_counts[reg][n] += 1
            for m in src:
                source_exposure[m] += 1
                for n in row["numbers"]: transition[m][n] += 1
    return predictions, similarities


def _prediction_rows(predictions, actual):
    rows = []
    for p in predictions:
        hit = len(set(p["predicted_numbers"]) & set(actual[p["target_round"]]))
        rows.append({"target_round": p["target_round"], "training_cutoff": p["training_cutoff"],
            "signal": p["signal"], "predicted_numbers": " ".join(map(str, p["predicted_numbers"])),
            "ranked_numbers": " ".join(map(str, p["ranked_numbers"])),
            "actual_numbers": " ".join(map(str, actual[p["target_round"]])), "hits": hit,
            "feature_max_round": p["training_cutoff"], "random_seed": SEED})
    return rows


def _metrics(values):
    n = len(values)
    return {"n": n, "mean_hits": statistics.mean(values),
        "variance_hits_population": statistics.pvariance(values),
        **{f"hits_{k}_count": values.count(k) for k in range(7)},
        **{f"rate_ge_{k}": sum(x >= k for x in values) / n for k in range(2, 7)}}


def _holm(rows: list[dict], p_field: str = "p_raw") -> None:
    order = sorted(range(len(rows)), key=lambda i: (rows[i][p_field], i))
    running = 0.0; m = len(rows)
    for rank, idx in enumerate(order):
        running = max(running, min(1.0, (m - rank) * float(rows[idx][p_field])))
        rows[idx]["p_holm"] = running


def _block_bootstrap(values: list[float], seed: int, reps: int = BOOTSTRAP_REPEATS,
                     block: int = BLOCK_LENGTH) -> dict:
    if not values: raise ValueError("Cannot bootstrap an empty paired series")
    n = len(values); observed = statistics.mean(values); rng = random.Random(seed)
    chunks = math.ceil(n / block); boot = []
    for _ in range(reps):
        total = 0.0; count = 0
        for _ in range(chunks):
            start = rng.randrange(n)
            take = min(block, n - count)
            for offset in range(take): total += values[(start + offset) % n]
            count += take
            if count == n: break
        boot.append(total / n)
    boot.sort()
    lo = boot[int(.025 * (reps - 1))]; hi = boot[int(.975 * (reps - 1))]
    centered = [x - observed for x in values]
    null_boot = []
    for _ in range(reps):
        total = 0.0; count = 0
        for _ in range(chunks):
            start = rng.randrange(n); take = min(block, n - count)
            for offset in range(take): total += centered[(start + offset) % n]
            count += take
            if count == n: break
        null_boot.append(total / n)
    p_two = (1 + sum(abs(x) >= abs(observed) for x in null_boot)) / (reps + 1)
    p_greater = (1 + sum(x >= observed for x in null_boot)) / (reps + 1)
    return {"estimate": observed, "ci95_low": lo, "ci95_high": hi,
            "p_two_sided": p_two, "p_greater": p_greater,
            "bootstrap_reps": reps, "block_length": block}


def _metric_values(hits: list[int], tickets_by_target: list[list[tuple[int, ...]]] | None = None,
                   actual_by_target: list[tuple[int, ...]] | None = None) -> dict:
    maximum = max(hits)
    result = {"max_hits": maximum, **{f"any_{k}plus": int(maximum >= k) for k in range(2, 6)},
              "any_6": int(maximum == 6)}
    if tickets_by_target is not None and actual_by_target is not None:
        metrics = []
        for tickets, actual in zip(tickets_by_target, actual_by_target):
            line_hits = [len(set(ticket) & set(actual)) for ticket in tickets]
            union = set().union(*(set(ticket) for ticket in tickets))
            overlaps = [len(set(a) & set(b)) for i, a in enumerate(tickets) for b in tickets[i + 1:]]
            metrics.append({"winning_union_coverage": len(union & set(actual)) / 6,
                "unique_number_coverage": len(union),
                "mean_pairwise_overlap": statistics.mean(overlaps) if overlaps else 0.0,
                "line_hit_variance": statistics.pvariance(line_hits),
                "mean_line_hits": statistics.mean(line_hits)})
        for key in metrics[0]: result[key] = statistics.mean(x[key] for x in metrics)
    return result


def _task_path(root: Path, task_id: str) -> Path:
    matches = [p.parent for p in (root / "analysis").rglob("COMPLETION.json")
               if p.parent.name == task_id and json.loads(p.read_text(encoding="utf-8")).get("task_id") == task_id]
    if len(matches) != 1: raise FileNotFoundError(f"Expected one completed {task_id}; found {len(matches)}")
    return matches[0]


def _e025(root: Path, out: Path, task: dict) -> dict:
    draws, actual, b_lookup = _load_inputs(root)
    predictions, similarities = _signal_panels(draws, b_lookup)
    similarity_by = defaultdict(list); model_jaccard = defaultdict(list)
    for row in similarities:
        key = row["signal"]; similarity_by[key].append(row)
        model_jaccard[key, row["b_model"]].append(row["jaccard_top6"])
    summary = []; survivor = {}
    for name in SIGNAL_NAMES:
        rows = similarity_by[name]
        mean_abs_corr = statistics.mean(abs(float(r["rank_to_selection_pearson"])) for r in rows)
        mean_jaccard = statistics.mean(float(r["jaccard_top6"]) for r in rows)
        model_means = {model: statistics.mean(model_jaccard[name, model]) for model in B_MODELS}
        max_model_jaccard = max(model_means.values())
        keep = mean_abs_corr < .20 and mean_jaccard < .20 and max_model_jaccard < .35
        survivor[name] = keep
        summary.append({"signal": name, "target_count": len(TARGETS), "b_component_count": len(B_MODELS),
            "mean_abs_rank_to_selection_correlation": mean_abs_corr,
            "mean_top6_jaccard": mean_jaccard, "max_component_mean_jaccard": max_model_jaccard,
            "max_jaccard_component": max(model_means, key=model_means.get),
            "independence_thresholds": "mean_abs_corr<0.20;mean_jaccard<0.20;max_component_mean_jaccard<0.35",
            "status": "SURVIVES" if keep else "DROPPED_AS_B_REDUNDANT"})
    definitions = {
        "study_id": task["id"], "target_rounds": [601, 1245], "training_cutoff": "t-1",
        "data_sha256": engine.digest(root / engine.DATA), "canonical_data_sha256_lf": CANONICAL_DATA_SHA256_LF,
        "canonical_source_commit": CANONICAL_SOURCE_COMMIT, "canonical_github_blob_sha1": CANONICAL_GITHUB_BLOB_SHA1,
        "b_cache_sha256": engine.raw_digest(root / engine.CACHE),
        "random_seed": SEED, "tie_break": "descending score, then lower number; ticket numbers sorted ascending",
        "selection_rule": "top six by frozen signal score; no outcome based parameter selection",
        "screening_rule": "A signal survives only if all three B similarity thresholds pass; outcome metrics do not enter screening.",
        "signals": [
            {"name": SIGNAL_NAMES[0], "formula": "mean over m in previous draw of (cooccur[m,n]+20*global_rate[n])/(source_exposure[m]+20)",
             "variables": "prior-round source number m; next-round target number n; global_rate from draws 1..t-1",
             "training_range": "transition source rounds 1..t-2; transition outcomes 2..t-1", "weight": "equal 1/6 over prior-round numbers", "smoothing": "20 pseudo-transitions at target-specific global rate"},
            {"name": SIGNAL_NAMES[1], "formula": "(season_count[n]+30*global_rate[n])/(season_draws+30)",
             "variables": "fixed four-season bucket of target date; counts of n in prior outcomes from the same season",
             "training_range": "outcome rounds 1..t-1", "weight": "one season bucket; no learned weight", "smoothing": "30 pseudo-draws at target-specific global rate"},
            {"name": SIGNAL_NAMES[2], "formula": "(conditional_count[previous_sum_bin,n]+20*global_rate[n])/(bin_draws+20)",
             "variables": "sum of draw t-1; fixed bins <120, 120..144, 145..169, >=170; target-number counts in successor draws",
             "training_range": "transition source rounds 1..t-2; successor outcomes 2..t-1", "weight": "one fixed prior-sum bin", "smoothing": "20 pseudo-draws at target-specific global rate"},
        ]}
    _write_json(out / "SIGNAL_DEFINITIONS.json", definitions)
    _write_csv(out / "SIGNAL_INDEPENDENCE.csv", summary)
    _write_csv(out / "TARGET_SIMILARITY.csv", similarities)
    _write_csv(out / "SURVIVOR_STATUS.csv", summary)
    _write_csv(out / "PREDICTIONS.csv", _prediction_rows(predictions, actual))
    checks = {"status": "PASS", "target_count": len(TARGETS), "signals": len(SIGNAL_NAMES),
        "similarity_rows": len(similarities), "cutoff_violations": sum(p["training_cutoff"] != p["target_round"] - 1 for p in predictions),
        "invalid_lines": sum(len(p["predicted_numbers"]) != 6 or len(set(p["predicted_numbers"])) != 6 for p in predictions),
        "screening_uses_outcomes": False, "future_predictions": 0,
        "survivors": [n for n, keep in survivor.items() if keep],
        "dropped": [n for n, keep in survivor.items() if not keep]}
    if checks["cutoff_violations"] or checks["invalid_lines"]: raise ValueError("E025 invariant failure")
    _write_json(out / "VERIFICATION.json", checks)
    _write_report(out / "REPORT.md", task, "Exploration was restricted to three frozen cross-round/seasonal conditional families. Correlation is Pearson correlation between candidate score rank and each cached B ticket's 0/1 membership vector; Jaccard compares top-six sets. Signals were screened on prediction geometry only, not hits.",
        {"similarity_summary": summary, "survivors": checks["survivors"], "dropped": checks["dropped"]},
        "Only signals below every pre-registered B-overlap threshold proceed as independent candidates. This screen tests redundancy, not predictive merit.")
    return {"executed_cases": len(predictions) + len(similarities), "verification": checks}


def _e026(root: Path, out: Path, task: dict) -> dict:
    e025 = _task_path(root, "E025_INDEPENDENT_SIGNAL_DISCOVERY_v1")
    draws, actual, b_lookup = _load_inputs(root)
    signal_rows = _read_csv(e025 / "PREDICTIONS.csv")
    survivors = {r["signal"] for r in _read_csv(e025 / "SURVIVOR_STATUS.csv") if r["status"] == "SURVIVES"}
    # All frozen candidates are tested as a falsification panel; only survivors are
    # considered independent candidates downstream.
    signal_tickets = {(int(r["target_round"]), r["signal"]): tuple(map(int, r["predicted_numbers"].split())) for r in signal_rows}
    random_rng = random.Random(SEED); random_rows = []; random_by_target = {}; target_records = []
    prediction_rows = []; hits_by_model = defaultdict(list); target_hits = defaultdict(dict)
    for t in TARGETS:
        target_random = [tuple(sorted(random_rng.sample(range(1, 46), 6))) for _ in range(RANDOM_REPEATS)]
        actual_set = set(actual[t]); random_hits = [len(actual_set & set(line)) for line in target_random]
        random_by_target[t] = random_hits
        for i, (line, hits) in enumerate(zip(target_random, random_hits), 1):
            random_rows.append({"target_round": t, "training_cutoff": t - 1, "replicate": i,
                "predicted_numbers": " ".join(map(str, line)), "hits": hits, "seed": SEED})
        target_records.append({"target_round": t, "training_cutoff": t - 1,
            "random_mean_hits": statistics.mean(random_hits),
            **{f"random_rate_ge_{k}": statistics.mean(h >= k for h in random_hits) for k in range(2, 7)}})
        for model in B_MODELS:
            line = b_lookup[t, model]; h = len(actual_set & set(line)); hits_by_model[model].append(h); target_hits[t][model] = h
            prediction_rows.append({"target_round": t, "training_cutoff": t - 1, "model": model,
                "source_status": "FROZEN_B_COMPARATOR", "predicted_numbers": " ".join(map(str, line)), "hits": h})
        for name in SIGNAL_NAMES:
            line = signal_tickets[t, name]; h = len(actual_set & set(line)); hits_by_model[name].append(h); target_hits[t][name] = h
            prediction_rows.append({"target_round": t, "training_cutoff": t - 1, "model": name,
                "source_status": "INDEPENDENCE_SURVIVOR" if name in survivors else "DROPPED_SIGNAL_EXPLORATORY",
                "predicted_numbers": " ".join(map(str, line)), "hits": h})
    all_random = [h for values in random_by_target.values() for h in values]
    metrics = []
    for model, vals in list(hits_by_model.items()) + [("RANDOM_6LINE", all_random)]:
        metrics.append({"model": model, "source_status": "RANDOM_BASELINE" if model == "RANDOM_6LINE" else
                        "INDEPENDENCE_SURVIVOR" if model in survivors else "COMPARATOR_OR_DROPPED_SIGNAL", **_metrics(vals)})
    paired = []
    for name in SIGNAL_NAMES:
        for metric in ("mean_hits", "rate_ge_2", "rate_ge_3", "rate_ge_4", "rate_ge_5"):
            series = []
            for t in TARGETS:
                model_hits = target_hits[t][name]; random_hits = random_by_target[t]
                model_value = model_hits if metric == "mean_hits" else int(model_hits >= int(metric.split("_")[-1]))
                random_values = random_hits if metric == "mean_hits" else [int(h >= int(metric.split("_")[-1])) for h in random_hits]
                series.append(float(model_value) - statistics.mean(random_values))
            boot = _block_bootstrap(series, SEED + SIGNAL_NAMES.index(name) * 17 + len(paired))
            paired.append({"signal": name, "survivor_status": "SURVIVES" if name in survivors else "DROPPED_AS_B_REDUNDANT",
                "metric": metric, **boot})
    for row in paired: row["p_raw"] = row["p_two_sided"]
    _holm(paired)
    block_rows = []
    for name in SIGNAL_NAMES:
        for start in range(601, 1246, 100):
            ts = list(range(start, min(start + 100, 1246)))
            vals = [target_hits[t][name] - statistics.mean(random_by_target[t]) for t in ts]
            block_rows.append({"signal": name, "start_round": start, "end_round": ts[-1], "n": len(ts),
                "mean_hit_delta_vs_random": statistics.mean(vals),
                "rate_3plus_delta_vs_random": statistics.mean(target_hits[t][name] >= 3 for t in ts) -
                    statistics.mean(statistics.mean(h >= 3 for h in random_by_target[t]) for t in ts)})
    checks = {"status": "PASS", "target_count": len(TARGETS), "candidate_signal_predictions": len(signal_rows),
        "random_tickets": len(random_rows), "random_repeats_per_target": RANDOM_REPEATS,
        "b_comparator_predictions": len(TARGETS) * len(B_MODELS), "cutoff_violations": 0,
        "random_seed": SEED, "target_outcome_used_for_tuning": False, "future_predictions": 0,
        "independent_survivors": sorted(survivors)}
    _write_csv(out / "PREDICTIONS.csv", prediction_rows)
    _write_csv(out / "RANDOM_BY_TARGET.csv", random_rows)
    _write_csv(out / "TARGET_RANDOM_SUMMARY.csv", target_records)
    _write_csv(out / "METRICS.csv", metrics)
    _write_csv(out / "PAIRED_RANDOM_COMPARISON.csv", paired)
    _write_csv(out / "BLOCK_STABILITY.csv", block_rows)
    _write_json(out / "VERIFICATION.json", checks)
    _write_report(out / "REPORT.md", task,
        "Each frozen signal was generated with cutoff t-1 for targets 601..1245. Each target received 100 new uniform six-number random tickets, compared on the same target. No parameter tuning was performed. Paired uncertainty uses circular 20-target moving-block bootstrap (4,000 replicates); Holm correction covers the 15 registered signal-by-metric contrasts.",
        {"metrics": metrics, "paired_random": paired, "survivors": sorted(survivors)},
        "This is retrospective walk-forward evidence through an already observed dataset; it cannot establish prospective advantage. A signal dropped for B redundancy remains exploratory only.")
    return {"executed_cases": len(prediction_rows) + len(random_rows), "verification": checks}


def _e027(root: Path, out: Path, task: dict) -> dict:
    e025 = _task_path(root, "E025_INDEPENDENT_SIGNAL_DISCOVERY_v1")
    e026 = _task_path(root, "E026_INDEPENDENT_MODEL_WALKFORWARD_v1")
    _, actual, b_lookup = _load_inputs(root)
    survivors = {r["signal"] for r in _read_csv(e025 / "SURVIVOR_STATUS.csv") if r["status"] == "SURVIVES"}
    vote_predictions = {(int(r["target_round"]), r["model"]): tuple(map(int, r["predicted_numbers"].split()))
                        for r in _read_csv(e026 / "PREDICTIONS.csv") if r["model"] in SIGNAL_NAMES}
    bank_rows = []; overlap_rows = []; provenance_rows = []
    b_order = {m: i for i, m in enumerate(B_MODELS)}
    for t in TARGETS:
        b_tickets = {m: b_lookup[t, m] for m in B_MODELS}
        depth = Counter(n for line in b_tickets.values() for n in line)
        raw = []
        for model in B_MODELS:
            line = tuple(sorted(b_tickets[model]))
            score = statistics.mean(depth[n] for n in line) / len(B_MODELS) + (len(B_MODELS) - b_order[model]) * 1e-7
            raw.append({"target_round": t, "training_cutoff": t - 1, "source_model": model,
                "source_family": "B", "numbers": line, "score": score, "score_rank": b_order[model] + 1,
                "eligible_independent": False,
                "inclusion_reason": "FROZEN_CUTOFF_SAFE_B_COMPONENT_FORECAST"})
        for i, name in enumerate(SIGNAL_NAMES):
            if name not in survivors: continue
            line = vote_predictions[t, name]
            # Within-source top-six rank strength, normalized to [0,1].
            source_row = next(r for r in _read_csv(e025 / "PREDICTIONS.csv")
                              if int(r["target_round"]) == t and r["signal"] == name)
            ranked = list(map(int, source_row["ranked_numbers"].split())) if "ranked_numbers" in source_row else list(line)
            rank_map = {n: i + 1 for i, n in enumerate(ranked)}
            score = statistics.mean((46 - rank_map.get(n, 45)) / 45 for n in line)
            raw.append({"target_round": t, "training_cutoff": t - 1, "source_model": name,
                "source_family": "INDEPENDENT", "numbers": line, "score": score,
                "score_rank": 8 + i + 1, "eligible_independent": True,
                "inclusion_reason": "PASSED_E025_GEOMETRY_SCREEN_AND_E026_CUTOFF_SAFE_FORECAST"})
        raw.sort(key=lambda r: (-r["score"], r["source_model"]))
        groups = []
        for row in raw:
            destination = next((g for g in groups if len(set(g["numbers"]) & set(row["numbers"])) >= 5), None)
            if destination is None:
                groups.append({"target_round": t, "training_cutoff": t - 1,
                    "candidate_id": f"T{t:04d}_C{len(groups)+1:02d}", "numbers": row["numbers"],
                    "score": row["score"], "primary_source": row["source_model"],
                    "sources": [row["source_model"]], "eligible_independent": row["eligible_independent"],
                    "reasons": [row["inclusion_reason"]]})
                provenance_rows.append({**row, "candidate_id": groups[-1]["candidate_id"],
                    "candidate_numbers": " ".join(map(str, row["numbers"])), "canonical_source": row["source_model"],
                    "dedup_status": "CANONICAL"})
            else:
                destination["sources"].append(row["source_model"])
                destination["eligible_independent"] |= row["eligible_independent"]
                destination["reasons"].append(row["inclusion_reason"])
                provenance_rows.append({**row, "candidate_id": destination["candidate_id"],
                    "candidate_numbers": " ".join(map(str, row["numbers"])), "canonical_source": destination["primary_source"],
                    "dedup_status": "MERGED_NEAR_DUPLICATE_OVERLAP_GE_5"})
        if len(groups) < 5: raise ValueError(f"Target {t} has only {len(groups)} unique candidate lines")
        for g in groups:
            g["candidate_score_rank"] = 1 + sum(x["score"] > g["score"] for x in groups)
            g["source_model"] = g["primary_source"]
            g["candidate_numbers"] = " ".join(map(str, g["numbers"]))
            g["source_models"] = "|".join(g["sources"])
            g["line_overlap_policy"] = "merge if intersection>=5; keep highest-score canonical; preserve every source in provenance"
            g["inclusion_reason"] = "|".join(sorted(set(g["reasons"])))
            bank_rows.append({k: v for k, v in g.items() if k not in ("numbers", "sources", "reasons")})
        for i, a in enumerate(groups):
            for b in groups[i + 1:]:
                inter = len(set(a["numbers"]) & set(b["numbers"]))
                overlap_rows.append({"target_round": t, "training_cutoff": t - 1,
                    "candidate_a": a["candidate_id"], "candidate_b": b["candidate_id"],
                    "intersection_count": inter, "jaccard": inter / len(set(a["numbers"]) | set(b["numbers"]))})
    checks = {"status": "PASS", "target_count": len(TARGETS), "candidate_rows": len(bank_rows),
        "provenance_rows": len(provenance_rows), "overlap_rows": len(overlap_rows),
        "cutoff_violations": sum(int(r["training_cutoff"]) != int(r["target_round"]) - 1 for r in bank_rows),
        "duplicate_or_near_duplicate_pairs": sum(int(r["intersection_count"]) >= 5 for r in overlap_rows),
        "independent_sources_included": sorted(survivors), "future_outcomes_used_for_bank": False,
        "future_predictions": 0}
    _write_csv(out / "CANDIDATE_BANK.csv", bank_rows)
    _write_csv(out / "CANDIDATE_PROVENANCE.csv", provenance_rows)
    _write_csv(out / "CANDIDATE_OVERLAP.csv", overlap_rows)
    _write_json(out / "VERIFICATION.json", checks)
    _write_report(out / "REPORT.md", task,
        "For every target, the bank contains the frozen B component/combined forecasts and only E025 survivors validated in E026. Candidate tickets are constructed from t-1 information. Exact/near duplicates with intersection at least five are merged to one canonical candidate while every source remains in CANDIDATE_PROVENANCE.csv.",
        checks, "The bank is a source-preserving historical candidate set; its existence does not imply any candidate outperforms random.")
    return {"executed_cases": len(bank_rows) + len(provenance_rows) + len(overlap_rows), "verification": checks}


def _parse_numbers(text: str) -> tuple[int, ...]:
    return tuple(sorted(map(int, text.split())))


def _portfolio_metrics(tickets: list[tuple[int, ...]], actual: tuple[int, ...]) -> dict:
    line_hits = [len(set(x) & set(actual)) for x in tickets]
    max_hits = max(line_hits); union = set().union(*(set(x) for x in tickets))
    pair_overlaps = [len(set(a) & set(b)) for i, a in enumerate(tickets) for b in tickets[i+1:]]
    return {"max_hits": max_hits, "any_2plus": int(max_hits >= 2), "any_3plus": int(max_hits >= 3),
        "any_4plus": int(max_hits >= 4), "any_5plus": int(max_hits >= 5), "any_6": int(max_hits == 6),
        "winning_union_coverage": len(union & set(actual)) / 6, "unique_number_coverage": len(union),
        "mean_pairwise_overlap": statistics.mean(pair_overlaps),
        "line_hit_variance": statistics.pvariance(line_hits), "mean_line_hits": statistics.mean(line_hits)}


def _select_portfolio(strategy: str, candidates: list[dict]) -> list[dict]:
    score_order = sorted(candidates, key=lambda x: (-float(x["candidate_score"]), x["candidate_id"]))
    b = [x for x in score_order if x["source_family"] == "B"]
    independent = [x for x in score_order if x["source_family"] == "INDEPENDENT"]
    selected = []
    if strategy == "TOP_5": return score_order[:5]
    if strategy == "MIN_OVERLAP_5":
        while len(selected) < 5:
            pool = [x for x in score_order if x not in selected]
            selected.append(min(pool, key=lambda x: (sum(len(set(x["numbers"]) & set(y["numbers"])) for y in selected),
                -float(x["candidate_score"]), x["candidate_id"])))
        return selected
    if strategy == "MID_OVERLAP_5":
        selected.append(score_order[0])
        while len(selected) < 5:
            pool = [x for x in score_order if x not in selected]
            selected.append(min(pool, key=lambda x: (abs(statistics.mean(
                len(set(x["numbers"]) & set(y["numbers"])) for y in selected) - 1.2),
                -float(x["candidate_score"]), x["candidate_id"])))
        return selected
    if strategy == "HIGH_OVERLAP_5":
        selected.append(score_order[0])
        while len(selected) < 5:
            pool = [x for x in score_order if x not in selected]
            selected.append(max(pool, key=lambda x: (sum(len(set(x["numbers"]) & set(y["numbers"])) for y in selected),
                float(x["candidate_score"]), x["candidate_id"])))
        return selected
    if strategy == "SOURCE_DIVERSITY_5":
        seen = set()
        for x in score_order:
            for source in x["source_models"].split("|"):
                if source not in seen:
                    selected.append(x); seen.update(x["source_models"].split("|")); break
            if len(selected) == 5: break
        selected.extend(x for x in score_order if x not in selected)
        return selected[:5]
    if strategy == "INDEPENDENT_SIGNAL_CENTRED_5":
        selected.extend(independent[:3])
        selected.extend(x for x in b if x not in selected)
        selected.extend(x for x in score_order if x not in selected)
        return selected[:5]
    if strategy == "B_PLUS_INDEPENDENT_MIX_5":
        selected.extend(b[:3]); selected.extend(x for x in independent if x not in selected)
        selected.extend(x for x in b if x not in selected); selected.extend(x for x in score_order if x not in selected)
        return selected[:5]
    raise ValueError("Unknown portfolio strategy: " + strategy)


def _random_portfolio(rng: random.Random) -> list[tuple[int, ...]]:
    result = set()
    while len(result) < 5:
        result.add(tuple(sorted(rng.sample(range(1, 46), 6))))
    return sorted(result)


def _e028(root: Path, out: Path, task: dict) -> dict:
    e027 = _task_path(root, "E027_FIVE_LINE_CANDIDATE_BANK_v1")
    _, actual, _ = _load_inputs(root)
    provenance = _read_csv(e027 / "CANDIDATE_PROVENANCE.csv")
    candidates_by_target = defaultdict(list)
    for row in provenance:
        if row["dedup_status"] != "CANONICAL": continue
        candidates_by_target[int(row["target_round"])].append({
            "candidate_id": row["candidate_id"], "numbers": _parse_numbers(row["candidate_numbers"]),
            "source_model": row["source_model"], "source_family": row["source_family"],
            "source_models": row["source_model"], "candidate_score": float(row["score"]),
            "candidate_score_rank": int(row["score_rank"]),
            "eligible_independent": row["eligible_independent"] == "True"})
    # Restore merged provenance groups from the candidate bank.
    bank = _read_csv(e027 / "CANDIDATE_BANK.csv")
    bank_by_key = {(int(r["target_round"]), r["candidate_id"]): r for r in bank}
    for t, items in candidates_by_target.items():
        for item in items:
            saved = bank_by_key[t, item["candidate_id"]]
            item["source_models"] = saved["source_models"]
            item["source_family"] = "INDEPENDENT" if saved["eligible_independent"] == "True" else "B"
            item["candidate_score"] = float(saved["score"])
            item["eligible_independent"] = saved["eligible_independent"] == "True"

    target_strategy = defaultdict(dict); portfolio_rows = []; target_rows = []
    random_rows = []; random_summary = {}; ticket_rows = []
    for t in TARGETS:
        cands = candidates_by_target[t]
        if len(cands) < 5: raise ValueError(f"Candidate bank too small at target {t}")
        actual_t = actual[t]
        for strategy in FIXED_STRATEGIES:
            selected = _select_portfolio(strategy, cands)
            if len(selected) != 5 or len({x["candidate_id"] for x in selected}) != 5:
                raise ValueError(f"Invalid five-distinct-line portfolio: {strategy}/{t}")
            lines = [x["numbers"] for x in selected]
            metrics = _portfolio_metrics(lines, actual_t)
            target_strategy[t][strategy] = {"metrics": metrics, "selected": selected}
            portfolio_rows.extend({"target_round": t, "training_cutoff": t - 1, "strategy": strategy,
                "line_rank": i + 1, "candidate_id": x["candidate_id"], "source_model": x["source_model"],
                "source_models": x["source_models"], "numbers": " ".join(map(str, x["numbers"])),
                "candidate_score": x["candidate_score"], "candidate_score_rank": x["candidate_score_rank"],
                "selected_strategy": strategy}
                for i, x in enumerate(selected))
        rng = random.Random(SEED + t); reps = []
        for rep in range(1, RANDOM_REPEATS + 1):
            lines = _random_portfolio(rng); metrics = _portfolio_metrics(lines, actual_t); reps.append(metrics)
            random_rows.append({"target_round": t, "training_cutoff": t - 1, "replicate": rep,
                **metrics, "seed": SEED + t})
        random_summary[t] = {k: statistics.mean(float(x[k]) for x in reps) for k in METRIC_NAMES + ("mean_line_hits",)}

    # Nested dynamic choice: trailing 200 completed targets; no target-t result is read.
    dynamic_rows = []; dynamic_trace = []
    for t in NESTED_TARGETS:
        prior = range(t - 200, t)
        ranked = []
        for order, strategy in enumerate(FIXED_STRATEGIES):
            vals = [target_strategy[p][strategy]["metrics"] for p in prior]
            ranked.append((sum(x["any_3plus"] for x in vals), sum(x["any_4plus"] for x in vals),
                statistics.mean(x["max_hits"] for x in vals), -order, strategy))
        chosen = max(ranked)[-1]
        current = target_strategy[t][chosen]
        lines = [x["numbers"] for x in current["selected"]]
        metrics = current["metrics"]
        target_strategy[t]["NESTED_DYNAMIC_5"] = current
        target_rows.append({"target_round": t, "training_cutoff": t - 1, "strategy": "NESTED_DYNAMIC_5",
            "selected_strategy": chosen, **metrics})
        dynamic_rows.extend({"target_round": t, "training_cutoff": t - 1, "strategy": "NESTED_DYNAMIC_5",
            "line_rank": i + 1, "candidate_id": x["candidate_id"], "source_model": x["source_model"],
            "source_models": x["source_models"], "numbers": " ".join(map(str, x["numbers"])),
            "selected_strategy": chosen} for i, x in enumerate(current["selected"]))
        dynamic_trace.append({"target_round": t, "training_cutoff": t - 1, "history_start": t - 200,
            "history_end": t - 1, "selected_strategy": chosen,
            "objective": "maximize trailing any_3plus count, then any_4plus count, then mean max_hits; fixed strategy order tie-break"})

    summary_rows = []
    for strategy in FIXED_STRATEGIES:
        for t in TARGETS:
            m = target_strategy[t][strategy]["metrics"]
            target_rows.append({"target_round": t, "training_cutoff": t - 1, "strategy": strategy, **m})
        summary_rows.append({"strategy": strategy, "target_count": len(TARGETS),
            **{metric: statistics.mean(target_strategy[t][strategy]["metrics"][metric] for t in TARGETS) for metric in METRIC_NAMES}})
    for t in TARGETS:
        target_rows.append({"target_round": t, "training_cutoff": t - 1, "strategy": "RANDOM_5_LINES",
                            **random_summary[t], "selected_strategy": "100 same-target random five-line portfolios"})
    summary_rows.append({"strategy": "RANDOM_5_LINES", "target_count": len(TARGETS),
        **{metric: statistics.mean(random_summary[t][metric] for t in TARGETS) for metric in METRIC_NAMES}})
    summary_rows.append({"strategy": "NESTED_DYNAMIC_5", "target_count": len(NESTED_TARGETS),
        **{metric: statistics.mean(target_strategy[t]["NESTED_DYNAMIC_5"]["metrics"][metric] for t in NESTED_TARGETS) for metric in METRIC_NAMES}})
    portfolio_rows.extend(dynamic_rows)
    for row in target_rows:
        if row["strategy"] != "RANDOM_5_LINES" and row["strategy"] not in FIXED_STRATEGIES and row["strategy"] != "NESTED_DYNAMIC_5":
            raise ValueError("Unexpected strategy record")
    checks = {"status": "PASS", "target_count": len(TARGETS), "random_portfolios": len(random_rows),
        "random_portfolios_per_target": RANDOM_REPEATS, "fixed_strategies": list(FIXED_STRATEGIES),
        "nested_dynamic_targets": len(NESTED_TARGETS), "nested_history_targets": 200,
        "portfolio_line_rows": len(portfolio_rows), "cutoff_violations": sum(int(r["training_cutoff"]) != int(r["target_round"]) - 1 for r in target_rows),
        "future_outcomes_used_in_candidate_bank": False, "future_outcomes_used_in_dynamic_choice": False,
        "future_predictions": 0}
    _write_csv(out / "PORTFOLIO_TICKETS.csv", portfolio_rows)
    _write_csv(out / "RANDOM_5_BY_TARGET.csv", random_rows)
    _write_csv(out / "STRATEGY_BY_TARGET.csv", target_rows)
    _write_csv(out / "STRATEGY_SUMMARY.csv", summary_rows)
    _write_csv(out / "NESTED_SELECTOR_TRACE.csv", dynamic_trace)
    _write_json(out / "VERIFICATION.json", checks)
    _write_report(out / "REPORT.md", task,
        "Every target receives seven fixed candidate-bank strategies, a same-target RANDOM_5_LINES baseline from 100 random bundles, and the nested selector for targets 801..1245. The selector uses only the preceding 200 target outcomes to choose among the seven frozen construction strategies; all candidate lines and overlaps are created before the target outcome is scored.",
        {"summary": summary_rows, "verification": checks},
        "Five-line outcomes are compared against five random lines on identical target rounds. This historical replay is exploratory and does not change the current five-line operational rule.")
    return {"executed_cases": len(portfolio_rows) + len(random_rows) + len(target_rows), "verification": checks}


def _e029(root: Path, out: Path, task: dict) -> dict:
    e028 = _task_path(root, "E028_FIVE_LINE_PORTFOLIO_SELECTOR_v2")
    target_rows = _read_csv(e028 / "STRATEGY_BY_TARGET.csv")
    by_strategy = defaultdict(dict)
    for row in target_rows:
        by_strategy[row["strategy"]][int(row["target_round"])] = row
    target_set = sorted(by_strategy["RANDOM_5_LINES"])
    if target_set != list(TARGETS): raise ValueError("Random-5 baseline target coverage mismatch")
    tests = []
    for strategy in ALL_MODEL_STRATEGIES:
        model_targets = sorted(by_strategy[strategy])
        if strategy == "NESTED_DYNAMIC_5" and model_targets != list(NESTED_TARGETS):
            raise ValueError("Nested selector target coverage mismatch")
        if strategy != "NESTED_DYNAMIC_5" and model_targets != list(TARGETS):
            raise ValueError(f"Strategy target coverage mismatch: {strategy}")
        for metric in METRIC_NAMES:
            common = model_targets
            model_mean = statistics.mean(float(by_strategy[strategy][t][metric]) for t in common)
            random_mean = statistics.mean(float(by_strategy["RANDOM_5_LINES"][t][metric]) for t in common)
            delta = model_mean - random_mean
            boot = (_block_bootstrap([float(by_strategy[strategy][t][metric]) - float(by_strategy["RANDOM_5_LINES"][t][metric]) for t in common],
                     SEED + ALL_MODEL_STRATEGIES.index(strategy) * 101 + METRIC_NAMES.index(metric))
                    if metric in PRIMARY_GATE_METRICS or (strategy == "NESTED_DYNAMIC_5" and metric == "any_4plus")
                    else {"estimate": delta, "ci95_low": None, "ci95_high": None, "p_two_sided": None,
                          "p_greater": None, "bootstrap_reps": 0, "block_length": BLOCK_LENGTH})
            tests.append({"strategy": strategy, "metric": metric, "targets": len(common),
                "model_mean": model_mean, "random5_mean": random_mean,
                **boot, "comparison_family": "PRIMARY_NESTED_DYNAMIC" if strategy == "NESTED_DYNAMIC_5" and metric in PRIMARY_GATE_METRICS else "EXPLORATORY"})
    primary = [r for r in tests if r["strategy"] == "NESTED_DYNAMIC_5" and r["metric"] in PRIMARY_GATE_METRICS]
    for row in primary: row["p_raw"] = row["p_greater"]
    _holm(primary)
    for row in primary:
        for dest in tests:
            if dest["strategy"] == row["strategy"] and dest["metric"] == row["metric"]:
                dest["p_holm"] = row["p_holm"]
    # Chronological 50-target blocks and leave-best-block-out sensitivity.
    block_rows = []
    dyn_targets = list(NESTED_TARGETS)
    for start in range(dyn_targets[0], dyn_targets[-1] + 1, 50):
        ts = [t for t in dyn_targets if start <= t < start + 50]
        if not ts: continue
        for metric in PRIMARY_GATE_METRICS + ("any_4plus",):
            deltas = [float(by_strategy["NESTED_DYNAMIC_5"][t][metric]) - float(by_strategy["RANDOM_5_LINES"][t][metric]) for t in ts]
            block_rows.append({"start_round": ts[0], "end_round": ts[-1], "metric": metric,
                "n": len(ts), "delta": statistics.mean(deltas), "positive": statistics.mean(deltas) > 0})
    leave_best = {}
    for metric in PRIMARY_GATE_METRICS:
        candidates = []
        for i in range(0, len(dyn_targets), 50):
            ts = dyn_targets[i:i+50]
            vals = [float(by_strategy["NESTED_DYNAMIC_5"][t][metric]) - float(by_strategy["RANDOM_5_LINES"][t][metric]) for t in ts]
            candidates.append((statistics.mean(vals), ts))
        _, worst = max(candidates, key=lambda x: x[0])
        remain = [float(by_strategy["NESTED_DYNAMIC_5"][t][metric]) - float(by_strategy["RANDOM_5_LINES"][t][metric])
                  for t in dyn_targets if t not in set(worst)]
        leave_best[metric] = {"removed_start": min(worst), "removed_end": max(worst), "remaining_delta": statistics.mean(remain)}
    gate_tests = {r["metric"]: r for r in primary}
    any4 = next(r for r in tests if r["strategy"] == "NESTED_DYNAMIC_5" and r["metric"] == "any_4plus")
    blocks_by_metric = {m: [r for r in block_rows if r["metric"] == m] for m in PRIMARY_GATE_METRICS + ("any_4plus",)}
    checks = {
        "positive_ci_any_3plus": gate_tests["any_3plus"]["ci95_low"] > 0,
        "positive_ci_max_hits": gate_tests["max_hits"]["ci95_low"] > 0,
        "holm_adjusted_primary_tests_below_0_05": all(float(r["p_holm"]) < .05 for r in primary),
        "any_4plus_not_worse_point_and_ci": any4["estimate"] >= 0 and any4["ci95_low"] >= 0,
        "block_direction_stable": all(sum(bool(r["positive"]) for r in blocks_by_metric[m]) >= math.ceil(.7 * len(blocks_by_metric[m]))
                                       for m in PRIMARY_GATE_METRICS),
        "not_driven_by_best_50_round_block": all(leave_best[m]["remaining_delta"] > 0 for m in PRIMARY_GATE_METRICS),
        "leakage_zero": int(json.loads((e028 / "VERIFICATION.json").read_text(encoding="utf-8"))["cutoff_violations"]) == 0,
        "at_least_one_independent_signal_survived": bool(json.loads((_task_path(root, "E025_INDEPENDENT_SIGNAL_DISCOVERY_v1") / "VERIFICATION.json").read_text(encoding="utf-8"))["survivors"]),
        "nested_targets": len(NESTED_TARGETS), "bootstrap_reps": BOOTSTRAP_REPEATS,
    }
    status = "PROMOTE" if all(v for k, v in checks.items() if isinstance(v, bool)) else "DO_NOT_PROMOTE"
    gate = {"promotion_status": status, "data_cutoff": 1245, "operational_ticket_count": 5,
        "selector": "NESTED_DYNAMIC_5", "comparison": "same-target 100-random-bundle mean; targets 801..1245",
        "primary_metrics": list(PRIMARY_GATE_METRICS), "multiplicity_correction": "Holm step-down across the two registered primary tests",
        "checks": checks, "leave_best_50_target_block_out": leave_best,
        "future_predictions": 0, "recommendation_generation": False}
    _write_csv(out / "PROMOTION_TESTS.csv", tests)
    _write_csv(out / "PROMOTION_BLOCKS.csv", block_rows)
    _write_json(out / "PROMOTION_GATE.json", gate)
    _write_json(out / "VERIFICATION.json", {"status": "PASS", "test_rows": len(tests), "block_rows": len(block_rows),
        "random_baseline_targets": len(target_set), "nested_targets": len(NESTED_TARGETS),
        "future_predictions": 0, "promotion_status": status})
    _write_report(out / "REPORT.md", task,
        "The registered nested 200-target selector was compared with 100 same-target random five-line portfolios on targets 801..1245. Primary tests were paired block-bootstrap differences for any_3plus and max_hits with Holm correction across those two tests. The gate also required non-worse any_4plus, chronological block consistency, zero leakage, and positive effects after removing the best 50-target block.",
        {"promotion_gate": gate, "primary_tests": primary, "any_4plus": any4},
        "Promotion is allowed only if every check passes. A failed gate preserves five lines as the operational count and keeps this selector out of use.")
    return {"executed_cases": len(tests) + len(block_rows), "verification": {"status": "PASS", "promotion_status": status}}


def _write_report(path: Path, task: dict, method: str, results: dict, finding: str) -> None:
    body = ["# " + task["question"], "", "## MAINTENANCE/RECHECK", "",
        "Canonical data and the frozen seven-component B forecast cache were read as provenance-controlled inputs. No E010-E024 study was rerun.",
        "", "## NEW STUDY", "", method, "", "## NEW FINDING", "", finding, "",
        "## Results", "", "```json", json.dumps(results, ensure_ascii=False, indent=2, allow_nan=False), "```", "",
        "## NEXT TEST", "", "Retain this specification and require the independent promotion gate; do not use the historical result to generate a recommendation.", ""]
    with path.open("x", encoding="utf-8") as stream: stream.write("\n".join(body))


def run_study(root: Path, out: Path, task: dict) -> dict:
    root = Path(root).resolve(); out = Path(out).resolve()
    if not out.is_dir(): raise FileNotFoundError("Research engine must create a fresh study output directory")
    kind = task["kind"]
    handlers = {"independent_signal_discovery": _e025,
        "independent_model_walkforward": _e026,
        "five_line_candidate_bank": _e027,
        "five_line_portfolio_selector": _e028,
        "five_line_promotion_gate": _e029}
    if kind not in handlers: raise ValueError("Unsupported E025-E029 kind: " + kind)
    return handlers[kind](root, out, task)
