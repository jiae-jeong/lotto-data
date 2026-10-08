from __future__ import annotations
import argparse, ast, csv, hashlib, importlib.util, inspect, json, math, statistics, subprocess, sys
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CODEX_ROOT = ROOT.parents[1]
OLD = CODEX_ROOT / "2026-10-06" / "cloud-x20"
RAW = OLD / "work" / "lotto-data" / "lotto_data.csv"
BASELINE = ROOT / "outputs" / "research_expansion_framework_v1" / "project_baseline_manifest.csv"
GH_ROOT = ROOT / "work" / "lotto-data-github"
GH_CORR = GH_ROOT / "research" / "expansion_framework_v1" / "studies" / "study_batch_001" / "model_correlation.csv"
LOCAL_CORR = ROOT / "outputs" / "research_expansion_framework_v1" / "studies" / "study_batch_001" / "model_correlation.csv"
EXPECTED_RAW_SHA256 = "243cd17e6b97a2d96709ddfc689a068038669341a52dcc0743c141d309e43b9f"
EXPECTED_GITHUB_HEAD = "d813f5ecc235a14eb70f8f002e82bd5f78506d21"
EXPECTED_GH_CORR_SHA256 = "722a3818032532e8c405fadc846345a855d617135f83d091f35c7d21c4da002e"
FRAMEWORK = ROOT/"outputs"/"research_expansion_framework_v1"
PROSPECTIVE_DIR = FRAMEWORK/"prospective"
STUDY_SOURCE = FRAMEWORK/"studies"/"study_batch_001"/"run_batch.py"
MODELS = ["long_frequency", "current_gap", "frequency_plus_gap", "recent_momentum", "structure_profile", "pair_association", "triple_association", "combined_equal_rank"]
GROUPS = ["all8_consensus", "frequency_time_consensus", "structure_association_consensus"]
INPUTS = {
 "full_predictions": (OLD/"outputs"/"b_model_predictions.csv", {"target_round","training_through_round","model","predicted_numbers","actual_numbers","hits"},33408),
 "full_metrics": (OLD/"outputs"/"b_model_holdout_metrics.csv", {"model","n","mean_hits","rate_ge_2","rate_ge_3","rate_ge_4","rate_ge_5"},256),
 "classification": (OLD/"outputs"/"b_model_classification.csv", {"model","classification","pooled_n","pooled_mean_hits"},8),
 "trends": (OLD/"outputs"/"b_model_50_round_trends.csv", {"anchor_after_round","tested_rounds","model","n","mean_hits","rate_ge_2"},56),
 "recent_predictions": (ROOT/"outputs"/"b_model_recent_predictions.csv", {"target_round","training_through_round","model","predicted_numbers","actual_numbers","hits"},352),
 "recent_metrics": (ROOT/"outputs"/"b_model_recent_metrics.csv", {"model","n","mean_hits","rate_ge_2","rate_ge_3","delta_mean_vs_random"},8),
 "candidates": (ROOT/"outputs"/"b_model_1245_analysis_predictions.csv", {"target_round","training_through_round","model","predicted_numbers"},8),
 "number_stats": (ROOT/"outputs"/"b_model_1245_number_stats.csv", {"number","models_selecting_number","long_frequency_1_1244","recent_frequency_last_50","current_gap_rounds"},45),
 "model_overlaps": (ROOT/"outputs"/"b_model_1245_ticket_overlaps.csv", {"model_a","model_b","overlap_count","overlap_numbers"},28),
 "number_history": (ROOT/"outputs"/"b_model_1245_candidate_historical_performance.csv", {"model","candidate_number","full_selection_count","full_actual_number_hit_count","last100_selection_count","last50_selection_count"},48),
 "group_metrics": (ROOT/"outputs"/"b_model_1245_candidate_groups_metrics.csv", {"candidate_group","member_models","candidate_numbers_1245","n","mean_hits","rate_ge_2","rate_ge_3","random_baseline_mean_hits","random_baseline_rate_ge_2"},3),
 "group_detail": (ROOT/"outputs"/"b_model_1245_candidate_groups_walkforward.csv", {"target_round","training_through_round","candidate_group","member_models","predicted_numbers","actual_numbers","hits"},3132),
}
ASSET_IDS = {"full_predictions":"b_model_predictions","full_metrics":"b_model_holdout_metrics","classification":"b_model_classification","trends":"b_model_50_round_trends","recent_predictions":"recent_predictions","recent_metrics":"recent_metrics","candidates":"candidate_1245_predictions","number_stats":"candidate_number_stats","model_overlaps":"model_ticket_overlaps","number_history":"candidate_number_history","group_metrics":"candidate_group_metrics","group_detail":"candidate_group_walkforward"}
RAW_COLUMNS = ["round","date","no1","no2","no3","no4","no5","no6","bonus"]

class Audit:
 def __init__(self): self.errors=[]; self.warnings=[]; self.expected_unavailable=[]; self.info=[]; self.inventory=[]; self.tables={}; self.asset_hashes={}; self.portfolio={}; self.components=[]; self.unique_predictions={}; self.direct_corr={}; self.github_pair={"hit_correlation":"n/a"}; self.model_independence=[]; self.prospective_entries={}; self.registered_candidates={}; self.candidate_overlaps=[]; self.registry_rows=[]; self.model_module=None
 def error(self,s): self.errors.append(s)
 def warn(self,s): self.warnings.append(s)

def sha256(path: Path) -> str:
 h=hashlib.sha256()
 with path.open("rb") as f:
  for block in iter(lambda:f.read(1024*1024),b""): h.update(block)
 return h.hexdigest()

def read_table(path: Path):
 with path.open(newline="",encoding="utf-8-sig") as f:
  r=csv.DictReader(f); fields=r.fieldnames or []; rows=list(r)
 return fields,rows

