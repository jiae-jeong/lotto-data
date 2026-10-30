#!/usr/bin/env python3
from pathlib import Path
p=Path(__file__).resolve().parent/'today_overlap_adaptive_v59.py'
src=p.read_text(encoding='utf-8')
needle="exec(compile(s,str(p),'exec'),globals(),globals())"
patch="""old2=\"'selector_scores':{n:(statistics.mean(hist[n]) if hist[n] else -999.) for n in NAMES}\"\nnew2=\"'selector_scores':{n:({k:statistics.mean(float(q[k]) for q in hist[n]) for k in ('max_hits','any2','any3','winning_union_coverage')} if hist[n] else {}) for n in NAMES}\"\nassert old2 in s\ns=s.replace(old2,new2)\nexec(compile(s,str(p),'exec'),globals(),globals())"""
assert needle in src
src=src.replace(needle,patch)
exec(compile(src,str(p),'exec'),globals(),globals())
