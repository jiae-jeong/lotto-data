#!/usr/bin/env python3
from __future__ import annotations
import csv, importlib.util, itertools, json, math, random, statistics
from collections import Counter, deque
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'lotto_data.csv'
B_SOURCE=ROOT/'research/1245_final_pipeline_v3/recovered_original_assets/b_model_backtest.py'
AC_SOURCE=ROOT/'automation/recovered_models_v2.py'
OUT=ROOT/'analysis/2026-10-23/TODAY_NESTED_EXPERT_PORTFOLIO_1247_V9.json'
KST=timezone(timedelta(hours=9))
B_NAMES=('long_frequency','current_gap','frequency_plus_gap','recent_momentum','structure_profile','pair_association','triple_association','combined_equal_rank')
AC_NAMES=('A_v2','C_v2','contrarian_v2')
MODELS=B_NAMES+AC_NAMES
BASE_MEAN=.8
BASE_GE2=.17530810086113546
ROLL=200
META_ROLL=200
RANDOM_PER_TARGET=160
BLOCK=50
BOOT=5000
SEED=202610231700

# Fixed before this run. These are alternative online selectors, not post-run tuned parameters.
SELECTORS={
 'mean200':(200,1.00,0.00,0.00,0.00),
 'mean100':(100,1.00,0.00,0.00,0.00),
 'mean50':(50,1.00,0.00,0.00,0.00),
 'combo200':(200,.72,.28,0.00,0.00),
 'combo100':(100,.72,.28,0.00,0.00),
 'recent_boost':(200,.55,.20,.25,0.00),
 'stable200':(200,.78,.22,0.00,.10),
}

def imp(path,name):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def load_draws():
 out=[]
 with DATA.open(encoding='utf-8-sig') as f:
  for r in csv.DictReader(f):out.append({'round':int(r['round']),'date':r['date'],'nums':tuple(sorted(int(r[f'no{i}']) for i in range(1,7)))})
 assert out[-1]['round']==1246 and [x['round'] for x in out]==list(range(1,1247));return out

def stat_score(hist, cfg):
 win,wmean,wge2,wrecent,wvar=cfg
 hs=list(hist)[-win:]
 if not hs:return 0.0
 n=len(hs)
 mean=(sum(hs)+60*BASE_MEAN)/(n+60)
 ge2=(sum(h>=2 for h in hs)+60*BASE_GE2)/(n+60)
 r50=statistics.mean(hs[-50:]) if hs else BASE_MEAN
 var=statistics.pvariance(hs) if len(hs)>1 else 0.0
 return wmean*(mean-BASE_MEAN)+wge2*(ge2-BASE_GE2)+wrecent*(r50-BASE_MEAN)-wvar*.03*var

def select_models(preds,hists,cfg):
 # Greedy objective: prior-only reliability minus current ticket redundancy.
 chosen=[]; used_tickets=set()
 while len(chosen)<5:
  best=None
  for m in MODELS:
   if m in chosen:continue
   ticket=tuple(preds[m])
   if ticket in used_tickets:continue
   base=stat_score(hists[m],cfg)
   if not chosen:
    red=0.0
   else:
    ovs=[len(set(ticket)&set(preds[x])) for x in chosen]
    # Penalize only redundant overlap; 1-2 common strong numbers remain allowed.
    red=.018*sum(max(0,o-2) for o in ovs)+.010*max(0,max(ovs)-3)
   obj=base-red
   key=(obj,base,-MODELS.index(m))
   if best is None or key>best[0]:best=(key,m)
  if best is None:raise RuntimeError('not enough distinct expert tickets')
  m=best[1];chosen.append(m);used_tickets.add(tuple(preds[m]))
 return chosen

def metrics(lines,actual):
 ss=[set(x) for x in lines];hits=[len(x&actual) for x in ss];u=set().union(*ss);ovs=[len(ss[i]&ss[j]) for i in range(5) for j in range(i+1,5)]
 return {'max_hits':max(hits),'any2':int(max(hits)>=2),'any3':int(max(hits)>=3),'any4':int(max(hits)>=4),'any5':int(max(hits)>=5),'any6':int(max(hits)>=6),'winning_union_coverage':len(u&actual),'union_size':len(u),'mean_overlap':statistics.mean(ovs),'max_overlap':max(ovs)}

def permuted(lines,rng):
 labels=list(range(1,46));sh=labels[:];rng.shuffle(sh);mp=dict(zip(labels,sh));return [tuple(sorted(mp[n] for n in row)) for row in lines]

def util(m):
 # fixed utility used only to choose among selector policies from PRIOR outcomes
 return 1.0*m['max_hits']+1.7*m['any2']+2.8*m['any3']+.10*m['winning_union_coverage']

