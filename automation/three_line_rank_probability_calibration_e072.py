#!/usr/bin/env python3
"""Frozen E072 candidate-rank probability calibration; never emits purchase lines."""
from __future__ import annotations
import argparse, bisect, csv, hashlib, json, math, random, statistics, subprocess
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA_PATH=ROOT/"lotto_data.csv"
PREREG_PATH=ROOT/"research/weekly_purchase/1251/E072_THREE_LINE_RANK_PROBABILITY_CALIBRATION_PREREG_20261118.json"
EXPECTED_DATA_SHA256="7203238dae69ce281c59e6a0928cc187b11d88ed342685cd2dd2f214f063b3c2"
EXPECTED_DATA_BLOB_SHA1="66431d711919f179e4cb1349e2f7295c68a8735e"
EXPECTED_FEATURE_SCRIPT_BLOB_SHA1="88bf52cb2918da8aeecdac60e3b63fc1f180a8de"
STUDY_ID="E072_THREE_LINE_RANK_PROBABILITY_CALIBRATION_v1"
TRAIN_START,TRAIN_END=201,600
TEST_START,TEST_END=601,1250
BASE_RATE=6/45
PRIOR_STRENGTH=45
BINS=5
RANDOM_PERMUTATIONS_PER_TARGET=120
RANDOM_SEED=20261118072
BOOTSTRAP_REPLICATES=4000
BLOCK_LENGTH=50
FAMILY_ALPHA=0.05
ALPHA_PER_METRIC=FAMILY_ALPHA/2


def _zscore(vals):
    xs=list(vals.values())
    mean=statistics.mean(xs)
    sd=statistics.pstdev(xs) or 1.0
    return {k:(v-mean)/sd for k,v in vals.items()}


def features(draws):
    """Same fixed consensus formula as candidate_recall_v1.py."""
    f30=Counter(n for d in draws[-30:] for n in d)
    f10=Counter(n for d in draws[-10:] for n in d)
    fprev20=Counter(n for d in draws[-30:-10] for n in d)
    gaps={}
    for n in range(1,46):
        gap=0
        for draw in reversed(draws):
            if n in draw: break
            gap+=1
        gaps[n]=gap
    recent30=_zscore({n:f30[n] for n in range(1,46)})
    gap=_zscore(gaps)
    momentum=_zscore({n:f10[n]/10-fprev20[n]/20 for n in range(1,46)})
    balanced={n:(recent30[n]+gap[n])/2 for n in range(1,46)}
    contrarian={n:(-recent30[n]+gap[n])/2 for n in range(1,46)}
    consensus={n:statistics.mean((recent30[n],gap[n],momentum[n],balanced[n],contrarian[n])) for n in range(1,46)}
    return {"consensus":consensus}


def load_draws(path):
    raw=path.read_bytes()
    digest=hashlib.sha256(raw).hexdigest()
    rows=[]
    with path.open("r",encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f)
        required=["round","no1","no2","no3","no4","no5","no6","bonus"]
        if reader.fieldnames is None or any(x not in reader.fieldnames for x in required):
            raise ValueError("canonical CSV header mismatch")
        for row in reader:
            if not row.get("round","").strip(): continue
            nums=[int(row[f"no{i}"]) for i in range(1,7)]
            bonus=int(row["bonus"]); rnd=int(row["round"])
            if len(set(nums))!=6 or any(n<1 or n>45 for n in nums): raise ValueError(f"invalid main numbers at {rnd}")
            if bonus<1 or bonus>45 or bonus in nums: raise ValueError(f"invalid bonus at {rnd}")
            rows.append({"round":rnd,"nums":tuple(nums),"bonus":bonus})
    rounds=[x["round"] for x in rows]
    if rounds!=list(range(1,len(rows)+1)): raise ValueError("round sequence not continuous")
    if len(rows)!=TEST_END: raise ValueError(f"expected {TEST_END} rows, got {len(rows)}")
    if digest!=EXPECTED_DATA_SHA256: raise ValueError(f"data SHA-256 mismatch: {digest}")
    return rows,digest


