#!/usr/bin/env python3
from __future__ import annotations
import itertools,json,random,statistics,math
from collections import Counter
from datetime import datetime,timezone,timedelta
from pathlib import Path
import importlib.util

ROOT=Path(__file__).resolve().parents[1]
V31_SOURCE=ROOT/'automation/today_crosshybrid_v31.py';B_SOURCE=ROOT/'research/1245_final_pipeline_v3/recovered_original_assets/b_model_backtest.py';AC_SOURCE=ROOT/'automation/recovered_models_v2.py';V12_SOURCE=ROOT/'automation/today_raw_signal_meta_v12.py';V18_SOURCE=ROOT/'automation/today_interaction_adagrad_v18.py'
OUT=ROOT/'analysis/2026-10-30/TODAY_ASSOCIATION_CLUSTER_1248_V35.json';KST=timezone(timedelta(hours=9));TEST_NULL=240;BLOCK=50;BOOT=7000;SEED=202610301100;LR=.035;L2=.0025
CFG={'slow':(1.0,1.0),'medium':(.9995,.999),'fast':(.9975,.992)}
def imp(p,n):s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def affinity(b,nums,n,freq,pc,tc):
 s=0.0
 for a,c in itertools.combinations(nums,2):s += .35*b.pair_z(a-1,c-1,n,freq,pc)
 for a,c,d in itertools.combinations(nums,3):s += b.triple_z(a-1,c-1,d-1,n,freq,tc)
 return s

def cluster_tail(b,tail,n,freq,pc,tc):
 rem=set(tail);rows=[]
 for li in range(4):
  if li==3:
   row=tuple(sorted(rem));assert len(row)==6;rows.append(row);break
  # seed with strongest historical triple among remaining labels
  seed=max(itertools.combinations(sorted(rem),3),key=lambda q:(b.triple_z(q[0]-1,q[1]-1,q[2]-1,n,freq,tc),tuple(-x for x in q)))
  cur=list(seed)
  while len(cur)<6:
   cand=[x for x in rem if x not in cur]
   x=max(cand,key=lambda x:(affinity(b,cur+[x],n,freq,pc,tc)-affinity(b,cur,n,freq,pc,tc),-x))
   cur.append(x)
  row=tuple(sorted(cur));rows.append(row);rem-=set(row)
 assert len(rows)==4 and len(set().union(*map(set,rows)))==24
 return rows

def met(L,a):
 h=[len(set(x)&a) for x in L];u=set().union(*map(set,L));return {'max_hits':max(h),'any2':int(max(h)>=2),'any3':int(max(h)>=3),'any4':int(max(h)>=4),'winning_union_coverage':len(u&a),'union_size':len(u)}
