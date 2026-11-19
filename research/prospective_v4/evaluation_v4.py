"""Frozen metrics for future, registered predictions. No data downloads or V3 writes."""
import csv, json, math, statistics
from collections import Counter

def exact_hit_pmf():
    den=math.comb(45,6)
    return [math.comb(6,k)*math.comb(39,6-k)/den for k in range(7)]

def exact_sum_tail(observed,n):
    pmf=exact_hit_pmf();dist=[1.]
    for _ in range(n):
        nxt=[0.]*(len(dist)+6)
        for i,p in enumerate(dist):
            for k,q in enumerate(pmf):nxt[i+k]+=p*q
        dist=nxt
    return min(1.,sum(dist[observed:]))

def holm(pvalues,alpha=.05):
    ordered=sorted(pvalues,key=lambda key:(pvalues[key],key));m=len(ordered);adjusted={};previous=0.
    for i,key in enumerate(ordered):
        previous=max(previous,min(1.,(m-i)*pvalues[key]));adjusted[key]=previous
    return {k:{'raw_p':pvalues[k],'holm_p':adjusted[k],'reject':adjusted[k]<=alpha} for k in ordered}

def summarize(hits):
    assert hits and all(type(h)==int and 0<=h<=6 for h in hits)
    n=len(hits);hist=Counter(hits);pmf=exact_hit_pmf();mean=statistics.mean(hits)
    return {'n':n,'mean_hits':mean,'population_variance':statistics.pvariance(hits),'distribution_0_6':[hist[k] for k in range(7)],
        'rates':{str(k):sum(h>=k for h in hits)/n for k in range(2,7)},'delta_mean_vs_random':mean-.8,
        'exact_uniform_null_upper_tail_p':exact_sum_tail(sum(hits),n),'random_pmf':pmf,
        'bounded_mean_95_halfwidth':6*math.sqrt(math.log(40)/(2*n))}

def portfolio_summary(line_hits):
    assert all(len(v)==3 for v in line_hits)
    means=[sum(v)/3 for v in line_hits];n=len(means);delta=statistics.mean(means)-.8
    # Valid under conditional fairness even when policy adapts to prior draws.
    return {'n':n,'mean_hits_per_line':statistics.mean(means),'mean_total_hits':statistics.mean(sum(v) for v in line_hits),
        'any_line_rates':{str(k):sum(max(v)>=k for v in line_hits)/n for k in range(2,7)},
        'conditional_fair_null_hoeffding_upper_p':math.exp(-2*n*max(0.,delta)**2/36),
        'note':'Portfolio lines are dependent; never use independent-line binomial null.'}

def validate_registration_table(rows,first=1245,last=1444):
    # Caller must provide independently collected pre-draw GitHub publication proof.
    assert sorted(int(r['target_round']) for r in rows)==list(range(first,last+1))
    for r in rows:
        assert r['published_before_draw_verified']=='YES'
        assert len(r['prediction_sha256'])==64 and len(r['prediction_commit'])==40
        assert r['publication_evidence_uri'].startswith('https://github.com/')
    return True
