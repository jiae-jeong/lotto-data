#!/usr/bin/env python3
from __future__ import annotations
import csv,importlib.util,itertools,json,math,random,statistics,hashlib
from collections import Counter,deque
from datetime import datetime,timezone,timedelta
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'lotto_data.csv';B_SOURCE=ROOT/'research/1245_final_pipeline_v3/recovered_original_assets/b_model_backtest.py';AC_SOURCE=ROOT/'automation/recovered_models_v2.py'
OUT=ROOT/'analysis/2026-10-23/TODAY_PURCHASE_PORTFOLIO_1247_V6.json';FREEZE=ROOT/'research/weekly_purchase/1247/FINAL_FIVE_LINES_1247_20261023_V6.json'
KST=timezone(timedelta(hours=9));B_NAMES=('long_frequency','current_gap','frequency_plus_gap','recent_momentum','structure_profile','pair_association','triple_association','combined_equal_rank');AC_NAMES=('A_v2','C_v2','contrarian_v2');MODELS=B_NAMES+AC_NAMES
ETA=.30;DECAY=.99;CAP=.35;OVERLAP_PENALTY=.12;RANDOM_PER_TARGET=200;SEED=202610231400

def imp(p,n):s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def load():
 o=[]
 with DATA.open(encoding='utf-8-sig') as f:
  for r in csv.DictReader(f):o.append({'round':int(r['round']),'date':r['date'],'nums':tuple(sorted(int(r[f'no{i}']) for i in range(1,7)))})
 assert o[-1]['round']==1246 and [x['round'] for x in o]==list(range(1,1247));return o
def capw(perf):
 mx=max(perf.values());raw={m:math.exp(ETA*(v-mx)) for m,v in perf.items()};z=sum(raw.values());w={m:raw[m]/z for m in raw};free=set(w);fixed={};rem=1.0
 while True:
  den=sum(w[x] for x in free);over=[m for m in free if rem*w[m]/den>CAP]
  if not over:break
  for m in over:fixed[m]=CAP;free.remove(m);rem-=CAP
  if not free:break
 if free:
  den=sum(w[m] for m in free)
  for m in free:fixed[m]=rem*w[m]/den
 return fixed
