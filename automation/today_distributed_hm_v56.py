#!/usr/bin/env python3
import os
from pathlib import Path
p=Path(__file__).resolve().parent/'today_frozen_signal_partition_v42.py'
s=p.read_text(encoding='utf-8')
policy=os.environ.get('DIST_POLICY','H:rr')
tag=policy.replace(':','_')
s=s.replace("TODAY_FROZEN_SIGNAL_PARTITION_1248_V42.json",f"TODAY_DISTRIBUTED_HM_{tag}_1248_V56.json")
s=s.replace("SEED=202610301610","SEED=202610301256")
s=s.replace("SIGNALS=('H','G','C','M','P','T')","SIGNALS=('H','M')")
s=s.replace("'FROZEN_V4_SIGNAL_PARTITION_V42'","'DISTRIBUTED_HM_V56'")
s=s.replace("pc=Counter(p for q in nums for p in itertools.combinations(q,2));tc=Counter(t for q in nums for t in itertools.combinations(q,3));PS={x:0. for x in range(1,46)};TS={x:0. for x in range(1,46)}","pc=Counter(p for q in nums for p in itertools.combinations(q,2));PS={x:0. for x in range(1,46)}")
oldtri=""" for tri in itertools.combinations(range(1,46),3):
  x,y,z=tri;e=(20/36)*(2025/1892)*freq[x]*freq[y]*freq[z]/(n*n);v=(tc[tri]-e)/math.sqrt(max(e,1e-12));TS[x]+=v;TS[y]+=v;TS[z]+=v
 return {'G':G,'C':C,'M':M,'P':PS,'T':TS}"""
assert oldtri in s
s=s.replace(oldtri,""" return {'G':G,'C':C,'M':M,'P':PS}""")
oldlines="""def lines(core,tail_order,pat):
 L=[tuple(sorted(core))]+[tuple(sorted(tail_order[j] for j in p)) for p in PAT[pat]]
 assert len(L)==5 and len(set(L))==5 and len(set().union(*map(set,L)))==30 and all(len(x)==6 for x in L);return L"""
newlines="""def lines(core,tail_order,pat):
 order=list(core)+list(tail_order)
 assert len(order)==30 and len(set(order))==30
 if pat=='rr':
  groups=[[order[i+5*j] for j in range(6)] for i in range(5)]
 elif pat=='contig':
  groups=[order[6*i:6*(i+1)] for i in range(5)]
 elif pat=='snake':
  groups=[[] for _ in range(5)]
  for j,n in enumerate(order):
   row,col=divmod(j,5); groups[col if row%2==0 else 4-col].append(n)
 else:
  perm=[order[(7*j)%30] for j in range(30)]
  groups=[perm[6*i:6*(i+1)] for i in range(5)]
 L=[tuple(sorted(g)) for g in groups]
 assert len(L)==5 and len(set(L))==5 and len(set().union(*map(set,L)))==30 and all(len(x)==6 and len(set(x))==6 for x in L)
 return L"""
assert oldlines in s
s=s.replace(oldlines,newlines)
old="""  if idx<320:chosen='H:rr'
  else:
   def score_name(n):return statistics.mean(hist[n]) if hist[n] else -999.
   chosen=max(NAMES,key=lambda n:(score_name(n),n=='H:rr',n))"""
new="""  if idx<400: chosen='H:rr'
  else: chosen=policy"""
assert old in s
s=s.replace(old,new)
s=s.replace("'selection':'24 predeclared signal x partition policies; each target selects highest previous rolling150 fixed V28 objective only'",f"'selection':'V56 preregistered static distributed-core policy {policy}; all 30 candidates unique, 5 disjoint lines, exact null and strict gate unchanged.'")
s=s.replace("'geometry':'Every candidate is 5 disjoint lines, union30; exact matched-label null identical to V38 unique30 geometry'","'geometry':'V56 redistributes core+tail across all five disjoint lines; union30 and exact matched-label null remain identical to V38 unique30 geometry'")
exec(compile(s,str(p),'exec'),globals(),globals())
