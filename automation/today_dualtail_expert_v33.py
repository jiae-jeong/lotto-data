#!/usr/bin/env python3
from __future__ import annotations
import itertools,json,random,statistics,math
from collections import Counter,deque
from datetime import datetime,timezone,timedelta
from pathlib import Path
import importlib.util

ROOT=Path(__file__).resolve().parents[1]
V31_SOURCE=ROOT/'automation/today_crosshybrid_v31.py'
B_SOURCE=ROOT/'research/1245_final_pipeline_v3/recovered_original_assets/b_model_backtest.py'
AC_SOURCE=ROOT/'automation/recovered_models_v2.py'
V12_SOURCE=ROOT/'automation/today_raw_signal_meta_v12.py'
V18_SOURCE=ROOT/'automation/today_interaction_adagrad_v18.py'
OUT=ROOT/'analysis/2026-10-30/TODAY_DUALTAIL_EXPERT_1248_V33.json'
KST=timezone(timedelta(hours=9));TEST_NULL=240;BLOCK=50;BOOT=7000;SEED=202610301000;ROLL=150;LR=.035;L2=.0025
CFG={'slow':(1.0,1.0),'medium':(.9995,.999),'fast':(.9975,.992)}

def imp(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def obj(h):
 if not h:return -999
 x=list(h)[-ROLL:]
 # Predeclared bottleneck-focused objective: preserve max/2+ while giving 3+
 # enough weight to distinguish the complementary multiwindow tail.
 return statistics.mean(q['max_hits']+.85*q['any2']+1.60*q['any3'] for q in x)

def main():
 OUT.parent.mkdir(parents=True,exist_ok=True)
 base=imp(V31_SOURCE,'v31base33');draws=base.load();b=imp(B_SOURCE,'bv33');ac=imp(AC_SOURCE,'acv33');v12=imp(V12_SOURCE,'v12v33');v18=imp(V18_SOURCE,'v18v33')
 bank=b.feature_structure_bank(b.make_structure_bank());freq=[0]*45;last=[0]*45;pc=Counter();tc=Counter();prof=[Counter() for _ in range(6)]
 for d in draws[:200]:
  for n in d['nums']:freq[n-1]+=1;last[n-1]=d['round']
  pc.update(itertools.combinations(d['nums'],2));tc.update(itertools.combinations(d['nums'],3));pr=b.structure_profile(d['nums'],None)
  for i,v in enumerate(pr[:5]):prof[i][v]+=1
 for i in range(1,200):prof[5][b.structure_profile(draws[i]['nums'],draws[i-1]['nums'])[5]]+=1
 p0=6/45;dim_old=len(v18.feature_names());dummyX=[0.0]*23;dim_mw=len(base.design_mw(v18,dummyX,[0.0]*6))
 old={k:{'w':[math.log(p0/(1-p0))]+[0.0]*(dim_old-1),'g2':[0.0]*dim_old} for k in CFG};mw={k:{'w':[math.log(p0/(1-p0))]+[0.0]*(dim_mw-1),'g2':[0.0]*dim_mw} for k in CFG}
 T=base.tails();names=[f'{src}:{t}' for src in ('oldtail','mwtail') for t in T];hist={k:deque(maxlen=ROLL) for k in names};obs=[];nul=[];diff={k:[] for k in ('max_hits','any2','any3','winning_union_coverage')};count=Counter();current=None
 for idx in range(200,len(draws)+1):
  preds={**b.predictions_for_round(draws,idx,freq,last,pc,tc,prof,bank),**ac.predict([q['nums'] for q in draws[:idx]])};X=v12.raw_features(draws,idx,freq,last,pc,tc,preds);E=base.extras(draws,idx,freq)
  os={k:base.predict_old(v18,X,s['w']) for k,s in old.items()};oz={k:base.zscore(v) for k,v in os.items()};oldblend={n:sum(oz[k][n] for k in CFG)/len(CFG) for n in range(1,46)}
  ms={k:base.predict_mw(v18,X,E,s['w']) for k,s in mw.items()};mz={k:base.zscore(v) for k,v in ms.items()};mwblend={n:sum(mz[k][n] for k in CFG)/len(CFG) for n in range(1,46)}
  core=sorted(range(1,46),key=lambda n:(-ms['slow'][n],n))[:6]
  ro=core+sorted((n for n in range(1,46) if n not in core),key=lambda n:(-oldblend[n],n))[:24]
  rm=core+sorted((n for n in range(1,46) if n not in core),key=lambda n:(-mwblend[n],n))[:24]
  experts={f'oldtail:{t}':base.lines(ro,p) for t,p in T.items()};experts.update({f'mwtail:{t}':base.lines(rm,p) for t,p in T.items()})
  chosen='oldtail:rr' if idx<320 else max(names,key=lambda k:(obj(hist[k]),k));L=experts[chosen]
  if idx==len(draws):
   current={'chosen_expert':chosen,'expert_scores':{k:obj(hist[k]) for k in names},'lines':[list(x) for x in L],'multiwindow_core':core,'oldtail_top30':ro,'mwtail_top30':rm};break
  actual=set(draws[idx]['nums']);target=idx+1
  for k,Q in experts.items():hist[k].append(base.met(Q,actual))
  if target>=401:
   count[chosen]+=1;om=base.met(L,actual);obs.append(om);rng=random.Random(SEED+target);sm=[base.met(base.perm(L,rng),actual) for _ in range(TEST_NULL)];nm={k:statistics.mean(float(q[k]) for q in sm) for k in sm[0]};nul.append(nm)
   for k in diff:diff[k].append(float(om[k])-nm[k])
  for k,(sh,gd) in CFG.items():old[k]['w'],old[k]['g2']=base.update_generic(v18,X,E,old[k]['w'],old[k]['g2'],actual,sh,gd,False);mw[k]['w'],mw[k]['g2']=base.update_generic(v18,X,E,mw[k]['w'],mw[k]['g2'],actual,sh,gd,True)
  d=draws[idx]
  for n in d['nums']:freq[n-1]+=1;last[n-1]=d['round']
  pc.update(itertools.combinations(d['nums'],2));tc.update(itertools.combinations(d['nums'],3));pr=b.structure_profile(d['nums'],draws[idx-1]['nums'])
  for i,v in enumerate(pr):prof[i][v]+=1
 keys=['max_hits','any2','any3','any4','winning_union_coverage','union_size'];score={'policy':{k:base.avg(obs,k) for k in keys},'matched_label_permutation':{k:base.avg(nul,k) for k in keys}};score['delta']={k:score['policy'][k]-score['matched_label_permutation'][k] for k in keys};alpha=.05/4;inf={}
 for j,k in enumerate(diff):
  s,bk=base.share(diff[k]);inf[k]={'adjusted_ci_delta':base.ci(diff[k],alpha,SEED+50+j),'positive_50_round_block_share':s,'block_deltas':bk}
 inf['strict_portfolio_pass']=inf['max_hits']['adjusted_ci_delta'][0]>0 and inf['any2']['adjusted_ci_delta'][0]>0 and inf['any3']['adjusted_ci_delta'][0]>0 and inf['any2']['positive_50_round_block_share']>=.65
 payload={'created_kst':datetime.now(KST).isoformat(),'target_round':1248,'data_cutoff':1247,'policy':'PREQUENTIAL_DUALTAIL_EXPERT_V33','no_future_leakage':True,'selection_rule':'Fixed V30 multiwindow core. Eight predeclared experts = old-feature tail or multiwindow tail x four fixed partitions. At every target select only from prior rolling150 objective=max_hits+0.85*any2+1.60*any3. Strict outer gate/comparator unchanged.','expert_selection_counts':dict(count),'current':current,'walkforward_targets':len(obs),'scorecard':score,'inference':inf,'final_status':'STRICT_PASS' if inf['strict_portfolio_pass'] else 'FAIL_SAME_GATE'};OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'strict_pass':inf['strict_portfolio_pass'],'scorecard':score,'current':current,'expert_selection_counts':dict(count),'inference':{k:{'adjusted_ci_delta':v['adjusted_ci_delta'],'positive_50_round_block_share':v['positive_50_round_block_share']} for k,v in inf.items() if isinstance(v,dict)}},ensure_ascii=False))
if __name__=='__main__':main()
