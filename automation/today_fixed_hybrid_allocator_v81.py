#!/usr/bin/env python3
from pathlib import Path
p=Path(__file__).resolve().parent/'today_frozen_signal_partition_v42.py'
s=p.read_text(encoding='utf-8')
s=s.replace("TODAY_FROZEN_SIGNAL_PARTITION_1248_V42.json","TODAY_FIXED_HYBRID_ALLOCATOR_1248_V81.json")
s=s.replace("SEED=202610301610","SEED=202610302481")
s=s.replace("SIGNALS=('H','G','C','M','P','T')","PAT={'hybrid27':None}\nSIGNALS=('H',)")
s=s.replace("'FROZEN_V4_SIGNAL_PARTITION_V42'","'FIXED_HYBRID_ALLOCATOR_V81'")
s=s.replace("pc=Counter(p for q in nums for p in itertools.combinations(q,2));tc=Counter(t for q in nums for t in itertools.combinations(q,3));PS={x:0. for x in range(1,46)};TS={x:0. for x in range(1,46)}","pc=Counter(p for q in nums for p in itertools.combinations(q,2));PS={x:0. for x in range(1,46)}")
oldtri=""" for tri in itertools.combinations(range(1,46),3):
  x,y,z=tri;e=(20/36)*(2025/1892)*freq[x]*freq[y]*freq[z]/(n*n);v=(tc[tri]-e)/math.sqrt(max(e,1e-12));TS[x]+=v;TS[y]+=v;TS[z]+=v
 return {'G':G,'C':C,'M':M,'P':PS,'T':TS}"""
assert oldtri in s;s=s.replace(oldtri,""" return {'G':G,'C':C,'M':M,'P':PS}""")
oldlines="""def lines(core,tail_order,pat):
 L=[tuple(sorted(core))]+[tuple(sorted(tail_order[j] for j in p)) for p in PAT[pat]]
 assert len(L)==5 and len(set(L))==5 and len(set().union(*map(set,L)))==30 and all(len(x)==6 for x in L);return L"""
newlines="""def template():
 # Fixed before validation: first two lines use the top6x2 concentration geometry,
 # remaining three use the x2 coverage geometry.  The chosen line indices maximize
 # union size (27) without using any lottery outcomes.
 top6=[[0,3,5,6,7,8],[1,4,9,10,11,12],[0,2,5,13,14,15],[1,3,16,17,18,19],[2,4,20,21,22,23]]
 x2=[[0,2,3,4,5,6],[1,7,8,9,10,11],[0,12,13,14,15,16],[1,17,18,19,20,21],[22,23,24,25,26,27]]
 return [top6[0],top6[1],x2[2],x2[3],x2[4]]
def lines(core,tail_order,pat):
 order=list(core)+list(tail_order);L=[tuple(sorted(order[j] for j in q)) for q in template()]
 assert len(L)==5 and len(set(L))==5 and len(set().union(*map(set,L)))==27 and all(len(x)==6 and len(set(x))==6 for x in L);return L"""
assert oldlines in s;s=s.replace(oldlines,newlines)
start=s.index('def exact_null_disjoint30():');end=s.index('NULL=exact_null_disjoint30()',start)+len('NULL=exact_null_disjoint30()')
newnull="""def exact_null_hybrid27():
 L=[tuple(j+1 for j in q) for q in template()];counts=[0]*32
 for n in range(1,46):
  mask=0
  for i,q in enumerate(L):
   if n in q:mask|=1<<i
  counts[mask]+=1
 dp={(0,0,0,0,0,0,0):1}
 for mask,c in enumerate(counts):
  if not c:continue
  nd={}
  for st,w in dp.items():
   k,*rest=st;hits=rest[:5];cov=rest[5]
   for j in range(min(c,6-k)+1):
    mult=math.comb(c,j);nh=[hits[i]+(j if mask&(1<<i) else 0) for i in range(5)];ns=(k+j,*nh,cov+(j if mask else 0));nd[ns]=nd.get(ns,0)+w*mult
  dp=nd
 total=math.comb(45,6);a={'max_hits':0.,'any2':0.,'any3':0.,'any4':0.,'winning_union_coverage':0.,'union_size':27.0}
 for st,w in dp.items():
  if st[0]!=6:continue
  h=st[1:6];cov=st[6];m=max(h);pr=w/total;a['max_hits']+=pr*m;a['any2']+=pr*(m>=2);a['any3']+=pr*(m>=3);a['any4']+=pr*(m>=4);a['winning_union_coverage']+=pr*cov
 return a
NULL=exact_null_hybrid27()"""
s=s[:start]+newnull+s[end:]
oldsel="""  if idx<320:chosen='H:rr'
  else:
   def score_name(n):return statistics.mean(hist[n]) if hist[n] else -999.
   chosen=max(NAMES,key=lambda n:(score_name(n),n=='H:rr',n))"""
assert oldsel in s;s=s.replace(oldsel,"  chosen='H:hybrid27'")
oldcur="""current={'chosen_policy':chosen,'selector_scores':{n:(statistics.mean(hist[n]) if hist[n] else -999.) for n in NAMES},'core':core,'hybrid_top30':r,'signal_tail_orders':{s:orders[s] for s in SIGNALS},'lines':[list(x) for x in L],'union_size':30};break"""
newcur="""current={'chosen_policy':chosen,'selector_scores':{n:(statistics.mean(hist[n]) if hist[n] else -999.) for n in NAMES},'core':core,'hybrid_top30':r,'signal_tail_orders':{sg:orders[sg] for sg in SIGNALS},'lines':[list(x) for x in L],'union_size':27};break"""
assert oldcur in s;s=s.replace(oldcur,newcur)
s=s.replace("'selection':'24 predeclared signal x partition policies; each target selects highest previous rolling150 fixed V28 objective only'","'selection':'V81 single fixed H:hybrid27 allocator; no policy selection on evaluation outcomes. Template combines two concentration lines and three coverage lines, fixed by outcome-blind maximum-union tie rule. Strict gate unchanged.'")
s=s.replace("'geometry':'Every candidate is 5 disjoint lines, union30; exact matched-label null identical to V38 unique30 geometry'","'geometry':'V81 fixed hybrid27: union27 with three duplicated rank positions; exact matched-label null computed for the identical overlap mask.'")
exec(compile(s,str(p),'exec'),globals(),globals())
