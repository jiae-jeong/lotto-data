#!/usr/bin/env python3
"""E054: rolling draw-frequency concentration regime conditional inclusion model."""
from __future__ import annotations
import argparse, hashlib, itertools, json, random, re, statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"automation/three_line_research_1251_v1.py"
POLICY=ROOT/"research/weekly_purchase/1251/THREE_LINE_POLICY_1251_PLUS.json"
PREREG=ROOT/"research/weekly_purchase/1251/E054_THREE_LINE_ROLLING_CONCENTRATION_REGIME_PREREG_20261116.json"
STUDY="E054_THREE_LINE_ROLLING_CONCENTRATION_REGIME_v1"
WINDOW, HISTORY_START, PRIOR_STRENGTH = 100, 301, 45.0
METRICS=("max_hits","any2","any3","winning_union_coverage")

def load_base():
    import importlib.util
    spec=importlib.util.spec_from_file_location("e054_e045_reference",BASE)
    if spec is None or spec.loader is None: raise RuntimeError("Cannot load frozen E045 helpers")
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module

def rolling_hhi(window):
    if len(window)!=WINDOW: raise ValueError("E054 requires exactly 100 draws per HHI window")
    counts=[0]*46
    for draw in window:
        nums=[int(n) for n in draw["nums"]]
        if len(nums)!=6 or len(set(nums))!=6 or any(n<1 or n>45 for n in nums):
            raise ValueError("Invalid E054 draw")
        for n in nums: counts[n]+=1
    return sum((counts[n]/600.0)**2 for n in range(1,46))

def build_hhi_series(draws):
    return {end:rolling_hhi(draws[end-WINDOW:end]) for end in range(WINDOW,len(draws)+1)}

def regime_details(target,hhi):
    if target<HISTORY_START: raise ValueError("E054 target before history start")
    current_end=target-1
    ref_start=max(WINDOW,target-300)
    ref_end=target-101
    if current_end not in hhi or ref_end<ref_start: raise ValueError("Missing pre-target HHI")
    refs=[float(hhi[k]) for k in range(ref_start,ref_end+1)]
    if len(refs)<100: raise ValueError("Insufficient prior HHI reference windows")
    threshold=statistics.median(refs)
    current=float(hhi[current_end])
    return {
        "regime":1 if current>=threshold else 0,
        "current_hhi":current,
        "threshold_hhi":threshold,
        "current_window_end_round":current_end,
        "reference_start_end_round":ref_start,
        "reference_end_end_round":ref_end,
        "reference_count":len(refs),
    }

def build_regime_history(hhi,cutoff):
    return {u:int(regime_details(u,hhi)["regime"]) for u in range(HISTORY_START,cutoff+1)}

def update_counts(regime,outcome,exposures,successes):
    actual=set(int(n) for n in outcome)
    if regime not in (0,1) or len(actual)!=6 or any(n<1 or n>45 for n in actual):
        raise ValueError("Invalid E054 regime/outcome")
    for n in range(1,46):
        exposures[regime][n]+=1
        if n in actual: successes[regime][n]+=1

def regime_scores(regime,exposures,successes):
    if regime not in (0,1): raise ValueError("Regime must be LOW=0 or HIGH=1")
    return {n:(successes[regime][n]+6.0)/(exposures[regime][n]+PRIOR_STRENGTH) for n in range(1,46)}

def make_portfolio(scores,base):
    used=set(); lines=[]
    for _ in range(3):
        line=tuple(int(n) for n in base.choose_disjoint_ticket(scores,scores,used))
        lines.append(line); used.update(line)
    if len(lines)!=3 or len(used)!=18: raise AssertionError("E054 requires three disjoint lines with union18")
    return lines

def _sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def _normalize_csvs(folder):
    for path in folder.glob("*.csv"):
        raw=path.read_bytes()
        if raw.startswith(b"\xef\xbb\xbf"): raw=raw[3:]
        path.write_bytes(raw.replace(b"\r\n",b"\n"))

