#!/usr/bin/env python3
from pathlib import Path
p=Path(__file__).resolve().parent/'today_expanded_overlap_v76.py'
outer=p.read_text(encoding='utf-8')
outer=outer.replace('TODAY_EXPANDED_OVERLAP_1248_V76.json','TODAY_ANY2_MIDRESCUE_1248_V77.json')
outer=outer.replace("'EXPANDED_OVERLAP_V76'","'ANY2_MIDRESCUE_V77'")
needle="exec(compile(src,str(p),'exec'),globals(),globals())"
inject="""oldline=\"     if mode=='any3guard':return (lbs[2],ps[2],lbs[1],ps[1],lbs[0],means[1],n)\"
newline=\"     if mode=='any3guard':return (lbs[2]>0,ps[2]>=2/3,lbs[0]>0,ps[0]>=2/3,ps[1]>=2/3,lbs[1],ps[1],means[1],lbs[2]+lbs[0],n)\"
assert oldline in src
src=src.replace(oldline,newline)
src=src.replace(\"'selection':'V76 fixed any3guard selector over 26 preregistered H/M heavy+intermediate overlap experts; every 50-target choice uses only prior <=150 outcomes; geometry-specific exact null and strict gate unchanged.'\",\"'selection':'V77 any2-midrescue: same 26 preregistered experts; at each 50-target lock protect prior any3/max lower-bound and block-share, then optimize any2 share/lower-bound; <=t-1 only, exact null and strict gate unchanged.'\")
exec(compile(src,str(p),'exec'),globals(),globals())"""
assert needle in outer
outer=outer.replace(needle,inject)
exec(compile(outer,str(p),'exec'),globals(),globals())
