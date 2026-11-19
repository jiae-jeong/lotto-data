#!/usr/bin/env python3
from pathlib import Path
p=Path(__file__).resolve().parent/'today_frozen_signal_partition_v42.py'
s=p.read_text(encoding='utf-8')
s=s.replace("TODAY_FROZEN_SIGNAL_PARTITION_1248_V42.json","TODAY_FROZEN_SIGNAL_PARTITION_ROBUST_1248_V43.json")
s=s.replace("SEED=202610301610","SEED=202610301640")
s=s.replace("'FROZEN_V4_SIGNAL_PARTITION_V42'","'FROZEN_V4_SIGNAL_PARTITION_ROBUST_V43'")
old="def score_name(n):return statistics.mean(hist[n]) if hist[n] else -999.\n   chosen=max(NAMES,key=lambda n:(score_name(n),n=='H:rr',n))"
new="def score_name(n):\n    x=list(hist[n])[-ROLL:]\n    if not x:return -999.\n    return statistics.mean(x)-.5*(statistics.pstdev(x)/math.sqrt(len(x)) if len(x)>1 else 0.)\n   chosen=max(NAMES,key=lambda n:(score_name(n),n=='H:rr',n))"
assert old in s
s=s.replace(old,new)
s=s.replace("'selection':'24 predeclared signal x partition policies; each target selects highest previous rolling150 fixed V28 objective only'","'selection':'24 predeclared signal x partition policies; each target selects the highest robust previous rolling150 fixed V28 objective, mean minus 0.5 standard-error, using only prior outcomes'")
exec(compile(s,str(p),'exec'),globals(),globals())
