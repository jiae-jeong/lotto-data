#!/usr/bin/env python3
from pathlib import Path
import os

tpl=os.environ.get('FIXED_TEMPLATE','rr')
assert tpl in ('rr','contig','snake','paired')
p=Path(__file__).resolve().parent/'today_repeated_core_v28.py'
s=p.read_text(encoding='utf-8')
s=s.replace("TODAY_REPEATED_CORE_1248_V28.json",f"TODAY_FIXED_H_{tpl.upper()}_1248_V47.json")
s=s.replace("SEED=202610300830",f"SEED={202610301900 + ('rr','contig','snake','paired').index(tpl)}")
s=s.replace("REPS=(0,1,2,3)","REPS=(0,)")
s=s.replace("chosen_t={rep:('rr' if idx<320 else max(T,key=lambda k:(obj(thist[rep][k]),k))) for rep in REPS}",f"chosen_t={{rep:'{tpl}' for rep in REPS}}")
s=s.replace("chosen_rep=0 if idx<400 else max(REPS,key=lambda rep:(obj(rhist[rep]),-rep));L=repP[chosen_rep]","chosen_rep=0;L=repP[chosen_rep]")
inject=r'''
_EXACT_NULL_CACHE={}
def _shape_key(L):
 counts=[0]*32;ss=[set(x) for x in L]
 for n in range(1,46):
  mask=0
  for i,q in enumerate(ss):
   if n in q:mask|=(1<<i)
  counts[mask]+=1
 return tuple(counts)
def exact_null(L):
 key=_shape_key(L)
 if key in _EXACT_NULL_CACHE:return _EXACT_NULL_CACHE[key]
 dp={(0,0,0,0,0,0,0):1}
 for mask,c in enumerate(key):
  if not c:continue
  nd={}
  for state,ways in dp.items():
   k,*rest=state;hits=rest[:5];cov=rest[5]
   for j in range(0,min(c,6-k)+1):
    mult=math.comb(c,j);nh=[hits[i]+(j if mask&(1<<i) else 0) for i in range(5)];ncov=cov+(j if mask else 0);ns=(k+j,*nh,ncov);nd[ns]=nd.get(ns,0)+ways*mult
  dp=nd
 total=math.comb(45,6);acc={'max_hits':0.0,'any2':0.0,'any3':0.0,'any4':0.0,'winning_union_coverage':0.0,'union_size':float(sum(key[1:]))}
 for state,ways in dp.items():
  if state[0]!=6:continue
  hits=state[1:6];cov=state[6];m=max(hits);w=ways/total
  acc['max_hits']+=w*m;acc['any2']+=w*(m>=2);acc['any3']+=w*(m>=3);acc['any4']+=w*(m>=4);acc['winning_union_coverage']+=w*cov
 _EXACT_NULL_CACHE[key]=acc;return acc
'''
s=s.replace("def avg(rows,k):",inject+"\ndef avg(rows,k):")
old="rng=random.Random(SEED+target);sm=[met(perm(L,rng),actual) for _ in range(TEST_NULL)];nm={k:statistics.mean(float(q[k]) for q in sm) for k in sm[0]};nul.append(nm)"
assert old in s
s=s.replace(old,"nm=exact_null(L);nul.append(nm)")
s=s.replace("'ADAPTIVE_REPEATED_CORE_HYBRID_V28'",f"'FIXED_H_{tpl.upper()}_V47'")
s=s.replace("'Hybrid V26 ranking. Four predeclared repetition levels rep0..rep3; for each rep, tail template chosen only by prior rolling150 results, then repetition level chosen only by its prior rolling150 adaptive-policy results. Strict outer gate unchanged.'",f"'V38/V28 hybrid top30, rep0 only, fixed {tpl} partition for every target. No template switching. Exact matched-label null and strict gate unchanged.'")
exec(compile(s,str(p),'exec'),globals(),globals())
