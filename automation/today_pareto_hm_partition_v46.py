#!/usr/bin/env python3
from pathlib import Path
p=Path(__file__).resolve().parent/'today_frozen_pair_partition_v44.py'
s=p.read_text(encoding='utf-8')
s=s.replace("TODAY_FROZEN_PAIR_PARTITION_1248_V44.json","TODAY_PARETO_HM_PARTITION_1248_V46.json")
s=s.replace("SEED=202610301700","SEED=202610301800")
s=s.replace("SIGNALS=('H','P')","SIGNALS=('H','M')")
s=s.replace("'FROZEN_V4_PAIR_PARTITION_V44'","'PARETO_FROZEN_HM_PARTITION_V46'")
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
s=s.replace("'partition_signals':'H plus rolling300 V4_P pair-residual; formula/mode frozen on 2026-10-09'","'partition_signals':'H plus rolling300 V4_M momentum; V4_M formula/mode frozen on 2026-10-09'")
s=s.replace("'selection':'8 predeclared H/P x partition policies; each target selects highest previous rolling150 fixed V28 objective only'","'selection':'8 predeclared H/M x partition policies. At each target take best H baseline by prior rolling150; M may replace it only when prior rolling150 max_hits, any2, any3 are all no worse. Among feasible maximize any2 then any3 then fixed V28 objective.'")
exec(compile(s,str(p),'exec'),globals(),globals())
