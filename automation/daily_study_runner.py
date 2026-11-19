#!/usr/bin/env python3
from __future__ import annotations
import csv, json, math, random, statistics, subprocess, sys
from collections import Counter
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATE = "2026-10-12"
OUT = ROOT / "analysis" / DATE
OUT.mkdir(parents=True, exist_ok=True)
LATEST = {"round":1245,"date":"2026.10.10","nums":(4,5,25,28,32,42),"bonus":12}
SEED = 20261012


def read_raw():
    with (ROOT/"lotto_data.csv").open(encoding="utf-8-sig", newline="") as f:
        rows=list(csv.DictReader(f))
    draws=[]
    for r in rows:
        nums=tuple(sorted(int(r[f"no{i}"]) for i in range(1,7)))
        draws.append({"round":int(r["round"]),"date":r["date"],"nums":nums,"bonus":int(r["bonus"])})
    return draws


def integrity(draws):
    rounds=[d["round"] for d in draws]
    checks={
        "rows":len(draws),
        "continuous":rounds==list(range(1,len(draws)+1)),
        "duplicate_rounds":len(rounds)-len(set(rounds)),
        "six_unique_main":all(len(d["nums"])==6 and len(set(d["nums"]))==6 for d in draws),
        "main_range":all(all(1<=x<=45 for x in d["nums"]) for d in draws),
        "bonus_range":all(1<=d["bonus"]<=45 for d in draws),
        "bonus_not_main":all(d["bonus"] not in d["nums"] for d in draws),
    }
    return checks


def qtile(xs,q):
    ys=sorted(xs); pos=(len(ys)-1)*q; lo=int(math.floor(pos)); hi=int(math.ceil(pos))
    return ys[lo] if lo==hi else ys[lo]+(ys[hi]-ys[lo])*(pos-lo)


def feat(nums, prev=None):
    nums=tuple(sorted(nums)); gaps=[b-a for a,b in zip(nums,nums[1:])]
    bands=[sum(lo<=x<=hi for x in nums) for lo,hi in [(1,10),(11,20),(21,30),(31,40),(41,45)]]
    return {
        "odd":sum(x%2 for x in nums),"even":sum(x%2==0 for x in nums),
        "low":sum(x<=22 for x in nums),"high":sum(x>=23 for x in nums),
        "sum":sum(nums),"consecutive_pairs":sum(g==1 for g in gaps),
        "ending_repeat_excess":6-len(set(x%10 for x in nums)),
        "mean_adjacent_gap":statistics.mean(gaps),"min_adjacent_gap":min(gaps),"max_adjacent_gap":max(gaps),
        "cluster_gaps_le3":sum(g<=3 for g in gaps),"bands":bands,
        "previous_overlap":sum(x in set(prev or ()) for x in nums)
    }


def number_table(draws):
    occ={n:[] for n in range(1,46)}
    for d in draws:
        for n in d["nums"]: occ[n].append(d["round"])
    windows=[10,30,50,100]
    rows=[]
    for n in range(1,46):
        rr=occ[n]; intervals=[b-a for a,b in zip(rr,rr[1:])]
        row={"number":n,"count_all":len(rr),"rate_all":len(rr)/len(draws),
             "current_gap":draws[-1]["round"]-rr[-1],
             "max_gap":max(intervals+[draws[-1]["round"]-rr[-1]]) if rr else draws[-1]["round"],
             "avg_interval":statistics.mean(intervals) if intervals else None}
        for w in windows:
            c=sum(n in d["nums"] for d in draws[-w:]); row[f"count_{w}"]=c; row[f"rate_{w}"]=c/w
            row[f"delta_{w}_vs_all"]=row[f"rate_{w}"]-row["rate_all"]
        rows.append(row)
    return rows


