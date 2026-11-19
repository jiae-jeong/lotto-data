#!/usr/bin/env python3
from __future__ import annotations
import csv, importlib.util, itertools, json, math, random, statistics
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'lotto_data.csv'
B_SOURCE=ROOT/'research/1245_final_pipeline_v3/recovered_original_assets/b_model_backtest.py'
AC_SOURCE=ROOT/'automation/recovered_models_v2.py'
OUT=ROOT/'analysis/2026-10-23/TODAY_CAPPED_ENSEMBLE_1247_V3.json'
KST=timezone(timedelta(hours=9))
B_NAMES=('long_frequency','current_gap','frequency_plus_gap','recent_momentum','structure_profile','pair_association','triple_association','combined_equal_rank')
AC_NAMES=('A_v2','C_v2','contrarian_v2')
MODELS=B_NAMES+AC_NAMES
VARIANTS=((0.30,0.99,0.25),(0.45,0.99,0.25),(0.60,0.99,0.25),(0.30,0.99,0.35),(0.45,0.99,0.35),(0.60,0.99,0.35),(0.45,0.97,0.35),(0.60,0.97,0.35),(0.60,0.99,0.45))
BLOCK=50; BOOT=6000; SEED=202610231300

def imp(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def load_draws():
    out=[]
    with DATA.open(encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):out.append({'round':int(r['round']),'date':r['date'],'nums':tuple(sorted(int(r[f'no{i}']) for i in range(1,7)))})
    assert out[-1]['round']==1246 and [x['round'] for x in out]==list(range(1,1247));return out

def baseline():
    den=math.comb(45,6);p=[math.comb(6,k)*math.comb(39,6-k)/den for k in range(7)]
    return {'mean':sum(k*p[k] for k in range(7)),'ge2':sum(p[2:]),'ge3':sum(p[3:])}

def capped_weights(perf,eta,cap):
    mx=max(perf.values()); raw={m:math.exp(eta*(v-mx)) for m,v in perf.items()}; z=sum(raw.values()); w={m:raw[m]/z for m in raw}
    # iterative cap and redistribute until stable
    free=set(w); fixed={}; remaining=1.0
    while True:
        over=[m for m in free if w[m]*remaining/sum(w[x] for x in free)>cap]
        if not over:break
        for m in over:fixed[m]=cap;free.remove(m);remaining-=cap
        if not free:break
    if free:
        zf=sum(w[m] for m in free)
        for m in free:fixed[m]=remaining*w[m]/zf
    return fixed

def ticket(preds,perf,eta,cap):
    w=capped_weights(perf,eta,cap)
    score={n:sum(w[m] for m in MODELS if n in preds[m]) for n in range(1,46)}
    pool=sorted(range(1,46),key=lambda n:(-score[n],n))[:14];best=None
    for t in itertools.combinations(pool,6):
        odd=sum(n%2 for n in t);low=sum(n<=22 for n in t);cons=sum(b-a==1 for a,b in zip(t,t[1:]));bands=len({(n-1)//10 for n in t})
        val=sum(score[n] for n in t)-.035*abs(odd-3)-.03*abs(low-3)-.02*max(0,cons-2)+.006*bands
        if best is None or val>best[0] or (val==best[0] and t<best[1]):best=(val,t)
    return tuple(sorted(best[1])),w

def ci(vals,base,alpha,seed):
    blocks=[vals[i:i+BLOCK] for i in range(0,len(vals),BLOCK)];rng=random.Random(seed);reps=[]
    for _ in range(BOOT):
        bb=[blocks[rng.randrange(len(blocks))] for __ in range(len(blocks))];flat=[x for b in bb for x in b];reps.append(statistics.mean(flat)-base)
    reps.sort();return [reps[int(alpha/2*(len(reps)-1))],reps[int((1-alpha/2)*(len(reps)-1))]]
def share(vals,base):
    b=[statistics.mean(vals[i:i+BLOCK])-base for i in range(0,len(vals),BLOCK)];return sum(x>0 for x in b)/len(b),b

def main():
    draws=load_draws();b=imp(B_SOURCE,'b_v3');ac=imp(AC_SOURCE,'ac_v3');bank=b.feature_structure_bank(b.make_structure_bank())
    freq=[0]*45;last=[0]*45;pc=Counter();tc=Counter();profiles=[Counter() for _ in range(6)]
    for d in draws[:200]:
        for x in d['nums']:freq[x-1]+=1;last[x-1]=d['round']
        pc.update(itertools.combinations(d['nums'],2));tc.update(itertools.combinations(d['nums'],3));pr=b.structure_profile(d['nums'],None)
        for i,v in enumerate(pr[:5]):profiles[i][v]+=1
    for i in range(1,200):profiles[5][b.structure_profile(draws[i]['nums'],draws[i-1]['nums'])[5]]+=1
    names=[f'e{e}_d{d}_c{c}' for e,d,c in VARIANTS]; perf={n:{m:0.0 for m in MODELS} for n in names}; rec={n:[] for n in names}; cur={};curw={}; expert_rec={m:[] for m in MODELS}; current_preds={}
    for idx in range(200,len(draws)+1):
        hist=[x['nums'] for x in draws[:idx]];preds={**b.predictions_for_round(draws,idx,freq,last,pc,tc,profiles,bank),**ac.predict(hist)};current_preds=preds
        for name,(eta,decay,cap) in zip(names,VARIANTS):cur[name],curw[name]=ticket(preds,perf[name],eta,cap)
        if idx==len(draws):break
        actual=set(draws[idx]['nums']);target=idx+1
        for name in names:rec[name].append((target,len(set(cur[name])&actual)))
        for m in MODELS:expert_rec[m].append((target,len(set(preds[m])&actual)))
        for name,(eta,decay,cap) in zip(names,VARIANTS):
            for m in MODELS:perf[name][m]=decay*perf[name][m]+(len(set(preds[m])&actual)-0.8)
        d=draws[idx]
        for x in d['nums']:freq[x-1]+=1;last[x-1]=d['round']
        pc.update(itertools.combinations(d['nums'],2));tc.update(itertools.combinations(d['nums'],3));pr=b.structure_profile(d['nums'],draws[idx-1]['nums'])
        for i,v in enumerate(pr):profiles[i][v]+=1
    base=baseline();alpha=.05/(len(names)*2);stats={};valid=[]
    for j,n in enumerate(names):
        hs=[h for t,h in rec[n] if t>=401];g2=[int(h>=2) for h in hs];g3=[int(h>=3) for h in hs];cm=ci(hs,base['mean'],alpha,SEED+j*11);c2=ci(g2,base['ge2'],alpha,SEED+j*11+1);sh,_=share(hs,base['mean']);ok=cm[0]>0 and c2[0]>0 and sh>=.65
        stats[n]={'n':len(hs),'mean_hits':statistics.mean(hs),'ge2':statistics.mean(g2),'ge3':statistics.mean(g3),'delta_mean':statistics.mean(hs)-base['mean'],'delta_ge2':statistics.mean(g2)-base['ge2'],'adjusted_ci_mean':cm,'adjusted_ci_ge2':c2,'positive_block_share':sh,'pass':ok}
        if ok:valid.append(n)
    ranking=sorted(names,key=lambda n:(stats[n]['mean_hits'],stats[n]['ge2'],stats[n]['ge3'],stats[n]['positive_block_share']),reverse=True);best=valid[0] if valid else ranking[0]
    # Build today's five candidates from best capped ensemble + distinct experts ranked on trailing 200 rounds, with overlap penalty.
    candidates=[(best,cur[best],stats[best]['mean_hits'])]
    for m in MODELS:
        trail=[h for _,h in expert_rec[m][-200:]];candidates.append((m,tuple(current_preds[m]),statistics.mean(trail)))
    chosen=[];used=set()
    while candidates and len(chosen)<5:
        pick=None
        for x in candidates:
            if x[1] in used:continue
            ov=sum(len(set(x[1])&set(y[1])) for y in chosen);obj=x[2]-.12*ov
            if pick is None or obj>pick[0]:pick=(obj,x)
        if pick is None:break
        chosen.append(pick[1]);used.add(pick[1]);candidates=[x for x in candidates if x[0]!=pick[1][0]]
    payload={'created_kst':datetime.now(KST).isoformat(),'target_round':1247,'data_cutoff':1246,'policy':'CAPPED_ONLINE_ENSEMBLE_V3','no_future_leakage':True,'baseline':base,'variants':stats,'validated_variants':valid,'ranking':ranking,'current_best_variant':best,'current_best_ticket':list(cur[best]),'current_best_weights':curw[best],'current_five_candidates':{'sources':[x[0] for x in chosen],'tickets':[list(x[1]) for x in chosen]},'final_status':'MODEL_VALIDATED' if valid else 'NO_VALIDATED_FINAL'}
    OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({'status':'PASS','validated':valid,'best':best,'stats':stats[best],'weights':curw[best],'final_status':payload['final_status'],'tickets':payload['current_five_candidates']['tickets']},ensure_ascii=False))
if __name__=='__main__':main()
