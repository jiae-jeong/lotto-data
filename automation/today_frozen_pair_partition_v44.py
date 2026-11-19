#!/usr/bin/env python3
from pathlib import Path
p=Path(__file__).resolve().parent/'today_frozen_signal_partition_v42.py'
s=p.read_text(encoding='utf-8')
s=s.replace("TODAY_FROZEN_SIGNAL_PARTITION_1248_V42.json","TODAY_FROZEN_PAIR_PARTITION_1248_V44.json")
s=s.replace("SEED=202610301610","SEED=202610301700")
s=s.replace("SIGNALS=('H','G','C','M','P','T')","SIGNALS=('H','P')")
s=s.replace("'FROZEN_V4_SIGNAL_PARTITION_V42'","'FROZEN_V4_PAIR_PARTITION_V44'")
s=s.replace("pc=Counter(p for q in nums for p in itertools.combinations(q,2));tc=Counter(t for q in nums for t in itertools.combinations(q,3));PS={x:0. for x in range(1,46)};TS={x:0. for x in range(1,46)}","pc=Counter(p for q in nums for p in itertools.combinations(q,2));PS={x:0. for x in range(1,46)}")
old=""" for tri in itertools.combinations(range(1,46),3):
  x,y,z=tri;e=(20/36)*(2025/1892)*freq[x]*freq[y]*freq[z]/(n*n);v=(tc[tri]-e)/math.sqrt(max(e,1e-12));TS[x]+=v;TS[y]+=v;TS[z]+=v
 return {'G':G,'C':C,'M':M,'P':PS,'T':TS}"""
new=""" return {'G':G,'C':C,'M':M,'P':PS}"""
assert old in s
s=s.replace(old,new)
s=s.replace("'partition_signals':'H plus rolling300 V4_G,V4_C,V4_M,V4_P,V4_T; V4 formulas/mode frozen on 2026-10-09'","'partition_signals':'H plus rolling300 V4_P pair-residual; formula/mode frozen on 2026-10-09'")
s=s.replace("'selection':'24 predeclared signal x partition policies; each target selects highest previous rolling150 fixed V28 objective only'","'selection':'8 predeclared H/P x partition policies; each target selects highest previous rolling150 fixed V28 objective only'")
exec(compile(s,str(p),'exec'),globals(),globals())