def parse_nums(text): return tuple(int(x) for x in str(text).split())

def exact_baseline():
 d=math.comb(45,6); probs=[math.comb(6,k)*math.comb(39,6-k)/d for k in range(7)]
 return {"mean":sum(k*p for k,p in enumerate(probs)),"p2plus":sum(probs[2:]),"p3plus":sum(probs[3:])}

def read_manifest(a: Audit):
 if not BASELINE.is_file(): a.error(f"Missing pinned baseline manifest: {BASELINE}"); return {}
 try:
  _,rows=read_table(BASELINE)
  return {r["asset_id"]:r for r in rows}
 except Exception as e: a.error(f"Cannot parse baseline manifest: {e}"); return {}

def audit_raw(a: Audit, manifest):
 if not RAW.is_file(): a.error(f"Missing raw source: {RAW}"); return
 try:
  got=sha256(RAW); a.asset_hashes["raw_data"]=got
  exp=manifest.get("raw_data",{}).get("sha256")
  if got != EXPECTED_RAW_SHA256 or got != exp: a.error(f"Raw SHA-256 mismatch: got={got}, expected={EXPECTED_RAW_SHA256}, baseline_manifest={exp}")
  with RAW.open(newline="",encoding="utf-8-sig") as f:
   rd=csv.DictReader(f)
   fields=rd.fieldnames or []
   if fields != RAW_COLUMNS: a.error(f"Raw columns must exactly equal {RAW_COLUMNS}; got {fields}")
   seen=[]; row_count=0
   for row in rd:
    row_count+=1
    if row_count>1244:
     # Only reject the existence of an extra record; never parse its draw or bonus values.
     a.error(f"Raw source has more than 1244 records (extra record #{row_count}); refusing to ignore it")
     break
    try:
     rnd=int(row["round"]); seen.append(rnd)
     if rnd<1 or rnd>1244: a.error(f"Out-of-range round {rnd} at data row {row_count}")
     nums=[int(row[f"no{i}"]) for i in range(1,7)]
     bonus=int(row["bonus"])
     if len(set(nums))!=6: a.error(f"Duplicate main number at round {rnd}")
     if any(n<1 or n>45 for n in nums): a.error(f"Main number out of range at round {rnd}")
     if bonus<1 or bonus>45: a.error(f"Bonus out of range at round {rnd}")
     if bonus in nums: a.error(f"Bonus is not separate from six main numbers at round {rnd}")
    except Exception as e: a.error(f"Malformed raw row {row_count}: {e}")
  if row_count!=1244: a.error(f"Raw data rows={row_count}; exactly 1244 required")
  if len(seen)!=1244 or set(seen)!=set(range(1,1245)): a.error("Rounds 1..1244 must each occur exactly once with no gaps or duplicates")
  if seen and max(seen)!=1244: a.error(f"Maximum round is {max(seen)}, expected 1244")
  a.inventory.append(("raw_data",str(RAW),row_count,"PASS" if not a.errors else "ERROR",got))
 except Exception as e: a.error(f"Raw audit failed: {e}")

def audit_inputs(a: Audit, manifest):
 for key,(path,required,expected_rows) in INPUTS.items():
  if not path.is_file(): a.error(f"Missing {key}: {path}"); a.inventory.append((key,str(path),0,"ERROR","")); continue
  try:
   fields,rows=read_table(path); aid=ASSET_IDS[key]; exp=manifest.get(aid,{}).get("sha256"); got=sha256(path); a.asset_hashes[aid]=got
   if exp and got!=exp: a.error(f"SHA-256 mismatch for {key}: {got} != {exp}")
   if not exp: a.error(f"No baseline SHA-256 for {key} ({aid})")
   missing=required-set(fields)
   if missing: a.error(f"{key} missing required columns {sorted(missing)}")
   if len(rows)!=expected_rows: a.error(f"{key} row count {len(rows)}; expected {expected_rows}")
   a.tables[key]=rows; a.inventory.append((key,str(path),len(rows),"PASS" if not missing and len(rows)==expected_rows and exp==got else "ERROR",got))
  except Exception as e: a.error(f"Cannot read {key}: {e}")

def audit_prospective_framework(a: Audit):
 p=ROOT/"outputs"/"research_expansion_framework_v1"/"prospective"
 protocol=p/"prospective_protocol_v1.md"; registry=p/"prospective_registry_v1.csv"; model_manifest=p/"prospective_model_manifest_v1.csv"; seal=p/"prospective_seal_v1.txt"
 if not all(x.is_file() for x in (protocol,registry,model_manifest,seal)):
  a.error("Prospective framework files are incomplete"); return
 try:
  expected=seal.read_text(encoding="utf-8").splitlines()[0].split("=",1)[1]
  if sha256(model_manifest)!=expected: a.error("Prospective manifest seal mismatch")
  _,entries=read_table(model_manifest); a.prospective_entries={Path(e["file"]).name:e for e in entries}
  for e in entries:
   path=ROOT/e["file"]
   if not path.is_file() or sha256(path)!=e["sha256"]: a.error(f"Prospective frozen file hash mismatch: {e['file']}")
  _,models=read_table(registry); a.registry_rows=models
  if {r["model_id"] for r in models}!={f"S{i:03d}" for i in range(1,9)}: a.error("Prospective registry must contain frozen S001-S008")
  a.asset_hashes["prospective_manifest"]=sha256(model_manifest)
  for name,path,count in (("prospective_protocol",protocol,1),("prospective_registry",registry,len(models)),("prospective_model_manifest",model_manifest,len(entries)),("prospective_seal",seal,len(seal.read_text(encoding="utf-8").splitlines()))):
   a.inventory.append((name,str(path),count,"PASS",sha256(path)))
 except Exception as e: a.error(f"Prospective framework integrity check failed: {e}")

