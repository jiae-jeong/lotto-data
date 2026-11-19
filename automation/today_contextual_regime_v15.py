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
OUT=ROOT/'analysis/2026-10-23/TODAY_CONTEXTUAL_REGIME_1247_V15.json'
KST=timezone(timedelta(hours=9))
B=('long_frequency','current_gap','frequency_plus_gap','recent_momentum','structure_profile','pair_association','triple_association','combined_equal_rank')
AC=('A_v2','C_v2','contrarian_v2')
MODELS=B+AC
POLICIES={
 'balanced':('triple_association','long_frequency','structure_profile','A_v2','contrarian_v2','pair_association','frequency_plus_gap','recent_momentum','current_gap','combined_equal_rank','C_v2'),
 'relation':('triple_association','pair_association','structure_profile','combined_equal_rank','A_v2','contrarian_v2','long_frequency','recent_momentum','frequency_plus_gap','current_gap','C_v2'),
 'freq_gap':('long_frequency','frequency_plus_gap','current_gap','combined_equal_rank','contrarian_v2','triple_association','structure_profile','A_v2','pair_association','recent_momentum','C_v2'),
 'recent':('recent_momentum','structure_profile','triple_association','A_v2','current_gap','pair_association','contrarian_v2','long_frequency','frequency_plus_gap','combined_equal_rank','C_v2'),
 'diverse':('contrarian_v2','long_frequency','pair_association','structure_profile','recent_momentum','triple_association','current_gap','A_v2','frequency_plus_gap','combined_equal_rank','C_v2'),
 'core_plus_hedge':('triple_association','A_v2','long_frequency','contrarian_v2','structure_profile','pair_association','recent_momentum','frequency_plus_gap','current_gap','combined_equal_rank','C_v2'),
}
ETA=.045;L2=.002;TRAIN_NULL=16;TEST_NULL=160
BLOCK=50;BOOT=5000;SEED=202610240500

def imp(path,name):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def load_draws():
 out=[]
 with DATA.open(encoding='utf-8-sig') as f:
  for r in csv.DictReader(f):out.append({'round':int(r['round']),'date':r['date'],'nums':tuple(sorted(int(r[f'no{i}']) for i in range(1,7)))})
 assert out[-1]['round']==1246 and [x['round'] for x in out]==list(range(1,1247));return out

def make_policy(preds,order):
 out=[];seen=set()
 for m in order:
  t=tuple(preds[m])
  if t in seen:continue
  out.append(t);seen.add(t)
  if len(out)==5:return out
 raise RuntimeError('not enough distinct model tickets')

def metrics(lines,actual):
 ss=[set(x) for x in lines];hits=[len(x&actual) for x in ss];u=set().union(*ss);ovs=[len(ss[i]&ss[j]) for i in range(5) for j in range(i+1,5)]
 return {'max_hits':max(hits),'any2':int(max(hits)>=2),'any3':int(max(hits)>=3),'any4':int(max(hits)>=4),'any5':int(max(hits)>=5),'any6':int(max(hits)>=6),'winning_union_coverage':len(u&actual),'union_size':len(u),'mean_overlap':statistics.mean(ovs),'max_overlap':max(ovs)}
def util(m):return m['max_hits']+1.5*m['any2']+3.0*m['any3']+6.0*m['any4']+.08*m['winning_union_coverage']
def permuted(lines,rng):
 labs=list(range(1,46));sh=labs[:];rng.shuffle(sh);mp=dict(zip(labs,sh));return [tuple(sorted(mp[n] for n in row)) for row in lines]
def regime_features(draws,idx,freq,last,preds):
 sets=[set(preds[m]) for m in MODELS];ovs=[len(sets[i]&sets[j])/6 for i in range(len(sets)) for j in range(i+1,len(sets))]
 votes=[sum(n in s for s in sets) for n in range(1,46)];union=len(set().union(*sets))/45
 fr=[float(x) for x in freq];gp=[float(draws[idx-1]['round']-last[i]) for i in range(45)]
 fcv=statistics.pstdev(fr)/(statistics.mean(fr)+1e-9);gcv=statistics.pstdev(gp)/(statistics.mean(gp)+1e-9)
 prev=draws[idx-1]['nums'];odd=sum(n%2 for n in prev)/6;low=sum(n<=22 for n in prev)/6;cons=sum(b-a==1 for a,b in zip(prev,prev[1:]))/5
 # bounded / roughly standardized context values
 return [1.0,statistics.mean(ovs),max(votes)/11,union,min(2.0,fcv),min(2.0,gcv),odd,low,cons]
