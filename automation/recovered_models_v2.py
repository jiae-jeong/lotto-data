#!/usr/bin/env python3
"""Executable successor models built only from recovered concepts.

These are NEW v2 models, not reconstructions of the lost legacy executables.
All features for target t are computed from draws < t only.

Performance note: the public model definitions are unchanged, but shared A scores
and structure bounds are computed once per ``predict(history)`` call. This keeps
predictions deterministic while avoiding thousands of repeated quantile
calculations inside the C-model combination search.
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

def _ticket_a_from_scores(scores):
    return tuple(sorted(sorted(scores,key=lambda x:(-scores[x],x))[:6]))

def ticket_a(history):
    return _ticket_a_from_scores(score_a(history))

def _structure_bounds(history):
    sums=[sum(d) for d in history]
    qs=statistics.quantiles(sums,n=10)
    return qs[0],qs[-1]

def _structure_ok_with_bounds(ticket, lo, hi):
    odd=sum(x%2 for x in ticket); low=sum(x<=22 for x in ticket)
    return lo<=sum(ticket)<=hi and 1<=odd<=5 and 1<=low<=5

def _structure_ok(ticket, history):
    lo,hi=_structure_bounds(history)
    return _structure_ok_with_bounds(ticket,lo,hi)

def _ticket_c_from_scores(history, scores, bounds=None, fallback=None):
    # Combined successor: A evidence plus diversity/structure guard; deterministic exhaustive top-pool search.
    lo,hi=bounds if bounds is not None else _structure_bounds(history)
    pool=sorted(scores,key=lambda x:(-scores[x],x))[:14]; best=None
    for t in itertools.combinations(pool,6):
        val=sum(scores[x] for x in t) + .02*len({x//10 for x in t}) + .01*len({x%10 for x in t})
        if _structure_ok_with_bounds(t,lo,hi) and (best is None or val>best[0] or (val==best[0] and t<best[1])): best=(val,t)
    if best:
        return tuple(sorted(best[1]))
    return tuple(sorted(fallback if fallback is not None else _ticket_a_from_scores(scores)))

def ticket_c(history):
    s=score_a(history)
    return _ticket_c_from_scores(history,s)

def _ticket_contrarian_from_scores(history, scores):
    # Opposite-hypothesis successor: prefer low A-score numbers while explicitly allowing atypical structure.
    pool=sorted(scores,key=lambda x:(scores[x],x))[:18]; best=None
    mean_sum=statistics.mean(sum(d) for d in history)
    for t in itertools.combinations(pool,6):
        odd=sum(x%2 for x in t); endings=6-len({x%10 for x in t}); consec=sum(b-a==1 for a,b in zip(t,t[1:])); skew=abs(odd-3)
        atyp=abs(sum(t)-mean_sum)/45 + .35*endings + .25*consec + .20*skew
        val=atyp-.20*sum(scores[x] for x in t)
        if best is None or val>best[0] or (val==best[0] and t<best[1]): best=(val,t)
    return tuple(sorted(best[1]))

def ticket_contrarian(history):
    return _ticket_contrarian_from_scores(history,score_a(history))

def predict(history):
    # One feature/score pass and one quantile pass per target. The old code
    # recomputed A scores three times and C structure quantiles once per combo.
    s=score_a(history)
    a=_ticket_a_from_scores(s)
    bounds=_structure_bounds(history)
    return {
        'A_v2':a,
        'C_v2':_ticket_c_from_scores(history,s,bounds=bounds,fallback=a),
        'contrarian_v2':_ticket_contrarian_from_scores(history,s),
    }
