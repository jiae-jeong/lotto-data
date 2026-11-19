#!/usr/bin/env python3
from pathlib import Path
p=Path(__file__).resolve().parent/'today_expanded_overlap_v76.py'
outer=p.read_text(encoding='utf-8')
outer=outer.replace('TODAY_EXPANDED_OVERLAP_1248_V76.json','TODAY_HONLY_EXPANDED_1248_V79.json')
outer=outer.replace("'EXPANDED_OVERLAP_V76'","'HONLY_EXPANDED_V79'")
needle="exec(compile(src,str(p),'exec'),globals(),globals())"
inject="""assert \"SIGNALS=('H','M')\" in src
src=src.replace(\"SIGNALS=('H','M')\",\"SIGNALS=('H',)\")
src=src.replace(\"'selection':'V76 fixed any3guard selector over 26 preregistered H/M heavy+intermediate overlap experts; every 50-target choice uses only prior <=150 outcomes; geometry-specific exact null and strict gate unchanged.'\",\"'selection':'V79 H-only expanded any3guard: 13 H heavy+intermediate overlap experts, locked every 50 targets from prior <=150 outcomes; exact geometry null and strict gate unchanged.'\")
exec(compile(src,str(p),'exec'),globals(),globals())"""
assert needle in outer
outer=outer.replace(needle,inject)
exec(compile(outer,str(p),'exec'),globals(),globals())
