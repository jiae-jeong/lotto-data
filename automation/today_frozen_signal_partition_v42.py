#!/usr/bin/env python3
from __future__ import annotations
import csv,importlib.util,itertools,json,random,statistics,math
from collections import Counter,deque
from datetime import datetime,timezone,timedelta
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'lotto_data.csv';B_SOURCE=ROOT/'research/1245_final_pipeline_v3/recovered_original_assets/b_model_backtest.py';AC_SOURCE=ROOT/'automation/recovered_models_v2.py';V12_SOURCE=ROOT/'automation/today_raw_signal_meta_v12.py';V18_SOURCE=ROOT/'automation/today_interaction_adagrad_v18.py'
OUT=ROOT/'analysis/2026-10-30/TODAY_FROZEN_SIGNAL_PARTITION_1248_V42.json';KST=timezone(timedelta(hours=9))
BLOCK=50;BOOT=7000;SEED=202610301610;ROLL=150;LR=.035;L2=.0025;P0=6/45
CFG={'slow':(1.0,1.0),'medium':(.9995,.999),'fast':(.9975,.992)}
PAT={
 'rr':[[0,4,8,12,16,20],[1,5,9,13,17,21],[2,6,10,14,18,22],[3,7,11,15,19,23]],
 'contig':[[0,1,2,3,4,5],[6,7,8,9,10,11],[12,13,14,15,16,17],[18,19,20,21,22,23]],
 'snake':[[0,7,8,15,16,23],[1,6,9,14,17,22],[2,5,10,13,18,21],[3,4,11,12,19,20]],
 'paired':[[0,1,8,9,16,17],[2,3,10,11,18,19],[4,5,12,13,20,21],[6,7,14,15,22,23]]}
SIGNALS=('H','G','C','M','P','T')
NAMES=tuple(f'{s}:{p}' for s in SIGNALS for p in PAT)

def imp(p,n):s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
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
 v=list(sc.values());m=statistics.mean(v);sd=statistics.pstdev(v) or 1.;return {n:(x-m)/sd for n,x in sc.items()}
def ranked_hybrid(slow,blend):
 core=sorted(range(1,46),key=lambda n:(-slow[n],n))[:6]
 tail=sorted((n for n in range(1,46) if n not in core),key=lambda n:(-blend[n],n))[:24]
 return core+tail

def agebin(age):return 0 if age==0 else 1 if age==1 else 2 if age==2 else 3 if age<=5 else 4 if age<=10 else 5

def frozen_scores(nums):
 # Exact formulas frozen in prospective_v4 on 2026-10-09; caller supplies rolling300 window.
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
 pc=Counter(p for q in nums for p in itertools.combinations(q,2));tc=Counter(t for q in nums for t in itertools.combinations(q,3));PS={x:0. for x in range(1,46)};TS={x:0. for x in range(1,46)}
 for pair in itertools.combinations(range(1,46),2):
  x,y=pair;e=(5/6)*(45/44)*freq[x]*freq[y]/n;v=(pc[pair]-e)/math.sqrt(max(e,1e-12));PS[x]+=v;PS[y]+=v
 for tri in itertools.combinations(range(1,46),3):
  x,y,z=tri;e=(20/36)*(2025/1892)*freq[x]*freq[y]*freq[z]/(n*n);v=(tc[tri]-e)/math.sqrt(max(e,1e-12));TS[x]+=v;TS[y]+=v;TS[z]+=v
 return {'G':G,'C':C,'M':M,'P':PS,'T':TS}

def lines(core,tail_order,pat):
 L=[tuple(sorted(core))]+[tuple(sorted(tail_order[j] for j in p)) for p in PAT[pat]]
 assert len(L)==5 and len(set(L))==5 and len(set().union(*map(set,L)))==30 and all(len(x)==6 for x in L);return L

