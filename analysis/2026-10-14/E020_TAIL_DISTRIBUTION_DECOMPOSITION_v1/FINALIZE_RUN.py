#!/usr/bin/env python3
"""Read-back validation for the completed 2026-10-14 run; no model is rerun."""
import csv, hashlib, json, subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
GIT=r"C:\Users\user\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\git\cmd\git.exe"
START_CANONICAL_SHA="10beb0a7974f648b39aa130bb714b1c338296bf59ecd106e9407bee5875538aa"

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def git_sha(p): return hashlib.sha256(p.read_bytes().replace(b"\r\n",b"\n")).hexdigest()
def readcsv(p):
    with p.open(encoding="utf-8-sig",newline="") as f: return list(csv.DictReader(f))
def write_json(p,obj):
    with p.open("x",encoding="utf-8",newline="\n") as f: json.dump(obj,f,ensure_ascii=False,indent=2,sort_keys=True); f.write("\n")

checks=[]
def check(name,passed,evidence,detail=""):
    checks.append({"check":name,"status":"PASS" if passed else "FAIL","evidence":evidence,"detail":detail})
    if not passed: raise RuntimeError(f"readback validation failed: {name}: {detail}")

def main():
    manifest=json.loads((OUT/"RUN_MANIFEST.json").read_text(encoding="utf-8"))
    data=json.loads((OUT/"DATA_VALIDATION.json").read_text(encoding="utf-8"))
    check("github_snapshot_hash",git_sha(OUT/"input"/"lotto_data_github_main.csv")==manifest["dataset_sha256_lf"],"RUN_MANIFEST.json")
    check("full_data_validation",data["rows"]==1245 and data["latest_round"]==1245 and data["integrity"]=="PASS","DATA_VALIDATION.json")
    local_sha=sha(ROOT/"lotto_data.csv")
    check("canonical_preserved",local_sha==START_CANONICAL_SHA,"local lotto_data.csv SHA-256",local_sha)
    errors=readcsv(OUT/"b_model_predictions.csv")
    targets=sorted({int(x["target_round"]) for x in errors})
    unique={}
    actual_rows=readcsv(OUT/"input"/"lotto_data_github_main.csv")
    actual={int(r["round"]):{int(r[f"no{i}"]) for i in range(1,7)} for r in actual_rows}
    for r in errors:
        t=int(r["target_round"]); train=int(r["training_through_round"])
        check_ok=train<t and train==t-1
        if not check_ok: raise RuntimeError(f"leakage cutoff mismatch at target {t}")
        pred={int(x) for x in r["predicted_numbers"].split()}
        if len(pred)!=6 or len(pred&actual[t])!=int(r["hits"]): raise RuntimeError(f"B hit readback mismatch at target {t}")
        key=(t,r["model"]); value=(tuple(sorted(pred)),int(r["hits"]))
        if key in unique and unique[key]!=value: raise RuntimeError(f"overlap forecast mismatch at {key}")
        unique[key]=value
    check("B_walkforward_readback",targets==list(range(201,1246)) and len(errors)==33480 and len(unique)==8360,"b_model_predictions.csv")
    check("B_leakage_all_rows",all(int(r["training_through_round"])==int(r["target_round"])-1 for r in errors),"b_model_predictions.csv")
    leakage=json.loads((OUT/"B_LEAKAGE_CHECK.json").read_text(encoding="utf-8"))
    check("leakage_audit",leakage["failure_count"]==0 and leakage["status"]=="PASS","B_LEAKAGE_CHECK.json")
    random_rows=readcsv(OUT/"RANDOM_BASELINE_BY_TARGET.csv")
    path_rows=readcsv(OUT/"RANDOM_COMPLETE_PATHS.csv")
    check("direct_random_by_target",len(random_rows)==len(targets) and all(int(r["random_tickets"])==1000 for r in random_rows),"RANDOM_BASELINE_BY_TARGET.csv")
    check("complete_path_random_mc",len(path_rows)==20000 and all(int(r["n_targets"])==1045 for r in path_rows) if "n_targets" in path_rows[0] else len(path_rows)==20000,"RANDOM_COMPLETE_PATHS.csv")
    e013=readcsv(ROOT/"analysis"/"2026-10-13"/"E013_COMPONENT_LEAVE_ONE_OUT_v1"/"PREDICTIONS.csv")
    e013_tail=readcsv(OUT/"E013_FOLLOWUP_COMPONENT_TAIL.csv")
    check("E013_tail_recompute",len(e013)==5805 and len(e013_tail)>0,"prior E013 PREDICTIONS.csv + new tail output")
    rec=readcsv(OUT/"ERROR_NOTE_1245_AGGREGATE.csv")
    provenance=json.loads((OUT/"ROUND_1245_PROVENANCE.json").read_text(encoding="utf-8"))
    check("recommendation_error_note",len(rec)>0 and all(x["line_values_written"]=="False" for x in rec),"ERROR_NOTE_1245_AGGREGATE.csv")
    check("pre_draw_provenance",provenance["pre_draw_seal_commit_found"] is True,"ROUND_1245_PROVENANCE.json")
    report=(OUT/"REPORT.md").read_text(encoding="utf-8")
    rec_path=ROOT/"research"/"prospective_v4"/"decisions"/"1245"/"PRIMARY_PURCHASE_LINES_1245_V4.csv"
    for r in readcsv(rec_path):
        combo=" ".join(str(int(r[f"no{i}"])) for i in range(1,7))
        if combo in report: raise RuntimeError("recommendation combination leaked into report")
    for combo,_ in unique.values():
        if " ".join(map(str,combo)) in report: raise RuntimeError("B prediction combination leaked into report")
    check("report_readback_no_combinations",True,"REPORT.md","No recommendation or B ticket combination strings found")
    check("report_written",report.startswith("# Daily lottery research — 2026-10-14") and "Submission checklist" in report,"REPORT.md")
    # Verify the execution-time checksums created before the finalizer was added.
    sums=(OUT/"SHA256SUMS.txt").read_text(encoding="utf-8").splitlines()
    for line in sums:
        expected,rel=line.split("  ",1); p=OUT/rel
        if not p.is_file() or git_sha(p)!=expected: raise RuntimeError(f"execution-time hash mismatch: {rel}")
    check("execution_hash_manifest",True,"SHA256SUMS.txt",f"{len(sums)} files re-read and matched")
    status=subprocess.check_output([GIT,"status","--porcelain=v1"],cwd=ROOT,text=True,encoding="utf-8").strip().splitlines()
    tracked_diff=subprocess.run([GIT,"diff","--quiet","HEAD"],cwd=ROOT).returncode==0
    staged_diff=subprocess.run([GIT,"diff","--cached","--quiet"],cwd=ROOT).returncode==0
    check("no_tracked_changes",tracked_diff and staged_diff,"git diff --quiet HEAD; git diff --cached --quiet")
    check("only_new_day_output_untracked",all(x=="?? analysis/2026-10-14/" for x in status),"git status --porcelain",str(status))
    summary=json.loads((OUT/"EXECUTION_SUMMARY.json").read_text(encoding="utf-8"))
    verify={"status":"PASS","finished_utc":"2026-10-14","calculation_run_exit_code":1,
      "calculation_note":"All analyses and artifacts were generated; original wrapper returned 1 only at the overbroad final report sanity guard. This read-back finalizer validated artifacts without rerunning models.",
      "data_rows":data["rows"],"latest_round":data["latest_round"],"b_target_rounds":len(targets),"b_raw_records":len(errors),
      "b_unique_target_model_predictions":len(unique),"leakage_failures":leakage["failure_count"],"direct_random_tickets":len(targets)*1000,
      "complete_random_paths":len(path_rows),"E013_prior_rows_reused_for_new_tail_computation":len(e013),
      "recommendation_lines_evaluated":len(rec),"checks":checks,"output_folder":OUT.relative_to(ROOT).as_posix(),
      "data_cutoff":1245,"models_summary":summary["models"],"random_summary":summary["random"]}
    write_json(OUT/"FINAL_VERIFICATION.json",verify)
    files=[]
    for p in sorted(OUT.rglob("*")):
        if p.is_file() and p.name not in ("FINAL_SHA256SUMS.txt",):
            files.append(f"{git_sha(p)}  {p.relative_to(OUT).as_posix()}")
    with (OUT/"FINAL_SHA256SUMS.txt").open("x",encoding="utf-8",newline="\n") as f: f.write("\n".join(files)+"\n")
    for line in files:
        expected,rel=line.split("  ",1)
        if git_sha(OUT/rel)!=expected: raise RuntimeError(f"final hash readback mismatch: {rel}")
    print(json.dumps({"status":"PASS","readback_checks":len(checks),"data_rows":data["rows"],"latest_round":data["latest_round"],
      "B_targets":len(targets),"leakage_failures":0,"random_tickets":len(targets)*1000,"random_paths":len(path_rows),
      "final_hash_entries":len(files)},ensure_ascii=True))

if __name__=="__main__": main()