def validate_cutoffs(a: Audit):
 models=set(MODELS)
 rows=a.tables.get("full_predictions",[]); uniq={}
 for r in rows:
  try:
   t=int(r["target_round"]); c=int(r["training_through_round"]); m=r["model"]
   if not 201<=t<=1244 or c!=t-1 or m not in models: a.error(f"full predictions cutoff/model invalid: {t}/{c}/{m}"); continue
   key=(t,m); vals=(r["predicted_numbers"],r["actual_numbers"],int(r["hits"]))
   if key in uniq and uniq[key]!=vals: a.error(f"Conflicting duplicate prediction {key}")
   uniq[key]=vals
  except Exception: a.error("Malformed full prediction row")
 if len(uniq)!=1044*8: a.error(f"Unique full target×model rows={len(uniq)}; expected 8352")
 for key,targets,expected in [("recent_predictions",range(1201,1245),352),("group_detail",range(201,1245),3132)]:
  rs=a.tables.get(key,[])
  if len(rs)!=expected: continue
  for r in rs:
   try:
    t=int(r["target_round"])
    if t not in targets or int(r["training_through_round"])!=t-1: a.error(f"{key} cutoff/target invalid at {t}")
    if len(set(parse_nums(r["predicted_numbers"])) & set(parse_nums(r["actual_numbers"])))!=int(r["hits"]): a.error(f"{key} hit mismatch at {t}")
   except Exception: a.error(f"Malformed row in {key}")
 for r in a.tables.get("candidates",[]):
  try:
   ns=parse_nums(r["predicted_numbers"])
   if int(r["target_round"])!=1245 or int(r["training_through_round"])!=1244 or r["model"] not in models or len(ns)!=6 or len(set(ns))!=6 or any(n<1 or n>45 for n in ns): a.error("Invalid 1245 candidate ticket/cutoff")
  except Exception: a.error("Malformed 1245 candidate row")
 if len(a.tables.get("candidates",[]))==8 and {r["model"] for r in a.tables["candidates"]}!=models: a.error("1245 candidates do not cover exactly the fixed 8 models")
 baseline=exact_baseline()
 for r in a.tables.get("group_metrics",[]):
  try:
   if abs(float(r["random_baseline_mean_hits"])-baseline["mean"])>1e-10 or abs(float(r["random_baseline_rate_ge_2"])-baseline["p2plus"])>1e-10: a.error(f"Exact random baseline mismatch in {r['candidate_group']}")
  except Exception: a.error("Malformed candidate group baseline fields")
 candidate_tickets={r["model"]:parse_nums(r["predicted_numbers"]) for r in a.tables.get("candidates",[]) if r.get("model") in models}
 if len(a.tables.get("candidates",[]))==8:
  for m,ns in candidate_tickets.items():
   if len(ns)!=6 or len(set(ns))!=6 or any(n<1 or n>45 for n in ns): a.error(f"Invalid candidate ticket for {m}")
 if len(a.tables.get("recent_predictions",[]))==352 and {r["model"] for r in a.tables["recent_predictions"]}!=models: a.error("Recent predictions must cover exactly the eight fixed models")
 if len(a.tables.get("recent_metrics",[]))==8 and {r["model"] for r in a.tables["recent_metrics"]}!=models: a.error("Recent metrics must cover exactly the eight fixed models")
 stats=a.tables.get("number_stats",[])
 if len(stats)==45:
  votes=Counter(n for ns in candidate_tickets.values() for n in ns)
  try:
   if {int(r["number"]) for r in stats}!=set(range(1,46)): a.error("Number statistics must contain numbers 1..45 exactly once")
   if any(int(r["models_selecting_number"])!=votes[int(r["number"])] for r in stats): a.error("Number-stat vote counts do not match the eight candidate tickets")
  except Exception: a.error("Malformed number-stat rows")
 overlaps=a.tables.get("model_overlaps",[])
 if len(overlaps)==28:
  expected_pairs={frozenset(p) for p in combinations(MODELS,2)}
  actual_pairs={frozenset((r["model_a"],r["model_b"])) for r in overlaps}
  if actual_pairs!=expected_pairs: a.error("Model overlap input must cover all 28 model pairs")
  for r in overlaps:
   try:
    actual=len(set(candidate_tickets[r["model_a"]])&set(candidate_tickets[r["model_b"]]))
    if int(r["overlap_count"])!=actual: a.error(f"Model overlap count mismatch: {r['model_a']}/{r['model_b']}")
   except Exception: a.error("Malformed model-overlap row")
 history=a.tables.get("number_history",[])
 if len(history)==48:
  expected={(m,n) for m,ns in candidate_tickets.items() for n in ns}
  actual={(r["model"],int(r["candidate_number"])) for r in history}
  if actual!=expected: a.error("Candidate-number history does not match the 48 selected model-number pairs")
  for r in history:
   if int(r["full_rounds"])!=1044 or int(r["last100_rounds"])!=100 or int(r["last50_rounds"])!=50: a.error("Candidate-number historical window/cutoff length mismatch")
 for r in a.tables.get("group_metrics",[]):
  try:
   members=r["member_models"].split(";")
   if not members or any(m not in candidate_tickets for m in members): raise ValueError("unknown/missing group member")
   votes=Counter(n for m in members for n in candidate_tickets[m])
   expected=tuple(sorted(sorted(votes,key=lambda n:(-votes[n],n))[:6]))
   if tuple(sorted(parse_nums(r["candidate_numbers_1245"])))!=expected: a.error(f"Group ticket does not reproduce vote/tie rule: {r['candidate_group']}")
   if int(r["n"])!=1044: a.error(f"Group metric n mismatch: {r['candidate_group']}")
  except Exception as e: a.error(f"Invalid candidate group construction: {e}")
 if len(a.tables.get("group_metrics",[]))==3 and {r["candidate_group"] for r in a.tables["group_metrics"]}!=set(GROUPS): a.error("Candidate group metrics must contain the three fixed groups")

