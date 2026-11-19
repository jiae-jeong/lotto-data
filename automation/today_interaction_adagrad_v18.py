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
V12_SOURCE=ROOT/'automation/today_raw_signal_meta_v12.py'
OUT=ROOT/'analysis/2026-10-23/TODAY_INTERACTION_ADAGRAD_1247_V18.json'
KST=timezone(timedelta(hours=9))
B=('long_frequency','current_gap','frequency_plus_gap','recent_momentum','structure_profile','pair_association','triple_association','combined_equal_rank')
AC=('A_v2','C_v2','contrarian_v2')
MODELS=B+AC
RAW_NAMES=('freq','gap','recent','momentum','pair','triple')
LR=.035;L2=.0025
TEST_NULL=200;BLOCK=50;BOOT=6000;SEED=202610241100

def imp(path,name):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def load_draws():
 out=[]
 with DATA.open(encoding='utf-8-sig') as f:
  for r in csv.DictReader(f):out.append({'round':int(r['round']),'date':r['date'],'nums':tuple(sorted(int(r[f'no{i}']) for i in range(1,7)))})
 assert out[-1]['round']==1246 and [x['round'] for x in out]==list(range(1,1247));return out

def design(x):
 # x is V12 raw feature vector: intercept, 11 votes, vote_share, six z-signals, prev,adj,odd,low
 votes=x[1:12];vote_share=x[12];raw=x[13:19];prev=x[19];adj=x[20]
 vals=[1.0]+list(votes)+[vote_share]+list(raw)+[prev,adj]
 # raw squares and raw-raw interactions
 vals += [v*v for v in raw]
 vals += [raw[i]*raw[j] for i in range(6) for j in range(i+1,6)]
 vals += [vote_share*r for r in raw]
 # model-specific context interactions
 vals += [v*r for v in votes for r in raw]
 # model-model co-support interactions
 vals += [votes[i]*votes[j] for i in range(len(votes)) for j in range(i+1,len(votes))]
 return vals

def feature_names():
 names=['intercept']+list(MODELS)+['vote_share']+list(RAW_NAMES)+['prev_member','adjacent_prev']
 names += [f'{r}^2' for r in RAW_NAMES]
 names += [f'{RAW_NAMES[i]}*{RAW_NAMES[j]}' for i in range(6) for j in range(i+1,6)]
 names += [f'vote_share*{r}' for r in RAW_NAMES]
 names += [f'{m}*{r}' for m in MODELS for r in RAW_NAMES]
 names += [f'{MODELS[i]}*{MODELS[j]}' for i in range(len(MODELS)) for j in range(i+1,len(MODELS))]
 return names

def sigmoid(z):
 if z>=0:
  e=math.exp(-z);return 1/(1+e)
 e=math.exp(z);return e/(1+e)
def predict(X,w):return {n:sum(a*b for a,b in zip(w,design(X[n]))) for n in X}
def update(X,w,g2,actual):
 grad=[0.0]*len(w)
 for n in range(1,46):
  f=design(X[n]);y=1.0 if n in actual else 0.0;p=sigmoid(sum(a*b for a,b in zip(w,f)))
  for j,v in enumerate(f):grad[j]+=(p-y)*v
 for j in range(len(w)):
  gr=grad[j]/45.0+(0 if j==0 else L2*w[j]);g2[j]+=gr*gr;w[j]-=LR*gr/math.sqrt(g2[j]+1e-8)
 return w,g2

def portfolio(sc):
 r=sorted(range(1,46),key=lambda n:(-sc[n],n))[:18]
 lines=[
  r[0:6],
  r[0:2]+r[6:10],
  r[0:2]+r[10:14],
  r[2:4]+r[6:8]+r[14:16],
  r[4:6]+r[8:10]+r[16:18],
 ]
 out=[tuple(sorted(x)) for x in lines]
 assert len(set(out))==5 and len(set().union(*map(set,out)))==18
 return out,r

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
 b=[statistics.mean(vals[i:i+BLOCK]) for i in range(0,len(vals),BLOCK)];return sum(v>0 for v in b)/len(b)

