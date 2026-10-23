#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
import random
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
KST=timezone(timedelta(hours=9))
SEED=202610231120
BOOT_REPS=5000
BLOCK_SIZE=50


def exact_baseline():
    den=math.comb(45,6)
    p={k:math.comb(6,k)*math.comb(39,6-k)/den for k in range(7)}
    return {
        'mean_hits':sum(k*p[k] for k in p),
        'rate_ge2':sum(p[k] for k in range(2,7)),
        'rate_ge3':sum(p[k] for k in range(3,7)),
        'rate_ge4':sum(p[k] for k in range(4,7)),
        'rate_ge5':sum(p[k] for k in range(5,7)),
        'rate_ge6':p[6],
        'hit_probabilities':p,
    }


def quantile(xs,q):
    xs=sorted(xs)
    idx=min(len(xs)-1,max(0,int(q*(len(xs)-1))))
    return xs[idx]


def bootstrap_ci(values, baseline, alpha, seed):
    rng=random.Random(seed); n=len(values); means=[]
    for _ in range(BOOT_REPS):
        means.append(sum(values[rng.randrange(n)] for __ in range(n))/n - baseline)
    return [quantile(means,alpha/2),quantile(means,1-alpha/2)]


def read_hits(path, model_col='model', hit_col='hits'):
    out=defaultdict(list); targets=defaultdict(list)
    with path.open(encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            out[r[model_col]].append(int(r[hit_col])); targets[r[model_col]].append(int(r['target_round']))
    return out,targets


def block_share(hits, baseline_mean):
    vals=[]
    for i in range(0,len(hits),BLOCK_SIZE):
        b=hits[i:i+BLOCK_SIZE]
        vals.append(statistics.mean(b)-baseline_mean)
    return {'positive_share':sum(v>0 for v in vals)/len(vals),'block_deltas':vals,'blocks':len(vals)}


def summarize_model(hits, base, alpha_adj, seed):
    metrics={
        'mean_hits':[float(h) for h in hits],
        'rate_ge2':[float(h>=2) for h in hits],
        'rate_ge3':[float(h>=3) for h in hits],
        'rate_ge4':[float(h>=4) for h in hits],
        'rate_ge5':[float(h>=5) for h in hits],
        'rate_ge6':[float(h>=6) for h in hits],
    }
    out={'n':len(hits),'observed':{},'random_exact':{},'delta':{},'ci95_delta':{},'ci_bonferroni_delta':{}}
    for j,(k,vals) in enumerate(metrics.items()):
        obs=statistics.mean(vals); b=base[k]
        out['observed'][k]=obs; out['random_exact'][k]=b; out['delta'][k]=obs-b
        out['ci95_delta'][k]=bootstrap_ci(vals,b,0.05,seed+j*101)
        out['ci_bonferroni_delta'][k]=bootstrap_ci(vals,b,alpha_adj,seed+j*101+9000)
    out['time_blocks_mean_hits']=block_share(hits,base['mean_hits'])
    out['edge_gate']={
        'mean_hits_adjusted_ci_lower_gt_0':out['ci_bonferroni_delta']['mean_hits'][0]>0,
        'rate_ge2_adjusted_ci_lower_gt_0':out['ci_bonferroni_delta']['rate_ge2'][0]>0,
        'positive_50round_block_share_ge_65pct':out['time_blocks_mean_hits']['positive_share']>=0.65,
    }
    out['edge_pass']=all(out['edge_gate'].values())
    return out


def main():
    date=sys.argv[1] if len(sys.argv)>1 else datetime.now(KST).date().isoformat()
    day=ROOT/'analysis'/date
    v5=max(day.glob('MASTER_FULL_V5_*'),key=lambda p:p.stat().st_mtime)
    v4=max(day.glob('MASTER_FULL_V4_*'),key=lambda p:p.stat().st_mtime)
    b_leak=json.loads((v4/'B_LEAKAGE_CHECK.json').read_text(encoding='utf-8-sig'))
    ver=json.loads((v5/'VERIFICATION.json').read_text(encoding='utf-8-sig'))
    assert int(ver.get('successor_leakage_failures',1))==0
    assert int(b_leak.get('failures', b_leak.get('leakage_failures',0)))==0

    a_hits,a_targets=read_hits(v5/'AC_CONTRARIAN_WALKFORWARD.csv')
    b_hits,b_targets=read_hits(v4/'B_PREDICTIONS_UNIQUE.csv')
    all_hits={**b_hits,**a_hits}
    all_targets={**b_targets,**a_targets}
    model_count=len(all_hits)
    # Bonferroni correction across models and the two primary tests (mean hits, >=2 rate).
    alpha_adj=0.05/(model_count*2)
    base=exact_baseline()
    models={}
    for i,name in enumerate(sorted(all_hits)):
        ts=all_targets[name]
        assert len(ts)==len(all_hits[name]) and ts==sorted(ts)
        assert all_targets[name][0]>=201 and all_targets[name][-1]==1246
        models[name]=summarize_model(all_hits[name],base,alpha_adj,SEED+i*10000)
        models[name]['target_range']=[ts[0],ts[-1]]

    ranked=sorted(models,key=lambda n:(models[n]['delta']['mean_hits'],models[n]['delta']['rate_ge2']),reverse=True)
    validated=[n for n in ranked if models[n]['edge_pass']]

    v3_path=ROOT/'research'/'weekly_purchase'/'1247'/'FINAL_FIVE_LINES_1247_20261023_PROTOCOL_FULL_V3.json'
    v3=json.loads(v3_path.read_text(encoding='utf-8-sig'))
    h=v3['walkforward_holdout']
    sel=h['holdout_selected']; matched=h['holdout_diversity_matched_random']; independent=h['holdout_independent_random']
    portfolio_audit={
        'stored_promotion_gate_pass':h['promotion_gate_pass'],
        'stored_selected_policy':h['selected_policy'],
        'problem':'V3 promotion compared the selected 30-unique portfolio against ordinary independent random tickets, not against the structure-matched 30-unique random baseline.',
        'selected_vs_diversity_matched_delta':{k:sel[k]-matched[k] for k in ['max_hits','any_2plus','any_3plus','any_4plus','winning_union_coverage']},
        'selected_vs_independent_delta':{k:sel[k]-independent[k] for k in ['max_hits','any_2plus','any_3plus','any_4plus','winning_union_coverage']},
    }
    d=portfolio_audit['selected_vs_diversity_matched_delta']
    portfolio_audit['corrected_model_promotion_status']='FAIL' if (d['any_2plus']<=0 or d['max_hits']<=0 or d['any_3plus']<=0) else 'REQUIRES_FURTHER_TEST'
    portfolio_audit['coverage_note']='A 30-unique portfolio has expected winning-number union coverage 6*(30/45)=4. Coverage near 4 is structural, not predictive evidence.'

    result={
        'date_kst':date,
        'data_cutoff':1246,
        'leakage_checks':{'B':b_leak,'successor_leakage_failures':ver.get('successor_leakage_failures')},
        'exact_uniform_single_ticket_baseline':base,
        'multiple_testing':{'model_count':model_count,'primary_tests_per_model':2,'bonferroni_alpha':alpha_adj,'bootstrap_reps':BOOT_REPS},
        'models':models,
        'ranking_by_mean_hit_delta':ranked,
        'validated_models':validated,
        'portfolio_v3_audit':portfolio_audit,
        'verdict':'MODEL_EDGE_VALIDATED' if validated else 'NO_MODEL_PASSES_STRICT_VALIDATION',
        'rule_for_future_final_numbers':'Do not label a model-guided portfolio as validated unless its untouched time-ordered performance beats a structure-matched random baseline, with positive adjusted confidence bounds and stable non-overlapping time blocks.',
    }
    out=day/'MODEL_VALIDATION_V5_ALL_MODELS_STRICT.json'
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':'PASS','verdict':result['verdict'],'models':model_count,'validated_models':validated,'top3':ranked[:3],'portfolio_v3_corrected_status':portfolio_audit['corrected_model_promotion_status'],'output':str(out)},ensure_ascii=False))

if __name__=='__main__': main()
