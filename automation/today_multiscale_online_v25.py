#!/usr/bin/env python3
from __future__ import annotations
import csv,importlib.util,itertools,json,random,statistics,math
from collections import Counter,deque
from datetime import datetime,timezone,timedelta
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'lotto_data.csv';B_SOURCE=ROOT/'research/1245_final_pipeline_v3/recovered_original_assets/b_model_backtest.py';AC_SOURCE=ROOT/'automation/recovered_models_v2.py';V12_SOURCE=ROOT/'automation/today_raw_signal_meta_v12.py';V18_SOURCE=ROOT/'automation/today_interaction_adagrad_v18.py'
OUT=ROOT/'analysis/2026-10-23/TODAY_MULTISCALE_ONLINE_1247_V25.json';KST=timezone(timedelta(hours=9))
TEST_NULL=240;BLOCK=50;BOOT=7000;SEED=202610231548;ROLL=120;LR=.035;L2=.0025
CFG={'slow':(1.0,1.0),'medium':(.9995,.999),'fast':(.9975,.992)}

def imp(p,n):s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def load():
 o=[]
 with DATA.open(encoding='utf-8-sig') as f:
  for r in csv.DictReader(f):o.append({'round':int(r['round']),'nums':tuple(sorted(int(r[f'no{i}']) for i in range(1,7)))})
 assert o[-1]['round']==1246 and [x['round'] for x in o]==list(range(1,1247));return o

def upd(v18,X,w,g2,shrink,gdec):
 grad=[0.0]*len(w)
 for n in range(1,46):
  f=v18.design(X[n]);y=1.0 if n in CURRENT_ACTUAL else 0.0;p=v18.sigmoid(sum(a*b for a,b in zip(w,f)))
  for j,x in enumerate(f):grad[j]+=(p-y)*x
 for j in range(len(w)):
  if j>0:w[j]*=shrink
  gr=grad[j]/45.0+(0 if j==0 else L2*w[j]);g2[j]=gdec*g2[j]+gr*gr;w[j]-=LR*gr/math.sqrt(g2[j]+1e-8)
 return w,g2

def zscore(sc):
 vals=list(sc.values());m=statistics.mean(vals);s=statistics.pstdev(vals) or 1.0;return {n:(v-m)/s for n,v in sc.items()}
def portfolio(sc):
 r=sorted(range(1,46),key=lambda n:(-sc[n],n))[:30]
 pos=[[0,1,2,3,4,5],[6,10,14,18,22,26],[7,11,15,19,23,27],[8,12,16,20,24,28],[9,13,17,21,25,29]]
 L=[tuple(sorted(r[j] for j in p)) for p in pos];assert len(set().union(*map(set,L)))==30
 return L,r

def met(L,a):
 h=[len(set(x)&a) for x in L];u=set().union(*map(set,L));return {'max_hits':max(h),'any2':int(max(h)>=2),'any3':int(max(h)>=3),'any4':int(max(h)>=4),'winning_union_coverage':len(u&a),'union_size':len(u)}
def perm(L,rng):
 labs=list(range(1,46));sh=labs[:];rng.shuffle(sh);mp=dict(zip(labs,sh));return [tuple(sorted(mp[n] for n in x)) for x in L]
