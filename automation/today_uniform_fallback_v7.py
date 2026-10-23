#!/usr/bin/env python3
from __future__ import annotations
import csv, hashlib, json, math, random, statistics
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'lotto_data.csv'
OUT=ROOT/'analysis/2026-10-23/TODAY_UNIFORM_FALLBACK_1247_V7.json'
FREEZE=ROOT/'research/weekly_purchase/1247/FINAL_FIVE_LINES_1247_20261023_V7.json'
KST=timezone(timedelta(hours=9))
POLICY='V7_UNIFORM_30_UNIQUE_FALLBACK'
TARGET=1247
CUTOFF=1246
MC_PER_TARGET=200
SEED_TAG='2026-10-23-v7-prospective-freeze'

def load_rows():
    rows=[]
    with DATA.open(encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            nums=tuple(sorted(int(r[f'no{i}']) for i in range(1,7)))
            rows.append((int(r['round']),nums,int(r['bonus'])))
    assert [x[0] for x in rows]==list(range(1,CUTOFF+1))
    assert len(rows)==CUTOFF
    return rows

def deterministic_bundle(history_bytes: bytes, target: int):
    digest=hashlib.sha256(history_bytes+b'|'+POLICY.encode()+b'|'+SEED_TAG.encode()+b'|'+str(target).encode()).hexdigest()
    rng=random.Random(int(digest[:16],16))
    nums=rng.sample(range(1,46),30)
    rng.shuffle(nums)
    lines=[sorted(nums[i*6:(i+1)*6]) for i in range(5)]
    return lines,digest

def validate(lines):
    if len(lines)!=5 or len({tuple(x) for x in lines})!=5:return False
    if not all(len(x)==6 and list(x)==sorted(x) and len(set(x))==6 and all(type(n) is int and 1<=n<=45 for n in x) for x in lines):return False
    flat=[n for x in lines for n in x]
    return len(flat)==30 and len(set(flat))==30

def metrics(lines,actual):
    ss=[set(x) for x in lines];a=set(actual);hits=[len(s&a) for s in ss]
    return {
      'max_hits':max(hits),'any2':int(max(hits)>=2),'any3':int(max(hits)>=3),'any4':int(max(hits)>=4),
      'any5':int(max(hits)>=5),'any6':int(max(hits)>=6),
      'winning_union_coverage':len(set().union(*ss)&a),'union_size':len(set().union(*ss)),
      'mean_overlap':statistics.mean(len(ss[i]&ss[j]) for i in range(5) for j in range(i+1,5)),
      'max_overlap':max(len(ss[i]&ss[j]) for i in range(5) for j in range(i+1,5))
    }

def random_30_unique(rng):
    nums=rng.sample(range(1,46),30);rng.shuffle(nums)
    return [sorted(nums[i*6:(i+1)*6]) for i in range(5)]

def avg(arr,k):return statistics.mean(float(x[k]) for x in arr)

def historical_bytes(rows,i):
    # Canonical history through target-1 only.
    return ('\n'.join(f"{r}:{','.join(map(str,n))}:{b}" for r,n,b in rows[:i])+'\n').encode()

def main():
    rows=load_rows()
    policy=[];matched=[]
    # Full leakage-safe evaluation from target 201 through 1246.
    for i in range(200,len(rows)):
        target=rows[i][0];actual=rows[i][1]
        lines,_=deterministic_bundle(historical_bytes(rows,i),target)
        assert validate(lines)
        pm=metrics(lines,actual);policy.append(pm)
        rng=random.Random(9100000+target)
        for _ in range(MC_PER_TARGET):matched.append(metrics(random_30_unique(rng),actual))
    keys=['max_hits','any2','any3','any4','any5','any6','winning_union_coverage','union_size','mean_overlap','max_overlap']
    ps={k:avg(policy,k) for k in keys};rs={k:avg(matched,k) for k in keys};delta={k:ps[k]-rs[k] for k in keys}
    # The fallback is the same probability family as the matched baseline by construction.
    # Historical deltas are diagnostic only; no superiority gate or claim is permitted.
    exact_union_expected=6*(30/45)
    data_sha=hashlib.sha256(DATA.read_bytes()).hexdigest()
    final_lines,seed_sha=deterministic_bundle(DATA.read_bytes(),TARGET)
    assert validate(final_lines);v1='PASS'
    assert validate(final_lines);v2='PASS'
    text='\n'.join(' '.join(map(str,x)) for x in final_lines)
    parsed=[[int(y) for y in row.split()] for row in text.splitlines()]
    assert parsed==final_lines and validate(parsed)
    payload={
      'created_kst':datetime.now(KST).isoformat(),'target_round':TARGET,'data_cutoff':CUTOFF,
      'policy':POLICY,'classification':'PRIMARY_ACTUAL_PURCHASE_FALLBACK_AFTER_MODEL_REJECTION',
      'reason':'Strict model validation found no reproducible predictive edge; use the predeclared non-predictive 30-unique diversification fallback rather than force an unvalidated model.',
      'data_sha256':data_sha,'seed_sha256':seed_sha,'selection':'uniform sample of 30 distinct numbers from 1..45, then uniform deterministic partition into five disjoint six-number tickets',
      'predictive_superiority_claim':false if False else False,
      'mathematical_properties':{'ticket_count':5,'numbers_per_ticket':6,'unique_union_size':30,'cross_ticket_overlap':0,'expected_winning_union_coverage':exact_union_expected},
      'walkforward_targets':len(policy),'matched_random_bundles_per_target':MC_PER_TARGET,
      'scorecard':{'policy':ps,'matched_30_unique_random':rs,'diagnostic_delta':delta,'interpretation':'Same probability family by construction; deltas are finite-sample noise and are not used to claim an edge.'},
      'final_lines':final_lines,
      'integrity':{'validator_1':v1,'validator_2':v2,'final_text_parse':'PASS','line_count':5,'numbers_per_line':6,'range_1_45':'PASS','within_line_unique':'PASS','duplicate_ticket':'PASS','cross_line_unique_30':'PASS','stored_vs_display':'PASS'}
    }
    # Python JSON boolean is created normally; avoid any post-write mutation.
    payload['predictive_superiority_claim']=False
    canon=json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
    payload['freeze_payload_sha256']=hashlib.sha256(canon).hexdigest()
    if FREEZE.exists():raise SystemExit(f'write-once violation: {FREEZE}')
    OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    FREEZE.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    stored=json.loads(FREEZE.read_text(encoding='utf-8'))
    assert stored['final_lines']==final_lines and validate(stored['final_lines'])
    assert json.loads(OUT.read_text(encoding='utf-8'))['final_lines']==stored['final_lines']
    print(json.dumps({'status':'PASS','target':TARGET,'cutoff':CUTOFF,'policy':POLICY,'final_lines':final_lines,'validator_1':'PASS','validator_2':'PASS','final_text_parse':'PASS','stored_vs_display':'PASS','scorecard':payload['scorecard'],'freeze':str(FREEZE)},ensure_ascii=False))
if __name__=='__main__':main()
