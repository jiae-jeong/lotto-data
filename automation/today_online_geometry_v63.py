#!/usr/bin/env python3
import os
from pathlib import Path
p=Path(__file__).resolve().parent/'today_frozen_signal_partition_v42.py'
s=p.read_text(encoding='utf-8')
mode=os.environ.get('ONLINE_MODE','gatefocus')
s=s.replace("TODAY_FROZEN_SIGNAL_PARTITION_1248_V42.json",f"TODAY_ONLINE_GEOMETRY_{mode}_1248_V63.json")
s=s.replace("SEED=202610301610","SEED=202610301963")
s=s.replace("SIGNALS=('H','G','C','M','P','T')","PAT={k:None for k in ('rr','contig','snake','paired','top6x2','top10x2')}\nSIGNALS=('H','M')")
s=s.replace("'FROZEN_V4_SIGNAL_PARTITION_V42'","'ONLINE_GEOMETRY_V63'")
s=s.replace("pc=Counter(p for q in nums for p in itertools.combinations(q,2));tc=Counter(t for q in nums for t in itertools.combinations(q,3));PS={x:0. for x in range(1,46)};TS={x:0. for x in range(1,46)}","pc=Counter(p for q in nums for p in itertools.combinations(q,2));PS={x:0. for x in range(1,46)}")
oldtri=""" for tri in itertools.combinations(range(1,46),3):
  x,y,z=tri;e=(20/36)*(2025/1892)*freq[x]*freq[y]*freq[z]/(n*n);v=(tc[tri]-e)/math.sqrt(max(e,1e-12));TS[x]+=v;TS[y]+=v;TS[z]+=v
 return {'G':G,'C':C,'M':M,'P':PS,'T':TS}"""
assert oldtri in s
s=s.replace(oldtri,""" return {'G':G,'C':C,'M':M,'P':PS}""")
oldlines="""def lines(core,tail_order,pat):
 L=[tuple(sorted(core))]+[tuple(sorted(tail_order[j] for j in p)) for p in PAT[pat]]
 assert len(L)==5 and len(set(L))==5 and len(set().union(*map(set,L)))==30 and all(len(x)==6 for x in L);return L"""
newlines="""BASEPAT={
 'rr':[[0,4,8,12,16,20],[1,5,9,13,17,21],[2,6,10,14,18,22],[3,7,11,15,19,23]],
 'contig':[[0,1,2,3,4,5],[6,7,8,9,10,11],[12,13,14,15,16,17],[18,19,20,21,22,23]],
 'snake':[[0,7,8,15,16,23],[1,6,9,14,17,22],[2,5,10,13,18,21],[3,4,11,12,19,20]],
 'paired':[[0,1,8,9,16,17],[2,3,10,11,18,19],[4,5,12,13,20,21],[6,7,14,15,22,23]]}
def template(pat):
 if pat in BASEPAT:return [[0,1,2,3,4,5]]+[[6+j for j in q] for q in BASEPAT[pat]]
 k=6 if pat=='top6x2' else 10;g=[[] for _ in range(5)]
 for r in range(k):g[r%5].append(r);g[(r+2)%5].append(r)
 u=k
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
s=s.replace("hist={k:deque(maxlen=ROLL) for k in NAMES};obs=[];diff=", "hist={k:deque(maxlen=150) for k in NAMES};obs=[];nullobs=[];diff=")
oldsel="""  if idx<320:chosen='H:rr'
  else:
   def score_name(n):return statistics.mean(hist[n]) if hist[n] else -999.
   chosen=max(NAMES,key=lambda n:(score_name(n),n=='H:rr',n))"""
newsel="""  if idx<400:chosen='H:rr'
  else:
   def ds(n,k):return [float(q[k])-float(NULLS[n][k]) for q in hist[n]]
   def ew(v,lam):
    if not v:return -999.
    w=[lam**(len(v)-1-i) for i in range(len(v))];return sum(a*b for a,b in zip(v,w))/sum(w)
   def posblocks(v):
    b=[statistics.mean(v[i:i+50]) for i in range(0,len(v),50) if len(v[i:i+50])>=40];return sum(x>0 for x in b)/len(b) if b else 0.
   def key(n):
    vm,v2,v3=ds(n,'max_hits'),ds(n,'any2'),ds(n,'any3')
    if len(vm)<50:return (-999.,)*7
    if mode=='gatefocus':
     a=(ew(vm,.985),ew(v2,.985),ew(v3,.985));return (min(a),sum(a),posblocks(v2),a[2],a[1],a[0],n)
    if mode=='balanced':
     a=(ew(vm,.99),ew(v2,.99),ew(v3,.99));return (.40*a[0]+.35*a[1]+.25*a[2],min(a),posblocks(v2),a[2],a[1],a[0],n)
    if mode=='any3lift':
     a=(ew(vm,.98),ew(v2,.98),ew(v3,.98));return (a[2]>0,a[1]>0,a[0]>0,1.3*a[2]+a[1]+.6*a[0],posblocks(v2),min(a),n)
    a=(ew(vm,.995),ew(v2,.995),ew(v3,.995));return (posblocks(v2),min(a),sum(a),a[2],a[1],a[0],n)
   chosen=max(NAMES,key=key)"""
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
s=s.replace("'selection':'24 predeclared signal x partition policies; each target selects highest previous rolling150 fixed V28 objective only'",f"'selection':'V63 {mode}: deterministic online expert selection among H/M x disjoint/top6/top10 geometries using only prior <=150 outcomes; exact geometry-specific null; strict gate unchanged.'")
s=s.replace("'geometry':'Every candidate is 5 disjoint lines, union30; exact matched-label null identical to V38 unique30 geometry'","'geometry':'V63 online geometry family; every target evaluated against exact matched-label null of chosen ticket-overlap mask.'")
exec(compile(s,str(p),'exec'),globals(),globals())
