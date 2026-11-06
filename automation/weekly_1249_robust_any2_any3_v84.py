#!/usr/bin/env python3
"""V84 exploratory robust selector. Fixed before this execution.
The ONLY policy difference vs V83 is the meta-expert selector's score:
maximise the worse of prior150 smoothed any2 and any3 lower z-scores,
plus a small max_hits tie-break. Null, weights inside experts, outcome
windows, bootstrap seed, and strict pass gate stay exactly the same.
A nominal pass on this already-explored historical sample is not an
independent confirmation.
"""
from pathlib import Path
p=Path(__file__).resolve().parent/'weekly_1249_any2_guard_v83.py'
s=p.read_text(encoding='utf-8')
old="return lower+0.15*tail3+0.08*mx"
new="""p3=(sum(float(x['any3']) for x in a)+20*float(NULL['any3']))/(n+20.)
      se2=math.sqrt(max(p*(1.-p),1e-10)/(n+20.))
      se3=math.sqrt(max(p3*(1.-p3),1e-10)/(n+20.))
      return min((lower-float(NULL['any2']))/se2,(p3-se3-float(NULL['any3']))/se3)+0.08*mx"""
assert old in s
s=s.replace(old,new)
oldname="TODAY_ANY2_GUARDED_1249_V83.json"
assert s.count(oldname)>=2
s=s.replace(oldname,"TODAY_ROBUST_ANY2_ANY3_1249_V84.json")
assert "'ANY2_GUARDED_V83'" in s
s=s.replace("'ANY2_GUARDED_V83'","'ROBUST_ANY2_ANY3_V84'")
exec(compile(s,str(p),'exec'),globals(),globals())
