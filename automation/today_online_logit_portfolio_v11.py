#!/usr/bin/env python3
from __future__ import annotations
import csv,importlib.util,itertools,json,math,random,statistics
from collections import Counter
from datetime import datetime,timezone,timedelta
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'lotto_data.csv'
B_SOURCE=ROOT/'research/1245_final_pipeline_v3/recovered_original_assets/b_model_backtest.py'
AC_SOURCE=ROOT/'automation/recovered_models_v2.py'
OUT=ROOT/'analysis/2026-10-23/TODAY_ONLINE_LOGIT_PORTFOLIO_1247_V11.json'
KST=timezone(timedelta(hours=9))
B_NAMES=('long_frequency','current_gap','frequency_plus_gap','recent_momentum','structure_profile','pair_association','triple_association','combined_equal_rank')
AC_NAMES=('A_v2','C_v2','contrarian_v2')
MODELS=B_NAMES+AC_NAMES
LR0=.035;L2=.0015;OVERLAP_PEN=.055;POOL=14
RANDOM_PER_TARGET=160;BLOCK=50;BOOT=5000;SEED=202610232100

def imp(path,name):s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def load_draws():
 out=[]
 with DATA.open(encoding='utf-8-sig') as f:
  for r in csv.DictReader(f):out.append({'round':int(r['round']),'date':r['date'],'nums':tuple(sorted(int(r[f'no{i}']) for i in range(1,7)))})
 assert out[-1]['round']==1246 and [x['round'] for x in out]==list(range(1,1247));return out
def sigmoid(z):
 if z>=0:
  e=math.exp(-z);return 1/(1+e)
 e=math.exp(z);return e/(1+e)
def feats(n,preds):return [1.0]+[1.0 if n in preds[m] else 0.0 for m in MODELS]
def scores(preds,w):return {n:sum(a*b for a,b in zip(w,feats(n,preds))) for n in range(1,46)}
def update(w,preds,actual,step):
 lr=LR0/math.sqrt(1+step/250.0)
 # one online pass through all 45 labels; class weighting keeps 6 positives visible.
 grad=[0.0]*len(w)
 for n in range(1,46):
  x=feats(n,preds);y=1.0 if n in actual else 0.0;p=sigmoid(sum(a*b for a,b in zip(w,x)))
  cw=3.25 if y else 1.0
  for j in range(len(w)):grad[j]+=cw*(p-y)*x[j]
 for j in range(len(w)):
  reg=0.0 if j==0 else L2*w[j]
  w[j]-=lr*(grad[j]/45.0+reg)
 return w