def structure(ns):
 n=sorted(ns); gaps=[b-x for x,b in zip(n,n[1:])]; ends=Counter(x%10 for x in n)
 return {"odd":sum(x%2 for x in n),"low_le22":sum(x<=22 for x in n),"sum":sum(n),"bands":tuple(sum(lo<=x<=hi for x in n) for lo,hi in ((1,10),(11,20),(21,30),(31,40),(41,45))),"consecutive_pairs":sum(g==1 for g in gaps),"repeated_end_excess":sum(v-1 for v in ends.values() if v>1),"clusters":1+sum(g>5 for g in gaps)}

def pearson(xs,ys):
 if len(xs)<2:return float("nan")
 mx=statistics.mean(xs);my=statistics.mean(ys);dx=[x-mx for x in xs];dy=[y-my for y in ys]
 den=math.sqrt(sum(x*x for x in dx)*sum(y*y for y in dy))
 return sum(x*y for x,y in zip(dx,dy))/den if den else float("nan")

def build_diagnostics(a: Audit):
 groups={}
 for r in a.tables.get("group_metrics",[]):
  try: groups[r["candidate_group"]]={"numbers":parse_nums(r["candidate_numbers_1245"]),"members":r["member_models"].split(";"),"row":r}
  except Exception as e: a.error(f"Malformed group metric: {e}")
 if set(groups)!=set(GROUPS): a.error("Candidate group set mismatch")
 overlap_rows=[]
 for ga,gb in combinations(GROUPS,2):
  if ga not in groups or gb not in groups: continue
  A=set(groups[ga]["numbers"]);B=set(groups[gb]["numbers"]); inter=A&B; union=A|B
  ma=set(groups[ga]["members"]);mb=set(groups[gb]["members"]);mi=ma&mb;mu=ma|mb
  sa=structure(A);sb=structure(B); keys=list(sa); struct_match=sum(sa[k]==sb[k] for k in keys)/len(keys)
  overlap_rows.append({"ticket_a":ga,"ticket_b":gb,"intersection_count":len(inter),"intersection_numbers":" ".join(map(str,sorted(inter))),"jaccard_similarity":len(inter)/len(union),"shared_models":len(mi),"shared_model_names":";".join(sorted(mi)),"model_signal_jaccard":len(mi)/len(mu),"structure_exact_feature_fraction":struct_match,"structure_a_json":json.dumps(sa,separators=(",",":")),"structure_b_json":json.dumps(sb,separators=(",",":")),"status":"WARNING" if len(inter)>=5 else "PASS"})
 all_slots=[n for g in groups.values() for n in g["numbers"]]; covered=set(m for g in groups.values() for m in g["members"])
 a.portfolio={"unique_numbers":len(set(all_slots)),"slots":len(all_slots),"model_coverage":len(covered),"model_names":";".join(sorted(covered)),"group_data":groups,"overlaps":overlap_rows}
 # Verify imported research is the checked-out GitHub snapshot and pin its data.
 if not GH_CORR.is_file(): a.error(f"Missing GitHub study correlation file: {GH_CORR}")
 else:
  ghhash=sha256(GH_CORR); a.asset_hashes["github_model_correlation"]=ghhash
  if ghhash!=EXPECTED_GH_CORR_SHA256: a.error(f"GitHub correlation SHA mismatch: {ghhash} != {EXPECTED_GH_CORR_SHA256}")
  if not LOCAL_CORR.is_file() or sha256(LOCAL_CORR)!=ghhash: a.error("Local and GitHub-synced model correlation files differ")
  try:
   head=subprocess.check_output(["git","-C",str(GH_ROOT),"rev-parse","HEAD"],text=True).strip()
   remote=subprocess.check_output(["git","-C",str(GH_ROOT),"rev-parse","origin/main"],text=True).strip()
   if head!=EXPECTED_GITHUB_HEAD or remote!=EXPECTED_GITHUB_HEAD: a.error(f"GitHub snapshot commit mismatch: HEAD={head}, origin/main={remote}")
  except Exception as e: a.error(f"Cannot verify GitHub research snapshot commit: {e}")
  try:
   _,corr=read_table(GH_CORR); pair=next(r for r in corr if r["model_a"]=="pair_residual_node" and r["model_b"]=="triple_residual_node"); a.github_pair=pair
   a.inventory.append(("github_model_correlation",str(GH_CORR),len(corr),"PASS",ghhash))
   a.info.append(f"GitHub post-hoc S006/S007: n={pair['n']}, ticket overlap={pair['mean_ticket_overlap']}, Jaccard={pair['mean_jaccard']}, hit corr={pair['hit_correlation']}, score corr={pair['score_correlation_latest_round']}; DUPLICATED_INFORMATION, not independent votes")
   if float(pair["hit_correlation"])>=.9 and float(pair["mean_jaccard"])>=.9: a.warn("GitHub batch001 pair/triple residual families are DUPLICATED_INFORMATION; do not count as two independent signals")
  except Exception as e: a.error(f"Cannot verify pair/triple correlation row: {e}")
 # Direct B-model pair/triple hit correlation from unique walk-forward rows.
 bymodel=defaultdict(dict)
 for (t,m),(_,_,h) in uniq_prediction_map(a).items(): bymodel[m][t]=h
 both=sorted(set(bymodel.get("pair_association",{})) & set(bymodel.get("triple_association",{})))
 direct=pearson([bymodel["pair_association"][t] for t in both],[bymodel["triple_association"][t] for t in both])
 a.direct_corr={"n":len(both),"hit_correlation":direct}
 pair_tickets=[]; triple_tickets=[]
 for t in sorted(set(bymodel.get("pair_association",{})) & set(bymodel.get("triple_association",{}))):
  pair_tickets.append(set(parse_nums(a.unique_predictions[(t,"pair_association")][0])))
  triple_tickets.append(set(parse_nums(a.unique_predictions[(t,"triple_association")][0])))
 overlaps=[len(x&y) for x,y in zip(pair_tickets,triple_tickets)]; jaccards=[len(x&y)/len(x|y) for x,y in zip(pair_tickets,triple_tickets)]
 a.model_independence.append({"model_a":"pair_association","model_b":"triple_association","n":len(both),"mean_ticket_overlap":statistics.mean(overlaps) if overlaps else "","mean_jaccard":statistics.mean(jaccards) if jaccards else "","hit_correlation":direct,"evidence_status":"POST_HOC_HISTORICAL","independence_status":"NOT_FLAGGED_AS_DUPLICATED_BY_B_TICKET/HIT METRICS","note":"This B-model pair is distinct from S006/S007 research families; do not transfer their correlation as if model identity were exact."})
 gh=a.github_pair
 a.model_independence.append({"model_a":"pair_residual_node (S006)","model_b":"triple_residual_node (S007)","n":int(gh.get("n",0)) if str(gh.get("n","")).isdigit() else "","mean_ticket_overlap":gh.get("mean_ticket_overlap",""),"mean_jaccard":gh.get("mean_jaccard",""),"hit_correlation":gh.get("hit_correlation",""),"evidence_status":"GITHUB_BATCH001_POST_HOC","independence_status":"DUPLICATED_INFORMATION","note":"GitHub-synced study_batch_001 relation; diagnostic only, not a direct substitute for B-model correlation."})
 # Scores are kept as separately labeled descriptive components. None are summed.
 a.components=[]; base=exact_baseline()
 for g in GROUPS:
  if g not in groups: continue
  row=groups[g]["row"]
  a.components.append({"candidate_group":g,"component":"historical_mean_hits_minus_random","value":float(row["mean_hits"])-base["mean"],"period":"201-1244","evidence_status":"HISTORICAL_DESCRIPTIVE_ONLY","independence":"DUPLICATED_INFORMATION","used_in_final_selection":"NO","note":"same historical rounds selected/ranked; descriptive only"})
  hist=[r for r in a.tables.get("group_detail",[]) if r.get("candidate_group")==g]
  for label,start,end in (("recent_100",1145,1244),("recent_50",1195,1244),("recent_44",1201,1244)):
   vals=[int(r["hits"]) for r in hist if start<=int(r["target_round"])<=end]
   a.components.append({"candidate_group":g,"component":"recent_mean_hits","value":statistics.mean(vals) if vals else "","period":label,"evidence_status":"DIAGNOSTIC_POST_HOC","independence":"DUPLICATED_INFORMATION","used_in_final_selection":"NO","note":"same historical target outcomes as full interval"})
  a.components.append({"candidate_group":g,"component":"independent_validation","value":"EXPECTED_UNAVAILABLE_FOR_1245","period":"prospective/untouched","evidence_status":"EXPECTED_UNAVAILABLE_FOR_1245","independence":"NOT_APPLICABLE","used_in_final_selection":"NO","note":"absence is expected; not required to generate before draw"})
  a.components.append({"candidate_group":g,"component":"model_independence_diagnostic","value":f"B pair/triple hit r={direct:.6f}; S006/S007 hit r={float(a.github_pair['hit_correlation']):.6f}","period":"historical 201-1244 / GitHub batch001","evidence_status":"POST_HOC_CORRELATION","independence":"SEPARATE_MODEL_IDENTITIES; S006/S007=DUPLICATED_INFORMATION","used_in_final_selection":"NO","note":"Do not transfer family correlation to B models; no correlation statistic is added as score"})

