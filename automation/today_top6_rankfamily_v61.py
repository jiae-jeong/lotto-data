#!/usr/bin/env python3
from pathlib import Path
p=Path(__file__).resolve().parent/'today_frozen_signal_partition_v42.py'
s=p.read_text(encoding='utf-8')
s=s.replace("TODAY_FROZEN_SIGNAL_PARTITION_1248_V42.json","TODAY_TOP6_RANKFAMILY_1248_V61.json")
s=s.replace("SEED=202610301610","SEED=202610301761")
s=s.replace("PAT={\n 'rr':[[0,4,8,12,16,20],[1,5,9,13,17,21],[2,6,10,14,18,22],[3,7,11,15,19,23]],\n 'contig':[[0,1,2,3,4,5],[6,7,8,9,10,11],[12,13,14,15,16,17],[18,19,20,21,22,23]],\n 'snake':[[0,7,8,15,16,23],[1,6,9,14,17,22],[2,5,10,13,18,21],[3,4,11,12,19,20]],\n 'paired':[[0,1,8,9,16,17],[2,3,10,11,18,19],[4,5,12,13,20,21],[6,7,14,15,22,23]]}","PAT={'top6x2':None}")
s=s.replace("SIGNALS=('H','G','C','M','P','T')","SIGNALS=('H','M')")
s=s.replace("NAMES=tuple(f'{s}:{p}' for s in SIGNALS for p in PAT)","RANKMODES=('base','blend30','slow30','slow3','slow10','slow15','wslow','wmedium')\nNAMES=tuple(f'{r}|{sg}:top6x2' for r in RANKMODES for sg in SIGNALS)")
s=s.replace("'FROZEN_V4_SIGNAL_PARTITION_V42'","'TOP6_RANKFAMILY_V61'")
s=s.replace("pc=Counter(p for q in nums for p in itertools.combinations(q,2));tc=Counter(t for q in nums for t in itertools.combinations(q,3));PS={x:0. for x in range(1,46)};TS={x:0. for x in range(1,46)}","pc=Counter(p for q in nums for p in itertools.combinations(q,2));PS={x:0. for x in range(1,46)}")
oldtri=""" for tri in itertools.combinations(range(1,46),3):
  x,y,z=tri;e=(20/36)*(2025/1892)*freq[x]*freq[y]*freq[z]/(n*n);v=(tc[tri]-e)/math.sqrt(max(e,1e-12));TS[x]+=v;TS[y]+=v;TS[z]+=v
 return {'G':G,'C':C,'M':M,'P':PS,'T':TS}"""
assert oldtri in s;s=s.replace(oldtri,""" return {'G':G,'C':C,'M':M,'P':PS}""")
oldlines="""def lines(core,tail_order,pat):
 L=[tuple(sorted(core))]+[tuple(sorted(tail_order[j] for j in p)) for p in PAT[pat]]
 assert len(L)==5 and len(set(L))==5 and len(set().union(*map(set,L)))==30 and all(len(x)==6 for x in L);return L"""
newlines="""def top6_template():
 g=[[] for _ in range(5)]
 for r in range(6):g[r%5].append(r);g[(r+2)%5].append(r)
 u=6
 for i in range(5):
  while len(g[i])<6:g[i].append(u);u+=1
 return g

def lines(core,tail_order,pat):
 order=list(core)+list(tail_order);L=[tuple(sorted(order[j] for j in q)) for q in top6_template()]
 assert len(L)==5 and len(set(L))==5 and all(len(x)==6 and len(set(x))==6 for x in L);return L"""
assert oldlines in s;s=s.replace(oldlines,newlines)
start=s.index('def exact_null_disjoint30():');end=s.index('NULL=exact_null_disjoint30()',start)+len('NULL=exact_null_disjoint30()')
newnull="""def exact_null_top6x2():
 L=[tuple(j+1 for j in q) for q in top6_template()];counts=[0]*32
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
 total=math.comb(45,6);u=len(set().union(*map(set,L)));a={'max_hits':0.,'any2':0.,'any3':0.,'any4':0.,'winning_union_coverage':0.,'union_size':float(u)}
 for st,w in dp.items():
  if st[0]!=6:continue
  h=st[1:6];cov=st[6];m=max(h);pr=w/total;a['max_hits']+=pr*m;a['any2']+=pr*(m>=2);a['any3']+=pr*(m>=3);a['any4']+=pr*(m>=4);a['winning_union_coverage']+=pr*cov
 return a
NULL=exact_null_top6x2()"""
s=s[:start]+newnull+s[end:]
oldrank="""scores={k:v18.predict(X,s['w']) for k,s in states.items()};zs={k:zscore(v) for k,v in scores.items()};blend={n:sum(zs[k][n] for k in CFG)/len(CFG) for n in range(1,46)};r=ranked_hybrid(scores['slow'],blend);core=r[:6];tail=r[6:]
  fs=frozen_scores([q['nums'] for q in draws[max(0,idx-300):idx]])
  orders={'H':tail}
  for s in SIGNALS[1:]:orders[s]=sorted(tail,key=lambda n:(-fs[s][n],n))
  policies={f'{s}:{p}':lines(core,orders[s],p) for s in SIGNALS for p in PAT}"""
