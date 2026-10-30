#!/usr/bin/env python3
import os
from pathlib import Path
p=Path(__file__).resolve().parent/'today_overlap_adaptive_v59.py'
src=p.read_text(encoding='utf-8')
mode=os.environ.get('V68_MODE','rescue0')
os.environ['OVERLAP_ADAPT_MODE']=mode
src=src.replace('TODAY_OVERLAP_ADAPTIVE_{mode}_1248_V59.json','TODAY_ANY2_RESCUE_{mode}_1248_V68.json')
src=src.replace("'OVERLAP_ADAPTIVE_V59'","'ANY2_RESCUE_V68'")
src=src.replace("('repeat1','repeat2','top5x2','top6x2','top10x2','top3x3')","('repeat1','repeat2','top5x2','top6x2','top10x2','top3x3','rr','contig','snake','paired')")
oldtpl="""def template(pat):
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
 return g"""
newtpl="""def template(pat):
 if pat in ('rr','contig','snake','paired'):
  bp={
   'rr':[[0,4,8,12,16,20],[1,5,9,13,17,21],[2,6,10,14,18,22],[3,7,11,15,19,23]],
   'contig':[[0,1,2,3,4,5],[6,7,8,9,10,11],[12,13,14,15,16,17],[18,19,20,21,22,23]],
   'snake':[[0,7,8,15,16,23],[1,6,9,14,17,22],[2,5,10,13,18,21],[3,4,11,12,19,20]],
   'paired':[[0,1,8,9,16,17],[2,3,10,11,18,19],[4,5,12,13,20,21],[6,7,14,15,22,23]]}
  return [[0,1,2,3,4,5]]+[[6+j for j in q] for q in bp[pat]]
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
 return g"""
assert oldtpl in src
src=src.replace(oldtpl,newtpl)
oldsel="""new=\"\"\"  if idx<400:
   chosen='H:repeat1'
  else:
   if (idx-400)%50==0:
    def deltas(n,k): return [float(q[k])-float(NULLS[n][k]) for q in list(hist[n])[-150:]]
    def blocks(v): return [statistics.mean(v[i:i+50]) for i in range(0,len(v),50) if len(v[i:i+50])>=40]
    def lb(v):
     if len(v)<40:return -999.
     mu=statistics.mean(v);sd=statistics.stdev(v) if len(v)>1 else 0.;return mu-sd/(len(v)**.5)
    def pos(v):
     b=blocks(v);return sum(x>0 for x in b)/len(b) if b else 0.
    def key(n):
     vm,v2,v3=deltas(n,'max_hits'),deltas(n,'any2'),deltas(n,'any3')
     if not vm:return (-999.,)*7
     lbs=(lb(vm),lb(v2),lb(v3));ps=(pos(vm),pos(v2),pos(v3));means=(statistics.mean(vm),statistics.mean(v2),statistics.mean(v3))
     if mode=='jointlb':return (min(lbs),sum(lbs),min(ps),means[2],means[1],means[0],n)
     if mode=='any2guard':return (ps[1]>=2/3,ps[2]>=.5,lbs[1],lbs[2],lbs[0],means[2],n)
     if mode=='any3guard':return (lbs[2],ps[2],lbs[1],ps[1],lbs[0],means[1],n)
     return (min(ps),min(lbs),sum(lbs),means[1]+1.25*means[2]+.5*means[0],means[2],means[1],n)
    locked=max(NAMES,key=key)
   chosen=locked\"\"\""""
newsel="""new=\"\"\"  if idx<400:
   chosen='H:repeat1'
  else:
   if (idx-400)%50==0:
    def deltas(n,k):return [float(q[k])-float(NULLS[n][k]) for q in list(hist[n])[-150:]]
    def blocks(v):return [statistics.mean(v[i:i+50]) for i in range(0,len(v),50) if len(v[i:i+50])>=40]
    def pos(v):
     b=blocks(v);return sum(x>0 for x in b)/len(b) if b else 0.
    def lb(v):
     if len(v)<40:return -999.
     mu=statistics.mean(v);sd=statistics.stdev(v) if len(v)>1 else 0.;return mu-sd/(len(v)**.5)
    overlap=[n for n in NAMES if n.split(':',1)[1] not in ('rr','contig','snake','paired')]
    rescue=[n for n in NAMES if n.split(':',1)[1] in ('rr','contig','snake','paired')]
    def basekey(n):
     vm,v2,v3=deltas(n,'max_hits'),deltas(n,'any2'),deltas(n,'any3');return (lb(v3),pos(v3),lb(v2),pos(v2),lb(vm),statistics.mean(v2),n)
    base=max(overlap,key=basekey);b2=deltas(base,'any2');recent=statistics.mean(b2[-50:]) if len(b2)>=50 else -999.;ps2=pos(b2)
    trigger=(recent<=0) if mode=='rescue0' else ((recent<=-0.005) if mode=='rescue005' else ((ps2<2/3) if mode=='rescueshare' else (recent<=0 and ps2<2/3)))
    if trigger:
     def rescuekey(n):
      vm,v2,v3=deltas(n,'max_hits'),deltas(n,'any2'),deltas(n,'any3');return (pos(v2),lb(v2),pos(v3)>=.5,pos(vm)>=.5,statistics.mean(v2),statistics.mean(v3),n)
     locked=max(rescue,key=rescuekey)
    else:locked=base
   chosen=locked\"\"\""""
assert oldsel in src
src=src.replace(oldsel,newsel)
src=src.replace("'selection':'V59 {mode}: 12 preregistered H/M overlap policies with geometry-specific exact nulls; selected only at 50-target boundaries from prior <=150 outcomes.'","'selection':'V68 {mode}: V59-style any3 guard is the base expert; only when its prior any2 block degrades does a preregistered disjoint rescue expert replace it for the next 50-target block. All decisions use <=t-1 only and exact geometry nulls.'")
needle="exec(compile(s,str(p),'exec'),globals(),globals())"
patch="""old2=\"'selector_scores':{n:(statistics.mean(hist[n]) if hist[n] else -999.) for n in NAMES}\"\nnew2=\"'selector_scores':{n:({k:statistics.mean(float(q[k]) for q in hist[n]) for k in ('max_hits','any2','any3','winning_union_coverage')} if hist[n] else {}) for n in NAMES}\"\nassert old2 in s\ns=s.replace(old2,new2)\nexec(compile(s,str(p),'exec'),globals(),globals())"""
assert needle in src
src=src.replace(needle,patch)
exec(compile(src,str(p),'exec'),globals(),globals())