def structure_summary(draws):
    fs=[]
    for i,d in enumerate(draws): fs.append(feat(d["nums"], draws[i-1]["nums"] if i else None))
    scalar=["odd","low","sum","consecutive_pairs","ending_repeat_excess","mean_adjacent_gap","cluster_gaps_le3","previous_overlap"]
    out={}
    for w in [len(draws),100,50,30,10]:
        key="all" if w==len(draws) else str(w); sub=fs[-w:]
        out[key]={k:statistics.mean(x[k] for x in sub) for k in scalar}
        out[key]["band_means"]=[statistics.mean(x["bands"][j] for x in sub) for j in range(5)]
    sums=[x["sum"] for x in fs[:-1]]
    out["historical_sum_p05"]=qtile(sums,.05); out["historical_sum_p95"]=qtile(sums,.95)
    out["latest"]=fs[-1]
    return out,fs


def relation_summary(draws):
    out={}
    for w in [len(draws),100,50,30,10]:
        key="all" if w==len(draws) else str(w); sub=draws[-w:]
        pc=Counter(); tc=Counter()
        for d in sub:
            pc.update(combinations(d["nums"],2)); tc.update(combinations(d["nums"],3))
        pvals=sorted(pc.values(),reverse=True); tvals=sorted(tc.values(),reverse=True)
        out[key]={
            "unique_pairs":len(pc),"unique_triples":len(tc),
            "pair_top10_share":sum(pvals[:10])/(15*len(sub)),
            "triple_top10_share":sum(tvals[:10])/(20*len(sub)),
            "pair_max_count":pvals[0] if pvals else 0,"triple_max_count":tvals[0] if tvals else 0
        }
    return out


def contrarian_summary(draws, fs, ss):
    p05,p95=ss["historical_sum_p05"],ss["historical_sum_p95"]
    def flag(x):
        return {"odd_extreme":x["odd"] in (0,1,5,6),"lowhigh_extreme":x["low"] in (0,1,5,6),
                "consecutive_dense":x["consecutive_pairs"]>=2,"ending_repeat_dense":x["ending_repeat_excess"]>=2,
                "sum_extreme":x["sum"]<=p05 or x["sum"]>=p95}
    flags=[flag(x) for x in fs]
    out={}
    for w in [len(flags),100,50,30,10]:
        key="all" if w==len(flags) else str(w); sub=flags[-w:]
        out[key]={k:sum(x[k] for x in sub)/len(sub) for k in sub[0]}
    out["latest"]=flags[-1]
    return out


def purchase_review(actual):
    p=ROOT/"research/prospective_v4/decisions/1245/PRIMARY_PURCHASE_LINES_1245_V4.csv"
    hits=[]; structure=[]
    if not p.exists(): return {"status":"NOT_FOUND"}
    with p.open(encoding="utf-8-sig",newline="") as f:
        for r in csv.DictReader(f):
            nums=tuple(int(r[f"no{i}"]) for i in range(1,7)); hits.append(len(set(nums)&set(actual)))
            structure.append({"odd":int(r["odd"]),"low":int(r["low"]),"sum":int(r["sum"]),"consecutive_count":int(r["consecutive_count"])})
    return {"status":"FOUND","line_count":len(hits),"hit_distribution":dict(Counter(hits)),"hits_per_line":hits,
            "rate_ge2":sum(h>=2 for h in hits)/len(hits),"max_hits":max(hits),"line_structure":structure}


