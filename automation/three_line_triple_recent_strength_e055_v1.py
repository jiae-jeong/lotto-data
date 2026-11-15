#!/usr/bin/env python3
"""E055: falsify whether trailing any3 performance predicts the next 50-target block."""
from __future__ import annotations
import argparse,csv,hashlib,json,math,random,re,statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"automation/three_line_research_1251_v1.py"
POLICY=ROOT/"research/weekly_purchase/1251/THREE_LINE_POLICY_1251_PLUS.json"
PREREG=ROOT/"research/weekly_purchase/1251/E055_THREE_LINE_TRIPLE_RECENT_STRENGTH_PREREG_20261116.json"
SOURCE=ROOT/"analysis/2026-11-14/gha_43595251776_1/E045_CUTOFF_REFRESH_1250_APPEND_ONLY_v1"
STUDY="E055_THREE_LINE_TRIPLE_RECENT_STRENGTH_v1"
TRAILING=100
FORWARD=50
RANDOM_REPLICATES=120
SEED=20261116055
BOOTSTRAP_REPS=4000
BOOTSTRAP_BLOCKS=3

def load_base():
    import importlib.util
    spec=importlib.util.spec_from_file_location("e055_e045_reference",BASE)
    if spec is None or spec.loader is None: raise RuntimeError("Cannot load frozen E045 helpers")
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module

def pearson(x,y):
    if len(x)!=len(y) or len(x)<3: raise ValueError("Pearson inputs require equal length >=3")
    mx,my=statistics.mean(x),statistics.mean(y)
    dx=[a-mx for a in x]; dy=[b-my for b in y]
    denom=math.sqrt(sum(a*a for a in dx)*sum(b*b for b in dy))
    if denom==0: return 0.0
    return sum(a*b for a,b in zip(dx,dy))/denom

def block_specs():
    return [{"block_start_target":b,"block_end_target":b+FORWARD-1,
      "trailing_start_target":b-TRAILING,"trailing_end_target":b-1,
      "forward_start_target":b,"forward_end_target":b+FORWARD-1}
      for b in range(501,1251,FORWARD)]

def trailing_rate(values,start_index):
    if start_index<TRAILING: raise ValueError("Insufficient pre-target history")
    window=values[start_index-TRAILING:start_index]
    if len(window)!=TRAILING: raise AssertionError("Trailing window length mismatch")
    return statistics.mean(window)

def moving_block_corr_ci(pairs,replicates=BOOTSTRAP_REPS,block_length=BOOTSTRAP_BLOCKS,seed=SEED,alpha=0.05):
    if len(pairs)!=15 or block_length!=3: raise ValueError("E055 frozen bootstrap geometry changed")
    rng=random.Random(seed); values=[]; n=len(pairs)
    for _ in range(replicates):
        sample=[]
        while len(sample)<n:
            start=rng.randrange(0,n-block_length+1)
            sample.extend(pairs[start:start+block_length])
        sample=sample[:n]
        values.append(pearson([x for x,_ in sample],[y for _,y in sample]))
    values.sort()
    lo=int((alpha/2)*(replicates-1)); hi=int((1-alpha/2)*(replicates-1))
    return [values[lo],values[hi]]

def _normalize_csvs(folder):
    for path in folder.glob("*.csv"):
        raw=path.read_bytes()
        if raw.startswith(b"\xef\xbb\xbf"): raw=raw[3:]
        path.write_bytes(raw.replace(b"\r\n",b"\n"))

def verify_spec(pr):
    assert pr["study_id"]==STUDY and pr["date_kst"]=="2026-11-16"
    assert pr["historical_data_cutoff"]==1250 and pr["target_range"]==[401,1250] and pr["target_count"]==850
    assert pr["trailing_window_targets"]==100 and pr["forward_block_targets"]==50
    assert pr["evaluation_block_starts"]==list(range(501,1251,50))
    assert pr["random_trajectory_count"]==RANDOM_REPLICATES and pr["random_bundles_total"]==102000
    assert pr["bootstrap_replicates"]==BOOTSTRAP_REPS and pr["bootstrap_block_length_blocks"]==BOOTSTRAP_BLOCKS
    assert pr["alpha"]==0.05 and pr["parameter_search"] is False and pr["variants_evaluated"]==1
    assert pr["support_rule"]=="Pearson correlation > 0, 95% moving-block bootstrap lower bound > 0, and one-sided matched-random trajectory tail probability <= 0.05."
    assert pr["source_data_sha256"]=="7203238dae69ce281c59e6a0928cc187b11d88ed342685cd2dd2f214f063b3c2"
    assert pr["source_prediction_sha256"]=="585ec30a6d51f7bb02b00c8497e30ec47caac8527b7baf8d6781e7017d09ca04"
    assert pr["source_prediction_path"]=="analysis/2026-11-14/gha_43595251776_1/E045_CUTOFF_REFRESH_1250_APPEND_ONLY_v1/PREDICTIONS.csv"
    assert pr["source_study_id"]=="E045_CUTOFF_REFRESH_1250_APPEND_ONLY_v1"
    assert pr["source_verification_status"]=="PASS" and pr["source_completion_status"]=="COMPLETE"

