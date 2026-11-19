#!/usr/bin/env python3
from pathlib import Path
p=Path(__file__).resolve().parent/'today_frozen_signal_partition_v42.py'
s=p.read_text(encoding='utf-8')
s=s.replace("TODAY_FROZEN_SIGNAL_PARTITION_1248_V42.json","TODAY_BLOCKLOCKED_BALANCED_HM_1248_V49.json")
s=s.replace("SEED=202610301610","SEED=202610302030")
s=s.replace("SIGNALS=('H','G','C','M','P','T')","SIGNALS=('H','M')")
s=s.replace("'FROZEN_V4_SIGNAL_PARTITION_V42'","'BLOCKLOCKED_BALANCED_HM_V49'")
s=s.replace("pc=Counter(p for q in nums for p in itertools.combinations(q,2));tc=Counter(t for q in nums for t in itertools.combinations(q,3));PS={x:0. for x in range(1,46)};TS={x:0. for x in range(1,46)}","pc=Counter(p for q in nums for p in itertools.combinations(q,2));PS={x:0. for x in range(1,46)}")
oldtri=""" for tri in itertools.combinations(range(1,46),3):
  x,y,z=tri;e=(20/36)*(2025/1892)*freq[x]*freq[y]*freq[z]/(n*n);v=(tc[tri]-e)/math.sqrt(max(e,1e-12));TS[x]+=v;TS[y]+=v;TS[z]+=v
 return {'G':G,'C':C,'M':M,'P':PS,'T':TS}"""
assert oldtri in s
s=s.replace(oldtri,""" return {'G':G,'C':C,'M':M,'P':PS}""")
# Store per-metric history and add a persistent 50-target lock.
s=s.replace("hist={k:deque(maxlen=ROLL) for k in NAMES};obs=[];diff=", "hist={k:deque(maxlen=ROLL) for k in NAMES};locked='H:rr';obs=[];diff=")
old="""  if idx<320:chosen='H:rr'
  else:
   def score_name(n):return statistics.mean(hist[n]) if hist[n] else -999.
   chosen=max(NAMES,key=lambda n:(score_name(n),n=='H:rr',n))"""
new="""  if idx<400:
   chosen='H:rr'
  else:
   if (idx-400)%50==0:
    def robust_tuple(n):
     x=list(hist[n])[-ROLL:]
     if len(x)<50:return (-999.,-999.,-999.)
     out=[]
     for k in ('max_hits','any2','any3'):
      vals=[float(q[k]) for q in x]
      mu=statistics.mean(vals)-float(NULL[k])
      se=statistics.pstdev(vals)/math.sqrt(len(vals)) if len(vals)>1 else 1.0
      out.append(mu/max(se,1e-9))
     return tuple(out)
    def key(n):
     z=robust_tuple(n)
     return (min(z),sum(z),z[2],z[1],n=='H:rr',n)
    locked=max(NAMES,key=key)
   chosen=locked"""
assert old in s
s=s.replace(old,new)
s=s.replace("for n,Q in policies.items():hist[n].append(obj(met(Q,actual)))","for n,Q in policies.items():hist[n].append(met(Q,actual))")
old2="'selector_scores':{n:(statistics.mean(hist[n]) if hist[n] else -999.) for n in NAMES}"
new2="'selector_scores':{n:({k:statistics.mean(float(q[k]) for q in hist[n]) for k in ('max_hits','any2','any3','winning_union_coverage')} if hist[n] else {}) for n in NAMES}"
assert old2 in s
s=s.replace(old2,new2)
s=s.replace("'partition_signals':'H plus rolling300 V4_G,V4_C,V4_M,V4_P,V4_T; V4 formulas/mode frozen on 2026-10-09'","'partition_signals':'H plus rolling300 V4_M momentum; V4_M formula/mode frozen on 2026-10-09'")
s=s.replace("'selection':'24 predeclared signal x partition policies; each target selects highest previous rolling150 fixed V28 objective only'","'selection':'8 predeclared H/M x partition policies. At each 50-target block boundary, use only the prior <=150 outcomes. For each policy compute t-like prior advantages over the identical exact null for max_hits, any2, any3; choose the policy maximizing its weakest of the three, then lock it for the entire next 50-target block. Gate unchanged.'")
exec(compile(s,str(p),'exec'),globals(),globals())
