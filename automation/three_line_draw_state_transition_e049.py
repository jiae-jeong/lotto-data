#!/usr/bin/env python3
"""E049: preregistered previous-main-draw-state to next-main transition signal."""
from __future__ import annotations
import argparse, hashlib, json, math, os, random, statistics, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from automation import three_line_bonus_transition_e048 as shared
PREREG_PATH=ROOT/"research/weekly_purchase/1251/E049_THREE_LINE_DRAW_STATE_TRANSITION_PREREG_20261114.json"
POLICY_PATH=ROOT/"research/weekly_purchase/1251/THREE_LINE_POLICY_1251_PLUS.json"
HELPER_PATH=ROOT/"automation/three_line_bonus_transition_e048.py"
STUDY_ID="E049_THREE_LINE_DRAW_STATE_TRANSITION_v1"
PREREG_SHA256="0d76cda3951c3130bc11ed77e9d7cda94c898abe6e065f1557fb9359e2c9461d"
SHARED_HELPER_GIT_BLOB_SHA="aef1471b141a57984b9fb58ca02367ddf661dbc9"
METRICS=("max_hits","any2","any3","winning_union_coverage")


def verify_shared_helper():
    actual=subprocess.check_output(["git","hash-object",str(HELPER_PATH)],cwd=ROOT,text=True).strip()
    if actual!=SHARED_HELPER_GIT_BLOB_SHA:
        raise ValueError(f"shared geometry/inference helper changed: {actual}")
    return actual


def sum_bin(total):
    return 0 if total<120 else 1 if total<145 else 2 if total<170 else 3


def draw_state(nums):
    values=tuple(sorted(int(n) for n in nums))
    if len(values)!=6 or len(set(values))!=6 or any(n<1 or n>45 for n in values):
        raise ValueError("draw_state requires six unique main numbers in 1..45")
    total=sum(values); odd=sum(n%2 for n in values); low=sum(n<=22 for n in values)
    consecutive=sum(b==a+1 for a,b in zip(values,values[1:]))
    return (sum_bin(total),0 if odd<=2 else 1 if odd<=4 else 2,
            0 if low<=2 else 1 if low<=4 else 2,
            0 if consecutive==0 else 1 if consecutive==1 else 2)


def hamming_distance(left,right):
    if len(left)!=4 or len(right)!=4:
        raise ValueError("state distance requires four categorical components")
    return sum(a!=b for a,b in zip(left,right))


def score_numbers(target_state,features,outcomes,global_counts,global_draws,alpha):
    if len(features)!=len(outcomes) or len(global_counts)!=45 or global_draws<=0 or alpha<=0 or not features:
        raise ValueError("invalid E049 score inputs")
    weights=[0.5**hamming_distance(feature,target_state) for feature in features]
    total_weight=math.fsum(weights); weighted=[0.0]*45
    for weight,outcome in zip(weights,outcomes):
        if len(outcome)!=6 or len(set(outcome))!=6:
            raise ValueError("invalid historical transition outcome")
        for number in outcome:
            if not 1<=number<=45: raise ValueError("invalid transition outcome number")
            weighted[number-1]+=weight
    return ([(weighted[i]+alpha*(global_counts[i]/global_draws))/(total_weight+alpha)
             for i in range(45)],total_weight)


