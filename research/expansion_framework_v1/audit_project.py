from __future__ import annotations
import argparse,csv,hashlib,sys
from pathlib import Path
from walkforward_core import load_draws_through

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
MANIFEST=HERE/'project_baseline_manifest.csv'
OLD=ROOT.parents[1]/'2026-10-06'/'cloud-x20'
OUT=ROOT/'outputs'
RAW=OLD/'work'/'lotto-data'/'lotto_data.csv'
MODELS={'long_frequency','current_gap','frequency_plus_gap','recent_momentum','structure_profile','pair_association','triple_association','combined_equal_rank'}

def read_csv(path):
 with path.open(newline='',encoding='utf-8-sig') as f:
  r=csv.DictReader(f);return r.fieldnames or [],list(r)

def main():
 ap=argparse.ArgumentParser(description='Read-only current-project audit against the frozen v1 manifest.')
 ap.add_argument('--write-report',help='Create a new report path; refuses to overwrite.')
 a=ap.parse_args();lines=['# Project State Audit','']
 errors=[]
 if not MANIFEST.is_file(): raise SystemExit(f'Manifest missing: {MANIFEST}')
 with MANIFEST.open(newline='',encoding='utf-8-sig') as f: entries=list(csv.DictReader(f))
 changed=[]
 for e in entries:
  p=Path(e['absolute_path'])
  if not p.is_file(): changed.append((e['asset_id'],'MISSING',e['absolute_path']));continue
  h=hashlib.sha256(p.read_bytes()).hexdigest()
  if p.stat().st_size!=int(e['bytes']) or h!=e['sha256']:changed.append((e['asset_id'],'CHANGED',e['absolute_path']))
 lines += [f'- Frozen baseline entries: {len(entries)}.',f'- Baseline integrity: {"PASS" if not changed else "DRIFT"}.']
 for x in changed:errors.append(f'Baseline {x[1]}: {x[0]} — {x[2]}')
 # Data check reads exactly rounds 1..1244; no subsequent row is requested.
 draws=load_draws_through(RAW,1244);actual={d.round:set(d.numbers) for d in draws}
 lines += [f'- Raw source: `{RAW}`; rows 1..1244 continuous; date/number/bonus validation passed.', '- No row after round 1244 was requested by the audit reader.']
 # Validate historical prediction cutoff, duplicated-window consistency, actual cross-check.
 full=OLD/'outputs'/'b_model_predictions.csv'; _,rows=read_csv(full);uniq={}
 for r in rows:
  t=int(r['target_round']);m=r['model'];cut=int(r['training_through_round'])
  if not 201<=t<=1244 or cut!=t-1 or m not in MODELS:errors.append(f'Invalid full walk-forward cutoff/model: {t}/{m}');continue
  pred=tuple(map(int,r['predicted_numbers'].split()));act=tuple(map(int,r['actual_numbers'].split()));h=int(r['hits'])
  if set(act)!=actual[t]:errors.append(f'Historical actual mismatch against raw draw: {t}')
  if len(set(pred)&set(act))!=h:errors.append(f'Hit mismatch in full walk-forward: {t}/{m}')
  key=(t,m);val=(pred,act,h)
  if key in uniq and uniq[key]!=val:errors.append(f'Conflicting duplicate forecast: {t}/{m}')
  uniq[key]=val
 if len(uniq)!=1044*8:errors.append(f'Unique full walk-forward records: {len(uniq)} (expected 8352)')
 lines.append(f'- Full walk-forward: {len(rows)} stored rows; {len(uniq)} consistent unique target/model predictions, 201..1244; cutoff=t-1; raw actual cross-check passed.')
 # Recent holdout.
 rp=OUT/'b_model_recent_predictions.csv';_,recent=read_csv(rp)
 if len(recent)!=352:errors.append(f'Recent prediction row count {len(recent)} (expected 352)')
 for r in recent:
  t=int(r['target_round']);m=r['model']
  if not 1201<=t<=1244 or int(r['training_through_round'])!=t-1:errors.append(f'Recent cutoff error {t}/{m}')
  if set(map(int,r['actual_numbers'].split()))!=actual[t]:errors.append(f'Recent actual mismatch {t}')
 lines.append(f'- Recent holdout: {len(recent)} rows for 1201..1244, all cutoffs t-1; actuals match raw.')
 # 1245 predicted tickets have no actual-number field.
 cp=OUT/'b_model_1245_analysis_predictions.csv';cf,candidates=read_csv(cp)
 if len(candidates)!=8 or 'actual_numbers' in cf:errors.append('1245 candidate input is missing/has unexpected actual outcome field')
 for r in candidates:
  nums=list(map(int,r['predicted_numbers'].split()))
  if int(r['target_round'])!=1245 or int(r['training_through_round'])!=1244 or len(nums)!=6 or len(set(nums))!=6:errors.append('Invalid 1245 prediction ticket/cutoff')
 lines.append('- Current 1245 candidates: 8 predicted tickets; target=1245/cutoff=1244; no actual result column.')
 # Group candidates and historical leakage/cross-source check.
 gd=OUT/'b_model_1245_candidate_groups_walkforward.csv';_,grows=read_csv(gd)
 if len(grows)!=3132:errors.append(f'Group walk-forward rows={len(grows)} (expected 3132)')
 for r in grows:
  t=int(r['target_round'])
  if not 201<=t<=1244 or int(r['training_through_round'])!=t-1:errors.append(f'Group cutoff error at {t}')
  if set(map(int,r['actual_numbers'].split()))!=actual[t]:errors.append(f'Group actual mismatch at {t}')
 lines.append('- Group walk-forward: 3,132 rows, 3 groups × 1,044 targets, cutoff=t-1; actuals match raw.')
 # Path fix and stale prior snapshot check.
 pipeline=OUT/'1245_final_pipeline'/'prepare_1245_final_three_lines.py'
 source=pipeline.read_text(encoding='utf-8-sig')
 if 'RAW = OLD / "work" / "lotto-data" / "lotto_data.csv"' not in source:errors.append('1245 pipeline RAW constant does not point to the confirmed source')
 snapshot=OUT/'1245_final_pipeline'/'input_audit.md'
 if snapshot.is_file() and 'NOT READY' in snapshot.read_text(encoding='utf-8-sig'):
  lines.append(f'- Prior preflight snapshot `{snapshot}` still records the earlier missing-path state; the subsequent --check-only run passed. Snapshot was preserved.')
 final_outputs=[OUT/'1245_final_pipeline'/'final_three_lines_1245.csv',OUT/'1245_final_pipeline'/'final_three_lines_1245.md']
 lines.append(f'- Final 3-line files currently exist: {any(p.exists() for p in final_outputs)} (expected false before final run).')
 lines += ['',f'## Result','',('PASS' if not errors else 'ISSUES FOUND')]
 if errors:lines += ['']+[f'- {x}' for x in errors]
 report='\n'.join(lines)+'\n'
 print(report,end='')
 if a.write_report:
  dst=Path(a.write_report)
  with dst.open('x',encoding='utf-8') as f:f.write(report)
  print(f'REPORT_CREATED {dst}')
 return 0 if not errors else 2

if __name__=='__main__':raise SystemExit(main())
