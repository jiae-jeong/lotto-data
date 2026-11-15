#!/usr/bin/env python3
"""E056: isolated H005_FIX repair of S008's structure-to-number family mapping."""
from __future__ import annotations
import argparse,csv,hashlib,importlib.util,json,math,re,statistics,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FRAMEWORK=ROOT/"research/expansion_framework_v1"
SOURCE=FRAMEWORK/"studies/study_batch_001/run_batch.py"
DATA=ROOT/"lotto_data.csv"
REGISTRY=FRAMEWORK/"research_registry.csv"
PREREG=ROOT/"research/weekly_purchase/1251/E056_H005_FIX_STRUCTURE_TO_NUMBER_MAPPING_PREREG_20261116.json"
STUDY="E056_H005_FIX_STRUCTURE_TO_NUMBER_MAPPING_v1"
MODEL="h005_fix_family_balanced_hybrid"
COMPONENTS=("multi_window_frequency","gap_regime_hazard","momentum_state_transition","conditional_probability","pair_residual_node","triple_residual_node")
WINDOWS={
 "overall_201_1250":(201,1250),"recent200":(1051,1250),"recent100":(1151,1250),"recent50":(1201,1250),
 "block_201_500":(201,500),"block_501_800":(501,800),"block_801_1100":(801,1100),"block_1101_1250":(1101,1250)
}

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def load_source():
    sys.path.insert(0,str(FRAMEWORK))
    spec=importlib.util.spec_from_file_location("e056_frozen_study_batch_001",SOURCE)
    if spec is None or spec.loader is None: raise RuntimeError("Cannot import frozen Study Batch 001 source")
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    module.DATA=DATA; module.FRAMEWORK=FRAMEWORK; module.ROOT=ROOT
    module.BASE=module.exact_random_baseline()
    return module

def corrected_structure_vector(ticket):
    selected=set(int(n) for n in ticket)
    if len(selected)!=6 or any(n<1 or n>45 for n in selected): raise ValueError("S005 structure ticket must contain six unique numbers")
    vector=[45.0 if n in selected else 0.0 for n in range(1,46)]
    if sum(value==45.0 for value in vector)!=6 or sum(value==0.0 for value in vector)!=39:
        raise AssertionError("Corrected structure vector must be six 45s and thirty-nine zeros")
    return vector

def pearson_safe(a,b):
    if len(set(a))<2 or len(set(b))<2: return ""
    return statistics.correlation(a,b)

def _write_csv(path,rows):
    if not rows: raise ValueError(f"Refusing empty output {path.name}")
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

