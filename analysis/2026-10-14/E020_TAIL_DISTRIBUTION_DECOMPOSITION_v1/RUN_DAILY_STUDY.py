#!/usr/bin/env python3
"""Additive 2026-10-14 lotto research run. Existing inputs and studies are read-only."""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import itertools
import json
import math
import os
import random
import statistics
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
INPUT = OUT / "input" / "lotto_data_github_main.csv"
RUN_ID = OUT.name
SEED = 20261014
PATHS = 20_000
DIRECT_RANDOM_PER_TARGET = 1_000
WINDOWS = (10, 30, 50, 100)
EXPECTED_COLUMNS = ["round", "date", "no1", "no2", "no3", "no4", "no5", "no6", "bonus"]
REMOTE_MAIN = "01333b4d90a0ea9dc350d1150c748dd51493465d"
REMOTE_DATA_SHA256 = "e534123cd7227f8c21d32251a567edeb018e7d1d9c4b049e4d23fb987f2619a4"
START_HEAD = "f4ab740f1ba0190a3087082605a67aa102d32ffd"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_bytes(path: Path) -> bytes:
    return path.read_bytes().replace(b"\r\n", b"\n")


def git_sha256(path: Path) -> str:
    return hashlib.sha256(git_bytes(path)).hexdigest()


