#!/usr/bin/env python3
import os
from pathlib import Path
p=Path(__file__).resolve().parent/'today_online_geometry_v63.py'
src=p.read_text(encoding='utf-8')
mode=os.environ.get('V65_MODE','protect23')
os.environ['ONLINE_MODE']=mode
src=src.replace('TODAY_ONLINE_GEOMETRY_{mode}_1248_V63.json','TODAY_BLOCKLOCKED_GEOMETRY_{mode}_1248_V65.json')
src=src.replace("'ONLINE_GEOMETRY_V63'","'BLOCKLOCKED_GEOMETRY_V65'")
src=src.replace("('rr','contig','snake','paired','top6x2','top10x2')","('rr','contig','snake','paired','top3x3','top6x2','top10x2')")
oldtpl="""def template(pat):
 if pat in BASEPAT:return [[0,1,2,3,4,5]]+[[6+j for j in q] for q in BASEPAT[pat]]
 k=6 if pat=='top6x2' else 10;g=[[] for _ in range(5)]
 for r in range(k):g[r%5].append(r);g[(r+2)%5].append(r)
 u=k
 for i in range(5):
  while len(g[i])<6:g[i].append(u);u+=1
 return g"""
newtpl="""def template(pat):
 if pat in BASEPAT:return [[0,1,2,3,4,5]]+[[6+j for j in q] for q in BASEPAT[pat]]
 if pat=='top3x3':
  g=[[0],[0,1],[0,1,2],[1,2],[2]];u=3
  for i in range(5):
   while len(g[i])<6:g[i].append(u);u+=1
  return g
 k=6 if pat=='top6x2' else 10;g=[[] for _ in range(5)]
 for r in range(k):g[r%5].append(r);g[(r+2)%5].append(r)
 u=k
 for i in range(5):
  while len(g[i])<6:g[i].append(u);u+=1
 return g"""
assert oldtpl in src
src=src.replace(oldtpl,newtpl)
oldsel="""newsel=\"\"\"  if idx<400:chosen='H:rr'
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
   chosen=max(NAMES,key=key)\"\"\""""
newsel="""newsel=\"\"\"  if idx<400:
   chosen='H:rr';locked=chosen
  else:
   if (idx-400)%50==0:
    def ds(n,k):return [float(q[k])-float(NULLS[n][k]) for q in list(hist[n])[-150:]]
    def blocks(v):return [statistics.mean(v[i:i+50]) for i in range(0,len(v),50) if len(v[i:i+50])>=40]
    def pshare(v):
     b=blocks(v);return sum(x>0 for x in b)/len(b) if b else 0.
    def lb(v):
     if len(v)<40:return -999.
     mu=statistics.mean(v);sd=statistics.stdev(v) if len(v)>1 else 0.;return mu-1.645*sd/(len(v)**.5)
    def key(n):
     vm,v2,v3=ds(n,'max_hits'),ds(n,'any2'),ds(n,'any3')
     if len(vm)<50:return (-999.,)*10
     lm,l2,l3=lb(vm),lb(v2),lb(v3);pm,p2,p3=pshare(vm),pshare(v2),pshare(v3)
     mm,m2,m3=statistics.mean(vm),statistics.mean(v2),statistics.mean(v3)
     if mode=='protect23':return (l3>0,lm>0,p3>=2/3,pm>=2/3,p2>=2/3,l2,p2,l3,lm,n)
     if mode=='share23':return (p3>=2/3,pm>=2/3,p2,l2,l3,lm,m2,m3,mm,n)
     if mode=='minlb':return (min(lm,l2,l3),p2,min(pm,p3),l2,l3,lm,m2+m3+.5*mm,n,'','')
     return (l3>0,p3>=2/3,lm>0,pm>=2/3,p2,l2,m2,0.8*m3+0.5*mm,l3+lm,n)
    locked=max(NAMES,key=key)
   chosen=locked\"\"\""""
assert oldsel in src
src=src.replace(oldsel,newsel)
src=src.replace("hist={k:deque(maxlen=150) for k in NAMES};obs=[];nullobs=[];diff=", "hist={k:deque(maxlen=150) for k in NAMES};locked='H:rr';obs=[];nullobs=[];diff=")
src=src.replace("'selection':'V63 {mode}: deterministic online expert selection among H/M x disjoint/top6/top10 geometries using only prior <=150 outcomes; exact geometry-specific null; strict gate unchanged.'","'selection':'V65 {mode}: block-locked 50-target selector among H/M x disjoint/top3/top6/top10 geometries. At each lock only prior <=150 outcomes are used; max/any3 gate protection precedes any2 optimization; exact geometry null and strict gate unchanged.'")
exec(compile(src,str(p),'exec'),globals(),globals())