def perm(L,rng):
 labs=list(range(1,46));sh=labs[:];rng.shuffle(sh);mp=dict(zip(labs,sh));return [tuple(sorted(mp[n] for n in x)) for x in L]
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
 OUT.parent.mkdir(parents=True,exist_ok=True);base=imp(V31_SOURCE,'v31base35');draws=base.load();b=imp(B_SOURCE,'bv35');ac=imp(AC_SOURCE,'acv35');v12=imp(V12_SOURCE,'v12v35');v18=imp(V18_SOURCE,'v18v35');bank=b.feature_structure_bank(b.make_structure_bank());freq=[0]*45;last=[0]*45;pc=Counter();tc=Counter();prof=[Counter() for _ in range(6)]
 for d in draws[:200]:
  for x in d['nums']:freq[x-1]+=1;last[x-1]=d['round']
  pc.update(itertools.combinations(d['nums'],2));tc.update(itertools.combinations(d['nums'],3));p=b.structure_profile(d['nums'],None)
  for i,v in enumerate(p[:5]):prof[i][v]+=1
 for i in range(1,200):prof[5][b.structure_profile(draws[i]['nums'],draws[i-1]['nums'])[5]]+=1
 p0=6/45;dim_old=len(v18.feature_names());dummyX=[0.0]*23;dim_mw=len(base.design_mw(v18,dummyX,[0.0]*6));old={k:{'w':[math.log(p0/(1-p0))]+[0.0]*(dim_old-1),'g2':[0.0]*dim_old} for k in CFG};mw={k:{'w':[math.log(p0/(1-p0))]+[0.0]*(dim_mw-1),'g2':[0.0]*dim_mw} for k in CFG};obs=[];nul=[];diff={k:[] for k in ('max_hits','any2','any3','winning_union_coverage')};current=None
 for idx in range(200,len(draws)+1):
  preds={**b.predictions_for_round(draws,idx,freq,last,pc,tc,prof,bank),**ac.predict([q['nums'] for q in draws[:idx]])};X=v12.raw_features(draws,idx,freq,last,pc,tc,preds);E=base.extras(draws,idx,freq);os={k:base.predict_old(v18,X,s['w']) for k,s in old.items()};oz={k:base.zscore(v) for k,v in os.items()};oldblend={num:sum(oz[k][num] for k in CFG)/len(CFG) for num in range(1,46)};ms={k:base.predict_mw(v18,X,E,s['w']) for k,s in mw.items()};core=sorted(range(1,46),key=lambda num:(-ms['slow'][num],num))[:6];tail=sorted((num for num in range(1,46) if num not in core),key=lambda num:(-oldblend[num],num))[:24];rank30=core+tail;tail_lines=cluster_tail(b,tail,idx,freq,pc,tc);L=[tuple(sorted(core))]+tail_lines
  if idx==len(draws):current={'lines':[list(x) for x in L],'multiwindow_core':core,'oldtail_top30':rank30,'tail_affinities':[affinity(b,list(x),idx,freq,pc,tc) for x in tail_lines],'union_size':len(set().union(*map(set,L)))};break
  actual=set(draws[idx]['nums']);target=idx+1
  if target>=401:
   om=met(L,actual);obs.append(om);rng=random.Random(SEED+target);sm=[met(perm(L,rng),actual) for _ in range(TEST_NULL)];nm={k:statistics.mean(float(q[k]) for q in sm) for k in sm[0]};nul.append(nm)
   for k in diff:diff[k].append(float(om[k])-nm[k])
  for k,(sh,gd) in CFG.items():old[k]['w'],old[k]['g2']=base.update_generic(v18,X,E,old[k]['w'],old[k]['g2'],actual,sh,gd,False);mw[k]['w'],mw[k]['g2']=base.update_generic(v18,X,E,mw[k]['w'],mw[k]['g2'],actual,sh,gd,True)
  d=draws[idx]
  for x in d['nums']:freq[x-1]+=1;last[x-1]=d['round']
  pc.update(itertools.combinations(d['nums'],2));tc.update(itertools.combinations(d['nums'],3));p=b.structure_profile(d['nums'],draws[idx-1]['nums'])
  for i,v in enumerate(p):prof[i][v]+=1
 keys=['max_hits','any2','any3','any4','winning_union_coverage','union_size'];score={'policy':{k:avg(obs,k) for k in keys},'matched_label_permutation':{k:avg(nul,k) for k in keys}};score['delta']={k:score['policy'][k]-score['matched_label_permutation'][k] for k in keys};alpha=.05/4;inf={}
 for j,k in enumerate(diff):
  s,bk=share(diff[k]);inf[k]={'adjusted_ci_delta':ci(diff[k],alpha,SEED+50+j),'positive_50_round_block_share':s,'block_deltas':bk}
 inf['strict_portfolio_pass']=inf['max_hits']['adjusted_ci_delta'][0]>0 and inf['any2']['adjusted_ci_delta'][0]>0 and inf['any3']['adjusted_ci_delta'][0]>0 and inf['any2']['positive_50_round_block_share']>=.65
 payload={'created_kst':datetime.now(KST).isoformat(),'target_round':1248,'data_cutoff':1247,'policy':'V31_RANK_ASSOCIATION_CLUSTER_V35','no_future_leakage':True,'selection_rule':'Keep V31 top6 multiwindow core as line1 and V31 old-feature blended ranks7-30 as tail pool. Partition the 24 tail numbers into four disjoint lines by deterministic past-only pair/triple association affinity (strongest triple seed, greedy affinity extension). Strict outer gate/comparator unchanged.','current':current,'walkforward_targets':len(obs),'scorecard':score,'inference':inf,'final_status':'STRICT_PASS' if inf['strict_portfolio_pass'] else 'FAIL_SAME_GATE'};OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'strict_pass':inf['strict_portfolio_pass'],'scorecard':score,'current':current,'inference':{k:{'adjusted_ci_delta':v['adjusted_ci_delta'],'positive_50_round_block_share':v['positive_50_round_block_share']} for k,v in inf.items() if isinstance(v,dict)}},ensure_ascii=False))
if __name__=='__main__':main()