def current_blob_sha(path):
    return subprocess.check_output(["git","rev-parse",f"HEAD:{path}"],cwd=ROOT,text=True).strip()


def preflight():
    rows,digest=load_draws(DATA_PATH)
    data_blob=current_blob_sha("lotto_data.csv")
    feature_blob=current_blob_sha("automation/candidate_recall_v1.py")
    if data_blob!=EXPECTED_DATA_BLOB_SHA1: raise ValueError(f"data blob SHA mismatch: {data_blob}")
    if feature_blob!=EXPECTED_FEATURE_SCRIPT_BLOB_SHA1: raise ValueError(f"feature source blob mismatch: {feature_blob}")
    prereg=json.loads(PREREG_PATH.read_text(encoding="utf-8"))
    if prereg.get("study_id")!=STUDY_ID or prereg.get("preregistration_status")!="FROZEN_BEFORE_EXECUTION": raise ValueError("preregistration identity/status mismatch")
    if prereg.get("training_targets")!=[TRAIN_START,TRAIN_END] or prereg.get("evaluation_targets")!=[TEST_START,TEST_END]: raise ValueError("frozen target split mismatch")
    if prereg.get("calibration",{}).get("bins")!=BINS or prereg.get("calibration",{}).get("prior_strength")!=PRIOR_STRENGTH: raise ValueError("frozen calibration parameters mismatch")
    if prereg.get("random_comparator",{}).get("permutations_per_target")!=RANDOM_PERMUTATIONS_PER_TARGET: raise ValueError("frozen random comparator mismatch")
    if prereg.get("inference",{}).get("bootstrap_replicates")!=BOOTSTRAP_REPLICATES or prereg.get("inference",{}).get("block_length_targets")!=BLOCK_LENGTH: raise ValueError("frozen inference parameters mismatch")
    return {"data_rows":len(rows),"data_sha256":digest,"data_blob_sha1":data_blob,"feature_script_blob_sha1":feature_blob}


def quantile_cutpoints(scores,bins=BINS):
    ordered=sorted(scores)
    if not ordered: raise ValueError("empty training scores")
    return [ordered[max(0,math.ceil(k*len(ordered)/bins)-1)] for k in range(1,bins)]


def assign_bin(score,cutpoints):
    return bisect.bisect_right(cutpoints,score)


def fit_bin_probabilities(scores,labels,cutpoints):
    counts=[0]*BINS; hits=[0]*BINS
    for score,label in zip(scores,labels):
        b=assign_bin(score,cutpoints); counts[b]+=1; hits[b]+=int(label)
    probs=[(hits[b]+PRIOR_STRENGTH*BASE_RATE)/(counts[b]+PRIOR_STRENGTH) for b in range(BINS)]
    return probs,counts,hits


def _logit(p):
    p=min(max(p,1e-12),1-1e-12)
    return math.log(p/(1-p))


def _sigmoid(x):
    if x>=0:
        z=math.exp(-x); return 1/(1+z)
    z=math.exp(x); return z/(1+z)


def normalize_to_expected_six(probabilities):
    if len(probabilities)!=45: raise ValueError("expected 45 probabilities")
    logits=[_logit(p) for p in probabilities]
    lo,hi=-30.0,30.0
    for _ in range(90):
        mid=(lo+hi)/2
        if sum(_sigmoid(x+mid) for x in logits)<6: lo=mid
        else: hi=mid
    shift=(lo+hi)/2
    out=[_sigmoid(x+shift) for x in logits]
    if abs(sum(out)-6)>1e-9: raise ArithmeticError("expected-six normalization failed")
    return out


def losses(probabilities,labels):
    if len(probabilities)!=45 or len(labels)!=45: raise ValueError("loss requires 45 candidates")
    eps=1e-12
    brier=statistics.mean((p-y)**2 for p,y in zip(probabilities,labels))
    logloss=statistics.mean(-(y*math.log(max(eps,p))+(1-y)*math.log(max(eps,1-p))) for p,y in zip(probabilities,labels))
    return brier,logloss