def dot(a,b):return sum(x*y for x,y in zip(a,b))
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
 draws=load_draws();b=imp(B_SOURCE,'bv15');ac=imp(AC_SOURCE,'acv15');bank=b.feature_structure_bank(b.make_structure_bank());freq=[0]*45;last=[0]*45;pc=Counter();tc=Counter();profiles=[Counter() for _ in range(6)]
 for d in draws[:200]:
  for x in d['nums']:freq[x-1]+=1;last[x-1]=d['round']
  pc.update(itertools.combinations(d['nums'],2));tc.update(itertools.combinations(d['nums'],3));pr=b.structure_profile(d['nums'],None)
  for i,v in enumerate(pr[:5]):profiles[i][v]+=1
 for i in range(1,200):profiles[5][b.structure_profile(draws[i]['nums'],draws[i-1]['nums'])[5]]+=1
 nf=9;theta={p:[0.0]*nf for p in POLICIES};counts=Counter();obs=[];null=[];diffs={k:[] for k in ('max_hits','any2','any3','winning_union_coverage')};current=None;step=0
 for idx in range(200,len(draws)+1):
  hist=[x['nums'] for x in draws[:idx]];preds={**b.predictions_for_round(draws,idx,freq,last,pc,tc,profiles,bank),**ac.predict(hist)};x=regime_features(draws,idx,freq,last,preds);ports={p:make_policy(preds,o) for p,o in POLICIES.items()};pred_util={p:dot(theta[p],x) for p in POLICIES};chosen=max(POLICIES,key=lambda p:(pred_util[p],-list(POLICIES).index(p)));lines=ports[chosen]
  if idx==len(draws):current={'policy':chosen,'predicted_excess_utility':pred_util,'context':x,'lines':[list(t) for t in lines],'theta':theta};break
  actual=set(draws[idx]['nums']);target=idx+1
  if target>=401:
   counts[chosen]+=1;om=metrics(lines,actual);om['target']=target;obs.append(om);rng=random.Random(SEED+target);sm=[metrics(permuted(lines,rng),actual) for _ in range(TEST_NULL)];nm={k:statistics.mean(float(q[k]) for q in sm) for k in sm[0]};nm['target']=target;null.append(nm)
   for k in diffs:diffs[k].append(float(om[k])-nm[k])
  # full-information update: after outcome, train every policy on its own matched-null excess utility
  for pi,(p,port) in enumerate(ports.items()):
   real=util(metrics(port,actual));rng=random.Random(SEED+900000+target*31+pi);baseline=statistics.mean(util(metrics(permuted(port,rng),actual)) for _ in range(TRAIN_NULL));y=real-baseline;pred=dot(theta[p],x);lr=ETA/math.sqrt(1+step/300)
   for j in range(nf):theta[p][j]-=lr*((pred-y)*x[j]+L2*theta[p][j])
  step+=1;d=draws[idx]
  for n in d['nums']:freq[n-1]+=1;last[n-1]=d['round']
  pc.update(itertools.combinations(d['nums'],2));tc.update(itertools.combinations(d['nums'],3));pr=b.structure_profile(d['nums'],draws[idx-1]['nums'])
  for i,v in enumerate(pr):profiles[i][v]+=1
 keys=['max_hits','any2','any3','any4','any5','any6','winning_union_coverage','union_size','mean_overlap','max_overlap'];score={'policy':{k:avg(obs,k) for k in keys},'matched_label_permutation':{k:avg(null,k) for k in keys}};score['delta']={k:score['policy'][k]-score['matched_label_permutation'][k] for k in keys};alpha=.05/4;inf={}
 for j,k in enumerate(diffs):inf[k]={'adjusted_ci_delta':ci(diffs[k],alpha,SEED+2000+j),'positive_50_round_block_share':posshare(diffs[k])}
 inf['strict_portfolio_pass']=(inf['max_hits']['adjusted_ci_delta'][0]>0 and inf['any2']['adjusted_ci_delta'][0]>0 and inf['any3']['adjusted_ci_delta'][0]>0 and inf['any2']['positive_50_round_block_share']>=.65)
 payload={'created_kst':datetime.now(KST).isoformat(),'target_round':1247,'data_cutoff':1246,'policy':'FULL_INFORMATION_CONTEXTUAL_REGIME_SELECTOR_V15','no_future_leakage':True,'candidate_policies':POLICIES,'context_features':['intercept','mean_model_overlap','max_vote_share','model_union_share','freq_cv','gap_cv','prev_odd_share','prev_low_share','prev_consecutive_share'],'note':'At target t, regime selector uses parameters updated only through outcomes <t. Every policy is trained after each realized target on matched-permutation excess utility; strict outer gate/comparator unchanged.','policy_use_counts':dict(counts),'current':current,'walkforward_targets':len(obs),'scorecard':score,'inference':inf,'final_status':'STRICT_PASS' if inf['strict_portfolio_pass'] else 'FAIL_SAME_GATE'};OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':'PASS','strict_pass':inf['strict_portfolio_pass'],'scorecard':score,'inference':inf,'current':current,'policy_use_counts':dict(counts)},ensure_ascii=False))
if __name__=='__main__':main()
