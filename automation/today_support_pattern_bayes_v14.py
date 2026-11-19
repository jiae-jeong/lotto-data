#!/usr/bin/env python3
from __future__ import annotations
import csv,importlib.util,itertools,json,math,random,statistics
from collections import Counter,defaultdict
from datetime import datetime,timezone,timedelta
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'lotto_data.csv'
B_SOURCE=ROOT/'research/1245_final_pipeline_v3/recovered_original_assets/b_model_backtest.py'
AC_SOURCE=ROOT/'automation/recovered_models_v2.py'
OUT=ROOT/'analysis/2026-10-23/TODAY_SUPPORT_PATTERN_BAYES_1247_V14.json'
KST=timezone(timedelta(hours=9))
B_NAMES=('long_frequency','current_gap','frequency_plus_gap','recent_momentum','structure_profile','pair_association','triple_association','combined_equal_rank')
AC_NAMES=('A_v2','C_v2','contrarian_v2')
MODELS=B_NAMES+AC_NAMES
BASE=6/45
POOL=18
RANDOM_PER_TARGET=160;BLOCK=50;BOOT=5000;SEED=202610240300

def imp(path,name):s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def load_draws():
 out=[]
 with DATA.open(encoding='utf-8-sig') as f:
  for r in csv.DictReader(f):out.append({'round':int(r['round']),'date':r['date'],'nums':tuple(sorted(int(r[f'no{i}']) for i in range(1,7)))})
 assert out[-1]['round']==1246 and [x['round'] for x in out]==list(range(1,1247));return out
def mask_for(n,preds):
 m=0
 for i,name in enumerate(MODELS):
  if n in preds[name]:m|=1<<i
 return m
def post(stat,strength):
 wins,trials=stat
 return (wins+strength*BASE)/(trials+strength)
def score_numbers(preds,exact,countstat,modelstat,pairstat):
 out={};details={}
 for n in range(1,46):
  mask=mask_for(n,preds);support=[i for i in range(len(MODELS)) if mask&(1<<i)];cnt=len(support)
  pe=post(exact[mask],220);pc=post(countstat[cnt],140)
  pm=statistics.mean(post(modelstat[i],180) for i in support) if support else BASE
  pairs=list(itertools.combinations(support,2));pp=statistics.mean(post(pairstat[p],110) for p in pairs) if pairs else pm
  # Nonlinear exact-pattern evidence dominates, with hierarchical shrinkage for sparse masks.
  p=.42*pe+.20*pc+.18*pm+.20*pp
  # Tiny consensus calibration: only prior-estimated probabilities drive ordering.
  out[n]=p;details[n]={'mask':mask,'support_count':cnt,'supporting_models':[MODELS[i] for i in support],'p_exact':pe,'p_count':pc,'p_models':pm,'p_pairs':pp,'score':p}
 return out,details
def update_stats(preds,actual,exact,countstat,modelstat,pairstat):
 for n in range(1,46):
  y=1 if n in actual else 0;mask=mask_for(n,preds);support=[i for i in range(len(MODELS)) if mask&(1<<i)];cnt=len(support)
  exact[mask][0]+=y;exact[mask][1]+=1;countstat[cnt][0]+=y;countstat[cnt][1]+=1
  for i in support:modelstat[i][0]+=y;modelstat[i][1]+=1
  for p in itertools.combinations(support,2):pairstat[p][0]+=y;pairstat[p][1]+=1