def moving_block_ci(values,seed,reps=BOOTSTRAP_REPLICATES,block_length=BLOCK_LENGTH,alpha=ALPHA_PER_METRIC):
    n=len(values)
    if n<block_length: raise ValueError("not enough targets for frozen block length")
    rng=random.Random(seed); blocks=math.ceil(n/block_length); means=[]
    for _ in range(reps):
        sample=[]
        for _ in range(blocks):
            start=rng.randrange(0,n-block_length+1)
            sample.extend(values[start:start+block_length])
        means.append(statistics.mean(sample[:n]))
    means.sort()
    lo=max(0,min(reps-1,math.floor((alpha/2)*(reps-1))))
    hi=max(0,min(reps-1,math.ceil((1-alpha/2)*(reps-1))))
    return {"lower":means[lo],"upper":means[hi],"replicates":reps,"block_length":block_length,"alpha_two_sided":alpha,"sample_targets":n}


def write_csv(path,rows,fields):
    with path.open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)


def build_study(rows,data_sha256,run_date,run_id):
    draws=[list(r["nums"]) for r in rows]; rounds=[r["round"] for r in rows]
    train_scores=[]; train_labels=[]; train_cutoff_violations=0
    for target in range(TRAIN_START,TRAIN_END+1):
        idx=target-1; score_map=features(draws[:idx])["consensus"]; actual=set(draws[idx])
        if rounds[idx-1]!=target-1: train_cutoff_violations+=1
        for n in range(1,46):
            train_scores.append(float(score_map[n])); train_labels.append(int(n in actual))
    cuts=quantile_cutpoints(train_scores)
    bin_probs,train_counts,train_hits=fit_bin_probabilities(train_scores,train_labels,cuts)
    outdir=ROOT/"analysis"/run_date/run_id/STUDY_ID
    outdir.mkdir(parents=True,exist_ok=False)
    predictions=[]; target_rows=[]
    test_counts=[0]*BINS; test_hits=[0]*BINS; test_prob_sums=[0.0]*BINS
    d_brier_u=[]; d_log_u=[]; d_brier_r=[]; d_log_r=[]
    all_random_brier=[]; all_random_log=[]; feature_cutoff_violations=0
    for target in range(TEST_START,TEST_END+1):
        idx=target-1; score_map=features(draws[:idx])["consensus"]; actual=set(draws[idx])
        labels=[int(n in actual) for n in range(1,46)]
        bins=[assign_bin(float(score_map[n]),cuts) for n in range(1,46)]
        raw=[bin_probs[b] for b in bins]; probs=normalize_to_expected_six(raw)
        if rounds[idx-1]!=target-1: feature_cutoff_violations+=1
        for n in range(1,46):
            b=bins[n-1]; test_counts[b]+=1; test_hits[b]+=labels[n-1]; test_prob_sums[b]+=probs[n-1]
            predictions.append({"target_round":target,"feature_history_through_round":target-1,"calibrator_trained_through_round":TRAIN_END,"number":n,"consensus_score":f"{float(score_map[n]):.12g}","calibration_bin":b,"probability_before_expected_six_normalization":f"{raw[n-1]:.12g}","probability_after_expected_six_normalization":f"{probs[n-1]:.12g}","main_number_inclusion":labels[n-1]})
        mb,ml=losses(probs,labels); ub,ul=losses([BASE_RATE]*45,labels)
        rng=random.Random(RANDOM_SEED+target); rb=[]; rl=[]
        for _ in range(RANDOM_PERMUTATIONS_PER_TARGET):
            x,y=losses(rng.sample(probs,len(probs)),labels); rb.append(x); rl.append(y)
        rmb,rml=statistics.mean(rb),statistics.mean(rl)
        d_brier_u.append(mb-ub); d_log_u.append(ml-ul); d_brier_r.append(mb-rmb); d_log_r.append(ml-rml)
        all_random_brier.extend(rb); all_random_log.extend(rl)
        target_rows.append({"target_round":target,"feature_history_through_round":target-1,"calibrator_trained_through_round":TRAIN_END,"model_brier":mb,"uniform_brier":ub,"delta_brier_vs_uniform":mb-ub,"random_permutation_brier_mean":rmb,"delta_brier_vs_random":mb-rmb,"model_log_loss":ml,"uniform_log_loss":ul,"delta_log_loss_vs_uniform":ml-ul,"random_permutation_log_loss_mean":rml,"delta_log_loss_vs_random":ml-rml,"random_permutations":RANDOM_PERMUTATIONS_PER_TARGET})
    bci=moving_block_ci(d_brier_u,RANDOM_SEED+1); lci=moving_block_ci(d_log_u,RANDOM_SEED+2)
    brci=moving_block_ci(d_brier_r,RANDOM_SEED+3); lrci=moving_block_ci(d_log_r,RANDOM_SEED+4)
    passed=bci["upper"]<0 and lci["upper"]<0
    bins=[]
    for b in range(BINS):
        bins.append({"calibration_bin":b,"score_lower_exclusive":cuts[b-1] if b>0 else "-inf","score_upper_inclusive":cuts[b] if b<BINS-1 else "+inf","training_candidates":train_counts[b],"training_hits":train_hits[b],"training_empirical_rate":train_hits[b]/train_counts[b] if train_counts[b] else None,"training_smoothed_probability":bin_probs[b],"test_candidates":test_counts[b],"test_hits":test_hits[b],"test_empirical_rate":test_hits[b]/test_counts[b] if test_counts[b] else None,"test_mean_normalized_probability":test_prob_sums[b]/test_counts[b] if test_counts[b] else None})
    inference={"study_id":STUDY_ID,"evidence_class":"HISTORICAL_CANDIDATE_PROBABILITY_CALIBRATION_NOT_THREE_LINE_PORTFOLIO_CONFIRMATION","data_cutoff":TEST_END,"training_targets":[TRAIN_START,TRAIN_END],"evaluation_targets":[TEST_START,TEST_END],"training_candidate_observations":len(train_scores),"evaluation_targets":len(target_rows),"evaluation_candidate_observations":len(predictions),"random_permutations_per_target":RANDOM_PERMUTATIONS_PER_TARGET,"random_permutations_total":len(target_rows)*RANDOM_PERMUTATIONS_PER_TARGET,"metrics":{"brier":{"model_mean":statistics.mean(x["model_brier"] for x in target_rows),"uniform_mean":statistics.mean(x["uniform_brier"] for x in target_rows),"delta_model_minus_uniform":statistics.mean(d_brier_u),"adjusted_moving_block_ci_vs_uniform":bci,"random_permutation_mean":statistics.mean(all_random_brier),"delta_model_minus_random":statistics.mean(d_brier_r),"adjusted_moving_block_ci_vs_random":brci,"improvement_supported_vs_uniform":bci["upper"]<0},"log_loss":{"model_mean":statistics.mean(x["model_log_loss"] for x in target_rows),"uniform_mean":statistics.mean(x["uniform_log_loss"] for x in target_rows),"delta_model_minus_uniform":statistics.mean(d_log_u),"adjusted_moving_block_ci_vs_uniform":lci,"random_permutation_mean":statistics.mean(all_random_log),"delta_model_minus_random":statistics.mean(d_log_r),"adjusted_moving_block_ci_vs_random":lrci,"improvement_supported_vs_uniform":lci["upper"]<0}},"family_alpha":FAMILY_ALPHA,"alpha_per_metric":ALPHA_PER_METRIC,"bootstrap_replicates":BOOTSTRAP_REPLICATES,"block_length_targets":BLOCK_LENGTH,"calibration_gate_pass":passed,"strict_portfolio_pass":False,"strict_pass_ready":False,"target_1251_three_line_readiness_eligible":False,"purchase_recommendation_generated":False,"thresholds_or_policy_changed":False,"parameter_search":False,"variants_evaluated":1}
    model_spec={"study_id":STUDY_ID,"preregistration":PREREG_PATH.relative_to(ROOT).as_posix(),"feature_source":"automation/candidate_recall_v1.py::features(draws)['consensus']","feature_source_blob_sha1":EXPECTED_FEATURE_SCRIPT_BLOB_SHA1,"score_definition":"mean(recent30_z, gap_z, momentum_z, balanced_z, contrarian_z)","training_targets":[TRAIN_START,TRAIN_END],"evaluation_targets":[TEST_START,TEST_END],"binning":{"method":"nearest-rank empirical quintiles of training candidate scores","cutpoints":cuts,"tie_rule":"bisect_right; equality enters higher bin"},"smoothing":{"prior_mean":BASE_RATE,"prior_strength":PRIOR_STRENGTH,"formula":"(bin_hits + 6) / (bin_exposures + 45)"},"normalization":"Per target, add one logit intercept shared by all 45 probabilities until their sum equals exactly six.","random_comparator":{"method":"120 uniform random permutations of the 45 calibrated probabilities per target; outcome and probability multiset held fixed","seed":RANDOM_SEED},"uniform_baseline":"Exact Bernoulli marginal inclusion probability 6/45 for each of 45 numbers.","inference":{"primary_metrics":["Brier","log loss"],"family_alpha":FAMILY_ALPHA,"alpha_per_metric":ALPHA_PER_METRIC,"bootstrap":"two-sided percentile moving-block bootstrap; 50-target blocks; 4000 replicates"},"independent_research_axis":True,"independent_sample":False,"historical_exploration_only":True,"strict_portfolio_readiness_eligible":False}
    report=f"""# E072 — Candidate consensus-rank probability calibration

Status: **{'HISTORICAL_CALIBRATION_PASS' if passed else 'HISTORICAL_CALIBRATION_NO_EDGE'}**

- Frozen calibration window: targets {TRAIN_START}–{TRAIN_END} ({len(train_scores):,} candidate observations).
- Untouched chronological evaluation: targets {TEST_START}–{TEST_END} ({len(target_rows):,} targets; {len(predictions):,} candidate observations).
- Calibration: five training-score quintile bins, Beta-binomial prior mean 6/45 and strength 45, then per-target probability normalization to six expected inclusions.
- Random control: {RANDOM_PERMUTATIONS_PER_TARGET} probability-vector permutations per target ({len(target_rows)*RANDOM_PERMUTATIONS_PER_TARGET:,} total).
- Bootstrap: {BOOTSTRAP_REPLICATES:,} moving-block replicates, block length {BLOCK_LENGTH}, Bonferroni alpha {ALPHA_PER_METRIC:.4f} per primary metric.

| Metric | Model | Exact uniform | Model − uniform | Adjusted CI | Random permutation |
|---|---:|---:|---:|---:|---:|
| Brier (lower better) | {inference['metrics']['brier']['model_mean']:.8f} | {inference['metrics']['brier']['uniform_mean']:.8f} | {inference['metrics']['brier']['delta_model_minus_uniform']:.8f} | [{bci['lower']:.8f}, {bci['upper']:.8f}] | {inference['metrics']['brier']['random_permutation_mean']:.8f} |
| Log loss (lower better) | {inference['metrics']['log_loss']['model_mean']:.8f} | {inference['metrics']['log_loss']['uniform_mean']:.8f} | {inference['metrics']['log_loss']['delta_model_minus_uniform']:.8f} | [{lci['lower']:.8f}, {lci['upper']:.8f}] | {inference['metrics']['log_loss']['random_permutation_mean']:.8f} |

Calibration gate: **{'PASS' if passed else 'FAIL'}**. Both adjusted CI upper bounds must be strictly below zero.

This is candidate-probability calibration, not a three-line portfolio evaluation. It cannot qualify STRICT_PASS_READY and emits no purchase lines. The evaluation window is historical, not an independent future sample. No strict thresholds, alpha levels, block lengths, or portfolio comparators were changed.
"""
    write_csv(outdir/"PREDICTIONS.csv",predictions,["target_round","feature_history_through_round","calibrator_trained_through_round","number","consensus_score","calibration_bin","probability_before_expected_six_normalization","probability_after_expected_six_normalization","main_number_inclusion"])
    write_csv(outdir/"TARGET_METRICS.csv",target_rows,list(target_rows[0].keys()))
    write_csv(outdir/"CALIBRATION_BINS.csv",bins,list(bins[0].keys()))
    (outdir/"MODEL_SPEC.json").write_text(json.dumps(model_spec,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (outdir/"INFERENCE.json").write_text(json.dumps(inference,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (outdir/"REPORT.md").write_text(report,encoding="utf-8")
    completion={"study_id":STUDY_ID,"status":"COMPLETE","data_cutoff":TEST_END,"training_targets":400,"evaluation_targets":650,"calibration_gate_pass":passed,"strict_portfolio_pass":False,"strict_pass_ready":False,"purchase_recommendation_generated":False}
    (outdir/"COMPLETION.json").write_text(json.dumps(completion,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    verification={"status":"PASS","study_id":STUDY_ID,"data_cutoff":TEST_END,"data_rows":len(rows),"data_sha256":data_sha256,"data_blob_sha1":EXPECTED_DATA_BLOB_SHA1,"feature_source_blob_sha1":EXPECTED_FEATURE_SCRIPT_BLOB_SHA1,"training_targets":[TRAIN_START,TRAIN_END],"evaluation_targets":[TEST_START,TEST_END],"training_candidate_observations":len(train_scores),"evaluation_targets_count":len(target_rows),"evaluation_candidate_observations":len(predictions),"random_permutations_total":len(target_rows)*RANDOM_PERMUTATIONS_PER_TARGET,"feature_cutoff_violations":feature_cutoff_violations,"training_feature_cutoff_violations":train_cutoff_violations,"future_predictions":0,"calibrator_uses_evaluation_outcomes":False,"leakage_failures":0,"calibration_gate_pass":passed,"strict_portfolio_pass":False,"strict_pass_ready":False,"purchase_recommendation_generated":False,"manifest_entries":8,"manifest_status":"PASS"}
    (outdir/"VERIFICATION.json").write_text(json.dumps(verification,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    expected=["CALIBRATION_BINS.csv","COMPLETION.json","INFERENCE.json","MODEL_SPEC.json","PREDICTIONS.csv","REPORT.md","TARGET_METRICS.csv","VERIFICATION.json"]
    manifest=[]
    for name in expected:
        raw=(outdir/name).read_bytes()
        manifest.append({"path":name,"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)})
    write_csv(outdir/"SHA256_MANIFEST.csv",manifest,["path","sha256","bytes"])
    for item in manifest:
        raw=(outdir/item["path"]).read_bytes()
        if len(raw)!=item["bytes"] or hashlib.sha256(raw).hexdigest()!=item["sha256"]: raise ValueError(f"manifest mismatch: {item['path']}")
    if train_cutoff_violations or feature_cutoff_violations or len(predictions)!=650*45 or len(all_random_brier)!=650*RANDOM_PERMUTATIONS_PER_TARGET: raise ValueError("E072 cutoff/count verification failed")
    return outdir,inference


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--preflight",action="store_true")
    parser.add_argument("--date",default="2026-11-18")
    parser.add_argument("--run-id",default="local_e072")
    args=parser.parse_args()
    info=preflight()
    if args.preflight:
        print(json.dumps({"preflight":"PASS",**info},indent=2)); return
    rows,digest=load_draws(DATA_PATH)
    outdir,inference=build_study(rows,digest,args.date,args.run_id)
    print(json.dumps({"result_path":outdir.relative_to(ROOT).as_posix(),"calibration_gate_pass":inference["calibration_gate_pass"],"strict_pass_ready":False,"manifest_entries":8},indent=2))


if __name__=="__main__":
    main()
