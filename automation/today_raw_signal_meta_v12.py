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
OUT=ROOT/'analysis/2026-10-23/TODAY_RAW_SIGNAL_META_1247_V12.json'
KST=timezone(timedelta(hours=9))
B_NAMES=('long_frequency','current_gap','frequency_plus_gap','recent_momentum','structure_profile','pair_association','triple_association','combined_equal_rank')
AC_NAMES=('A_v2','C_v2','contrarian_v2')
MODELS=B_NAMES+AC_NAMES
LR0=.018;L2=.002;POOL=13;OVERLAP=.045
RANDOM_PER_TARGET=160;BLOCK=50;BOOT=5000;SEED=202610232300

def imp(path,name):s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def load_draws():
 out=[]
 with DATA.open(encoding='utf-8-sig') as f:
  for r in csv.DictReader(f):out.append({'round':int(r['round']),'date':r['date'],'nums':tuple(sorted(int(r[f'no{i}']) for i in range(1,7)))})
 assert out[-1]['round']==1246 and [x['round'] for x in out]==list(range(1,1247));return out
def z(vals):
 mu=statistics.mean(vals);sd=statistics.pstdev(vals)
 return [0.0 if sd<1e-12 else (x-mu)/sd for x in vals]
def sigmoid(x):
 if x>=0:
  e=math.exp(-x);return 1/(1+e)
 e=math.exp(x);return e/(1+e)
def raw_features(draws,idx,freq,last,pc,tc,preds):
 current_round=draws[idx-1]['round'];prev=draws[idx-1]['nums'];prevset=set(prev)
 gaps=[current_round-last[i] if last[i] else current_round for i in range(45)]
 recent=draws[max(0,idx-50):idx];earlier=draws[max(0,idx-100):max(0,idx-50)]
 rc=[0]*45;ec=[0]*45
 for d in recent:
  for n in d['nums']:rc[n-1]+=1
 for d in earlier:
  for n in d['nums']:ec[n-1]+=1
 mom=[rc[i]/max(1,len(recent))-ec[i]/max(1,len(earlier)) for i in range(45)]
 pairprev=[];tripleprev=[]
 for n in range(1,46):
  pairprev.append(sum(pc[tuple(sorted((n,x)))] for x in prev if x!=n))
  tripleprev.append(sum(tc[tuple(sorted((n,a,b)))] for a,b in itertools.combinations(prev,2) if n not in (a,b)))
 fz,gz,rz,mz,pz,tz=map(z,([float(x) for x in freq],[float(x) for x in gaps],[float(x) for x in rc],mom,[float(x) for x in pairprev],[float(x) for x in tripleprev]))
 out={}
 for n in range(1,46):
  votes=[1.0 if n in preds[m] else 0.0 for m in MODELS]
  vote=sum(votes)/len(MODELS)
  prev_member=1.0 if n in prevset else 0.0
  adjacent=1.0 if any(abs(n-x)==1 for x in prev) else 0.0
  out[n]=[1.0]+votes+[vote,fz[n-1],gz[n-1],rz[n-1],mz[n-1],pz[n-1],tz[n-1],prev_member,adjacent,1.0 if n%2 else 0.0,1.0 if n<=22 else 0.0]
 return out
def score_all(X,w):return {n:sum(a*b for a,b in zip(w,X[n])) for n in X}
def update(w,X,actual,step):
 lr=LR0/math.sqrt(1+step/300);grad=[0.0]*len(w)
 for n,x in X.items():
  y=1.0 if n in actual else 0.0;p=sigmoid(sum(a*b for a,b in zip(w,x)));cw=3.0 if y else 1.0
  for j,v in enumerate(x):grad[j]+=cw*(p-y)*v
 for j in range(len(w)):
  reg=0 if j==0 else L2*w[j];w[j]-=lr*(grad[j]/45+reg)
 return w