def verify_spec(pr,policy):
    assert pr["study_id"]==STUDY and pr["policy_id"]==policy["policy_id"]
    assert pr["preregistration_status"]=="FROZEN_BEFORE_EXECUTION"
    assert pr["independent_research_axis"] is True and pr["independent_signal_family"] is True
    assert pr["historical_data_cutoff"]==1250 and pr["target_rounds"]=="401..1250 inclusive"
    assert pr["source_data_prefix_sha256"]=="7203238dae69ce281c59e6a0928cc187b11d88ed342685cd2dd2f214f063b3c2"
    assert pr["source_data_full_file_sha256"]==pr["source_data_prefix_sha256"]
    f=pr["feature_definition"]
    assert f["rolling_window_draws"]==100 and f["reference_window_count"]==200 and f["minimum_reference_window_count"]==100
    assert f["concentration_metric"]=="HHI=sum_n((count_n/600)^2) over all 45 main-number inclusion frequencies in the immediately preceding 100 draws."
    assert f["classification"]=="At target t, HIGH when current HHI is greater than or equal to the median of up to 200 earlier valid rolling-100-draw HHI values ending t-300..t-101 (minimum 100; exactly 200 when available); otherwise LOW."
    assert f["historical_outcome_regime"]=="For outcome u, classify using draws u-100..u-1 and valid HHI reference windows ending max(100,u-300)..u-101; minimum 100, exactly 200 when available; all inputs precede outcome u."
    assert f["candidate_universe"]=="All integers 1..45 are scored for every target."
    assert f["training_outcome_start_round"]==HISTORY_START
    e=pr["estimator"]
    assert e["prior_mean"]=="6/45 main-number inclusion probability under the uniform 6-of-45 null"
    assert e["prior_strength"]==45 and e["posterior_probability"]=="(success[regime,n] + 45*(6/45))/(exposure[regime,n] + 45)"
    assert e["ranking"]=="Score descending, then number ascending." and e["variants"]==1 and e["parameter_search"] is False
    p=pr["portfolio"]
    assert p["geometry"]=="Exactly three pairwise-disjoint six-number lines, union18."
    assert p["selection"]=="Three sequential calls to the unchanged E045 choose_disjoint_ticket selector, passing the E054 regime-conditional score as both role_score and global_score; remove selected numbers after each line."
    assert p["randomness_in_selection"] is False and p["variants"]==1
    r=pr["random_comparator"]
    assert r["random_bundles_per_target"]==120 and r["seed"]==20261116054 and r["randomness_used_for_final_selection"] is False
    assert r["method"]=="For each target, uniformly permute labels 1..45 jointly over the three fixed model lines, preserving three six-number lines, pairwise disjointness, union18, and line-incidence geometry."
    inf=pr["inference"]
    assert inf["metrics"]==list(METRICS) and inf["family_alpha"]==0.05 and inf["alpha_per_metric"]==0.0125
    assert inf["bootstrap_replicates"]==4000 and inf["bootstrap_seed"]==20261116054 and inf["block_length_targets"]==50
    assert inf["retain_final_remainder_block"] is True and inf["any2_positive_nonoverlapping_50_target_block_share_min"]==0.65
    assert all(inf[k] is True for k in ("no_threshold_relaxation","no_alpha_change","no_block_length_change","no_comparator_change","no_unbounded_microvariants"))
    pc=pr["prospective_confirmation"]
    assert pc["required_by_policy"] is True and pc["minimum_target_count"] is None and pc["completion_rule"] is None and pc["status"]=="UNSPECIFIED_IN_POLICY"
    assert pr["expected_record_counts"]=={"PREDICTIONS":850,"RANDOM_BASELINE":850,"BLOCK_STABILITY":17,"REGIME_SUMMARY":2}
    assert pr["no_future_leakage"] is True and pr["strict_pass_ready_requires_prospective_rule"] is True
    assert policy["effective_from_target"]==1251 and policy["purchase_lines"]==3
    g=policy["strict_gate"]
    assert g["family_alpha"]==0.05 and g["alpha_per_metric"]==0.0125 and g["any2_positive_nonoverlapping_50_target_block_share_min"]==0.65
    assert g["all_adjusted_moving_block_ci_lower_bounds_strictly_gt_zero"] is True
    assert g["no_threshold_relaxation"] is True and g["prospective_confirmation_required"] is True
    for key in ("mean_max_hit","p_any2","p_any3","expected_union_coverage"):
        assert abs(float(policy["exact_null"][key])-float(r["exact_null"][key]))<1e-14

