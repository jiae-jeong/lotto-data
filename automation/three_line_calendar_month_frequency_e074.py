#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, hashlib, importlib.util, io, json, random, statistics
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"lotto_data.csv"
POLICY_PATH=ROOT/"research/weekly_purchase/1251/THREE_LINE_POLICY_1251_PLUS.json"
PREREG_PATH=ROOT/"research/weekly_purchase/1251/E074_CALENDAR_MONTH_CONDITIONAL_FREQUENCY_PREREG_20261118.json"
STUDY_ID="E074_THREE_LINE_CALENDAR_MONTH_CONDITIONAL_FREQUENCY_v1"
METRICS=("max_hits","any2","any3","winning_union_coverage")
KST=timezone(timedelta(hours=9))

def load_base():
    spec=importlib.util.spec_from_file_location("e074_e045_reference",ROOT/"automation/three_line_research_1251_v1.py")
    if spec is None or spec.loader is None: raise RuntimeError("Cannot load frozen E045 helpers")
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module

def month_from_date(value):
    parts=str(value).strip().replace("-",".").replace("/",".").split(".")
    if len(parts)!=3: raise ValueError(f"Invalid draw date: {value}")
    month=int(parts[1])
    if not 1<=month<=12: raise ValueError(f"Invalid calendar month: {value}")
    return month

def calendar_month_scores(prior_draws,target_month):
    if not 1<=int(target_month)<=12: raise ValueError("target_month must be in 1..12")
    selected=[d for d in prior_draws if int(d["month"])==int(target_month)]
    exposures=len(selected); hits=Counter()
    for draw in selected:
        nums=tuple(int(n) for n in draw["nums"])
        if len(nums)!=6 or len(set(nums))!=6 or any(n<1 or n>45 for n in nums):
            raise ValueError("Invalid historical draw in calendar-month prefix")
        hits.update(nums)
    return {n:(hits[n]+6.0)/(exposures+45.0) for n in range(1,46)},exposures

def make_portfolio(scores):
    if set(scores)!=set(range(1,46)): raise ValueError("Scores must contain numbers 1..45")
    ranked=sorted(range(1,46),key=lambda n:(-float(scores[n]),n))
    lines=[tuple(sorted(ranked[i:i+6])) for i in (0,6,12)]
    union=set().union(*(set(x) for x in lines))
    if len(union)!=18 or any(len(x)!=6 for x in lines): raise AssertionError("Invalid union18")
    return lines

