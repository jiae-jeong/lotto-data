#!/usr/bin/env python3
from __future__ import annotations
import csv, importlib.util, itertools, json, math, random, statistics
from collections import Counter, defaultdict, deque
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'lotto_data.csv'
B_SOURCE=ROOT/'research/1245_final_pipeline_v3/recovered_original_assets/b_model_backtest.py'
AC_SOURCE=ROOT/'automation/recovered_models_v2.py'
OUT=ROOT/'analysis/2026-10-23/TODAY_ONLINE_ENSEMBLE_1247_V2.json'
KST=timezone(timedelta(hours=9))
B_NAMES=('long_frequency','current_gap','frequency_plus_gap','recent_momentum','structure_profile','pair_association','triple_association','combined_equal_rank')
AC_NAMES=('A_v2','C_v2','contrarian_v2')
MODELS=B_NAMES+AC_NAMES
ETAS=(0.15,0.30,0.60)
DECAYS=(0.97,0.99,1.0)
BLOCK=50
BOOT=6000
SEED=202610231235

def imp(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def load_draws():
    rows=[]
    with DATA.open(encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            rows.append({'round':int(r['round']),'date':r['date'],'nums':tuple(sorted(int(r[f'no{i}']) for i in range(1,7)))})
    assert [r['round'] for r in rows]==list(range(1,len(rows)+1)) and rows[-1]['round']==1246
    return rows

def exact():
    den=math.comb(45,6);p=[math.comb(6,k)*math.comb(39,6-k)/den for k in range(7)]
    return {'mean':sum(k*p[k] for k in range(7)),'ge2':sum(p[2:]),'ge3':sum(p[3:])}

def softmax(scores):
    mx=max(scores.values()); e={k:math.exp(v-mx) for k,v in scores.items()}; z=sum(e.values()); return {k:v/z for k,v in e.items()}

def ensemble_ticket(preds, perf, eta):
    w=softmax({m:eta*perf[m] for m in MODELS})
    ns={n:sum(w[m] for m in MODELS if n in preds[m]) for n in range(1,46)}
    # outcome-blind structure guard: score first; only mild deterministic tie-break toward normal spread.
    pool=sorted(range(1,46),key=lambda n:(-ns[n],n))[:14]
    best=None
    for t in itertools.combinations(pool,6):
        odd=sum(n%2 for n in t); low=sum(n<=22 for n in t); bands=len({(n-1)//10 for n in t})
        pen=.05*abs(odd-3)+.04*abs(low-3)-.01*bands
        val=sum(ns[n] for n in t)-pen
        if best is None or val>best[0] or (val==best[0] and t<best[1]): best=(val,t)
    return tuple(sorted(best[1])),w

def portfolio_from_variants(variant_tickets, variant_scores):
    # choose five distinct candidates, maximizing past score and penalizing overlap.
    cand=[]
    for name,t in variant_tickets.items():
        if t not in [x[1] for x in cand]: cand.append((name,t,variant_scores[name]))
    cand.sort(key=lambda x:(-x[2],x[0]))
    chosen=[]
    while cand and len(chosen)<5:
        best=None
        for x in cand:
            ov=sum(len(set(x[1])&set(y[1])) for y in chosen)
            obj=x[2]-.10*ov
            if best is None or obj>best[0] or (obj==best[0] and x[0]<best[1][0]): best=(obj,x)
        chosen.append(best[1]); cand=[x for x in cand if x[0]!=best[1][0]]
    return chosen

def blocks_ci(vals,base,alpha,seed):
    blocks=[vals[i:i+BLOCK] for i in range(0,len(vals),BLOCK)]
    rng=random.Random(seed); reps=[]
    for _ in range(BOOT):
        sample=[blocks[rng.randrange(len(blocks))] for __ in range(len(blocks))]
        flat=[x for b in sample for x in b]; reps.append(statistics.mean(flat)-base)
    reps.sort(); lo=reps[int((alpha/2)*(len(reps)-1))]; hi=reps[int((1-alpha/2)*(len(reps)-1))]
    return [lo,hi]

def block_share(vals,base):
    bs=[statistics.mean(vals[i:i+BLOCK])-base for i in range(0,len(vals),BLOCK)]
    return sum(x>0 for x in bs)/len(bs),bs

def main():
    draws=load_draws(); b=imp(B_SOURCE,'b_oe2'); ac=imp(AC_SOURCE,'ac_oe2')
    bank=b.feature_structure_bank(b.make_structure_bank());freq=[0]*45;last=[0]*45;pc=Counter();tc=Counter();profiles=[Counter() for _ in range(6)]
    for d in draws[:200]:
        for x in d['nums']:freq[x-1]+=1;last[x-1]=d['round']
        pc.update(itertools.combinations(d['nums'],2));tc.update(itertools.combinations(d['nums'],3));pr=b.structure_profile(d['nums'],None)
        for i,v in enumerate(pr[:5]):profiles[i][v]+=1
    for i in range(1,200):profiles[5][b.structure_profile(draws[i]['nums'],draws[i-1]['nums'])[5]]+=1

    variants=[f'e{eta}_d{decay}' for eta in ETAS for decay in DECAYS]
    perf={v:{m:0.0 for m in MODELS} for v in variants}
    rec={v:[] for v in variants}; model_hits={m:[] for m in MODELS}; port=[]
    current_preds=None; current_tickets={}; current_weights={}
    for idx in range(200,len(draws)+1):
        target=idx+1
        hist_nums=[d['nums'] for d in draws[:idx]]
        bpred=b.predictions_for_round(draws,idx,freq,last,pc,tc,profiles,bank)
        apred=ac.predict(hist_nums)
        preds={**bpred,**apred}; assert set(preds)==set(MODELS)
        for v in variants:
            eta=float(v.split('_')[0][1:]); t,w=ensemble_ticket(preds,perf[v],eta)
            current_tickets[v]=t; current_weights[v]=w
        current_preds=preds
        if idx==len(draws): break
        actual=set(draws[idx]['nums'])
        vh={}
        for v in variants:
            h=len(set(current_tickets[v])&actual); rec[v].append((target,h)); vh[v]=h
        for m in MODELS:model_hits[m].append((target,len(set(preds[m])&actual)))
        # portfolio is built strictly from pre-outcome rolling past variant scores.
        scores={v:(statistics.mean([h for _,h in rec[v][-200:-1]]) if len(rec[v])>1 else 0.8) for v in variants}
        chosen=portfolio_from_variants(current_tickets,scores)
        hs=[len(set(t)&actual) for _,t,_ in chosen]; port.append((target,max(hs) if hs else 0))
        for v in variants:
            decay=float(v.split('_d')[1])
            for m in MODELS:
                mh=len(set(preds[m])&actual)
                perf[v][m]=decay*perf[v][m]+(mh-0.8)
        d=draws[idx]
        for x in d['nums']:freq[x-1]+=1;last[x-1]=d['round']
        pc.update(itertools.combinations(d['nums'],2));tc.update(itertools.combinations(d['nums'],3));pr=b.structure_profile(d['nums'],draws[idx-1]['nums'])
        for i,x in enumerate(pr):profiles[i][x]+=1

    base=exact(); alpha=0.05/(len(variants)*2)
    stats={}
    validated=[]
    for j,v in enumerate(variants):
        hs=[h for t,h in rec[v] if t>=401]; ge2=[int(h>=2) for h in hs]; ge3=[int(h>=3) for h in hs]
        ci_m=blocks_ci(hs,base['mean'],alpha,SEED+j*17); ci_2=blocks_ci(ge2,base['ge2'],alpha,SEED+j*17+1); sh,_=block_share(hs,base['mean'])
        ok=ci_m[0]>0 and ci_2[0]>0 and sh>=0.65
        stats[v]={'n':len(hs),'mean_hits':statistics.mean(hs),'ge2':statistics.mean(ge2),'ge3':statistics.mean(ge3),'delta_mean':statistics.mean(hs)-base['mean'],'delta_ge2':statistics.mean(ge2)-base['ge2'],'adjusted_ci_mean':ci_m,'adjusted_ci_ge2':ci_2,'positive_block_share':sh,'pass':ok}
        if ok:validated.append(v)
    # portfolio baseline estimated exactly by deterministic matched random simulation over same target count.
    ph=[h for t,h in port if t>=401]
    rng=random.Random(SEED+999); rb=[]
    for _ in range(len(ph)*200):
        actual=set(rng.sample(range(1,46),6)); mx=max(len(set(rng.sample(range(1,46),6))&actual) for __ in range(5)); rb.append(mx)
    pbase=statistics.mean(rb); pci=blocks_ci(ph,pbase,0.01,SEED+777); pshare,_=block_share(ph,pbase)
    ppass=pci[0]>0 and pshare>=0.65
    ranking=sorted(variants,key=lambda v:(stats[v]['mean_hits'],stats[v]['ge2'],stats[v]['ge3']),reverse=True)
    best=validated[0] if validated else ranking[0]
    # current five lines: ensemble variants first, then strongest experts if duplicates reduce count.
    vscores={v:stats[v]['mean_hits'] for v in variants}; chosen=portfolio_from_variants(current_tickets,vscores)
    used={t for _,t,_ in chosen}
    exp_rank=sorted(MODELS,key=lambda m:statistics.mean(h for t,h in model_hits[m][-200:]),reverse=True)
    for m in exp_rank:
        t=tuple(current_preds[m])
        if t not in used and len(chosen)<5:
            chosen.append((m,t,statistics.mean(h for _,h in model_hits[m][-200:])));used.add(t)
    payload={'created_kst':datetime.now(KST).isoformat(),'target_round':1247,'data_cutoff':1246,'policy':'ONLINE_EXPERT_ENSEMBLE_V2','no_future_leakage':True,'baseline':base,'variants':stats,'validated_variants':validated,'ranking':ranking,'portfolio_validation':{'n':len(ph),'mean_max_hits':statistics.mean(ph),'random_matched_mean_max_hits':pbase,'adjusted_ci_delta':pci,'positive_block_share':pshare,'pass':ppass},'current_best_variant':best,'current_variant_ticket':list(current_tickets[best]),'current_variant_weights':current_weights[best],'current_five_candidates':{'sources':[x[0] for x in chosen[:5]],'tickets':[list(x[1]) for x in chosen[:5]]},'final_status':'MODEL_VALIDATED' if (validated and ppass) else 'NO_VALIDATED_FINAL'}
    OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':'PASS','validated_variants':validated,'best':best,'best_stats':stats[best],'portfolio':payload['portfolio_validation'],'final_status':payload['final_status'],'tickets':payload['current_five_candidates']['tickets']},ensure_ascii=False))
if __name__=='__main__':main()