def met(L,a):
 h=[len(set(x)&a) for x in L];u=set().union(*map(set,L));return {'max_hits':max(h),'any2':int(max(h)>=2),'any3':int(max(h)>=3),'any4':int(max(h)>=4),'winning_union_coverage':len(u&a),'union_size':len(u)}

def exact_null_disjoint30():
 # All candidate portfolios are five disjoint 6-number lines => identical null geometry.
 L=[tuple(range(1+6*i,7+6*i)) for i in range(5)]
 counts=[0]*32
 for n in range(1,46):
  mask=0
  for i,q in enumerate(L):
   if n in q:mask|=1<<i
  counts[mask]+=1
 dp={(0,0,0,0,0,0,0):1}
 for mask,c in enumerate(counts):
  if not c:continue
  nd={}
  for st,w in dp.items():
   k,*rest=st;hits=rest[:5];cov=rest[5]
   for j in range(min(c,6-k)+1):
    mult=math.comb(c,j);nh=[hits[i]+(j if mask&(1<<i) else 0) for i in range(5)];ns=(k+j,*nh,cov+(j if mask else 0));nd[ns]=nd.get(ns,0)+w*mult
  dp=nd
 total=math.comb(45,6);a={'max_hits':0.,'any2':0.,'any3':0.,'any4':0.,'winning_union_coverage':0.,'union_size':30.}
 for st,w in dp.items():
  if st[0]!=6:continue
  h=st[1:6];cov=st[6];m=max(h);p=w/total;a['max_hits']+=p*m;a['any2']+=p*(m>=2);a['any3']+=p*(m>=3);a['any4']+=p*(m>=4);a['winning_union_coverage']+=p*cov
 return a