def choose_selector(selector_hist):
 best=None
 for s in SELECTORS:
  hs=list(selector_hist[s])[-META_ROLL:]
  # shrink toward zero excess utility; all policies face same comparator later
  score=(sum(hs))/(len(hs)+80) if hs else 0.0
  key=(score,-list(SELECTORS).index(s))
  if best is None or key>best[0]:best=(key,s)
 return best[1]

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
 draws=load_draws();b=imp(B_SOURCE,'bv9');ac=imp(AC_SOURCE,'acv9');bank=b.feature_structure_bank(b.make_structure_bank())
 freq=[0]*45;last=[0]*45;pc=Counter();tc=Counter();profiles=[Counter() for _ in range(6)]
 for d in draws[:200]:
  for x in d['nums']:freq[x-1]+=1;last[x-1]=d['round']
  pc.update(itertools.combinations(d['nums'],2));tc.update(itertools.combinations(d['nums'],3));pr=b.structure_profile(d['nums'],None)
  for i,v in enumerate(pr[:5]):profiles[i][v]+=1
 for i in range(1,200):profiles[5][b.structure_profile(draws[i]['nums'],draws[i-1]['nums'])[5]]+=1
 hists={m:deque(maxlen=ROLL) for m in MODELS};selhist={s:deque(maxlen=META_ROLL) for s in SELECTORS}
 obs=[];null=[];diffs={k:[] for k in ('max_hits','any2','any3','winning_union_coverage')};selector_counts=Counter();current=None
 for idx in range(200,len(draws)+1):
  hist=[x['nums'] for x in draws[:idx]];preds={**b.predictions_for_round(draws,idx,freq,last,pc,tc,profiles,bank),**ac.predict(hist)}
  portfolios={s:select_models(preds,hists,cfg) for s,cfg in SELECTORS.items()}
  chosen_selector=choose_selector(selhist);chosen_models=portfolios[chosen_selector];lines=[tuple(preds[m]) for m in chosen_models]
  if idx==len(draws):
   current={'selector':chosen_selector,'models':chosen_models,'lines':[list(x) for x in lines],'all_selector_models':portfolios,'model_scores':{s:{m:stat_score(hists[m],cfg) for m in MODELS} for s,cfg in SELECTORS.items()}}
   break
  actual=set(draws[idx]['nums']);target=idx+1
  # Update selector policy histories from this outcome, after selection was made.
  for s,mods in portfolios.items():
   mm=metrics([preds[m] for m in mods],actual);selhist[s].append(util(mm))
  if target>=401:
   selector_counts[chosen_selector]+=1;om=metrics(lines,actual);om['target']=target;obs.append(om)
   rng=random.Random(SEED+target);samples=[]
   for _ in range(RANDOM_PER_TARGET):samples.append(metrics(permuted(lines,rng),actual))
   nm={k:statistics.mean(float(x[k]) for x in samples) for k in samples[0]};nm['target']=target;null.append(nm)
   for k in diffs:diffs[k].append(float(om[k])-nm[k])
  for m in MODELS:hists[m].append(len(set(preds[m])&actual))
  d=draws[idx]
  for x in d['nums']:freq[x-1]+=1;last[x-1]=d['round']
  pc.update(itertools.combinations(d['nums'],2));tc.update(itertools.combinations(d['nums'],3));pr=b.structure_profile(d['nums'],draws[idx-1]['nums'])
  for i,v in enumerate(pr):profiles[i][v]+=1
 keys=['max_hits','any2','any3','any4','any5','any6','winning_union_coverage','union_size','mean_overlap','max_overlap']
 score={'policy':{k:avg(obs,k) for k in keys},'matched_label_permutation':{k:avg(null,k) for k in keys}}
 score['delta']={k:score['policy'][k]-score['matched_label_permutation'][k] for k in keys}
 alpha=.05/4;inf={}
 for j,k in enumerate(diffs):inf[k]={'adjusted_ci_delta':ci(diffs[k],alpha,SEED+8000+j),'positive_50_round_block_share':posshare(diffs[k])}
 inf['strict_portfolio_pass']=(inf['max_hits']['adjusted_ci_delta'][0]>0 and inf['any2']['adjusted_ci_delta'][0]>0 and inf['any3']['adjusted_ci_delta'][0]>0 and inf['any2']['positive_50_round_block_share']>=.65)
 payload={'created_kst':datetime.now(KST).isoformat(),'target_round':1247,'data_cutoff':1246,'policy':'NESTED_PRIOR_ONLY_EXPERT_SELECTION_V9','no_future_leakage':True,'note':'Every target chooses among fixed online selectors using only earlier outcomes; no threshold is relaxed to force PASS. Historical data have been inspected in prior research, so this is prequential/nested evidence, not a never-seen fresh holdout.','selectors':SELECTORS,'selector_counts':dict(selector_counts),'current':current,'walkforward_targets':len(obs),'random_comparator':'Joint label permutation preserving the exact five-ticket overlap/union structure at each target.','scorecard':score,'inference':inf,'final_status':'STRICT_PASS' if inf['strict_portfolio_pass'] else 'FAIL_SAME_GATE'}
 OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'status':'PASS','strict_pass':inf['strict_portfolio_pass'],'scorecard':score,'inference':inf,'current':current,'selector_counts':dict(selector_counts)},ensure_ascii=False))
if __name__=='__main__':main()
