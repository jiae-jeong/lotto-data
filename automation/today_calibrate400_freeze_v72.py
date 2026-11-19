#!/usr/bin/env python3
from pathlib import Path
p=Path(__file__).resolve().parent/'today_twostage_overlap_v69.py'
src=p.read_text(encoding='utf-8')
# Reuse the finite rank-family + overlap expert construction, but replace adaptive post-400 selection by one calibration-only freeze.
src=src.replace("TODAY_TWOSTAGE_OVERLAP_{mode}_1248_V69.json","TODAY_CALIBRATE400_FREEZE_1248_V72.json")
src=src.replace("'TWOSTAGE_OVERLAP_V69'","'CALIBRATE400_FREEZE_V72'")
needle="exec(compile(s,str(p),'exec'),globals(),globals())"
patch=r'''# Apply geometry-specific null patch as in V69fix.
s=s.replace("float(NULL[k])","float(NULLS[n][k])")
# Freeze exactly once at the 401 boundary using only <=400 outcomes. The selected expert is never changed afterward.
old="""  if idx<400:
   chosen='base|H:repeat1'
  else:
   if (idx-400)%50==0:
    def blocks(v):return [statistics.mean(v[i:i+50]) for i in range(0,len(v),50) if len(v[i:i+50])>=40]
    def lb(v):
     if len(v)<40:return -999.
     mu=statistics.mean(v);sd=statistics.stdev(v) if len(v)>1 else 0.;return mu-1.645*sd/(len(v)**.5)
    def pshare(v):
     b=blocks(v);return sum(x>0 for x in b)/len(b) if b else 0.
    def rankkey(rm):
     v=list(rankhist[rm]);return (lb(v),pshare(v),statistics.mean(v) if v else -999.,rm)
    locked_rank=max(RANKMODES,key=rankkey)
    cand=[n for n in NAMES if n.startswith(locked_rank+'|')]
    def ds(n,k):return [float(q[k])-float(NULLS[n][k]) for q in list(hist[n])[-150:]]
    def tkey(n):
     vm,v2,v3=ds(n,'max_hits'),ds(n,'any2'),ds(n,'any3');lm,l2,l3=lb(vm),lb(v2),lb(v3);pm,p2,p3=pshare(vm),pshare(v2),pshare(v3)
     if mode=='recall_any3':return (l3>0,p3>=2/3,lm>0,pm>=2/3,p2,l2,statistics.mean(v3),n)
     if mode=='recall_any2':return (l3>0,lm>0,p3>=2/3,pm>=2/3,p2>=2/3,l2,p2,n)
     if mode=='recall_joint':return (min(lm,l2,l3),sum((lm,l2,l3)),min(pm,p2,p3),p2,p3,n,'','')
     return (min(pm,p2,p3),min(lm,l2,l3),p2,p3,sum((lm,l2,l3)),n,'','')
    locked=max(cand,key=tkey)
   chosen=locked"""
new="""  if idx<400:
   chosen='base|H:repeat1'
  else:
   if idx==400:
    def blocks(v):return [statistics.mean(v[i:i+50]) for i in range(0,len(v),50) if len(v[i:i+50])>=40]
    def lb(v):
     if len(v)<40:return -999.
     mu=statistics.mean(v);sd=statistics.stdev(v) if len(v)>1 else 0.;return mu-1.645*sd/(len(v)**.5)
    def pshare(v):
     b=blocks(v);return sum(x>0 for x in b)/len(b) if b else 0.
    def ds(n,k):return [float(q[k])-float(NULLS[n][k]) for q in list(hist[n])]
    def key(n):
     vm,v2,v3=ds(n,'max_hits'),ds(n,'any2'),ds(n,'any3')
     if len(vm)<100:return (-999.,)*9
     lm,l2,l3=lb(vm),lb(v2),lb(v3);pm,p2,p3=pshare(vm),pshare(v2),pshare(v3)
     mm,m2,m3=statistics.mean(vm),statistics.mean(v2),statistics.mean(v3)
     return (min(lm,l2,l3),min(pm,p2,p3),sum((lm,l2,l3)),p2,p3,mm+m2+m3,l2,l3,n)
    locked=max(NAMES,key=key)
   chosen=locked"""
assert old in s
s=s.replace(old,new)
s=s.replace("'selection':'V69 {mode}: stage1 chooses rank family from prior top30 recall only; stage2 chooses H/M x overlap geometry within that rank from prior geometry-specific exact-null deltas; both locked for next 50 targets.'","'selection':'V72 independent holdout: choose exactly one finite rank-family x H/M x overlap expert at the 401 boundary using only outcomes <=400 and a preregistered maximin lower-bound/stability key; freeze it unchanged for targets 401..1248. Evaluation gate unchanged.'")
# Repair selector score serialization inherited through V69.
old2="'selector_scores':{n:(statistics.mean(hist[n]) if hist[n] else -999.) for n in NAMES}"
if old2 in s:
 new2="'selector_scores':{n:({k:statistics.mean(float(q[k]) for q in hist[n]) for k in ('max_hits','any2','any3','winning_union_coverage')} if hist[n] else {}) for n in NAMES}"
 s=s.replace(old2,new2)
exec(compile(s,str(p),'exec'),globals(),globals())'''
assert needle in src
src=src.replace(needle,patch)
exec(compile(src,str(p),'exec'),globals(),globals())
