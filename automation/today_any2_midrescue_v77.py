#!/usr/bin/env python3
import os
from pathlib import Path
p=Path(__file__).resolve().parent/'today_expanded_overlap_v76.py'
src=p.read_text(encoding='utf-8')
# Keep V76's finite heavy+intermediate expert family but replace the V59 any3guard key
# with a preregistered two-stage guard: preserve max/any3 first, then maximize any2.
src=src.replace('TODAY_EXPANDED_OVERLAP_1248_V76.json','TODAY_ANY2_MIDRESCUE_1248_V77.json')
src=src.replace("'EXPANDED_OVERLAP_V76'","'ANY2_MIDRESCUE_V77'")
old="""     if mode=='jointlb':return (min(lbs),sum(lbs),min(ps),means[2],means[1],means[0],n)
     if mode=='any2guard':return (ps[1]>=2/3,ps[2]>=.5,lbs[1],lbs[2],lbs[0],means[2],n)
     if mode=='any3guard':return (lbs[2],ps[2],lbs[1],ps[1],lbs[0],means[1],n)
     return (min(ps),min(lbs),sum(lbs),means[1]+1.25*means[2]+.5*means[0],means[2],means[1],n)"""
new="""     # V77: protect the two metrics already strongest in V59, then optimize the any2 bottleneck.
     # All quantities are prior-window only; the next 50-target block is locked before outcomes.
     return (lbs[2]>0, ps[2]>=2/3, lbs[0]>0, ps[0]>=2/3, ps[1]>=2/3, lbs[1], ps[1], means[1], lbs[2]+lbs[0], n)"""
assert old in src
src=src.replace(old,new)
src=src.replace("'selection':'V76 fixed any3guard selector over 26 preregistered H/M heavy+intermediate overlap experts; every 50-target choice uses only prior <=150 outcomes; geometry-specific exact null and strict gate unchanged.'","'selection':'V77 any2-midrescue: same finite 26 H/M heavy+intermediate overlap experts. At each 50-target boundary, prior <=150 outcomes first protect any3 and max-hit lower-bound/share, then optimize the any2 share/lower-bound bottleneck. Geometry-specific exact null and strict gate unchanged.'")
exec(compile(src,str(p),'exec'),globals(),globals())
