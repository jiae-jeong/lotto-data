#!/usr/bin/env python3
from __future__ import annotations
import csv, importlib.util, itertools, json, math, random, statistics
from collections import Counter, deque
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'lotto_data.csv'
B_SOURCE = ROOT / 'research/1245_final_pipeline_v3/recovered_original_assets/b_model_backtest.py'
AC_SOURCE = ROOT / 'automation/recovered_models_v2.py'
OUT = ROOT / 'analysis/2026-10-23/TODAY_RESEARCH_PORTFOLIO_1247_V8.json'
KST = timezone(timedelta(hours=9))
B_NAMES = ('long_frequency','current_gap','frequency_plus_gap','recent_momentum','structure_profile','pair_association','triple_association','combined_equal_rank')
AC_NAMES = ('A_v2','C_v2','contrarian_v2')
MODELS = B_NAMES + AC_NAMES
ROLL = 200
PRIOR_N = 75
RANDOM_PER_TARGET = 120
BLOCK = 50
BOOT = 4000
SEED = 202610231530
BASE_MEAN = 0.8
BASE_GE2 = 0.17530810086113546

ROLES = [
    ('consensus', MODELS),
    ('relation', ('pair_association','triple_association','structure_profile','combined_equal_rank')),
    ('frequency_gap', ('long_frequency','current_gap','frequency_plus_gap')),
    ('recent_structure', ('recent_momentum','structure_profile','combined_equal_rank')),
    ('ac_crosscheck', ('A_v2','C_v2','contrarian_v2','long_frequency')),
]


