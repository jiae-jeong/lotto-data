#!/usr/bin/env python3
from __future__ import annotations
import csv,importlib.util,itertools,json,random,statistics,math
from collections import Counter,deque
from datetime import datetime,timezone,timedelta
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'lotto_data.csv'
B_SOURCE=ROOT/'research/1245_final_pipeline_v3/recovered_original_assets/b_model_backtest.py'
AC_SOURCE=ROOT/'automation/recovered_models_v2.py'
V12_SOURCE=ROOT/'automation/today_raw_signal_meta_v12.py'
V18_SOURCE=ROOT/'automation/today_interaction_adagrad_v18.py'
OUT=ROOT/'analysis/2026-10-23/TODAY_ADAPTIVE_PORTFOLIO_1247_V19.json'
KST=timezone(timedelta(hours=9))
B=('long_frequency','current_gap','frequency_plus_gap','recent_momentum','structure_profile','pair_association','triple_association','combined_equal_rank')
AC=('A_v2','C_v2','contrarian_v2')
MODELS=B+AC
POLICIES=('rank24','rank18','rank30','expert50','hybrid')
TRAIN_NULL=28;TEST_NULL=200;ROLL=200
BLOCK=50;BOOT=6000;SEED=202610241300

def imp(path,name):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def load_draws():
 out=[]
 with DATA.open(encoding='utf-8-sig') as f:
  for r in csv.DictReader(f):out.append({'round':int(r['round']),'date':r['date'],'nums':tuple(sorted(int(r[f'no{i}']) for i in range(1,7)))})
 assert out[-1]['round']==1246 and [x['round'] for x in out]==list(range(1,1247));return out

def rank24(r):
 return [tuple(sorted(x)) for x in [r[0:6],r[0:2]+r[6:10],r[2:4]+r[10:14],r[4:6]+r[14:18],r[18:24]]]
def rank30(r):return [tuple(sorted(r[i:i+6])) for i in range(0,30,6)]
def expert50(preds,hists,anchor=None):
 ranked=sorted(MODELS,key=lambda m:(-(sum(hists[m][-50:])+40*.8)/(len(hists[m][-50:])+40),MODELS.index(m)))
 chosen=[];used=set()
 if anchor is not None:chosen=[('interaction_anchor',tuple(anchor))];used.add(tuple(anchor))
 for m in ranked:
  t=tuple(preds[m])
  if t in used:continue
  ovs=[len(set(t)&set(q[1])) for q in chosen]
  # in hybrid, do not copy almost the whole anchor; otherwise retain strong repeats.
  if anchor is not None and ovs and max(ovs)>=5:continue
  chosen.append((m,t));used.add(t)
  if len(chosen)==5:break
 if len(chosen)<5:raise RuntimeError('not enough distinct expert tickets')
 return [q[1] for q in chosen]
def metrics(lines,actual):
 ss=[set(x) for x in lines];hits=[len(x&actual) for x in ss];u=set().union(*ss);ovs=[len(ss[i]&ss[j]) for i in range(5) for j in range(i+1,5)]
 return {'max_hits':max(hits),'any2':int(max(hits)>=2),'any3':int(max(hits)>=3),'any4':int(max(hits)>=4),'any5':int(max(hits)>=5),'any6':int(max(hits)>=6),'winning_union_coverage':len(u&actual),'union_size':len(u),'mean_overlap':statistics.mean(ovs),'max_overlap':max(ovs)}
def permuted(lines,rng):
 labs=list(range(1,46));sh=labs[:];rng.shuffle(sh);mp=dict(zip(labs,sh));return [tuple(sorted(mp[n] for n in row)) for row in lines]
