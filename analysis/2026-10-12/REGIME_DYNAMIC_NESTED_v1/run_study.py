"""New retrospective regime/dynamic-selection study. No future recommendation."""
from __future__ import annotations
import argparse, csv, hashlib, importlib.util, itertools, json, math, random
import platform, subprocess, sys, time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

sys.dont_write_bytecode = True
EXPECTED_HEAD = '857bea9a7b258c2033f7e752808bb3e52d6de9eb'
MODELS = ['long_frequency','current_gap','frequency_plus_gap','recent_momentum',
          'structure_profile','pair_association','triple_association','combined_equal_rank']
PRIMARY = ['D001_nested_mean','D002_nested_2plus','D003_nested_regime']
SEED = 20261012
WINDOWS = [25,50,100]
CONFIGS = [('mean',w,0.) for w in WINDOWS] + [('2plus',w,0.) for w in WINDOWS] + [
    ('regime',w,z) for w in WINDOWS for z in [1.5,2.0]]
POLICY_IDS = [f'{family}_w{w}_z{z:g}' for family,w,z in CONFIGS]
SPEC = {
 'study_id':'R20261012_REGIME_DYNAMIC_NESTED_V1', 'evidence':'POST_HOC_EXPLORATORY',
 'component_models':MODELS[:7], 'component_source':'unchanged preserved B v1 source',
 'targets':{'base_cache':'201..1245','inner_policy':'401..1245','outer':'601..1245'},
 'windows':WINDOWS,'regime_thresholds':[1.5,2.0],'outer_inner_history':200,
 'D001':'select best trailing mean component; choose window by trailing 200 inner-policy mean hits',
 'D002':'select best trailing 2+ component; choose window by trailing 200 inner-policy 2+ rate',
 'D003':'z=(recent mean-previous mean)/sqrt(recent population variance/w+previous population variance/w+1e-9); positive z>=threshold eligible; choose highest recent mean eligible, else combined_equal_rank; choose window/threshold by trailing 200 inner-policy mean hits',
 'ties':'B source model order; config list order (shorter window, then lower threshold); number ties lower number',
 'equal_weight_ticket_vote':'seven B component tickets, 1 vote per included number per model, top six; lower number tie',
 'equal_rank_reference':'existing combined_equal_rank, four equal rank axes; not seven-ticket vote',
 'uniform_stream':'one six-number uniform ticket per historical target, random.Random(seed+target); exact hypergeometric primary baseline; no repeated large Monte Carlo',
 'uncertainty':'circular moving block bootstrap length20, 5000 resamples; Wilson rate intervals',
 'primary_tests':'3 dynamic strategies x mean/2+/3+/4+ =12 one-sided exact uniform-null tests; Holm12',
 'paired_tests':'3 dynamic x2 ensemble controls x4 metrics=24 exploratory paired block-bootstrap tests; Holm24',
 'recent_views':[200,100,50], 'historical_holdout':'1201..1245; NOT untouched',
 'promotion':'none without subsequent independent prospective evidence', 'seed':SEED,
 'future_predictions':'not generated', 'scope':'new model-selection research; not B reproduction/H001/H002/relation retest'
}

def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def readcsv(p):
    with Path(p).open(encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))