NULL=exact_null_disjoint30()
def obj(m):return m['max_hits']+.85*m['any2']+1.35*m['any3']+.10*m['winning_union_coverage']
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
 OUT.parent.mkdir(parents=True,exist_ok=True);draws=load();b=imp(B_SOURCE,'bv42');ac=imp(AC_SOURCE,'acv42');v12=imp(V12_SOURCE,'v12v42');v18=imp(V18_SOURCE,'v18v42');bank=b.feature_structure_bank(b.make_structure_bank());freq=[0]*45;last=[0]*45;pc=Counter();tc=Counter();prof=[Counter() for _ in range(6)]
 for d in draws[:200]:
  for n in d['nums']:freq[n-1]+=1;last[n-1]=d['round']
  pc.update(itertools.combinations(d['nums'],2));tc.update(itertools.combinations(d['nums'],3));pr=b.structure_profile(d['nums'],None)
  for i,v in enumerate(pr[:5]):prof[i][v]+=1
 for i in range(1,200):prof[5][b.structure_profile(draws[i]['nums'],draws[i-1]['nums'])[5]]+=1
 dim=len(v18.feature_names());states={k:{'w':[math.log(P0/(1-P0))]+[0.0]*(dim-1),'g2':[0.0]*dim} for k in CFG};hist={k:deque(maxlen=ROLL) for k in NAMES};obs=[];diff={k:[] for k in ('max_hits','any2','any3','winning_union_coverage')};count=Counter();current=None
 for idx in range(200,len(draws)+1):
  preds={**b.predictions_for_round(draws,idx,freq,last,pc,tc,prof,bank),**ac.predict([q['nums'] for q in draws[:idx]])};X=v12.raw_features(draws,idx,freq,last,pc,tc,preds);scores={k:v18.predict(X,s['w']) for k,s in states.items()};zs={k:zscore(v) for k,v in scores.items()};blend={n:sum(zs[k][n] for k in CFG)/len(CFG) for n in range(1,46)};r=ranked_hybrid(scores['slow'],blend);core=r[:6];tail=r[6:]
  fs=frozen_scores([q['nums'] for q in draws[max(0,idx-300):idx]])
  orders={'H':tail}
  for s in SIGNALS[1:]:orders[s]=sorted(tail,key=lambda n:(-fs[s][n],n))
  policies={f'{s}:{p}':lines(core,orders[s],p) for s in SIGNALS for p in PAT}
  if idx<320:chosen='H:rr'
  else:
   def score_name(n):return statistics.mean(hist[n]) if hist[n] else -999.
   chosen=max(NAMES,key=lambda n:(score_name(n),n=='H:rr',n))
  L=policies[chosen]
  if idx==len(draws):
   current={'chosen_policy':chosen,'selector_scores':{n:(statistics.mean(hist[n]) if hist[n] else -999.) for n in NAMES},'core':core,'hybrid_top30':r,'signal_tail_orders':{s:orders[s] for s in SIGNALS},'lines':[list(x) for x in L],'union_size':30};break
  actual=set(draws[idx]['nums']);target=idx+1
  for n,Q in policies.items():hist[n].append(obj(met(Q,actual)))
  if target>=401:
   count[chosen]+=1;om=met(L,actual);obs.append(om)
   for k in diff:diff[k].append(float(om[k])-NULL[k])
  for k,(sh,gd) in CFG.items():states[k]['w'],states[k]['g2']=update(v18,X,states[k]['w'],states[k]['g2'],actual,sh,gd)
  d=draws[idx]
  for n in d['nums']:freq[n-1]+=1;last[n-1]=d['round']
  pc.update(itertools.combinations(d['nums'],2));tc.update(itertools.combinations(d['nums'],3));pr=b.structure_profile(d['nums'],draws[idx-1]['nums'])
  for i,v in enumerate(pr):prof[i][v]+=1
 keys=['max_hits','any2','any3','any4','winning_union_coverage','union_size'];score={'policy':{k:avg(obs,k) for k in keys},'matched_exact_label_null':dict(NULL)};score['delta']={k:score['policy'][k]-score['matched_exact_label_null'][k] for k in keys};alpha=.05/4;inf={}
 for j,k in enumerate(diff):
  s,bk=share(diff[k]);inf[k]={'adjusted_ci_delta':ci(diff[k],alpha,SEED+50+j),'positive_50_round_block_share':s,'block_deltas':bk}
 inf['strict_portfolio_pass']=inf['max_hits']['adjusted_ci_delta'][0]>0 and inf['any2']['adjusted_ci_delta'][0]>0 and inf['any3']['adjusted_ci_delta'][0]>0 and inf['any2']['positive_50_round_block_share']>=.65
 payload={'created_kst':datetime.now(KST).isoformat(),'target_round':1248,'data_cutoff':1247,'policy':'FROZEN_V4_SIGNAL_PARTITION_V42','no_future_leakage':True,'lineage':{'number_selection':'V38/V28 hybrid top30: slow core6 + multiscale blend tail24','partition_signals':'H plus rolling300 V4_G,V4_C,V4_M,V4_P,V4_T; V4 formulas/mode frozen on 2026-10-09','selection':'24 predeclared signal x partition policies; each target selects highest previous rolling150 fixed V28 objective only','geometry':'Every candidate is 5 disjoint lines, union30; exact matched-label null identical to V38 unique30 geometry','gate':'Unchanged Bonferroni block-bootstrap lower CI >0 for max/any2/any3 and any2 50-round positive share >=0.65'},'candidate_family':list(NAMES),'selection_counts':dict(count),'current':current,'walkforward_targets':len(obs),'scorecard':score,'inference':inf,'final_status':'STRICT_PASS' if inf['strict_portfolio_pass'] else 'FAIL_SAME_GATE'};OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'strict_pass':inf['strict_portfolio_pass'],'status':payload['final_status'],'selection_counts':dict(count),'scorecard':score,'current':current,'inference':{k:{'adjusted_ci_delta':v['adjusted_ci_delta'],'positive_50_round_block_share':v['positive_50_round_block_share']} for k,v in inf.items() if isinstance(v,dict)}},ensure_ascii=False))
if __name__=='__main__':main()