def generate_registered_candidates(a: Audit):
 """Build frozen S001-S008 cutoff-1244 tickets in memory; never read a target result."""
 entry=a.prospective_entries.get("run_batch.py")
 if not entry: a.error("Frozen prospective model source is absent from its manifest"); return
 model_path=ROOT/entry["file"]
 if model_path.resolve()!=STUDY_SOURCE.resolve() or sha256(model_path)!=entry["sha256"]:
  a.error("Frozen prospective model source path/hash mismatch"); return
 try:
  sys.path.insert(0,str(FRAMEWORK))
  spec=importlib.util.spec_from_file_location("frozen_study_batch001_v1",model_path)
  module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
  a.model_module=module
  draws=module.load_draws_through(RAW,1244)
  if [d.round for d in draws]!=list(range(1,1245)): raise ValueError("training prefix must be exactly rounds 1..1244")
  bank=module.candidate_bank()
  if len(bank)!=5000: raise ValueError(f"frozen structure bank size mismatch: {len(bank)}")
  module.BASE_PROFILES={q:module.prof(q,()) for q in bank}
  result=module.make_models(draws,bank)
  name_to_id={r["model_name"]:r["model_id"] for r in a.registry_rows}
  if set(result)!=set(name_to_id): raise ValueError("registered model names do not match frozen implementation")
  for name,(ticket,scores) in result.items():
   nums=tuple(sorted(map(int,ticket)))
   if len(nums)!=6 or len(set(nums))!=6 or any(n<1 or n>45 for n in nums): raise ValueError(f"invalid frozen candidate from {name}")
   if len(scores)!=45: raise ValueError(f"invalid score vector from {name}")
   a.registered_candidates[name_to_id[name]]={"model_name":name,"ticket":nums,"scores":list(scores),"family":next(r["family"] for r in a.registry_rows if r["model_id"]==name_to_id[name])}
  a.info.append("S001-S008 candidates calculated in memory from exactly rounds 1..1244; target 1245 actual/result not loaded")
 except Exception as e: a.error(f"Cannot build frozen prospective-registry candidate diagnostics: {e}")

