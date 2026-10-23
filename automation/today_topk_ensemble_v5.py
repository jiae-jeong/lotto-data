#!/usr/bin/env python3
from __future__ import annotations
import csv,importlib.util,itertools,json,math,random,statistics
from collections import Counter,deque
from datetime import datetime,timezone,timedelta
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'lotto_data.csv';B_SOURCE=ROOT/'research/1245_final_pipeline_v3/recovered_original_assets/b_model_backtest.py';AC_SOURCE=ROOT/'automation/recovered_models_v2.py';OUT=ROOT/'analysis/2026-10-23/TODAY_TOPK_ENSEMBLE_1247_V5.json'
KST=timezone(timedelta(hours=9));B_NAMES=('long_frequency','current_gap','frequency_plus_gap','recent_momentum','structure_profile','pair_association','triple_association','combined_equal_rank');AC_NAMES=('A_v2','C_v2','contrarian_v2');MODELS=B_NAMES+AC_NAMES
VARIANTS=[(w,k) for w in (50,100,200) for k in (3,5,7)];BLOCK=50;BOOT=6000;SEED=202610231340

def imp(p,n):s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def load():
 o=[]
 with DATA.open(encoding='utf-8-sig') as f:
  for r in csv.DictReader(f):o.append({'round':int(r['round']),'date':r['date'],'nums':tuple(sorted(int(r[f'no{i}']) for i in range(1,7)))})
 assert o[-1]['round']==1246;return o
def base():
 d=math.comb(45,6);p=[math.comb(6,k)*math.comb(39,6-k)/d for k in range(7)];return {'mean':.8,'ge2':sum(p[2:]),'ge3':sum(p[3:])}
def choose_ticket(preds,hist,w,k):
 ranked=[];b=base()
 for m in MODELS:
  hs=list(hist[m])[-w:]; n=len(hs)
  mean=(sum(hs)+50*b['mean'])/(n+50);g2=(sum(x>=2 for x in hs)+50*b['ge2'])/(n+50);r20=statistics.mean(hs[-20:]) if hs else .8
  ranked.append((mean+.35*(g2-b['ge2'])+.08*(r20-.8),m,mean,g2,r20))
 ranked.sort(reverse=True);sel=ranked[:k]
 # moderate performance weighting only inside the preselected expert pool
 raw={m:math.exp(4*(score-ranked[k-1][0])) for score,m,*_ in sel};z=sum(raw.values());ww={m:v/z for m,v in raw.items()}
 ns={n:sum(ww[m] for m in ww if n in preds[m]) for n in range(1,46)};pool=sorted(range(1,46),key=lambda n:(-ns[n],n))[:14];best=None
 for t in itertools.combinations(pool,6):
  odd=sum(n%2 for n in t);low=sum(n<=22 for n in t);bands=len({(n-1)//10 for n in t});val=sum(ns[n] for n in t)-.035*abs(odd-3)-.03*abs(low-3)+.006*bands
  if best is None or val>best[0] or (val==best[0] and t<best[1]):best=(val,t)
 return tuple(sorted(best[1])),[x[1] for x in sel],ww
def ci(vals,b,alpha,seed):
 blocks=[vals[i:i+BLOCK] for i in range(0,len(vals),BLOCK)];rng=random.Random(seed);r=[]
 for _ in range(BOOT):
  bb=[blocks[rng.randrange(len(blocks))] for __ in range(len(blocks))];flat=[x for q in bb for x in q];r.append(statistics.mean(flat)-b)
 r.sort();return [r[int(alpha/2*(len(r)-1))],r[int((1-alpha/2)*(len(r)-1))]]
def share(vals,b):
 q=[statistics.mean(vals[i:i+BLOCK])-b for i in range(0,len(vals),BLOCK)];return sum(x>0 for x in q)/len(q)
def main():
 draws=load();bmod=imp(B_SOURCE,'bv5');ac=imp(AC_SOURCE,'acv5');bank=bmod.feature_structure_bank(bmod.make_structure_bank());freq=[0]*45;last=[0]*45;pc=Counter();tc=Counter();prof=[Counter() for _ in range(6)]
 for d in draws[:200]:
  for x in d['nums']:freq[x-1]+=1;last[x-1]=d['round']
  pc.update(itertools.combinations(d['nums'],2));tc.update(itertools.combinations(d['nums'],3));p=bmod.structure_profile(d['nums'],None)
  for i,v in enumerate(p[:5]):prof[i][v]+=1
 for i in range(1,200):prof[5][bmod.structure_profile(draws[i]['nums'],draws[i-1]['nums'])[5]]+=1
 hist={m:deque(maxlen=200) for m in MODELS};names=[f'w{w}_k{k}' for w,k in VARIANTS];rec={n:[] for n in names};cur={};selnow={};wnow={}
 for idx in range(200,len(draws)+1):
  preds={**bmod.predictions_for_round(draws,idx,freq,last,pc,tc,prof,bank),**ac.predict([x['nums'] for x in draws[:idx]])}
  for name,(w,k) in zip(names,VARIANTS):cur[name],selnow[name],wnow[name]=choose_ticket(preds,hist,w,k)
  if idx==len(draws):break
  actual=set(draws[idx]['nums']);target=idx+1
  for n in names:rec[n].append((target,len(set(cur[n])&actual)))
  for m in MODELS:hist[m].append(len(set(preds[m])&actual))
  d=draws[idx]
  for x in d['nums']:freq[x-1]+=1;last[x-1]=d['round']
  pc.update(itertools.combinations(d['nums'],2));tc.update(itertools.combinations(d['nums'],3));p=bmod.structure_profile(d['nums'],draws[idx-1]['nums'])
  for i,v in enumerate(p):prof[i][v]+=1
 bas=base();alpha=.05/(len(names)*2);stats={};valid=[]
 for j,n in enumerate(names):
  hs=[h for t,h in rec[n] if t>=401];g2=[int(h>=2) for h in hs];g3=[int(h>=3) for h in hs];cm=ci(hs,bas['mean'],alpha,SEED+j*9);c2=ci(g2,bas['ge2'],alpha,SEED+j*9+1);sh=share(hs,bas['mean']);ok=cm[0]>0 and c2[0]>0 and sh>=.65
  stats[n]={'n':len(hs),'mean_hits':statistics.mean(hs),'ge2':statistics.mean(g2),'ge3':statistics.mean(g3),'delta_mean':statistics.mean(hs)-bas['mean'],'delta_ge2':statistics.mean(g2)-bas['ge2'],'adjusted_ci_mean':cm,'adjusted_ci_ge2':c2,'positive_block_share':sh,'pass':ok}
  if ok:valid.append(n)
 rank=sorted(names,key=lambda n:(stats[n]['mean_hits'],stats[n]['ge2'],stats[n]['positive_block_share']),reverse=True);best=valid[0] if valid else rank[0]
 payload={'created_kst':datetime.now(KST).isoformat(),'target_round':1247,'data_cutoff':1246,'policy':'TOPK_ONLINE_ENSEMBLE_V5','no_future_leakage':True,'baseline':bas,'variants':stats,'validated_variants':valid,'ranking':rank,'current_best_variant':best,'current_best_ticket':list(cur[best]),'current_selected_models':selnow[best],'current_weights':wnow[best],'final_status':'MODEL_VALIDATED' if valid else 'NO_VALIDATED_FINAL'}
 OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':'PASS','validated':valid,'best':best,'stats':stats[best],'ticket':list(cur[best]),'selected_models':selnow[best],'weights':wnow[best],'final_status':payload['final_status']},ensure_ascii=False))
if __name__=='__main__':main()
