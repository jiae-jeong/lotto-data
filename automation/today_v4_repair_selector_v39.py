#!/usr/bin/env python3
from __future__ import annotations
import csv, importlib.util, itertools, json, random, statistics, math
from collections import Counter, deque
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'lotto_data.csv'
B_SOURCE=ROOT/'research/1245_final_pipeline_v3/recovered_original_assets/b_model_backtest.py'
AC_SOURCE=ROOT/'automation/recovered_models_v2.py'
V12_SOURCE=ROOT/'automation/today_raw_signal_meta_v12.py'
V18_SOURCE=ROOT/'automation/today_interaction_adagrad_v18.py'
OUT=ROOT/'analysis/2026-10-30/TODAY_V4_REPAIR_SELECTOR_1248_V39.json'
KST=timezone(timedelta(hours=9))
BLOCK=50; BOOT=7000; SEED=202610301430; ROLL=150; LR=.035; L2=.0025
CFG={'slow':(1.0,1.0),'medium':(.9995,.999),'fast':(.9975,.992)}
TEMPLATES={
 'rr':[[6,10,14,18,22,26],[7,11,15,19,23,27],[8,12,16,20,24,28],[9,13,17,21,25,29]],
 'contig':[[6,7,8,9,10,11],[12,13,14,15,16,17],[18,19,20,21,22,23],[24,25,26,27,28,29]],
 'snake':[[6,13,14,21,22,29],[7,12,15,20,23,28],[8,11,16,19,24,27],[9,10,17,18,25,26]],
 'paired':[[6,7,14,15,22,23],[8,9,16,17,24,25],[10,11,18,19,26,27],[12,13,20,21,28,29]]}
CANDIDATE_NAMES=('base','G1E','C1E','M1E','P1E','G1R','C1R','M1R','P1R','GC2E','GP2E','CM2E','GC2R','GP2R','CM2R','GCMP4E','GCMP4R')

