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
OUT=ROOT/'analysis/2026-10-23/TODAY_HYBRID_SOURCE_PORTFOLIO_1247_V13.json'
KST=timezone(timedelta(hours=9))
B_NAMES=('long_frequency','current_gap','frequency_plus_gap','recent_momentum','structure_profile','pair_association','triple_association','combined_equal_rank')
AC_NAMES=('A_v2','C_v2','contrarian_v2')
MODELS=B_NAMES+AC_NAMES
RAW_NAMES=tuple(f'raw_rank{i}' for i in range(1,6))
SOURCES=tuple(f'expert:{m}' for m in MODELS)+tuple(f'raw:{r}' for r in RAW_NAMES)
ROLL=200
BASE_MEAN=.8
BASE_GE2=.17530810086113546
BASE_GE3=.023834078609221467
RANDOM_PER_TARGET=160;BLOCK=50;BOOT=5000;SEED=202610240100

def imp(path,name):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def load_draws():
 out=[]
 with DATA.open(encoding='utf-8-sig') as f:
  for r in csv.DictReader(f):out.append({'round':int(r['round']),'date':r['date'],'nums':tuple(sorted(int(r[f'no{i}']) for i in range(1,7)))})
 assert out[-1]['round']==1246 and [x['round'] for x in out]==list(range(1,1247));return out

def source_score(hist):
 hs=list(hist)[-ROLL:];n=len(hs)
 mean=(sum(hs)+100*BASE_MEAN)/(n+100)
 ge2=(sum(h>=2 for h in hs)+100*BASE_GE2)/(n+100)
 ge3=(sum(h>=3 for h in hs)+100*BASE_GE3)/(n+100)
 recent=statistics.mean(hs[-50:]) if hs else BASE_MEAN
 return (mean-BASE_MEAN)+.70*(ge2-BASE_GE2)+1.40*(ge3-BASE_GE3)+.15*(recent-BASE_MEAN)

