#!/usr/bin/env python3
from pathlib import Path
p=Path(__file__).resolve().parent/'today_frozen_signal_partition_v42.py'
s=p.read_text(encoding='utf-8')
s=s.replace("TODAY_FROZEN_SIGNAL_PARTITION_1248_V42.json","TODAY_RANKFAMILY_PREQUENTIAL_1248_V60.json")
s=s.replace("SEED=202610301610","SEED=202610301660")
s=s.replace("SIGNALS=('H','G','C','M','P','T')","SIGNALS=('H','M')")
s=s.replace("'FROZEN_V4_SIGNAL_PARTITION_V42'","'RANKFAMILY_PREQUENTIAL_V60'")
s=s.replace("pc=Counter(p for q in nums for p in itertools.combinations(q,2));tc=Counter(t for q in nums for t in itertools.combinations(q,3));PS={x:0. for x in range(1,46)};TS={x:0. for x in range(1,46)}","pc=Counter(p for q in nums for p in itertools.combinations(q,2));PS={x:0. for x in range(1,46)}")
oldtri=""" for tri in itertools.combinations(range(1,46),3):
  x,y,z=tri;e=(20/36)*(2025/1892)*freq[x]*freq[y]*freq[z]/(n*n);v=(tc[tri]-e)/math.sqrt(max(e,1e-12));TS[x]+=v;TS[y]+=v;TS[z]+=v
 return {'G':G,'C':C,'M':M,'P':PS,'T':TS}"""
assert oldtri in s
s=s.replace(oldtri,""" return {'G':G,'C':C,'M':M,'P':PS}""")
# Extend candidate names to rank family x H/M x partition.
s=s.replace("NAMES=tuple(f'{s}:{p}' for s in SIGNALS for p in PAT)","RANKMODES=('base','blend30','slow30','slow3','slow10','slow15','wslow','wmedium')\nNAMES=tuple(f'{r}|{sg}:{pt}' for r in RANKMODES for sg in SIGNALS for pt in PAT)")
# Replace one-rank construction with 8 preregistered rank families and all associated ticket policies.
oldrank="""scores={k:v18.predict(X,s['w']) for k,s in states.items()};zs={k:zscore(v) for k,v in scores.items()};blend={n:sum(zs[k][n] for k in CFG)/len(CFG) for n in range(1,46)};r=ranked_hybrid(scores['slow'],blend);core=r[:6];tail=r[6:]
  fs=frozen_scores([q['nums'] for q in draws[max(0,idx-300):idx]])
  orders={'H':tail}
  for s in SIGNALS[1:]:orders[s]=sorted(tail,key=lambda n:(-fs[s][n],n))
  policies={f'{s}:{p}':lines(core,orders[s],p) for s in SIGNALS for p in PAT}"""
newrank="""scores={k:v18.predict(X,s['w']) for k,s in states.items()};zs={k:zscore(v) for k,v in scores.items()};blend={n:sum(zs[k][n] for k in CFG)/len(CFG) for n in range(1,46)}
  def top(sc,k=30):return sorted(range(1,46),key=lambda n:(-sc[n],n))[:k]
  def hyb(k):
   c=top(scores['slow'],k);return c+sorted((n for n in range(1,46) if n not in c),key=lambda n:(-blend[n],n))[:30-k]
  wslow={n:.55*zs['slow'][n]+.30*zs['medium'][n]+.15*zs['fast'][n] for n in range(1,46)}
  wmedium={n:.25*zs['slow'][n]+.50*zs['medium'][n]+.25*zs['fast'][n] for n in range(1,46)}
  ranks={'base':hyb(6),'blend30':top(blend),'slow30':top(scores['slow']),'slow3':hyb(3),'slow10':hyb(10),'slow15':hyb(15),'wslow':top(wslow),'wmedium':top(wmedium)}
  fs=frozen_scores([q['nums'] for q in draws[max(0,idx-300):idx]])
  policies={};rankmeta={}
  for rm,r0 in ranks.items():
   core0=r0[:6];tail0=r0[6:];orders0={'H':tail0,'M':sorted(tail0,key=lambda n:(-fs['M'][n],n))};rankmeta[rm]=(core0,tail0,orders0)
   for sg in SIGNALS:
    for pt in PAT:policies[f'{rm}|{sg}:{pt}']=lines(core0,orders0[sg],pt)"""
