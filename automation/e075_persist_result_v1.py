#!/usr/bin/env python3
import argparse,csv,hashlib,json
from datetime import datetime,timezone,timedelta
from pathlib import Path

STUDY_ID="E075_E045_SELECTOR_ORDER_CONFORMANCE_CORRECTION_v1"
EXPECTED_FILES={"PREDICTIONS.csv","RANDOM_BASELINE.csv","BLOCK_STABILITY.csv","INFERENCE.json","READINESS_UPDATE.json","VERIFICATION.json","COMPLETION.json","REPORT.md"}
METRICS=("max_hits","any2","any3","winning_union_coverage")


def verify_manifest(out):
    with (out/"SHA256_MANIFEST.csv").open("r",encoding="utf-8-sig",newline="") as stream:
        rows=list(csv.DictReader(stream))
    assert len(rows)==8 and {x["path"] for x in rows}==EXPECTED_FILES
    for row in rows:
        path=out/row["path"]
        assert path.is_file() and path.parent==out and not path.is_symlink()
        raw=path.read_bytes()
        assert len(raw)==int(row["bytes"]) and hashlib.sha256(raw).hexdigest()==row["sha256"],row["path"]
    return len(rows)


def build_report(inference,verification,data_sha,run_url,workflow_run_id):
    metrics=inference["metrics"]
    lines=[
        "# 2026-11-19 E075 publication-recovery addendum","",
        "## E075 — E045 selector-order implementation-conformance correction","",
        "**Classification: historical implementation-conformance correction only. Not an independent signal, independent sample, clean holdout, or prospective confirmation.**","",
        "### Execution and integrity","",
        f"- Recovery workflow run: [{workflow_run_id}]({run_url})",
        f"- Data cutoff: {inference['data_cutoff']}; data SHA-256: `{data_sha}`",
        f"- Walk-forward targets: {inference['target_range'][0]}–{inference['target_range'][1]} ({inference['targets']})",
        f"- Matched random bundles: {inference['random_bundles_total_per_version']:,} per version",
        f"- Candidate-pool comparisons: {inference['candidate_pool_comparisons']}; ranking rule identical: {inference['candidate_pool_rule_identical']}",
        f"- First-role pool mismatches: {inference['first_role_pool_mismatches']}; downstream pool-content differences: {inference['downstream_pool_content_differences']}",
        f"- Legacy score-order adjacency mismatches: {inference['legacy_order_consecutive_mismatches']}",
        f"- Targets with changed line assignments: {inference['targets_with_changed_lines']}; changed line assignments: {inference['changed_line_count']}",
        f"- Leakage failures: {verification['leakage_failures']}; training-cutoff violations: {verification['training_cutoff_violations']}; future predictions: {verification['future_predictions']}",
        f"- Portfolio geometry violations: {verification['portfolio_geometry_violations']}; random geometry violations: {verification['random_geometry_violations']}",
        "- Output manifest: PASS (8/8 files)","",
        "### Historical metrics","",
        "| Metric | Legacy delta vs exact null | Corrected delta vs exact null | Corrected minus legacy | Paired moving-block CI |",
        "|---|---:|---:|---:|---:|"
    ]
    for metric in METRICS:
        old=metrics["legacy_vs_exact_null"][metric]
        new=metrics["corrected_vs_exact_null"][metric]
        paired=metrics["corrected_minus_legacy"][metric]
        ci=paired["moving_block_ci"]
        lines.append(f"| {metric} | {old['delta_mean']:.6f} | {new['delta_mean']:.6f} | {paired['delta_mean']:.6f} | [{ci[0]:.6f}, {ci[1]:.6f}] |")
    lines += [
        "",
        f"- Legacy any2-positive 50-target block share: {inference['legacy_any2_positive_50_target_block_share']:.2%}",
        f"- Corrected any2-positive 50-target block share: {inference['corrected_any2_positive_50_target_block_share']:.2%}",
        f"- Legacy historical strict gate: {'PASS' if inference['historical_strict_gate_pass_legacy'] else 'FAIL'}",
        f"- Corrected historical strict gate: {'PASS' if inference['historical_strict_gate_pass_corrected'] else 'FAIL'}",
        "- Prospective confirmation remains required; its minimum target count and completion rule are unspecified.",
        "- STRICT_PASS_READY: **not created**",
        "- Final purchase lines, random fallback, freeze, and seal: **not generated**","",
        "### Interpretation","",
        "The frozen E045 specification evaluates consecutive pairs and lexicographic tie-breaks on sorted six-number tickets. E075 corrects only those order-dependent operations. The original E045 runner and outputs remain unchanged. Model weights, role order, candidate-pool ranking formula, exact null, random seed, alpha, block length, bootstrap count, and strict gates are unchanged.","",
        "This is a reproducible implementation-conformance correction, not new predictive evidence. Historical results remain contaminated live-history diagnostics and cannot create purchase readiness.","",
        "No thresholds, alpha levels, block lengths, comparators, model weights, or parameter variants were changed.",""
    ]
    return "\n".join(lines)


