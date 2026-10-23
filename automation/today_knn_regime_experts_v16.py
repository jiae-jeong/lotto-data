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
OUT=ROOT/'analysis/2026-10-23/TODAY_KNN_REGIME_EXPERTS_1247_V16.json'
KST=timezone(timedelta(hours=9))
B=('long_frequency','current_gap','frequency_plus_gap','recent_momentum','structure_profile','pair_association','triple_association','combined_equal_rank')
AC=('A_v2','C_v2','contrarian_v2')
MODELS=B+AC
BASE_MEAN=.8;BASE_GE2=.17530810086113546;BASE_GE3=.023834078609221467
K=120;PRIOR_N=60;OVERLAP=.035
TEST_NULL=160;BLOCK=50;BOOT=5000;SEED=202610240700

def imp(path,name):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def load_draws():
 out=[]
 with DATA.open(encoding='utf-8-sig') as f:
  for r in csv.DictReader(f):out.append({'round':int(r['round']),'date':r['date'],'nums':tuple(sorted(int(r[f'no{i}']) for i in range(1,7)))})
 assert out[-1]['round']==1246 and [x['round'] for x in out]==list(range(1,1247));return out

def context(draws,idx,freq,last,preds):
 sets=[set(preds[m]) for m in MODELS]
 overlaps=[len(sets[i]&sets[j])/6 for i in range(len(sets)) for j in range(i+1,len(sets))]
 votes=[sum(n in s for s in sets) for n in range(1,46)]
 union=len(set().union(*sets))/45
 fr=[float(x) for x in freq];round_now=draws[idx-1]['round'];gp=[float(round_now-last[i]) for i in range(45)]
 fcv=statistics.pstdev(fr)/(statistics.mean(fr)+1e-9);gcv=statistics.pstdev(gp)/(statistics.mean(gp)+1e-9)
 prev=draws[idx-1]['nums'];odd=sum(n%2 for n in prev)/6;low=sum(n<=22 for n in prev)/6;cons=sum(b-a==1 for a,b in zip(prev,prev[1:]))/5
 recent=draws[max(0,idx-20):idx];rc=[0]*45
 for d in recent:
  for n in d['nums']:rc[n-1]+=1
 rcv=statistics.pstdev(rc)/(statistics.mean(rc)+1e-9)
 return [statistics.mean(overlaps),max(votes)/11,union,min(fcv,2.0),min(gcv,3.0),odd,low,cons,min(rcv,2.0)]

def neighbor_scores(x,records):
 if not records:return {m:0.0 for m in MODELS},[]
 dims=len(x);means=[statistics.mean(r['x'][j] for r in records) for j in range(dims)];sds=[statistics.pstdev(r['x'][j] for r in records) for j in range(dims)]
 def dist(r):
  return math.sqrt(sum(((x[j]-r['x'][j])/(sds[j]+1e-6))**2 for j in range(dims)))
 nearest=sorted(records,key=dist)[:min(K,len(records))]
 # inverse-distance weighting; shrink every local estimate to exact random single-ticket baselines
 ws=[1/(.35+dist(r)) for r in nearest];sw=sum(ws)
 out={}
 for m in MODELS:
  mean=(sum(w*r['hits'][m] for w,r in zip(ws,nearest))+PRIOR_N*BASE_MEAN)/(sw+PRIOR_N)
  ge2=(sum(w*(r['hits'][m]>=2) for w,r in zip(ws,nearest))+PRIOR_N*BASE_GE2)/(sw+PRIOR_N)
  ge3=(sum(w*(r['hits'][m]>=3) for w,r in zip(ws,nearest))+PRIOR_N*BASE_GE3)/(sw+PRIOR_N)
  out[m]=(mean-BASE_MEAN)+.75*(ge2-BASE_GE2)+1.25*(ge3-BASE_GE3)
 return out,[{'round':r['round'],'distance':dist(r)} for r in nearest[:12]]