def run(date_kst,run_id):
    prereg=json.loads(PREREG_PATH.read_text(encoding="utf-8"))
    policy=json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    if prereg["study_id"]!=STUDY_ID or prereg["policy_id"]!=policy["policy_id"]: raise ValueError("Identity mismatch")
    if prereg["preregistration_status"]!="FROZEN_BEFORE_EXECUTION": raise ValueError("Preregistration is not frozen")
    if date_kst!=prereg["date_kst"] or not run_id.replace("_","").replace("-","").isalnum(): raise ValueError("Invalid run arguments")
    if int(policy["effective_from_target"])!=1251 or int(policy["purchase_lines"])!=3: raise ValueError("Policy changed")
    raw=DATA.read_bytes(); data_sha=hashlib.sha256(raw).hexdigest()
    if data_sha!=prereg["source_data_full_file_sha256"]: raise ValueError("Source data hash mismatch")
    rows=[r for r in csv.DictReader(io.StringIO(raw.decode("utf-8-sig"),newline="")) if r.get("round")]
    cutoff=int(prereg["historical_data_cutoff"])
    if len(rows)!=cutoff or [int(r["round"]) for r in rows]!=list(range(1,cutoff+1)): raise ValueError("Incomplete source sequence")
    draws=[]
    for row in rows:
        nums=tuple(sorted(int(row[f"no{i}"]) for i in range(1,7))); bonus=int(row["bonus"])
        if len(set(nums))!=6 or any(n<1 or n>45 for n in nums) or not 1<=bonus<=45 or bonus in nums: raise ValueError("Invalid draw")
        draws.append({"round":int(row["round"]),"date":row["date"],"month":month_from_date(row["date"]),"nums":nums})
    base=load_base()
    random_count=int(prereg["random_comparator"]["random_bundles_per_target"])
    seed=int(prereg["random_comparator"]["seed"])
    reps=int(prereg["inference"]["bootstrap_replicates"])
    block_size=int(prereg["inference"]["block_length_targets"])
    alpha=float(prereg["inference"]["alpha_per_metric"])
    observations=[]; random_rows=[]
    training_violations=leakage_failures=future_predictions=portfolio_violations=random_violations=0
    for target in range(401,cutoff+1):
        idx=target-1; prior=draws[:idx]; through=prior[-1]["round"]
        if through!=target-1 or any(d["round"]>=target for d in prior):
            training_violations+=1; leakage_failures+=1; raise AssertionError("Future data in training prefix")
        draw=draws[idx]; scores,exposure=calendar_month_scores(prior,draw["month"])
        lines=make_portfolio(scores); union=set().union(*(set(x) for x in lines))
        if len(union)!=18 or any(set(lines[i])&set(lines[j]) for i in range(3) for j in range(i+1,3)):
            portfolio_violations+=1; raise AssertionError("Model geometry violation")
        actual=set(draw["nums"]); observed=base.portfolio_metrics(lines,actual)
        observations.append({"target_round":target,"target_date":draw["date"],"target_month":draw["month"],
            "training_through_round":through,"same_month_prior_draws":exposure,"scores":scores,
            "ranked_numbers":sorted(scores,key=lambda n:(-scores[n],n)),"lines":lines,"actual":tuple(sorted(actual)),**observed})
        rng=random.Random(seed+target); random_metrics=[]
        for _ in range(random_count):
            random_lines=base.permute_portfolio_labels(lines,rng)
            if len(set().union(*(set(x) for x in random_lines)))!=18:
                random_violations+=1; raise AssertionError("Random geometry violation")
            random_metrics.append(base.portfolio_metrics(random_lines,actual))
        random_rows.append({"target_round":target,"random_bundles":random_count,
            "random_mean_max_hits":statistics.mean(x["max_hits"] for x in random_metrics),
            "random_p_any2":statistics.mean(x["any2"] for x in random_metrics),
            "random_p_any3":statistics.mean(x["any3"] for x in random_metrics),
            "random_mean_union_coverage":statistics.mean(x["winning_union_coverage"] for x in random_metrics),
            "exact_null_mean_max_hit":float(policy["exact_null"]["mean_max_hit"]),
            "exact_null_p_any2":float(policy["exact_null"]["p_any2"]),
            "exact_null_p_any3":float(policy["exact_null"]["p_any3"]),
            "exact_null_expected_union_coverage":float(policy["exact_null"]["expected_union_coverage"]),
            "geometry_violations":0})
    if [x["target_round"] for x in observations]!=list(range(401,cutoff+1)): raise AssertionError("Target range mismatch")
    nulls={"max_hits":float(policy["exact_null"]["mean_max_hit"]),"any2":float(policy["exact_null"]["p_any2"]),
           "any3":float(policy["exact_null"]["p_any3"]),"winning_union_coverage":float(policy["exact_null"]["expected_union_coverage"])}
    diffs={m:[float(x[m])-nulls[m] for x in observations] for m in METRICS}
    metric_results={}
    for i,m in enumerate(METRICS):
        ci=base.moving_block_ci(diffs[m],alpha,seed+1000+i,reps,block_size)
        metric_results[m]={"observed_mean":statistics.mean(float(x[m]) for x in observations),
            "exact_geometry_matched_null":nulls[m],"delta_mean":statistics.mean(diffs[m]),
            "adjusted_moving_block_ci":ci,"lower_bound_strictly_gt_zero":bool(ci[0]>0)}
    blocks=[]
    for i,start in enumerate(range(0,len(observations),block_size),1):
        stop=min(start+block_size,len(observations))
        block={m:statistics.mean(diffs[m][start:stop]) for m in METRICS}
        blocks.append({"block_index":i,"target_start":observations[start]["target_round"],
            "target_end":observations[stop-1]["target_round"],"n":stop-start,
            "mean_delta_max_hits":block["max_hits"],"mean_delta_any2":block["any2"],
            "mean_delta_any3":block["any3"],"mean_delta_winning_union_coverage":block["winning_union_coverage"],
            "any2_positive":int(block["any2"]>0)})
    block_share=sum(x["any2_positive"] for x in blocks)/len(blocks)
    historical_pass=all(metric_results[m]["lower_bound_strictly_gt_zero"] for m in METRICS) and block_share>=float(prereg["inference"]["any2_positive_nonoverlapping_50_target_block_share_min"])
    failed=[m for m in METRICS if not metric_results[m]["lower_bound_strictly_gt_zero"]]
    if block_share<float(prereg["inference"]["any2_positive_nonoverlapping_50_target_block_share_min"]): failed.append("any2_positive_50_target_block_share")
    out=ROOT/"analysis"/date_kst/run_id/STUDY_ID; out.mkdir(parents=True,exist_ok=False)
    prediction_rows=[]
    for x in observations:
        prediction_rows.append({"target_round":x["target_round"],"target_date":x["target_date"],"target_month":x["target_month"],
            "training_through_round":x["training_through_round"],"same_month_prior_draws":x["same_month_prior_draws"],
            "ranked_numbers":" ".join(map(str,x["ranked_numbers"])),"line1":" ".join(map(str,x["lines"][0])),
            "line2":" ".join(map(str,x["lines"][1])),"line3":" ".join(map(str,x["lines"][2])),
            "actual_main":" ".join(map(str,x["actual"])),"line_hits":" ".join(str(len(set(line)&set(x["actual"]))) for line in x["lines"]),
            "max_hits":x["max_hits"],"any2":x["any2"],"any3":x["any3"],"winning_union_coverage":x["winning_union_coverage"],
            "scores_json":json.dumps({str(k):round(v,12) for k,v in x["scores"].items()},sort_keys=True)})
    base.write_csv(out/"PREDICTIONS.csv",prediction_rows,list(prediction_rows[0]))
    base.write_csv(out/"RANDOM_BASELINE.csv",random_rows,list(random_rows[0]))
    base.write_csv(out/"BLOCK_STABILITY.csv",blocks,list(blocks[0]))
    model_spec={"study_id":STUDY_ID,"evidence_class":"HISTORICAL_NEW_CALENDAR_FEATURE_SCREEN_NOT_INDEPENDENT_SAMPLE_OR_PROSPECTIVE_CONFIRMATION",
        "data_cutoff":cutoff,"data_sha256":data_sha,"target_range":[401,cutoff],"target_count":len(observations),
        "feature_definition":prereg["feature_definition"],"estimator":prereg["estimator"],
        "portfolio_construction":prereg["portfolio_construction"],"random_comparator":prereg["random_comparator"],
        "inference":prereg["inference"],"parameter_search":False,"variants_evaluated":1}
    base.write_json(out/"MODEL_SPEC.json",model_spec)
    inference={"study_id":STUDY_ID,"evidence_class":model_spec["evidence_class"],"data_cutoff":cutoff,"data_sha256":data_sha,
        "target_range":[401,cutoff],"targets":len(observations),"random_bundles_per_target":random_count,
        "random_bundles_total":len(random_rows)*random_count,"bootstrap_replicates":reps,"block_size":block_size,
        "block_count":len(blocks),"alpha_per_metric":alpha,"metrics":metric_results,
        "any2_positive_50_target_block_share":block_share,"historical_strict_gate_pass":historical_pass,
        "failed_gates":failed,"strict_portfolio_pass":False,"strict_pass_ready":False,
        "prospective_confirmation_status":"UNSPECIFIED_IN_POLICY","prospective_minimum_target_count":None,
        "prospective_completion_rule":None,"thresholds_or_policy_changed":False,"parameter_search":False,"variants_evaluated":1}
    base.write_json(out/"INFERENCE.json",inference)
    completed=datetime.now(timezone.utc).astimezone(KST).isoformat()
    verification={"status":"PASS","study_id":STUDY_ID,"data_cutoff":cutoff,"current_source_data_rows":len(rows),
        "data_sha256":data_sha,"target_range":[401,cutoff],"target_count":len(observations),
        "prediction_records":len(prediction_rows),"random_bundles_per_target":random_count,
        "random_bundles_total":len(random_rows)*random_count,"random_baseline_executed":True,
        "training_cutoff_violations":training_violations,"leakage_failures":leakage_failures,
        "future_predictions":future_predictions,"no_future_leakage":True,
        "portfolio_geometry_violations":portfolio_violations,"random_geometry_violations":random_violations,
        "independent_research_axis":True,"independent_signal_family":True,"independent_sample":False,
        "parameter_search":False,"thresholds_changed":False,"alpha_changed":False,"block_length_changed":False,
        "comparator_changed":False,"historical_strict_gate_pass":historical_pass,"strict_portfolio_pass":False,
        "strict_pass_ready":False,"purchase_recommendation_generated":False,"manifest_entries":8,"manifest_status":"PASS",
        "completed_at_kst":completed}
    base.write_json(out/"VERIFICATION.json",verification)
    completion={"study_id":STUDY_ID,"status":"COMPLETE","data_cutoff":cutoff,"target_range":[401,cutoff],
        "target_count":len(observations),"historical_strict_gate_pass":historical_pass,"strict_portfolio_pass":False,
        "strict_pass_ready":False,"purchase_recommendation_generated":False,"manifest_entries":8,"completed_at_kst":completed}
    base.write_json(out/"COMPLETION.json",completion)
    report=["# "+STUDY_ID,"",f"- Historical cutoff: {cutoff}; targets: 401..{cutoff} ({len(observations)})",
        "- One frozen calendar-month Beta(6,39) estimator; no parameter search",
        f"- Random bundles: {len(random_rows)*random_count}; bootstrap: {reps}; block length: {block_size}",
        f"- Historical gate: {'PASS' if historical_pass else 'FAIL'}; STRICT_PASS_READY: NO (prospective rule unspecified)",
        "", "| Metric | Observed | Exact null | Delta | Adjusted CI |","|---|---:|---:|---:|---:|"]
    for m in METRICS:
        x=metric_results[m]; ci=x["adjusted_moving_block_ci"]
        report.append(f"| {m} | {x['observed_mean']:.6f} | {x['exact_geometry_matched_null']:.6f} | {x['delta_mean']:.6f} | [{ci[0]:.6f}, {ci[1]:.6f}] |")
    report += ["",f"Any2-positive blocks: {sum(x['any2_positive'] for x in blocks)}/{len(blocks)} ({block_share:.2%}); required 65%.",
        "","Historical exploratory evidence only; not an independent sample or prospective confirmation. No purchase lines or freeze/seal generated."]
    (out/"REPORT.md").write_text("\n".join(report)+"\n",encoding="utf-8")
    count=base.write_and_verify_manifest(out)
    if count!=8: raise AssertionError(f"Expected 8 manifest entries, got {count}")
    print(json.dumps({"status":"PASS","study_id":STUDY_ID,"data_cutoff":cutoff,"target_count":len(observations),
        "random_bundles_total":len(random_rows)*random_count,"historical_strict_gate_pass":historical_pass,
        "failed_gates":failed,"manifest_entries":count,"result_path":out.relative_to(ROOT).as_posix(),"strict_pass_ready":False},ensure_ascii=False))

def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--date",required=True); parser.add_argument("--run-id",required=True)
    args=parser.parse_args(); run(args.date,args.run_id)

if __name__=="__main__": main()
