#!/usr/bin/env python3
from pathlib import Path
p=Path(__file__).resolve().parent/'today_online_geometry_v63.py'
src=p.read_text(encoding='utf-8')
src=src.replace('TODAY_ONLINE_GEOMETRY_{mode}_1248_V63.json','TODAY_CONTEXTUAL_KNN_1248_V74.json')
src=src.replace("'ONLINE_GEOMETRY_V63'","'CONTEXTUAL_KNN_V74'")
src=src.replace("hist={k:deque(maxlen=150) for k in NAMES};obs=[];nullobs=[];diff=", "hist={k:deque(maxlen=150) for k in NAMES};ctxhist=deque(maxlen=300);obs=[];nullobs=[];diff=")
old="""newsel=\"\"\"  if idx<400:chosen='H:rr'
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
new="""newsel=\"\"\"  top10={k:set(sorted(range(1,46),key=lambda n:(-scores[k][n],n))[:10]) for k in CFG}
  feat=(
   statistics.mean(blend[n] for n in r[:6])-statistics.mean(blend[n] for n in r[6:30]),
   statistics.pstdev(blend.values()),
   len(top10['slow']&top10['medium'])/10.0,
   len(top10['slow']&top10['fast'])/10.0,
   len(top10['medium']&top10['fast'])/10.0)
  if idx<400 or len(ctxhist)<100:
   chosen='H:rr'
  else:
   rows=list(ctxhist)
   scales=[]
   for j in range(len(feat)):
    vals=[z[0][j] for z in rows];sd=statistics.pstdev(vals);scales.append(sd if sd>1e-12 else 1.0)
   def dist(z):return sum(((feat[j]-z[0][j])/scales[j])**2 for j in range(len(feat)))
   near=sorted(rows,key=dist)[:100]
   def key(n):
    dm=[float(z[1][n]['max_hits'])-float(NULLS[n]['max_hits']) for z in near]
    d2=[float(z[1][n]['any2'])-float(NULLS[n]['any2']) for z in near]
    d3=[float(z[1][n]['any3'])-float(NULLS[n]['any3']) for z in near]
    mm,m2,m3=statistics.mean(dm),statistics.mean(d2),statistics.mean(d3)
    return (min(mm,m2,m3),m2>0,m3>0,mm>0,m2+1.25*m3+.6*mm,m3,m2,n)
   chosen=max(NAMES,key=key)\"\"\""""
assert old in src
src=src.replace(old,new)
oldhist="for n,Q in policies.items():hist[n].append(met(Q,actual))"
newhist="ctxhist.append((feat,{n:met(Q,actual) for n,Q in policies.items()}))\\n  for n,Q in policies.items():hist[n].append(met(Q,actual))"
assert oldhist in src
src=src.replace(oldhist,newhist)
src=src.replace("'selection':'V63 {mode}: deterministic online expert selection among H/M x disjoint/top6/top10 geometries using only prior <=150 outcomes; exact geometry-specific null; strict gate unchanged.'","'selection':'V74 contextual kNN: current choice uses only model-state features available before draw (blend concentration and slow/medium/fast top10 agreement), 100 nearest prior contexts from <=300 history, and their realized geometry deltas. No current/future outcome enters selection; exact geometry null and strict gate unchanged.'")
exec(compile(src,str(p),'exec'),globals(),globals())