def select(preds,mscore):
 chosen=[];used=set();detail=[]
 while len(chosen)<5:
  best=None
  for m in MODELS:
   if any(m==q[0] for q in chosen):continue
   t=tuple(preds[m])
   if t in used:continue
   ovs=[len(set(t)&set(q[1])) for q in chosen]
   pen=OVERLAP*sum(max(0,o-2) for o in ovs)+.014*max(0,(max(ovs) if ovs else 0)-3)
   key=(mscore[m]-pen,mscore[m],-MODELS.index(m))
   if best is None or key>best[0]:best=(key,m,t,pen)
  if best is None:raise RuntimeError('not enough distinct expert tickets')
  _,m,t,pen=best;chosen.append((m,t));used.add(t);detail.append({'model':m,'local_score':mscore[m],'overlap_penalty':pen,'ticket':list(t)})
 return chosen,detail

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
 draws=load_draws();b=imp(B_SOURCE,'bv16');ac=imp(AC_SOURCE,'acv16');bank=b.feature_structure_bank(b.make_structure_bank());freq=[0]*45;last=[0]*45;pc=Counter();tc=Counter();profiles=[Counter() for _ in range(6)]
 for d in draws[:200]:
  for n in d['nums']:freq[n-1]+=1;last[n-1]=d['round']
  pc.update(itertools.combinations(d['nums'],2));tc.update(itertools.combinations(d['nums'],3));pr=b.structure_profile(d['nums'],None)
  for i,v in enumerate(pr[:5]):profiles[i][v]+=1
 for i in range(1,200):profiles[5][b.structure_profile(draws[i]['nums'],draws[i-1]['nums'])[5]]+=1
 records=[];obs=[];null=[];diffs={k:[] for k in ('max_hits','any2','any3','winning_union_coverage')};use=Counter();current=None
 for idx in range(200,len(draws)+1):
  hist=[q['nums'] for q in draws[:idx]];preds={**b.predictions_for_round(draws,idx,freq,last,pc,tc,profiles,bank),**ac.predict(hist)};x=context(draws,idx,freq,last,preds);mscore,neighbors=neighbor_scores(x,records);sel,detail=select(preds,mscore);lines=[q[1] for q in sel]
  if idx==len(draws):current={'models':[q[0] for q in sel],'lines':[list(q) for q in lines],'context':x,'model_local_scores':mscore,'nearest_prior_rounds':neighbors,'selection_details':detail};break
  actual=set(draws[idx]['nums']);target=idx+1
  if target>=401:
   for m,_ in sel:use[m]+=1
   om=metrics(lines,actual);om['target']=target;obs.append(om);rng=random.Random(SEED+target);samples=[metrics(permuted(lines,rng),actual) for _ in range(TEST_NULL)];nm={k:statistics.mean(float(q[k]) for q in samples) for k in samples[0]};nm['target']=target;null.append(nm)
   for k in diffs:diffs[k].append(float(om[k])-nm[k])
  # add current regime only after outcome resolves
  records.append({'round':target,'x':x,'hits':{m:len(set(preds[m])&actual) for m in MODELS}})
  d=draws[idx]
  for n in d['nums']:freq[n-1]+=1;last[n-1]=d['round']
  pc.update(itertools.combinations(d['nums'],2));tc.update(itertools.combinations(d['nums'],3));pr=b.structure_profile(d['nums'],draws[idx-1]['nums'])
  for i,v in enumerate(pr):profiles[i][v]+=1
 keys=['max_hits','any2','any3','any4','any5','any6','winning_union_coverage','union_size','mean_overlap','max_overlap'];score={'policy':{k:avg(obs,k) for k in keys},'matched_label_permutation':{k:avg(null,k) for k in keys}};score['delta']={k:score['policy'][k]-score['matched_label_permutation'][k] for k in keys};alpha=.05/4;inf={}
 for j,k in enumerate(diffs):inf[k]={'adjusted_ci_delta':ci(diffs[k],alpha,SEED+1000+j),'positive_50_round_block_share':posshare(diffs[k])}
 inf['strict_portfolio_pass']=(inf['max_hits']['adjusted_ci_delta'][0]>0 and inf['any2']['adjusted_ci_delta'][0]>0 and inf['any3']['adjusted_ci_delta'][0]>0 and inf['any2']['positive_50_round_block_share']>=.65)
 payload={'created_kst':datetime.now(KST).isoformat(),'target_round':1247,'data_cutoff':1246,'policy':'NONPARAMETRIC_KNN_REGIME_EXPERT_SELECTION_V16','no_future_leakage':True,'hyperparameters':{'k_neighbors':K,'prior_n':PRIOR_N,'overlap_penalty':OVERLAP},'context_features':['mean_model_overlap','max_vote_share','model_union_share','freq_cv','gap_cv','prev_odd_share','prev_low_share','prev_consecutive_share','recent20_freq_cv'],'note':'At t, model reliability is estimated only from earlier targets with similar pre-outcome contexts. Strict outer gate and matched joint label-permutation comparator unchanged.','model_use_counts':dict(use),'current':current,'walkforward_targets':len(obs),'scorecard':score,'inference':inf,'final_status':'STRICT_PASS' if inf['strict_portfolio_pass'] else 'FAIL_SAME_GATE'};OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':'PASS','strict_pass':inf['strict_portfolio_pass'],'scorecard':score,'inference':inf,'current':current,'model_use_counts':dict(use)},ensure_ascii=False))
if __name__=='__main__':main()
