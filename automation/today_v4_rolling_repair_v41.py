#!/usr/bin/env python3
from pathlib import Path
p=Path(__file__).resolve().parent/'today_v4_repair_selector_v39.py'
s=p.read_text(encoding='utf-8')
s=s.replace("TODAY_V4_REPAIR_SELECTOR_1248_V39.json","TODAY_V4_ROLLING_REPAIR_1248_V41.json")
s=s.replace("SEED=202610301430","SEED=202610301530")
s=s.replace("CANDIDATE_NAMES=('base','G1E','C1E','M1E','P1E','G1R','C1R','M1R','P1R','GC2E','GP2E','CM2E','GC2R','GP2R','CM2R','GCMP4E','GCMP4R')","CANDIDATE_NAMES=('base','G1R','C1R','M1R','P1R','GC2R','GP2R','CM2R','GCMP4R')")
s=s.replace("svE=frozen_v4_scores(nums_all);svR=frozen_v4_scores(nums_all[-300:]);tix={'E':{k:ticket(v) for k,v in svE.items()},'R':{k:ticket(v) for k,v in svR.items()}}","svR=frozen_v4_scores(nums_all[-300:]);tix={'R':{k:ticket(v) for k,v in svR.items()}}")
s=s.replace("om=met(Q,actual);nm=exact_null(Q);thist[k].append(obj_delta(om,nm))","om=met(Q,actual);thist[k].append(om['max_hits']+.85*om['any2']+1.35*om['any3']+.10*om['winning_union_coverage'])")
s=s.replace("om=met(Q,actual);nm=exact_null(Q);cand_hist[name].append(obj_delta(om,nm))","om=met(Q,actual);cand_hist[name].append(om['max_hits']+.85*om['any2']+1.35*om['any3']+.10*om['winning_union_coverage'])")
s=s.replace("'FROZEN_V4_REPAIR_SELECTOR_V39'","'FROZEN_V4_ROLLING_REPAIR_V41'")
s=s.replace("'independent_repairs':'Only formulas frozen in research/prospective_v4 on 2026-10-09: V4_G,V4_C,V4_M,V4_P; expanding and frozen rolling300 modes'","'independent_repairs':'Only formulas and rolling300 mode frozen in research/prospective_v4 on 2026-10-09: V4_G,V4_C,V4_M,V4_P'")
s=s.replace("'selector':'At each target choose from finite predeclared repair family using only previous <=150 outcome deltas; robust score=mean-0.5*SE; base retained unless challenger exceeds base'","'selector':'At each target choose from the finite rolling300 repair family using only previous <=150 raw outcome scores; robust score=mean-0.5*SE; base retained unless challenger exceeds base. Exact matched-label null is applied to the selected outer policy only.'")
exec(compile(s,str(p),'exec'),globals(),globals())
