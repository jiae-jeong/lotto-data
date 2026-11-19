#!/usr/bin/env python3
from pathlib import Path
p=Path(__file__).resolve().parent/'today_frozen_signal_partition_v42.py'
s=p.read_text(encoding='utf-8')
s=s.replace("TODAY_FROZEN_SIGNAL_PARTITION_1248_V42.json","TODAY_CALIBRATE400_FREEZE_1248_V72B.json")
s=s.replace("SEED=202610301610","SEED=202610302172")
s=s.replace("SIGNALS=('H','G','C','M','P','T')","PAT={k:None for k in ('repeat1','repeat2','top5x2','top6x2','top10x2','top3x3')}\nSIGNALS=('H','M')")
s=s.replace("'FROZEN_V4_SIGNAL_PARTITION_V42'","'CALIBRATE400_FREEZE_V72B'")
s=s.replace("pc=Counter(p for q in nums for p in itertools.combinations(q,2));tc=Counter(t for q in nums for t in itertools.combinations(q,3));PS={x:0. for x in range(1,46)};TS={x:0. for x in range(1,46)}","pc=Counter(p for q in nums for p in itertools.combinations(q,2));PS={x:0. for x in range(1,46)}")
oldtri=""" for tri in itertools.combinations(range(1,46),3):
  x,y,z=tri;e=(20/36)*(2025/1892)*freq[x]*freq[y]*freq[z]/(n*n);v=(tc[tri]-e)/math.sqrt(max(e,1e-12));TS[x]+=v;TS[y]+=v;TS[z]+=v
 return {'G':G,'C':C,'M':M,'P':PS,'T':TS}"""
assert oldtri in s
s=s.replace(oldtri,""" return {'G':G,'C':C,'M':M,'P':PS}""")
oldlines="""def lines(core,tail_order,pat):
 L=[tuple(sorted(core))]+[tuple(sorted(tail_order[j] for j in p)) for p in PAT[pat]]
 assert len(L)==5 and len(set(L))==5 and len(set().union(*map(set,L)))==30 and all(len(x)==6 for x in L);return L"""
newlines="""def template(pat):
 if pat=='repeat1': return [[0]+[1+i+5*j for j in range(5)] for i in range(5)]
 if pat=='repeat2': return [[0,1]+[2+i+5*j for j in range(4)] for i in range(5)]
 if pat=='top5x2': return [[i,(i+1)%5]+[5+i+5*j for j in range(4)] for i in range(5)]
 if pat in ('top6x2','top10x2'):
  k=6 if pat=='top6x2' else 10;g=[[] for _ in range(5)]
  for r in range(k):g[r%5].append(r);g[(r+2)%5].append(r)
  u=k
  for i in range(5):
   while len(g[i])<6:g[i].append(u);u+=1
  return g
 g=[[0],[0,1],[0,1,2],[1,2],[2]];u=3
 for i in range(5):
  while len(g[i])<6:g[i].append(u);u+=1
 return g

def lines(core,tail_order,pat):
 order=list(core)+list(tail_order);L=[tuple(sorted(order[j] for j in q)) for q in template(pat)]
 assert len(L)==5 and len(set(L))==5 and all(len(x)==6 and len(set(x))==6 for x in L);return L"""
assert oldlines in s;s=s.replace(oldlines,newlines)
start=s.index('def exact_null_disjoint30():');end=s.index('NULL=exact_null_disjoint30()',start)+len('NULL=exact_null_disjoint30()')
newnull="""def exact_null_geometry(pat):
 L=[tuple(j+1 for j in q) for q in template(pat)];counts=[0]*32
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
 total=math.comb(45,6);u=len(set().union(*map(set,L)));a={'max_hits':0.,'any2':0.,'any3':0.,'any4':0.,'winning_union_coverage':0.,'union_size':float(u)}
 for st,w in dp.items():
  if st[0]!=6:continue
  h=st[1:6];cov=st[6];m=max(h);pr=w/total;a['max_hits']+=pr*m;a['any2']+=pr*(m>=2);a['any3']+=pr*(m>=3);a['any4']+=pr*(m>=4);a['winning_union_coverage']+=pr*cov
 return a
NULLS={n:exact_null_geometry(n.split(':',1)[1]) for n in NAMES}"""
s=s[:start]+newnull+s[end:]
s=s.replace("hist={k:deque(maxlen=ROLL) for k in NAMES};obs=[];diff=", "hist={k:deque(maxlen=150) for k in NAMES};locked='H:repeat1';obs=[];nullobs=[];diff=")
oldsel="""  if idx<320:chosen='H:rr'
  else:
   def score_name(n):return statistics.mean(hist[n]) if hist[n] else -999.
   chosen=max(NAMES,key=lambda n:(score_name(n),n=='H:rr',n))"""