def validate_preregistration(prereg,policy):
    if prereg.get("study_id")!=STUDY_ID or prereg.get("policy_id")!=policy.get("policy_id"):
        raise ValueError("E049 study/policy identity mismatch")
    if prereg.get("date_kst")!="2026-11-14" or int(prereg.get("target_round",-1))!=1251:
        raise ValueError("E049 target/date changed")
    if int(prereg.get("historical_data_cutoff",-1))!=1249 or prereg.get("target_rounds")!="401..1249 inclusive":
        raise ValueError("E049 frozen target range changed")
    expected_state={
        "sum_bin":["0 if sum<120","1 if 120<=sum<145","2 if 145<=sum<170","3 if sum>=170"],
        "odd_count_bin":["0 if odd<=2","1 if 3<=odd<=4","2 if odd>=5"],
        "low_count_bin":["0 if count(numbers<=22)<=2","1 if 3<=count<=4","2 if count>=5"],
        "consecutive_pair_bin":["0 if no consecutive pair","1 if exactly one consecutive pair","2 if two or more consecutive pairs"],
        "distance":"Hamming distance across the four categorical state components."}
    if prereg.get("state_definition")!=expected_state: raise ValueError("E049 state definition changed")
    if prereg.get("feature_source")!=("Previous draw's six main numbers only; bonus numbers are excluded. "
        "The state definition is frozen to the existing _state definition in automation/orthogonal_research_v2.py."):
        raise ValueError("E049 feature source changed")
    expected_estimator={
        "kernel_weight":"0.5 ** HammingDistance(previous_draw_state, target_previous_draw_state)",
        "conditional_count":"Weighted count of each main number in historical transition outcomes.",
        "global_rate":"Count of each main number in draws 1..t-1 divided by t-1.",
        "smoothing_alpha":60,
        "score_formula":"(weighted_conditional_count[n] + 60 * global_main_inclusion_rate[n]) / (sum_transition_weights + 60)",
        "ranking":"Score descending, then number ascending."}
    if prereg.get("estimator")!=expected_estimator: raise ValueError("E049 estimator changed")
    p=prereg["portfolio"]
    if (p.get("selected_union")!="Top 18 ranked numbers."
        or p.get("line_assignment")!="Deterministic rank interleaving: line 1 uses ranks 1,4,7,10,13,16; line 2 uses ranks 2,5,8,11,14,17; line 3 uses ranks 3,6,9,12,15,18."
        or p.get("geometry")!="Exactly three pairwise-disjoint six-number lines, union18."
        or p.get("randomness_in_selection") is not False
        or p.get("parameter_tuning") is not False or int(p.get("variants",-1))!=1):
        raise ValueError("E049 portfolio specification changed")
    r=prereg["random_comparator"]
    if r.get("method")!="For each target, uniformly permute labels 1..45 jointly over the three fixed model lines, preserving three six-number lines, pairwise disjointness, union18, and line incidence geometry.":
        raise ValueError("E049 random comparator changed")
    if int(r.get("random_bundles_per_target",-1))!=120 or int(r.get("seed",-1))!=2026111404 or r.get("randomness_used_for_final_selection") is not False:
        raise ValueError("E049 random seed/count/selection rule changed")
    i=prereg["inference"]
    if (i.get("metrics")!=list(METRICS) or float(i.get("family_alpha",-1))!=0.05
        or float(i.get("alpha_per_metric",-1))!=0.0125 or int(i.get("bootstrap_replicates",-1))!=4000
        or int(i.get("bootstrap_seed",-1))!=2026111404 or int(i.get("block_length_targets",-1))!=50
        or i.get("retain_final_remainder_block") is not True
        or float(i.get("any2_positive_nonoverlapping_50_target_block_share_min",-1))!=0.65
        or any(i.get(k) is not True for k in ("no_threshold_relaxation","no_alpha_change","no_block_length_change","no_comparator_change","no_unbounded_microvariants"))):
        raise ValueError("E049 inference specification changed")
    pc=prereg["prospective_confirmation"]
    if pc.get("required_by_policy") is not True or pc.get("minimum_target_count") is not None or pc.get("completion_rule") is not None or pc.get("status")!="UNSPECIFIED_IN_POLICY":
        raise ValueError("E049 prospective rule must remain unspecified")
    if prereg.get("expected_record_counts")!={"PREDICTIONS":849,"RANDOM_BASELINE":849,"BLOCK_STABILITY":17}:
        raise ValueError("E049 record counts changed")
    if prereg.get("source_data_prefix_sha256")!="a5996af8b842799d777beae0abeef9767f79726870e4d78d6683dfb0fe4802e7" or prereg.get("source_data_full_file_sha256")!="a5996af8b842799d777beae0abeef9767f79726870e4d78d6683dfb0fe4802e7":
        raise ValueError("E049 frozen source hashes changed")
    if prereg.get("no_future_leakage") is not True or prereg.get("strict_pass_ready_requires_prospective_rule") is not True:
        raise ValueError("E049 leakage/readiness policy changed")
    if int(policy.get("effective_from_target",-1))!=1251 or int(policy.get("purchase_lines",-1))!=3 or int(policy.get("numbers_per_line",-1))!=6:
        raise ValueError("active three-line policy changed")
    g=policy["strict_gate"]
    if (float(g["family_alpha"])!=0.05 or float(g["alpha_per_metric"])!=0.0125
        or float(g["any2_positive_nonoverlapping_50_target_block_share_min"])!=0.65
        or g.get("all_adjusted_moving_block_ci_lower_bounds_strictly_gt_zero") is not True
        or g.get("no_threshold_relaxation") is not True or g.get("prospective_confirmation_required") is not True):
        raise ValueError("strict gate differs from active policy")
    for key in ("mean_max_hit","p_any2","p_any3","expected_union_coverage"):
        if abs(float(r["exact_null"][key])-float(policy["exact_null"][key]))>1e-14:
            raise ValueError(f"E049 exact null changed: {key}")


