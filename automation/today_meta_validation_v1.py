#!/usr/bin/env python3
from __future__ import annotations

import csv, importlib.util, itertools, json, math, random, statistics, sys
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'lotto_data.csv'
RUN_DIR=ROOT/'analysis/2026-10-23/MASTER_FULL_V5_233420_110068'
B_DIR=ROOT/'analysis/2026-10-23/MASTER_FULL_V4_232811_580357'
B_SOURCE=ROOT/'research/1245_final_pipeline_v3/recovered_original_assets/b_model_backtest.py'
AC_SOURCE=ROOT/'automation/recovered_models_v2.py'
KST=timezone(timedelta(hours=9))
ROLL=200
BLOCK=50
BOOT=10000
SEED=202610231135
B_NAMES=('long_frequency','current_gap','frequency_plus_gap','recent_momentum','structure_profile','pair_association','triple_association','combined_equal_rank')
AC_NAMES=('A_v2','C_v2','contrarian_v2')
MODELS=B_NAMES+AC_NAMES


def load_draws():
    rows=[]
    with DATA.open(encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            rows.append({'round':int(r['round']),'date':r['date'],'nums':tuple(sorted(int(r[f'no{i}']) for i in range(1,7)))})
    assert [x['round'] for x in rows]==list(range(1,len(rows)+1))
    return rows


def read_hit_history():
    hist=defaultdict(dict)
    with (B_DIR/'B_PREDICTIONS_UNIQUE.csv').open(encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            t=int(r['target_round']); tr=int(r['training_through_round']); m=r['model']
            assert tr==t-1
            hist[m][t]=int(r['hits'])
    with (RUN_DIR/'AC_CONTRARIAN_WALKFORWARD.csv').open(encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            t=int(r['target_round']); tr=int(r['training_through_round']); m=r['model']
            assert tr==t-1
            hist[m][t]=int(r['hits'])
    targets=set(range(201,1247))
    assert set(hist)==set(MODELS)
    for m in MODELS: assert set(hist[m])==targets
    return hist


def exact_single():
    den=math.comb(45,6)
    p={k:math.comb(6,k)*math.comb(39,6-k)/den for k in range(7)}
    ge={k:sum(p[j] for j in range(k,7)) for k in range(1,7)}
    return {'p':p,'mean':sum(k*p[k] for k in p),'ge':ge}


def exact_portfolio5(single):
    ge={k:1-(1-single['ge'][k])**5 for k in range(1,7)}
    return {'mean_max':sum(ge.values()),'ge':ge,'assumption':'5 independent uniform tickets'}


def ranking_for_target(hist,target):
    lo=max(201,target-ROLL); prev=list(range(lo,target))
    assert prev and max(prev)<target
    rows=[]
    for m in MODELS:
        hs=[hist[m][t] for t in prev]
        n=len(hs)
        # fixed shrinkage toward exact random expectation; no target outcome is used.
        shrunk=(sum(hs)+100*0.8)/(n+100)
        ge2=sum(h>=2 for h in hs)/n
        ge3=sum(h>=3 for h in hs)/n
        recent50=statistics.mean(hs[-50:]) if len(hs)>=50 else statistics.mean(hs)
        rows.append((shrunk,ge2,ge3,recent50,m))
    rows.sort(reverse=True)
    return rows


def eval_policies(hist):
    single=exact_single(); p5=exact_portfolio5(single)
    single_rows=[]; port_rows=[]
    for t in range(401,1247):
        rank=ranking_for_target(hist,t)
        champ=rank[0][-1]
        h=hist[champ][t]
        single_rows.append({'target':t,'model':champ,'hits':h,'ge2':int(h>=2),'ge3':int(h>=3)})
        top5=[r[-1] for r in rank[:5]]
        hs=[hist[m][t] for m in top5]
        mx=max(hs)
        port_rows.append({'target':t,'models':top5,'max_hits':mx,'any2':int(mx>=2),'any3':int(mx>=3),'any4':int(mx>=4)})

    def block_values(rows,key,base):
        vals=[]
        for i in range(0,len(rows),BLOCK):
            b=rows[i:i+BLOCK]
            vals.append(statistics.mean(float(x[key]) for x in b)-base)
        return vals

    def boot_blocks(rows,key,base,alpha,seed):
        blocks=[]
        for i in range(0,len(rows),BLOCK):
            b=rows[i:i+BLOCK]
            blocks.append([float(x[key])-base for x in b])
        rng=random.Random(seed); reps=[]
        for _ in range(BOOT):
            chosen=[blocks[rng.randrange(len(blocks))] for __ in range(len(blocks))]
            flat=[x for b in chosen for x in b]
            reps.append(statistics.mean(flat))
        reps.sort()
        lo=reps[max(0,int((alpha/2)*len(reps))-1)]
        hi=reps[min(len(reps)-1,int((1-alpha/2)*len(reps)))]
        return [lo,hi]

    alpha=0.05/5 # two single-ticket primary tests + three portfolio primary tests
    s_obs={'mean_hits':statistics.mean(x['hits'] for x in single_rows),'ge2':statistics.mean(x['ge2'] for x in single_rows),'ge3':statistics.mean(x['ge3'] for x in single_rows)}
    s_base={'mean_hits':single['mean'],'ge2':single['ge'][2],'ge3':single['ge'][3]}
    s_ci={
        'mean_hits':boot_blocks(single_rows,'hits',s_base['mean_hits'],alpha,SEED+1),
        'ge2':boot_blocks(single_rows,'ge2',s_base['ge2'],alpha,SEED+2),
    }
    s_blocks=block_values(single_rows,'hits',s_base['mean_hits'])
    s_pass=s_ci['mean_hits'][0]>0 and s_ci['ge2'][0]>0 and sum(v>0 for v in s_blocks)/len(s_blocks)>=0.65

    p_obs={'max_hits':statistics.mean(x['max_hits'] for x in port_rows),'any2':statistics.mean(x['any2'] for x in port_rows),'any3':statistics.mean(x['any3'] for x in port_rows),'any4':statistics.mean(x['any4'] for x in port_rows)}
    p_base={'max_hits':p5['mean_max'],'any2':p5['ge'][2],'any3':p5['ge'][3],'any4':p5['ge'][4]}
    p_ci={
        'max_hits':boot_blocks(port_rows,'max_hits',p_base['max_hits'],alpha,SEED+11),
        'any2':boot_blocks(port_rows,'any2',p_base['any2'],alpha,SEED+12),
        'any3':boot_blocks(port_rows,'any3',p_base['any3'],alpha,SEED+13),
    }
    p_blocks=block_values(port_rows,'any2',p_base['any2'])
    p_pass=p_ci['max_hits'][0]>0 and p_ci['any2'][0]>0 and p_ci['any3'][0]>0 and sum(v>0 for v in p_blocks)/len(p_blocks)>=0.65
    return {
        'test_targets':[401,1246],'n_targets':len(single_rows),'rolling_window':ROLL,
        'multiple_testing_alpha':alpha,
        'single_champion':{'observed':s_obs,'baseline':s_base,'delta':{k:s_obs[k]-s_base[k] for k in s_obs},'adjusted_block_bootstrap_ci_delta':s_ci,'positive_50round_block_share_mean_hits':sum(v>0 for v in s_blocks)/len(s_blocks),'pass':s_pass},
        'top5_portfolio':{'observed':p_obs,'baseline':p_base,'delta':{k:p_obs[k]-p_base[k] for k in p_obs},'adjusted_block_bootstrap_ci_delta':p_ci,'positive_50round_block_share_any2':sum(v>0 for v in p_blocks)/len(p_blocks),'pass':p_pass},
    }


def import_file(path,name):
    spec=importlib.util.spec_from_file_location(name,path); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


def current_b_forecast(draws):
    b=import_file(B_SOURCE,'bsource_today')
    bank=b.feature_structure_bank(b.make_structure_bank()); freq=[0]*45; last=[0]*45; pc=Counter(); tc=Counter(); profiles=[Counter() for _ in range(6)]
    for d in draws[:200]:
        for x in d['nums']: freq[x-1]+=1; last[x-1]=d['round']
        pc.update(itertools.combinations(d['nums'],2)); tc.update(itertools.combinations(d['nums'],3)); pr=b.structure_profile(d['nums'],None)
        for i,v in enumerate(pr[:5]): profiles[i][v]+=1
    for i in range(1,200): profiles[5][b.structure_profile(draws[i]['nums'],draws[i-1]['nums'])[5]]+=1
    for idx in range(200,len(draws)):
        d=draws[idx]
        for x in d['nums']: freq[x-1]+=1; last[x-1]=d['round']
        pc.update(itertools.combinations(d['nums'],2)); tc.update(itertools.combinations(d['nums'],3)); pr=b.structure_profile(d['nums'],draws[idx-1]['nums'])
        for i,v in enumerate(pr): profiles[i][v]+=1
    return b.predictions_for_round(draws,len(draws),freq,last,pc,tc,profiles,bank)


def current_predictions(draws):
    bpred=current_b_forecast(draws)
    ac=import_file(AC_SOURCE,'ac_today').predict([d['nums'] for d in draws])
    out={**bpred,**ac}
    assert set(out)==set(MODELS)
    return {k:list(v) for k,v in out.items()}


def main():
    draws=load_draws(); assert draws[-1]['round']==1246
    hist=read_hit_history(); audit=eval_policies(hist)
    rank=ranking_for_target(hist,1247); preds=current_predictions(draws)
    ordered=[r[-1] for r in rank]
    champ=ordered[0]
    distinct=[]; used=set()
    for m in ordered:
        t=tuple(preds[m])
        if t not in used:
            distinct.append(m); used.add(t)
        if len(distinct)==5: break
    payload={
        'created_kst':datetime.now(KST).isoformat(),'target_round':1247,'data_cutoff':1246,
        'policy':'ROLLING_META_MODEL_V1_NO_FUTURE_LEAKAGE','models':list(MODELS),
        'audit':audit,'current_ranking':[{'model':r[-1],'shrunk_mean':r[0],'ge2':r[1],'ge3':r[2],'recent50_mean':r[3]} for r in rank],
        'current_predictions':preds,'current_single_champion':{'model':champ,'ticket':preds[champ]},
        'current_top5_distinct':{'models':distinct,'tickets':[preds[m] for m in distinct]},
        'model_validated_for_1247':bool(audit['single_champion']['pass'] or audit['top5_portfolio']['pass']),
        'final_status':'MODEL_VALIDATED' if audit['top5_portfolio']['pass'] else 'NO_VALIDATED_FINAL',
    }
    out=ROOT/'analysis/2026-10-23/TODAY_META_VALIDATION_1247_V1.json'
    out.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if audit['top5_portfolio']['pass']:
        f=ROOT/'research/weekly_purchase/1247/FINAL_FIVE_LINES_1247_20261023_META_V1.json'
        if f.exists(): raise SystemExit(f'write-once: {f}')
        f.write_text(json.dumps({'target_round':1247,'data_cutoff':1246,'policy':'ROLLING_META_MODEL_V1','validation':'PASS','models':distinct,'final_lines':[preds[m] for m in distinct],'audit':audit['top5_portfolio']},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':'PASS','target':1247,'single_pass':audit['single_champion']['pass'],'portfolio_pass':audit['top5_portfolio']['pass'],'champion':champ,'top5':distinct,'tickets':[preds[m] for m in distinct],'report':str(out)},ensure_ascii=False))

if __name__=='__main__': main()
