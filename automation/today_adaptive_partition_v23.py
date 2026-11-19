#!/usr/bin/env python3
from __future__ import annotations
import csv,importlib.util,itertools,json,random,statistics,math
from collections import Counter,deque
from datetime import datetime,timezone,timedelta
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'lotto_data.csv';B_SOURCE=ROOT/'research/1245_final_pipeline_v3/recovered_original_assets/b_model_backtest.py';AC_SOURCE=ROOT/'automation/recovered_models_v2.py';V12_SOURCE=ROOT/'automation/today_raw_signal_meta_v12.py';V18_SOURCE=ROOT/'automation/today_interaction_adagrad_v18.py'
OUT=ROOT/'analysis/2026-10-23/TODAY_ADAPTIVE_PARTITION_1247_V23.json';KST=timezone(timedelta(hours=9));TEST_NULL=240;BLOCK=50;BOOT=7000;SEED=202610232020;ROLL=150

def imp(p,n):s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def load():
 o=[]
 with DATA.open(encoding='utf-8-sig') as f:
  for r in csv.DictReader(f):o.append({'round':int(r['round']),'nums':tuple(sorted(int(r[f'no{i}']) for i in range(1,7)))})
 assert o[-1]['round']==1246 and [x['round'] for x in o]==list(range(1,1247));return o

def templates():
 return {
 'core6_rr':[[0,1,2,3,4,5],[6,10,14,18,22,26],[7,11,15,19,23,27],[8,12,16,20,24,28],[9,13,17,21,25,29]],
 'contiguous':[[0,1,2,3,4,5],[6,7,8,9,10,11],[12,13,14,15,16,17],[18,19,20,21,22,23],[24,25,26,27,28,29]],
 'columns':[[0,5,10,15,20,25],[1,6,11,16,21,26],[2,7,12,17,22,27],[3,8,13,18,23,28],[4,9,14,19,24,29]],
 'snake':[[0,9,10,19,20,29],[1,8,11,18,21,28],[2,7,12,17,22,27],[3,6,13,16,23,26],[4,5,14,15,24,25]],
 'top10_pairs':[[0,5,10,15,20,25],[1,6,11,16,21,26],[2,7,12,17,22,27],[3,8,13,18,23,28],[4,9,14,19,24,29]],
 'top15_mix':[[0,5,10,15,20,25],[1,6,11,16,21,26],[2,7,12,17,22,27],[3,8,13,18,23,28],[4,9,14,19,24,29]]}

def make_lines(r,pos):return [tuple(sorted(r[j] for j in p)) for p in pos]
def metrics(lines,a):
 ss=[set(x) for x in lines];h=[len(x&a) for x in ss];u=set().union(*ss);return {'max_hits':max(h),'any2':int(max(h)>=2),'any3':int(max(h)>=3),'any4':int(max(h)>=4),'winning_union_coverage':len(u&a),'union_size':len(u)}
def perm(lines,rng):
 labs=list(range(1,46));sh=labs[:];rng.shuffle(sh);mp=dict(zip(labs,sh));return [tuple(sorted(mp[n] for n in x)) for x in lines]
def objective(hist):
 if not hist:return -999
 x=list(hist)[-ROLL:];return statistics.mean(q['max_hits']+.80*q['any2']+.50*q['any3'] for q in x)
def avg(rows,k):return statistics.mean(float(x[k]) for x in rows)
def ci(v,alpha,seed):
 blocks=[v[i:i+BLOCK] for i in range(0,len(v),BLOCK)];rng=random.Random(seed);re=[]
 for _ in range(BOOT):
  flat=[]
  for __ in range(len(blocks)):flat+=blocks[rng.randrange(len(blocks))]
  re.append(statistics.mean(flat))
 re.sort();return [re[int(alpha/2*(len(re)-1))],re[int((1-alpha/2)*(len(re)-1))]]
def share(v):
 b=[statistics.mean(v[i:i+BLOCK]) for i in range(0,len(v),BLOCK)];return sum(x>0 for x in b)/len(b),b