def build(sc):
 pool=sorted(sc,key=lambda n:(-sc[n],n))[:POOL];cands=[]
 for t in itertools.combinations(pool,6):
  odd=sum(n%2 for n in t);low=sum(n<=22 for n in t);bands=len({(n-1)//10 for n in t});cons=sum(b-a==1 for a,b in zip(t,t[1:]));base=sum(sc[n] for n in t)-.006*abs(odd-3)-.005*abs(low-3)-.004*max(0,cons-2)+.0015*bands;cands.append((base,tuple(sorted(t))))
 cands.sort(key=lambda x:(-x[0],x[1]));chosen=[];used=set()
 while len(chosen)<5:
  best=None
  for base,t in cands:
   if t in used:continue
   ovs=[len(set(t)&set(q)) for q in chosen]
   # allow a 2-number core, penalize only heavier repetition
   pen=.022*sum(max(0,o-2) for o in ovs)+.010*max(0,(max(ovs) if ovs else 0)-4)
   key=(base-pen,base,tuple(-n for n in t))
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
 draws=load_draws();b=imp(B_SOURCE,'bv14');ac=imp(AC_SOURCE,'acv14');bank=b.feature_structure_bank(b.make_structure_bank());freq=[0]*45;last=[0]*45;pc=Counter();tc=Counter();profiles=[Counter() for _ in range(6)]
 for d in draws[:200]:
  for x in d['nums']:freq[x-1]+=1;last[x-1]=d['round']
  pc.update(itertools.combinations(d['nums'],2));tc.update(itertools.combinations(d['nums'],3));pr=b.structure_profile(d['nums'],None)
  for i,v in enumerate(pr[:5]):profiles[i][v]+=1
 for i in range(1,200):profiles[5][b.structure_profile(draws[i]['nums'],draws[i-1]['nums'])[5]]+=1
 exact=defaultdict(lambda:[0,0]);countstat=defaultdict(lambda:[0,0]);modelstat=defaultdict(lambda:[0,0]);pairstat=defaultdict(lambda:[0,0]);obs=[];null=[];diffs={k:[] for k in ('max_hits','any2','any3','winning_union_coverage')};current=None
 for idx in range(200,len(draws)+1):
  hist=[x['nums'] for x in draws[:idx]];preds={**b.predictions_for_round(draws,idx,freq,last,pc,tc,profiles,bank),**ac.predict(hist)};sc,details=score_numbers(preds,exact,countstat,modelstat,pairstat);lines=build(sc)
  if idx==len(draws):current={'lines':[list(x) for x in lines],'number_scores':{str(n):details[n] for n in details},'top_numbers':sorted(range(1,46),key=lambda n:(-sc[n],n))[:20]};break
  actual=set(draws[idx]['nums']);target=idx+1
  if target>=401:
   om=metrics(lines,actual);om['target']=target;obs.append(om);rng=random.Random(SEED+target);samples=[metrics(permuted(lines,rng),actual) for _ in range(RANDOM_PER_TARGET)];nm={k:statistics.mean(float(x[k]) for x in samples) for k in samples[0]};nm['target']=target;null.append(nm)
   for k in diffs:diffs[k].append(float(om[k])-nm[k])
  update_stats(preds,actual,exact,countstat,modelstat,pairstat)
  d=draws[idx]
  for x in d['nums']:freq[x-1]+=1;last[x-1]=d['round']
  pc.update(itertools.combinations(d['nums'],2));tc.update(itertools.combinations(d['nums'],3));pr=b.structure_profile(d['nums'],draws[idx-1]['nums'])
  for i,v in enumerate(pr):profiles[i][v]+=1
 keys=['max_hits','any2','any3','any4','any5','any6','winning_union_coverage','union_size','mean_overlap','max_overlap'];score={'policy':{k:avg(obs,k) for k in keys},'matched_label_permutation':{k:avg(null,k) for k in keys}};score['delta']={k:score['policy'][k]-score['matched_label_permutation'][k] for k in keys};alpha=.05/4;inf={}
 for j,k in enumerate(diffs):inf[k]={'adjusted_ci_delta':ci(diffs[k],alpha,SEED+3000+j),'positive_50_round_block_share':posshare(diffs[k])}
 inf['strict_portfolio_pass']=(inf['max_hits']['adjusted_ci_delta'][0]>0 and inf['any2']['adjusted_ci_delta'][0]>0 and inf['any3']['adjusted_ci_delta'][0]>0 and inf['any2']['positive_50_round_block_share']>=.65)
 payload={'created_kst':datetime.now(KST).isoformat(),'target_round':1247,'data_cutoff':1246,'policy':'NONLINEAR_SUPPORT_PATTERN_EMPIRICAL_BAYES_V14','no_future_leakage':True,'hierarchy':{'exact_mask_weight':.42,'support_count_weight':.20,'model_marginal_weight':.18,'model_pair_weight':.20,'prior_strengths':{'exact':220,'count':140,'model':180,'pair':110}},'note':'For target t, support-pattern posteriors use only outcomes from earlier targets. Strict gate and matched joint label-permutation comparator unchanged.','current':current,'walkforward_targets':len(obs),'scorecard':score,'inference':inf,'final_status':'STRICT_PASS' if inf['strict_portfolio_pass'] else 'FAIL_SAME_GATE'};OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':'PASS','strict_pass':inf['strict_portfolio_pass'],'scorecard':score,'inference':inf,'current':{'lines':current['lines'],'top_numbers':current['top_numbers']}},ensure_ascii=False))
if __name__=='__main__':main()