def main():
 draws=load_draws();b=imp(B_SOURCE,'bv18');ac=imp(AC_SOURCE,'acv18');v12=imp(V12_SOURCE,'v12v18');bank=b.feature_structure_bank(b.make_structure_bank());freq=[0]*45;last=[0]*45;pc=Counter();tc=Counter();profiles=[Counter() for _ in range(6)]
 for d in draws[:200]:
  for n in d['nums']:freq[n-1]+=1;last[n-1]=d['round']
  pc.update(itertools.combinations(d['nums'],2));tc.update(itertools.combinations(d['nums'],3));pr=b.structure_profile(d['nums'],None)
  for i,v in enumerate(pr[:5]):profiles[i][v]+=1
 for i in range(1,200):profiles[5][b.structure_profile(draws[i]['nums'],draws[i-1]['nums'])[5]]+=1
 names=feature_names();p0=6/45;w=[math.log(p0/(1-p0))]+[0.0]*(len(names)-1);g2=[0.0]*len(names);obs=[];null=[];diffs={k:[] for k in ('max_hits','any2','any3','winning_union_coverage')};current=None
 for idx in range(200,len(draws)+1):
  hist=[q['nums'] for q in draws[:idx]];preds={**b.predictions_for_round(draws,idx,freq,last,pc,tc,profiles,bank),**ac.predict(hist)};X=v12.raw_features(draws,idx,freq,last,pc,tc,preds);sc=predict(X,w);lines,ranked=portfolio(sc)
  if idx==len(draws):
   top_weights=sorted(zip(names,w),key=lambda z:abs(z[1]),reverse=True)[:30];current={'lines':[list(t) for t in lines],'top18_ranked_numbers':ranked,'number_logits':{str(n):sc[n] for n in sc},'top_abs_weights':top_weights};break
  actual=set(draws[idx]['nums']);target=idx+1
  if target>=401:
   om=metrics(lines,actual);om['target']=target;obs.append(om);rng=random.Random(SEED+target);samples=[metrics(permuted(lines,rng),actual) for _ in range(TEST_NULL)];nm={k:statistics.mean(float(q[k]) for q in samples) for k in samples[0]};nm['target']=target;null.append(nm)
   for k in diffs:diffs[k].append(float(om[k])-nm[k])
  w,g2=update(X,w,g2,actual);d=draws[idx]
  for n in d['nums']:freq[n-1]+=1;last[n-1]=d['round']
  pc.update(itertools.combinations(d['nums'],2));tc.update(itertools.combinations(d['nums'],3));pr=b.structure_profile(d['nums'],draws[idx-1]['nums'])
  for i,v in enumerate(pr):profiles[i][v]+=1
 keys=['max_hits','any2','any3','any4','any5','any6','winning_union_coverage','union_size','mean_overlap','max_overlap'];score={'policy':{k:avg(obs,k) for k in keys},'matched_label_permutation':{k:avg(null,k) for k in keys}};score['delta']={k:score['policy'][k]-score['matched_label_permutation'][k] for k in keys};alpha=.05/4;inf={}
 for j,k in enumerate(diffs):inf[k]={'adjusted_ci_delta':ci(diffs[k],alpha,SEED+100+j),'positive_50_round_block_share':posshare(diffs[k])}
 inf['strict_portfolio_pass']=(inf['max_hits']['adjusted_ci_delta'][0]>0 and inf['any2']['adjusted_ci_delta'][0]>0 and inf['any3']['adjusted_ci_delta'][0]>0 and inf['any2']['positive_50_round_block_share']>=.65)
 payload={'created_kst':datetime.now(KST).isoformat(),'target_round':1247,'data_cutoff':1246,'policy':'ONLINE_ADAGRAD_INTERACTION_META_FIXED_CORE_DIVERSIFICATION_V18','no_future_leakage':True,'feature_count':len(names),'portfolio_rule':'Rank 45 numbers by online interaction logit; line1 ranks1-6, lines2-3 repeat ranks1-2 with ranks7-14, lines4-5 redistribute ranks3-18. Union exactly 18; no random selection.','note':'All coefficients update only after each target outcome. Model-model and model-context interactions are learned online. Strict outer gate and matched joint label-permutation comparator unchanged.','current':current,'walkforward_targets':len(obs),'scorecard':score,'inference':inf,'final_status':'STRICT_PASS' if inf['strict_portfolio_pass'] else 'FAIL_SAME_GATE'};OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':'PASS','strict_pass':inf['strict_portfolio_pass'],'scorecard':score,'inference':inf,'current':current},ensure_ascii=False))
if __name__=='__main__':main()