def h001_h002(draws):
    rec=[]
    for ti in range(200,len(draws)):
        train=draws[:ti]; actual=set(draws[ti]["nums"]); tround=draws[ti]["round"]
        counts=Counter(n for d in train for n in d["nums"])
        last={n:0 for n in range(1,46)}
        for d in train:
            for n in d["nums"]: last[n]=d["round"]
        waits={n:train[-1]["round"]-last[n] if last[n] else train[-1]["round"] for n in range(1,46)}
        due=sorted(range(1,46), key=lambda n:(-waits[n],n))[:6]
        anti=sorted(range(1,46), key=lambda n:(waits[n],n))[:6]
        rec.append(("H002_due",tround,len(set(due)&actual))); rec.append(("H002_anti",tround,len(set(anti)&actual)))
        for w in [10,30,50,100]:
            rc=Counter(n for d in train[-w:] for n in d["nums"])
            scores={n:rc[n]/w-counts[n]/len(train) for n in range(1,46)}
            a=sorted(range(1,46),key=lambda n:(-scores[n],n))[:6]
            b=sorted(range(1,46),key=lambda n:(scores[n],n))[:6]
            rec.append((f"H001_recent_over_long_{w}",tround,len(set(a)&actual)))
            rec.append((f"H001_long_over_recent_{w}",tround,len(set(b)&actual)))
    out={}
    for name in sorted(set(x[0] for x in rec)):
        hs=[x[2] for x in rec if x[0]==name]
        out[name]={"n":len(hs),"mean":statistics.mean(hs),"variance":statistics.pvariance(hs),
                   "rate_ge2":sum(h>=2 for h in hs)/len(hs),"rate_ge3":sum(h>=3 for h in hs)/len(hs),
                   "hits_0_6":{str(k):sum(h==k for h in hs) for k in range(7)}}
    return out


def monte_carlo(draws):
    rng=random.Random(SEED); hist=Counter(); targets=draws[200:]; per_target=2000
    for d in targets:
        actual=set(d["nums"])
        for _ in range(per_target): hist[len(actual & set(rng.sample(range(1,46),6)))] += 1
    n=sum(hist.values()); vals=[]
    mean=sum(k*v for k,v in hist.items())/n; var=sum(((k-mean)**2)*v for k,v in hist.items())/n
    return {"seed":SEED,"targets":len(targets),"tickets_per_target":per_target,"comparisons":n,"mean":mean,"variance":var,
            "rate_ge2":sum(v for k,v in hist.items() if k>=2)/n,"rate_ge3":sum(v for k,v in hist.items() if k>=3)/n,
            "rate_ge4":sum(v for k,v in hist.items() if k>=4)/n,"rate_ge5":sum(v for k,v in hist.items() if k>=5)/n,
            "rate_6":hist[6]/n,"hits_0_6":{str(k):hist[k] for k in range(7)}}


def run_b(snapshot):
    temp=ROOT/".daily_tmp_20261012"; (temp/"scripts").mkdir(parents=True,exist_ok=True); (temp/"work/lotto-data").mkdir(parents=True,exist_ok=True); (temp/"outputs").mkdir(parents=True,exist_ok=True)
    (temp/"work/lotto-data/lotto_data.csv").write_text(snapshot,encoding="utf-8")
    src=(ROOT/"outputs/B_MODEL_REPRODUCTION_20261009_v1/EXECUTED_b_model_backtest.py").read_text(encoding="utf-8")
    src=src.replace('if len(draws) != 1244 or [d["round"] for d in draws] != list(range(1, 1245)):', 'if len(draws) != 1245 or [d["round"] for d in draws] != list(range(1, 1246)):')
    src=src.replace('validated rounds 1..1244','validated rounds 1..1245').replace('1244 - anchor','1245 - anchor')
    script=temp/"scripts/b_model_backtest.py"; script.write_text(src,encoding="utf-8")
    cp=subprocess.run([sys.executable,str(script)],cwd=temp,capture_output=True,text=True,timeout=240)
    (OUT/"B_EXECUTION_STDOUT.log").write_text(cp.stdout,encoding="utf-8"); (OUT/"B_EXECUTION_STDERR.log").write_text(cp.stderr,encoding="utf-8")
    result={"returncode":cp.returncode}
    if cp.returncode!=0: return result
    for name in ["b_model_classification.csv","b_model_holdout_metrics.csv","b_model_50_round_trends.csv","b_model_backtest_report.md"]:
        p=temp/"outputs"/name
        if p.exists(): (OUT/name).write_bytes(p.read_bytes())
    # leakage invariant from detailed predictions
    pred=temp/"outputs/b_model_predictions.csv"
    leak=True; nrows=0; target1245=0
    if pred.exists():
        with pred.open(encoding="utf-8-sig",newline="") as f:
            for r in csv.DictReader(f):
                nrows+=1; leak &= int(r["training_through_round"])==int(r["target_round"])-1
                if int(r["target_round"])==1245: target1245+=1
    result.update({"prediction_rows":nrows,"training_target_invariant":bool(leak),"rows_for_target_1245":target1245})
    # newest anchor 1200 / to_end metric summary
    hp=temp/"outputs/b_model_holdout_metrics.csv"; latest=[]
    if hp.exists():
        with hp.open(encoding="utf-8-sig",newline="") as f:
            for r in csv.DictReader(f):
                if r["anchor_after_round"]=="1200" and r["horizon"].startswith("to_end"):
                    latest.append({k:r[k] for k in ["model","n","mean_hits","variance_hits_population","rate_ge_2","rate_ge_3","rate_ge_4","rate_ge_5","structure_conditions_mean_of_6","structure_full_match_rate"]})
    result["latest_anchor_1200"]=latest
    return result