newsel="""  if idx<400:
   chosen='H:repeat1'
  else:
   if idx==400:
    def ds(n,k):return [float(q[k])-float(NULLS[n][k]) for q in list(hist[n])]
    def blocks(v):return [statistics.mean(v[i:i+50]) for i in range(0,len(v),50) if len(v[i:i+50])>=40]
    def lb(v):
     if len(v)<100:return -999.
     mu=statistics.mean(v);sd=statistics.stdev(v) if len(v)>1 else 0.;return mu-1.645*sd/(len(v)**.5)
    def pshare(v):
     b=blocks(v);return sum(x>0 for x in b)/len(b) if b else 0.
    def key(n):
     vm,v2,v3=ds(n,'max_hits'),ds(n,'any2'),ds(n,'any3')
     lm,l2,l3=lb(vm),lb(v2),lb(v3);pm,p2,p3=pshare(vm),pshare(v2),pshare(v3)
     return (min(lm,l2,l3),min(pm,p2,p3),sum((lm,l2,l3)),p2,p3,l2,l3,lm,n)
    locked=max(NAMES,key=key)
   chosen=locked"""
assert oldsel in s;s=s.replace(oldsel,newsel)
s=s.replace("for n,Q in policies.items():hist[n].append(obj(met(Q,actual)))","for n,Q in policies.items():hist[n].append(met(Q,actual))")
oldobs="""  if target>=401:
   count[chosen]+=1;om=met(L,actual);obs.append(om)
   for k in diff:diff[k].append(float(om[k])-NULL[k])"""
newobs="""  if target>=401:
   count[chosen]+=1;om=met(L,actual);sn=NULLS[chosen];obs.append(om);nullobs.append(sn)
   for k in diff:diff[k].append(float(om[k])-float(sn[k]))"""
assert oldobs in s;s=s.replace(oldobs,newobs)
oldscore="score={'policy':{k:avg(obs,k) for k in keys},'matched_exact_label_null':dict(NULL)}"
newscore="score={'policy':{k:avg(obs,k) for k in keys},'matched_exact_label_null':{k:statistics.mean(float(x[k]) for x in nullobs) for k in keys}}"
assert oldscore in s;s=s.replace(oldscore,newscore)
oldcur="""current={'chosen_policy':chosen,'selector_scores':{n:(statistics.mean(hist[n]) if hist[n] else -999.) for n in NAMES},'core':core,'hybrid_top30':r,'signal_tail_orders':{s:orders[s] for s in SIGNALS},'lines':[list(x) for x in L],'union_size':30};break"""
newcur="""current={'chosen_policy':chosen,'selector_scores':{n:({k:statistics.mean(float(q[k]) for q in hist[n]) for k in ('max_hits','any2','any3')} if hist[n] else {}) for n in NAMES},'core':core,'hybrid_top30':r,'signal_tail_orders':{sg:orders[sg] for sg in SIGNALS},'lines':[list(x) for x in L],'union_size':len(set().union(*map(set,L)))};break"""
assert oldcur in s;s=s.replace(oldcur,newcur)
s=s.replace("'selection':'24 predeclared signal x partition policies; each target selects highest previous rolling150 fixed V28 objective only'","'selection':'V72B independent holdout: at target401 choose one of 12 preregistered H/M overlap experts using only <=400 outcomes and a maximin lower-bound/stability key; freeze unchanged for all 401..1248. Strict gate unchanged.'")
s=s.replace("'geometry':'Every candidate is 5 disjoint lines, union30; exact matched-label null identical to V38 unique30 geometry'","'geometry':'V72B selected overlap expert uses its exact matched-label null; selection is frozen before holdout evaluation.'")
exec(compile(s,str(p),'exec'),globals(),globals())