def anchor(preds,perf):
 w=capw(perf);sc={n:sum(w[m] for m in MODELS if n in preds[m]) for n in range(1,46)};pool=sorted(range(1,46),key=lambda n:(-sc[n],n))[:14];best=None
 for t in itertools.combinations(pool,6):
  odd=sum(n%2 for n in t);low=sum(n<=22 for n in t);bands=len({(n-1)//10 for n in t});val=sum(sc[n] for n in t)-.035*abs(odd-3)-.03*abs(low-3)+.006*bands
  if best is None or val>best[0] or (val==best[0] and t<best[1]):best=(val,t)
 return tuple(sorted(best[1])),w
def select_portfolio(anchor_ticket,preds,expert_hist):
 chosen=[('V3_anchor',anchor_ticket,0.0)];used={anchor_ticket};cand=[]
 for m in MODELS:
  hs=list(expert_hist[m]);score=(sum(hs[-200:])+75*.8)/(min(200,len(hs))+75) if hs else .8;cand.append((m,tuple(preds[m]),score))
 while len(chosen)<5:
  pick=None
  for x in cand:
   if x[1] in used:continue
   overlap=sum(len(set(x[1])&set(y[1])) for y in chosen);load=sum(max(0,sum(n in y[1] for y in chosen)) for n in x[1]);obj=x[2]-OVERLAP_PENALTY*overlap-.02*load
   if pick is None or obj>pick[0] or (obj==pick[0] and x[0]<pick[1][0]):pick=(obj,x)
  if pick is None:raise RuntimeError('not enough distinct tickets')
  chosen.append(pick[1]);used.add(pick[1]);cand=[x for x in cand if x[0]!=pick[1][0]]
 return chosen
def metrics(lines,actual):
 ss=[set(x) for x in lines];hits=[len(s&actual) for s in ss];u=set().union(*ss);ovs=[len(ss[i]&ss[j]) for i in range(5) for j in range(i+1,5)]
 return {'max_hits':max(hits),'any2':int(max(hits)>=2),'any3':int(max(hits)>=3),'any4':int(max(hits)>=4),'any5':int(max(hits)>=5),'any6':int(max(hits)>=6),'winning_union_coverage':len(u&actual),'union_size':len(u),'mean_overlap':statistics.mean(ovs),'max_overlap':max(ovs)}
def random_union_matched(union_size,rng):
 U=rng.sample(range(1,46),union_size);rng.shuffle(U);lines=[[] for _ in range(5)]
 # ensure every union number appears at least once while respecting six slots/ticket
 for i,n in enumerate(U):lines[i%5].append(n)
 for i in range(5):
  while len(lines[i])<6:
   n=rng.choice(U)
   if n not in lines[i]:lines[i].append(n)
  lines[i].sort()
 assert len(set().union(*map(set,lines)))==union_size
 return lines
def avg(rows,k):return statistics.mean(float(x[k]) for x in rows)
def validate(lines):return len(lines)==5 and len({tuple(x) for x in lines})==5 and all(len(x)==6 and x==sorted(x) and len(set(x))==6 and all(1<=n<=45 for n in x) for x in lines)
def main():
 draws=load();b=imp(B_SOURCE,'bv6');ac=imp(AC_SOURCE,'acv6');bank=b.feature_structure_bank(b.make_structure_bank());freq=[0]*45;last=[0]*45;pc=Counter();tc=Counter();prof=[Counter() for _ in range(6)]
 for d in draws[:200]:
  for x in d['nums']:freq[x-1]+=1;last[x-1]=d['round']
  pc.update(itertools.combinations(d['nums'],2));tc.update(itertools.combinations(d['nums'],3));p=b.structure_profile(d['nums'],None)
  for i,v in enumerate(p[:5]):prof[i][v]+=1
 for i in range(1,200):prof[5][b.structure_profile(draws[i]['nums'],draws[i-1]['nums'])[5]]+=1
 perf={m:0.0 for m in MODELS};eh={m:deque(maxlen=200) for m in MODELS};policy=[];rand=[];current=None;current_sources=None;current_weights=None
 for idx in range(200,len(draws)+1):
  preds={**b.predictions_for_round(draws,idx,freq,last,pc,tc,prof,bank),**ac.predict([x['nums'] for x in draws[:idx]])};a,w=anchor(preds,perf);sel=select_portfolio(a,preds,eh);lines=[x[1] for x in sel];assert validate(lines)
  if idx==len(draws):current=lines;current_sources=[x[0] for x in sel];current_weights=w;break
  actual=set(draws[idx]['nums']);target=idx+1
  if target>=401:
   pm=metrics(lines,actual);pm['target']=target;policy.append(pm);rng=random.Random(SEED+target)
   for _ in range(RANDOM_PER_TARGET):
    rm=metrics(random_union_matched(pm['union_size'],rng),actual);rm['target']=target;rand.append(rm)
  for m in MODELS:
   h=len(set(preds[m])&actual);eh[m].append(h);perf[m]=DECAY*perf[m]+(h-.8)
  d=draws[idx]
  for x in d['nums']:freq[x-1]+=1;last[x-1]=d['round']
  pc.update(itertools.combinations(d['nums'],2));tc.update(itertools.combinations(d['nums'],3));p=b.structure_profile(d['nums'],draws[idx-1]['nums'])
  for i,v in enumerate(p):prof[i][v]+=1
 keys=['max_hits','any2','any3','any4','any5','any6','winning_union_coverage','union_size','mean_overlap','max_overlap'];ps={k:avg(policy,k) for k in keys};rs={k:avg(rand,k) for k in keys};delta={k:ps[k]-rs[k] for k in keys}
 assert validate(current);v1='PASS';assert validate(current);v2='PASS';text='\n'.join(' '.join(map(str,x)) for x in current);parsed=[[int(y) for y in x.split()] for x in text.splitlines()];assert parsed==current and validate(parsed)
 payload={'created_kst':datetime.now(KST).isoformat(),'target_round':1247,'data_cutoff':1246,'policy':'V3_ANCHORED_DIVERSIFIED_PURCHASE_V6','model_anchor':'e0.3_d0.99_c0.35','model_anchor_validation_note':'V3 improved over random point estimates but did not pass adjusted significance/stability gate; V6 therefore evaluates the full purchase portfolio separately and does not claim predictive superiority unless supported by matched comparison.','walkforward_targets':len(policy),'random_bundles_per_target':RANDOM_PER_TARGET,'matched_random':'union_size_matched','portfolio_scorecard':{'policy':ps,'matched_random':rs,'delta':delta},'sources':current_sources,'final_lines':current,'anchor_weights':current_weights,'integrity':{'validator_1':v1,'validator_2':v2,'final_text_parse':'PASS','stored_vs_display':'PENDING'},'classification':'ACTUAL_PURCHASE_POLICY_BEST_AVAILABLE_NOT_STATISTICALLY_VALIDATED_MODEL'}
 canon=json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode();payload['sha256']=hashlib.sha256(canon).hexdigest();OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
 if FREEZE.exists():raise SystemExit(f'write-once violation {FREEZE}')
 FREEZE.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n');stored=json.loads(FREEZE.read_text());assert stored['final_lines']==current and validate(stored['final_lines']);payload['integrity']['stored_vs_display']='PASS';OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n');FREEZE.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'status':'PASS','target':1247,'cutoff':1246,'policy_scorecard':ps,'matched_random':rs,'delta':delta,'sources':current_sources,'final_lines':current,'validator_1':'PASS','validator_2':'PASS','final_text_parse':'PASS','stored_vs_display':'PASS','freeze':str(FREEZE)},ensure_ascii=False))
if __name__=='__main__':main()
