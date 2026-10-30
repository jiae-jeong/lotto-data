#!/usr/bin/env python3
from pathlib import Path
p=Path(__file__).resolve().parent/'today_online_geometry_v63.py'
src=p.read_text(encoding='utf-8')
src=src.replace('TODAY_ONLINE_GEOMETRY_{mode}_1248_V63.json','TODAY_CONFIDENCE_REGIME_1248_V71.json')
src=src.replace("'ONLINE_GEOMETRY_V63'","'CONFIDENCE_REGIME_V71'")
src=src.replace("hist={k:deque(maxlen=150) for k in NAMES};obs=[];nullobs=[];diff=", "hist={k:deque(maxlen=150) for k in NAMES};confhist=deque(maxlen=150);obs=[];nullobs=[];diff=")
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
new="""newsel=\"\"\"  conf=statistics.mean(blend[n] for n in r[:6])-statistics.mean(blend[n] for n in r[6:30])
  if idx<400 or len(confhist)<50:
   chosen='H:contig'
  else:
   thr=statistics.median(confhist)
   chosen='H:top6x2' if conf>=thr else 'H:contig'
  confhist.append(conf)\"\"\""""
assert old in src
src=src.replace(old,new)
src=src.replace("'selection':'V63 {mode}: deterministic online expert selection among H/M x disjoint/top6/top10 geometries using only prior <=150 outcomes; exact geometry-specific null; strict gate unchanged.'","'selection':'V71 outcome-blind confidence regime: if current multiscale top6 concentration is above median of prior <=150 concentrations use H:top6x2, else H:contig. No outcome-tuned threshold; exact geometry null and strict gate unchanged.'")
exec(compile(src,str(p),'exec'),globals(),globals())
