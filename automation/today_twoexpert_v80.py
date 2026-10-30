#!/usr/bin/env python3
from pathlib import Path
p=Path(__file__).resolve().parent/'today_expanded_overlap_v76.py'
outer=p.read_text(encoding='utf-8')
outer=outer.replace('TODAY_EXPANDED_OVERLAP_1248_V76.json','TODAY_TWOEXPERT_1248_V80.json')
outer=outer.replace("'EXPANDED_OVERLAP_V76'","'TWOEXPERT_V80'")
needle="exec(compile(src,str(p),'exec'),globals(),globals())"
inject="""expanded=\"('repeat1','repeat2','top5x2','top6x2','top10x2','top3x3','x1','x2','x3','x4','x5','triple1','triple2')\"
assert expanded in src
src=src.replace(expanded,\"('top6x2','x2')\")
assert \"SIGNALS=('H','M')\" in src
src=src.replace(\"SIGNALS=('H','M')\",\"SIGNALS=('H',)\")
oldline=\"     if mode=='any3guard':return (lbs[2],ps[2],lbs[1],ps[1],lbs[0],means[1],n)\"
newline=\"     if mode=='any3guard':return (lbs[2]>0,ps[2]>=2/3,lbs[0]>0,ps[0]>=2/3,ps[1],lbs[1],means[1],means[2],means[0],n)\"
assert oldline in src
src=src.replace(oldline,newline)
src=src.replace(\"'selection':'V76 fixed any3guard selector over 26 preregistered H/M heavy+intermediate overlap experts; every 50-target choice uses only prior <=150 outcomes; geometry-specific exact null and strict gate unchanged.'\",\"'selection':'V80 low-variance two-expert policy: only H:top6x2 and H:x2 are eligible. Every 50-target lock uses prior <=150 outcomes, protecting any3/max then optimizing any2; exact geometry null and strict gate unchanged.'\")
exec(compile(src,str(p),'exec'),globals(),globals())"""
assert needle in outer
outer=outer.replace(needle,inject)
exec(compile(outer,str(p),'exec'),globals(),globals())