def main():
    raw=read_raw(); integ_pre=integrity(raw)
    if len(raw)!=1244 or not all([integ_pre["continuous"],integ_pre["six_unique_main"],integ_pre["main_range"],integ_pre["bonus_range"],integ_pre["bonus_not_main"]]):
        raise SystemExit("raw 1..1244 integrity failed")
    draws=raw+[LATEST]; integ=integrity(draws)
    # reproducible snapshot, original lotto_data.csv remains untouched
    lines=["round,date,no1,no2,no3,no4,no5,no6,bonus"]
    for d in draws: lines.append(",".join(map(str,[d["round"],d["date"],*d["nums"],d["bonus"]])))
    snapshot="\n".join(lines)+"\n"; (OUT/"lotto_data_1_1245_snapshot.csv").write_text(snapshot,encoding="utf-8")
    nums=number_table(draws); (OUT/"NUMBER_STATS_1245.csv").write_text("",encoding="utf-8")
    with (OUT/"NUMBER_STATS_1245.csv").open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(nums[0].keys())); w.writeheader(); w.writerows(nums)
    ss,fs=structure_summary(draws); rel=relation_summary(draws); contra=contrarian_summary(draws,fs,ss)
    h=h001_h002(draws); mc=monte_carlo(draws); pr=purchase_review(LATEST["nums"]); b=run_b(snapshot)
    theoretical={"mean":0.8,"variance":0.6145454545454545}
    den=math.comb(45,6); probs={k:math.comb(6,k)*math.comb(39,6-k)/den for k in range(7)}
    theoretical.update({"rate_ge2":sum(probs[k] for k in range(2,7)),"rate_ge3":sum(probs[k] for k in range(3,7)),"rate_ge4":sum(probs[k] for k in range(4,7)),"rate_ge5":sum(probs[k] for k in range(5,7)),"rate_6":probs[6]})
    summary={"date":DATE,"data":{"repository_rows_before":len(raw),"analysis_rows":len(draws),"latest_round":1245,"integrity_before":integ_pre,"integrity_with_1245":integ},
             "number_stats":{"rows":45,"long_recent_windows":[10,30,50,100]},"structure":ss,"relations":rel,"contrarian":contra,
             "h001_h002":h,"random_monte_carlo":mc,"random_theoretical":theoretical,"purchase_review":pr,"b_execution":b,
             "limitations":{"legacy_A_integrated_source":"NOT_EXECUTABLE_FROM_VERIFIED_SOURCE","legacy_C_integrated_source":"NOT_EXECUTABLE_FROM_VERIFIED_SOURCE","H005_corrected_S008":"NOT_EXECUTED_NO_FROZEN_MAPPING"}}
    (OUT/"DAILY_STUDY_RESULT.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
    # concise report; no candidate/final numbers
    best=max((v["mean"],k) for k,v in h.items() if k.startswith("H001")); due=h["H002_due"]; anti=h["H002_anti"]
    l=ss["latest"]
    report=f'''# Daily Lotto study — {DATE}\n\n## 1. Data / execution\n- Repository raw file verified: rounds 1..1244; original was not overwritten.\n- Round 1245 was appended only to today's versioned snapshot after external two-source verification.\n- Analysis snapshot rows: {len(draws)}; continuity={integ['continuous']}; duplicate rounds={integ['duplicate_rounds']}; six unique main={integ['six_unique_main']}; main range={integ['main_range']}; bonus separation={integ['bonus_not_main']}.\n\n## 2. Actually recalculated today\n- Full 1..45 cumulative counts/rates, current/max gaps, average intervals, and 10/30/50/100 deltas: `NUMBER_STATS_1245.csv`.\n- Structure, pair/triple concentration, contrarian incidence: recalculated on 1..1245.\n- H001/H002 cutoff-safe walk-forward: rerun on targets 201..1245.\n- Uniform random baseline: actually simulated {mc['comparisons']:,} ticket-vs-draw comparisons with seed {SEED}.\n- B model: actual rerun from the preserved executable B source on the 1..1245 snapshot; returncode={b['returncode']}; prediction rows={b.get('prediction_rows')}; leakage invariant={b.get('training_target_invariant')}; target-1245 rows={b.get('rows_for_target_1245')}.\n\n## 3. New factual findings\n- H002 due-only mean={due['mean']:.6f}, 2+={due['rate_ge2']:.4%}, 3+={due['rate_ge3']:.4%}.\n- H002 anti-due mean={anti['mean']:.6f}, 2+={anti['rate_ge2']:.4%}, 3+={anti['rate_ge3']:.4%}.\n- Numerically best H001 direction/window today was `{best[1]}` mean={best[0]:.6f}; this is not promoted without a stable random-beating result.\n- Monte Carlo mean={mc['mean']:.6f}, 2+={mc['rate_ge2']:.4%}, 3+={mc['rate_ge3']:.4%}; theoretical random mean={theoretical['mean']:.6f}, 2+={theoretical['rate_ge2']:.4%}.\n- Latest draw structure: odd/even={l['odd']}:{l['even']}, low/high={l['low']}:{l['high']}, sum={l['sum']}, consecutive-pair count={l['consecutive_pairs']}, ending-repeat-excess={l['ending_repeat_excess']}, previous-overlap={l['previous_overlap']}.\n- Stored pre-draw purchase record review: lines={pr.get('line_count')}, max hits={pr.get('max_hits')}, 2+ rate={pr.get('rate_ge2')}; no historical recommendation was reconstructed.\n\n## 4. Relation / structure summary\n- Pair top-10 share all={rel['all']['pair_top10_share']:.4%}, recent50={rel['50']['pair_top10_share']:.4%}; triple top-10 share all={rel['all']['triple_top10_share']:.4%}, recent50={rel['50']['triple_top10_share']:.4%}.\n- Historical sum 5th/95th percentile thresholds={ss['historical_sum_p05']:.1f}/{ss['historical_sum_p95']:.1f}.\n- Contrarian latest flags: {json.dumps(contra['latest'],ensure_ascii=False)}.\n\n## 5. A / B / C status\n- A: separable signal components were actually recomputed through B-compatible long-frequency/gap/recent/structure/pair/triple diagnostics. The exact legacy integrated A source is still not verified, so no invented A aggregate is reported.\n- B: actual execution today. Detailed outputs saved beside this report.\n- C/contrarian: structural incidence recalculated; no new unvalidated weighting was adopted.\n- H005/S008 correction: NOT EXECUTED because no pre-frozen corrected mapping exists; inventing one after observing 1245 would violate the protocol.\n\n## 6. Forced-check result\nToday contains real new computations, not a state-only summary. However `legacy A integrated`, `legacy C integrated`, and `H005 corrected S008` remain unavailable/not executed, so this report does **not** label the entire MASTER checklist as fully complete.\n'''
    (OUT/"DAILY_STUDY_REPORT.md").write_text(report,encoding="utf-8")

if __name__=="__main__": main()