def build_portfolio(sc):
 pool=sorted(range(1,46),key=lambda n:(-sc[n],n))[:POOL];cands=[]
 for t in itertools.combinations(pool,6):
  odd=sum(n%2 for n in t);low=sum(n<=22 for n in t);bands=len({(n-1)//10 for n in t});cons=sum(b-a==1 for a,b in zip(t,t[1:]))
  val=sum(sc[n] for n in t)-.010*abs(odd-3)-.008*abs(low-3)-.006*max(0,cons-2)+.002*bands
  cands.append((val,tuple(sorted(t))))
 cands.sort(key=lambda x:(-x[0],x[1]));chosen=[];used=set()
 while len(chosen)<5:
  best=None
  for base,t in cands:
   if t in used:continue
   ov=sum(max(0,len(set(t)&set(q))-2) for q in chosen)
   maxov=max([len(set(t)&set(q)) for q in chosen] or [0])
   obj=base-OVERLAP_PEN*ov-.018*max(0,maxov-4)
   key=(obj,base,tuple(-n for n in t))
   if best is None or key>best[0]:best=(key,t)
  if best is None:raise RuntimeError('portfolio build failed')
  chosen.append(best[1]);used.add(best[1])
 return chosen
def metrics(lines,actual):
 ss=[set(x) for x in lines];hits=[len(x&actual) for x in ss];u=set().union(*ss);ovs=[len(ss[i]&ss[j]) for i in range(5) for j in range(i+1,5)]
 return {'max_hits':max(hits),'any2':int(max(hits)>=2),'any3':int(max(hits)>=3),'any4':int(max(hits)>=4),'any5':int(max(hits)>=5),'any6':int(max(hits)>=6),'winning_union_coverage':len(u&actual),'union_size':len(u),'mean_overlap':statistics.mean(ovs),'max_overlap':max(ovs)}
def permuted(lines,rng):
 labs=list(range(1,46));sh=labs[:];rng.shuffle(sh);mp=dict(zip(labs,sh));return [tuple(sorted(mp[n] for n in row)) for row in lines]
def avg(rows,k):return statistics.mean(float(r[k]) for r in rows)
def ci(vals,alpha,seed):
 blocks=[vals[i:i+BLOCK] for i in range(0,len(vals),BLOCK)];rng=random.Random(seed);reps=[]
 for _ in range(BOOT):
  flat=[]
  for __ in range(len(blocks)):flat+=blocks[rng.randrange(len(blocks))]
  reps.append(statistics.mean(flat))
 reps.sort();return [reps[int(alpha/2*(len(reps)-1))],reps[int((1-alpha/2)*(len(reps)-1))]]
def posshare(vals):
 b=[statistics.mean(vals[i:i+BLOCK]) for i in range(0,len(vals),BLOCK)];return sum(x>0 for x in b)/len(b)
def main():
 draws=load_draws();b=imp(B_SOURCE,'bv11');ac=imp(AC_SOURCE,'acv11');bank=b.feature_structure_bank(b.make_structure_bank())
 freq=[0]*45;last=[0]*45;pc=Counter();tc=Counter();profiles=[Counter() for _ in range(6)]
 for d in draws[:200]:
  for x in d['nums']:freq[x-1]+=1;last[x-1]=d['round']
  pc.update(itertools.combinations(d['nums'],2));tc.update(itertools.combinations(d['nums'],3));pr=b.structure_profile(d['nums'],None)
  for i,v in enumerate(pr[:5]):profiles[i][v]+=1
 for i in range(1,200):profiles[5][b.structure_profile(draws[i]['nums'],draws[i-1]['nums'])[5]]+=1
 # intercept initialized at logit(6/45); model coefficients start neutral.
 p0=6/45;w=[math.log(p0/(1-p0))]+[0.0]*len(MODELS);obs=[];null=[];diffs={k:[] for k in ('max_hits','any2','any3','winning_union_coverage')};current=None;step=0
 for idx in range(200,len(draws)+1):
  hist=[x['nums'] for x in draws[:idx]];preds={**b.predictions_for_round(draws,idx,freq,last,pc,tc,profiles,bank),**ac.predict(hist)};sc=scores(preds,w);lines=build_portfolio(sc)
  if idx==len(draws):
   current={'weights':{'intercept':w[0],**{m:w[i+1] for i,m in enumerate(MODELS)}},'number_logits':{str(n):sc[n] for n in range(1,46)},'lines':[list(x) for x in lines]};break
  actual=set(draws[idx]['nums']);target=idx+1
  if target>=401:
   om=metrics(lines,actual);om['target']=target;obs.append(om);rng=random.Random(SEED+target);samples=[metrics(permuted(lines,rng),actual) for _ in range(RANDOM_PER_TARGET)];nm={k:statistics.mean(float(x[k]) for x in samples) for k in samples[0]};nm['target']=target;null.append(nm)
   for k in diffs:diffs[k].append(float(om[k])-nm[k])
  w=update(w,preds,actual,step);step+=1
  d=draws[idx]
  for x in d['nums']:freq[x-1]+=1;last[x-1]=d['round']
  pc.update(itertools.combinations(d['nums'],2));tc.update(itertools.combinations(d['nums'],3));pr=b.structure_profile(d['nums'],draws[idx-1]['nums'])
  for i,v in enumerate(pr):profiles[i][v]+=1
 keys=['max_hits','any2','any3','any4','any5','any6','winning_union_coverage','union_size','mean_overlap','max_overlap'];score={'policy':{k:avg(obs,k) for k in keys},'matched_label_permutation':{k:avg(null,k) for k in keys}};score['delta']={k:score['policy'][k]-score['matched_label_permutation'][k] for k in keys};alpha=.05/4;inf={}
 for j,k in enumerate(diffs):inf[k]={'adjusted_ci_delta':ci(diffs[k],alpha,SEED+6000+j),'positive_50_round_block_share':posshare(diffs[k])}
 inf['strict_portfolio_pass']=(inf['max_hits']['adjusted_ci_delta'][0]>0 and inf['any2']['adjusted_ci_delta'][0]>0 and inf['any3']['adjusted_ci_delta'][0]>0 and inf['any2']['positive_50_round_block_share']>=.65)
 payload={'created_kst':datetime.now(KST).isoformat(),'target_round':1247,'data_cutoff':1246,'policy':'ONLINE_NUMBER_LEVEL_LOGIT_META_V11','no_future_leakage':True,'hyperparameters':{'lr0':LR0,'l2':L2,'pool':POOL,'overlap_penalty':OVERLAP_PEN},'note':'Each historical target is scored before its outcome is used. The online logistic learner only sees earlier model-vote patterns and outcomes. Strict gate/comparator unchanged.','current':current,'walkforward_targets':len(obs),'scorecard':score,'inference':inf,'final_status':'STRICT_PASS' if inf['strict_portfolio_pass'] else 'FAIL_SAME_GATE'};OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':'PASS','strict_pass':inf['strict_portfolio_pass'],'scorecard':score,'inference':inf,'current':current},ensure_ascii=False))
if __name__=='__main__':main()
