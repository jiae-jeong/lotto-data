"""Independent replay of saved selection/calibration records; never changes study rules."""
import argparse,csv,hashlib,json,math,statistics
from collections import Counter,defaultdict
from pathlib import Path

def rows(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def mean(x):return sum(x)/len(x)
def select(history,family,w,z):
    a=history[-w:];b=history[-2*w:-w]
    means=[mean([r[j] for r in a]) for j in range(7)]
    if family=='mean':return max(range(7),key=lambda j:(means[j],-j))
    if family=='2plus':return max(range(7),key=lambda j:(sum(r[j]>=2 for r in a),-j))
    eligible=[]
    for j in range(7):
        av=[r[j] for r in a];bv=[r[j] for r in b]
        zs=(means[j]-mean(bv))/math.sqrt(statistics.pvariance(av)/w+statistics.pvariance(bv)/w+1e-9)
        if zs>=z:eligible.append(j)
    return max(eligible,key=lambda j:(means[j],-j)) if eligible else 7

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--study',type=Path,required=True);args=ap.parse_args();d=args.study
    freeze=json.loads((d/'FROZEN_SPEC.json').read_text(encoding='utf-8'))
    assert freeze['code_sha256']==sha(d/'run_study.py')
    for r in rows(d/'SHA256_MANIFEST.csv'):
        p=d/r['file'];assert p.stat().st_size==int(r['bytes']) and sha(p)==r['sha256']
    models=freeze['component_models']+['combined_equal_rank'];base=rows(d/'base_predictions_reused.csv')
    lookup={};H=[]
    for r in base:
        t=int(r['target_round']);m=r['model'];assert int(r['training_through_round'])==t-1
        p=set(map(int,r['predicted_numbers'].split()));a=set(map(int,r['actual_numbers'].split()))
        assert len(p)==6 and len(a)==6 and len(p&a)==int(r['hits'])
        assert (t,m) not in lookup;lookup[t,m]=r
    for t in range(201,1246):H.append([int(lookup[t,m]['hits']) for m in models])
    inner=rows(d/'inner_policy_walkforward.csv');inner_map={};configs=[];inner_count=0
    for r in inner:
        t=int(r['target_round']);w=int(r['window']);z=float(r['threshold']);family=r['family']
        assert int(r['training_through_round'])==t-1 and int(r['feature_end'])==t-1
        j=select(H[:t-201],family,w,z);assert r['selected_model']==models[j]
        assert int(r['hits'])==int(lookup[t,models[j]]['hits'])
        assert int(r['feature_start'])==t-(2*w if family=='regime' else w)
        inner_map[t,r['policy_id']]=r;inner_count+=1
        if (r['policy_id'],family) not in configs:configs.append((r['policy_id'],family))
    trace=rows(d/'selection_trace.csv');selection_count=0;diagnosis=defaultdict(list)
    for r in trace:
        t=int(r['target_round']);name=r['model'];family={'D001_nested_mean':'mean','D002_nested_2plus':'2plus','D003_nested_regime':'regime'}[name]
        assert int(r['training_through_round'])==t-1 and int(r['maximum_outcome_used_in_selection'])==t-1
        assert int(r['hyperparameter_validation_start'])==t-200 and int(r['hyperparameter_validation_end'])==t-1 and int(r['inner_n'])==200
        possible=[cid for cid,f in configs if f==family];utilities={}
        for cid in possible:
            hs=[int(inner_map[u,cid]['hits']) for u in range(t-200,t)]
            utilities[cid]=sum(h>=2 for h in hs) if family=='2plus' else sum(hs)
        best=max(possible,key=lambda cid:(utilities[cid],-possible.index(cid)))
        assert r['chosen_policy']==best
        ir=inner_map[t,best];assert r['selected_component']==ir['selected_model']
        assert math.isclose(float(r['inner_objective']),utilities[best]/200,abs_tol=1e-12)
        selected=r['selected_component'];cached=lookup[t,selected]
        assert r['predicted_numbers']==cached['predicted_numbers'] and int(r['hits'])==int(cached['hits'])
        selection_count+=1;w=int(ir['window']);j=models.index(selected);prior=H[t-201-w:t-201]
        diagnosis[name].append({'prior_selected_mean':mean([row[j] for row in prior]),'next_hits':int(r['hits']),
                               'inner_objective':float(r['inner_objective']),'model':selected,'trigger':int(r['regime_trigger'])})
    all_hits=defaultdict(list)
    for m in models:all_hits[m]=[int(lookup[t,m]['hits']) for t in range(601,1246)]
    new=rows(d/'new_strategy_predictions.csv');seen=set()
    for r in new:
        t=int(r['target_round']);m=r['model'];assert (t,m) not in seen;seen.add((t,m))
        assert 601<=t<=1245 and int(r['training_through_round'])==t-1
        p=set(map(int,r['predicted_numbers'].split()));a=set(map(int,r['actual_numbers'].split()))
        assert len(p)==6 and a==set(map(int,lookup[t,models[0]]['actual_numbers'].split())) and int(r['hits'])==len(p&a)
        all_hits[m].append(int(r['hits']))
    view_slices={'overall_601_1245':slice(0,645),'recent200':slice(445,645),'recent100':slice(545,645),'recent50':slice(595,645),
                 'historical_holdout_1201_1245':slice(600,645),'block_601_800':slice(0,200),'block_801_1000':slice(200,400),'block_1001_1200':slice(400,600)}
    metric_count=0
    for r in rows(d/'model_metrics.csv'):
        h=all_hits[r['model']][view_slices[r['view']]];n=len(h);assert n==int(r['n'])
        assert math.isclose(mean(h),float(r['mean_hits']),abs_tol=1e-12)
        assert math.isclose(statistics.pvariance(h),float(r['variance_hits_population']),abs_tol=1e-12)
        for k in range(7):assert sum(x==k for x in h)==int(r[f'hits_{k}_count'])
        for k in [2,3,4,5,6]:assert math.isclose(sum(x>=k for x in h)/n,float(r[f'rate_ge_{k}']),abs_tol=1e-12)
        metric_count+=1
    null=json.loads((d/'exact_uniform_baseline.json').read_text());p=[math.comb(6,k)*math.comb(39,6-k)/math.comb(45,6) for k in range(7)]
    assert all(math.isclose(x,y,abs_tol=1e-14) for x,y in zip(p,null['probabilities_0_6']))
    assert math.isclose(sum(k*v for k,v in enumerate(p)),.8,abs_tol=1e-14)
    out=[]
    for name,rr in diagnosis.items():
        switches=sum(a['model']!=b['model'] for a,b in zip(rr,rr[1:]));prior_mean=mean([r['prior_selected_mean'] for r in rr]);actual=mean([r['next_hits'] for r in rr])
        out.append({'model':name,'n':len(rr),'prior_chosen_component_window_mean':prior_mean,'next_draw_mean':actual,
                    'prior_to_next_mean_drop':prior_mean-actual,'model_switch_count':switches,'model_switch_rate':switches/(len(rr)-1),
                    'regime_trigger_count':sum(r['trigger'] for r in rr),'regime_fallback_count':len(rr)-sum(r['trigger'] for r in rr) if name=='D003_nested_regime' else '',
                    'interpretation':'POST_HOC_DIAGNOSTIC; selected in-window performance is not out-of-window evidence'})
    with (d/'selection_optimism_diagnostic.csv').open('x',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
    result={'status':'PASS','frozen_code_and_manifest':'PASS','independent_inner_replays':inner_count,'independent_nested_outer_replays':selection_count,
            'new_ticket_hit_checks':len(new),'metric_rows_independently_recomputed':metric_count,'exact_null_checked':True,'future_predictions_generated':False,
            'diagnostic':out}
    with (d/'INDEPENDENT_VERIFICATION.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