def selector_contract(a: Audit):
 try:
  source=inspect.getsource(select_portfolio); tree=ast.parse(source)
  fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef))
  args={x.arg for x in fn.args.args}; forbidden={"group_metrics","group_detail","recent_metrics","historical_score","actual_numbers","hits","number_history"}
  names={x.id for x in ast.walk(fn) if isinstance(x,ast.Name)}
  blocked_tokens=("historical","posthoc","actual","recent","group_metric","number_history","baseline","hit_count")
  if args!={"model_outputs","model_module"}: a.error(f"Selector inputs are not fixed and isolated: {sorted(args)}")
  if names & forbidden: a.error(f"Post-hoc inputs leak into final selector: {sorted(names&forbidden)}")
  if any(token in source.lower() for token in blocked_tokens): a.error("Post-hoc/history token found in final selector source")
  if "random" in names or "sorted" not in names or "combinations" not in names: a.error("Selector deterministic/tie-break contract failed")
 except Exception as e: a.error(f"Cannot verify deterministic selector contract: {e}")

def select_portfolio(model_outputs, model_module):
 """Fixed rule: independent-family consensus plus two distinct-family model tickets."""
 ranks={mid:model_module.rank(model_outputs[mid]["scores"]) for mid in ("S001","S002","S003","S004","S006","S007")}
 families={"frequency":ranks["S001"],"gap_time":ranks["S002"],"momentum":ranks["S003"],"conditional":ranks["S004"],"structure":[45.0 if n in model_outputs["S005"]["ticket"] else 0.0 for n in range(1,46)],"relationship_residual":[(ranks["S006"][i]+ranks["S007"][i])/2 for i in range(45)]}
 consensus_scores=[sum(families[f][i] for f in families)/len(families) for i in range(45)]
 consensus=tuple(sorted(sorted(range(1,46),key=lambda n:(-consensus_scores[n-1],n))[:6]))
 id_family={"S001":"frequency","S002":"gap_time","S003":"momentum","S004":"conditional","S005":"structure","S006":"relationship_residual","S007":"relationship_residual"}
 eligible=sorted(id_family); pairs=[]
 for left,right in combinations(eligible,2):
  if id_family[left]==id_family[right]: continue
  left_nums=set(model_outputs[left]["ticket"]); right_nums=set(model_outputs[right]["ticket"]); consensus_set=set(consensus)
  profiles=[structure(x) for x in (consensus,left_nums,right_nums)]
  structure_coverage=sum(len({p[k] for p in profiles}) for k in profiles[0])
  pairs.append((-structure_coverage,-len(consensus_set|left_nums|right_nums),len(consensus_set&left_nums)+len(consensus_set&right_nums)+len(left_nums&right_nums),left,right))
 if not pairs: raise ValueError("No supplemental tickets from distinct signal families")
 _,_,_,left,right=min(pairs)
 lines=[{"line":1,"numbers":consensus,"model_sources":"S001;S002;S003;S004;S005;S006;S007","signal_sources":"frequency;gap_time;momentum;conditional;structure;relationship_residual (S006/S007 averaged as one family)","rule":"equal-family-rank consensus; S008 hybrid not counted again; ties lower number"}]
 for i,mid in ((2,left),(3,right)):
  lines.append({"line":i,"numbers":tuple(model_outputs[mid]["ticket"]),"model_sources":mid,"signal_sources":id_family[mid],"rule":"registered model candidate; distinct signal family; maximize portfolio number coverage"})
 return lines

# Existing helpers use this map populated during cutoff checks.
def uniq_prediction_map(a): return getattr(a,"unique_predictions",{})

# Wrap cutoff validation to retain unique rows for paired correlations.
_old_validate_cutoffs=validate_cutoffs
def validate_cutoffs(a):
 _old_validate_cutoffs(a); uniq={}
 for r in a.tables.get("full_predictions",[]):
  try: uniq[(int(r["target_round"]),r["model"])]=(r["predicted_numbers"],r["actual_numbers"],int(r["hits"]))
  except Exception: pass
 a.unique_predictions=uniq

def write_csv_new(path: Path, rows, fields):
 with path.open("w",newline="",encoding="utf-8-sig") as f:
  w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore");w.writeheader();w.writerows(rows)

def build_registered_overlap_rows(a: Audit):
 rows=[]
 for left,right in combinations(sorted(a.registered_candidates),2):
  x=a.registered_candidates[left]; y=a.registered_candidates[right]
  A=set(x["ticket"]); B=set(y["ticket"]); inter=A&B; union=A|B
  same=(left,right)==("S006","S007")
  rows.append({"candidate_source":"PROSPECTIVE_REGISTRY_MODEL_CANDIDATES","candidate_a":left,"candidate_b":right,"ticket_a":" ".join(map(str,sorted(A))),"ticket_b":" ".join(map(str,sorted(B))),"intersection_count":len(inter),"intersection_numbers":" ".join(map(str,sorted(inter))),"jaccard_similarity":len(inter)/len(union),"family_a":x["family"],"family_b":y["family"],"duplicated_information":"DUPLICATED_INFORMATION" if same or x["family"]=="ensemble" or y["family"]=="ensemble" else "NO_DIRECT_DUPLICATE_FLAG","structure_exact_feature_fraction":sum(structure(A)[k]==structure(B)[k] for k in structure(A))/len(structure(A)),"status":"ADVISORY_WARNING" if len(inter)>=5 else "DIAGNOSTIC"})
 for r in a.portfolio.get("overlaps",[]):
  rows.append({"candidate_source":"B_V1_POSTHOC_GROUP_REFERENCE","candidate_a":r["ticket_a"],"candidate_b":r["ticket_b"],"ticket_a":" ".join(map(str,a.portfolio["group_data"][r["ticket_a"]]["numbers"])),"ticket_b":" ".join(map(str,a.portfolio["group_data"][r["ticket_b"]]["numbers"])),"intersection_count":r["intersection_count"],"intersection_numbers":r["intersection_numbers"],"jaccard_similarity":r["jaccard_similarity"],"family_a":"B-model group","family_b":"B-model group","duplicated_information":"POST_HOC_GROUP_SIGNALS","structure_exact_feature_fraction":r["structure_exact_feature_fraction"],"status":"ADVISORY_WARNING" if r["intersection_count"]>=5 else "DIAGNOSTIC"})
 a.candidate_overlaps=rows