def choose_policy(ph):
 best=None;details={}
 for p in POLICIES:
  rows=list(ph[p])[-ROLL:];n=len(rows)
  if n:
   shrink=n/(n+80);em=statistics.mean(q[0] for q in rows)*shrink;e2=statistics.mean(q[1] for q in rows)*shrink;e3=statistics.mean(q[2] for q in rows)*shrink
  else:em=e2=e3=0.0
  norm=[em/.10,e2/.05,e3/.03];score=min(norm)+.08*sum(norm);details[p]={'excess_max':em,'excess_any2':e2,'excess_any3':e3,'bottleneck_score':score,'n':n}
  key=(score,-POLICIES.index(p))
  if best is None or key>best[0]:best=(key,p)
 return best[1],details
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
 draws=load_draws();b=imp(B_SOURCE,'bv19');ac=imp(AC_SOURCE,'acv19');v12=imp(V12_SOURCE,'v12v19');v18=imp(V18_SOURCE,'v18v19');bank=b.feature_structure_bank(b.make_structure_bank());freq=[0]*45;last=[0]*45;pc=Counter();tc=Counter();profiles=[Counter() for _ in range(6)]
 for d in draws[:200]:
  for n in d['nums']:freq[n-1]+=1;last[n-1]=d['round']
  pc.update(itertools.combinations(d['nums'],2));tc.update(itertools.combinations(d['nums'],3));pr=b.structure_profile(d['nums'],None)
  for i,v in enumerate(pr[:5]):profiles[i][v]+=1
 for i in range(1,200):profiles[5][b.structure_profile(draws[i]['nums'],draws[i-1]['nums'])[5]]+=1
 names=v18.feature_names();p0=6/45;w=[math.log(p0/(1-p0))]+[0.0]*(len(names)-1);g2=[0.0]*len(names);mh={m:deque(maxlen=50) for m in MODELS};ph={p:deque(maxlen=ROLL) for p in POLICIES};use=Counter();obs=[];null=[];diffs={k:[] for k in ('max_hits','any2','any3','winning_union_coverage')};current=None
 for idx in range(200,len(draws)+1):
  hist=[q['nums'] for q in draws[:idx]];preds={**b.predictions_for_round(draws,idx,freq,last,pc,tc,profiles,bank),**ac.predict(hist)};X=v12.raw_features(draws,idx,freq,last,pc,tc,preds);sc=v18.predict(X,w);ranked=sorted(range(1,46),key=lambda n:(-sc[n],n));r18,_=v18.portfolio(sc);r24=rank24(ranked);r30=rank30(ranked);e50=expert50(preds,mh);hy=expert50(preds,mh,anchor=tuple(ranked[:6]));ports={'rank24':r24,'rank18':r18,'rank30':r30,'expert50':e50,'hybrid':hy};chosen,pdetails=choose_policy(ph);lines=ports[chosen]
  if idx==len(draws):current={'policy':chosen,'policy_prior_details':pdetails,'lines':[list(t) for t in lines],'all_current_policies':{p:[list(t) for t in ports[p]] for p in POLICIES},'top30_ranked_numbers':ranked[:30]};break
  actual=set(draws[idx]['nums']);target=idx+1
  if target>=401:
   use[chosen]+=1;om=metrics(lines,actual);om['target']=target;obs.append(om);rng=random.Random(SEED+target);sm=[metrics(permuted(lines,rng),actual) for _ in range(TEST_NULL)];nm={k:statistics.mean(float(q[k]) for q in sm) for k in sm[0]};nm['target']=target;null.append(nm)
   for k in diffs:diffs[k].append(float(om[k])-nm[k])
  # after outcome resolves, update every portfolio policy with its matched-null excess triple
  for pi,p in enumerate(POLICIES):
   real=metrics(ports[p],actual);rng=random.Random(SEED+900000+target*17+pi);sm=[metrics(permuted(ports[p],rng),actual) for _ in range(TRAIN_NULL)];bm={k:statistics.mean(q[k] for q in sm) for k in ('max_hits','any2','any3')};ph[p].append((real['max_hits']-bm['max_hits'],real['any2']-bm['any2'],real['any3']-bm['any3']))
  for m in MODELS:mh[m].append(len(set(preds[m])&actual))
  w,g2=v18.update(X,w,g2,actual);d=draws[idx]
  for n in d['nums']:freq[n-1]+=1;last[n-1]=d['round']
  pc.update(itertools.combinations(d['nums'],2));tc.update(itertools.combinations(d['nums'],3));pr=b.structure_profile(d['nums'],draws[idx-1]['nums'])
  for i,v in enumerate(pr):profiles[i][v]+=1
 keys=['max_hits','any2','any3','any4','any5','any6','winning_union_coverage','union_size','mean_overlap','max_overlap'];score={'policy':{k:avg(obs,k) for k in keys},'matched_label_permutation':{k:avg(null,k) for k in keys}};score['delta']={k:score['policy'][k]-score['matched_label_permutation'][k] for k in keys};alpha=.05/4;inf={}
 for j,k in enumerate(diffs):inf[k]={'adjusted_ci_delta':ci(diffs[k],alpha,SEED+50+j),'positive_50_round_block_share':posshare(diffs[k])}
 inf['strict_portfolio_pass']=(inf['max_hits']['adjusted_ci_delta'][0]>0 and inf['any2']['adjusted_ci_delta'][0]>0 and inf['any3']['adjusted_ci_delta'][0]>0 and inf['any2']['positive_50_round_block_share']>=.65)
 payload={'created_kst':datetime.now(KST).isoformat(),'target_round':1247,'data_cutoff':1246,'policy':'PRIOR_ONLY_ADAPTIVE_PORTFOLIO_STRUCTURE_V19','no_future_leakage':True,'candidate_policies':POLICIES,'selection_rule':'Choose the portfolio template with the best prior-only bottleneck score across matched-null excess max_hits, any2, any3; V18 interaction ranking and expert50 are updated only after each target.','policy_use_counts':dict(use),'current':current,'walkforward_targets':len(obs),'scorecard':score,'inference':inf,'final_status':'STRICT_PASS' if inf['strict_portfolio_pass'] else 'FAIL_SAME_GATE'};OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':'PASS','strict_pass':inf['strict_portfolio_pass'],'scorecard':score,'inference':inf,'policy_use_counts':dict(use),'current':current},ensure_ascii=False))
if __name__=='__main__':main()
