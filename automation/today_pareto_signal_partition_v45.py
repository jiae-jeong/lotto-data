#!/usr/bin/env python3
from pathlib import Path
p=Path(__file__).resolve().parent/'today_frozen_signal_partition_v42.py'
s=p.read_text(encoding='utf-8')
s=s.replace("TODAY_FROZEN_SIGNAL_PARTITION_1248_V42.json","TODAY_PARETO_SIGNAL_PARTITION_1248_V45.json")
s=s.replace("SEED=202610301610","SEED=202610301730")
s=s.replace("'FROZEN_V4_SIGNAL_PARTITION_V42'","'PARETO_FROZEN_SIGNAL_PARTITION_V45'")
old="""  if idx<320:chosen='H:rr'
  else:
   def score_name(n):return statistics.mean(hist[n]) if hist[n] else -999.
   chosen=max(NAMES,key=lambda n:(score_name(n),n=='H:rr',n))"""
new="""  if idx<320:chosen='H:rr'
  else:
   def means(n):
    x=list(hist[n])[-ROLL:]
    if not x:return {'max_hits':-999.,'any2':-999.,'any3':-999.,'winning_union_coverage':-999.}
    return {k:statistics.mean(float(q[k]) for q in x) for k in ('max_hits','any2','any3','winning_union_coverage')}
   def score_m(m):return m['max_hits']+.85*m['any2']+1.35*m['any3']+.10*m['winning_union_coverage']
   hnames=tuple(n for n in NAMES if n.startswith('H:'))
   base_name=max(hnames,key=lambda n:(score_m(means(n)),n=='H:rr',n));bm=means(base_name)
   feasible=[]
   for n in NAMES:
    m=means(n)
    if m['max_hits']>=bm['max_hits'] and m['any2']>=bm['any2'] and m['any3']>=bm['any3']:feasible.append(n)
   chosen=max(feasible,key=lambda n:(means(n)['any2'],means(n)['any3'],score_m(means(n)),n==base_name,n)) if feasible else base_name"""
assert old in s;s=s.replace(old,new)
s=s.replace("for n,Q in policies.items():hist[n].append(obj(met(Q,actual)))","for n,Q in policies.items():hist[n].append(met(Q,actual))")
old2="'selector_scores':{n:(statistics.mean(hist[n]) if hist[n] else -999.) for n in NAMES}"
new2="'selector_scores':{n:({k:statistics.mean(float(q[k]) for q in hist[n]) for k in ('max_hits','any2','any3','winning_union_coverage')} if hist[n] else {}) for n in NAMES}"
assert old2 in s;s=s.replace(old2,new2)
s=s.replace("'selection':'24 predeclared signal x partition policies; each target selects highest previous rolling150 fixed V28 objective only'","'selection':'At each target choose the best H partition from prior rolling150; a frozen-signal partition may replace it only if prior rolling150 max_hits, any2 and any3 are all no worse than that H baseline. Among feasible policies maximize any2 then any3 then fixed V28 objective.'")
exec(compile(s,str(p),'exec'),globals(),globals())
