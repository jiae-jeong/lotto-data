#!/usr/bin/env python3
from __future__ import annotations
import csv,importlib.util,itertools,json,random,statistics,math
from collections import Counter
from datetime import datetime,timezone,timedelta
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'lotto_data.csv';B_SOURCE=ROOT/'research/1245_final_pipeline_v3/recovered_original_assets/b_model_backtest.py'
OUT=ROOT/'analysis/2026-10-30/TODAY_DIRECT_ASSOCIATION_1248_V36.json';KST=timezone(timedelta(hours=9));TEST_NULL=240;BLOCK=50;BOOT=7000;SEED=202610301130

def imp(p,n):s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def load():
 o=[]
 with DATA.open(encoding='utf-8-sig') as f:
  for r in csv.DictReader(f):o.append({'round':int(r['round']),'nums':tuple(sorted(int(r[f'no{i}']) for i in range(1,7)))})
 assert o[-1]['round']==1247 and [x['round'] for x in o]==list(range(1,1248));return o
def z(v):
 m=statistics.mean(v);s=statistics.pstdev(v) or 1.0;return [(x-m)/s for x in v]
def recent100(draws,idx):
 c=[0]*45
 for d in draws[max(0,idx-100):idx]:
  for n in d['nums']:c[n-1]+=1
 return z(c)
def line_aff(b,row,n,freq,pc,tc,r100):
 ps=sum(b.pair_z(a-1,c-1,n,freq,pc) for a,c in itertools.combinations(row,2))
 ts=sum(b.triple_z(a-1,c-1,d-1,n,freq,tc) for a,c,d in itertools.combinations(row,3))
 rs=sum(r100[x-1] for x in row)
 return ts+.30*ps+.18*rs
def portfolio(b,n,freq,pc,tc,r100):
 used=set();lines=[]
 triples=list(itertools.combinations(range(1,46),3))
 # fixed top-180 historical triple seeds gives diversity room without target tuning
 scored=sorted(triples,key=lambda q:(-(b.triple_z(q[0]-1,q[1]-1,q[2]-1,n,freq,tc)+.15*sum(r100[x-1] for x in q)),q))[:180]
 for _ in range(5):
  seed=next((q for q in scored if not (set(q)&used)),None)
  if seed is None:
   seed=max((q for q in triples if not(set(q)&used)),key=lambda q:(b.triple_z(q[0]-1,q[1]-1,q[2]-1,n,freq,tc)+.15*sum(r100[x-1] for x in q),tuple(-x for x in q)))
  row=list(seed)
  while len(row)<6:
   cand=[x for x in range(1,46) if x not in used and x not in row]
   x=max(cand,key=lambda x:(line_aff(b,row+[x],n,freq,pc,tc,r100)-line_aff(b,row,n,freq,pc,tc,r100),-x))
   row.append(x)
  row=tuple(sorted(row));lines.append(row);used|=set(row)
 assert len(lines)==5 and len(used)==30 and len(set(lines))==5
 return lines
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
 OUT.parent.mkdir(parents=True,exist_ok=True);draws=load();b=imp(B_SOURCE,'bv36');freq=[0]*45;pc=Counter();tc=Counter()
 for d in draws[:200]:
  for x in d['nums']:freq[x-1]+=1
  pc.update(itertools.combinations(d['nums'],2));tc.update(itertools.combinations(d['nums'],3))
 obs=[];nul=[];diff={k:[] for k in ('max_hits','any2','any3','winning_union_coverage')};current=None
 for idx in range(200,len(draws)+1):
  r100=recent100(draws,idx);L=portfolio(b,idx,freq,pc,tc,r100)
  if idx==len(draws):current={'lines':[list(x) for x in L],'union_size':30,'line_affinities':[line_aff(b,list(x),idx,freq,pc,tc,r100) for x in L]};break
  actual=set(draws[idx]['nums']);target=idx+1
  if target>=401:
   om=met(L,actual);obs.append(om);rng=random.Random(SEED+target);sm=[met(perm(L,rng),actual) for _ in range(TEST_NULL)];nm={k:statistics.mean(float(q[k]) for q in sm) for k in sm[0]};nul.append(nm)
   for k in diff:diff[k].append(float(om[k])-nm[k])
  d=draws[idx]
  for x in d['nums']:freq[x-1]+=1
  pc.update(itertools.combinations(d['nums'],2));tc.update(itertools.combinations(d['nums'],3))
 keys=['max_hits','any2','any3','any4','winning_union_coverage','union_size'];score={'policy':{k:avg(obs,k) for k in keys},'matched_label_permutation':{k:avg(nul,k) for k in keys}};score['delta']={k:score['policy'][k]-score['matched_label_permutation'][k] for k in keys};alpha=.05/4;inf={}
 for j,k in enumerate(diff):
  s,bk=share(diff[k]);inf[k]={'adjusted_ci_delta':ci(diff[k],alpha,SEED+50+j),'positive_50_round_block_share':s,'block_deltas':bk}
 inf['strict_portfolio_pass']=inf['max_hits']['adjusted_ci_delta'][0]>0 and inf['any2']['adjusted_ci_delta'][0]>0 and inf['any3']['adjusted_ci_delta'][0]>0 and inf['any2']['positive_50_round_block_share']>=.65
 payload={'created_kst':datetime.now(KST).isoformat(),'target_round':1248,'data_cutoff':1247,'policy':'DIRECT_TRIPLE_PAIR_RECENT100_V36','no_future_leakage':True,'selection_rule':'Five disjoint tickets built directly from prior-only triple association seeds, greedy triple/pair affinity extension, and small recent100 weighting. No V18/V30 ranking is used. Fixed coefficients and seed-pool size declared before evaluation. Strict outer gate/comparator unchanged.','current':current,'walkforward_targets':len(obs),'scorecard':score,'inference':inf,'final_status':'STRICT_PASS' if inf['strict_portfolio_pass'] else 'FAIL_SAME_GATE'};OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'strict_pass':inf['strict_portfolio_pass'],'scorecard':score,'current':current,'inference':{k:{'adjusted_ci_delta':v['adjusted_ci_delta'],'positive_50_round_block_share':v['positive_50_round_block_share']} for k,v in inf.items() if isinstance(v,dict)}},ensure_ascii=False))
if __name__=='__main__':main()
