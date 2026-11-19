#!/usr/bin/env python3
from pathlib import Path
p=Path(__file__).resolve().parent/'today_frozen_signal_partition_v42.py'
s=p.read_text(encoding='utf-8')
s=s.replace("TODAY_FROZEN_SIGNAL_PARTITION_1248_V42.json","TODAY_RECALLWEIGHTED_MID_OVERLAP_1248_V75.json")
s=s.replace("SEED=202610301610","SEED=202610302375")
s=s.replace("SIGNALS=('H','G','C','M','P','T')","PAT={'x3':None}\nSIGNALS=('H',)")
s=s.replace("'FROZEN_V4_SIGNAL_PARTITION_V42'","'RECALLWEIGHTED_MID_OVERLAP_V75'")
s=s.replace("pc=Counter(p for q in nums for p in itertools.combinations(q,2));tc=Counter(t for q in nums for t in itertools.combinations(q,3));PS={x:0. for x in range(1,46)};TS={x:0. for x in range(1,46)}","pc=Counter(p for q in nums for p in itertools.combinations(q,2));PS={x:0. for x in range(1,46)}")
oldtri=""" for tri in itertools.combinations(range(1,46),3):
  x,y,z=tri;e=(20/36)*(2025/1892)*freq[x]*freq[y]*freq[z]/(n*n);v=(tc[tri]-e)/math.sqrt(max(e,1e-12));TS[x]+=v;TS[y]+=v;TS[z]+=v
 return {'G':G,'C':C,'M':M,'P':PS,'T':TS}"""
assert oldtri in s;s=s.replace(oldtri,""" return {'G':G,'C':C,'M':M,'P':PS}""")
oldlines="""def lines(core,tail_order,pat):
 L=[tuple(sorted(core))]+[tuple(sorted(tail_order[j] for j in p)) for p in PAT[pat]]
 assert len(L)==5 and len(set(L))==5 and len(set().union(*map(set,L)))==30 and all(len(x)==6 for x in L);return L"""
newlines="""def template():
 g=[[] for _ in range(5)]
 for r in range(3):g[r].append(r);g[(r+2)%5].append(r)
 u=3
 for i in range(5):
  while len(g[i])<6:g[i].append(u);u+=1
 return g

def lines(core,tail_order,pat):
 order=list(core)+list(tail_order);L=[tuple(sorted(order[j] for j in q)) for q in template()]
 assert len(L)==5 and len(set(L))==5 and len(set().union(*map(set,L)))==27 and all(len(x)==6 and len(set(x))==6 for x in L);return L"""
assert oldlines in s;s=s.replace(oldlines,newlines)
start=s.index('def exact_null_disjoint30():');end=s.index('NULL=exact_null_disjoint30()',start)+len('NULL=exact_null_disjoint30()')
newnull="""def exact_null_mid():
 L=[tuple(j+1 for j in q) for q in template()];counts=[0]*32
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
 total=math.comb(45,6);a={'max_hits':0.,'any2':0.,'any3':0.,'any4':0.,'winning_union_coverage':0.,'union_size':27.0}
 for st,w in dp.items():
  if st[0]!=6:continue
  h=st[1:6];cov=st[6];m=max(h);pr=w/total;a['max_hits']+=pr*m;a['any2']+=pr*(m>=2);a['any3']+=pr*(m>=3);a['any4']+=pr*(m>=4);a['winning_union_coverage']+=pr*cov
 return a
NULL=exact_null_mid()"""
s=s[:start]+newnull+s[end:]
s=s.replace("hist={k:deque(maxlen=ROLL) for k in NAMES};obs=[];diff=", "hist={k:deque(maxlen=ROLL) for k in NAMES};recallperf={k:deque(maxlen=150) for k in CFG};obs=[];diff=")
oldrank="scores={k:v18.predict(X,s['w']) for k,s in states.items()};zs={k:zscore(v) for k,v in scores.items()};blend={n:sum(zs[k][n] for k in CFG)/len(CFG) for n in range(1,46)};r=ranked_hybrid(scores['slow'],blend);core=r[:6];tail=r[6:]"
newrank="""scores={k:v18.predict(X,s['w']) for k,s in states.items()};zs={k:zscore(v) for k,v in scores.items()}
  means={k:(statistics.mean(recallperf[k]) if recallperf[k] else 0.0) for k in CFG};raw={k:math.exp(4.0*means[k]) for k in CFG};den=sum(raw.values());lw={k:raw[k]/den for k in CFG}
  blend={n:sum(lw[k]*zs[k][n] for k in CFG) for n in range(1,46)};r=sorted(range(1,46),key=lambda n:(-blend[n],n))[:30];core=r[:6];tail=r[6:]"""
assert oldrank in s;s=s.replace(oldrank,newrank)
oldsel="""  if idx<320:chosen='H:rr'
  else:
   def score_name(n):return statistics.mean(hist[n]) if hist[n] else -999.
   chosen=max(NAMES,key=lambda n:(score_name(n),n=='H:rr',n))"""
newsel="""  chosen='H:x3'"""
assert oldsel in s;s=s.replace(oldsel,newsel)
oldhist="for n,Q in policies.items():hist[n].append(obj(met(Q,actual)))"
newhist="""for k in CFG:
   top30=set(sorted(range(1,46),key=lambda n:(-scores[k][n],n))[:30]);recallperf[k].append(len(top30&actual)-4.0)
  for n,Q in policies.items():hist[n].append(obj(met(Q,actual)))"""
assert oldhist in s;s=s.replace(oldhist,newhist)
s=s.replace("'selection':'24 predeclared signal x partition policies; each target selects highest previous rolling150 fixed V28 objective only'","'selection':'V75 fixed H:x3 ticket construction; learner blend weights are deterministic softmax of each slow/medium/fast learner prior <=150 top30 recall delta, updated only after each realized draw for the next target.'")
s=s.replace("'number_selection':'V38/V28 hybrid top30: slow core6 + multiscale blend tail24'","'number_selection':'V75 rolling recall-weighted slow/medium/fast z-score ensemble, pure top30; no current outcome enters weights'")
s=s.replace("'geometry':'Every candidate is 5 disjoint lines, union30; exact matched-label null identical to V38 unique30 geometry'","'geometry':'V75 fixed x3 intermediate overlap: top3 ranks appear twice, union27; exact matched-label null computed for this geometry.'")
exec(compile(s,str(p),'exec'),globals(),globals())