def select(candidates,hists):
 chosen=[];used=set();details=[]
 while len(chosen)<5:
  best=None
  for src,t in candidates.items():
   tt=tuple(t)
   if src in [x[0] for x in chosen] or tt in used:continue
   base=source_score(hists[src]);ovs=[len(set(tt)&set(x[1])) for x in chosen]
   # V12 failed by over-concentration. Penalize only overlap beyond two shared numbers.
   pen=.030*sum(max(0,o-2) for o in ovs)+.015*max(0,(max(ovs) if ovs else 0)-3)
   obj=base-pen
   key=(obj,base,-SOURCES.index(src))
   if best is None or key>best[0]:best=(key,src,tt,base,pen)
  if best is None:raise RuntimeError('not enough distinct hybrid candidates')
  _,src,tt,base,pen=best;chosen.append((src,tt));used.add(tt);details.append({'source':src,'prior_score':base,'diversity_penalty':pen,'ticket':list(tt)})
 return chosen,details

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
 draws=load_draws();b=imp(B_SOURCE,'bv13');ac=imp(AC_SOURCE,'acv13');v12=imp(V12_SOURCE,'v12mod');bank=b.feature_structure_bank(b.make_structure_bank())
 freq=[0]*45;last=[0]*45;pc=Counter();tc=Counter();profiles=[Counter() for _ in range(6)]
 for d in draws[:200]:
  for x in d['nums']:freq[x-1]+=1;last[x-1]=d['round']
  pc.update(itertools.combinations(d['nums'],2));tc.update(itertools.combinations(d['nums'],3));pr=b.structure_profile(d['nums'],None)
  for i,v in enumerate(pr[:5]):profiles[i][v]+=1
 for i in range(1,200):profiles[5][b.structure_profile(draws[i]['nums'],draws[i-1]['nums'])[5]]+=1
 nfeat=1+len(MODELS)+11;p0=6/45;w=[math.log(p0/(1-p0))]+[0.0]*(nfeat-1);hists={s:deque(maxlen=ROLL) for s in SOURCES};obs=[];null=[];diffs={k:[] for k in ('max_hits','any2','any3','winning_union_coverage')};current=None;source_use=Counter();step=0
 for idx in range(200,len(draws)+1):
  hist=[x['nums'] for x in draws[:idx]];preds={**b.predictions_for_round(draws,idx,freq,last,pc,tc,profiles,bank),**ac.predict(hist)}
  X=v12.raw_features(draws,idx,freq,last,pc,tc,preds);sc=v12.score_all(X,w);raw_lines=v12.build(sc)
  candidates={f'expert:{m}':tuple(preds[m]) for m in MODELS}
  candidates.update({f'raw:{RAW_NAMES[i]}':tuple(raw_lines[i]) for i in range(5)})
  selected,details=select(candidates,hists);lines=[x[1] for x in selected]
  if idx==len(draws):
   current={'sources':[x[0] for x in selected],'lines':[list(x) for x in lines],'selection_details':details,'raw_weights':w};break
  actual=set(draws[idx]['nums']);target=idx+1
  if target>=401:
   for s,_ in selected:source_use[s]+=1
   om=metrics(lines,actual);om['target']=target;obs.append(om);rng=random.Random(SEED+target);samples=[metrics(permuted(lines,rng),actual) for _ in range(RANDOM_PER_TARGET)];nm={k:statistics.mean(float(x[k]) for x in samples) for k in samples[0]};nm['target']=target;null.append(nm)
   for k in diffs:diffs[k].append(float(om[k])-nm[k])
  # Update every candidate source after the target resolves, so next target sees only past performance.
  for src,t in candidates.items():hists[src].append(len(set(t)&actual))
  w=v12.update(w,X,actual,step);step+=1
  d=draws[idx]
  for x in d['nums']:freq[x-1]+=1;last[x-1]=d['round']
  pc.update(itertools.combinations(d['nums'],2));tc.update(itertools.combinations(d['nums'],3));pr=b.structure_profile(d['nums'],draws[idx-1]['nums'])
  for i,v in enumerate(pr):profiles[i][v]+=1
 keys=['max_hits','any2','any3','any4','any5','any6','winning_union_coverage','union_size','mean_overlap','max_overlap'];score={'policy':{k:avg(obs,k) for k in keys},'matched_label_permutation':{k:avg(null,k) for k in keys}};score['delta']={k:score['policy'][k]-score['matched_label_permutation'][k] for k in keys};alpha=.05/4;inf={}
 for j,k in enumerate(diffs):inf[k]={'adjusted_ci_delta':ci(diffs[k],alpha,SEED+4000+j),'positive_50_round_block_share':posshare(diffs[k])}
 inf['strict_portfolio_pass']=(inf['max_hits']['adjusted_ci_delta'][0]>0 and inf['any2']['adjusted_ci_delta'][0]>0 and inf['any3']['adjusted_ci_delta'][0]>0 and inf['any2']['positive_50_round_block_share']>=.65)
 payload={'created_kst':datetime.now(KST).isoformat(),'target_round':1247,'data_cutoff':1246,'policy':'HYBRID_RAW_META_PLUS_EXPERT_SOURCES_V13','no_future_leakage':True,'selection':'16 candidate sources = 11 expert model tickets + five ordered V12 raw-meta tickets; trailing source performance plus current overlap penalty, all prior-only.','source_score_weights':{'mean':1.0,'ge2':.70,'ge3':1.40,'recent50_mean':.15},'current':current,'source_use_counts':dict(source_use),'walkforward_targets':len(obs),'scorecard':score,'inference':inf,'final_status':'STRICT_PASS' if inf['strict_portfolio_pass'] else 'FAIL_SAME_GATE'}
 OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':'PASS','strict_pass':inf['strict_portfolio_pass'],'scorecard':score,'inference':inf,'current':current,'source_use':dict(source_use)},ensure_ascii=False))
if __name__=='__main__':main()
