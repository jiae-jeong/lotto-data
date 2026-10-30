#!/usr/bin/env python3
import os
from pathlib import Path
p=Path(__file__).resolve().parent/'today_overlap_adaptive_v59.py'
src=p.read_text(encoding='utf-8')
os.environ['OVERLAP_ADAPT_MODE']='any3guard'
src=src.replace('TODAY_OVERLAP_ADAPTIVE_{mode}_1248_V59.json','TODAY_EXPANDED_OVERLAP_1248_V76.json')
src=src.replace("'OVERLAP_ADAPTIVE_V59'","'EXPANDED_OVERLAP_V76'")
src=src.replace("('repeat1','repeat2','top5x2','top6x2','top10x2','top3x3')","('repeat1','repeat2','top5x2','top6x2','top10x2','top3x3','x1','x2','x3','x4','x5','triple1','triple2')")
needle="""def template(pat):
 if pat=='repeat1': return [[0]+[1+i+5*j for j in range(5)] for i in range(5)]"""
repl="""def template(pat):
 if pat.startswith('x'):
  k=int(pat[1:]);g=[[] for _ in range(5)]
  for r in range(k):g[r%5].append(r);g[(r+2)%5].append(r)
  u=k
  for i in range(5):
   while len(g[i])<6:g[i].append(u);u+=1
  return g
 if pat=='triple1':
  g=[[],[],[],[],[]];g[0].append(0);g[2].append(0);g[4].append(0);u=1
  for i in range(5):
   while len(g[i])<6:g[i].append(u);u+=1
  return g
 if pat=='triple2':
  g=[[],[],[],[],[]]
  for r in range(2):g[r%5].append(r);g[(r+2)%5].append(r);g[(r+4)%5].append(r)
  u=2
  for i in range(5):
   while len(g[i])<6:g[i].append(u);u+=1
  return g
 if pat=='repeat1': return [[0]+[1+i+5*j for j in range(5)] for i in range(5)]"""
assert needle in src
src=src.replace(needle,repl)
src=src.replace("'selection':'V59 {mode}: 12 preregistered H/M overlap policies with geometry-specific exact nulls; selected only at 50-target boundaries from prior <=150 outcomes.'","'selection':'V76 fixed any3guard selector over 26 preregistered H/M heavy+intermediate overlap experts; every 50-target choice uses only prior <=150 outcomes; geometry-specific exact null and strict gate unchanged.'")
# repair V59 selector score serialization
needle2="exec(compile(s,str(p),'exec'),globals(),globals())"
patch="""old2=\"'selector_scores':{n:(statistics.mean(hist[n]) if hist[n] else -999.) for n in NAMES}\"\nnew2=\"'selector_scores':{n:({k:statistics.mean(float(q[k]) for q in hist[n]) for k in ('max_hits','any2','any3','winning_union_coverage')} if hist[n] else {}) for n in NAMES}\"\nassert old2 in s\ns=s.replace(old2,new2)\nexec(compile(s,str(p),'exec'),globals(),globals())"""
assert needle2 in src
src=src.replace(needle2,patch)
exec(compile(src,str(p),'exec'),globals(),globals())
