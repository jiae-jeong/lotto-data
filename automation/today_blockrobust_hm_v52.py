#!/usr/bin/env python3
import os
from pathlib import Path
p=Path(__file__).resolve().parent/'today_frozen_signal_partition_v42.py'
s=p.read_text(encoding='utf-8')
mode=os.environ.get('ROBUST_MODE','minblock')
tag=os.environ.get('ROBUST_TAG',mode)
s=s.replace("TODAY_FROZEN_SIGNAL_PARTITION_1248_V42.json",f"TODAY_BLOCKROBUST_HM_{tag}_1248_V52.json")
s=s.replace("SEED=202610301610","SEED=202610301052")
s=s.replace("SIGNALS=('H','G','C','M','P','T')","SIGNALS=('H','M')")
s=s.replace("'FROZEN_V4_SIGNAL_PARTITION_V42'","'BLOCKROBUST_HM_V52'")
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
new="""  if idx<400:
   chosen='H:rr'
  else:
   if (idx-400)%50==0:
    def block_stats(n,k):
     vals=[float(q[k])-float(NULL[k]) for q in list(hist[n])[-150:]]
     blocks=[statistics.mean(vals[i:i+50]) for i in range(0,len(vals),50) if len(vals[i:i+50])>=40]
     return blocks
    def key(n):
     bm=block_stats(n,'max_hits'); b2=block_stats(n,'any2'); b3=block_stats(n,'any3')
     if not bm or not b2 or not b3:return (-999.,)*6
     if mode=='minblock':
      return (min(b3),min(b2),min(bm),statistics.mean(b3),statistics.mean(b2),n=='H:rr')
     if mode=='balanced':
      floors=[min(bm),min(b2),min(b3)]
      return (min(floors),sum(floors),statistics.mean(b3),statistics.mean(b2),n=='H:rr',n)
     if mode=='any3first':
      return (min(b3),statistics.mean(b3),min(b2),statistics.mean(b2),min(bm),n=='H:rr')
     if mode=='positiveblocks':
      pos=lambda z:sum(x>0 for x in z)/len(z)
      return (min(pos(b2),pos(b3)),pos(b3),pos(b2),min(b3),min(b2),n=='H:rr')
     return (min(b3),min(b2),min(bm),statistics.mean(b3),statistics.mean(b2),n=='H:rr')
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
s=s.replace("'selection':'24 predeclared signal x partition policies; each target selects highest previous rolling150 fixed V28 objective only'",f"'selection':'V52 {mode}: 8 predeclared H/M x partition policies; at each 50-target boundary choose using only prior 150 outcomes and prior 50-target block robustness. Gate unchanged.'")
exec(compile(s,str(p),'exec'),globals(),globals())
