#!/usr/bin/env python3
from __future__ import annotations
import csv, importlib.util, itertools, json, random, statistics
from collections import Counter, deque
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'lotto_data.csv'
B_SOURCE=ROOT/'research/1245_final_pipeline_v3/recovered_original_assets/b_model_backtest.py'
AC_SOURCE=ROOT/'automation/recovered_models_v2.py'
OUT=ROOT/'analysis/2026-10-23/TODAY_COMBO_SEARCH_PORTFOLIO_1247_V10.json'
KST=timezone(timedelta(hours=9))
B_NAMES=('long_frequency','current_gap','frequency_plus_gap','recent_momentum','structure_profile','pair_association','triple_association','combined_equal_rank')
AC_NAMES=('A_v2','C_v2','contrarian_v2')
MODELS=B_NAMES+AC_NAMES
COMBOS=list(itertools.combinations(MODELS,5))
ROLL=200
RANDOM_PER_TARGET=160
BLOCK=50
BOOT=5000
SEED=202610231900

# Fixed objective before V10 outcomes are computed. It explicitly targets V9's weak dimensions.
# Any3 and max_hits dominate; any2 keeps broad consistency.
W_MAX=1.0;W_ANY2=1.2;W_ANY3=3.6;W_ANY4=7.0

def imp(path,name):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def load_draws():
 out=[]
 with DATA.open(encoding='utf-8-sig') as f:
  for r in csv.DictReader(f):out.append({'round':int(r['round']),'date':r['date'],'nums':tuple(sorted(int(r[f'no{i}']) for i in range(1,7)))})
 assert out[-1]['round']==1246 and [x['round'] for x in out]==list(range(1,1247));return out

def combo_score(combo, hit_hist):
 n=min(ROLL,min((len(hit_hist[m]) for m in combo),default=0))
 if n==0:return 0.0
 vals=[]
 for j in range(-n,0):
  mx=max(hit_hist[m][j] for m in combo)
  vals.append(W_MAX*mx+W_ANY2*(mx>=2)+W_ANY3*(mx>=3)+W_ANY4*(mx>=4))
 # conservative shrinkage toward a common prior so short histories cannot dominate
 return sum(vals)/(n+100)

def choose_combo(preds,hit_hist):
 best=None
 for combo in COMBOS:
  tickets=[tuple(preds[m]) for m in combo]
  if len(set(tickets))<5:continue
  s=combo_score(combo,hit_hist)
  ss=[set(x) for x in tickets];ovs=[len(ss[i]&ss[j]) for i in range(5) for j in range(i+1,5)]
  # tiny tie-break style penalty only; historical performance remains dominant.
  redundancy=.004*statistics.mean(ovs)+.002*max(ovs)
  key=(s-redundancy,s,-statistics.mean(ovs),tuple(-MODELS.index(m) for m in combo))
  if best is None or key>best[0]:best=(key,combo)
 if best is None:raise RuntimeError('no five distinct expert tickets')
 return best[1],best[0][1]

def metrics(lines,actual):
 ss=[set(x) for x in lines];hits=[len(x&actual) for x in ss];u=set().union(*ss);ovs=[len(ss[i]&ss[j]) for i in range(5) for j in range(i+1,5)]
 return {'max_hits':max(hits),'any2':int(max(hits)>=2),'any3':int(max(hits)>=3),'any4':int(max(hits)>=4),'any5':int(max(hits)>=5),'any6':int(max(hits)>=6),'winning_union_coverage':len(u&actual),'union_size':len(u),'mean_overlap':statistics.mean(ovs),'max_overlap':max(ovs)}