def build(sc):
 pool=sorted(sc,key=lambda n:(-sc[n],n))[:POOL];c=[]
 for t in itertools.combinations(pool,6):
  odd=sum(n%2 for n in t);low=sum(n<=22 for n in t);bands=len({(n-1)//10 for n in t});cons=sum(b-a==1 for a,b in zip(t,t[1:]));base=sum(sc[n] for n in t)-.008*abs(odd-3)-.007*abs(low-3)-.006*max(0,cons-2)+.002*bands;c.append((base,tuple(sorted(t))))
 c.sort(key=lambda x:(-x[0],x[1]));chosen=[];used=set()
 while len(chosen)<5:
  best=None
  for base,t in c:
   if t in used:continue
   ovs=[len(set(t)&set(q)) for q in chosen];pen=OVERLAP*sum(max(0,o-2) for o in ovs)+.012*max(0,(max(ovs) if ovs else 0)-4);key=(base-pen,base,tuple(-x for x in t))
   if best is None or key>best[0]:best=(key,t)
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
 draws=load_draws();b=imp(B_SOURCE,'bv12');ac=imp(AC_SOURCE,'acv12');bank=b.feature_structure_bank(b.make_structure_bank());freq=[0]*45;last=[0]*45;pc=Counter();tc=Counter();profiles=[Counter() for _ in range(6)]
 for d in draws[:200]:
  for x in d['nums']:freq[x-1]+=1;last[x-1]=d['round']
  pc.update(itertools.combinations(d['nums'],2));tc.update(itertools.combinations(d['nums'],3));pr=b.structure_profile(d['nums'],None)
  for i,v in enumerate(pr[:5]):profiles[i][v]+=1
 for i in range(1,200):profiles[5][b.structure_profile(draws[i]['nums'],draws[i-1]['nums'])[5]]+=1
 nfeat=1+len(MODELS)+11;p0=6/45;w=[math.log(p0/(1-p0))]+[0.0]*(nfeat-1);obs=[];null=[];diffs={k:[] for k in ('max_hits','any2','any3','winning_union_coverage')};current=None;step=0
 for idx in range(200,len(draws)+1):
  hist=[x['nums'] for x in draws[:idx]];preds={**b.predictions_for_round(draws,idx,freq,last,pc,tc,profiles,bank),**ac.predict(hist)};X=raw_features(draws,idx,freq,last,pc,tc,preds);sc=score_all(X,w);lines=build(sc)
  if idx==len(draws):
   names=['intercept']+list(MODELS)+['vote_share','freq_z','gap_z','recent50_z','momentum_z','pair_prev_z','triple_prev_z','prev_member','adjacent_prev','odd','low22'];current={'weights':dict(zip(names,w)),'number_scores':{str(n):sc[n] for n in sc},'lines':[list(x) for x in lines]};break
  actual=set(draws[idx]['nums']);target=idx+1
  if target>=401:
   om=metrics(lines,actual);om['target']=target;obs.append(om);rng=random.Random(SEED+target);samples=[metrics(permuted(lines,rng),actual) for _ in range(RANDOM_PER_TARGET)];nm={k:statistics.mean(float(x[k]) for x in samples) for k in samples[0]};nm['target']=target;null.append(nm)
   for k in diffs:diffs[k].append(float(om[k])-nm[k])
  w=update(w,X,actual,step);step+=1;d=draws[idx]
  for x in d['nums']:freq[x-1]+=1;last[x-1]=d['round']
  pc.update(itertools.combinations(d['nums'],2));tc.update(itertools.combinations(d['nums'],3));pr=b.structure_profile(d['nums'],draws[idx-1]['nums'])
  for i,v in enumerate(pr):profiles[i][v]+=1
 keys=['max_hits','any2','any3','any4','any5','any6','winning_union_coverage','union_size','mean_overlap','max_overlap'];score={'policy':{k:avg(obs,k) for k in keys},'matched_label_permutation':{k:avg(null,k) for k in keys}};score['delta']={k:score['policy'][k]-score['matched_label_permutation'][k] for k in keys};alpha=.05/4;inf={}
 for j,k in enumerate(diffs):inf[k]={'adjusted_ci_delta':ci(diffs[k],alpha,SEED+5000+j),'positive_50_round_block_share':posshare(diffs[k])}
 inf['strict_portfolio_pass']=(inf['max_hits']['adjusted_ci_delta'][0]>0 and inf['any2']['adjusted_ci_delta'][0]>0 and inf['any3']['adjusted_ci_delta'][0]>0 and inf['any2']['positive_50_round_block_share']>=.65)
 payload={'created_kst':datetime.now(KST).isoformat(),'target_round':1247,'data_cutoff':1246,'policy':'ONLINE_RAW_SIGNAL_META_V12','no_future_leakage':True,'features':['11 model votes','vote_share','freq_z','gap_z','recent50_z','momentum_z','pair_prev_z','triple_prev_z','prev_member','adjacent_prev','odd','low22'],'hyperparameters':{'lr0':LR0,'l2':L2,'pool':POOL,'overlap':OVERLAP},'note':'All features at target t are computed only from rounds <t; the outcome is applied only after scoring. Strict validation gate and matched label-permutation comparator unchanged.','current':current,'walkforward_targets':len(obs),'scorecard':score,'inference':inf,'final_status':'STRICT_PASS' if inf['strict_portfolio_pass'] else 'FAIL_SAME_GATE'};OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':'PASS','strict_pass':inf['strict_portfolio_pass'],'scorecard':score,'inference':inf,'current':current},ensure_ascii=False))
if __name__=='__main__':main()