def imp(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def load():
 o=[]
 with DATA.open(encoding='utf-8-sig') as f:
  for r in csv.DictReader(f):o.append({'round':int(r['round']),'nums':tuple(sorted(int(r[f'no{i}']) for i in range(1,7)))})
 assert o[-1]['round']==1247 and [x['round'] for x in o]==list(range(1,1248));return o

def update(v18,X,w,g2,actual,shrink,gdec):
 grad=[0.0]*len(w)
 for n in range(1,46):
  f=v18.design(X[n]);y=1.0 if n in actual else 0.0;p=v18.sigmoid(sum(a*b for a,b in zip(w,f)))
  for j,x in enumerate(f):grad[j]+=(p-y)*x
 for j in range(len(w)):
  if j>0:w[j]*=shrink
  gr=grad[j]/45.0+(0 if j==0 else L2*w[j]);g2[j]=gdec*g2[j]+gr*gr;w[j]-=LR*gr/math.sqrt(g2[j]+1e-8)
 return w,g2

def zscore(sc):
 vals=list(sc.values());m=statistics.mean(vals);s=statistics.pstdev(vals) or 1.0;return {n:(v-m)/s for n,v in sc.items()}
def ranked_hybrid(slow,blend):
 core=sorted(range(1,46),key=lambda n:(-slow[n],n))[:6]
 tail=sorted((n for n in range(1,46) if n not in core),key=lambda n:(-blend[n],n))[:24]
 return core+tail

def base_lines(r,t):
 out=[tuple(sorted(r[:6]))]+[tuple(sorted(r[j] for j in p)) for p in t]
 assert len(out)==5 and len(set(out))==5 and len(set().union(*map(set,out)))==30
 return out

def met(L,a):
 h=[len(set(x)&a) for x in L];u=set().union(*map(set,L));return {'max_hits':max(h),'any2':int(max(h)>=2),'any3':int(max(h)>=3),'any4':int(max(h)>=4),'winning_union_coverage':len(u&a),'union_size':len(u)}

def shape_key(L):
 counts=[0]*32;ss=[set(x) for x in L]
 for n in range(1,46):
  mask=0
  for i,q in enumerate(ss):
   if n in q:mask|=1<<i
  counts[mask]+=1
 return tuple(counts)
_EXACT={}
def exact_null(L):
 key=shape_key(L)
 if key in _EXACT:return _EXACT[key]
 dp={(0,0,0,0,0,0,0):1}
 for mask,c in enumerate(key):
  if not c:continue
  nd={}
  for state,ways in dp.items():
   k,*rest=state;hits=rest[:5];cov=rest[5]
   for j in range(min(c,6-k)+1):
    mult=math.comb(c,j);nh=[hits[i]+(j if mask&(1<<i) else 0) for i in range(5)];nc=cov+(j if mask else 0);ns=(k+j,*nh,nc);nd[ns]=nd.get(ns,0)+ways*mult
  dp=nd
 total=math.comb(45,6);acc={'max_hits':0.,'any2':0.,'any3':0.,'any4':0.,'winning_union_coverage':0.,'union_size':float(sum(key[1:]))}
 for state,ways in dp.items():
  if state[0]!=6:continue
  hits=state[1:6];cov=state[6];mx=max(hits);w=ways/total
  acc['max_hits']+=w*mx;acc['any2']+=w*(mx>=2);acc['any3']+=w*(mx>=3);acc['any4']+=w*(mx>=4);acc['winning_union_coverage']+=w*cov
 _EXACT[key]=acc;return acc

def agebin(age):return 0 if age==0 else 1 if age==1 else 2 if age==2 else 3 if age<=5 else 4 if age<=10 else 5
P0=6/45

def frozen_v4_scores(nums):
 n=len(nums);freq=Counter(x for q in nums for x in q)
 risk=Counter();hit=Counter();seen={x:None for x in range(1,46)}
 for i,q in enumerate(nums):
  if i:
   for x in range(1,46):
    if seen[x] is None:continue
    b=agebin(i-1-seen[x]);risk[b]+=1;hit[b]+=int(x in q)
  for x in q:seen[x]=i
 G={x:(hit[agebin(n-1-seen[x] if seen[x] is not None else n)]+20*P0)/(risk[agebin(n-1-seen[x] if seen[x] is not None else n)]+20) for x in range(1,46)}
 cr=Counter();ch=Counter();mr=Counter();mh=Counter()
 for i,q in enumerate(nums):
  if i>=10:
   c=Counter(x for old in nums[i-10:i] for x in old)
   for x in range(1,46):cr[c[x]]+=1;ch[c[x]]+=int(x in q)
  if i>=40:
   a=Counter(x for old in nums[i-40:i-20] for x in old);b=Counter(x for old in nums[i-20:i] for x in old)
   for x in range(1,46):state=(a[x]>20*P0,b[x]>20*P0);mr[state]+=1;mh[state]+=int(x in q)
 c=Counter(x for q in nums[-10:] for x in q);a=Counter(x for q in nums[-40:-20] for x in q);b=Counter(x for q in nums[-20:] for x in q)
 C={x:(ch[c[x]]+30*P0)/(cr[c[x]]+30) for x in range(1,46)}
 M={x:(mh[(a[x]>20*P0,b[x]>20*P0)]+20*P0)/(mr[(a[x]>20*P0,b[x]>20*P0)]+20) for x in range(1,46)}
 pc=Counter(p for q in nums for p in itertools.combinations(q,2));PS={x:0. for x in range(1,46)}
 for pair in itertools.combinations(range(1,46),2):
  x,y=pair;e=(5/6)*(45/44)*freq[x]*freq[y]/n;z=(pc[pair]-e)/math.sqrt(max(e,1e-12));PS[x]+=z;PS[y]+=z
 return {'G':G,'C':C,'M':M,'P':PS}

def ticket(sc):return tuple(sorted(sorted(range(1,46),key=lambda n:(-sc[n],n))[:6]))

def assemble(base,tix,code):
 if code=='base':return list(base)
 mode=code[-1];core=code[:-2] if code[-2].isdigit() else code[:-1]
 k=int(code[-2]) if code[-2].isdigit() else 1
 chosen=list(base[:5-k])
 for letter in core:
  q=tix[mode][letter]
  if q not in chosen:chosen.append(q)
 while len(chosen)<5:
  for q in base:
   if q not in chosen:chosen.append(q)
   if len(chosen)==5:break
 assert len(chosen)==5 and len(set(chosen))==5
 return chosen

def obj_delta(om,nm):
 return (om['max_hits']-nm['max_hits'])+.85*(om['any2']-nm['any2'])+1.35*(om['any3']-nm['any3'])+.10*(om['winning_union_coverage']-nm['winning_union_coverage'])
def robust(hist):
 if not hist:return -999.
 x=list(hist)[-ROLL:];m=statistics.mean(x);se=(statistics.pstdev(x)/math.sqrt(len(x))) if len(x)>1 else 0.;return m-.5*se

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
 OUT.parent.mkdir(parents=True,exist_ok=True);draws=load();b=imp(B_SOURCE,'bv39');ac=imp(AC_SOURCE,'acv39');v12=imp(V12_SOURCE,'v12v39');v18=imp(V18_SOURCE,'v18v39')
 bank=b.feature_structure_bank(b.make_structure_bank());freq=[0]*45;last=[0]*45;pc=Counter();tc=Counter();prof=[Counter() for _ in range(6)]
 for d in draws[:200]:
  for n in d['nums']:freq[n-1]+=1;last[n-1]=d['round']
  pc.update(itertools.combinations(d['nums'],2));tc.update(itertools.combinations(d['nums'],3));pr=b.structure_profile(d['nums'],None)
  for i,v in enumerate(pr[:5]):prof[i][v]+=1
 for i in range(1,200):prof[5][b.structure_profile(draws[i]['nums'],draws[i-1]['nums'])[5]]+=1
 dim=len(v18.feature_names());states={k:{'w':[math.log(P0/(1-P0))]+[0.0]*(dim-1),'g2':[0.0]*dim} for k in CFG};thist={k:deque(maxlen=ROLL) for k in TEMPLATES}
 cand_hist={k:deque(maxlen=ROLL) for k in CANDIDATE_NAMES};obs=[];nul=[];diff={k:[] for k in ('max_hits','any2','any3','winning_union_coverage')};select_count=Counter();template_count=Counter();current=None
 for idx in range(200,len(draws)+1):
  preds={**b.predictions_for_round(draws,idx,freq,last,pc,tc,prof,bank),**ac.predict([q['nums'] for q in draws[:idx]])};X=v12.raw_features(draws,idx,freq,last,pc,tc,preds)
  scores={k:v18.predict(X,s['w']) for k,s in states.items()};zs={k:zscore(v) for k,v in scores.items()};blend={n:sum(zs[k][n] for k in CFG)/len(CFG) for n in range(1,46)};r=ranked_hybrid(scores['slow'],blend)
  allbase={k:base_lines(r,p) for k,p in TEMPLATES.items()};chosen_t='rr' if idx<320 else max(TEMPLATES,key=lambda k:(statistics.mean(thist[k]) if thist[k] else -999,k));base=allbase[chosen_t]
  nums_all=[q['nums'] for q in draws[:idx]];svE=frozen_v4_scores(nums_all);svR=frozen_v4_scores(nums_all[-300:]);tix={'E':{k:ticket(v) for k,v in svE.items()},'R':{k:ticket(v) for k,v in svR.items()}}
  policies={name:assemble(base,tix,name) for name in CANDIDATE_NAMES}
  if idx<400:chosen='base'
  else:
   scoresel={name:robust(cand_hist[name]) for name in CANDIDATE_NAMES};best=max(CANDIDATE_NAMES,key=lambda n:(scoresel[n],n=='base',n));chosen=best if scoresel[best]>scoresel['base'] else 'base'
  L=policies[chosen]
  if idx==len(draws):
   current={'chosen_policy':chosen,'selector_scores':{k:robust(v) for k,v in cand_hist.items()},'chosen_template':chosen_t,'base_lines':[list(x) for x in base],'v4_tickets':{m:{k:list(v) for k,v in q.items()} for m,q in tix.items()},'lines':[list(x) for x in L],'union_size':len(set().union(*map(set,L)))};break
  actual=set(draws[idx]['nums']);target=idx+1
  for k,Q in allbase.items():
   om=met(Q,actual);nm=exact_null(Q);thist[k].append(obj_delta(om,nm))
  for name,Q in policies.items():
   om=met(Q,actual);nm=exact_null(Q);cand_hist[name].append(obj_delta(om,nm))
  if target>=401:
   select_count[chosen]+=1;template_count[chosen_t]+=1;om=met(L,actual);nm=exact_null(L);obs.append(om);nul.append(nm)
   for k in diff:diff[k].append(float(om[k])-nm[k])
  for k,(sh,gd) in CFG.items():states[k]['w'],states[k]['g2']=update(v18,X,states[k]['w'],states[k]['g2'],actual,sh,gd)
  d=draws[idx]
  for n in d['nums']:freq[n-1]+=1;last[n-1]=d['round']
  pc.update(itertools.combinations(d['nums'],2));tc.update(itertools.combinations(d['nums'],3));pr=b.structure_profile(d['nums'],draws[idx-1]['nums'])
  for i,v in enumerate(pr):prof[i][v]+=1
 keys=['max_hits','any2','any3','any4','winning_union_coverage','union_size'];score={'policy':{k:avg(obs,k) for k in keys},'matched_exact_label_null':{k:avg(nul,k) for k in keys}};score['delta']={k:score['policy'][k]-score['matched_exact_label_null'][k] for k in keys};alpha=.05/4;inf={}
 for j,k in enumerate(diff):
  s,bk=share(diff[k]);inf[k]={'adjusted_ci_delta':ci(diff[k],alpha,SEED+50+j),'positive_50_round_block_share':s,'block_deltas':bk}
 inf['strict_portfolio_pass']=inf['max_hits']['adjusted_ci_delta'][0]>0 and inf['any2']['adjusted_ci_delta'][0]>0 and inf['any3']['adjusted_ci_delta'][0]>0 and inf['any2']['positive_50_round_block_share']>=.65
 payload={'created_kst':datetime.now(KST).isoformat(),'target_round':1248,'data_cutoff':1247,'policy':'FROZEN_V4_REPAIR_SELECTOR_V39','no_future_leakage':True,'lineage':{'base':'V38/V28 hybrid ranker and same exact matched-label null','independent_repairs':'Only formulas frozen in research/prospective_v4 on 2026-10-09: V4_G,V4_C,V4_M,V4_P; expanding and frozen rolling300 modes','selector':'At each target choose from finite predeclared repair family using only previous <=150 outcome deltas; robust score=mean-0.5*SE; base retained unless challenger exceeds base','gate':'Unchanged: Bonferroni-adjusted block-bootstrap lower CI >0 for max/any2/any3 plus any2 positive 50-round block share >=0.65'},'candidate_family':list(CANDIDATE_NAMES),'selection_counts':dict(select_count),'template_counts':dict(template_count),'current':current,'walkforward_targets':len(obs),'scorecard':score,'inference':inf,'final_status':'STRICT_PASS' if inf['strict_portfolio_pass'] else 'FAIL_SAME_GATE'}
 OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'strict_pass':inf['strict_portfolio_pass'],'status':payload['final_status'],'scorecard':score,'selection_counts':dict(select_count),'current':current,'inference':{k:{'adjusted_ci_delta':v['adjusted_ci_delta'],'positive_50_round_block_share':v['positive_50_round_block_share']} for k,v in inf.items() if isinstance(v,dict)}},ensure_ascii=False))
if __name__=='__main__':main()
