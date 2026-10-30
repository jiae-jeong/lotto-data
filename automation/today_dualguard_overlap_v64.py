#!/usr/bin/env python3
import os
from pathlib import Path
p=Path(__file__).resolve().parent/'today_overlap_adaptive_v59.py'
src=p.read_text(encoding='utf-8')
mode=os.environ.get('DUAL_MODE','dualguard')
os.environ['OVERLAP_ADAPT_MODE']=mode
src=src.replace('TODAY_OVERLAP_ADAPTIVE_{mode}_1248_V59.json','TODAY_DUALGUARD_OVERLAP_{mode}_1248_V64.json')
src=src.replace("'OVERLAP_ADAPTIVE_V59'","'DUALGUARD_OVERLAP_V64'")
old="""     if mode=='jointlb':return (min(lbs),sum(lbs),min(ps),means[2],means[1],means[0],n)
     if mode=='any2guard':return (ps[1]>=2/3,ps[2]>=.5,lbs[1],lbs[2],lbs[0],means[2],n)
     if mode=='any3guard':return (lbs[2],ps[2],lbs[1],ps[1],lbs[0],means[1],n)
     return (min(ps),min(lbs),sum(lbs),means[1]+1.25*means[2]+.5*means[0],means[2],means[1],n)"""
new="""     if mode=='dualguard':return (ps[2]>=2/3,ps[0]>=2/3,ps[1]>=2/3,lbs[1],lbs[2],lbs[0],sum(lbs),n)
     if mode=='any2lift':return (lbs[2]>0,lbs[0]>0,ps[1]>=2/3,lbs[1],ps[2],ps[0],sum(lbs),n)
     if mode=='triguard':return (ps[1]>=2/3,ps[2]>=2/3,ps[0]>=2/3,min(lbs),sum(lbs),means[1]+means[2]+.5*means[0],n)
     if mode=='pareto':return (min(ps),min(lbs),lbs[1]+lbs[2]+.5*lbs[0],means[1]+means[2]+.5*means[0],ps[1],ps[2],n)
     return (ps[2]>=2/3,ps[1]>=2/3,lbs[1],lbs[2],lbs[0],sum(means),n)"""
assert old in src
src=src.replace(old,new)
src=src.replace("'selection':'V59 {mode}: 12 preregistered H/M overlap policies with geometry-specific exact nulls; selected only at 50-target boundaries from prior <=150 outcomes.'","'selection':'V64 {mode}: dual-guard preregistered selector over the same 12 overlap experts; locked every 50 targets from prior <=150 only; exact null and strict gate unchanged.'")
# Repair selector_scores serialization directly, as in V59fix.
needle="exec(compile(s,str(p),'exec'),globals(),globals())"
patch="""old2=\"'selector_scores':{n:(statistics.mean(hist[n]) if hist[n] else -999.) for n in NAMES}\"\nnew2=\"'selector_scores':{n:({k:statistics.mean(float(q[k]) for q in hist[n]) for k in ('max_hits','any2','any3','winning_union_coverage')} if hist[n] else {}) for n in NAMES}\"\nassert old2 in s\ns=s.replace(old2,new2)\nexec(compile(s,str(p),'exec'),globals(),globals())"""
assert needle in src
src=src.replace(needle,patch)
exec(compile(src,str(p),'exec'),globals(),globals())