def persist(root,date,run_id,workflow_run_id,run_number,run_attempt,run_url,data_sha):
    out=root/"analysis"/date/run_id/STUDY_ID
    inference=json.loads((out/"INFERENCE.json").read_text(encoding="utf-8"))
    verification=json.loads((out/"VERIFICATION.json").read_text(encoding="utf-8"))
    completion=json.loads((out/"COMPLETION.json").read_text(encoding="utf-8"))
    entries=verify_manifest(out)
    assert inference["data_cutoff"]==1250 and inference["data_sha256"]==data_sha
    assert inference["target_range"]==[401,1250] and inference["targets"]==850
    assert inference["random_bundles_total_per_version"]==102000 and inference["block_count"]==17
    assert verification["status"]=="PASS" and verification["data_sha256"]==data_sha
    assert verification["training_cutoff_violations"]==0 and verification["leakage_failures"]==0
    assert verification["future_predictions"]==0 and verification["no_future_leakage"] is True
    assert verification["portfolio_geometry_violations"]==0 and verification["random_geometry_violations"]==0
    assert verification["strict_pass_ready"] is False and verification["purchase_recommendation_generated"] is False
    assert completion["status"]=="COMPLETE" and completion["data_cutoff"]==1250
    assert completion["target_range"]==[401,1250] and completion["target_count"]==850
    assert completion["strict_pass_ready"] is False and completion["purchase_recommendation_generated"] is False

    queue_path=root/"automation/research_queue_v2.json"
    queue=json.loads(queue_path.read_text(encoding="utf-8"))
    task=next(x for x in queue["tasks"] if x.get("id")==STUDY_ID)
    if task["execution_status"]!="PREREGISTERED_PENDING_DEDICATED_WORKFLOW":
        raise RuntimeError("Refusing duplicate/conflicting E075 persistence: "+task["execution_status"])
    if task.get("post_v3_attempt_history",[])[-1].get("workflow_run_id")!=44426026061:
        raise RuntimeError("Failed E075 persistence attempt is not preserved in queue")

    status="EXECUTED_HISTORICAL_GATE_PASS_PROSPECTIVE_PENDING" if inference["historical_strict_gate_pass_corrected"] else "EXECUTED_HISTORICAL_STRICT_FAIL"
    now=datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=9))).isoformat()
    result={
        "study_id":STUDY_ID,
        "evidence_class":"HISTORICAL_IMPLEMENTATION_CONFORMANCE_CORRECTION_NOT_INDEPENDENT_SIGNAL_OR_PROSPECTIVE_CONFIRMATION",
        "independent_research_axis":False,"independent_sample":False,
        "workflow_name":"target-1251-e075-publication-recovery",
        "workflow_run_id":int(workflow_run_id),"workflow_run_number":int(run_number),"run_attempt":int(run_attempt),
        "workflow_run_conclusion":"success","run_url":run_url,"completed_at_kst":now,
        "result_path":out.relative_to(root).as_posix(),"data_cutoff":1250,"data_sha256":data_sha,
        "target_range":[401,1250],"target_count":850,
        "random_bundles_per_target_per_version":120,"random_bundles_total_per_version":102000,
        "block_length":50,"block_count":17,"training_cutoff_violations":0,"leakage_failures":0,
        "future_predictions":0,"portfolio_geometry_violations":0,"random_geometry_violations":0,
        "candidate_pool_comparisons":verification["candidate_pool_comparisons"],
        "candidate_pool_rule_identical":verification["candidate_pool_rule_identical"],
        "first_role_pool_mismatches":verification["first_role_pool_mismatches"],
        "downstream_pool_content_differences":verification["downstream_pool_content_differences"],
        "legacy_order_consecutive_mismatches":verification["legacy_order_consecutive_mismatches"],
        "targets_with_changed_lines":verification["targets_with_changed_lines"],
        "changed_line_count":verification["changed_line_count"],
        "manifest_entries":entries,"manifest_status":"PASS",
        "historical_strict_gate_pass_legacy":inference["historical_strict_gate_pass_legacy"],
        "historical_strict_gate_pass_corrected":inference["historical_strict_gate_pass_corrected"],
        "strict_portfolio_pass":False,"strict_pass_ready":False,
        "prospective_confirmation_status":"UNSPECIFIED_IN_POLICY",
        "failed_gates":[m for m in METRICS if not inference["metrics"]["corrected_vs_exact_null"][m]["lower_bound_strictly_gt_zero"]]
                       +(["any2_positive_50_target_block_share"] if inference["corrected_any2_positive_50_target_block_share"]<0.65 else []),
        "no_threshold_changes":True,"parameter_search":False,"purchase_recommendation_generated":False,
        "daily_report_addendum_path":"research/daily/2026-11-19_E075_PUBLICATION_RECOVERY_ADDENDUM.md"
    }
    task["execution_status"]=status
    task["execution_result"]=result
    task["execution_completed_at_kst"]=now
    task["result_path"]=result["result_path"]
    task["spec"]["execution_status"]=status
    task["spec"]["execution_result"]=result
    task["spec"]["strict_pass_ready"]=False

    addendum=root/result["daily_report_addendum_path"]
    if addendum.exists(): raise FileExistsError("Refusing to overwrite existing E075 addendum")
    addendum.parent.mkdir(parents=True,exist_ok=True)
    addendum.write_text(build_report(inference,verification,data_sha,run_url,workflow_run_id),encoding="utf-8")

    status_path=root/"research/weekly_purchase/1251/DAILY_MASTER_STATUS_1251_20261119.json"
    if status_path.exists():
        daily=json.loads(status_path.read_text(encoding="utf-8"))
        completed=daily.setdefault("completed_today",[])
        note="E075 v3 historical implementation-conformance correction completed with verified 8/8 manifest; no independent signal, prospective confirmation, or purchase readiness was created."
        if note not in completed: completed.append(note)
        daily["pending_work"]=[x for x in daily.get("pending_work",[]) if not str(x).startswith("E075 v3 dedicated workflow remains")]
        if not any("prospective confirmation minimum target count" in str(x).lower() for x in daily["pending_work"]):
            daily["pending_work"].append("Prospective confirmation minimum target count and completion rule remain unspecified.")
        daily["e075_execution"]={"status":status,"workflow_run_id":int(workflow_run_id),"workflow_run_url":run_url,
                                 "result_path":result["result_path"],"manifest_status":"PASS","strict_pass_ready":False,
                                 "purchase_recommendation_generated":False}
        daily["daily_master_status"]="PARTIAL"
        daily["next_start"]="Keep the strict gate unchanged; resolve the prospective confirmation minimum/completion rule through explicit policy approval; do not generate purchase lines until a separately validated and prospectively eligible artifact exists."
        status_path.write_text(json.dumps(daily,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

    queue_path.write_text(json.dumps(queue,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return {"status":"PERSISTED","execution_status":status,"manifest_entries":entries,
            "strict_pass_ready":False,"result_path":result["result_path"],
            "daily_report_addendum_path":result["daily_report_addendum_path"]}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1])
    p.add_argument("--date",required=True);p.add_argument("--run-id",required=True)
    p.add_argument("--workflow-run-id",required=True,type=int);p.add_argument("--run-number",required=True,type=int)
    p.add_argument("--run-attempt",required=True,type=int);p.add_argument("--run-url",required=True);p.add_argument("--data-sha",required=True)
    a=p.parse_args()
    print(json.dumps(persist(a.root.resolve(),a.date,a.run_id,a.workflow_run_id,a.run_number,a.run_attempt,a.run_url,a.data_sha),ensure_ascii=False))


if __name__=="__main__": main()