def run(date,run_id):
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}",date) or not re.fullmatch(r"[A-Za-z0-9_-]+",run_id):
        raise ValueError("Unsafe date/run id")
    pr=json.loads(PREREG.read_text(encoding="utf-8")); verify_spec(pr)
    policy=json.loads(POLICY.read_text(encoding="utf-8"))
    base=load_base()
    cutoff=1250
    draws,prefix_sha,data_sha,rows=base.load_frozen_draw_prefix(cutoff,pr["source_data_sha256"],pr["source_data_sha256"])
    if rows!=cutoff or len(draws)!=cutoff: raise ValueError("E055 requires canonical rounds 1..1250")
    pred_path=SOURCE/"PREDICTIONS.csv"
    if hashlib.sha256(pred_path.read_bytes()).hexdigest()!=pr["source_prediction_sha256"]:
        raise ValueError("Frozen E045 prediction SHA256 mismatch")
    source_rows=list(csv.DictReader(pred_path.open(encoding="utf-8-sig",newline="")))
    if len(source_rows)!=850: raise AssertionError("E045 source prediction count mismatch")
    model_any3=[]; model_rows=[]; random_trajectories=[[0]*850 for _ in range(RANDOM_REPLICATES)]
    model_geometry_violations=0; random_geometry_violations=0; cutoff_violations=0
    for index,row in enumerate(source_rows):
        target=int(row["target_round"])
        if target!=401+index or int(row["training_through_round"])!=target-1:
            cutoff_violations+=1; raise AssertionError(f"E045 source cutoff violation at {target}")
        lines=[tuple(sorted(int(n) for n in row[f"line{i}"].split())) for i in (1,2,3)]
        actual=set(draws[target-1]["nums"])
        recorded=set(int(n) for n in row["actual_numbers"].split())
        if actual!=recorded: raise AssertionError(f"E045 actual outcome differs from canonical data at {target}")
        if len(set().union(*(set(x) for x in lines)))!=18 or any(set(lines[i])&set(lines[j]) for i in range(3) for j in range(i+1,3)):
            model_geometry_violations+=1; raise AssertionError(f"E045 model geometry violation at {target}")
        metrics=base.portfolio_metrics(lines,actual)
        if int(row["any3"])!=metrics["any3"] or int(row["max_hits"])!=metrics["max_hits"]:
            raise AssertionError(f"E045 any3 outcome does not reproduce at {target}")
        model_any3.append(int(metrics["any3"]))
        model_rows.append({"target_round":target,"training_through_round":target-1,"any3":int(metrics["any3"]),
          "max_hits":int(metrics["max_hits"]),"line1":" ".join(map(str,lines[0])),"line2":" ".join(map(str,lines[1])),
          "line3":" ".join(map(str,lines[2])),"actual_numbers":" ".join(map(str,sorted(actual)))})
        for rep in range(RANDOM_REPLICATES):
            rng=random.Random(SEED+rep*1000003+target)
            random_lines=base.permute_portfolio_labels(lines,rng)
            random_union=set().union(*(set(x) for x in random_lines))
            if len(random_union)!=18 or any(set(random_lines[i])&set(random_lines[j]) for i in range(3) for j in range(i+1,3)):
                random_geometry_violations+=1; raise AssertionError(f"E055 random geometry violation at {target}")
            random_trajectories[rep][index]=int(base.portfolio_metrics(random_lines,actual)["any3"])
    specs=block_specs()
    if len(specs)!=15: raise AssertionError("E055 must contain exactly 15 forward blocks")
    model_pairs=[]; block_rows=[]
    for spec in specs:
        start=spec["block_start_target"]-401
        trailing=model_any3[start-TRAILING:start]
        forward=model_any3[start:start+FORWARD]
        if len(trailing)!=100 or len(forward)!=50: raise AssertionError("E055 model block window length mismatch")
        tr=statistics.mean(trailing); fr=statistics.mean(forward)
        model_pairs.append((tr,fr))
        block_rows.append({**spec,"trailing_any3_count":sum(trailing),"trailing_any3_rate":tr,
          "forward_any3_count":sum(forward),"forward_any3_rate":fr})
    model_corr=pearson([x for x,_ in model_pairs],[y for _,y in model_pairs])
    random_corrs=[]; random_rows=[]
    for rep,trajectory in enumerate(random_trajectories):
        pairs=[]
        for spec in specs:
            start=spec["block_start_target"]-401
            pairs.append((statistics.mean(trajectory[start-TRAILING:start]),statistics.mean(trajectory[start:start+FORWARD])))
        corr=pearson([x for x,_ in pairs],[y for _,y in pairs])
        random_corrs.append(corr)
        random_rows.append({"random_replicate":rep,"pearson_correlation":corr,
          "mean_trailing_any3_rate":statistics.mean(x for x,_ in pairs),
          "mean_forward_any3_rate":statistics.mean(y for _,y in pairs)})
    ci=moving_block_corr_ci(model_pairs)
    sorted_null=sorted(random_corrs)
    null_mean=statistics.mean(sorted_null)
    null_q95=sorted_null[int(0.95*(len(sorted_null)-1))]
    tail=(1+sum(x>=model_corr for x in sorted_null))/(1+len(sorted_null))
    supported=bool(model_corr>0 and ci[0]>0 and tail<=0.05)
    status="PREDICTIVE_TRIPLE_STRENGTH_SUPPORTED" if supported else "PREDICTIVE_TRIPLE_STRENGTH_NOT_SUPPORTED"
    pred_rows=[]
    for index,row in enumerate(model_rows):
        if row["target_round"]>=501:
            trailing=model_any3[index-TRAILING:index]
            trailing_count=sum(trailing); trailing_value=statistics.mean(trailing)
        else:
            trailing_count=None; trailing_value=None
        pred_rows.append({**row,"trailing100_any3_count":trailing_count,"trailing100_any3_rate":trailing_value,
          "random_mean_any3":statistics.mean(random_trajectories[r][index] for r in range(RANDOM_REPLICATES))})
    for block,row in zip(specs,block_rows):
        start=block["block_start_target"]-401
        row["random_mean_trailing_any3_rate"]=statistics.mean(statistics.mean(random_trajectories[r][start-TRAILING:start]) for r in range(RANDOM_REPLICATES))
        row["random_mean_forward_any3_rate"]=statistics.mean(statistics.mean(random_trajectories[r][start:start+FORWARD]) for r in range(RANDOM_REPLICATES))
    folder=ROOT/"analysis"/date/run_id/STUDY
    folder.mkdir(parents=True,exist_ok=False)
    base.write_csv(folder/"PREDICTIONS.csv",pred_rows,list(pred_rows[0]))
    base.write_csv(folder/"BLOCKS.csv",block_rows,list(block_rows[0]))
    base.write_csv(folder/"RANDOM_TRAJECTORY_CORRELATIONS.csv",random_rows,list(random_rows[0]))
    _normalize_csvs(folder)
    source_paths=[PREREG,POLICY,BASE,pred_path,SOURCE/"SHA256_MANIFEST.csv",SOURCE/"COMPLETION.json",SOURCE/"VERIFICATION.json",Path(__file__).resolve()]
    source_hashes={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths}
    base.write_json(folder/"MODEL_SPEC.json",{"study_id":STUDY,"hypothesis":pr["hypothesis"],"statistic":pr["statistic"],
      "trailing_window_targets":TRAILING,"forward_block_targets":FORWARD,"evaluation_blocks":specs,
      "random_trajectory_count":RANDOM_REPLICATES,"random_seed_rule":"20261116055 + replicate*1000003 + target_round",
      "bootstrap_replicates":BOOTSTRAP_REPS,"bootstrap_block_length_blocks":BOOTSTRAP_BLOCKS,
      "alpha":0.05,"parameter_search":False,"variants_evaluated":1,"source_hashes":source_hashes})
    inference={"study_id":STUDY,"evidence_class":"HISTORICAL_PREDICTIVE_FALSIFICATION_NOT_PURCHASE_READINESS",
      "data_cutoff":1250,"target_range":[401,1250],"targets":850,"evaluation_blocks":len(specs),
      "trailing_window_targets":TRAILING,"forward_block_targets":FORWARD,"random_trajectory_count":RANDOM_REPLICATES,
      "random_bundles_total":RANDOM_REPLICATES*850,"model_pearson_correlation":model_corr,
      "model_correlation_moving_block_ci":ci,"bootstrap_replicates":BOOTSTRAP_REPS,
      "bootstrap_block_length_blocks":BOOTSTRAP_BLOCKS,"alpha":0.05,"random_mean_pearson_correlation":null_mean,
      "random_correlation_95th_percentile":null_q95,"random_one_sided_tail_probability":tail,
      "random_correlation_min":min(sorted_null),"random_correlation_max":max(sorted_null),
      "predictive_signal_supported":supported,"predictive_signal_status":status,
      "model_mean_trailing_any3_rate":statistics.mean(x for x,_ in model_pairs),
      "model_mean_forward_any3_rate":statistics.mean(y for _,y in model_pairs),
      "exact_geometry_matched_null_any3":float(policy["exact_null"]["p_any3"]),
      "strict_portfolio_pass":False,"strict_pass_ready":False,"purchase_recommendation_generated":False,
      "parameter_search":False,"variants_evaluated":1}
    base.write_json(folder/"INFERENCE.json",inference)
    verification={"status":"PASS","study_id":STUDY,"data_cutoff":1250,"data_sha256":data_sha,
      "source_prediction_sha256":pr["source_prediction_sha256"],"source_prediction_records":len(source_rows),
      "target_range":[401,1250],"target_count":850,"evaluation_blocks":len(specs),"block_count":len(specs),
      "random_trajectory_count":RANDOM_REPLICATES,"random_bundles_total":RANDOM_REPLICATES*850,
      "bootstrap_replicates":BOOTSTRAP_REPS,"bootstrap_block_length_blocks":BOOTSTRAP_BLOCKS,
      "training_cutoff_violations":cutoff_violations,"leakage_failures":0,
      "portfolio_geometry_violations":model_geometry_violations,"random_geometry_violations":random_geometry_violations,
      "no_future_leakage":True,"random_baseline_executed":True,"parameter_search":False,
      "strict_portfolio_pass":False,"strict_pass_ready":False,"purchase_recommendation_generated":False,
      "source_hashes":source_hashes}
    base.write_json(folder/"VERIFICATION.json",verification)
    completion={"study_id":STUDY,"status":"COMPLETE","data_cutoff":1250,"target_range":[401,1250],
      "target_count":850,"evaluation_blocks":15,"predictive_signal_supported":supported,
      "predictive_signal_status":status,"strict_portfolio_pass":False,"strict_pass_ready":False,
      "evidence_class":"HISTORICAL_PREDICTIVE_FALSIFICATION_NOT_PURCHASE_READINESS",
      "purchase_recommendation_generated":False}
    base.write_json(folder/"COMPLETION.json",completion)
    report=["# E055 — Triple recent-strength falsification","",f"- Result: **{status}**",
      "- Source: frozen E045 target-1251 three-line predictions, cutoff 1250; this does not alter E045.",
      "- Predictive question: does the previous 100-target any3 rate predict the next non-overlapping 50-target any3 rate?",
      "- Evaluation blocks: 15 (targets 501–1250); each trailing window ends at block_start−1.",
      "- Random comparator: 120 full geometry-matched random trajectories, 102,000 random portfolios total.",
      "- Correlation statistic: Pearson; one predeclared test, alpha 0.05.",
      "- Uncertainty: 4,000 moving-block bootstrap replicates, block length 3 adjacent 50-target block-pairs.","",
      f"- Model Pearson correlation: **{model_corr:+.6f}**",
      f"- 95% moving-block bootstrap CI: **[{ci[0]:+.6f}, {ci[1]:+.6f}]**",
      f"- Random mean correlation: **{null_mean:+.6f}**",
      f"- Random 95th percentile: **{null_q95:+.6f}**",
      f"- One-sided random tail probability: **{tail:.4f}**",
      f"- Predeclared support rule: **{'PASS' if supported else 'FAIL'}**",
      "- No model selection, ticket generation, purchase recommendation, or STRICT_PASS_READY.","",
      "| Block start | Trailing 100 any3 rate | Forward 50 any3 rate | Random trailing mean | Random forward mean |",
      "|---:|---:|---:|---:|---:|"]
    for row in block_rows:
        report.append(f"| {row['block_start_target']} | {row['trailing_any3_rate']:.4%} | {row['forward_any3_rate']:.4%} | {row['random_mean_trailing_any3_rate']:.4%} | {row['random_mean_forward_any3_rate']:.4%} |")
    report.extend(["","This is a historical falsification diagnostic. A positive result would not establish prospective purchase readiness; the existing strict gate and prospective confirmation requirement remain unchanged."])
    (folder/"REPORT.md").write_text("\n".join(report)+"\n",encoding="utf-8")
    entries=base.write_and_verify_manifest(folder); _normalize_csvs(folder)
    if entries!=8: raise AssertionError(f"E055 manifest entries {entries} != 8")
    return {"status":"COMPLETE","study_id":STUDY,"result_path":folder.relative_to(ROOT).as_posix(),
      "data_cutoff":1250,"target_count":850,"evaluation_blocks":15,"random_trajectory_count":120,
      "random_bundles_total":102000,"model_correlation":model_corr,"bootstrap_ci":ci,
      "random_tail_probability":tail,"predictive_signal_supported":supported,
      "predictive_signal_status":status,"strict_pass_ready":False,"manifest_entries":entries}

def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--date",required=True); parser.add_argument("--run-id",required=True)
    args=parser.parse_args(); print(json.dumps(run(args.date,args.run_id),ensure_ascii=False,indent=2))

if __name__=="__main__": main()
