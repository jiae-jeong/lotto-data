#!/usr/bin/env python3
import os
from pathlib import Path
p=Path(__file__).resolve().parent/'today_frozen_signal_partition_v42.py'
s=p.read_text(encoding='utf-8')
mode=os.environ.get('ADAPT_MODE','lowerbound')
tag=mode
s=s.replace("TODAY_FROZEN_SIGNAL_PARTITION_1248_V42.json",f"TODAY_ADAPTIVE_DISTRIBUTED_{tag}_1248_V57.json")
s=s.replace("SEED=202610301610","SEED=202610301357")
s=s.replace("SIGNALS=('H','G','C','M','P','T')","SIGNALS=('H','M')")
s=s.replace("'FROZEN_V4_SIGNAL_PARTITION_V42'","'ADAPTIVE_DISTRIBUTED_V57'")
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
 if pat=='rr': groups=[[order[i+5*j] for j in range(6)] for i in range(5)]
 elif pat=='contig': groups=[order[6*i:6*(i+1)] for i in range(5)]
 elif pat=='snake':
  groups=[[] for _ in range(5)]
  for j,n in enumerate(order):
   row,col=divmod(j,5); groups[col if row%2==0 else 4-col].append(n)
 else:
  perm=[order[(7*j)%30] for j in range(30)]; groups=[perm[6*i:6*(i+1)] for i in range(5)]
 L=[tuple(sorted(g)) for g in groups]
 assert len(L)==5 and len(set(L))==5 and len(set().union(*map(set,L)))==30 and all(len(x)==6 and len(set(x))==6 for x in L)
 return L"""
assert oldlines in s
s=s.replace(oldlines,newlines)
s=s.replace("hist={k:deque(maxlen=ROLL) for k in NAMES};obs=[];diff=", "hist={k:deque(maxlen=ROLL) for k in NAMES};locked='H:rr';obs=[];diff=")
old="""  if idx<320:chosen='H:rr'
  else:
   def score_name(n):return statistics.mean(hist[n]) if hist[n] else -999.
   chosen=max(NAMES,key=lambda n:(score_name(n),n=='H:rr',n))"""
new="""  if idx<400:
   chosen='H:rr'
  else:
   if (idx-400)%50==0:
    def vals(n,k): return [float(q[k])-float(NULL[k]) for q in list(hist[n])[-150:]]
    def blocks(v): return [statistics.mean(v[i:i+50]) for i in range(0,len(v),50) if len(v[i:i+50])>=40]
    def lb(v):
     if len(v)<40:return -999.
     mu=statistics.mean(v); sd=statistics.stdev(v) if len(v)>1 else 0.; return mu-sd/(len(v)**0.5)
    def pos(bs): return sum(x>0 for x in bs)/len(bs) if bs else 0.
    def key(n):
     vm,v2,v3=vals(n,'max_hits'),vals(n,'any2'),vals(n,'any3')
     bm,b2,b3=blocks(vm),blocks(v2),blocks(v3)
     if not bm or not b2 or not b3:return (-999.,)*7
     lbs=(lb(vm),lb(v2),lb(v3)); floors=(min(bm),min(b2),min(b3))
     means=(statistics.mean(vm),statistics.mean(v2),statistics.mean(v3))
     if mode=='lowerbound': return (min(lbs),sum(lbs),min(floors),means[2],means[1],means[0],n=='H:rr')
     if mode=='any2guard': return (pos(b2)>=2/3,pos(b3)>=2/3,lb(v2),lb(v3),lb(vm),min(floors),n=='H:rr')
     if mode=='blockpareto': return (min(pos(bm),pos(b2),pos(b3)),min(floors),sum(floors),means[2],means[1],means[0],n=='H:rr')
     return (min(lbs[0],lbs[1],lbs[2]),min(pos(b2),pos(b3)),means[1]+1.2*means[2]+.5*means[0],min(floors),n=='H:rr',n,'')
    locked=max(NAMES,key=key)
   chosen=locked"""
assert old in s
s=s.replace(old,new)
s=s.replace("for n,Q in policies.items():hist[n].append(obj(met(Q,actual)))","for n,Q in policies.items():hist[n].append(met(Q,actual))")
old2="'selector_scores':{n:(statistics.mean(hist[n]) if hist[n] else -999.) for n in NAMES}"
new2="'selector_scores':{n:({k:statistics.mean(float(q[k]) for q in hist[n]) for k in ('max_hits','any2','any3','winning_union_coverage')} if hist[n] else {}) for n in NAMES}"
assert old2 in s
s=s.replace(old2,new2)
s=s.replace("'selection':'24 predeclared signal x partition policies; each target selects highest previous rolling150 fixed V28 objective only'",f"'selection':'V57 {mode}: 8 preregistered H/M distributed policies; policy locked for each 50-target block using only prior 150 outcomes. Gate unchanged.'")
s=s.replace("'geometry':'Every candidate is 5 disjoint lines, union30; exact matched-label null identical to V38 unique30 geometry'","'geometry':'V57 distributes core+tail over five disjoint lines; union30, exact matched-label null and strict gate unchanged'")
exec(compile(s,str(p),'exec'),globals(),globals())
