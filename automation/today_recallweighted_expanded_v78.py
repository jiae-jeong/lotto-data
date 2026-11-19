#!/usr/bin/env python3
from pathlib import Path
p=Path(__file__).resolve().parent/'today_expanded_overlap_v76.py'
outer=p.read_text(encoding='utf-8')
outer=outer.replace('TODAY_EXPANDED_OVERLAP_1248_V76.json','TODAY_RECALLWEIGHTED_EXPANDED_1248_V78.json')
outer=outer.replace("'EXPANDED_OVERLAP_V76'","'RECALLWEIGHTED_EXPANDED_V78'")
needle="exec(compile(src,str(p),'exec'),globals(),globals())"
inject=r'''# V78 injects a cutoff-safe learner-recall weighting into V76's ranking stage.
inner="exec(compile(s,str(p),'exec'),globals(),globals())"
patch=r"""# add rolling learner recall state before execution of transformed V42
oldh=\"hist={k:deque(maxlen=ROLL) for k in NAMES};locked='H:repeat1';obs=[];nullobs=[];diff=\"
newh=\"hist={k:deque(maxlen=ROLL) for k in NAMES};locked='H:repeat1';recallperf={k:deque(maxlen=150) for k in CFG};obs=[];nullobs=[];diff=\"
assert oldh in s
s=s.replace(oldh,newh)
oldr=\"scores={k:v18.predict(X,s['w']) for k,s in states.items()};zs={k:zscore(v) for k,v in scores.items()};blend={n:sum(zs[k][n] for k in CFG)/len(CFG) for n in range(1,46)};r=ranked_hybrid(scores['slow'],blend);core=r[:6];tail=r[6:]\"
newr=\"\"\"scores={k:v18.predict(X,s['w']) for k,s in states.items()};zs={k:zscore(v) for k,v in scores.items()}
  means={k:(statistics.mean(recallperf[k]) if recallperf[k] else 0.0) for k in CFG};raw={k:math.exp(3.0*means[k]) for k in CFG};den=sum(raw.values());lw={k:raw[k]/den for k in CFG}
  blend={n:sum(lw[k]*zs[k][n] for k in CFG) for n in range(1,46)};r=ranked_hybrid(scores['slow'],blend);core=r[:6];tail=r[6:]\"\"\"
assert oldr in s
s=s.replace(oldr,newr)
oldhist=\"for n,Q in policies.items():hist[n].append(met(Q,actual))\"
newhist=\"\"\"for k in CFG:
   top30=set(sorted(range(1,46),key=lambda n:(-scores[k][n],n))[:30]);recallperf[k].append(len(top30&actual)-4.0)
  for n,Q in policies.items():hist[n].append(met(Q,actual))\"\"\"
assert oldhist in s
s=s.replace(oldhist,newhist)
s=s.replace(\"'number_selection':'V38/V28 hybrid top30: slow core6 + multiscale blend tail24'\",\"'number_selection':'V78 slow core6 + tail24 from softmax-weighted slow/medium/fast z-scores; weights use only prior <=150 top30 recall deltas'\")
s=s.replace(\"'selection':'V76 fixed any3guard selector over 26 preregistered H/M heavy+intermediate overlap experts; every 50-target choice uses only prior <=150 outcomes; geometry-specific exact null and strict gate unchanged.'\",\"'selection':'V78 separates recall and construction: learner weights update from prior top30 recall only; V76 any3guard then selects among 26 preregistered overlap geometries at 50-target boundaries using prior <=150 ticket deltas. Strict gate unchanged.'\")
exec(compile(s,str(p),'exec'),globals(),globals())"""
assert inner in src
src=src.replace(inner,patch)
exec(compile(src,str(p),'exec'),globals(),globals())'''
assert needle in outer
outer=outer.replace(needle,inject)
exec(compile(outer,str(p),'exec'),globals(),globals())