assert oldrank in s
s=s.replace(oldrank,newrank)
s=s.replace("hist={k:deque(maxlen=ROLL) for k in NAMES};obs=[];diff=", "hist={k:deque(maxlen=ROLL) for k in NAMES};locked='base|H:rr';obs=[];diff=")
oldsel="""  if idx<320:chosen='H:rr'
  else:
   def score_name(n):return statistics.mean(hist[n]) if hist[n] else -999.
   chosen=max(NAMES,key=lambda n:(score_name(n),n=='H:rr',n))"""
newsel="""  if idx<400:
   chosen='base|H:rr'
  else:
   if (idx-400)%50==0:
    def bs(n,k):
     v=[float(q[k])-float(NULL[k]) for q in list(hist[n])[-150:]];return [statistics.mean(v[i:i+50]) for i in range(0,len(v),50) if len(v[i:i+50])>=40]
    def key(n):
     bm,b2,b3=bs(n,'max_hits'),bs(n,'any2'),bs(n,'any3')
     if not bm or not b2 or not b3:return (-999.,)*7
     floors=(min(bm),min(b2),min(b3));pm=sum(x>0 for x in bm)/len(bm);p2=sum(x>0 for x in b2)/len(b2);p3=sum(x>0 for x in b3)/len(b3)
     return (min(floors),min(pm,p2,p3),sum(floors),statistics.mean(b3),statistics.mean(b2),statistics.mean(bm),n)
    locked=max(NAMES,key=key)
   chosen=locked"""
assert oldsel in s
s=s.replace(oldsel,newsel)
s=s.replace("for n,Q in policies.items():hist[n].append(obj(met(Q,actual)))","for n,Q in policies.items():hist[n].append(met(Q,actual))")
oldcur="""current={'chosen_policy':chosen,'selector_scores':{n:(statistics.mean(hist[n]) if hist[n] else -999.) for n in NAMES},'core':core,'hybrid_top30':r,'signal_tail_orders':{s:orders[s] for s in SIGNALS},'lines':[list(x) for x in L],'union_size':30};break"""
newcur="""rm=chosen.split('|',1)[0];core0,tail0,orders0=rankmeta[rm];current={'chosen_policy':chosen,'selector_scores':{n:({k:statistics.mean(float(q[k]) for q in hist[n]) for k in ('max_hits','any2','any3')} if hist[n] else {}) for n in NAMES},'rank_mode':rm,'core':core0,'hybrid_top30':ranks[rm],'signal_tail_orders':{sg:orders0[sg] for sg in SIGNALS},'lines':[list(x) for x in L],'union_size':30};break"""
assert oldcur in s
s=s.replace(oldcur,newcur)
s=s.replace("'selection':'24 predeclared signal x partition policies; each target selects highest previous rolling150 fixed V28 objective only'","'selection':'V60: 64 preregistered rank-mode x H/M x partition policies; locked for each 50-target block using only prior <=150 outcomes and block-robust lexicographic key.'")
s=s.replace("'number_selection':'V38/V28 hybrid top30: slow core6 + multiscale blend tail24'","'number_selection':'V60 finite preregistered family: base/blend30/slow30/slow-core3/10/15/fixed multiscale wslow/wmedium; each target uses only <=t-1 features'")
s=s.replace("'partition_signals':'H plus rolling300 V4_G,V4_C,V4_M,V4_P,V4_T; V4 formulas/mode frozen on 2026-10-09'","'partition_signals':'H plus rolling300 frozen V4_M momentum only'")
exec(compile(s,str(p),'exec'),globals(),globals())