def run(date,run_id):
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}",date) or not re.fullmatch(r"[A-Za-z0-9_-]+",run_id):
        raise ValueError("Unsafe date/run id")
    pr=json.loads(PREREG.read_text(encoding="utf-8")); policy=json.loads(POLICY.read_text(encoding="utf-8"))
    if date!=pr["date_kst"]: raise ValueError("Run date differs from frozen E054 preregistration")
    verify_spec(pr,policy); base=load_base(); cutoff=1250
    draws,prefix_sha,data_sha,rows=base.load_frozen_draw_prefix(cutoff,pr["source_data_prefix_sha256"],pr["source_data_full_file_sha256"])
    if rows!=cutoff or len(draws)!=cutoff: raise ValueError("E054 requires canonical rounds 1..1250")
    start=401
    hhi=build_hhi_series(draws); regimes=build_regime_history(hhi,cutoff)
    exposures=[[0]*46 for _ in range(2)]; successes=[[0]*46 for _ in range(2)]
    for u in range(HISTORY_START,start): update_counts(regimes[u],draws[u-1]["nums"],exposures,successes)
    obs=[]; random_rows=[]; model_geo=0; random_geo=0; random_count=120
    null=pr["random_comparator"]["exact_null"]
    exact={"max_hits":float(null["mean_max_hit"]),"any2":float(null["p_any2"]),"any3":float(null["p_any3"]),"winning_union_coverage":float(null["expected_union_coverage"])}
    for target in range(start,cutoff+1):
        detail=regime_details(target,hhi); regime=detail["regime"]; scores=regime_scores(regime,exposures,successes)
        lines=make_portfolio(scores,base); union=set().union(*(set(x) for x in lines))
        if len(union)!=18 or any(set(a)&set(b) for a,b in itertools.combinations(lines,2)):
            model_geo+=1; raise AssertionError(f"Model geometry failure at {target}")
        actual=set(draws[target-1]["nums"]); metrics=base.portfolio_metrics(lines,actual)
        hits=[len(set(line)&actual) for line in lines]
        score_raw=json.dumps([[n,round(scores[n],16)] for n in range(1,46)],separators=(",",":")).encode()
        obs.append({"target_round":target,"training_through_round":target-1,"training_outcome_count":target-HISTORY_START,
          "regime":regime,"current_hhi":detail["current_hhi"],"threshold_hhi":detail["threshold_hhi"],
          "prior_hhi_reference_count":detail["reference_count"],"regime_training_outcomes":exposures[regime][1],
          "lines":lines,"actual":tuple(sorted(actual)),"line_hits":hits,"score_sha256":hashlib.sha256(score_raw).hexdigest(),**metrics})
        rng=random.Random(20261116054+target); sims=[]
        for _ in range(random_count):
            rl=base.permute_portfolio_labels(lines,rng); ru=set().union(*(set(x) for x in rl))
            if len(ru)!=18 or any(set(a)&set(b) for a,b in itertools.combinations(rl,2)):
                random_geo+=1; raise AssertionError(f"Random geometry failure at {target}")
            sims.append(base.portfolio_metrics(rl,actual))
        random_rows.append({"target_round":target,"regime":"HIGH" if regime else "LOW","random_bundles":random_count,
          "random_mean_max_hits":statistics.mean(x["max_hits"] for x in sims),"random_p_any2":statistics.mean(x["any2"] for x in sims),
          "random_p_any3":statistics.mean(x["any3"] for x in sims),"random_mean_union_coverage":statistics.mean(x["winning_union_coverage"] for x in sims),
          "exact_null_mean_max_hit":exact["max_hits"],"exact_null_p_any2":exact["any2"],"exact_null_p_any3":exact["any3"],
          "exact_null_expected_union_coverage":exact["winning_union_coverage"],"geometry_violations":0})
        update_counts(regimes[target],actual,exposures,successes)
    if [x["target_round"] for x in obs]!=list(range(401,1251)): raise AssertionError("Target sequence mismatch")
    diffs={m:[float(x[m])-exact[m] for x in obs] for m in METRICS}
    block_size=50; reps=4000; alpha=0.0125
    blocks=[]
    for idx,s in enumerate(range(0,len(obs),block_size),1):
        e=min(s+block_size,len(obs)); row={"block_index":idx,"start_target":obs[s]["target_round"],"end_target":obs[e-1]["target_round"],"n":e-s}
        for m in METRICS: row["mean_delta_"+m]=statistics.mean(diffs[m][s:e])
        row["any2_positive"]=int(row["mean_delta_any2"]>0); blocks.append(row)
    if len(blocks)!=17 or any(x["n"]!=50 for x in blocks): raise AssertionError("Block geometry mismatch")
    positive=sum(x["any2_positive"] for x in blocks); share=positive/len(blocks)
    metric_results={}
    for i,m in enumerate(METRICS):
        ci=base.moving_block_ci(diffs[m],alpha,20261116054+9000+i,reps,block_size)
        metric_results[m]={"observed_mean":statistics.mean(x[m] for x in obs),"exact_geometry_matched_null":exact[m],
          "delta_mean":statistics.mean(diffs[m]),"adjusted_moving_block_ci":ci,"lower_bound_strictly_gt_zero":ci[0]>0}
    historical=all(metric_results[m]["lower_bound_strictly_gt_zero"] for m in METRICS) and share>=0.65
    strict=base.strict_portfolio_ready(historical,None,None)
    readiness="HISTORICAL_GATE_PASS_BUT_NOT_READY_PROSPECTIVE_RULE_UNSPECIFIED" if historical else "STRICT_FAIL"
    random_means={"max_hits":statistics.mean(x["random_mean_max_hits"] for x in random_rows),
      "any2":statistics.mean(x["random_p_any2"] for x in random_rows),"any3":statistics.mean(x["random_p_any3"] for x in random_rows),
      "winning_union_coverage":statistics.mean(x["random_mean_union_coverage"] for x in random_rows)}
    regime_summary=[]
    for value,label in ((0,"LOW"),(1,"HIGH")):
        mg=[x for x in obs if x["regime"]==value]; rg=[x for x in random_rows if x["regime"]==label]
        if not mg: raise AssertionError("Both LOW and HIGH regimes must be represented")
        regime_summary.append({"regime":label,"targets":len(mg),"mean_max_hits":statistics.mean(x["max_hits"] for x in mg),
          "p_any2":statistics.mean(x["any2"] for x in mg),"p_any3":statistics.mean(x["any3"] for x in mg),
          "mean_union_coverage":statistics.mean(x["winning_union_coverage"] for x in mg),
          "random_mean_max_hits":statistics.mean(x["random_mean_max_hits"] for x in rg),
          "random_p_any2":statistics.mean(x["random_p_any2"] for x in rg),
          "random_p_any3":statistics.mean(x["random_p_any3"] for x in rg),
          "random_mean_union_coverage":statistics.mean(x["random_mean_union_coverage"] for x in rg)})
    folder=ROOT/"analysis"/date/run_id/STUDY; folder.mkdir(parents=True,exist_ok=False)
    pred=[]
    for x in obs:
        pred.append({"target_round":x["target_round"],"training_through_round":x["training_through_round"],
          "training_outcome_count":x["training_outcome_count"],"regime":"HIGH" if x["regime"] else "LOW",
          "current_hhi":x["current_hhi"],"threshold_hhi":x["threshold_hhi"],"prior_hhi_reference_count":x["prior_hhi_reference_count"],
          "regime_training_outcomes":x["regime_training_outcomes"],"line1":" ".join(map(str,x["lines"][0])),
          "line2":" ".join(map(str,x["lines"][1])),"line3":" ".join(map(str,x["lines"][2])),
          "actual_numbers":" ".join(map(str,x["actual"])),"line1_hits":x["line_hits"][0],"line2_hits":x["line_hits"][1],
          "line3_hits":x["line_hits"][2],"max_hits":x["max_hits"],"any2":x["any2"],"any3":x["any3"],
          "winning_union_coverage":x["winning_union_coverage"],"union_size":x["union_size"],"score_sha256":x["score_sha256"]})
    base.write_csv(folder/"PREDICTIONS.csv",pred,list(pred[0]))
    base.write_csv(folder/"RANDOM_BASELINE.csv",random_rows,list(random_rows[0]))
    base.write_csv(folder/"BLOCK_STABILITY.csv",blocks,list(blocks[0]))
    base.write_csv(folder/"REGIME_SUMMARY.csv",regime_summary,list(regime_summary[0]))
    _normalize_csvs(folder)
    source_paths=[PREREG,POLICY,BASE,Path(__file__).resolve()]
    source_hashes={p.relative_to(ROOT).as_posix():_sha(p) for p in source_paths}
    base.write_json(folder/"MODEL_SPEC.json",{"study_id":STUDY,"feature_definition":pr["feature_definition"],
      "estimator":pr["estimator"],"portfolio":pr["portfolio"],"random_comparator":pr["random_comparator"],
      "inference":pr["inference"],"selection_uses_randomness":False,"parameter_search":False,"variants_evaluated":1,
      "source_hashes":source_hashes})
    inference={"study_id":STUDY,"evidence_class":"HISTORICAL_INDEPENDENT_SIGNAL_FAMILY_SCREEN_NOT_PROSPECTIVE_CONFIRMATION",
      "data_cutoff":cutoff,"target_range":[start,cutoff],"targets":len(obs),"random_bundles_per_target":random_count,
      "random_bundles_total":len(obs)*random_count,"block_size":block_size,"block_lengths":[x["n"] for x in blocks],
      "family_alpha":0.05,"alpha_per_metric":alpha,"bootstrap_replicates":reps,"metrics":metric_results,
      "any2_positive_50_target_block_share":share,"positive_any2_blocks":positive,"simulated_random_means":random_means,
      "regime_target_counts":{x["regime"]:x["targets"] for x in regime_summary},"regime_summary":regime_summary,
      "historical_strict_gate_pass":historical,"strict_portfolio_pass":strict,"strict_pass_ready":False,"readiness_status":readiness,
      "prospective_minimum_target_count":None,"prospective_completion_rule":None,"prospective_confirmation_status":"UNSPECIFIED_IN_POLICY",
      "parameter_search":False,"thresholds_changed":False,"alpha_changed":False,"block_length_changed":False,
      "comparator_changed":False,"purchase_recommendation_generated":False}
    base.write_json(folder/"INFERENCE.json",inference)
    verification={"status":"PASS","study_id":STUDY,"data_cutoff":cutoff,"current_source_data_rows":rows,
      "data_sha256":data_sha,"data_prefix_sha256":prefix_sha,"target_range":[start,cutoff],"target_count":len(obs),
      "prediction_records":len(pred),"random_bundles_per_target":random_count,"random_bundles_total":len(obs)*random_count,
      "training_cutoff_violations":0,"leakage_failures":0,"future_predictions":0,"portfolio_geometry_violations":model_geo,
      "random_geometry_violations":random_geo,"no_future_leakage":True,"random_baseline_executed":True,
      "independent_research_axis":True,"independent_signal_family":True,"parameter_search":False,
      "thresholds_changed":False,"alpha_changed":False,"block_length_changed":False,"comparator_changed":False,
      "strict_portfolio_pass":strict,"strict_pass_ready":False,"purchase_recommendation_generated":False,"source_hashes":source_hashes}
    base.write_json(folder/"VERIFICATION.json",verification)
    completion={"study_id":STUDY,"status":"COMPLETE","data_cutoff":cutoff,"target_range":[start,cutoff],"target_count":len(obs),
      "historical_strict_gate_pass":historical,"strict_portfolio_pass":strict,"strict_pass_ready":False,"readiness_status":readiness,
      "evidence_class":"HISTORICAL_INDEPENDENT_SIGNAL_FAMILY_SCREEN_NOT_PROSPECTIVE_CONFIRMATION",
      "independent_research_axis":True,"independent_signal_family":True,"purchase_recommendation_generated":False}
    base.write_json(folder/"COMPLETION.json",completion)
    report=["# E054 — Rolling draw-frequency concentration regime","",f"- Study status: **{readiness}**",
      f"- Data cutoff: **{cutoff}**; source rows: **{rows}**",f"- Walk-forward targets: **{len(obs)}** ({start}..{cutoff})",
      f"- Random bundles: **{len(obs)*random_count:,}** ({random_count} per target)",
      "- Feature: prior 100-draw main-number HHI classified against the median of 200 earlier rolling HHI windows; bonus excluded",
      "- Estimator: one fixed Beta-smoothed regime-conditional inclusion probability, prior mean 6/45 and strength 45",
      "- Portfolio: three pairwise-disjoint six-number lines, union18, using unchanged E045 selector",
      "- Randomness is used only for the geometry-matched null, never for selection","",
      "| Metric | Model mean | Exact null | Delta | Adjusted CI lower | Adjusted CI upper |","|---|---:|---:|---:|---:|---:|"]
    for m in METRICS:
        x=metric_results[m]; report.append(f"| {m} | {x['observed_mean']:.6f} | {x['exact_geometry_matched_null']:.6f} | {x['delta_mean']:+.6f} | {x['adjusted_moving_block_ci'][0]:+.6f} | {x['adjusted_moving_block_ci'][1]:+.6f} |")
    report.extend(["","| Regime | Targets | Model mean max hits | Model any2 | Model any3 | Random mean max hits | Random any2 |","|---|---:|---:|---:|---:|---:|---:|"])
    for x in regime_summary:
        report.append(f"| {x['regime']} | {x['targets']} | {x['mean_max_hits']:.6f} | {x['p_any2']:.4%} | {x['p_any3']:.4%} | {x['random_mean_max_hits']:.6f} | {x['random_p_any2']:.4%} |")
    report.extend(["",f"- Any2-positive 50-target block share: **{share:.2%}** ({positive}/{len(blocks)} blocks)",
      f"- Historical strict gate: **{'PASS' if historical else 'FAIL'}**","- STRICT_PASS_READY: **not created**",
      "- Prospective minimum/completion rule: **unspecified and not adopted**",
      "- No final purchase lines, recommendation, or freeze/seal were generated.","",
      "Each target's current regime uses only draws through t-1. Each historical outcome enters its own pre-outcome regime count only after its prediction is frozen. The HHI reference windows end before the current 100-draw window. One frozen signal family, one estimator, no variants or tuning."])
    (folder/"REPORT.md").write_text("\n".join(report)+"\n",encoding="utf-8")
    entries=base.write_and_verify_manifest(folder); _normalize_csvs(folder)
    if entries!=9: raise AssertionError(f"E054 manifest entries {entries} != 9")
    return {"status":"COMPLETE","study_id":STUDY,"result_path":folder.relative_to(ROOT).as_posix(),
      "data_cutoff":cutoff,"target_count":len(obs),"random_bundles_total":len(obs)*random_count,
      "historical_strict_gate_pass":historical,"strict_portfolio_pass":strict,"strict_pass_ready":False,
      "readiness_status":readiness,"manifest_entries":entries}

def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--date",required=True); parser.add_argument("--run-id",required=True)
    args=parser.parse_args(); print(json.dumps(run(args.date,args.run_id),ensure_ascii=False,indent=2))

if __name__=="__main__": main()