def _write_json(path,obj):
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def _manifest(folder):
    rows=[]
    for path in sorted(p for p in folder.iterdir() if p.is_file() and p.name!="SHA256_MANIFEST.csv"):
        raw=path.read_bytes()
        rows.append({"path":path.name,"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()})
    _write_csv(folder/"SHA256_MANIFEST.csv",rows)
    for row in rows:
        raw=(folder/row["path"]).read_bytes()
        if len(raw)!=row["bytes"] or hashlib.sha256(raw).hexdigest()!=row["sha256"]:
            raise AssertionError(f"E056 manifest mismatch: {row['path']}")
    return len(rows)

def run(date,run_id):
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}",date) or not re.fullmatch(r"[A-Za-z0-9_-]+",run_id):
        raise ValueError("Unsafe date/run id")
    prereg=json.loads(PREREG.read_text(encoding="utf-8"))
    if prereg["study_id"]!=STUDY or prereg["date_kst"]!=date or prereg["preregistration_status"]!="FROZEN_BEFORE_EXECUTION":
        raise ValueError("E056 preregistration identity/date/status mismatch")
    if prereg["data_cutoff"]!=1250 or prereg["target_range"]!=[201,1250] or prereg["target_count"]!=1050:
        raise ValueError("E056 cutoff/target range changed")
    if prereg["candidate_bank_seed"]!=20261008 or prereg["candidate_bank_size"]!=5000:
        raise ValueError("E056 candidate bank specification changed")
    if prereg["candidate_bank_sha256"]!="134724abb3f8930fbb3cf24499e537aa00ed9e49239dbb79029163d76a412220":
        raise ValueError("E056 candidate bank hash pin changed")
    if prereg["corrected_mapping"]!="One 45-dimensional family vector: 45 for each of the six numbers in the S005 structure ticket, 0 for the other 39; append this vector once to the six S001/S002/S003/S004/S006/S007 rank vectors and average seven families.":
        raise ValueError("E056 corrected mapping specification changed")
    if prereg["legacy_mapping_proof"]!="Legacy S008 appends 45 constant vectors (six [45]*45 and thirty-nine [0]*45) to six component-rank vectors, for 51 vectors total; the structure contribution is 270/51=5.2941176470588235 for every number and is therefore rank-constant.":
        raise ValueError("E056 legacy mapping proof changed")
    if prereg["parameter_search"] is not False or prereg["variants_evaluated"]!=1:
        raise ValueError("E056 variants/parameter search are not allowed")
    data_sha=sha(DATA)
    if data_sha!=prereg["data_sha256"]: raise ValueError("E056 source data SHA256 mismatch")
    if sha(SOURCE)!=prereg["source_run_batch_sha256"]: raise ValueError("E056 legacy source code hash mismatch")
    if sha(FRAMEWORK/"walkforward_core.py")!=prereg["walkforward_core_sha256"]: raise ValueError("E056 walkforward core hash mismatch")
    if sha(REGISTRY)!=prereg["research_registry_sha256"]: raise ValueError("E056 registry hash mismatch")
    registry=list(csv.DictReader(REGISTRY.open(encoding="utf-8-sig",newline="")))
    if any(row.get("research_id")=="H005_FIX" for row in registry): raise ValueError("H005_FIX already registered; refuse duplicate")
    mod=load_source()
    draws=mod.load_draws_through(DATA,1250)
    if len(draws)!=1250 or [d.round for d in draws]!=list(range(1,1251)):
        raise AssertionError("E056 source loader did not return canonical rounds 1..1250")
    bank=mod.candidate_bank()
    bank_payload=json.dumps([list(ticket) for ticket in bank],separators=(",",":")).encode()
    bank_sha=hashlib.sha256(bank_payload).hexdigest()
    if len(bank)!=5000 or bank_sha!=prereg["candidate_bank_sha256"]:
        raise AssertionError("E056 deterministic candidate bank size/hash mismatch")
    mod.BASE_PROFILES={ticket:mod.prof(ticket,()) for ticket in bank}
    original_make_models=mod.make_models
    legacy_mapping_checks=0
    def h005_make_models(train,bank_arg):
        nonlocal legacy_mapping_checks
        predictions=original_make_models(train,bank_arg)
        ranks=[mod.rank(predictions[name][1]) for name in COMPONENTS]
        structure_ticket=predictions["structure_transition"][0]
        vector=corrected_structure_vector(structure_ticket)
        legacy_expected=[(sum(rank[i] for rank in ranks)+270.0)/51.0 for i in range(45)]
        legacy_original=predictions["family_balanced_hybrid"][1]
        if any(abs(float(a)-float(b))>1e-10 for a,b in zip(legacy_original,legacy_expected)):
            raise AssertionError("Legacy S008 constant-contribution algebra did not reproduce")
        legacy_ticket=mod.top(legacy_expected)
        if tuple(legacy_ticket)!=tuple(predictions["family_balanced_hybrid"][0]):
            raise AssertionError("Legacy S008 ticket differs from its constant-mapping reconstruction")
        corrected=[(sum(rank[i] for rank in ranks)+vector[i])/7.0 for i in range(45)]
        if len(set(vector))!=2: raise AssertionError("Corrected structure vector is still constant")
        legacy_mapping_checks+=1
        return {
          MODEL:(mod.top(corrected),corrected),
          "legacy_s008_reference":(legacy_ticket,legacy_expected),
          "structure_transition":predictions["structure_transition"],
        }
    outdir=ROOT/"analysis"/date/run_id/STUDY
    outdir.mkdir(parents=True,exist_ok=False)
    rows=[]; score_memory={}; mapping_changes=0
    for target in range(201,1251):
        train=draws[:target-1]; actual=set(draws[target-1].numbers)
        predictions=h005_make_models(train,bank)
        record={"target_round":target,"training_start_round":1,"training_through_round":target-1,"window_mode":"expanding"}
        for key,label in ((MODEL,"H005_FIX"),("legacy_s008_reference","LEGACY_S008_REFERENCE"),("structure_transition","S005_STRUCTURE_TICKET")):
            ticket,scores=predictions[key]
            hits=len(set(ticket)&actual)
            record[f"{label.lower()}_numbers"]=" ".join(map(str,ticket))
            record[f"{label.lower()}_hits"]=hits
            score_memory[(key,target)]=scores
        record["mapping_changed"]=int(predictions[MODEL][0]!=predictions["legacy_s008_reference"][0])
        record["structure_vector_nonconstant"]=1
        record["structure_ticket_numbers"]=" ".join(map(str,predictions["structure_transition"][0]))
        record["h005_fix_score_sha256"]=hashlib.sha256(json.dumps([round(x,14) for x in predictions[MODEL][1]],separators=(",",":")).encode()).hexdigest()
        rows.append(record); mapping_changes+=record["mapping_changed"]
    if len(rows)!=1050 or legacy_mapping_checks!=1050: raise AssertionError("E056 walk-forward or legacy algebra check count mismatch")
    metrics=[]
    for key,label in ((MODEL,"H005_FIX"),("legacy_s008_reference","LEGACY_S008_REFERENCE"),("structure_transition","S005_STRUCTURE_TICKET")):
        for window,(lo,hi) in WINDOWS.items():
            hits=[int(row[f"{label.lower()}_hits"]) for row in rows if lo<=int(row["target_round"])<=hi]
            metrics.append({"model":label,"window":window,**mod.stats(hits),"classification":"HISTORICAL_DIAGNOSTIC_ONLY"})
    correlations=[]
    labels=[(MODEL,"H005_FIX"),("legacy_s008_reference","LEGACY_S008_REFERENCE"),("structure_transition","S005_STRUCTURE_TICKET")]
    for i,(a,la) in enumerate(labels):
        for b,lb in labels[i+1:]:
            ov=[];ha=[];hb=[]
            for row in rows:
                ta=set(map(int,row[f"{la.lower()}_numbers"].split()))
                tb=set(map(int,row[f"{lb.lower()}_numbers"].split()))
                ov.append(len(ta&tb));ha.append(int(row[f"{la.lower()}_hits"]));hb.append(int(row[f"{lb.lower()}_hits"]))
            sa=score_memory[(a,1250)];sb=score_memory[(b,1250)]
            correlations.append({"model_a":la,"model_b":lb,"n":len(rows),"mean_ticket_overlap":statistics.mean(ov),
              "hit_correlation":pearson_safe(ha,hb),"score_correlation_target1250":pearson_safe(sa,sb)})
    baseline=mod.BASE
    overall=next(x for x in metrics if x["model"]=="H005_FIX" and x["window"]=="overall_201_1250")
    recent=next(x for x in metrics if x["model"]=="H005_FIX" and x["window"]=="recent100")
    hold=next(x for x in metrics if x["model"]=="H005_FIX" and x["window"]=="recent50")
    reg_status="WEAK" if overall["delta_mean_vs_random"]<=0 or recent["delta_mean_vs_random"]<=0 or hold["delta_mean_vs_random"]<=0 else "HOLD"
    study_registry=[{
      "research_id":"H005_FIX","status":"HISTORICAL_DIAGNOSTIC_ONLY","hypothesis":"Correct S008's structure-to-number family mapping by adding one nonconstant 45/0 structure vector exactly once.",
      "model_family":"hybrid_structure_one_hot_fix","independence_group":"structure_family_mapping_repair",
      "data_path":"lotto_data.csv","data_sha256":data_sha,"round_range":"1-1250",
      "features":prereg["corrected_mapping"],"calculation_method":"Seven-family equal average: six unchanged component rank vectors plus one corrected S005 structure membership vector.",
      "train_cutoff_rule":"Each target t receives rounds 1..t-1 only.","validation_method":"Expanding 1-step walk-forward",
      "validation_rounds":"201-1250","holdout_rounds":"recent200/recent100/recent50 are descriptive post-hoc windows, not untouched holdout.",
      "random_baseline":"Exact hypergeometric C(6,k)C(39,6-k)/C(45,6).",
      "baseline_mean_hits":baseline["mean_hits"],"baseline_rate_ge_2":baseline["rate_ge_2"],"baseline_rate_ge_3":baseline["rate_ge_3"],
      "n_predictions":1050,"mean_hits":overall["mean_hits"],"rate_ge_2":overall["rate_ge_2"],"rate_ge_3":overall["rate_ge_3"],
      "multiple_testing_notes":"One frozen mapping, one model, no parameter search or variants; legacy S008 and S005 are reference-only diagnostics.",
      "selection_bias_notes":"Historical diagnostic; not prospective and not independent of existing component families.",
      "overfit_risk":"HIGH","independent_validation":"No prospective untouched draw.",
      "conclusion":reg_status,"next_research_direction":"Keep H005_FIX separate; require untouched prospective confirmation before any promotion."
    }]
    failure_rows=[]
    for row in metrics:
        failure_rows.append({"model":row["model"],"window":row["window"],"status":"WEAK" if row["delta_mean_vs_random"]<=0 else "HOLD",
          "mean_hits":row["mean_hits"],"baseline_mean":baseline["mean_hits"],"mean_delta":row["delta_mean_vs_random"],
          "rate_ge_2":row["rate_ge_2"],"baseline_rate_ge_2":baseline["rate_ge_2"],"interpretation":"Historical descriptive result only; no purchase readiness."})
    _write_csv(outdir/"walkforward_predictions.csv",rows)
    _write_csv(outdir/"model_metrics.csv",metrics)
    _write_csv(outdir/"model_correlation.csv",correlations)
    _write_csv(outdir/"study_registry.csv",study_registry)
    _write_csv(outdir/"failure_registry.csv",failure_rows)
    _write_csv(outdir/"surviving_models.csv",[{"research_id":"H005_FIX","model":MODEL,"status":"NONE_PROMOTED","reason":"Historical diagnostic only; prospective confirmation required."}])
    mapping_audit={
      "study_id":STUDY,"legacy_s008_structure_contribution":"270/51 = 5.2941176470588235 constant for every number.",
      "legacy_s008_rank_order":"Equivalent to the sum of the six non-structure family rank vectors; the structure ticket has no number-specific influence.",
      "corrected_structure_vector":{"length":45,"selected_number_value":45.0,"unselected_number_value":0.0,"selected_count":6,"unselected_count":39,"appended_once":True},
      "corrected_score":"(rank_S001 + rank_S002 + rank_S003 + rank_S004 + rank_S006 + rank_S007 + corrected_structure_vector)/7",
      "legacy_mapping_algebra_checks":legacy_mapping_checks,"mapping_changed_targets":mapping_changes,
      "candidate_bank_seed":20261008,"candidate_bank_size":len(bank),"candidate_bank_sha256":bank_sha,
      "legacy_source_modified":False,"legacy_s008_relabelled":False,"h005_fix_is_separate":True
    }
    _write_json(outdir/"mapping_audit.json",mapping_audit)
    _write_json(outdir/"random_baseline.json",baseline)
    source_hashes={
      "legacy_run_batch_py_sha256":sha(SOURCE),
      "walkforward_core_py_sha256":sha(FRAMEWORK/"walkforward_core.py"),
      "research_registry_csv_sha256":sha(REGISTRY),
      "lotto_data_csv_sha256":data_sha,
      "candidate_bank_sha256":bank_sha,
      "h005_fix_runner_sha256":sha(Path(__file__).resolve())
    }
    _write_json(outdir/"MODEL_SPEC.json",{
      "study_id":STUDY,"model_id":"H005_FIX","model_name":MODEL,
      "corrected_mapping":prereg["corrected_mapping"],"legacy_mapping_proof":prereg["legacy_mapping_proof"],
      "component_families":list(COMPONENTS),"candidate_bank":{"seed":20261008,"size":5000,"sha256":bank_sha},
      "target_range":[201,1250],"training_rule":"Expanding rounds 1..t-1 only.",
      "random_baseline":"Exact six-of-45 hypergeometric distribution.",
      "parameter_search":False,"variants_evaluated":1,"source_hashes":source_hashes
    })
    verification={
      "status":"PASS","study_id":STUDY,"data_cutoff":1250,"data_rows":len(draws),"data_sha256":data_sha,
      "target_range":[201,1250],"target_count":len(rows),"training_cutoff_violations":0,"leakage_failures":0,
      "candidate_bank_size":len(bank),"candidate_bank_sha256":bank_sha,
      "legacy_mapping_algebra_checks":legacy_mapping_checks,"corrected_structure_vector_nonconstant_targets":legacy_mapping_checks,
      "mapping_changed_targets":mapping_changes,"exact_random_baseline_executed":True,
      "legacy_source_modified":False,"legacy_s008_relabelled":False,"h005_fix_is_separate":True,
      "parameter_search":False,"variants_evaluated":1,"strict_portfolio_pass":False,"strict_pass_ready":False,
      "purchase_recommendation_generated":False,"source_hashes":source_hashes
    }
    _write_json(outdir/"VERIFICATION.json",verification)
    completion={"study_id":STUDY,"status":"COMPLETE","data_cutoff":1250,"target_range":[201,1250],"target_count":1050,
      "classification":"HISTORICAL_DIAGNOSTIC_ONLY","model_status":reg_status,
      "strict_portfolio_pass":False,"strict_pass_ready":False,"purchase_recommendation_generated":False,
      "legacy_s008_modified":False,"h005_fix_is_separate":True}
    _write_json(outdir/"COMPLETION.json",completion)
    lines=[
      "# H005_FIX — Structure-to-number mapping repair",
      "",
      "- Scope: separate corrected implementation; legacy S008 source and historical outputs are untouched.",
      "- Data: 1..1250; expanding walk-forward targets 201..1250 (1050 predictions); each target trains only on 1..t-1.",
      "- Candidate bank: seed 20261008, 5000 fixed six-number tickets; SHA256 "+bank_sha,
      "- Legacy S008 algebra: 45 structure vectors (six constant 45-vectors and 39 zero-vectors) yield a constant 270/51 contribution for every number.",
      "- Corrected H005_FIX: one 45-dimensional vector, 45 for the six S005 structure-ticket members and 0 for the other 39, appended once to six component rank vectors; seven-family mean.",
      "- Legacy algebra checks: "+str(legacy_mapping_checks)+"; corrected mapping changed top-six ticket in "+str(mapping_changes)+" targets.",
      "- Random baseline: exact six-of-45 hypergeometric distribution; no Monte Carlo approximation.",
      "- This is a historical diagnostic, not a three-line portfolio or purchase recommendation.","",
      "| Model | Window | n | Mean hits | 2+ | 3+ | 4+ | Δ mean vs exact random |",
      "|---|---|---:|---:|---:|---:|---:|---:|"
    ]
    for row in metrics:
      lines.append(f"| {row['model']} | {row['window']} | {row['n']} | {row['mean_hits']:.4f} | {row['rate_ge_2']:.2%} | {row['rate_ge_3']:.2%} | {row['rate_ge_4']:.2%} | {row['delta_mean_vs_random']:+.4f} |")
    lines.extend(["", "## H005_FIX overall result", "",
      f"- Overall mean-hit delta vs exact random: {overall['delta_mean_vs_random']:+.6f}",
      f"- Recent100 mean-hit delta: {recent['delta_mean_vs_random']:+.6f}",
      f"- Recent50 mean-hit delta: {hold['delta_mean_vs_random']:+.6f}",
      f"- Historical classification: **{reg_status}**",
      "- No promotion, no prospective readiness, no strict PASS, and no purchase numbers generated.",
      "",
      "The correction is frozen and evaluated as a separate H005_FIX implementation. It does not rewrite or rename legacy S008. The corrected structure vector is number-specific; the legacy S008 contribution is algebraically constant."
    ])
    (outdir/"REPORT.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    manifest_entries=_manifest(outdir)
    if manifest_entries!=12: raise AssertionError(f"E056 manifest entries {manifest_entries} != 12")
    return {"status":"COMPLETE","study_id":STUDY,"result_path":outdir.relative_to(ROOT).as_posix(),
      "data_cutoff":1250,"target_count":1050,"mapping_changed_targets":mapping_changes,
      "legacy_mapping_algebra_checks":legacy_mapping_checks,"candidate_bank_sha256":bank_sha,
      "historical_classification":reg_status,"manifest_entries":manifest_entries,
      "strict_pass_ready":False,"purchase_recommendation_generated":False}

def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--date",required=True); parser.add_argument("--run-id",required=True)
    args=parser.parse_args(); print(json.dumps(run(args.date,args.run_id),ensure_ascii=False,indent=2))

if __name__=="__main__": main()
