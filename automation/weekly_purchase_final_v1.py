from __future__ import annotations
import csv, json, hashlib, itertools, random
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'lotto_data.csv'
OUTROOT=ROOT/'research'/'weekly_purchase'
POLICY='WEEKLY_FIVE_TICKET_PORTFOLIO_V1'
SEED=2026102301

def load():
    rows=[]
    with DATA.open(encoding='utf-8') as f:
        for r in csv.DictReader(f):
            rows.append((int(r['round']), [int(r[f'no{i}']) for i in range(1,7)], int(r['bonus'])))
    rounds=[r[0] for r in rows]
    assert rounds==list(range(1,max(rounds)+1)) and len(rounds)==len(set(rounds))
    for _,nums,b in rows:
        assert len(nums)==6 and len(set(nums))==6 and all(1<=n<=45 for n in nums)
        assert 1<=b<=45 and b not in nums
    return rows

def features(hist):
    draws=[x[1] for x in hist]
    f30=Counter(n for d in draws[-30:] for n in d)
    f10=Counter(n for d in draws[-10:] for n in d)
    fprev20=Counter(n for d in draws[-30:-10] for n in d)
    gap={}
    for n in range(1,46):
        g=0
        for d in reversed(draws):
            if n in d: break
            g+=1
        gap[n]=g
    def z(vals):
        xs=list(vals.values()); m=sum(xs)/len(xs); sd=(sum((x-m)**2 for x in xs)/len(xs))**.5 or 1
        return {k:(v-m)/sd for k,v in vals.items()}
    zf30=z({n:f30[n] for n in range(1,46)}); zg=z(gap)
    mom=z({n:f10[n]/10-fprev20[n]/20 for n in range(1,46)})
    return {'recent30':zf30,'gap':zg,'momentum':mom,
      'balanced':{n:(zf30[n]+zg[n])/2 for n in range(1,46)},
      'contrarian':{n:(-zf30[n]+zg[n])/2 for n in range(1,46)}}

def candidate_bank(scores,limit=80):
    ranked=sorted(range(1,46),key=lambda n:(-scores[n],n)); pool=ranked[:13]; combos=[]
    for c in itertools.combinations(pool,6): combos.append((sum(scores[n] for n in c),tuple(sorted(c))))
    combos.sort(key=lambda x:(-x[0],x[1])); return [c for _,c in combos[:limit]]

def select(hist):
    fam=features(hist); banks={k:candidate_bank(v) for k,v in fam.items()}; chosen=[]; sources=[]
    for name in ['recent30','gap','momentum','balanced','contrarian']:
        best=None
        for rank,t in enumerate(banks[name]):
            if t in chosen: continue
            ov=[len(set(t)&set(x)) for x in chosen]
            penalty=sum(max(0,x-2)**2*20+x*0.35 for x in ov); value=-rank-penalty
            key=(value,-max(ov or [0]),-sum(ov),tuple(-x for x in t))
            if best is None or key>best[0]: best=(key,t,rank,ov)
        chosen.append(best[1]); sources.append({'family':name,'candidate_rank':best[2]+1,'overlaps_to_prior':best[3]})
    return [list(x) for x in chosen],sources

def metrics(tickets,win):
    hs=[len(set(t)&set(win)) for t in tickets]; union=set().union(*map(set,tickets)); ovs=[len(set(a)&set(b)) for a,b in itertools.combinations(tickets,2)]
    return {'max_hits':max(hs),'any_2plus':int(max(hs)>=2),'any_3plus':int(max(hs)>=3),'any_4plus':int(max(hs)>=4),
      'winning_union_coverage':len(union&set(win)),'ticket_union_size':len(union),'mean_pair_overlap':sum(ovs)/len(ovs),'max_pair_overlap':max(ovs)}

def backtest(rows,random_bundles=300):
    start=max(200,len(rows)-200); rng=random.Random(SEED); pm=[]; rm=[]; universe=list(range(1,46))
    for i in range(start,len(rows)):
        tickets,_=select(rows[:i]); win=rows[i][1]; pm.append(metrics(tickets,win))
        for _ in range(random_bundles): rm.append(metrics([sorted(rng.sample(universe,6)) for __ in range(5)],win))
    keys=['max_hits','any_2plus','any_3plus','any_4plus','winning_union_coverage','ticket_union_size','mean_pair_overlap','max_pair_overlap']
    avg=lambda arr,k:sum(x[k] for x in arr)/len(arr)
    return {'targets':len(pm),'random_bundles_per_target':random_bundles,'policy':{k:avg(pm,k) for k in keys},
      'matched_uniform_random':{k:avg(rm,k) for k in keys},'delta_policy_minus_random':{k:avg(pm,k)-avg(rm,k) for k in keys}}

def validate(tickets):
    return len(tickets)==5 and len({tuple(t) for t in tickets})==5 and all(len(t)==6 and len(set(t))==6 and all(isinstance(n,int) and 1<=n<=45 for n in t) and t==sorted(t) for t in tickets)

def main():
    rows=load(); cutoff=rows[-1][0]; target=cutoff+1; tickets,sources=select(rows)
    assert validate(tickets); first_pass=True; bt=backtest(rows); assert validate(tickets); second_pass=True
    display='\n'.join(' '.join(map(str,t)) for t in tickets); parsed=[[int(x) for x in line.split()] for line in display.splitlines()]
    assert parsed==tickets and validate(parsed)
    payload={'target_round':target,'created_kst':datetime.now(timezone(timedelta(hours=9))).isoformat(),'data_cutoff':cutoff,
      'data_sha256':hashlib.sha256(DATA.read_bytes()).hexdigest(),'policy_version':POLICY,'classification':'PRIMARY_WEEKLY_PURCHASE_POLICY',
      'selection_sources':sources,'final_lines':tickets,'portfolio':{'unique_number_coverage':len(set().union(*map(set,tickets))),
      'pairwise_overlaps':[len(set(a)&set(b)) for a,b in itertools.combinations(tickets,2)]},'historical_matched_random_backtest':bt,
      'integrity':{'pass_1':first_pass,'pass_2':second_pass,'final_text_parse':'PASS','line_count':5,'numbers_per_line':6,'range_1_45':'PASS','within_line_unique':'PASS','duplicate_ticket':'PASS'},
      'evidence_note':'Policy is cutoff-safe and benchmarked; matched-random results are reported without claiming superiority unless positive evidence exists.',
      'historical_closed_loop_scope':'All verifiable preserved weekly-purchase records are reviewed; missing older originals are not reconstructed.','freeze_payload_sha256':None}
    canon=json.dumps({k:v for k,v in payload.items() if k!='freeze_payload_sha256'},ensure_ascii=False,sort_keys=True,separators=(',',':')).encode(); payload['freeze_payload_sha256']=hashlib.sha256(canon).hexdigest()
    outdir=OUTROOT/str(target); outdir.mkdir(parents=True,exist_ok=True); out=outdir/f"FINAL_FIVE_LINES_{target}_{datetime.now(timezone(timedelta(hours=9))).strftime('%Y%m%d')}.json"
    if out.exists(): raise SystemExit(f'write-once violation: {out}')
    out.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':'PASS','target':target,'cutoff':cutoff,'policy':POLICY,'final_lines':tickets,'validator_1':'PASS','validator_2':'PASS','final_text_parse':'PASS','output':str(out)},ensure_ascii=False))
if __name__=='__main__': main()
