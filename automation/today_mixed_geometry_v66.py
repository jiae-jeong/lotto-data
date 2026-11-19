#!/usr/bin/env python3
import os
from pathlib import Path
p=Path(__file__).resolve().parent/'today_online_geometry_v63.py'
src=p.read_text(encoding='utf-8')
mode=os.environ.get('V66_MODE','any3guard')
os.environ['ONLINE_MODE']=mode
src=src.replace('TODAY_ONLINE_GEOMETRY_{mode}_1248_V63.json','TODAY_MIXED_GEOMETRY_{mode}_1248_V66.json')
src=src.replace("'ONLINE_GEOMETRY_V63'","'MIXED_GEOMETRY_V66'")
src=src.replace("('rr','contig','snake','paired','top6x2','top10x2')","('mix1','mix2','mix3','mix4','mix5','mix6')")
oldtpl="""def template(pat):
 if pat in BASEPAT:return [[0,1,2,3,4,5]]+[[6+j for j in q] for q in BASEPAT[pat]]
 k=6 if pat=='top6x2' else 10;g=[[] for _ in range(5)]
 for r in range(k):g[r%5].append(r);g[(r+2)%5].append(r)
 u=k
 for i in range(5):
  while len(g[i])<6:g[i].append(u);u+=1
 return g"""
newtpl="""def template(pat):
 if pat=='mix1':
  return [[0,1,2,3,4,5],[0,6,7,8,9,10],[1,11,12,13,14,15],[2,16,17,18,19,20],[3,21,22,23,24,25]]
 if pat=='mix2':
  return [[0,1,2,3,4,5],[0,1,6,7,8,9],[2,3,10,11,12,13],[4,5,14,15,16,17],[18,19,20,21,22,23]]
 if pat=='mix3':
  return [[0,1,2,3,4,5],[0,6,7,8,9,10],[1,11,12,13,14,15],[16,17,18,19,20,21],[22,23,24,25,26,27]]
 if pat=='mix4':
  return [[0,1,2,3,4,5],[0,1,6,7,8,9],[2,3,10,11,12,13],[4,14,15,16,17,18],[5,19,20,21,22,23]]
 if pat=='mix5':
  return [[0,1,2,3,4,5],[0,1,6,7,8,9],[0,2,10,11,12,13],[1,3,14,15,16,17],[4,5,18,19,20,21]]
 return [[0,1,2,3,4,5],[0,1,6,7,8,9],[2,3,10,11,12,13],[4,5,14,15,16,17],[0,1,18,19,20,21]]"""
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
   chosen='H:mix1';locked=chosen
  else:
   if (idx-400)%50==0:
    def ds(n,k):return [float(q[k])-float(NULLS[n][k]) for q in list(hist[n])[-150:]]
    def pshare(v):
     b=[statistics.mean(v[i:i+50]) for i in range(0,len(v),50) if len(v[i:i+50])>=40];return sum(x>0 for x in b)/len(b) if b else 0.
    def lb(v):
     if len(v)<40:return -999.
     mu=statistics.mean(v);sd=statistics.stdev(v) if len(v)>1 else 0.;return mu-1.645*sd/(len(v)**.5)
    def key(n):
     vm,v2,v3=ds(n,'max_hits'),ds(n,'any2'),ds(n,'any3')
     if len(vm)<50:return (-999.,)*9
     lm,l2,l3=lb(vm),lb(v2),lb(v3);pm,p2,p3=pshare(vm),pshare(v2),pshare(v3)
     mm,m2,m3=statistics.mean(vm),statistics.mean(v2),statistics.mean(v3)
     if mode=='any3guard':return (l3>0,p3>=2/3,lm>0,pm>=2/3,p2,l2,m2,l3+lm,n)
     if mode=='any2guard':return (l3>0,lm>0,p3>=2/3,pm>=2/3,p2>=2/3,l2,p2,l3+lm,n)
     if mode=='jointlb':return (min(lm,l2,l3),sum((lm,l2,l3)),min(pm,p2,p3),p2,m3,m2,n,'','')
     return (min(pm,p2,p3),p2,min(lm,l2,l3),sum((lm,l2,l3)),m3,m2,mm,n,'')
    locked=max(NAMES,key=key)
   chosen=locked\"\"\""""
assert oldsel in src
src=src.replace(oldsel,newsel)
src=src.replace("hist={k:deque(maxlen=150) for k in NAMES};obs=[];nullobs=[];diff=", "hist={k:deque(maxlen=150) for k in NAMES};locked='H:mix1';obs=[];nullobs=[];diff=")
src=src.replace("'selection':'V63 {mode}: deterministic online expert selection among H/M x disjoint/top6/top10 geometries using only prior <=150 outcomes; exact geometry-specific null; strict gate unchanged.'","'selection':'V66 {mode}: six preregistered mixed overlap/coverage geometries x H/M, locked for each 50-target block using only prior <=150 outcomes; exact geometry-specific null and final strict gate unchanged.'")
src=src.replace("'geometry':'V63 online geometry family; every target evaluated against exact matched-label null of chosen ticket-overlap mask.'","'geometry':'V66 mixed portfolios combine overlap-heavy core lines and coverage-heavy tail lines; each chosen geometry is evaluated against its exact matched-label null.'")
exec(compile(src,str(p),'exec'),globals(),globals())