def writecsv(p, rows):
    with Path(p).open('x',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
def writejson(p,v):
    with Path(p).open('x',encoding='utf-8') as f: json.dump(v,f,ensure_ascii=False,indent=2)
def writetext(p,v):
    with Path(p).open('x',encoding='utf-8') as f: f.write(v)
def git(root,*args): return subprocess.check_output(['git','-C',str(root),*args],text=True).strip()
def validate_data(rows,n):
    assert len(rows)==n and [int(r['round']) for r in rows]==list(range(1,n+1))
    assert set(rows[0])=={'round','date','no1','no2','no3','no4','no5','no6','bonus'}
    for r in rows:
        nums=[int(r[f'no{i}']) for i in range(1,7)]; bonus=int(r['bonus'])
        assert len(set(nums))==6 and all(1<=x<=45 for x in nums)
        assert 1<=bonus<=45 and bonus not in nums
    return [{'round':int(r['round']),'date':r['date'],
             'nums':tuple(sorted(int(r[f'no{i}']) for i in range(1,7)))} for r in rows]

def fresh_prefix(b,draws,t,bank):
    prefix=draws[:t-1]; freq=[0]*45; last=[0]*45; pc=Counter();tc=Counter();profiles=[Counter() for _ in range(6)]
    for i,d in enumerate(prefix):
        for x in d['nums']:freq[x-1]+=1;last[x-1]=d['round']
        pc.update(itertools.combinations(d['nums'],2));tc.update(itertools.combinations(d['nums'],3))
        prof=b.structure_profile(d['nums'],prefix[i-1]['nums'] if i else None)
        for j in range(5):profiles[j][prof[j]]+=1
        if i:profiles[5][prof[5]]+=1
    return b.predictions_for_round(prefix,len(prefix),freq,last,pc,tc,profiles,bank)

def policy(prior, family,w,z):
    assert len(prior)>=2*w
    recent=prior[-w:,:7].astype(float); scores=recent.mean(axis=0)
    if family=='mean':return int(np.argmax(scores)),float(np.max(scores)),False
    if family=='2plus':
        scores=(recent>=2).mean(axis=0);return int(np.argmax(scores)),float(np.max(scores)),False
    prev=prior[-2*w:-w,:7].astype(float)
    zs=(scores-prev.mean(axis=0))/np.sqrt(recent.var(axis=0)/w+prev.var(axis=0)/w+1e-9)
    eligible=zs>=z
    if not eligible.any():return 7,float(np.max(zs)),False
    chosen=int(np.argmax(np.where(eligible,scores,-np.inf)))
    return chosen,float(zs[chosen]),True

def inner_grid(H):
    choices=np.full((len(H),len(CONFIGS)),-1,dtype=int)
    realized=np.full((len(H),len(CONFIGS)),np.nan);scores=np.full_like(realized,np.nan);triggers=np.zeros_like(choices,dtype=bool)
    for i in range(200,len(H)):
        for k,cfg in enumerate(CONFIGS):
            selected,score,trigger=policy(H[:i],*cfg)
            choices[i,k]=selected;scores[i,k]=score;triggers[i,k]=trigger
            realized[i,k]=H[i,selected]  # scoring only AFTER the decision
    return choices,realized,scores,triggers

def outer_decision(prior_inner, family):
    assert len(prior_inner)==200 and np.isfinite(prior_inner).all()
    candidates=[k for k,c in enumerate(CONFIGS) if c[0]==family]
    utility=(prior_inner[:,candidates]>=2).sum(axis=0) if family=='2plus' else prior_inner[:,candidates].sum(axis=0)
    k=candidates[int(np.argmax(utility))]
    return k, float(np.max(utility)/200)

def wilson(k,n):
    p=k/n;z=1.959963984540054;d=1+z*z/n
    mid=(p+z*z/(2*n))/d;radius=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return mid-radius,mid+radius
def binomial_upper(k,n,p):
    if k<=0:return 1.
    return min(1.,sum(math.exp(math.lgamma(n+1)-math.lgamma(j+1)-math.lgamma(n-j+1)+j*math.log(p)+(n-j)*math.log1p(-p)) for j in range(k,n+1)))
def holm(rows,pkey,outkey):
    order=sorted(range(len(rows)),key=lambda i:rows[i][pkey]);running=0.
    for rank,i in enumerate(order):running=max(running,min(1.,(len(rows)-rank)*rows[i][pkey]));rows[i][outkey]=running
def metrics(h,model,view):
    n=len(h);out={'model':model,'view':view,'n':n,'mean_hits':float(h.mean()),'variance_hits_population':float(h.var()),'delta_mean_vs_uniform':float(h.mean()-.8)}
    for k in range(7):out[f'hits_{k}_count']=int(np.sum(h==k));out[f'hits_{k}_rate']=float(np.mean(h==k))
    for k in [2,3,4,5,6]:
        count=int(np.sum(h>=k));lo,hi=wilson(count,n)
        out[f'rate_ge_{k}']=count/n;out[f'rate_ge_{k}_wilson_low']=lo;out[f'rate_ge_{k}_wilson_high']=hi
    return out
def block_indices(n,seed):
    rng=np.random.default_rng(seed);starts=rng.integers(0,n,size=(5000,math.ceil(n/20)))
    return ((starts[:,:,None]+np.arange(20))%n).reshape(5000,-1)[:,:n]
def metric_vector(h,k):return h.astype(float) if k==0 else (h>=k).astype(float)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repository',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
    root=args.repository.resolve();out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
    assert git(root,'rev-parse','HEAD')==EXPECTED_HEAD,'Pinned study base HEAD differs'
    if (out/'FROZEN_SPEC.json').exists():raise FileExistsError('Use a new version/output directory; no overwrite')
    started=time.time();tracked=git(root,'ls-files').splitlines();before={p:digest(root/p) for p in tracked}
    raw=root/'lotto_data.csv';snapshot=root/'analysis/2026-10-12/lotto_data_1_1245_snapshot.csv'
    cache=root/'outputs/B_MODEL_REPRODUCTION_20261009_v1/b_model_predictions.csv'
    source=root/'outputs/B_MODEL_REPRODUCTION_20261009_v1/EXECUTED_b_model_backtest.py'
    rawrows=readcsv(raw);rows=readcsv(snapshot);validate_data(rawrows,1244);draws=validate_data(rows,1245)
    assert rawrows==rows[:1244], 'Snapshot differs from original prefix'
    seals={p.relative_to(root).as_posix():digest(p) for p in [raw,snapshot,cache,source,root/'AGENTS.md',root/'LOTTO_PROJECT_PROTOCOL.md']}
    freeze={**SPEC,'created_utc':datetime.now(timezone.utc).isoformat(),'base_head':EXPECTED_HEAD,'input_sha256':seals,'code_sha256':digest(__file__)}
    writejson(out/'FROZEN_SPEC.json',freeze)
    writetext(out/'ANTI_REPETITION_GATE.md', '# Anti-repetition gate — before new evaluation\n\n'
       'Read latest main AGENTS.md and LOTTO_PROJECT_PROTOCOL.md in full; analysis/2026-10-12 daily report/runner; October9/10 relation reports/registries; batch001 report, hypothesis/failure registry and correlation; V4 research registry; prior B/MC status and source.\n\n'
       'Completed: B reproduction; 3.5 million MC baseline; H001/H002 rerun; pair/triple corrected tests (0 surviving); relation WF; basic window/structure statistics; batch001 static and rolling models; S008 cancellation finding. These are not today\'s main study.\n\n'
       'Unresolved in pinned main: performance-regime detectability and nested selection of frozen B components. This asks whether PRE-target performance changes persist and can improve next-target selection. The batch001 gap_regime model concerns number age, NOT model-performance regime.\n\n'
       'MAINTENANCE/RECHECK: data/cached predictions/source integrity; 5 sample prefixes and only missing target1245 extension. NEW STUDY: D001/D002/D003 nested WF. All are historical post-hoc exploration, not prospective confirmation.\n\n'
       'Recovery: default Git DNS path failed; permissioned Git fetch succeeded; old V3 checkout preserved; clean separate checkout has expected HEAD. Native MXC unavailable after permission request; approved executable path used. Bundled Python+NumPy available; SciPy absent, exact tests implemented without SciPy. Missing legacy A/C excluded, not reconstructed.\n')
    spec=importlib.util.spec_from_file_location('preserved_b',source);b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
    assert b.MODEL_NAMES==MODELS and b.STRUCTURE_BANK_SIZE==10000 and b.STRUCTURE_BANK_SEED==20261006
    cached={};duplicate_count=0
    for r in readcsv(cache):
        t=int(r['target_round']);model=r['model'];assert 201<=t<=1244 and int(r['training_through_round'])==t-1
        pred=tuple(map(int,r['predicted_numbers'].split()));actual=tuple(map(int,r['actual_numbers'].split()));hit=int(r['hits'])
        assert len(set(pred))==6 and all(1<=x<=45 for x in pred) and actual==draws[t-1]['nums'] and hit==len(set(pred)&set(actual))
        val=(pred,hit);key=(t,model)
        if key in cached:assert cached[key]==val;duplicate_count+=1
        cached[key]=val
    assert set(cached)=={(t,m) for t in range(201,1245) for m in MODELS}
    bank=b.feature_structure_bank(b.make_structure_bank());sample_checks=[]
    for t in [201,401,801,1201,1244]:
        fresh=fresh_prefix(b,draws,t,bank)
        assert all(fresh[m]==cached[t,m][0] for m in MODELS)
        sample_checks.append({'target':t,'cutoff':t-1,'models_match':8})
    last=fresh_prefix(b,draws,1245,bank)
    for m,pred in last.items():cached[1245,m]=(pred,len(set(pred)&set(draws[1244]['nums'])))
    H=np.array([[cached[t,m][1] for m in MODELS] for t in range(201,1246)],dtype=int)
    base_rows=[{'target_round':t,'training_through_round':t-1,'model':m,'predicted_numbers':' '.join(map(str,cached[t,m][0])),
                'actual_numbers':' '.join(map(str,draws[t-1]['nums'])),'hits':cached[t,m][1],
                'provenance':'REUSED_FROZEN_B_CACHE' if t<=1244 else 'ONE_TARGET_EXTENSION_UNCHANGED_B_FUNCTIONS'} for t in range(201,1246) for m in MODELS]
    writecsv(out/'base_predictions_reused.csv',base_rows)
    choices,inner,scores,triggers=inner_grid(H)
    inner_rows=[]
    for i in range(200,len(H)):
        t=i+201
        for k,c in enumerate(CONFIGS):
            inner_rows.append({'target_round':t,'training_through_round':t-1,'policy_id':POLICY_IDS[k],'family':c[0],'window':c[1],'threshold':c[2],
              'feature_start':t-(2*c[1] if c[0]=='regime' else c[1]),'feature_end':t-1,'selected_model':MODELS[choices[i,k]],
              'pre_target_score':scores[i,k],'regime_trigger':int(triggers[i,k]),'hits':int(inner[i,k])})
    writecsv(out/'inner_policy_walkforward.csv',inner_rows)
    decision_rows=[];prediction_rows=[];series={m:H[400:,j] for j,m in enumerate(MODELS)}
    extra_hits={'equal_weight_ticket_vote':[], 'uniform_seeded_stream':[], 'fixed_mean_w50':[], 'fixed_2plus_w50':[], 'fixed_regime_w50_z1.5':[]}
    dynamic_hits={name:[] for name in PRIMARY};selection_counts={name:Counter() for name in PRIMARY}
    for i in range(400,len(H)):
        t=i+201;actual=set(draws[t-1]['nums'])
        votes=Counter(n for m in MODELS[:7] for n in cached[t,m][0]);vote=tuple(sorted(sorted(range(1,46),key=lambda n:(-votes[n],n))[:6]))
        uniform=tuple(sorted(random.Random(SEED+t).sample(range(1,46),6)))
        decisions={'equal_weight_ticket_vote':vote,'uniform_seeded_stream':uniform}
        for label,cfg in [('fixed_mean_w50',('mean',50,0.)),('fixed_2plus_w50',('2plus',50,0.)),('fixed_regime_w50_z1.5',('regime',50,1.5))]:
            j,_,_=policy(H[:i],*cfg);decisions[label]=cached[t,MODELS[j]][0]
        for name,family in zip(PRIMARY,['mean','2plus','regime']):
            k,inner_score=outer_decision(inner[i-200:i],family);j,score,trigger=policy(H[:i],*CONFIGS[k])
            assert j==choices[i,k]
            p=cached[t,MODELS[j]][0];hit=len(set(p)&actual);dynamic_hits[name].append(hit);selection_counts[name][MODELS[j]]+=1
            decisions[name]=p
            decision_rows.append({'target_round':t,'model':name,'training_through_round':t-1,'hyperparameter_validation_start':t-200,'hyperparameter_validation_end':t-1,
                'inner_n':200,'chosen_policy':POLICY_IDS[k],'inner_objective':inner_score,'selected_component':MODELS[j],
                'pre_target_score':score,'regime_trigger':int(trigger),'maximum_outcome_used_in_selection':t-1,
                'predicted_numbers':' '.join(map(str,p)),'actual_numbers':' '.join(map(str,sorted(actual))),'hits':hit})
        for name,p in decisions.items():
            hit=len(set(p)&actual)
            if name in extra_hits:extra_hits[name].append(hit)
            prediction_rows.append({'target_round':t,'training_through_round':t-1,'model':name,'predicted_numbers':' '.join(map(str,p)),
                                    'actual_numbers':' '.join(map(str,sorted(actual))),'hits':hit})
    series.update({k:np.array(v) for k,v in extra_hits.items()});series.update({k:np.array(v) for k,v in dynamic_hits.items()})
    writecsv(out/'selection_trace.csv',decision_rows);writecsv(out/'new_strategy_predictions.csv',prediction_rows)
    # Meaningful leakage checks: change target and ALL later outcome rows; current choices/configs remain equal.
    mutation=[]
    for t in [601,801,1001,1201,1245]:
        i=t-201;mut=H.copy();mut[i:]=(mut[i:]+3)%7
        _,mut_inner,_,_=inner_grid(mut)
        for family in ['mean','2plus','regime']:
            k,_=outer_decision(inner[i-200:i],family);mk,_=outer_decision(mut_inner[i-200:i],family)
            assert k==mk and policy(H[:i],*CONFIGS[k])==policy(mut[:i],*CONFIGS[mk])
        mutation.append({'target':t,'altered_outcomes_from':t,'strategies_invariant':3})
    assert policy(np.zeros((200,8),dtype=int),'mean',50,0)[0]==0
    assert policy(np.zeros((200,8),dtype=int),'regime',50,1.5)[0]==7
    synthetic=np.zeros((200,8));synthetic[-50:,4]=3
    assert policy(synthetic,'regime',50,1.5)[0]==4
    assert outer_decision(np.ones((200,12)),'mean')[0]==0
    views={'overall_601_1245':np.arange(645),'recent200':np.arange(445,645),'recent100':np.arange(545,645),'recent50':np.arange(595,645),
           'historical_holdout_1201_1245':np.arange(600,645),'block_601_800':np.arange(200),'block_801_1000':np.arange(200,400),
           'block_1001_1200':np.arange(400,600)}
    metric_rows=[metrics(h[idx],model,view) for model,h in series.items() for view,idx in views.items()]
    probs=np.array([math.comb(6,k)*math.comb(39,6-k)/math.comb(45,6) for k in range(7)])
    baseline={'mean':.8,'variance':float(sum((np.arange(7)-.8)**2*probs)),'probabilities_0_6':probs.tolist(),
              **{f'rate_ge_{k}':float(probs[k:].sum()) for k in range(2,7)},'prior_MC':'existing 3.5M baseline retained; no rerun'}
    writejson(out/'exact_uniform_baseline.json',baseline)
    null_sum=np.array([1.])
    for _ in range(645):null_sum=np.convolve(null_sum,probs)
    tests=[]
    for name in PRIMARY:
        h=series[name]
        for k in [0,2,3,4]:
            observed=int(h.sum()) if k==0 else int(np.sum(h>=k));p=float(null_sum[observed:].sum()) if k==0 else binomial_upper(observed,645,float(probs[k:].sum()))
            tests.append({'model':name,'metric':'mean' if k==0 else f'{k}plus','n':645,'observed_sum_or_count':observed,'raw_upper_p':p,'holm_family_size':12})
    holm(tests,'raw_upper_p','holm_upper_p');writecsv(out/'uniform_null_tests.csv',tests)
    boot=block_indices(645,SEED);paired=[];mean_ci={}
    for name in PRIMARY:
        sample=series[name][boot].mean(axis=1);mean_ci[name]=[float(x) for x in np.quantile(sample,[.025,.975])]
        for control in ['combined_equal_rank','equal_weight_ticket_vote']:
            for k in [0,2,3,4]:
                diff=metric_vector(series[name],k)-metric_vector(series[control],k);samples=diff[boot].mean(axis=1)
                lo,hi=np.quantile(samples,[.025,.975]);centered=samples-diff.mean()
                p=(1+int(np.sum(np.abs(centered)>=abs(diff.mean()))))/(len(samples)+1)
                paired.append({'model':name,'control':control,'metric':'mean' if k==0 else f'{k}plus','n':645,'difference':float(diff.mean()),
                               'block_bootstrap_ci_low':float(lo),'block_bootstrap_ci_high':float(hi),'exploratory_two_sided_p':p,'holm_family_size':24})
    holm(paired,'exploratory_two_sided_p','holm_exploratory_p');writecsv(out/'paired_comparisons.csv',paired)
    for row in metric_rows:
        name=row['model'];idx=views[row['view']]
        indices=boot if len(idx)==645 else block_indices(len(idx),SEED+len(idx))
        samples=series[name][idx][indices].mean(axis=1);lo,hi=np.quantile(samples,[.025,.975])
        row['mean_block_bootstrap_low']=float(lo);row['mean_block_bootstrap_high']=float(hi)
        row['evidence']='POST_HOC_EXPLORATORY'
    writecsv(out/'model_metrics.csv',metric_rows)
    persistence=[]
    for j,m in enumerate(MODELS[:7]):
        mask=np.array([policy(H[:i],'regime',50,1.5)[2] and
                       ((H[i-50:i,j].mean()-H[i-100:i-50,j].mean())/math.sqrt(H[i-50:i,j].var()/50+H[i-100:i-50,j].var()/50+1e-9)>=1.5)
                       for i in range(400,len(H))])
        h=H[400:,j]
        persistence.append({'model':m,'window':50,'z_threshold':1.5,'trigger_n':int(mask.sum()),'nontrigger_n':int((~mask).sum()),
             'next_draw_mean_when_trigger':float(h[mask].mean()) if mask.any() else '',
             'next_draw_mean_when_nontrigger':float(h[~mask].mean()) if (~mask).any() else '',
             'trigger_delta_vs_uniform':float(h[mask].mean()-.8) if mask.any() else '',
             'small_trigger_sample':int(mask.sum()<30),'evidence':'POST_HOC_DIAGNOSTIC; correlated model rows not independent samples'})
    writecsv(out/'regime_persistence.csv',persistence)
    correlations=[]
    for a,c in itertools.combinations(MODELS,2):
        overlaps=[len(set(cached[t,a][0])&set(cached[t,c][0])) for t in range(601,1246)]
        correlations.append({'model_a':a,'model_b':c,'n':645,'mean_prediction_overlap':float(np.mean(overlaps)),
                'hit_correlation':float(np.corrcoef(series[a],series[c])[0,1]),'independence':'NOT ASSUMED; shared draw history'})
    writecsv(out/'model_correlation.csv',correlations)
    all_metrics={r['model']:r for r in metric_rows if r['view']=='overall_601_1245'}
    registries=[]
    for name in PRIMARY:
        m=all_metrics[name];sig=any(r['holm_upper_p']<.05 for r in tests if r['model']==name)
        status='VALIDATION_REQUIRED' if sig else ('WEAK' if m['mean_hits']<.8 else 'HOLD')
        registries.append({'study_id':SPEC['study_id'],'model_id':name,'hypothesis':SPEC[name[:4]],'status':status,
          'evidence':'POST_HOC_EXPLORATORY','cutoff':'all base/model/meta selection inputs <=t-1','outer_targets':'601..1245',
          'nested_inner':'200 pre-target inner walkforward outcomes; inner decisions use earlier windows only',
          'mean_hits':m['mean_hits'],'rate_ge_2':m['rate_ge_2'],'rate_ge_3':m['rate_ge_3'],'rate_ge_4':m['rate_ge_4'],
          'prospective':'NOT AVAILABLE; current study was frozen after historical outcomes were public',
          'promotion':'NONE','next_test':'future 1246+ frozen evaluation or separate preregistered decorrelation/tail objective'})
    writecsv(out/'hypothesis_registry.csv',registries)
    writecsv(out/'failure_registry.csv',[{**r,'failure_reason':'not independently confirmed; see block/recent metrics and multiplicity-adjusted tests'} for r in registries])
    preserved=all(digest(root/p)==h for p,h in before.items());assert preserved
    audit={'base_HEAD':EXPECTED_HEAD,'root_rows':1244,'snapshot_rows':1245,'snapshot_prefix_equals_raw':True,
      'cached_unique_targets':1044,'cached_unique_predictions':8352,'overlapping_records_removed':duplicate_count,
      'base_extension_targets':1,'source_unmodified':digest(source)==seals[source.relative_to(root).as_posix()],
      'sampled_prefix_checks':sample_checks,'future_outcome_mutation_checks':mutation,
      'toy_tie_regime_fallback_and_nested_contract':'PASS','blocking_leakage_violations':0,
      'tracked_files_preserved_count':len(before),'tracked_files_preserved':preserved,
      'new_outer_targets':645,'primary_dynamic_predictions':1935,'all_new_strategy_predictions':len(prediction_rows),
      'inner_policy_predictions':len(inner_rows),'future_recommendation_generated':False,
      'runtime_seconds':round(time.time()-started,3),'python':sys.version,'numpy':np.__version__}
    writejson(out/'VALIDATION_AUDIT.json',audit)
    writejson(out/'RUN_METADATA.json',{'date':'2026-10-12','started_utc':freeze['created_utc'],'finished_utc':datetime.now(timezone.utc).isoformat(),
                   'repository':str(root),'snapshot_sha256':digest(snapshot),'code_sha256':digest(__file__),'audit':audit,'selection_counts':selection_counts,'mean_ci':mean_ci})
    summary=['# Regime detection / dynamic model selection — 2026-10-12 v1','',
       '## NEW STUDY','',
       '질문: 목표 회차 이전에 관찰한 모델 성과의 상승 국면이 다음 회차에도 유지되는가? 창/임계값을 선택하는 과정까지 nested walk-forward하면 고정 B 및 동일가중 대조군보다 나은가?','',
       '기준 HEAD: `'+EXPECTED_HEAD+'`. 1~1245 검증 스냅샷 사용. 원본 1~1244와 prefix 동일. 기존 8,352개 B 예측은 재사용하고 누락된 1245 한 회차만 원본 B 함수를 호출했다.',
       '3 신규 전략, 645개 outer 목표(601~1245), 1,935개 주평가 예측. 12개 내부 정책 ×845회=10,140개 inner 예측. 5개 고정/랜덤 대조군을 포함한 신규 티켓 평가 5,160개. 기존 B 8개 ×645회 대조는 재사용한 역사적 예측의 같은 구간 평가다.','',
       'D001은 평균 적중, D002는 2+ 목표, D003은 두 인접 창의 성과 변화 z 국면을 사용한다. 각 t의 내부 정책은 t-1 이전 성과만 보고 결정하며, 외부 정책은 t-200..t-1의 내부 정책 평가만 보고 설정을 선택한다. tie-break 고정.','',
       '**POST_HOC_EXPLORATORY**: 오늘 코드 평가 전에 규칙/hash를 봉인했지만 과거 결과 공개 후 설계했다. 최근/역사 holdout을 untouched라고 부르지 않는다. 최근 좋아 보이는 모델을 결과를 본 뒤 최종 선정하지 않는다. 모든 전략·블록·실패를 보고한다.','',
       '## NEW FINDING','',
       '| 전략/고정대조 | n | 평균 | 2+ | 3+ | 4+ | Δ평균 vs random |','|---|---:|---:|---:|---:|---:|---:|']
    for name,h in series.items():
        m=all_metrics[name];summary.append(f"|{name}|645|{m['mean_hits']:.6f}|{m['rate_ge_2']:.4%}|{m['rate_ge_3']:.4%}|{m['rate_ge_4']:.4%}|{m['delta_mean_vs_uniform']:+.6f}|")
    summary.append(f"|exact uniform baseline|645|0.800000|{baseline['rate_ge_2']:.4%}|{baseline['rate_ge_3']:.4%}|{baseline['rate_ge_4']:.4%}|0.000000|")
    summary+=['','### 주평가와 불확실성','']
    for r in registries:
        name=r['model_id'];ps=[x['holm_upper_p'] for x in tests if x['model']==name];ci=mean_ci[name]
        summary.append(f"- {name}: {r['status']}; 평균 block-bootstrap 95% CI [{ci[0]:.4f}, {ci[1]:.4f}]; 12검정 Holm 최소 p={min(ps):.6f}. 추천 적용 없음.")
    summary+=['','uniform 귀무가설은 독립 균등 6/45 추첨이다. 과거 정보로 선택한 6개 티켓의 조건부 hit 분포도 hypergeometric이다. 평균 합계의 정확 convolution과 2+/3+/4+ binomial 상위 꼬리를 계산했다. Holm12는 이번 3전략×4지표만 보정하며 전체 누적 탐색의 사후선택을 제거하지 않는다.',
       'paired_comparisons.csv는 두 ensemble 대조군과의 paired 차이를 circular block20 bootstrap 5,000회로 계산한다. 24개 exploratory 검정에 Holm 적용. 시계열 재표집 CI는 참고 추정이며 adaptive process의 정확 재시뮬레이션 검정은 아니다.','',
       '### 최근 및 역사 holdout','',
       '| 전략 | 기간 | n | 평균 | 2+ | 3+ | 4+ |','|---|---|---:|---:|---:|---:|---:|']
    for r in metric_rows:
        if r['model'] in PRIMARY and r['view'] in ['recent200','recent100','recent50','historical_holdout_1201_1245']:
            summary.append(f"|{r['model']}|{r['view']}|{r['n']}|{r['mean_hits']:.4f}|{r['rate_ge_2']:.2%}|{r['rate_ge_3']:.2%}|{r['rate_ge_4']:.2%}|")
    summary+=['','### 국면의 실제 지속성','',
       '| B component | positive-change 표본 | 다음 평균 | 미감지 평균 |','|---|---:|---:|---:|']
    for r in persistence:
        summary.append(f"|{r['model']}|{r['trigger_n']}|{r['next_draw_mean_when_trigger']}|{r['next_draw_mean_when_nontrigger']}|")
    summary+=['','감지 표본 30 미만은 SMALL_SAMPLE. 국면 감지는 각 모델별 z>=1.5/창50을 사전 고정한 진단이다. 서로 같은 추첨을 공유하는 모델 행을 독립 표본으로 풀링하지 않는다. 4+ 사건은 적어 이 지표만으로 국면 선택의 우위를 판정하지 않는다.',
       'model_correlation.csv에는 28쌍의 hit correlation/티켓 overlap이 있다. 동적 모델은 한 component만 선택해 유사 모델을 독립 표로 가산하지 않는다. seven-ticket 동일가중은 중복 신호를 그대로 둔 명시적 대조군이며 B combined_equal_rank와 정의가 다르다.','',
       '## MAINTENANCE/RECHECK','',
       '최신 main/필수 문서 전체 읽기, 누적 결과 anti-repetition gate, 원자료·스냅샷 검증, 중첩 B 레코드 제거, 5개 prefix 40티켓 캐시 대조, 1245 단일 target 확장만 수행했다. B 전체 재현, 기존 대규모 MC, H001/H002, 관계 검정, 기본 통계 재실행을 신규 성과로 세지 않았다.',
       f"추적된 기존 파일 {len(before)}개 hash 보존 PASS. 목표 이후 outcome을 변조해 5개 cutoff의 3개 전략 선택/설정 불변 PASS. leakage 위반 0. 예측 추천/최종 3줄 생성 없음. 1245 실제 결과는 이번 역사 평가 outcome으로만 사용; 1245 결정 입력은 <=1244이다.",'',
       '## NEXT TEST','',
       '1. 이번 실패/보류를 유지하고, future1246+에서 별도 prospective protocol로 고정한 선택기만 평가한다. 미래 성과를 본 후 창/threshold 재선택 금지.',
       '2. 성과 추세의 지속성이 불확실하면 계열 독립성과 ensemble de-correlation을 별도 가설로 검증한다. 원시 static 우승 모델을 사후 승격하지 않는다.',
       '3. 3+/4+ 목표는 이번 2+ 최적화와 분리해 신규 사전 규칙·다중검정 범위를 정한 후 평가한다. 기존 known-outcome 구간을 untouched로 다시 명명하지 않는다.','',
       '## 실행 및 보존','',
       '재현: `python run_study.py --repository <clean pinned 857bea9 checkout> --out <new empty output directory>`; 기존 output 존재 시 거부. 필요한 런타임은 Python+NumPy. FROZEN_SPEC, trace, inner outcomes, CSV, source/input SHA, 실행 audit 보존.',
       'Git DNS 차단은 permissioned fetch로 우회했고 최신 main 별도 checkout을 사용했다. SciPy가 없어 정확 null 계산은 NumPy/stdlib로 수행했다. 미확보 legacy A/C/contrarian 원본은 모델 선택에서 제외했으며 복원/추정하지 않았다. 이 연구 완료는 전체 MASTER 체크리스트나 예측 우위 확정을 뜻하지 않는다.','']
    writetext(out/'STUDY_REPORT.md','\n'.join(summary))
    files=sorted(p for p in out.iterdir() if p.is_file())
    writecsv(out/'SHA256_MANIFEST.csv',[{'file':p.name,'bytes':p.stat().st_size,'sha256':digest(p)} for p in files])
    print(json.dumps({'audit':audit,'primary_metrics':[all_metrics[x] for x in PRIMARY],'registry':registries},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