def imp(path, name):
    s = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def load_draws():
    out=[]
    with DATA.open(encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            out.append({'round':int(r['round']), 'date':r['date'], 'nums':tuple(sorted(int(r[f'no{i}']) for i in range(1,7)))})
    assert out[-1]['round']==1246
    assert [x['round'] for x in out] == list(range(1,1247))
    return out


def reliability(hist):
    hs=list(hist)[-ROLL:]
    n=len(hs)
    if n==0:
        return 1.0
    mean=(sum(hs)+PRIOR_N*BASE_MEAN)/(n+PRIOR_N)
    ge2=(sum(h>=2 for h in hs)+PRIOR_N*BASE_GE2)/(n+PRIOR_N)
    raw = 1.0 + 2.8*(mean-BASE_MEAN) + 1.2*(ge2-BASE_GE2)
    return max(0.35, min(1.65, raw))


def global_support(preds, hists):
    rel={m:reliability(hists[m]) for m in MODELS}
    den=sum(rel.values())
    score={n:sum(rel[m] for m in MODELS if n in preds[m])/den for n in range(1,46)}
    return score, rel


def role_score(role_models, preds, rel, gscore):
    den=sum(rel[m] for m in role_models)
    rs={n:sum(rel[m] for m in role_models if n in preds[m])/den for n in range(1,46)}
    return {n:0.78*rs[n]+0.22*gscore[n] for n in range(1,46)}


def choose_ticket(score, gscore, prior_lines, role_name):
    pool=sorted(range(1,46), key=lambda n:(-score[n],-gscore[n],n))[:16]
    best=None
    for t in itertools.combinations(pool,6):
        if prior_lines and tuple(t) in prior_lines:
            continue
        odd=sum(n%2 for n in t)
        low=sum(n<=22 for n in t)
        bands=len({(n-1)//10 for n in t})
        cons=sum(b-a==1 for a,b in zip(t,t[1:]))
        val=sum(score[n] for n in t)
        val -= 0.022*abs(odd-3) + 0.020*abs(low-3) + 0.010*max(0,cons-2)
        val += 0.004*bands
        if prior_lines:
            load={n:sum(n in x for x in prior_lines) for n in t}
            val -= sum(0.016*load[n] for n in t if gscore[n] < 0.30)
        if role_name=='ac_crosscheck' and prior_lines:
            val -= 0.018*max(len(set(t)&set(x)) for x in prior_lines)
        key=(val, tuple(-n for n in t))
        if best is None or key>best[0]:
            best=(key,t)
    assert best is not None
    return tuple(sorted(best[1]))


def build_portfolio(preds, hists):
    gscore, rel = global_support(preds,hists)
    lines=[]; details=[]
    for role_name, role_models in ROLES:
        rs=role_score(role_models,preds,rel,gscore)
        ticket=choose_ticket(rs,gscore,lines,role_name)
        lines.append(ticket)
        details.append({
            'role':role_name,
            'models':list(role_models),
            'ticket':list(ticket),
            'numbers':[
                {'number':n,'role_score':rs[n],'global_support':gscore[n],
                 'supporting_models':[m for m in MODELS if n in preds[m]]}
                for n in ticket
            ]
        })
    assert len(lines)==5 and len({tuple(x) for x in lines})==5
    return lines, details, rel, gscore


def metrics(lines, actual):
    ss=[set(x) for x in lines]
    hits=[len(s&actual) for s in ss]
    union=set().union(*ss)
    ovs=[len(ss[i]&ss[j]) for i in range(5) for j in range(i+1,5)]
    return {
        'max_hits':max(hits), 'any2':int(max(hits)>=2), 'any3':int(max(hits)>=3),
        'any4':int(max(hits)>=4), 'any5':int(max(hits)>=5), 'any6':int(max(hits)>=6),
        'winning_union_coverage':len(union&actual), 'union_size':len(union),
        'mean_overlap':statistics.mean(ovs), 'max_overlap':max(ovs)
    }


def permuted(lines, rng):
    labels=list(range(1,46)); shuffled=labels[:]; rng.shuffle(shuffled)
    mp=dict(zip(labels,shuffled))
    return [tuple(sorted(mp[n] for n in row)) for row in lines]


def bootstrap_ci(diffs, alpha, seed):
    blocks=[diffs[i:i+BLOCK] for i in range(0,len(diffs),BLOCK)]
    rng=random.Random(seed); reps=[]
    for _ in range(BOOT):
        sampled=[blocks[rng.randrange(len(blocks))] for __ in range(len(blocks))]
        flat=[x for b in sampled for x in b]
        reps.append(statistics.mean(flat))
    reps.sort()
    lo=reps[int((alpha/2)*(len(reps)-1))]
    hi=reps[int((1-alpha/2)*(len(reps)-1))]
    return [lo,hi]


def positive_block_share(diffs):
    vals=[statistics.mean(diffs[i:i+BLOCK]) for i in range(0,len(diffs),BLOCK)]
    return sum(v>0 for v in vals)/len(vals)


def avg(rows,k):
    return statistics.mean(float(r[k]) for r in rows)


def main():
    draws=load_draws(); b=imp(B_SOURCE,'b_v8'); ac=imp(AC_SOURCE,'ac_v8')
    bank=b.feature_structure_bank(b.make_structure_bank())
    freq=[0]*45; last=[0]*45; pc=Counter(); tc=Counter(); profiles=[Counter() for _ in range(6)]
    for d in draws[:200]:
        for x in d['nums']:
            freq[x-1]+=1; last[x-1]=d['round']
        pc.update(itertools.combinations(d['nums'],2)); tc.update(itertools.combinations(d['nums'],3))
        pr=b.structure_profile(d['nums'],None)
        for i,v in enumerate(pr[:5]): profiles[i][v]+=1
    for i in range(1,200):
        profiles[5][b.structure_profile(draws[i]['nums'],draws[i-1]['nums'])[5]]+=1

    hists={m:deque(maxlen=ROLL) for m in MODELS}
    obs=[]; null=[]; diffs={k:[] for k in ('max_hits','any2','any3','winning_union_coverage')}
    current=None; current_details=None; current_rel=None; current_g=None; current_preds=None

    for idx in range(200,len(draws)+1):
        hist=[x['nums'] for x in draws[:idx]]
        preds={**b.predictions_for_round(draws,idx,freq,last,pc,tc,profiles,bank), **ac.predict(hist)}
        lines,details,rel,gscore=build_portfolio(preds,hists)
        if idx==len(draws):
            current=lines; current_details=details; current_rel=rel; current_g=gscore; current_preds=preds
            break
        actual=set(draws[idx]['nums']); target=idx+1
        if target>=401:
            om=metrics(lines,actual); om['target']=target; obs.append(om)
            rng=random.Random(SEED+target); nm=[]
            for _ in range(RANDOM_PER_TARGET): nm.append(metrics(permuted(lines,rng),actual))
            mean_null={k:statistics.mean(float(x[k]) for x in nm) for k in nm[0]}
            mean_null['target']=target; null.append(mean_null)
            for k in diffs: diffs[k].append(float(om[k])-mean_null[k])
        for m in MODELS:
            hists[m].append(len(set(preds[m])&actual))
        d=draws[idx]
        for x in d['nums']:
            freq[x-1]+=1; last[x-1]=d['round']
        pc.update(itertools.combinations(d['nums'],2)); tc.update(itertools.combinations(d['nums'],3))
        pr=b.structure_profile(d['nums'],draws[idx-1]['nums'])
        for i,v in enumerate(pr): profiles[i][v]+=1

    keys=['max_hits','any2','any3','any4','any5','any6','winning_union_coverage','union_size','mean_overlap','max_overlap']
    score={'policy':{k:avg(obs,k) for k in keys}, 'matched_label_permutation':{k:avg(null,k) for k in keys}}
    score['delta']={k:score['policy'][k]-score['matched_label_permutation'][k] for k in keys}
    alpha=.05/4
    inference={}
    for j,k in enumerate(diffs):
        inference[k]={
            'adjusted_ci_delta':bootstrap_ci(diffs[k],alpha,SEED+9000+j),
            'positive_50_round_block_share':positive_block_share(diffs[k])
        }
    inference['strict_portfolio_pass']=(
        inference['max_hits']['adjusted_ci_delta'][0]>0 and
        inference['any2']['adjusted_ci_delta'][0]>0 and
        inference['any3']['adjusted_ci_delta'][0]>0 and
        inference['any2']['positive_50_round_block_share']>=0.65
    )

    final_lines=[list(x) for x in current]
    flat=[n for row in final_lines for n in row]
    integrity={
        'five_distinct_lines':len(final_lines)==5 and len({tuple(x) for x in final_lines})==5,
        'six_numbers_each':all(len(x)==6 for x in final_lines),
        'range_unique_sorted':all(x==sorted(x) and len(set(x))==6 and all(1<=n<=45 for n in x) for x in final_lines),
        'union_size':len(set(flat)),
    }
    assert all(v is True for k,v in integrity.items() if k!='union_size')
    payload={
        'created_kst':datetime.now(KST).isoformat(), 'target_round':1247, 'data_cutoff':1246,
        'policy':'FIXED_FIVE_ROLE_RESEARCH_PORTFOLIO_V8', 'no_future_leakage':True,
        'selection_rule':'All five lines are generated only from historical model predictions and trailing historical model reliability; no uniform/random fallback is used for selection.',
        'roles':current_details, 'model_reliability':current_rel,
        'current_model_predictions':{m:list(current_preds[m]) for m in MODELS},
        'global_number_support':{str(n):current_g[n] for n in range(1,46)},
        'final_lines':final_lines, 'walkforward_targets':len(obs),
        'random_comparator':'Random permutation of labels 1..45 applied jointly to the five selected tickets, preserving exact union size and every cross-ticket overlap.',
        'random_per_target':RANDOM_PER_TARGET, 'scorecard':score, 'inference':inference,
        'integrity':integrity,
        'classification':'RESEARCH_BASED_ACTUAL_PURCHASE_CANDIDATE' if not inference['strict_portfolio_pass'] else 'STRICTLY_VALIDATED_RESEARCH_PORTFOLIO'
    }
    OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':'PASS','target':1247,'strict_pass':inference['strict_portfolio_pass'],'scorecard':score,'inference':inference,'final_lines':final_lines,'roles':[x['role'] for x in current_details],'union_size':integrity['union_size']},ensure_ascii=False))

if __name__=='__main__':
    main()
