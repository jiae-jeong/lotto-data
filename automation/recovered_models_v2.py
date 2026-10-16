#!/usr/bin/env python3
"""Executable successor models built only from recovered concepts.

These are NEW v2 models, not reconstructions of the lost legacy executables.
All features for target t are computed from draws < t only.
"""
from collections import Counter
import itertools, statistics

MODEL_VERSION = 'RECOVERED_SUCCESSOR_V2'
A_WEIGHTS = {'long_frequency': .35, 'recent_100': .25, 'gap': .20, 'pair': .20}

def _rank01(values):
    order=sorted(range(len(values)), key=lambda i:(values[i], i))
    out=[0.0]*len(values)
    den=max(1,len(values)-1)
    for r,i in enumerate(order): out[i]=r/den
    return out

def _features(history):
    n=len(history); freq=Counter(x for d in history for x in d); recent=Counter(x for d in history[-100:] for x in d)
    last={x:0 for x in range(1,46)}; pairs=Counter()
    for i,d in enumerate(history,1):
        for x in d:last[x]=i
        pairs.update(itertools.combinations(sorted(d),2))
    f=[freq[x] for x in range(1,46)]; r=[recent[x] for x in range(1,46)]; g=[n-last[x] for x in range(1,46)]
    pair_strength=[]
    for x in range(1,46):
        vals=[pairs[tuple(sorted((x,y)))] for y in range(1,46) if y!=x]
        pair_strength.append(statistics.mean(vals))
    return [_rank01(v) for v in (f,r,g,pair_strength)]

def score_a(history):
    fs=_features(history); ws=list(A_WEIGHTS.values())
    return {x:sum(w*fs[j][x-1] for j,w in enumerate(ws)) for x in range(1,46)}

def ticket_a(history):
    s=score_a(history); return tuple(sorted(sorted(s,key=lambda x:(-s[x],x))[:6]))

def _structure_ok(ticket, history):
    sums=[sum(d) for d in history]; lo,hi=statistics.quantiles(sums,n=10)[0],statistics.quantiles(sums,n=10)[-1]
    odd=sum(x%2 for x in ticket); low=sum(x<=22 for x in ticket)
    return lo<=sum(ticket)<=hi and 1<=odd<=5 and 1<=low<=5

def ticket_c(history):
    # Combined successor: A evidence plus diversity/structure guard; deterministic exhaustive top-pool search.
    s=score_a(history); pool=sorted(s,key=lambda x:(-s[x],x))[:14]; best=None
    for t in itertools.combinations(pool,6):
        val=sum(s[x] for x in t) + .02*len({x//10 for x in t}) + .01*len({x%10 for x in t})
        if _structure_ok(t,history) and (best is None or val>best[0] or (val==best[0] and t<best[1])): best=(val,t)
    return tuple(sorted(best[1] if best else ticket_a(history)))

def ticket_contrarian(history):
    # Opposite-hypothesis successor: prefer low A-score numbers while explicitly allowing atypical structure.
    s=score_a(history); pool=sorted(s,key=lambda x:(s[x],x))[:18]; best=None
    mean_sum=statistics.mean(sum(d) for d in history)
    for t in itertools.combinations(pool,6):
        odd=sum(x%2 for x in t); endings=6-len({x%10 for x in t}); consec=sum(b-a==1 for a,b in zip(t,t[1:])); skew=abs(odd-3)
        atyp=abs(sum(t)-mean_sum)/45 + .35*endings + .25*consec + .20*skew
        val=atyp-.20*sum(s[x] for x in t)
        if best is None or val>best[0] or (val==best[0] and t<best[1]): best=(val,t)
    return tuple(sorted(best[1]))

def predict(history):
    return {'A_v2':ticket_a(history),'C_v2':ticket_c(history),'contrarian_v2':ticket_contrarian(history)}