newrank="""scores={k:v18.predict(X,s['w']) for k,s in states.items()};zs={k:zscore(v) for k,v in scores.items()};blend={n:sum(zs[k][n] for k in CFG)/len(CFG) for n in range(1,46)}
  def top(sc,k=30):return sorted(range(1,46),key=lambda n:(-sc[n],n))[:k]
  def hyb(k):
   c=top(scores['slow'],k);return c+sorted((n for n in range(1,46) if n not in c),key=lambda n:(-blend[n],n))[:30-k]
  wslow={n:.55*zs['slow'][n]+.30*zs['medium'][n]+.15*zs['fast'][n] for n in range(1,46)};wmedium={n:.25*zs['slow'][n]+.50*zs['medium'][n]+.25*zs['fast'][n] for n in range(1,46)}
  ranks={'base':hyb(6),'blend30':top(blend),'slow30':top(scores['slow']),'slow3':hyb(3),'slow10':hyb(10),'slow15':hyb(15),'wslow':top(wslow),'wmedium':top(wmedium)}
  fs=frozen_scores([q['nums'] for q in draws[max(0,idx-300):idx]]);policies={};rankmeta={}
  for rm,r0 in ranks.items():
   core0=r0[:6];tail0=r0[6:];orders0={'H':tail0,'M':sorted(tail0,key=lambda n:(-fs['M'][n],n))};rankmeta[rm]=(core0,orders0)
   for sg in SIGNALS:policies[f'{rm}|{sg}:top6x2']=lines(core0,orders0[sg],'top6x2')"""
assert oldrank in s;s=s.replace(oldrank,newrank)
s=s.replace("hist={k:deque(maxlen=ROLL) for k in NAMES};obs=[];diff=", "hist={k:deque(maxlen=ROLL) for k in NAMES};locked='base|H:top6x2';obs=[];diff=")
oldsel="""  if idx<320:chosen='H:rr'
  else:
   def score_name(n):return statistics.mean(hist[n]) if hist[n] else -999.
   chosen=max(NAMES,key=lambda n:(score_name(n),n=='H:rr',n))"""
newsel="""  if idx<400:chosen='base|H:top6x2'
  else:
   if (idx-400)%50==0:
    def bs(n,k):
     v=[float(q[k])-float(NULL[k]) for q in list(hist[n])[-150:]];return [statistics.mean(v[i:i+50]) for i in range(0,len(v),50) if len(v[i:i+50])>=40]
    def key(n):
     bm,b2,b3=bs(n,'max_hits'),bs(n,'any2'),bs(n,'any3')
     if not bm or not b2 or not b3:return (-999.,)*8
     pm=sum(x>0 for x in bm)/len(bm);p2=sum(x>0 for x in b2)/len(b2);p3=sum(x>0 for x in b3)/len(b3);floors=(min(bm),min(b2),min(b3))
     return (min(floors),p2>=2/3,min(pm,p2,p3),sum(floors),statistics.mean(b3),statistics.mean(b2),statistics.mean(bm),n)
    locked=max(NAMES,key=key)
   chosen=locked"""
assert oldsel in s;s=s.replace(oldsel,newsel)
s=s.replace("for n,Q in policies.items():hist[n].append(obj(met(Q,actual)))","for n,Q in policies.items():hist[n].append(met(Q,actual))")
oldcur="""current={'chosen_policy':chosen,'selector_scores':{n:(statistics.mean(hist[n]) if hist[n] else -999.) for n in NAMES},'core':core,'hybrid_top30':r,'signal_tail_orders':{s:orders[s] for s in SIGNALS},'lines':[list(x) for x in L],'union_size':30};break"""
newcur="""rm=chosen.split('|',1)[0];core0,orders0=rankmeta[rm];current={'chosen_policy':chosen,'rank_mode':rm,'selector_scores':{n:({k:statistics.mean(float(q[k]) for q in hist[n]) for k in ('max_hits','any2','any3')} if hist[n] else {}) for n in NAMES},'core':core0,'hybrid_top30':ranks[rm],'signal_tail_orders':{sg:orders0[sg] for sg in SIGNALS},'lines':[list(x) for x in L],'union_size':len(set().union(*map(set,L)))};break"""
assert oldcur in s;s=s.replace(oldcur,newcur)
s=s.replace("'union_size':30};break","'union_size':len(set().union(*map(set,L)))};break")
s=s.replace("'selection':'24 predeclared signal x partition policies; each target selects highest previous rolling150 fixed V28 objective only'","'selection':'V61: 16 preregistered rank-mode x H/M top6x2 policies; locked every 50 targets using only prior <=150 outcomes, same strict gate.'")
s=s.replace("'number_selection':'V38/V28 hybrid top30: slow core6 + multiscale blend tail24'","'number_selection':'V61 finite rank family applied to fixed top6x2 overlap geometry; all rankings cutoff-safe'")
s=s.replace("'partition_signals':'H plus rolling300 V4_G,V4_C,V4_M,V4_P,V4_T; V4 formulas/mode frozen on 2026-10-09'","'partition_signals':'H plus frozen rolling300 V4_M momentum'")
s=s.replace("'geometry':'Every candidate is 5 disjoint lines, union30; exact matched-label null identical to V38 unique30 geometry'","'geometry':'Fixed top6x2 overlap mask for every candidate; exact matched-label null recomputed for identical geometry, union24.'")
exec(compile(s,str(p),'exec'),globals(),globals())