def write_csv_file(path: Path, rows, fields):
 with path.open("w",newline="",encoding="utf-8-sig") as f:
  w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore"); w.writeheader(); w.writerows(rows)

def write_audit_files(a: Audit, status: str):
 overlap=HERE/"candidate_overlap_v3.csv"; score=HERE/"score_components_v3.csv"; trace=HERE/"selection_trace_v3.csv"; audit=HERE/"input_audit_v3.md"
 write_csv_file(overlap,a.candidate_overlaps,["candidate_source","candidate_a","candidate_b","ticket_a","ticket_b","intersection_count","intersection_numbers","jaccard_similarity","family_a","family_b","duplicated_information","structure_exact_feature_fraction","status"])
 write_csv_file(score,a.components,["candidate_group","component","value","period","evidence_status","independence","used_in_final_selection","note"])
 trace=[]
 trace.append({"stage":"INPUT_AND_CUTOFF_CHECK","item":"raw+all required inputs","status":"PASS" if not a.errors else "BLOCKING_ERROR","rule":"exact raw SHA; 1..1244 only; every historical forecast cutoff t-1"})
 trace.append({"stage":"MODEL_CANDIDATES","item":"registered S001-S008","status":"IN_MEMORY_DIAGNOSTIC_ONLY" if len(a.registered_candidates)==8 else "BLOCKING_ERROR","rule":"frozen prospective registry and code hash; train rounds 1..1244; no outcome row"})
 trace.append({"stage":"MODEL_INDEPENDENCE","item":"S006/S007 and S008","status":"DUPLICATED_INFORMATION_DEDUPED","rule":"S006/S007 averaged as one relationship family; S008 hybrid excluded from an extra vote"})
 trace.append({"stage":"HISTORICAL_SCORE","item":"201-1244 candidate-group metrics","status":"HISTORICAL_DESCRIPTIVE_ONLY_EXCLUDED","rule":"not passed to select_portfolio; no ranking or weight"})
 trace.append({"stage":"DETERMINISM","item":"selector contract","status":"PASS" if not any("selector" in x.lower() or "post-hoc inputs leak" in x.lower() for x in a.errors) else "BLOCKING_ERROR","rule":"fixed six-family rank consensus; lexical model-pair tiebreak; lower-number score tiebreak"})
 trace.append({"stage":"PROSPECTIVE_RESULT","item":"1245 untouched outcome","status":"EXPECTED_UNAVAILABLE_FOR_1245","rule":"absence is not an error; never read future result"})
 trace.append({"stage":"FINAL_SELECTION","item":"three ticket selector","status":"NOT_RUN_IN_CHECK_ONLY","rule":"only GENERATE calls selector: independent families, structure coverage, unique numbers, lower pair overlap, model-id tie-break"})
 write_csv_file(HERE/"selection_trace_v3.csv",trace,["stage","item","status","rule"])
 lines=["# V3 input and gate audit", "", "Generated by `prepare_1245_final_three_lines_v3.py --check-only`. Model-level S001-S008 candidates were computed in memory solely for overlap/model checks; the final portfolio selector was not called.", "", f"Raw source: `{RAW}`", f"Raw SHA-256: `{a.asset_hashes.get('raw_data','NOT VERIFIED')}`", "", "## Gate status", "", f"- BLOCKING_ERROR: **{len(a.errors)}**", f"- ADVISORY_WARNING: **{len(a.warnings)}**", f"- EXPECTED_UNAVAILABLE: **{len(a.expected_unavailable)}**", f"- FINAL STATUS: **{status}**", "", "## Inventory", "", "|asset|path|rows|status|sha256|", "|---|---|---:|---|---|"]
 for name,path,n,st,digest in a.inventory: lines.append(f"|{name}|`{path}`|{n}|{st}|{digest}|")
 lines += ["", "## Blocking errors", ""] + ([f"- {x}" for x in a.errors] or ["- None"])
 lines += ["", "## Advisory warnings", ""] + ([f"- {x}" for x in a.warnings] or ["- None"])
 lines += ["", "## Expected unavailable", ""] + ([f"- {x}" for x in a.expected_unavailable] or ["- None"])
 lines += ["", "## Model / cutoff notes", ""] + ([f"- {x}" for x in a.info] or ["- No additional notes"])
 lines += ["", "## Final-selection separation", "", "- Historical candidate-group values are `HISTORICAL_DESCRIPTIVE_ONLY` and not inputs to `select_portfolio`.", "- S001-S008 candidate tickets are computed from the strict 1..1244 training prefix only and held in memory for diagnostic overlap analysis.", "- S006/S007 share one relationship-residual family vote; S008 is an ensemble diagnostic and is not counted as another independent vote.", "- No 1245 actual result was loaded or used.", "- Final selection executed: **NO**; final 3-line file generated: **NO**.", ""]
 audit.write_text("\n".join(lines),encoding="utf-8")