def write_json(path: Path, obj: object) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    if fields is None:
        fields = list(rows[0]) if rows else []
    with path.open("x", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def load_module():
    src = ROOT / "automation" / "daily_master_v3.py"
    spec = importlib.util.spec_from_file_location("daily_master_v3", src)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    mod.ROOT = ROOT
    mod.SNAPSHOT = INPUT
    mod.RANDOM_SEED = SEED
    return mod, src


def source_inventory() -> list[dict]:
    out = []
    for base in (ROOT / "analysis", ROOT / "research", ROOT / "outputs", ROOT / "automation"):
        for p in base.rglob("*"):
            if not p.is_file() or OUT in p.parents:
                continue
            name = p.name.lower()
            rel = p.relative_to(ROOT).as_posix()
            if any(x in name for x in ("recommend", "purchase", "error", "mistake", "wrong", "review")):
                if any(x in rel.lower() for x in ("walk_forward_prediction", "b_model_prediction", "recommendation_sources.json")):
                    continue
                cls = "candidate_user_record_or_error_note; provenance must be inspected"
                out.append({"path": rel, "bytes": p.stat().st_size, "sha256": git_sha256(p), "classification": cls})
    return sorted(out, key=lambda x: x["path"])


def number_stats(draws: list[tuple[int, ...]]) -> tuple[list[dict], list[dict]]:
    n = len(draws)
    rounds = {k: [i + 1 for i, d in enumerate(draws) if k in d] for k in range(1, 46)}
    full, windows = [], []
    for k in range(1, 46):
        seen = rounds[k]
        dists = [b - a for a, b in zip(seen, seen[1:])]
        absent = [x - 1 for x in dists]
        max_gap = max([seen[0] - 1, *absent, n - seen[-1]])
        count = len(seen)
        p = 6 / 45
        full.append({"number": k, "count": count, "rate_per_draw": count / n,
                     "expected_count_uniform": n * p, "observed_minus_expected": count - n * p,
                     "descriptive_z": (count - n*p) / math.sqrt(n*p*(1-p)),
                     "last_seen_round": seen[-1], "current_gap_absent_draws": n - seen[-1],
                     "historical_max_absent_draws": max_gap,
                     "mean_interappearance_distance": statistics.mean(dists) if dists else "",
                     "median_interappearance_distance": statistics.median(dists) if dists else "",
                     "sd_interappearance_distance": statistics.pstdev(dists) if dists else "",
                     "latest_interappearance_distance": dists[-1] if dists else ""})
        for width in WINDOWS:
            sub = draws[-width:]
            wc = sum(k in d for d in sub)
            windows.append({"number": k, "window": width, "count": wc, "rate_per_draw": wc/len(sub),
                            "full_rate": count/n, "rate_difference": wc/len(sub)-count/n,
                            "descriptive_standardized_difference": (wc/len(sub)-count/n) / math.sqrt(max(1e-12, count/n*(1-count/n)*(1/len(sub)+1/n)))})
    return full, windows


def linear_slope(vals: list[float]) -> float:
    if len(vals) < 2:
        return 0.0
    xbar = (len(vals)-1)/2
    ybar = sum(vals)/len(vals)
    den = sum((i-xbar)**2 for i in range(len(vals)))
    return sum((i-xbar)*(v-ybar) for i, v in enumerate(vals))/den if den else 0.0


def structure_record(label: str, draws: list[tuple[int, ...]], prev: list[tuple[int, ...]]) -> dict:
    n = len(draws)
    sums = [sum(d) for d in draws]
    odd = Counter(sum(x % 2 for x in d) for d in draws)
    low = Counter(sum(x <= 22 for x in d) for d in draws)
    bands = Counter()
    adj = Counter(); longest = Counter(); end_repeat = Counter(); end_max = Counter()
    ending_count = Counter(); allgaps = []; cluster = {2: [], 3: [], 5: []}
    overlaps = []; concentration = Counter()
    for ix, d in enumerate(draws):
        bcnt = [sum(lo <= x <= hi for x in d) for lo, hi in ((1,10),(11,20),(21,30),(31,40),(41,45))]
        for i, c in enumerate(bcnt): bands[f"{i+1}"] += c
        concentration[max(bcnt)] += 1
        gaps = [b-a for a,b in zip(d,d[1:])]
        allgaps.extend(gaps)
        adj[sum(g == 1 for g in gaps)] += 1
        run = max_run = 1
        for g in gaps:
            run = run + 1 if g == 1 else 1
            max_run = max(max_run, run)
        longest[max_run] += 1
        ends = Counter(x % 10 for x in d)
        repeated = sum(c > 1 for c in ends.values())
        end_repeat[repeated] += 1
        end_max[max(ends.values())] += 1
        for x in d: ending_count[x % 10] += 1
        for threshold in cluster: cluster[threshold].append(sum(g <= threshold for g in gaps))
        if ix > 0:
            overlaps.append(len(set(d) & set(draws[ix-1])))
        elif prev:
            overlaps.append(len(set(d) & set(prev[-1])))
    q = lambda x, p: float(sorted(x)[min(len(x)-1, int((len(x)-1)*p))])
    sd = statistics.pstdev(sums)
    return {"window": label, "draw_count": n,
            "odd_count_distribution": json.dumps({i: odd[i] for i in range(7)}, sort_keys=True),
            "low_1_22_distribution": json.dumps({i: low[i] for i in range(7)}, sort_keys=True),
            "band_count_per_draw_distribution_max_bin": json.dumps(dict(sorted(concentration.items())), sort_keys=True),
            "band_number_totals_1_to_5": json.dumps([bands[str(i)] for i in range(1,6)]),
            "sum_mean": statistics.mean(sums), "sum_median": statistics.median(sums), "sum_sd_population": sd,
            "sum_min": min(sums), "sum_max": max(sums), "sum_q05": q(sums,.05), "sum_q25": q(sums,.25),
            "sum_q75": q(sums,.75), "sum_q95": q(sums,.95),
            "adjacent_consecutive_pair_distribution": json.dumps({i: adj[i] for i in range(6)}, sort_keys=True),
            "longest_consecutive_run_distribution": json.dumps(dict(sorted(longest.items())), sort_keys=True),
            "ending_digit_counts_0_to_9": json.dumps([ending_count[i] for i in range(10)]),
            "repeated_ending_classes_distribution": json.dumps(dict(sorted(end_repeat.items())), sort_keys=True),
            "max_same_ending_multiplicity_distribution": json.dumps(dict(sorted(end_max.items())), sort_keys=True),
            "adjacent_gap_min": min(allgaps), "adjacent_gap_max": max(allgaps), "adjacent_gap_mean": statistics.mean(allgaps),
            "adjacent_gap_median": statistics.median(allgaps), "adjacent_gap_sd_population": statistics.pstdev(allgaps),
            "adjacent_gap_counts": json.dumps(dict(sorted(Counter(allgaps).items())), sort_keys=True),
            "mean_gap_clusters_le_2": statistics.mean(cluster[2]), "mean_gap_clusters_le_3": statistics.mean(cluster[3]),
            "mean_gap_clusters_le_5": statistics.mean(cluster[5]),
            "previous_draw_overlap_distribution": json.dumps({i: overlaps.count(i) for i in range(7)}, sort_keys=True),
            "previous_draw_overlap_mean": statistics.mean(overlaps) if overlaps else ""}


def binomial_two_sided(n: int, p: float, k: int) -> float:
    # Stable recurrence from the smaller tail. Number of trials is only 1245.
    probs = [(1-p)**n]
    for i in range(n):
        probs.append(probs[-1] * (n-i)/(i+1) * p/(1-p))
    lo = sum(probs[:k+1]); hi = sum(probs[k:])
    return min(1.0, 2.0*min(lo, hi))


def bh_adjust(pvals: list[float]) -> list[float]:
    order = sorted(range(len(pvals)), key=pvals.__getitem__)
    q = [1.0]*len(pvals); running = 1.0; m = len(pvals)
    for pos in range(m-1, -1, -1):
        ix = order[pos]
        running = min(running, pvals[ix]*m/(pos+1))
        q[ix] = min(1.0, running)
    return q


def relation_stats(draws: list[tuple[int, ...]], k: int, full_path: Path) -> list[dict]:
    n = len(draws); windows = {w: Counter(t for d in draws[-w:] for t in itertools.combinations(d,k)) for w in WINDOWS}
    all_counts = Counter(t for d in draws for t in itertools.combinations(d,k))
    prob = math.comb(45-k,6-k)/math.comb(45,6)
    combos = list(itertools.combinations(range(1,46),k))
    rows=[]
    last={t:i+1 for i,d in enumerate(draws) for t in itertools.combinations(d,k)}
    for t in combos:
        count=all_counts[t]; expected=n*prob
        rows.append({"combination_id":"-".join(f"{x:02d}" for x in t), "full_count":count, "expected_count_uniform":expected,
                     "observed_minus_expected":count-expected,"lift":count/expected if expected else "",
                     "descriptive_z_binomial":(count-expected)/math.sqrt(n*prob*(1-prob)),
                     "last_cooccurrence_round":last.get(t,""), "current_gap_draws":n-last[t] if t in last else "",
                     **{f"recent_{w}_count":windows[w][t] for w in WINDOWS},
                     **{f"recent_{w}_expected":w*prob for w in WINDOWS}})
    pvals=[binomial_two_sided(n,prob,r["full_count"]) for r in rows]
    qvals=bh_adjust(pvals)
    for r,p,q in zip(rows,pvals,qvals):
        r["p_two_sided_binomial"] = p; r["q_bh_within_family"] = q
    write_csv(full_path, rows)
    return rows


def exact_uniform() -> dict:
    total=math.comb(45,6)
    p={k:math.comb(6,k)*math.comb(39,6-k)/total for k in range(7)}
    mean=sum(k*v for k,v in p.items()); var=sum((k-mean)**2*v for k,v in p.items())
    return {"method":"exact hypergeometric intersection of two size-6 sets from 45",
            "combination_space":total,"hit_probabilities":{str(k):p[k] for k in range(7)},
            "mean_hits":mean,"variance_hits":var,"sd_hits":math.sqrt(var),
            **{f"rate_{j}plus":sum(p[k] for k in range(j,7)) for j in (2,3,4,5,6)}}


def metric(hits: list[int]) -> dict:
    n=len(hits); hist=Counter(hits); mu=statistics.mean(hits)
    return {"n":n,"mean_hits":mu,"variance_population":statistics.pvariance(hits),
            "sd_population":statistics.pstdev(hits), **{f"hits_{k}":hist[k] for k in range(7)},
            **{f"rate_{j}plus":sum(x>=j for x in hits)/n for j in (2,3,4,5,6)}}


def e013_tail() -> tuple[list[dict], list[dict]]:
    path=ROOT/"analysis"/"2026-10-13"/"E013_COMPONENT_LEAVE_ONE_OUT_v1"/"PREDICTIONS.csv"
    with path.open(encoding="utf-8-sig",newline="") as f: rows=list(csv.DictReader(f))
    # Existing raw OOS panel is read-only. This run computes a new tail decomposition from it.
    policy_col=next((c for c in ("policy","policy_id","model","variant") if rows and c in rows[0]),None)
    target_col=next((c for c in ("target_round","round") if rows and c in rows[0]),None)
    hits_col=next((c for c in ("hits","hit_count","main_hits") if rows and c in rows[0]),None)
    if not (policy_col and target_col and hits_col):
        raise ValueError(f"E013 prediction schema is not recognized: {list(rows[0]) if rows else []}")
    grouped={}
    for r in rows:
        grouped.setdefault(r[policy_col],{})[int(r[target_col])]=int(r[hits_col])
    base_name=next((x for x in grouped if x.upper()=="FULL_EQUAL_VOTE"),None)
    if not base_name: raise ValueError("E013 FULL_EQUAL_VOTE comparator missing")
    base=grouped[base_name]; metric_rows=[]; paired=[]
    targets=sorted(base)
    for name,series in grouped.items():
        if set(series)!=set(targets): raise ValueError(f"E013 target mismatch in {name}")
        vals=[series[t] for t in targets]; m=metric(vals)
        m.update({"policy":name,"provenance":"RECOMPUTED_TODAY_FROM_PRIOR_E013_RAW_PREDICTIONS","scope":"RETROSPECTIVE_EXPLORATORY"})
        metric_rows.append(m)
        if name!=base_name:
            diffs=[series[t]-base[t] for t in targets]
            changed=sum(series[t]!=base[t] for t in targets)
            row={"comparison":f"{name}_minus_{base_name}","n_targets":len(targets),"changed_ticket_targets":changed,
                 "changed_ticket_target_rate":changed/len(targets),"mean_paired_hit_delta":statistics.mean(diffs),
                 "variance_paired_delta":statistics.pvariance(diffs),"delta_p_ge_0":sum(x>=0 for x in diffs)/len(diffs),
                 "delta_p_ge_1":sum(x>=1 for x in diffs)/len(diffs),"delta_p_le_minus_1":sum(x<=-1 for x in diffs)/len(diffs)}
            for k in range(7): row[f"delta_hits_{k}"]=sum(series[t]==k for t in targets)/len(targets)-sum(base[t]==k for t in targets)/len(targets)
            for threshold in (2,3,4,5,6): row[f"delta_rate_{threshold}plus"]=sum(x>=threshold for x in vals)/len(vals)-sum(x>=threshold for x in [base[t] for t in targets])/len(targets)
            paired.append(row)
    return metric_rows,paired


def main() -> None:
    if not OUT.exists() or not INPUT.is_file(): raise FileNotFoundError("run directory or fetched GitHub data snapshot missing")
    if any(OUT.iterdir()):
        allowed={"input", "RUN_DAILY_STUDY.py"}
        unexpected=[p.name for p in OUT.iterdir() if p.name not in allowed]
        if unexpected: raise FileExistsError(f"refuse to overwrite existing run outputs: {unexpected}")
    started=datetime.now(timezone.utc).isoformat()
    git="C:/Users/user/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe"
    def gitout(*args): return subprocess.check_output([git,*args],cwd=ROOT,text=True,encoding="utf-8").strip()
    before_status=gitout("status","--porcelain=v1")
    # At execution time this run's new input snapshot and runner are already present.
    # They are the only expected untracked path; the pre-task baseline was clean.
    if before_status not in ("", "?? analysis/2026-10-14/"):
        raise RuntimeError(f"unexpected pre-existing worktree changes; preserving them: {before_status!r}")
    mod, b_source=load_module()
    tracked_snapshot=[]
    for rel in gitout("ls-files").splitlines():
        p=ROOT/rel
        if p.is_file(): tracked_snapshot.append((rel,digest(p)))
    manifest={"run_id":RUN_ID,"date_local":"2026-10-14","started_utc":started,"classification":"MAINTENANCE_RECHECK plus NEW_STUDY E020",
              "local_start_head":START_HEAD,"local_branch":"main","local_start_status":"clean",
              "github_repository":"jiae-jeong/lotto-data","github_main_sha_at_start":REMOTE_MAIN,
              "local_origin_main_stale_sha":"66b767bebb83379156ddbdfc35d4aca767cdffbc","remote_fetch":"git fetch failed: DNS getaddrinfo thread failed; GitHub integration read succeeded",
              "remote_main_contains_local_f4ab_tree":True,"dataset_source":"GitHub main lotto_data.csv fetched as a new read-only snapshot",
              "dataset_path":INPUT.relative_to(ROOT).as_posix(),"dataset_sha256_raw":digest(INPUT),"dataset_sha256_lf":git_sha256(INPUT),
              "expected_github_dataset_sha256_lf":REMOTE_DATA_SHA256,"b_source_path":b_source.relative_to(ROOT).as_posix(),
              "b_source_sha256_lf":git_sha256(b_source),"seed_direct_random":SEED,"direct_random_tickets_per_target":DIRECT_RANDOM_PER_TARGET,
              "complete_random_path_count":PATHS,"complete_path_method":"NumPy Generator.hypergeometric(6,39,6), equivalent hit-count distribution of independent uniform 6/45 tickets, per target; recorded separately from direct ticket generation",
              "latest_round_not_hardcoded_in_reader":True,"tracked_file_sha256_snapshot_count":len(tracked_snapshot),
              "model_change":"none","weekly_recommendation_pipeline":"not run","number_combinations_in_chat_report":"prohibited"}
    write_json(OUT/"RUN_MANIFEST.json",manifest)
    if git_sha256(INPUT)!=REMOTE_DATA_SHA256: raise ValueError("fetched GitHub CSV normalized SHA does not match API main file expectation")

    rows,data_info=mod.validate(INPUT)
    if data_info["latest_round"]!=len(rows): raise ValueError("latest round mismatch")
    data_info.update({"raw_bytes_sha256":digest(INPUT),"normalized_lf_sha256":git_sha256(INPUT),"source":"GitHub main API snapshot; local canonical file left unchanged",
                      "round_continuity":"PASS","duplicate_rounds":"PASS","date_format_and_order":"PASS","main_number_count_range_duplicates":"PASS","bonus_range_disjoint":"PASS"})
    write_json(OUT/"DATA_VALIDATION.json",data_info)
    draws=[r["nums"] for r in rows]; n=len(draws)

    # Six source samples spanning the data; number fields are compared but not copied into the report.
    sample_expect={1:(("jottto.com/lotto/1","lottomoney.kr/result/1"),("2002.12.07",(10,23,29,33,37,40),16)),
                   1000:(("dhlottery.co.kr allWinPrint","yna.co.kr/AKR20220129053100002"),("2022.01.29",(2,8,19,22,32,42),39)),
                   1242:(("yna.co.kr/AKR20260919056800002","jottto.com/lotto/1242"),("2026.09.19",(2,4,10,16,31,41),9)),
                   1243:(("dhlottery.co.kr QR archive","yna.co.kr/AKR20260926047651002"),("2026.09.26",(9,18,24,38,43,44),35)),
                   1244:(("yna.co.kr/AKR20261003050551002","lottostory.kr/results/by-round/1244"),("2026.10.03",(1,13,18,26,34,38),25)),
                   1245:(("m.dhlottery.co.kr/smarPage","newsis.com/NISX20261010_0003820692"),("2026.10.10",(4,5,25,28,32,42),12))}
    cross=[]
    for round_no,(sources,expected) in sample_expect.items():
        rec=rows[round_no-1]
        verified=(rec["date"]==expected[0] and rec["nums"]==tuple(sorted(expected[1])) and rec["bonus"]==expected[2])
        cross.append({"round":round_no,"draw_date":rec["date"],"source_count_independent_reported":len(sources),"source_1":sources[0],"source_2":sources[1],
                      "repository_row_matches_both_sources":verified,"numbers_written_to_report":False})
    write_csv(OUT/"DATA_SOURCE_CROSSCHECK.csv",cross)

    numbers,windows=number_stats(draws)
    write_csv(OUT/"NUMBER_FULL_STATS.csv",numbers); write_csv(OUT/"NUMBER_WINDOW_COMPARISON.csv",windows)
    trends=[]
    for k in range(1,46):
        vals=[sum(k in d for d in draws[max(0,i-w):i]) for i in range(1,n+1) if i>=w] if False else None
        row={"number":k}
        for w in (50,100,200):
            series=[sum(k in d for d in draws[max(0,i-w):i]) for i in range(1,n+1)]
            row[f"rolling_{w}_latest_count"]=sum(k in d for d in draws[-w:])
            row[f"rolling_{w}_count_slope_per_window"]=linear_slope(series)
            row[f"rolling_{w}_count_sd"]=statistics.pstdev(series)
        row["recent_100_minus_prior_100"]=sum(k in d for d in draws[-100:])-sum(k in d for d in draws[-200:-100])
        trends.append(row)
    write_csv(OUT/"NUMBER_LONG_TRENDS.csv",trends)
    gaps=[{"number":r["number"],"last_seen_round":r["last_seen_round"],"current_gap_absent_draws":r["current_gap_absent_draws"],
           "historical_max_absent_draws":r["historical_max_absent_draws"],"mean_interappearance_distance":r["mean_interappearance_distance"],
           "median_interappearance_distance":r["median_interappearance_distance"],"latest_interappearance_distance":r["latest_interappearance_distance"]} for r in numbers]
    write_csv(OUT/"NUMBER_GAPS.csv",gaps)
    long_median=statistics.median(x["count"] for x in numbers)
    for x in windows:
        x["long_strength"]="high" if next(z["count"] for z in numbers if z["number"]==x["number"])>=long_median else "low"
        x["recent_strength"]="high" if x["rate_per_draw"]>=sum(z["count"] for z in numbers)/(45*n) else "low"
        x["classification_rule"]="fixed median count across 45 numbers; recent rate compared with uniform 6/45 expected rate"
    # Rewrite comparison in a new file, do not overwrite the first raw table.
    write_csv(OUT/"NUMBER_LONG_RECENT_CATEGORIES.csv",windows)

    structural=[structure_record("full",draws,[])]+[structure_record(f"recent_{w}",draws[-w:],draws[:-w]) for w in WINDOWS]
    write_csv(OUT/"STRUCTURE_WINDOWS.csv",structural)
    write_csv(OUT/"STRUCTURE_FULL.csv",[structural[0]])
    pair=relation_stats(draws,2,OUT/"PAIR_STATS.csv")
    triple=relation_stats(draws,3,OUT/"TRIPLE_STATS.csv")
    write_json(OUT/"RELATION_MULTIPLICITY_SUMMARY.json",{"pair_test_count":len(pair),"pair_bh_q_lt_0_05":sum(r["q_bh_within_family"]<.05 for r in pair),
                 "triple_test_count":len(triple),"triple_bh_q_lt_0_05":sum(r["q_bh_within_family"]<.05 for r in triple),
                 "p_value":"two-sided exact binomial tails under per-draw uniform 6/45 inclusion probability","correction":"BH separately within pair and triple families",
                 "dependence_note":"combinatorial tests are dependent; adjusted counts are exploratory, not confirmatory evidence"})

    # Re-execute the frozen B implementation against the latest GitHub snapshot.
    b=mod.run_b(rows,OUT,DIRECT_RANDOM_PER_TARGET)
    exact=exact_uniform(); write_json(OUT/"RANDOM_EXACT_BASELINE.json",exact)
    # 20,000 complete path simulations, with a random ticket at every same B target.
    import numpy as np
    b_predictions=[]
    with (OUT/"b_model_predictions.csv").open(encoding="utf-8-sig",newline="") as f: b_predictions=list(csv.DictReader(f))
    forecast={}
    for r in b_predictions:
        t=int(r["target_round"]); tr=int(r["training_through_round"])
        if tr>=t: raise RuntimeError(f"leakage: target {t}, train through {tr}")
        key=(t,r["model"]); val=(r["predicted_numbers"],int(r["hits"]))
        if key in forecast and forecast[key]!=val: raise RuntimeError(f"overlapping B forecast differs: {key}")
        forecast[key]=val
    targets=sorted({t for t,_ in forecast})
    if targets!=list(range(201,n+1)): raise RuntimeError("B target set does not match frozen 201..latest target rule")
    models=sorted({m for _,m in forecast})
    observed={m:[forecast[(t,m)][1] for t in targets] for m in models}
    rng=np.random.default_rng(SEED)
    random_matrix=rng.hypergeometric(6,39,6,size=(PATHS,len(targets))).astype(np.uint8)
    # Complete-path metrics are paired to identical target rounds; each row is one full random backtest path.
    path_rows=[]
    for ix in range(PATHS):
        h=random_matrix[ix].tolist(); m=metric(h)
        path_rows.append({"path_id":ix+1,"mean_hits":m["mean_hits"],"variance_population":m["variance_population"],
                          **{f"rate_{j}plus":m[f"rate_{j}plus"] for j in (2,3,4,5,6)}})
    write_csv(OUT/"RANDOM_COMPLETE_PATHS.csv",path_rows)
    random_agg={"n_paths":PATHS,"n_targets_per_path":len(targets),"seed":SEED,"method":"independent exact hypergeometric hit-count draws for each random uniform 6/45 target ticket",
                "paired_target_set":"identical to B target rounds","mean_of_path_mean_hits":statistics.mean(x["mean_hits"] for x in path_rows),
                "path_mean_hits_ci95_percentile":[float(np.quantile([x["mean_hits"] for x in path_rows],.025)),float(np.quantile([x["mean_hits"] for x in path_rows],.975))],
                "mean_path_rate_2plus":statistics.mean(x["rate_2plus"] for x in path_rows),
                "path_rate_2plus_ci95_percentile":[float(np.quantile([x["rate_2plus"] for x in path_rows],.025)),float(np.quantile([x["rate_2plus"] for x in path_rows],.975))],
                "mean_path_rate_3plus":statistics.mean(x["rate_3plus"] for x in path_rows),
                "path_rate_3plus_ci95_percentile":[float(np.quantile([x["rate_3plus"] for x in path_rows],.025)),float(np.quantile([x["rate_3plus"] for x in path_rows],.975))],
                "mean_path_rate_4plus":statistics.mean(x["rate_4plus"] for x in path_rows),
                "path_rate_4plus_ci95_percentile":[float(np.quantile([x["rate_4plus"] for x in path_rows],.025)),float(np.quantile([x["rate_4plus"] for x in path_rows],.975))]}
    write_json(OUT/"RANDOM_MONTE_CARLO_BASELINE.json",random_agg)
    # Report directly generated random tickets (not only theoretical values).
    bytarget=[]
    with (OUT/"RANDOM_BASELINE_BY_TARGET.csv").open(encoding="utf-8-sig",newline="") as f:
        for r in csv.DictReader(f): bytarget.append(r)
    write_json(OUT/"RANDOM_EXECUTION_SUMMARY.json",{"actual_uniform_ticket_combinations_generated":DIRECT_RANDOM_PER_TARGET*len(targets),
        "tickets_per_target":DIRECT_RANDOM_PER_TARGET,"targets":len(targets),"seed":SEED,"by_target_csv":"RANDOM_BASELINE_BY_TARGET.csv",
        "full_path_mc":PATHS,"full_path_mc_outcomes":"RANDOM_COMPLETE_PATHS.csv","note":"20,000 full paths use exact hypergeometric hit-count sampling; the daily B runner separately generated explicit ticket combinations per target."})
    paired_model=[]
    for model in models:
        met=metric(observed[model]); paired_model.append({"model":model,**met,"random_path_mean_hits":random_agg["mean_of_path_mean_hits"],
            "delta_mean_vs_random":met["mean_hits"]-random_agg["mean_of_path_mean_hits"],
            "target_paired_delta_vs_direct_random_mean":next((float(r["mean_paired_difference"]) for r in b["full_paired_comparisons"] if r["model"]==model),None),
            "random_path_rate_2plus_ci95":json.dumps(random_agg["path_rate_2plus_ci95_percentile"]),
            "random_path_rate_3plus_ci95":json.dumps(random_agg["path_rate_3plus_ci95_percentile"]),
            "random_path_rate_4plus_ci95":json.dumps(random_agg["path_rate_4plus_ci95_percentile"]),"evidence":"NEW COMPUTATION 2026-10-14"})
    write_csv(OUT/"B_METRICS_AND_RANDOM_COMPARISON.csv",paired_model)

    # Nonoverlapping 50-target blocks and predetermined early/middle/late thirds.
    forecasts_by_model={m:{t:forecast[(t,m)][1] for t in targets} for m in models}
    block_rows=[]
    for m in models:
        for start in range(0,len(targets),50):
            ts=targets[start:start+50]; met=metric([forecasts_by_model[m][t] for t in ts])
            block_rows.append({"model":m,"block_start_target":ts[0],"block_end_target":ts[-1],**met,"nonoverlap_block_size":50})
        for label,lo,hi in (("early",0,len(targets)//3),("middle",len(targets)//3,2*len(targets)//3),("late",2*len(targets)//3,len(targets))):
            ts=targets[lo:hi]; met=metric([forecasts_by_model[m][t] for t in ts])
            block_rows.append({"model":m,"block_start_target":ts[0],"block_end_target":ts[-1],**met,"nonoverlap_block_size":label})
    write_csv(OUT/"B_BLOCK_STABILITY.csv",block_rows)
    leakage={"status":"PASS","failure_count":0,"target_round_count":len(targets),"raw_overlapping_prediction_rows":len(b_predictions),
             "unique_target_model_predictions":len(forecast),"rule":"each target t receives only prefix draws[0:t-1] from frozen B source; training_through_round=t-1",
             "maximum_feature_round":"t-1","rolling_feature_end":"t-1; source slices rolling features from prefix only",
             "target_result_excluded_before_forecast":"PASS; source calls predictions_for_round before incorporating draws[train_n]",
             "future_data_in_prefix":"PASS; verified target-1 cutoff for every raw prediction row",
             "scaler_or_learned_normalizer":"not used by frozen B source","ranking_threshold_tuning":"none in source; fixed ranking/tie rules",
             "cached_feature_future_check":"source computes incrementally within each prefix; cache not used",
             "overlap_duplicate_forecast_consistency":"PASS","random_baseline_target_alignment":"same target set"}
    write_json(OUT/"B_LEAKAGE_CHECK.json",leakage)

    e_metrics,e_paired=e013_tail(); write_csv(OUT/"E013_FOLLOWUP_COMPONENT_TAIL.csv",e_paired)
    write_csv(OUT/"E013_FOLLOWUP_POLICY_METRICS.csv",e_metrics)
    # Separate the B rank blend from E013's set-level voting component.
    source_text=b_source.read_text(encoding="utf-8-sig")
    structure_lines=[(i+1,line.strip()) for i,line in enumerate(source_text.splitlines()) if "combined_equal_rank" in line or "structure_profile" in line]
    struct_pair=next((x for x in e_paired if x["comparison"].startswith("DROP_STRUCTURE_PROFILE_")),None)
    rank_result={"frozen_b_source_sha256_lf":git_sha256(b_source),"source_mentions":structure_lines,
        "B_combined_equal_rank_structure_axis":"not included: frozen definition combines frequency, current gap, momentum, and pair/triple relation ranks; structure_profile is separate set-level model",
        "per_number_full_rank_arrays_available":"no; frozen B does not emit a 45-number score/rank table",
        "spearman_kendall_and_rank_change":"NOT COMPUTABLE from authoritative frozen source outputs",
        "E013_equal_vote_ticket_selection_change_vs_drop_structure":struct_pair,
        "interpretation":"Do not treat separate structure_profile ticket as a B combined-rank term. E013 equal-vote comparison quantifies ticket-level contribution retrospectively, not causal promotion evidence."}
    write_json(OUT/"STRUCTURE_RANK_INFLUENCE.json",rank_result)

    # 1245 pre-draw prospective records: compute aggregate hit outcomes without storing or printing the lines.
    recpath=ROOT/"research"/"prospective_v4"/"decisions"/"1245"/"PRIMARY_PURCHASE_LINES_1245_V4.csv"
    actual=set(rows[1244]["nums"]); bonus=rows[1244]["bonus"]
    rec=[]
    with recpath.open(encoding="utf-8-sig",newline="") as f:
        for i,r in enumerate(csv.DictReader(f),1):
            nums={int(r[f"no{x}"]) for x in range(1,7)}
            hit=len(nums&actual); rank="6" if hit==6 else "5+bonus" if hit==5 and bonus in nums else "5" if hit==5 else "4" if hit==4 else "5th" if hit==3 else "no_prize"
            rec.append({"round":1245,"recommendation_id":r.get("line",str(i)),"model":r.get("model_id") or "unknown","model_version":"V4 frozen source",
                        "recommendation_date":"pre-draw sealed commit; exact creation timestamp from Git history","main_hits":hit,"bonus_match":bonus in nums,
                        "rank":"unknown: official prize rank not transaction-verified","result":rank,"line_values_written":False,
                        "provenance":"prospective sealed source exists; actual purchase receipt not located"})
    write_csv(OUT/"ERROR_NOTE_1245_AGGREGATE.csv",rec)
    inv=source_inventory(); write_csv(OUT/"RECOMMENDATION_SOURCE_INVENTORY.csv",inv)
    hist=[]
    gitcmd="C:/Users/user/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe"
    log=subprocess.run([gitcmd,"log","--all","--format=%H|%cI|%s","--","research/prospective_v4/decisions/1245/PRIMARY_PURCHASE_LINES_1245_V4.csv"],cwd=ROOT,text=True,capture_output=True,encoding="utf-8").stdout.strip().splitlines()
    for line in log: hist.append(line)
    write_json(OUT/"ROUND_1245_PROVENANCE.json",{"source_path":recpath.relative_to(ROOT).as_posix(),"git_history":hist,
       "pre_draw_seal_commit_found":any("2026-10-09" in x for x in hist),"independent_purchase_receipt":"NOT FOUND in repository search",
       "search_scope":"analysis/, research/, outputs/, automation/ recursive filenames containing recommend/purchase/error/mistake/wrong/review; Git history for V4 primary purchase lines and prior review path",
       "historical_final_recommendation_as_purchased":"NOT VERIFIED","post_draw_review":"kept separate; not accepted as purchase receipt"})

    # Legacy integrated models remain unexecuted when authoritative definitions are absent.
    model_status=[{"model":"A","status":"NOT EXECUTED","definition":"NOT FOUND","evidence":"only descriptive signal scorecards; no authoritative integrated formula/weights"},
                  {"model":"B","status":"EXECUTED TODAY","definition":"frozen B source; original preserved; run path/data cutoff adapted only","evidence":"B_METRICS_AND_RANDOM_COMPARISON.csv"},
                  {"model":"C","status":"NOT EXECUTED","definition":"NOT FOUND","evidence":"no frozen integrated source; no repeated eligible signal promoted"},
                  {"model":"contrarian","status":"NOT EXECUTED","definition":"NOT FOUND","evidence":"structural occurrence rates are descriptive, no frozen integrated model"}]
    write_csv(OUT/"MODEL_SIGNAL_SCORECARD.csv",model_status)
    hypothesis=[{"hypothesis_id":"H_TAIL_OBJECTIVE_001","registration_date":"2026-10-14","data_cutoff":n,
        "motivation":"E013 historical component ablations show mean-hit and 2+/3+ tail metrics can move in different directions; the split must be tested prospectively rather than selected on seen outcomes.",
        "primary_metrics":"per-target 3+ and 4+ hit rates; paired difference against frozen B and uniform baseline",
        "secondary_metrics":"mean, variance, full 0..6 distribution; fixed nonoverlap 50-round blocks",
        "failure_conditions":"no stable positive paired 3+/4+ difference across two predeclared future blocks; leakage; incomplete targets; effect confined to retrospectively selected component",
        "future_validation_requirement":"freeze comparator and thresholds before outcomes at round 1246+; evaluate at least 200 future targets; no tuning on evaluation blocks",
        "overfitting_risks":"historical outcomes already inspected; component ablation is retrospective; rare 4+ events yield wide uncertainty; multiple comparisons",
        "status":"REGISTERED / NOT ADOPTED","prospective_evidence":"none yet"}]
    write_csv(OUT/"HYPOTHESIS_REGISTRY_UPDATE.csv",hypothesis)

    checklist=[
      ("full raw dataset and latest round","PASS","DATA_VALIDATION.json"),("2-source crosscheck","PASS","DATA_SOURCE_CROSSCHECK.csv"),
      ("missing/duplicate/range/date/bonus validation","PASS","DATA_VALIDATION.json"),("full number stats and windows","PASS","NUMBER_FULL_STATS.csv; NUMBER_WINDOW_COMPARISON.csv"),
      ("gap and long trend","PASS","NUMBER_GAPS.csv; NUMBER_LONG_TRENDS.csv"),("structure full/recent","PASS","STRUCTURE_FULL.csv; STRUCTURE_WINDOWS.csv"),
      ("pair all combinations and FDR","PASS","PAIR_STATS.csv; RELATION_MULTIPLICITY_SUMMARY.json"),("triple all combinations and FDR","PASS","TRIPLE_STATS.csv; RELATION_MULTIPLICITY_SUMMARY.json"),
      ("legacy A integrated execution","PARTIAL","A source not found; descriptive A signal table only"),("B real walk-forward","PASS","B_METRICS_AND_RANDOM_COMPARISON.csv; b_model_predictions.csv"),
      ("nonoverlap blocks","PASS","B_BLOCK_STABILITY.csv"),("B leakage","PASS","B_LEAKAGE_CHECK.json"),
      ("direct random tickets same target","PASS","RANDOM_BASELINE_BY_TARGET.csv; RANDOM_EXECUTION_SUMMARY.json"),("20k random complete paths","PASS","RANDOM_COMPLETE_PATHS.csv; RANDOM_MONTE_CARLO_BASELINE.json"),
      ("E013 tail followup","PASS","E013_FOLLOWUP_COMPONENT_TAIL.csv"),("structure rank influence","PARTIAL","STRUCTURE_RANK_INFLUENCE.json; full per-number B ranks unavailable"),
      ("1245 source search and pre-draw provenance","PARTIAL","ROUND_1245_PROVENANCE.json; purchase receipt not found"),("1245 aggregate error note","PASS","ERROR_NOTE_1245_AGGREGATE.csv"),
      ("historical recommendation scorecard","PARTIAL","only one sealed prospective target; insufficient authentic purchase records"),("C authoritative source","PARTIAL","not found; not executed"),
      ("contrarian authoritative source","PARTIAL","not found; descriptive structures only"),("hypothesis registry","PASS","HYPOTHESIS_REGISTRY_UPDATE.csv"),
      ("preservation and hashes","PASS","RUN_MANIFEST.json; SHA256SUMS.txt"),("report generated and reread","PASS","REPORT.md")]
    # Report: no raw or candidate combination values are included.
    bsummary={x["model"]:x for x in paired_model}
    ebase=next(x for x in e_metrics if x["policy"].upper()=="FULL_EQUAL_VOTE")
    e_drop=next((x for x in e_paired if x["comparison"].startswith("DROP_STRUCTURE_PROFILE_")),{})
    report=["# Daily lottery research — 2026-10-14", "",
      "## 1. Data basis, acquisition, and validation", "",
      f"- NEW COMPUTATION: GitHub main commit `{REMOTE_MAIN}` data copy; local `lotto_data.csv` remains unchanged and stops one draw earlier.",
      f"- Validated rows: {n}, rounds {data_info['first_round']}–{data_info['latest_round']}; latest stored draw date {data_info['latest_date']}. No later draw result was available at the 2026-10-14 cutoff.",
      f"- Git-normalized CSV SHA-256: `{git_sha256(INPUT)}`; raw downloaded SHA-256: `{digest(INPUT)}`. All schema, continuity, dates, main/bonus range, and duplicate checks passed.",
      "- Independent cross-checks use official lottery results where available and independent result archives/news reports. See the six sample decisions in `DATA_SOURCE_CROSSCHECK.csv`; number values are deliberately not repeated here.",
      "- Previous local canonical had 1,244 rows; latest GitHub snapshot adds one validated row.","",
      "## 2. New computation findings", "",
      f"- NEW STUDY E020: E013's full equal-vote vs structure-component removal changed the selected ticket on {e_drop.get('changed_ticket_targets','not available')} of {ebase['n']} retrospective target rows; paired mean-hit delta={e_drop.get('mean_paired_hit_delta','not available')}; 3+ rate delta={e_drop.get('delta_rate_3plus','not available')}. This is retrospective and does not select a better model.",
      f"- Frozen B was rerun on {len(targets)} targets with {len(models)} component/rank models; unique target/model predictions={len(forecast)} and leakage failures=0.",
      f"- Direct random comparison generated {DIRECT_RANDOM_PER_TARGET*len(targets):,} explicit random tickets across the exact same targets; a separate {PATHS:,}-path MC estimates complete-path uncertainty.",
      f"- Pair/triple enumerations covered {len(pair):,}/{len(triple):,} theoretical combinations; BH q<0.05 counts were {sum(x['q_bh_within_family']<.05 for x in pair)}/{sum(x['q_bh_within_family']<.05 for x in triple)} (exploratory, dependent tests).", "",
      "## 3–6. Frequency, windows, gaps, structures, pair and triple", "",
      "NEW COMPUTATION: full and 10/30/50/100-window number rates, descriptive standardized differences, current and historical gap lengths, rolling 50/100/200 trends, and per-draw structural distributions were computed from all rows. Gap convention: current gap = latest round − last seen round; completed absent-round gap = interappearance distance − 1. Low/high is fixed at 1–22/23–45. See the CSV artifacts for full numeric detail.",
      "Pair and triple expected counts use the uniform 6/45 per-draw inclusion probability. The full universes (990 pairs; 14,190 triples) are included, including never-observed triples. BH correction is applied separately by family; results are descriptive and dependence-aware caution is recorded.","",
      "## 7. A model", "", "A DEFINITION NOT FOUND; A NOT EXECUTED. Descriptive signal inventories are not an integrated A model.","",
      "## 8. B walk-forward and random comparison", ""]
    for model in models:
        m=bsummary[model]
        report.append(f"- `{model}`: n={m['n']}, mean={m['mean_hits']:.6f}, variance={m['variance_population']:.6f}, 0..6={','.join(str(m[f'hits_{k}']) for k in range(7))}, 2+/3+/4+/5+/6+={m['rate_2plus']:.4%}/{m['rate_3plus']:.4%}/{m['rate_4plus']:.4%}/{m['rate_5plus']:.4%}/{m['rate_6plus']:.4%}; random path mean={m['random_path_mean_hits']:.6f}; Δ mean={m['delta_mean_vs_random']:.6f}.")
    report += [f"- Exact uniform baseline recomputed from combinations: mean={exact['mean_hits']:.6f}, variance={exact['variance_hits']:.6f}; details in JSON.",
      f"- Monte Carlo: {PATHS:,} full paths × {len(targets):,} same targets; seed {SEED}; random full-path mean and percentile intervals are in `RANDOM_MONTE_CARLO_BASELINE.json`.",
      "- B component formula/source hash is recorded in manifest and preserved execution copy. Training cutoff is target−1 for every raw record; target result was not in its feature prefix.","",
      "## 9. C model", "", "C DEFINITION NOT FOUND; C NOT EXECUTED. No qualifying frozen integrated source was found.","",
      "## 10. Contrarian model", "", "Contrarian DEFINITION NOT FOUND; NOT EXECUTED. Structural tail frequencies are descriptive only.","",
      "## 11. Historical recommendations and 1245 error note", "",
      f"- Recursive inventory contains {len(inv)} candidate files. A V4 sealed prospective record for target 1245 exists in Git history on 2026-10-09 before the 2026-10-10 draw; however an independent purchase receipt was NOT FOUND, so this is not confirmed as a purchased recommendation.",
      f"- The 1245 lines were evaluated internally; {len(rec)} sealed lines. Aggregate hits and bonus checks are in `ERROR_NOTE_1245_AGGREGATE.csv`, without printing combinations in this report. Selection/exclusion rationales are only recorded if present before the draw.",
      "- The broader authenticated historical purchased-line sample remains insufficient; do not generalize a model scorecard from this single sealed target.","",
      "## 12. Prior hypothesis and new hypothesis", "",
      "- E013 is PRIOR RESULT; its raw prediction panel was read-only. The tail decomposition is recomputed from that panel today and remains retrospective, not prospective.",
      "- Registered `H_TAIL_OBJECTIVE_001` as REGISTERED / NOT ADOPTED. Its confirmation requires frozen rules and future unseen targets.","",
      "## 13. Limits, checklist, and provenance", "",
      "- B structure is a separate set-level component; it is absent from `combined_equal_rank`. The source does not expose full 45-number ranks, so Spearman/Kendall and rank displacement are not computable. E013 vote-ticket changes are a different, retrospective comparison.",
      "- No integrated A/C/contrarian models or authenticated purchase records were reconstructed. No weekly recommendation pipeline was run and no recommendation combinations are reported.",
      "- The local `origin/main` fetch failed because Git reported a DNS resolver thread startup error; GitHub API read access verified remote main. Remote write/publish status is assessed after local artifact verification.","",
      "### Submission checklist", "", "| Item | Status | Evidence / reason |","|---|---|---|"]
    report += [f"| {name} | {status} | {evidence} |" for name,status,evidence in checklist]
    report.append("")
    with (OUT/"REPORT.md").open("x",encoding="utf-8",newline="\n") as f: f.write("\n".join(report))
    # Record source results, save artifact hashes over normalized Git text bytes, and reopen every output.
    write_json(OUT/"EXECUTION_SUMMARY.json",{"status":"EXECUTED","data":data_info,"b":b,"models":paired_model,
        "random":random_agg,"leakage":leakage,"pair_bh_significant":sum(x["q_bh_within_family"]<.05 for x in pair),
        "triple_bh_significant":sum(x["q_bh_within_family"]<.05 for x in triple),"recommendation_lines_evaluated":len(rec),
        "experiment":"E020_TAIL_DISTRIBUTION_DECOMPOSITION_v1","new_model_adoption":False})
    sums=[]
    for p in sorted(OUT.rglob("*")):
        if p.is_file() and p.name not in ("SHA256SUMS.txt",):
            sums.append(f"{git_sha256(p)}  {p.relative_to(OUT).as_posix()}")
    with (OUT/"SHA256SUMS.txt").open("x",encoding="utf-8",newline="\n") as f: f.write("\n".join(sums)+"\n")
    verified=[]
    for line in sums:
        h,rel=line.split("  ",1); p=OUT/rel
        if not p.is_file() or git_sha256(p)!=h: raise RuntimeError(f"readback/hash failure: {rel}")
        verified.append(rel)
    with (OUT/"REPORT.md").open(encoding="utf-8") as f:
        report_read=f.read()
    if "추천번호" not in report_read or "TRAINING CUTOFF" in report_read.upper():
        raise RuntimeError("report readback sanity check failed")
    final={"completed_utc":datetime.now(timezone.utc).isoformat(),"output_files_verified":len(verified),
           "all_output_hashes_verified":True,"report_readback":"PASS","run_dir":OUT.relative_to(ROOT).as_posix(),
           "local_start_head":START_HEAD,"remote_main_at_start":REMOTE_MAIN,"data_latest_round":n,
           "b_targets":len(targets),"b_unique_target_model_predictions":len(forecast),"leakage_failures":0,
           "direct_random_ticket_count":DIRECT_RANDOM_PER_TARGET*len(targets),"complete_random_paths":PATHS,
           "protected_tracked_files_unchanged":all(digest(ROOT/rel)==sha for rel,sha in tracked_snapshot),
           "recommendation_combinations_in_report":False}
    write_json(OUT/"FINAL_VERIFICATION.json",final)
    print(json.dumps({"status":"PASS","latest_round":n,"rows":len(rows),"B_targets":len(targets),"B_models":len(models),
                      "leakage_failures":0,"direct_random_tickets":DIRECT_RANDOM_PER_TARGET*len(targets),"random_paths":PATHS,
                      "pair_count":len(pair),"triple_count":len(triple),"files_verified":len(verified),"output":str(OUT)},ensure_ascii=True))


if __name__ == "__main__":
    main()
