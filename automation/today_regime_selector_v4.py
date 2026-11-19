#!/usr/bin/env python3
from __future__ import annotations
import csv,json,math,random,statistics
from collections import defaultdict
from datetime import datetime,timezone,timedelta
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
B=ROOT/'analysis/2026-10-23/MASTER_FULL_V4_232811_580357/B_PREDICTIONS_UNIQUE.csv'
AC=ROOT/'analysis/2026-10-23/MASTER_FULL_V5_233420_110068/AC_CONTRARIAN_WALKFORWARD.csv'
OUT=ROOT/'analysis/2026-10-23/TODAY_REGIME_SELECTOR_1247_V4.json'
KST=timezone(timedelta(hours=9));BLOCK=50;BOOT=8000;SEED=202610231320
MODELS=('long_frequency','current_gap','frequency_plus_gap','recent_momentum','structure_profile','pair_association','triple_association','combined_equal_rank','A_v2','C_v2','contrarian_v2')
RULES=[(w,k,s) for w in (20,50,100,200) for k in (0.0,0.4,0.8) for s in (25,75)]

def hist():
    h=defaultdict(dict)
    for p in (B,AC):
        with p.open(encoding='utf-8-sig') as f:
            for r in csv.DictReader(f):
                t=int(r['target_round']);assert int(r['training_through_round'])==t-1;h[r['model']][t]=int(r['hits'])
    assert set(h)==set(MODELS)
    return h

def base():
    den=math.comb(45,6);p=[math.comb(6,k)*math.comb(39,6-k)/den for k in range(7)];return {'mean':.8,'ge2':sum(p[2:]),'ge3':sum(p[3:])}

def choose(h,t,rule):
    w,k,sh=rule;lo=max(201,t-w);ts=list(range(lo,t));best=None
    for m in MODELS:
        hs=[h[m][x] for x in ts];mean=(sum(hs)+sh*.8)/(len(hs)+sh);ge2=(sum(x>=2 for x in hs)+sh*base()['ge2'])/(len(hs)+sh);recent10=statistics.mean(hs[-10:]) if len(hs)>=10 else statistics.mean(hs)
        score=mean+k*(ge2-base()['ge2'])+.05*(recent10-.8)
        item=(score,mean,ge2,recent10,m)
        if best is None or item>best:best=item
    return best[-1]

def ci(vals,b,alpha,seed):
    blocks=[vals[i:i+BLOCK] for i in range(0,len(vals),BLOCK)];rng=random.Random(seed);r=[]
    for _ in range(BOOT):
        samp=[blocks[rng.randrange(len(blocks))] for __ in range(len(blocks))];flat=[x for z in samp for x in z];r.append(statistics.mean(flat)-b)
    r.sort();return [r[int(alpha/2*(len(r)-1))],r[int((1-alpha/2)*(len(r)-1))]]
def share(vals,b):
    d=[statistics.mean(vals[i:i+BLOCK])-b for i in range(0,len(vals),BLOCK)];return sum(x>0 for x in d)/len(d)

def main():
    h=hist();b=base();stats={};alpha=.05/(len(RULES)*2);valid=[]
    for j,r in enumerate(RULES):
        hs=[];chosen=[]
        for t in range(401,1247):
            m=choose(h,t,r);chosen.append(m);hs.append(h[m][t])
        g2=[int(x>=2) for x in hs];g3=[int(x>=3) for x in hs];cm=ci(hs,b['mean'],alpha,SEED+j*7);c2=ci(g2,b['ge2'],alpha,SEED+j*7+1);sh=share(hs,b['mean']);ok=cm[0]>0 and c2[0]>0 and sh>=.65
        name=f'w{r[0]}_k{r[1]}_s{r[2]}';stats[name]={'rule':r,'n':len(hs),'mean_hits':statistics.mean(hs),'ge2':statistics.mean(g2),'ge3':statistics.mean(g3),'delta_mean':statistics.mean(hs)-b['mean'],'delta_ge2':statistics.mean(g2)-b['ge2'],'adjusted_ci_mean':cm,'adjusted_ci_ge2':c2,'positive_block_share':sh,'pass':ok,'choice_counts':{m:chosen.count(m) for m in MODELS}}
        if ok:valid.append(name)
    ranking=sorted(stats,key=lambda n:(stats[n]['mean_hits'],stats[n]['ge2'],stats[n]['positive_block_share']),reverse=True);best=valid[0] if valid else ranking[0];r=tuple(stats[best]['rule']);today=choose(h,1247,r)
    payload={'created_kst':datetime.now(KST).isoformat(),'target_round':1247,'data_cutoff':1246,'policy':'REGIME_SELECTOR_V4','no_future_leakage':True,'baseline':b,'rules':stats,'validated_rules':valid,'ranking':ranking,'best_rule':best,'today_selected_model':today,'final_status':'MODEL_VALIDATED' if valid else 'NO_VALIDATED_FINAL'}
    OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':'PASS','validated':valid,'best':best,'stats':stats[best],'today_model':today,'final_status':payload['final_status']},ensure_ascii=False))
if __name__=='__main__':main()
