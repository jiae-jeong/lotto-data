#!/usr/bin/env python3
from pathlib import Path
import os
ADV=float(os.environ.get('ANY2_ADV','0.00'))
TOL3=float(os.environ.get('ANY3_TOL','0.00'))
assert ADV in (0.0,0.01,0.02,0.03)
assert TOL3 in (0.0,0.01)
tag=f"a{int(round(ADV*100)):02d}_t{int(round(TOL3*100)):02d}"
p=Path(__file__).resolve().parent/'today_frozen_signal_partition_v42.py'
s=p.read_text(encoding='utf-8')
s=s.replace("TODAY_FROZEN_SIGNAL_PARTITION_1248_V42.json",f"TODAY_BLOCKLOCKED_HYSTERESIS_HM_{tag}_1248_V51.json")
s=s.replace("SEED=202610301610",f"SEED={202610302200 + int(ADV*100)*10 + int(TOL3*100)}")
s=s.replace("SIGNALS=('H','G','C','M','P','T')","SIGNALS=('H','M')")
s=s.replace("'FROZEN_V4_SIGNAL_PARTITION_V42'",f"'BLOCKLOCKED_HYSTERESIS_HM_V51_{tag}'")
s=s.replace("pc=Counter(p for q in nums for p in itertools.combinations(q,2));tc=Counter(t for q in nums for t in itertools.combinations(q,3));PS={x:0. for x in range(1,46)};TS={x:0. for x in range(1,46)}","pc=Counter(p for q in nums for p in itertools.combinations(q,2));PS={x:0. for x in range(1,46)}")
oldtri=""" for tri in itertools.combinations(range(1,46),3):
  x,y,z=tri;e=(20/36)*(2025/1892)*freq[x]*freq[y]*freq[z]/(n*n);v=(tc[tri]-e)/math.sqrt(max(e,1e-12));TS[x]+=v;TS[y]+=v;TS[z]+=v
 return {'G':G,'C':C,'M':M,'P':PS,'T':TS}"""
assert oldtri in s
s=s.replace(oldtri,""" return {'G':G,'C':C,'M':M,'P':PS}""")
s=s.replace("hist={k:deque(maxlen=ROLL) for k in NAMES};obs=[];diff=", "hist={k:deque(maxlen=ROLL) for k in NAMES};locked='H:rr';obs=[];diff=")
old="""  if idx<320:chosen='H:rr'
  else:
   def score_name(n):return statistics.mean(hist[n]) if hist[n] else -999.
   chosen=max(NAMES,key=lambda n:(score_name(n),n=='H:rr',n))"""
new=f"""  if idx<400:
   chosen='H:rr'
  else:
   if (idx-400)%50==0:
    def means(n):
     x=list(hist[n])[-ROLL:]
     if len(x)<50:return {{'max_hits':-999.,'any2':-999.,'any3':-999.,'winning_union_coverage':-999.}}
     return {{k:statistics.mean(float(q[k]) for q in x) for k in ('max_hits','any2','any3','winning_union_coverage')}}
    def fixed_score(m):return m['max_hits']+.85*m['any2']+1.35*m['any3']+.10*m['winning_union_coverage']
    hs=[n for n in NAMES if n.startswith('H:')];ms=[n for n in NAMES if n.startswith('M:')]
    h=max(hs,key=lambda n:(fixed_score(means(n)),n=='H:rr',n));m=max(ms,key=lambda n:(fixed_score(means(n)),n))
    hm,mm=means(h),means(m)
    switch=(mm['any2']>=hm['any2']+{ADV!r} and mm['any3']>=hm['any3']-{TOL3!r} and mm['max_hits']>=hm['max_hits'])
    locked=m if switch else h
   chosen=locked"""
assert old in s
s=s.replace(old,new)
s=s.replace("for n,Q in policies.items():hist[n].append(obj(met(Q,actual)))","for n,Q in policies.items():hist[n].append(met(Q,actual))")
old2="'selector_scores':{n:(statistics.mean(hist[n]) if hist[n] else -999.) for n in NAMES}"
new2="'selector_scores':{n:({k:statistics.mean(float(q[k]) for q in hist[n]) for k in ('max_hits','any2','any3','winning_union_coverage')} if hist[n] else {}) for n in NAMES}"
assert old2 in s
s=s.replace(old2,new2)
s=s.replace("'partition_signals':'H plus rolling300 V4_G,V4_C,V4_M,V4_P,V4_T; V4 formulas/mode frozen on 2026-10-09'","'partition_signals':'H plus rolling300 V4_M momentum; V4_M formula/mode frozen on 2026-10-09'")
s=s.replace("'selection':'24 predeclared signal x partition policies; each target selects highest previous rolling150 fixed V28 objective only'",f"'selection':'At each 50-target block boundary choose the best H and best M partition from prior <=150 outcomes by fixed score. Switch H->M only if prior any2 improves by >= {ADV:.2f}, prior any3 is no worse than H by more than {TOL3:.2f}, and prior max_hits is no worse. Lock for the next 50 targets. Exact null and strict gate unchanged.'")
exec(compile(s,str(p),'exec'),globals(),globals())
