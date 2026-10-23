#!/usr/bin/env python3
from __future__ import annotations
import csv,importlib.util,itertools,json,random,statistics,math
from collections import Counter
from datetime import datetime,timezone,timedelta
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'lotto_data.csv'
B_SOURCE=ROOT/'research/1245_final_pipeline_v3/recovered_original_assets/b_model_backtest.py'
AC_SOURCE=ROOT/'automation/recovered_models_v2.py'
V12_SOURCE=ROOT/'automation/today_raw_signal_meta_v12.py'
V18_SOURCE=ROOT/'automation/today_interaction_adagrad_v18.py'
OUT=ROOT/'analysis/2026-10-23/TODAY_FIXED_RANK30_1247_V20.json'
KST=timezone(timedelta(hours=9))
B=('long_frequency','current_gap','frequency_plus_gap','recent_momentum','structure_profile','pair_association','triple_association','combined_equal_rank')
AC=('A_v2','C_v2','contrarian_v2')
MODELS=B+AC
TEST_NULL=240;BLOCK=50;BOOT=7000;SEED=202610241500

def imp(path,name):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def load_draws():
 out=[]
 with DATA.open(encoding='utf-8-sig') as f:
  for r in csv.DictReader(f):out.append({'round':int(r['round']),'date':r['date'],'nums':tuple(sorted(int(r[f'no{i}']) for i in range(1,7)))})
 assert out[-1]['round']==1246 and [x['round'] for x in out]==list(range(1,1247));return out

def rank30(sc):
 ranked=sorted(range(1,46),key=lambda n:(-sc[n],n))[:30]
 lines=[tuple(sorted(ranked[i:i+6])) for i in range(0,30,6)]
 assert len(lines)==5 and len(set().union(*map(set,lines)))==30
 return lines,ranked

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
 b=[statistics.mean(vals[i:i+BLOCK]) for i in range(0,len(vals),BLOCK)];return sum(v>0 for v in b)/len(b),b

def main():
 draws=load_draws();b=imp(B_SOURCE,'bv20');ac=imp(AC_SOURCE,'acv20');v12=imp(V12_SOURCE,'v12v20');v18=imp(V18_SOURCE,'v18v20');bank=b.feature_structure_bank(b.make_structure_bank());freq=[0]*45;last=[0]*45;pc=Counter();tc=Counter();profiles=[Counter() for _ in range(6)]
 for d in draws[:200]:
  for n in d['nums']:freq[n-1]+=1;last[n-1]=d['round']
  pc.update(itertools.combinations(d['nums'],2));tc.update(itertools.combinations(d['nums'],3));pr=b.structure_profile(d['nums'],None)
  for i,v in enumerate(pr[:5]):profiles[i][v]+=1
 for i in range(1,200):profiles[5][b.structure_profile(draws[i]['nums'],draws[i-1]['nums'])[5]]+=1
 names=v18.feature_names();p0=6/45;w=[math.log(p0/(1-p0))]+[0.0]*(len(names)-1);g2=[0.0]*len(names);obs=[];null=[];diffs={k:[] for k in ('max_hits','any2','any3','winning_union_coverage')};current=None
 for idx in range(200,len(draws)+1):
  hist=[q['nums'] for q in draws[:idx]];preds={**b.predictions_for_round(draws,idx,freq,last,pc,tc,profiles,bank),**ac.predict(hist)};X=v12.raw_features(draws,idx,freq,last,pc,tc,preds);sc=v18.predict(X,w);lines,ranked=rank30(sc)
  if idx==len(draws):current={'lines':[list(t) for t in lines],'top30_ranked_numbers':ranked,'number_logits':{str(n):sc[n] for n in sc}};break
  actual=set(draws[idx]['nums']);target=idx+1
  if target>=401:
   om=metrics(lines,actual);om['target']=target;obs.append(om);rng=random.Random(SEED+target);sm=[metrics(permuted(lines,rng),actual) for _ in range(TEST_NULL)];nm={k:statistics.mean(float(q[k]) for q in sm) for k in sm[0]};nm['target']=target;null.append(nm)
   for k in diffs:diffs[k].append(float(om[k])-nm[k])
  w,g2=v18.update(X,w,g2,actual);d=draws[idx]
  for n in d['nums']:freq[n-1]+=1;last[n-1]=d['round']
  pc.update(itertools.combinations(d['nums'],2));tc.update(itertools.combinations(d['nums'],3));pr=b.structure_profile(d['nums'],draws[idx-1]['nums'])
  for i,v in enumerate(pr):profiles[i][v]+=1
 keys=['max_hits','any2','any3','any4','any5','any6','winning_union_coverage','union_size','mean_overlap','max_overlap'];score={'policy':{k:avg(obs,k) for k in keys},'matched_label_permutation':{k:avg(null,k) for k in keys}};score['delta']={k:score['policy'][k]-score['matched_label_permutation'][k] for k in keys};alpha=.05/4;inf={}
 for j,k in enumerate(diffs):
  share,blocks=posshare(diffs[k]);inf[k]={'adjusted_ci_delta':ci(diffs[k],alpha,SEED+20+j),'positive_50_round_block_share':share,'block_deltas':blocks}
 inf['strict_portfolio_pass']=(inf['max_hits']['adjusted_ci_delta'][0]>0 and inf['any2']['adjusted_ci_delta'][0]>0 and inf['any3']['adjusted_ci_delta'][0]>0 and inf['any2']['positive_50_round_block_share']>=.65)
 payload={'created_kst':datetime.now(KST).isoformat(),'target_round':1247,'data_cutoff':1246,'policy':'FIXED_RANK30_INTERACTION_META_V20','no_future_leakage':True,'portfolio_rule':'Use the V18 online interaction number ranking; take ranks 1-30 and partition deterministically into five disjoint six-number tickets. No portfolio-policy switching and no random selection.','note':'V20 isolates the policy-switching diagnosis from V19. V18 interaction coefficients still update only after each target. Strict gate and matched joint label-permutation comparator unchanged.','current':current,'walkforward_targets':len(obs),'scorecard':score,'inference':inf,'final_status':'STRICT_PASS' if inf['strict_portfolio_pass'] else 'FAIL_SAME_GATE'};OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':'PASS','strict_pass':inf['strict_portfolio_pass'],'scorecard':score,'inference':{k:v for k,v in inf.items() if k=='strict_portfolio_pass' or not isinstance(v,dict) or 'block_deltas' not in v} | {k:{'adjusted_ci_delta':v['adjusted_ci_delta'],'positive_50_round_block_share':v['positive_50_round_block_share']} for k,v in inf.items() if isinstance(v,dict) and 'block_deltas' in v},'current':current},ensure_ascii=False))
if __name__=='__main__':main()
