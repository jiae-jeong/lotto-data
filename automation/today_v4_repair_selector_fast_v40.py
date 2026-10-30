#!/usr/bin/env python3
from pathlib import Path
p=Path(__file__).resolve().parent/'today_v4_repair_selector_v39.py'
s=p.read_text(encoding='utf-8')
s=s.replace("TODAY_V4_REPAIR_SELECTOR_1248_V39.json","TODAY_V4_REPAIR_SELECTOR_FAST_1248_V40.json")
s=s.replace("SEED=202610301430","SEED=202610301500")
s=s.replace("'FROZEN_V4_REPAIR_SELECTOR_V39'","'FROZEN_V4_REPAIR_SELECTOR_FAST_V40'")
s=s.replace("om=met(Q,actual);nm=exact_null(Q);thist[k].append(obj_delta(om,nm))","om=met(Q,actual);thist[k].append(om['max_hits']+.85*om['any2']+1.35*om['any3']+.10*om['winning_union_coverage'])")
s=s.replace("om=met(Q,actual);nm=exact_null(Q);cand_hist[name].append(obj_delta(om,nm))","om=met(Q,actual);cand_hist[name].append(om['max_hits']+.85*om['any2']+1.35*om['any3']+.10*om['winning_union_coverage'])")
s=s.replace("'selector':'At each target choose from finite predeclared repair family using only previous <=150 outcome deltas; robust score=mean-0.5*SE; base retained unless challenger exceeds base'","'selector':'At each target choose from finite predeclared repair family using only previous <=150 raw outcome scores; robust score=mean-0.5*SE; base retained unless challenger exceeds base. Exact matched-label null is used only for the actually selected outer policy, preserving the strict gate while avoiding candidate-screening DP cost.'")
exec(compile(s,str(p),'exec'),globals(),globals())
