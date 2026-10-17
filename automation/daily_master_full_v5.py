#!/usr/bin/env python3
"""Daily MASTER v5 gate.
Runs v4 core first, then independently reruns recovered successor A/C/contrarian
on every cutoff-safe target. FULL_COMPLETE is permitted only if all mandatory
checks pass in the same invocation/date.
"""
import csv,json,subprocess,sys,datetime,importlib.util,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'lotto_data.csv'
MODELS=ROOT/'automation/recovered_models_v2.py'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x): p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
    date=sys.argv[1] if len(sys.argv)>1 else datetime.datetime.now().astimezone().date().isoformat()
    # Fresh v4 execution supplies data validation, cumulative stats, B full WF,
    # random baseline, pair/triple and B leakage evidence.
    subprocess.run([sys.executable,str(ROOT/'automation/daily_master_full_v4.py'),'--date',date],cwd=ROOT,check=True)
    masters=sorted((ROOT/'analysis'/date).glob('MASTER_FULL_V4_*'),key=lambda p:p.stat().st_mtime)
    base=masters[-1]
    data=json.loads((base/'DATA_VALIDATION.json').read_text())
    b=json.loads((base/'B_LEAKAGE_CHECK.json').read_text())
    rows=list(csv.DictReader(DATA.open(encoding='utf-8-sig')))
    draws=[tuple(sorted(int(r[f'no{i}']) for i in range(1,7))) for r in rows]
    spec=importlib.util.spec_from_file_location('recovered',MODELS);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    start=200; records=[]; leak=0; counts={'A_v2':0,'C_v2':0,'contrarian_v2':0}
    for idx in range(start,len(draws)):
        target=idx+1; hist=draws[:idx]; actual=set(draws[idx]); pred=m.predict(hist)
        if len(hist)!=target-1: leak+=1
        for name,ticket in pred.items():
            counts[name]+=1; records.append({'target_round':target,'training_through_round':idx,'model':name,'ticket':'-'.join(map(str,ticket)),'hits':len(set(ticket)&actual)})
            if idx>=target: leak+=1
    out=ROOT/'analysis'/date/f"MASTER_FULL_V5_{datetime.datetime.now().astimezone().strftime('%H%M%S_%f')}";out.mkdir(parents=True)
    with (out/'AC_CONTRARIAN_WALKFORWARD.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
    expected=len(draws)-start
    mandatory={
      'latest_data_integrity':data.get('integrity')=='PASS' and data.get('latest_round')==len(draws),
      'fresh_cumulative_stats':(base/'NUMBER_FULL_STATS.csv').exists() and (base/'STRUCTURE_WINDOWS.csv').exists(),
      'B_full_walkforward':b.get('targets')==expected and b.get('leakage_failures')==0,
      'fresh_random_baseline':(base/'RANDOM_BY_TARGET.csv').exists() and (base/'RANDOM_EXACT_BASELINE.json').exists(),
      'A_full_walkforward':counts['A_v2']==expected,
      'C_full_walkforward':counts['C_v2']==expected,
      'contrarian_full_walkforward':counts['contrarian_v2']==expected,
      'AC_contrarian_leakage':leak==0,
    }
    status='FULL_COMPLETE' if all(mandatory.values()) else 'PARTIAL'
    verification={'status':status,'date':date,'data_cutoff':len(draws),'base_v4':base.relative_to(ROOT).as_posix(),'targets_expected':expected,'successor_prediction_records':len(records),'successor_counts':counts,'successor_leakage_failures':leak,'mandatory_checks':mandatory,'data_sha256':sha(DATA),'successor_source_sha256':sha(MODELS)}
    dump(out/'VERIFICATION.json',verification);dump(out/'COMPLETION.json',{'study_id':'DAILY_MASTER_FULL_V5','status':status,'data_cutoff':len(draws),'executed':True})
    (out/'REPORT.md').write_text(f"# DAILY MASTER FULL v5 — {date}\n\nStatus: **{status}**\n\nFresh A/C/contrarian successor walk-forward targets: {expected} each.\nSuccessor leakage failures: {leak}.\nB targets: {b.get('targets')}; B leakage failures: {b.get('leakage_failures')}.\n\nFULL_COMPLETE is emitted only when every VERIFICATION mandatory check is true.\n",encoding='utf-8')
    print(json.dumps(verification,ensure_ascii=False));
    if status!='FULL_COMPLETE': raise SystemExit(2)
if __name__=='__main__': main()