def permuted(lines,rng):
 labels=list(range(1,46));sh=labels[:];rng.shuffle(sh);mp=dict(zip(labels,sh));return [tuple(sorted(mp[n] for n in row)) for row in lines]
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
 draws=load_draws();b=imp(B_SOURCE,'bv10');ac=imp(AC_SOURCE,'acv10');bank=b.feature_structure_bank(b.make_structure_bank())
 freq=[0]*45;last=[0]*45;pc=Counter();tc=Counter();profiles=[Counter() for _ in range(6)]
 for d in draws[:200]:
  for x in d['nums']:freq[x-1]+=1;last[x-1]=d['round']
  pc.update(itertools.combinations(d['nums'],2));tc.update(itertools.combinations(d['nums'],3));pr=b.structure_profile(d['nums'],None)
  for i,v in enumerate(pr[:5]):profiles[i][v]+=1
 for i in range(1,200):profiles[5][b.structure_profile(draws[i]['nums'],draws[i-1]['nums'])[5]]+=1
 hit_hist={m:deque(maxlen=ROLL) for m in MODELS};obs=[];null=[];diffs={k:[] for k in ('max_hits','any2','any3','winning_union_coverage')};combo_counts=Counter();current=None
 for idx in range(200,len(draws)+1):
  hist=[x['nums'] for x in draws[:idx]];preds={**b.predictions_for_round(draws,idx,freq,last,pc,tc,profiles,bank),**ac.predict(hist)}
  combo,train_score=choose_combo(preds,hit_hist);lines=[tuple(preds[m]) for m in combo]
  if idx==len(draws):current={'models':list(combo),'lines':[list(x) for x in lines],'trailing_objective_score':train_score};break
  actual=set(draws[idx]['nums']);target=idx+1
  if target>=401:
   combo_counts['|'.join(combo)]+=1;om=metrics(lines,actual);om['target']=target;obs.append(om)
   rng=random.Random(SEED+target);samples=[metrics(permuted(lines,rng),actual) for _ in range(RANDOM_PER_TARGET)]
   nm={k:statistics.mean(float(x[k]) for x in samples) for k in samples[0]};nm['target']=target;null.append(nm)
   for k in diffs:diffs[k].append(float(om[k])-nm[k])
  for m in MODELS:hit_hist[m].append(len(set(preds[m])&actual))
  d=draws[idx]
  for x in d['nums']:freq[x-1]+=1;last[x-1]=d['round']
  pc.update(itertools.combinations(d['nums'],2));tc.update(itertools.combinations(d['nums'],3));pr=b.structure_profile(d['nums'],draws[idx-1]['nums'])
  for i,v in enumerate(pr):profiles[i][v]+=1
 keys=['max_hits','any2','any3','any4','any5','any6','winning_union_coverage','union_size','mean_overlap','max_overlap']
 score={'policy':{k:avg(obs,k) for k in keys},'matched_label_permutation':{k:avg(null,k) for k in keys}}
 score['delta']={k:score['policy'][k]-score['matched_label_permutation'][k] for k in keys}
 alpha=.05/4;inf={}
 for j,k in enumerate(diffs):inf[k]={'adjusted_ci_delta':ci(diffs[k],alpha,SEED+7000+j),'positive_50_round_block_share':posshare(diffs[k])}
 inf['strict_portfolio_pass']=(inf['max_hits']['adjusted_ci_delta'][0]>0 and inf['any2']['adjusted_ci_delta'][0]>0 and inf['any3']['adjusted_ci_delta'][0]>0 and inf['any2']['positive_50_round_block_share']>=.65)
 payload={'created_kst':datetime.now(KST).isoformat(),'target_round':1247,'data_cutoff':1246,'policy':'TRAILING_200_FULL_PORTFOLIO_COMBO_SEARCH_V10','no_future_leakage':True,'objective_weights':{'max_hits':W_MAX,'any2':W_ANY2,'any3':W_ANY3,'any4':W_ANY4},'note':'At each target all eligible five-expert combinations are scored only on the preceding <=200 realized hit vectors. The strict gate and matched label-permutation comparator are unchanged.','current':current,'walkforward_targets':len(obs),'most_used_combos':combo_counts.most_common(12),'scorecard':score,'inference':inf,'final_status':'STRICT_PASS' if inf['strict_portfolio_pass'] else 'FAIL_SAME_GATE'}
 OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'status':'PASS','strict_pass':inf['strict_portfolio_pass'],'scorecard':score,'inference':inf,'current':current,'top_combos':combo_counts.most_common(8)},ensure_ascii=False))
if __name__=='__main__':main()