def obj(h):
 if not h:return -999
 x=list(h)[-ROLL:];return statistics.mean(q['max_hits']+.80*q['any2']+1.20*q['any3']+.15*q['winning_union_coverage'] for q in x)
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
 global CURRENT_ACTUAL
 draws=load();b=imp(B_SOURCE,'bv25');ac=imp(AC_SOURCE,'acv25');v12=imp(V12_SOURCE,'v12v25');v18=imp(V18_SOURCE,'v18v25');bank=b.feature_structure_bank(b.make_structure_bank());freq=[0]*45;last=[0]*45;pc=Counter();tc=Counter();prof=[Counter() for _ in range(6)]
 for d in draws[:200]:
  for n in d['nums']:freq[n-1]+=1;last[n-1]=d['round']
  pc.update(itertools.combinations(d['nums'],2));tc.update(itertools.combinations(d['nums'],3));pr=b.structure_profile(d['nums'],None)
  for i,v in enumerate(pr[:5]):prof[i][v]+=1
 for i in range(1,200):prof[5][b.structure_profile(draws[i]['nums'],draws[i-1]['nums'])[5]]+=1
 p0=6/45;dim=len(v18.feature_names());states={k:{'w':[math.log(p0/(1-p0))]+[0.0]*(dim-1),'g2':[0.0]*dim} for k in CFG};hist={k:deque(maxlen=ROLL) for k in (*CFG,'blend')};obs=[];nul=[];diff={k:[] for k in ('max_hits','any2','any3','winning_union_coverage')};count=Counter();current=None
 for idx in range(200,len(draws)+1):
  preds={**b.predictions_for_round(draws,idx,freq,last,pc,tc,prof,bank),**ac.predict([q['nums'] for q in draws[:idx]])};X=v12.raw_features(draws,idx,freq,last,pc,tc,preds)
  scores={k:v18.predict(X,s['w']) for k,s in states.items()};zs={k:zscore(v) for k,v in scores.items()};scores['blend']={n:sum(zs[k][n] for k in CFG)/len(CFG) for n in range(1,46)};ports={k:portfolio(sc) for k,sc in scores.items()}
  chosen='blend' if idx<320 else max(ports,key=lambda k:(obj(hist[k]),k));L,r=ports[chosen]
  if idx==len(draws):current={'chosen_learner':chosen,'learner_scores':{k:obj(hist[k]) for k in ports},'lines':[list(x) for x in L],'top30_ranked_numbers':r};break
  actual=set(draws[idx]['nums']);CURRENT_ACTUAL=actual;target=idx+1
  for k,(Q,_) in ports.items():hist[k].append(met(Q,actual))
  if target>=401:
   count[chosen]+=1;om=met(L,actual);obs.append(om);rng=random.Random(SEED+target);sm=[met(perm(L,rng),actual) for _ in range(TEST_NULL)];nm={k:statistics.mean(float(q[k]) for q in sm) for k in sm[0]};nul.append(nm)
   for k in diff:diff[k].append(float(om[k])-nm[k])
  for k,(sh,gd) in CFG.items():states[k]['w'],states[k]['g2']=upd(v18,X,states[k]['w'],states[k]['g2'],sh,gd)
  d=draws[idx]
  for n in d['nums']:freq[n-1]+=1;last[n-1]=d['round']
  pc.update(itertools.combinations(d['nums'],2));tc.update(itertools.combinations(d['nums'],3));pr=b.structure_profile(d['nums'],draws[idx-1]['nums'])
  for i,v in enumerate(pr):prof[i][v]+=1
 keys=['max_hits','any2','any3','any4','winning_union_coverage','union_size'];score={'policy':{k:avg(obs,k) for k in keys},'matched_label_permutation':{k:avg(nul,k) for k in keys}};score['delta']={k:score['policy'][k]-score['matched_label_permutation'][k] for k in keys};alpha=.05/4;inf={}
 for j,k in enumerate(diff):
  s,bk=share(diff[k]);inf[k]={'adjusted_ci_delta':ci(diff[k],alpha,SEED+50+j),'positive_50_round_block_share':s,'block_deltas':bk}
 inf['strict_portfolio_pass']=inf['max_hits']['adjusted_ci_delta'][0]>0 and inf['any2']['adjusted_ci_delta'][0]>0 and inf['any3']['adjusted_ci_delta'][0]>0 and inf['any2']['positive_50_round_block_share']>=.65
 payload={'created_kst':datetime.now(KST).isoformat(),'target_round':1247,'data_cutoff':1246,'policy':'MULTISCALE_ONLINE_RANK30_V25','no_future_leakage':True,'selection_rule':'Maintain slow/medium/fast V18 online learners plus equal-z blend. Choose learner only from prior rolling120 portfolio outcomes. Fixed V22 core6+round-robin portfolio; strict gate unchanged.','learner_selection_counts':dict(count),'current':current,'walkforward_targets':len(obs),'scorecard':score,'inference':inf,'final_status':'STRICT_PASS' if inf['strict_portfolio_pass'] else 'FAIL_SAME_GATE'};OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':'PASS','strict_pass':inf['strict_portfolio_pass'],'scorecard':score,'current':current,'learner_selection_counts':dict(count),'inference':{k:{'adjusted_ci_delta':v['adjusted_ci_delta'],'positive_50_round_block_share':v['positive_50_round_block_share']} for k,v in inf.items() if isinstance(v,dict)}},ensure_ascii=False))
if __name__=='__main__':main()
