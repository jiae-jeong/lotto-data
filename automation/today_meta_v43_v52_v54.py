#!/usr/bin/env python3
from pathlib import Path
p=Path(__file__).resolve().parent/'today_frozen_signal_partition_v42.py'
s=p.read_text(encoding='utf-8')
s=s.replace("TODAY_FROZEN_SIGNAL_PARTITION_1248_V42.json","TODAY_META_V43_V52_1248_V54.json")
s=s.replace("SEED=202610301610","SEED=202610301154")
s=s.replace("'FROZEN_V4_SIGNAL_PARTITION_V42'","'META_V43_V52_V54'")
s=s.replace("hist={k:deque(maxlen=ROLL) for k in NAMES};obs=[];diff=", "hist={k:deque(maxlen=ROLL) for k in NAMES};hist52={k:deque(maxlen=ROLL) for k in NAMES if k.startswith(('H:','M:'))};locked52='H:rr';meta_locked='V52';meta43=deque(maxlen=50);meta52=deque(maxlen=50);obs=[];diff=")
old="""  if idx<320:chosen='H:rr'
  else:
   def score_name(n):return statistics.mean(hist[n]) if hist[n] else -999.
   chosen=max(NAMES,key=lambda n:(score_name(n),n=='H:rr',n))
  L=policies[chosen]"""
new="""  if idx<320:
   chosen43='H:rr'
  else:
   def score43(n):
    x=list(hist[n])[-ROLL:]
    if not x:return -999.
    return statistics.mean(x)-.5*(statistics.pstdev(x)/math.sqrt(len(x)) if len(x)>1 else 0.)
   chosen43=max(NAMES,key=lambda n:(score43(n),n=='H:rr',n))
  if idx<400:
   chosen52='H:rr'
  else:
   if (idx-400)%50==0:
    if idx>400 and meta43 and meta52:
     def mav(q,k):return statistics.mean(float(x[k]) for x in q)
     d=(2*(mav(meta52,'max_hits')-mav(meta43,'max_hits'))+4*(mav(meta52,'any2')-mav(meta43,'any2'))+3*(mav(meta52,'any3')-mav(meta43,'any3')))/9.0
     meta_locked='V52' if d>-0.03 else 'V43'
     meta43.clear();meta52.clear()
    def block_stats52(n,k):
     vals=[float(q[k])-float(NULL[k]) for q in list(hist52[n])[-150:]]
     return [statistics.mean(vals[i:i+50]) for i in range(0,len(vals),50) if len(vals[i:i+50])>=40]
    def key52(n):
     bm=block_stats52(n,'max_hits');b2=block_stats52(n,'any2');b3=block_stats52(n,'any3')
     if not bm or not b2 or not b3:return (-999.,)*6
     floors=[min(bm),min(b2),min(b3)]
     return (min(floors),sum(floors),statistics.mean(b3),statistics.mean(b2),n=='H:rr',n)
    locked52=max(hist52,key=key52)
   chosen52=locked52
  L43=policies[chosen43];L52=policies[chosen52]
  chosen=chosen52 if meta_locked=='V52' else chosen43
  L=L52 if meta_locked=='V52' else L43"""
assert old in s
s=s.replace(old,new)
old2="for n,Q in policies.items():hist[n].append(obj(met(Q,actual)))"
new2="""for n,Q in policies.items():
   mm=met(Q,actual);hist[n].append(obj(mm))
   if n in hist52:hist52[n].append(mm)
  if target>=401:
   meta43.append(met(L43,actual));meta52.append(met(L52,actual))"""
assert old2 in s
s=s.replace(old2,new2)
s=s.replace("'selection':'24 predeclared signal x partition policies; each target selects highest previous rolling150 fixed V28 objective only'","'selection':'V54 meta-selector: V43 robust 24-policy expert versus V52 balanced H/M block-locked expert. First outer block uses V52; thereafter at each 50-target boundary use only the immediately prior completed block. Keep V52 unless its weighted prior-block disadvantage 2*max+4*any2+3*any3 exceeds 0.03; otherwise use V43. Both child experts evolve independently from prior outcomes only. Gate unchanged.'")
s=s.replace("'current':current,'walkforward_targets'", "'meta_current':meta_locked,'current':current,'walkforward_targets'")
exec(compile(s,str(p),'exec'),globals(),globals())