def run(date_kst,run_id,run_attempt):
    helper_sha=verify_shared_helper()
    raw=PREREG_PATH.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=PREREG_SHA256: raise ValueError("E049 preregistration SHA256 mismatch")
    prereg=json.loads(raw.decode("utf-8")); policy=json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    if date_kst!=prereg["date_kst"]: raise ValueError("run date differs from frozen E049 preregistration")
    validate_preregistration(prereg,policy)
    cutoff=int(prereg["historical_data_cutoff"])
    draws,prefix_sha,data_sha,total_rows=shared.read_frozen_prefix(cutoff,prereg["source_data_prefix_sha256"],prereg["source_data_full_file_sha256"])
    start=int(prereg["target_rounds"].split("..")[0]); alpha=float(prereg["estimator"]["smoothing_alpha"])
    reps=int(prereg["random_comparator"]["random_bundles_per_target"]); seed=int(prereg["random_comparator"]["seed"])
    n=prereg["random_comparator"]["exact_null"]
    exact={"max_hits":float(n["mean_max_hit"]),"any2":float(n["p_any2"]),"any3":float(n["p_any3"]),"winning_union_coverage":float(n["expected_union_coverage"])}
    global_counts=[0]*45
    for draw in draws[:start-1]:
        for number in draw["nums"]: global_counts[number-1]+=1
    features=[draw_state(draws[u-2]["nums"]) for u in range(2,start)]
    outcomes=[draws[u-1]["nums"] for u in range(2,start)]
    predictions=[]; random_rows=[]
    for target in range(start,cutoff+1):
        if len(features)!=target-2 or len(outcomes)!=target-2: raise AssertionError(f"transition cutoff violation at {target}")
        state=draw_state(draws[target-2]["nums"])
        scores,total_weight=score_numbers(state,features,outcomes,global_counts,target-1,alpha)
        lines=shared.build_portfolio(scores); actual=set(draws[target-1]["nums"])
        observed=shared.portfolio_metrics(lines,actual)
        line_hits=[len(set(line)&actual) for line in lines]
        predictions.append({"target_round":target,"training_through_round":target-1,
            "previous_draw_state":" ".join(map(str,state)),"transition_example_count":len(features),
            "sum_transition_weights":f"{total_weight:.12f}","top18_candidate_recall":observed["winning_union_coverage"],
            "line1":" ".join(map(str,lines[0])),"line2":" ".join(map(str,lines[1])),
            "line3":" ".join(map(str,lines[2])),"actual_main":" ".join(map(str,sorted(actual))),
            "line_hits":" ".join(map(str,line_hits)),**observed})
        rng=random.Random(seed+target)
        rm=[shared.portfolio_metrics(shared.permute_portfolio_labels(lines,rng),actual) for _ in range(reps)]
        random_rows.append({"target_round":target,"random_bundles":reps,
            "random_mean_max_hits":statistics.mean(x["max_hits"] for x in rm),
            "random_p_any2":statistics.mean(x["any2"] for x in rm),
            "random_p_any3":statistics.mean(x["any3"] for x in rm),
            "random_mean_union_coverage":statistics.mean(x["winning_union_coverage"] for x in rm),
            "exact_null_mean_max_hit":exact["max_hits"],"exact_null_p_any2":exact["any2"],
            "exact_null_p_any3":exact["any3"],"exact_null_expected_union_coverage":exact["winning_union_coverage"],
            "geometry_violations":0})
        for number in actual: global_counts[number-1]+=1
        features.append(state); outcomes.append(draws[target-1]["nums"])
    targets=list(range(start,cutoff+1))
    if [int(x["target_round"]) for x in predictions]!=targets or len(predictions)!=849 or len(random_rows)!=849:
        raise AssertionError("E049 walk-forward target/count mismatch")
    diffs={m:[float(x[m])-exact[m] for x in predictions] for m in METRICS}
    block=50; alpha_ci=float(prereg["inference"]["alpha_per_metric"])
    boot=int(prereg["inference"]["bootstrap_replicates"]); boot_seed=int(prereg["inference"]["bootstrap_seed"])
    blocks=[]
    for ix,s in enumerate(range(0,len(predictions),block),1):
        e=min(s+block,len(predictions)); row={"block_index":ix,"start_target":targets[s],"end_target":targets[e-1],"n":e-s}
        for m in METRICS: row[f"mean_delta_{m}"]=statistics.mean(diffs[m][s:e])
        row["any2_positive"]=int(row["mean_delta_any2"]>0); blocks.append(row)
    if len(blocks)!=17: raise AssertionError("E049 block count mismatch")
    positive=sum(x["any2_positive"] for x in blocks); share=positive/len(blocks); inf={}
    for offset,m in enumerate(METRICS):
        ci=shared.moving_block_ci(diffs[m],alpha_ci,boot_seed+9000+offset,boot,block)
        inf[m]={"observed_mean":statistics.mean(float(x[m]) for x in predictions),
            "exact_geometry_matched_null":exact[m],"delta_mean":statistics.mean(diffs[m]),
            "adjusted_moving_block_ci":ci,"lower_bound_strictly_gt_zero":ci[0]>0}
    historical=all(inf[m]["lower_bound_strictly_gt_zero"] for m in METRICS) and share>=0.65
    pc=prereg["prospective_confirmation"]; prospective_defined=pc["minimum_target_count"] is not None and pc["completion_rule"] is not None
    strict=bool(historical and prospective_defined)
    readiness="HISTORICAL_GATE_PASS_BUT_NOT_READY_PROSPECTIVE_RULE_UNSPECIFIED" if historical and not prospective_defined else "PROSPECTIVE_CONFIRMATION_PENDING" if historical else "STRICT_FAIL"
    out=ROOT/"analysis"/date_kst/f"gha_{run_id}_{run_attempt}"/STUDY_ID; out.mkdir(parents=True,exist_ok=False)
    shared.write_csv(out/"PREDICTIONS.csv",predictions,["target_round","training_through_round","previous_draw_state","transition_example_count","sum_transition_weights","top18_candidate_recall","line1","line2","line3","actual_main","line_hits","max_hits","any2","any3","winning_union_coverage"])
    shared.write_csv(out/"RANDOM_BASELINE.csv",random_rows,["target_round","random_bundles","random_mean_max_hits","random_p_any2","random_p_any3","random_mean_union_coverage","exact_null_mean_max_hit","exact_null_p_any2","exact_null_p_any3","exact_null_expected_union_coverage","geometry_violations"])
    shared.write_csv(out/"BLOCK_STABILITY.csv",blocks,["block_index","start_target","end_target","n","mean_delta_max_hits","mean_delta_any2","mean_delta_any3","mean_delta_winning_union_coverage","any2_positive"])
    shared.write_json(out/"MODEL_SPEC.json",{"study_id":STUDY_ID,"state_definition":prereg["state_definition"],"estimator":prereg["estimator"],"portfolio":prereg["portfolio"],"random_comparator":prereg["random_comparator"],"inference":prereg["inference"],"shared_geometry_inference_helper_git_blob_sha":helper_sha,"selection_uses_randomness":False,"parameter_tuning":False,"variants_evaluated":1})
    shared.write_json(out/"INFERENCE.json",{"study_id":STUDY_ID,"data_cutoff":cutoff,"target_range":[start,cutoff],"target_count":len(predictions),"exact_geometry_matched_null":exact,"metrics":inf,"block_stability":{"block_length_targets":50,"total_blocks_including_remainder":len(blocks),"positive_any2_blocks":positive,"any2_positive_block_share":share,"required_minimum":0.65,"remainder_block":blocks[-1]},"historical_strict_gate_pass":historical,"prospective_confirmation":{"required":True,"minimum_target_count":pc["minimum_target_count"],"completion_rule":pc["completion_rule"],"status":"UNSPECIFIED_IN_POLICY","minimum_count_adopted":False},"strict_portfolio_pass":strict,"strict_pass_ready":False,"readiness_status":readiness})
    report=["# E049 — Previous-main-draw-state to next-main transition","",f"- Study status: **{readiness}**",f"- Data cutoff: **{cutoff}**; source rows: **{total_rows}**",f"- Walk-forward targets: **{len(predictions)}** ({start}..{cutoff})",f"- Random bundles: **{len(random_rows)*reps:,}** ({reps} per target)","- Feature: previous draw's six main numbers only; bonus excluded","- Portfolio: three disjoint six-number lines, union18","- Randomness is used only for the geometry-matched null, never selection","","| Metric | Model mean | Exact null | Delta | Adjusted CI lower | Adjusted CI upper |","|---|---:|---:|---:|---:|---:|"]
    for m in METRICS:
        x=inf[m]; ci=x["adjusted_moving_block_ci"]; report.append(f"| {m} | {x['observed_mean']:.6f} | {x['exact_geometry_matched_null']:.6f} | {x['delta_mean']:+.6f} | {ci[0]:+.6f} | {ci[1]:+.6f} |")
    report += ["",f"- any2-positive 50-target block share: **{share:.2%}** ({positive}/{len(blocks)} blocks)",f"- Historical strict gate: **{'PASS' if historical else 'FAIL'}**","- STRICT_PASS_READY: **not created**","- Prospective minimum/completion rule: **unspecified and not adopted**","- No final purchase lines or freeze/seal were generated.","","Each target is scored before its outcome enters global counts and transition history. One frozen specification, no variants or tuning.",""]
    (out/"REPORT.md").write_text("\n".join(report),encoding="utf-8")
    verification={"study_id":STUDY_ID,"status":"PASS","date_kst":date_kst,"run_id":run_id,"run_attempt":run_attempt,"target_round":1251,"data_cutoff":cutoff,"source_data_rows":total_rows,"data_sha256":data_sha,"data_prefix_sha256":prefix_sha,"target_range":[start,cutoff],"target_count":len(predictions),"prediction_records":len(predictions),"random_bundles_per_target":reps,"random_bundles_total":len(random_rows)*reps,"training_cutoff_rule":"training_through_round = target_round - 1","training_cutoff_violations":0,"leakage_failures":0,"future_predictions":0,"no_future_leakage":True,"portfolio_geometry_violations":0,"random_geometry_violations":0,"all_portfolios_three_lines_six_numbers_union18":True,"all_random_comparators_preserve_union18_geometry":True,"selection_uses_randomness":False,"randomness_used_only_for_comparator":True,"source_code_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),"shared_geometry_inference_helper_git_blob_sha":helper_sha,"preregistration_sha256":hashlib.sha256(PREREG_PATH.read_bytes()).hexdigest(),"policy_sha256":hashlib.sha256(POLICY_PATH.read_bytes()).hexdigest(),"historical_strict_gate_pass":historical,"strict_portfolio_pass":strict,"strict_pass_ready":False,"readiness_status":readiness,"purchase_lines_generated":False,"final_purchase_freeze_allowed":False,"prospective_minimum_count_adopted":False,"manifest_entries":8,"manifest_status":"PENDING"}
    shared.write_json(out/"VERIFICATION.json",verification)
    shared.write_json(out/"COMPLETION.json",{"study_id":STUDY_ID,"status":"COMPLETE","data_cutoff":cutoff,"target_count":len(predictions),"random_bundles_total":len(random_rows)*reps,"historical_strict_gate_pass":historical,"strict_portfolio_pass":strict,"strict_pass_ready":False,"computation_complete":True,"promotion_to_purchase_policy":False})
    entries=shared.write_and_verify_manifest(out); verification["manifest_entries"]=entries; verification["manifest_status"]="PASS"
    shared.write_json(out/"VERIFICATION.json",verification); entries=shared.write_and_verify_manifest(out)
    if entries!=8: raise AssertionError(f"E049 manifest count {entries} != 8")
    result={"status":"PASS","study_id":STUDY_ID,"output":str(out.relative_to(ROOT)),"data_cutoff":cutoff,"target_count":len(predictions),"random_bundles_total":len(random_rows)*reps,"historical_strict_gate_pass":historical,"strict_portfolio_pass":strict,"strict_pass_ready":False,"readiness_status":readiness,"manifest_entries":entries}
    print(json.dumps(result,ensure_ascii=False)); return result


def main():
    p=argparse.ArgumentParser(); p.add_argument("--date",required=True); p.add_argument("--run-id",required=True)
    p.add_argument("--run-attempt",default=os.environ.get("GITHUB_RUN_ATTEMPT","1"))
    a=p.parse_args(); run(a.date,a.run_id,str(a.run_attempt))


if __name__=="__main__": main()