def main():
 draws=load();b=imp(B_SOURCE,'bv23');ac=imp(AC_SOURCE,'acv23');v12=imp(V12_SOURCE,'v12v23');v18=imp(V18_SOURCE,'v18v23');bank=b.feature_structure_bank(b.make_structure_bank());freq=[0]*45;last=[0]*45;pc=Counter();tc=Counter();prof=[Counter() for _ in range(6)]
 for d in draws[:200]:
  for n in d['nums']:freq[n-1]+=1;last[n-1]=d['round']
  pc.update(itertools.combinations(d['nums'],2));tc.update(itertools.combinations(d['nums'],3));pr=b.structure_profile(d['nums'],None)
  for i,v in enumerate(pr[:5]):prof[i][v]+=1
 for i in range(1,200):prof[5][b.structure_profile(draws[i]['nums'],draws[i-1]['nums'])[5]]+=1
 names=v18.feature_names();p0=6/45;w=[math.log(p0/(1-p0))]+[0.0]*(len(names)-1);g2=[0.0]*len(names);T=templates();hist={k:deque(maxlen=ROLL) for k in T};obs=[];nul=[];diff={k:[] for k in ('max_hits','any2','any3','winning_union_coverage')};sel_count=Counter();current=None
 for idx in range(200,len(draws)+1):
  preds={**b.predictions_for_round(draws,idx,freq,last,pc,tc,prof,bank),**ac.predict([q['nums'] for q in draws[:idx]])};X=v12.raw_features(draws,idx,freq,last,pc,tc,preds);sc=v18.predict(X,w);r=sorted(range(1,46),key=lambda n:(-sc[n],n))[:30];all_lines={k:make_lines(r,p) for k,p in T.items()}
  if idx<300:chosen='core6_rr'
  else:chosen=max(T,key=lambda k:(objective(hist[k]),k))
  lines=all_lines[chosen]
  if idx==len(draws):current={'template':chosen,'template_scores':{k:objective(hist[k]) for k in T},'lines':[list(x) for x in lines],'top30_ranked_numbers':r};break
  actual=set(draws[idx]['nums']);target=idx+1
  for k,L in all_lines.items():hist[k].append(metrics(L,actual))
  if target>=401:
   sel_count[chosen]+=1;om=metrics(lines,actual);om['target']=target;obs.append(om);rng=random.Random(SEED+target);sm=[metrics(perm(lines,rng),actual) for _ in range(TEST_NULL)];nm={k:statistics.mean(float(q[k]) for q in sm) for k in sm[0]};nul.append(nm)
   for k in diff:diff[k].append(float(om[k])-nm[k])
  w,g2=v18.update(X,w,g2,actual);d=draws[idx]
  for n in d['nums']:freq[n-1]+=1;last[n-1]=d['round']
  pc.update(itertools.combinations(d['nums'],2));tc.update(itertools.combinations(d['nums'],3));pr=b.structure_profile(d['nums'],draws[idx-1]['nums'])
  for i,v in enumerate(pr):prof[i][v]+=1
 keys=['max_hits','any2','any3','any4','winning_union_coverage','union_size'];score={'policy':{k:avg(obs,k) for k in keys},'matched_label_permutation':{k:avg(nul,k) for k in keys}};score['delta']={k:score['policy'][k]-score['matched_label_permutation'][k] for k in keys};alpha=.05/4;inf={}
 for j,k in enumerate(diff):
  s,blocks=share(diff[k]);inf[k]={'adjusted_ci_delta':ci(diff[k],alpha,SEED+30+j),'positive_50_round_block_share':s,'block_deltas':blocks}
 inf['strict_portfolio_pass']=inf['max_hits']['adjusted_ci_delta'][0]>0 and inf['any2']['adjusted_ci_delta'][0]>0 and inf['any3']['adjusted_ci_delta'][0]>0 and inf['any2']['positive_50_round_block_share']>=.65
 payload={'created_kst':datetime.now(KST).isoformat(),'target_round':1247,'data_cutoff':1246,'policy':'ADAPTIVE_PARTITION_RANK30_V23','no_future_leakage':True,'ranking_model':'V18 interaction AdaGrad unchanged','selection_rule':'Choose one predeclared rank-partition template using only the prior rolling 150 targets objective=max_hits+0.80*any2+0.50*any3; strict gate unchanged.','template_selection_counts':dict(sel_count),'current':current,'walkforward_targets':len(obs),'scorecard':score,'inference':inf,'final_status':'STRICT_PASS' if inf['strict_portfolio_pass'] else 'FAIL_SAME_GATE'};OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':'PASS','strict_pass':inf['strict_portfolio_pass'],'scorecard':score,'current':current,'template_selection_counts':dict(sel_count),'inference':{k:{'adjusted_ci_delta':v['adjusted_ci_delta'],'positive_50_round_block_share':v['positive_50_round_block_share']} for k,v in inf.items() if isinstance(v,dict)}},ensure_ascii=False))
if __name__=='__main__':main()