def generate_final_outputs(lines):
 csv_path=HERE/"final_three_lines_1245_v3.csv"; md_path=HERE/"final_three_lines_1245_v3.md"; trace_path=HERE/"final_selection_trace_v3.csv"
 if any(p.exists() for p in (csv_path,md_path,trace_path)): raise FileExistsError("V3 final output exists; refusing to overwrite")
 rows=[]; trace=[]
 for item in lines:
  nums=tuple(sorted(item["numbers"])); profile=structure(nums)
  rows.append({"line":item["line"],"numbers":" ".join(map(str,nums)),"model_sources":item["model_sources"],"signal_sources":item["signal_sources"],"selection_rule":item["rule"],"structure_profile_json":json.dumps(profile,separators=(",",":"))})
  trace.append({"stage":"candidate_to_final","line":item["line"],"numbers":" ".join(map(str,nums)),"model_sources":item["model_sources"],"signal_sources":item["signal_sources"],"rule":item["rule"],"historical_score_used":"NO"})
 for i,j in combinations(range(3),2):
  A=set(lines[i]["numbers"]);B=set(lines[j]["numbers"]);common=A&B;union=A|B
  trace.append({"stage":"portfolio_overlap","line":f"{i+1}-{j+1}","numbers":" ".join(map(str,sorted(common))),"model_sources":";".join((lines[i]["model_sources"],lines[j]["model_sources"])),"signal_sources":";".join((lines[i]["signal_sources"],lines[j]["signal_sources"])),"rule":f"intersection={len(common)}; Jaccard={len(common)/len(union):.6f}; structural_similarity={sum(structure(A)[k]==structure(B)[k] for k in structure(A))/len(structure(A)):.6f}","historical_score_used":"NO"})
 with csv_path.open("x",newline="",encoding="utf-8-sig") as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 with trace_path.open("x",newline="",encoding="utf-8-sig") as f:
  w=csv.DictWriter(f,fieldnames=["stage","line","numbers","model_sources","signal_sources","rule","historical_score_used"]);w.writeheader();w.writerows(trace)
 md=["# 1245 Final Three Lines — V3", "", "Generated after BLOCKING_ERROR checks passed. Advisory warnings and expected unavailable prospective outcomes remain visible.", "", "|Line|Numbers|Model sources|Signal sources|", "|---:|---|---|---|"]
 for r in rows: md.append(f"|{r['line']}|{r['numbers']}|{r['model_sources']}|{r['signal_sources']}|")
 md += ["", "## Portfolio checks", "", "Pairwise intersection, Jaccard, and structure-feature similarity are recorded in `final_selection_trace_v3.csv`. No historical candidate-group performance was used to select or rank lines."]
 with md_path.open("x",encoding="utf-8") as f: f.write("\n".join(md)+"\n")
def run(args):
 a=Audit(); manifest=read_manifest(a); audit_raw(a,manifest); audit_inputs(a,manifest); audit_prospective_framework(a); validate_cutoffs(a); build_diagnostics(a); selector_contract(a)
 if not a.errors: generate_registered_candidates(a)
 if a.registered_candidates: build_registered_overlap_rows(a)
 a.warn("Candidate-group 201-1244 results are HISTORICAL_DESCRIPTIVE_ONLY / POST_HOC; excluded from final score and selection")
 a.warn("Recent model performance uses only 44 rounds; small-sample diagnostic, not selection weight")
 if any(r["intersection_count"]>=5 for r in a.portfolio.get("overlaps",[])): a.warn("B-v1 candidate-group reference includes a 5/6 ticket overlap; diagnostic only; no arbitrary replacement")
 if any(r["intersection_count"]>=5 for r in a.candidate_overlaps if r["candidate_source"]=="PROSPECTIVE_REGISTRY_MODEL_CANDIDATES"):
  a.warn("At least one S001-S008 candidate pair has 5/6 overlap; advisory only; final portfolio rule handles candidate tickets deterministically")
 a.expected_unavailable.append("1245 prospective/untouched actual result and post-draw performance: EXPECTED_UNAVAILABLE_FOR_1245; absence is not a blocking error")
 status="NOT_READY" if a.errors else "READY_WITH_WARNINGS" if a.warnings else "READY"
 if args.check_only:
  write_audit_files(a,status)
  print("CHECK-ONLY: final selector not called; no final tickets generated")
 else:
  print("GENERATE requested; applying blocking checks before selection")
 print(f"BLOCKING_ERROR={len(a.errors)}")
 print(f"ADVISORY_WARNING={len(a.warnings)}")
 print(f"EXPECTED_UNAVAILABLE={len(a.expected_unavailable)}")
 print(f"FINAL_STATUS={status}")
 for w in a.warnings: print("ADVISORY_WARNING:",w)
 for x in a.expected_unavailable: print("EXPECTED_UNAVAILABLE_FOR_1245:",x)
 for e in a.errors: print("BLOCKING_ERROR:",e)
 if a.errors: return 2
 if args.check_only: return 0
 try:
  lines=select_portfolio(a.registered_candidates,a.model_module)
  generate_final_outputs(lines)
  print("FINAL_OUTPUTS_CREATED: final_three_lines_1245_v3.md, final_three_lines_1245_v3.csv, final_selection_trace_v3.csv")
  return 0
 except Exception as e:
  print(f"BLOCKING_ERROR: final generation failed before output completion: {e}"); return 3
def main():
 ap=argparse.ArgumentParser(description="V3 validation/generation gate; never reads a 1245 actual result")
 mode=ap.add_mutually_exclusive_group(required=True); mode.add_argument("--check-only",action="store_true"); mode.add_argument("--generate",action="store_true")
 return run(ap.parse_args())
if __name__=="__main__": raise SystemExit(main())
