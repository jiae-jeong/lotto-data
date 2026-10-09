"""Independent descriptive signals and structural probability diagnostics; no ticket generator.
Read only the SHA-pinned rounds 1..1244. Do not execute B/S/V3/V4 model code.
"""
from pathlib import Path
import argparse, csv, json, hashlib, datetime, math, statistics, time, ast
from collections import Counter, defaultdict
from itertools import combinations, product
import numpy as np

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def write(out,name,data,fields=None):
    data=list(data);fields=fields or list(data[0])
    with (out/name).open('x',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(data)
def js(out,name,value):
    with (out/name).open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def wilson(k,n):
    if not n:return (None,None)
    z=1.959963984540054;p=k/n;den=1+z*z/n;c=(p+z*z/(2*n))/den;h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return max(0,c-h),min(1,c+h)
def rank(x):return {i+1:j+1 for j,i in enumerate(sorted(range(45),key=lambda i:(-x[i],i)))}
def mean(x):return statistics.mean(x) if x else None
def direction(x):return 'UP' if x>1e-12 else 'DOWN' if x< -1e-12 else 'FLAT'
def profile(ns,previous=None):
    ns=sorted(ns);g=[b-a for a,b in zip(ns,ns[1:])];bands=[sum(lo<=n<=hi for n in ns) for lo,hi in [(1,10),(11,20),(21,30),(31,40),(41,45)]]
    e=Counter(n%10 for n in ns);cg=1;best=1
    for gap in g:cg=cg+1 if gap<=2 else 1;best=max(best,cg)
    return dict(odd_count=sum(n%2 for n in ns),low_count=sum(n<=22 for n in ns),**{f'band_{i+1}_count':v for i,v in enumerate(bands)},sum=sum(ns),span=ns[-1]-ns[0],min_gap=min(g),max_gap=max(g),mean_gap=mean(g),consecutive_pairs=sum(x==1 for x in g),consecutive_runs=sum(g[i]==1 and (i==0 or g[i-1]!=1) for i in range(5)),repeat_end_extra=sum(v-1 for v in e.values()),repeat_end_groups=sum(v>=2 for v in e.values()),max_end_multiplicity=max(e.values()),clusters_gap_le2=1+sum(x>2 for x in g),max_cluster_gap_le2_size=best,narrow_three_span_le4=int(any(ns[i+2]-ns[i]<=4 for i in range(4))),previous_overlap=None if previous is None else len(set(ns)&set(previous)),band_max=max(bands),gap_1=g[0],gap_2=g[1],gap_3=g[2],gap_4=g[3],gap_5=g[4])
def predicates(p):
    return dict(consecutive_ge1=p['consecutive_pairs']>=1,consecutive_ge2=p['consecutive_pairs']>=2,band_ge3=p['band_max']>=3,band_ge4=p['band_max']>=4,odd_imbalance=p['odd_count']<=1 or p['odd_count']>=5,low_high_imbalance=p['low_count']<=1 or p['low_count']>=5,repeated_end=p['repeat_end_extra']>=1,end_multiplicity_ge3=p['max_end_multiplicity']>=3,multiple_repeat_end_groups=p['repeat_end_groups']>=2,extreme_sum=p['sum']<=90 or p['sum']>=186,narrow_three_span_le4=bool(p['narrow_three_span_le4']),large_gap_ge15=p['max_gap']>=15,previous_overlap_ge2=None if p['previous_overlap'] is None else p['previous_overlap']>=2)
def exact_structure_baseline():
    """Count combinatorial states, never construct or rank candidate six-number tickets."""
    den=math.comb(45,6);out={}
    out['consecutive_ge1']=1-math.comb(40,6)/den
    out['consecutive_ge2']=sum(math.comb(5,r-1)*math.comb(40,r) for r in range(1,5))/den
    for m in [3,4]:
        count=0
        for ns in product(range(7),repeat=5):
            if sum(ns)!=6 or ns[-1]>5:continue
            if max(ns)>=m:count+=math.prod(math.comb(size,n) for size,n in zip([10,10,10,10,5],ns))
        out[f'band_ge{m}']=count/den
    out['odd_imbalance']=sum(math.comb(23,k)*math.comb(22,6-k) for k in [0,1,5,6])/den
    out['low_high_imbalance']=sum(math.comb(22,k)*math.comb(23,6-k) for k in [0,1,5,6])/den
    # DP over ending-digit groups: selection count, repeated groups, maximum multiplicity.
    dp={(0,0,0):1}
    for size in [4,5,5,5,5,5,4,4,4,4]:
        nd=defaultdict(int)
        for (used,rep,mx),c in dp.items():
            for k in range(min(size,6-used)+1):nd[used+k,rep+(k>=2),max(mx,k)]+=c*math.comb(size,k)
        dp=nd
    out['repeated_end']=sum(c for (k,r,m),c in dp.items() if k==6 and r>=1)/den
    out['end_multiplicity_ge3']=sum(c for (k,r,m),c in dp.items() if k==6 and m>=3)/den
    out['multiple_repeat_end_groups']=sum(c for (k,r,m),c in dp.items() if k==6 and r>=2)/den
    dp={(0,0):1}
    for n in range(1,46):
        nd=dict(dp)
        for (k,s),c in dp.items():
            if k<6:nd[k+1,s+n]=nd.get((k+1,s+n),0)+c
        dp=nd
    out['extreme_sum']=sum(c for (k,s),c in dp.items() if k==6 and (s<=90 or s>=186))/den
    # Count six-number subsets avoiding any three selected numbers within width four.
    dp={(a,b):1 for a in range(1,45) for b in range(a+1,46)}
    for k in range(3,7):
        nd=defaultdict(int)
        for (a,b),c in dp.items():
            for n in range(b+1,46):
                if n-a>=5:nd[b,n]+=c
        dp=nd
    out['narrow_three_span_le4']=1-sum(dp.values())/den
    out['large_gap_ge15']=sum((-1)**(j+1)*math.comb(5,j)*math.comb(45-14*j,6) for j in range(1,3))/den
    out['previous_overlap_ge2']=sum(math.comb(6,k)*math.comb(39,6-k) for k in range(2,7))/den
    return out
def main():
    pa=argparse.ArgumentParser();pa.add_argument('--repo',type=Path,required=True);pa.add_argument('--out',type=Path,required=True);a=pa.parse_args();out=a.out;repo=a.repo
    cfg=json.loads((out/'RESEARCH_CONFIG.json').read_text());seal=json.loads((out/'EXECUTION_PLAN_SEAL.json').read_text())
    for name,h in seal['files'].items():assert sha(out/name)==h, 'Pre-execution plan changed: '+name
    t0=time.perf_counter();started=datetime.datetime.now(datetime.timezone.utc).isoformat()
    raw=repo/'lotto_data.csv';assert sha(raw)==cfg['raw_sha256'];r=rows(raw)
    rounds=[int(x['round']) for x in r];assert rounds==list(range(1,1245))
    draws=[[int(x[f'no{i}']) for i in range(1,7)] for x in r];bonus=[int(x['bonus']) for x in r]
    assert all(len(set(ns))==6 and all(1<=n<=45 for n in ns) and 1<=b<=45 and b not in ns for ns,b in zip(draws,bonus))
    js(out,'DATA_INTEGRITY.json',dict(status='VERIFIED',path=str(raw),sha256=sha(raw),rows=len(r),min_round=1,max_round=1244,missing=[],duplicate_rounds=0,number_errors=0,bonus_errors=0,actual_1245='NOT READ / NOT USED'))
    # Read and hash all earlier framework artifacts before any new numerical research.
    ledger=[]
    for p in sorted((repo/'research/expansion_framework_v1').rglob('*')):
        if not p.is_file() or '__pycache__' in p.parts:continue
        rawbytes=p.read_bytes();n=''
        if p.suffix=='.csv':n=len(rows(p))
        ledger.append(dict(path=p.relative_to(repo).as_posix(),sha256=sha(p),bytes=len(rawbytes),rows=n,review_status='READ ONLY; stored historical evidence; NOT RERUN'))
    write(out,'PRIOR_RESEARCH_READ_LEDGER.csv',ledger)
    # B manifests are verified, not rerun. All stored results remain byte-for-byte unchanged.
    checks=[]
    for folder,manifest in [('B_MODEL_REPRODUCTION_20261009_v1','AUDIT_SHA256.csv'),('B_RANDOM_BASELINE_20261009_v1','SHA256_MANIFEST.csv')]:
        base=repo/'outputs'/folder
        for item in rows(base/manifest):
            p=base/item['file'];assert p.stat().st_size==int(item['bytes']) and sha(p)==item['sha256']
            checks.append(dict(path=p.relative_to(repo).as_posix(),sha256=sha(p),status='PASS'))
    write(out,'FROZEN_B_REFERENCE_HASH_VERIFICATION.csv',checks)
    frozen=json.loads((repo/'outputs/B_RANDOM_BASELINE_20261009_v1/B_REPRODUCTION_REFERENCE_FROZEN.json').read_text())
    js(out,'B_FROZEN_REFERENCE.json',frozen|dict(current_task_B_execution='NOT EXECUTED; reference only',current_task_retuning=False))
    print(f'INPUT PASS rows=1244 cutoff=1244; frozen B/MC artifact checks={len(checks)}; B NOT RERUN',flush=True)
    slices=[('overall',0,1244)]+[(f'recent{w}',1244-w,1244) for w in cfg['recent_windows']]
    blocks=[(lo,min(lo+49,1244)) for lo in range(1,1245,50)]
    X=np.zeros((1244,45),dtype=np.int64)
    for i,ns in enumerate(draws):X[i,np.array(ns)-1]=1
    occ=[list(map(int,np.flatnonzero(X[:,n])+1)) for n in range(45)];blockrates=np.array([X[lo-1:hi].mean(axis=0) for lo,hi in blocks]);fullblocks=blockrates[:24]
    freqs=[];stability=[]
    full=X.sum(axis=0)
    for name,lo,hi in slices:
        count=X[lo:hi].sum(axis=0);n=hi-lo;ranking=rank(count)
        prior=X[:lo].sum(axis=0)/lo if lo else None
        for j in range(45):
            events=[q for q in occ[j] if lo<q<=hi];gaps=[b-a for a,b in zip(occ[j],occ[j][1:]) if lo<b<=hi];inside=[b-a for a,b in zip(events,events[1:])]
            rate=float(count[j])/n;delta=rate-float(full[j])/1244;dp=None if prior is None else rate-float(prior[j]);tail=1244-occ[j][-1]
            ci=wilson(int(count[j]),n)
            freqs.append(dict(window=name,start_round=lo+1,end_round=hi,number=j+1,n_draws=n,count=int(count[j]),rate=rate,frequency_rank=ranking[j+1],rate_ci95_low=ci[0],rate_ci95_high=ci[1],delta_vs_overall=delta,delta_vs_disjoint_prior=dp,direction_vs_disjoint_prior='NA' if dp is None else direction(dp),current_global_wait=tail,current_wait_window_right_censored=tail>=n,mean_completed_gap_ending_in_window=mean(gaps),mean_completed_gap_wholly_inside_window=mean(inside),latest_completed_gap_ending_in_window=gaps[-1] if gaps else None,completed_intervals_ending_in_window=len(gaps),max_completed_nonappearance_gap_ending_in_window=max(gaps)-1 if gaps else None,theoretical_rate=6/45,theoretical_mean_interarrival=45/6))
    write(out,'NUMBER_SIGNAL_WINDOWS.csv',freqs)
    for j in range(45):
        deltas=[x['delta_vs_disjoint_prior'] for x in freqs if x['number']==j+1 and x['window']!='overall'];sg=[direction(x) for x in deltas]
        slope=statistics.linear_regression(range(24),list(fullblocks[:,j])).slope
        stability.append(dict(number=j+1,full_50round_blocks=24,partial_last_block=44,full_block_rate_sd=statistics.pstdev(fullblocks[:,j]),block_min=float(min(fullblocks[:,j])),block_max=float(max(fullblocks[:,j])),block_linear_slope=slope,recent_direction_agreement=max(Counter(sg).values())/4,recent_directions=';'.join(sg),nested_recent_windows_independent=False))
    write(out,'NUMBER_TEMPORAL_STABILITY.csv',stability)
    write(out,'NUMBER_TIME_BLOCKS.csv',[dict(start_round=lo,end_round=hi,n_draws=hi-lo+1,number=j+1,count=int(X[lo-1:hi,j].sum()),rate=float(blockrates[k,j]),partial_block=hi-lo+1!=50) for k,(lo,hi) in enumerate(blocks) for j in range(45)])
    # Every pair and triple, including zeros, so the report cannot hide sparse relations.
    relrows=[];relstable=[]
    for order in [2,3]:
        universe=list(combinations(range(1,46),order));index={k:i for i,k in enumerate(universe)};events=np.zeros((1244,len(universe)),dtype=np.int8)
        for i,ns in enumerate(draws):
            for k in combinations(sorted(ns),order):events[i,index[k]]=1
        totals=events.sum(axis=0);br=np.array([events[lo-1:hi].mean(axis=0) for lo,hi in blocks]);prob=math.comb(6,order)/math.comb(45,order)
        for name,lo,hi in slices:
            co=events[lo:hi].sum(axis=0);prior=events[:lo].sum(axis=0)/lo if lo else None;n=hi-lo
            for j,k in enumerate(universe):
                rate=float(co[j])/n;delta=None if prior is None else rate-float(prior[j]);z=(int(co[j])-n*prob)/math.sqrt(n*prob*(1-prob))
                relrows.append(dict(order=order,numbers='-'.join(map(str,k)),window=name,start_round=lo+1,end_round=hi,n_draws=n,count=int(co[j]),rate=rate,overall_count=int(totals[j]),delta_vs_overall=rate-float(totals[j])/1244,delta_vs_disjoint_prior=delta,direction_vs_disjoint_prior='NA' if delta is None else direction(delta),exact_uniform_probability=prob,descriptive_null_z=z,multiple_testing='15180 relations x nested windows; no predictive/significance claim'))
        means=br[:24].mean(axis=0);stds=br[:24].std(axis=0)
        for j,k in enumerate(universe):relstable.append(dict(order=order,numbers='-'.join(map(str,k)),total_count=int(totals[j]),full_50round_block_rate_mean=float(means[j]),full_50round_block_rate_sd=float(stds[j]),full_blocks_observed=int((br[:24,j]>0).sum()),full_blocks_above_exact=int((br[:24,j]>prob).sum()),partial_last_block_rate=float(br[-1,j]),evidence='DESCRIPTIVE ONLY; sparse, dependent and multiple-tested'))
        print(f'RELATIONS computed order={order} combinations={len(universe)} observations={int(totals.sum())}',flush=True)
    write(out,'PAIR_TRIPLE_WINDOW_SIGNALS.csv',relrows);write(out,'PAIR_TRIPLE_TEMPORAL_STABILITY.csv',relstable)
    profiles=[profile(ns,draws[i-1] if i else None) for i,ns in enumerate(draws)];features=list(profiles[0]);binary=[predicates(p) for p in profiles];names=list(binary[0]);exact=exact_structure_baseline()
    js(out,'EXACT_STRUCTURE_BASELINE.json',dict(method='Exact combinatorial state counts / C(45,6); no random tickets or candidates generated',probabilities=exact))
    write(out,'DRAW_STRUCTURE_FEATURES.csv',[dict(round=i+1,**p,**{k:'' if v is None else int(v) for k,v in binary[i].items()}) for i,p in enumerate(profiles)])
    summaries=[];distribution=[]
    for name,lo,hi in slices:
        for f in features:
            v=[p[f] for p in profiles[lo:hi] if p[f] is not None];ov=[p[f] for p in profiles if p[f] is not None];pr=[p[f] for p in profiles[:lo] if p[f] is not None]
            summaries.append(dict(window=name,feature=f,n=len(v),mean=mean(v),variance=statistics.pvariance(v),min=min(v),max=max(v),delta_mean_vs_overall=mean(v)-mean(ov),delta_mean_vs_disjoint_prior=None if not pr else mean(v)-mean(pr),direction='NA' if not pr else direction(mean(v)-mean(pr))))
            for value,count in sorted(Counter(v).items()):distribution.append(dict(window=name,feature=f,value=value,count=count,n=len(v),rate=count/len(v)))
    write(out,'STRUCTURE_WINDOW_SUMMARY.csv',summaries);write(out,'STRUCTURE_DISTRIBUTIONS.csv',distribution)
    incidence=[];timeblocks=[];stab=[]
    for name,lo,hi in slices:
        for f in names:
            vals=[p[f] for p in binary[lo:hi] if p[f] is not None];prior=[p[f] for p in binary[:lo] if p[f] is not None];n=len(vals);k=sum(vals);ci=wilson(k,n);rate=k/n
            incidence.append(dict(window=name,structure=f,n=n,count=k,rate=rate,ci95_low=ci[0],ci95_high=ci[1],exact_uniform_rate=exact[f],delta_vs_exact=rate-exact[f],delta_vs_disjoint_prior=None if not prior else rate-sum(prior)/len(prior),direction='NA' if not prior else direction(rate-sum(prior)/len(prior))))
    for lo,hi in blocks:
        for f in names:
            vals=[p[f] for p in binary[lo-1:hi] if p[f] is not None];n=len(vals);k=sum(vals)
            timeblocks.append(dict(start_round=lo,end_round=hi,structure=f,n=n,count=k,rate=k/n,exact_uniform_rate=exact[f],partial=hi-lo+1!=50))
    for f in names:
        v=[x['rate'] for x in timeblocks if x['structure']==f and not x['partial']];stab.append(dict(structure=f,blocks=24,min_rate=min(v),max_rate=max(v),rate_sd=statistics.pstdev(v),blocks_above_exact=sum(x>exact[f] for x in v),slope=statistics.linear_regression(range(24),v).slope,evidence='Observed structural prevalence only; no edge inferred'))
    write(out,'CONTRARIAN_STRUCTURE_INCIDENCE.csv',incidence);write(out,'STRUCTURE_TIME_BLOCKS.csv',timeblocks);write(out,'STRUCTURE_TEMPORAL_STABILITY.csv',stab)
    # New post-hoc, preregistered-before-computation diagnostic: train historical event probabilities.
    # It assesses coverage lost by a hypothetical veto, not simulated purchases or replacement tickets.
    forecasts=[];coverage=[];fsummary=[]
    for target in range(cfg['historical_targets'][0],cfg['historical_targets'][1]+1):
        i=target-1
        for f in names:
            y=int(binary[i][f]);p0=exact[f]
            for mode in ['expanding','rolling300']:
                lo=0 if mode=='expanding' else max(0,i-300);hist=[p[f] for p in binary[lo:i] if p[f] is not None];n=len(hist)
                p=(sum(hist)+cfg['prior_strength']*p0)/(n+cfg['prior_strength'])
                forecasts.append(dict(target_round=target,training_start_round=lo+1,training_through_round=target-1,mode=mode,structure=f,training_n=n,training_count=sum(hist),predicted_probability=p,exact_probability=p0,actual_historical_structure=y,brier=(p-y)**2,baseline_brier=(p0-y)**2,logloss=-math.log(p if y else 1-p),baseline_logloss=-math.log(p0 if y else 1-p0)))
    for f in names:
        y=[int(binary[t-1][f]) for t in range(*[cfg['historical_targets'][0],cfg['historical_targets'][1]+1])];k=sum(y);ci=wilson(k,len(y))
        coverage.append(dict(structure=f,start_target=1045,end_target=1244,n_targets=200,allow_all_winning_structure_coverage=1.0,veto_winning_structure_coverage=1-k/200,coverage_loss=k/200,coverage_loss_ci95_low=ci[0],coverage_loss_ci95_high=ci[1],exact_uniform_coverage_loss=exact[f],ticket_performance='NOT EXECUTED; no allocation/replacement policy defined'))
    for mode in ['expanding','rolling300']:
        for f in names:
            rr=[x for x in forecasts if x['mode']==mode and x['structure']==f];diff=[x['brier']-x['baseline_brier'] for x in rr];se=statistics.stdev(diff)/math.sqrt(200)
            fsummary.append(dict(mode=mode,structure=f,n=200,brier=mean([x['brier'] for x in rr]),exact_baseline_brier=mean([x['baseline_brier'] for x in rr]),paired_brier_delta=mean(diff),paired_delta_ci95_low=mean(diff)-1.96*se,paired_delta_ci95_high=mean(diff)+1.96*se,ci_method='Exploratory paired normal CI; temporal dependence not adjusted; not an adoption test',logloss=mean([x['logloss'] for x in rr]),exact_logloss=mean([x['baseline_logloss'] for x in rr]),status='INSUFFICIENT EVIDENCE; post-hoc 26 comparisons'))
    write(out,'STRUCTURE_WALKFORWARD_PROBABILITIES.csv',forecasts);write(out,'STRUCTURE_WALKFORWARD_SUMMARY.csv',fsummary);write(out,'STRUCTURE_VETO_COVERAGE_DIAGNOSTIC.csv',coverage)
    print(f'STRUCTURES computed predicates={len(names)} forecast_records={len(forecasts)} targets=1045..1244; NO TICKETS GENERATED',flush=True)
    score=[]
    for x in rows(repo/'outputs/B_RANDOM_BASELINE_20261009_v1/B_VS_RANDOM_POOLED.csv'):
        score.append(dict(item='B_v1:'+x['model'],source='HASH VERIFIED frozen B-v1; not rerun this task',status=frozen['classification'][x['model']],evidence='REPRODUCED (prior audit); edge INSUFFICIENT EVIDENCE',n=int(x['historical_targets']),mean_hits=float(x['mean_hits']),variance=float(x['variance_hits_population']),distribution_0_6=json.dumps([int(x[f'hits_{i}_count']) for i in range(7)]),rate_2plus=float(x['rate_ge_2']),rate_3plus=float(x['rate_ge_3']),rate_4plus=float(x['rate_ge_4']),rate_5plus=float(x['rate_ge_5']),rate_6=float(x['rate_ge_6']),delta_exact=float(x['mean_delta_theoretical']),delta_mc=float(x['mean_delta_mc']),stability=x['block_mean_sd'],overfit_risk='Multiple models; historical screening; no verified edge'))
    for label in ['A_MODEL_ORIGINAL','C_MODEL_ORIGINAL','CONTRARIAN_MODEL_ORIGINAL']:
        score.append(dict(item=label,source='NOT FOUND in documented accessible scope',status='NOT FOUND',evidence='NOT EXECUTED: original formula unavailable',n='',mean_hits='',variance='',distribution_0_6='',rate_2plus='',rate_3plus='',rate_4plus='',rate_5plus='',rate_6='',delta_exact='',delta_mc='',stability='',overfit_risk='Cannot evaluate missing model; related S/V4 IDs not substituted'))
    for label in ['frequency','current_gap','mean_gap','recent_gap','structure','pair','triple']:
        score.append(dict(item='independent_signal:'+label,source='pinned rounds 1..1244; current executed script',status='VERIFIED',evidence='DESCRIPTIVE; not a six-number prediction model',n=1244,mean_hits='',variance='',distribution_0_6='',rate_2plus='',rate_3plus='',rate_4plus='',rate_5plus='',rate_6='',delta_exact='',delta_mc='',stability='See signal/block stability CSVs',overfit_risk='Nested windows, multiple signals, sparse relations; predictive evidence INSUFFICIENT EVIDENCE'))
    write(out,'MODEL_SIGNAL_SCORECARD.csv',score)
    write(out,'HISTORICAL_RECOMMENDATION_SOURCE_COVERAGE.csv',[dict(target_round=t,source_status='SOURCE NOT FOUND',recommendations_existed='UNKNOWN',cutoff='',selection_reasons='NOT RECORDED',exclusion_reasons='NOT RECORDED',errorloop_status='NOT EXECUTED; no authentic contemporaneous source') for t in range(1,1245)])
    js(out,'ERRORLOOP_VERIFICATION_STATUS.json',dict(source_status='SOURCE NOT FOUND',eligible_authentic_historical_recommendations=0,closed_loop='NOT EXECUTED',missing_reason='No sourced contemporaneous recommendation / target / cutoff / version / publication evidence for targets <=1244. Backtest rows are excluded.',models=['A','B','C','contrarian'],mean_hits=None,hit_distribution=None,bonus=None,winner_rank_reconstruction='NOT EXECUTED: contemporaneous recommendation/cutoff not established',failure_reasons='NOT RECORDED; no causal attribution invented',pending_1245='Existing sealed predictions not evaluated; actual NOT READ / NOT USED'))
    # New relationships are research registrations, not changes to any A/C/B rule.
    hypotheses=[('H001','Long/recent direction conflicts','NUMBER_SIGNAL_WINDOWS.csv','frequency rank; disjoint-prefix delta','No fixed advantage direction; test calibration/attenuation','Nested-window disagreement, not independent evidence'),('H002','Gap is not a due-number guarantee','NUMBER_SIGNAL_WINDOWS.csv','current wait; completed interarrival; right censoring','Compare gap-only calibration against constant 6/45','Completed intervals and censoring differ'),('H003','Sparse pair/triple recent rates may overfit','PAIR_TRIPLE_TEMPORAL_STABILITY.csv','relation counts; block support; marginal frequencies','Shrink sparse relations rather than promote raw maxima','15180 dependent relations x 5 nested windows'),('H004','Structure veto can exclude legitimate winning structures','STRUCTURE_VETO_COVERAGE_DIAGNOSTIC.csv','13 fixed structure predicates','Removing predicates loses winning-structure coverage; ticket benefit unproven','Coverage and event-probability diagnosis only'),('H005','Related S008 structure contribution cancels algebraically','RELATED_SOURCE_CODE_FINDINGS.md','S008 identical per-column added vectors','No structure-specific ordering effect in existing code','Inspect-only finding; not legacy C identity'),('H006','Repeated miss reasons need authentic recommendations','ERRORLOOP_VERIFICATION_STATUS.json','included/excluded winners; historical cutoff/reason','Direction unknown; requires sourced decisions','SOURCE NOT FOUND; no fabricated error attribution')]
    write(out,'NEW_HYPOTHESIS_REGISTRY.csv',[dict(hypothesis_id=i,hypothesis=h,discovery_evidence=ev,variables=v,expected_direction=d,validation_method='Freeze new standalone test; paired expanding/rolling, exact/random matched exposure; no post-hoc tuning',walk_forward_result='Executed event-probability/coverage diagnosis only' if i=='H004' else 'NOT EXECUTED',random_baseline_result='Exact structural null computed' if i=='H004' else 'NOT EXECUTED; frozen B MC is not this hypothesis test',temporal_stability=st,status='INSUFFICIENT EVIDENCE' if i in ['H003','H004','H005'] else 'NEW',recommendation_use='PROHIBITED until separately validated') for i,h,ev,v,d,st in hypotheses])
    elapsed=time.perf_counter()-t0
    js(out,'RUN_METADATA.json',dict(started_utc=started,completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),duration_seconds=elapsed,input_sha256=sha(raw),cutoff=1244,rows=1244,recommendation_or_candidate_generation=False,actual_1245='NOT READ / NOT USED',B_rerun=False,numpy_version=np.__version__,pair_combinations=990,triple_combinations=14190,relation_window_rows=len(relrows),structure_probability_forecasts=len(forecasts),status='EXECUTED SUCCESSFULLY',claim_limit='Descriptive signals and post-hoc structural probability/coverage diagnosis; no original A/C reconstruction or predictive promotion'))
    print(f'RESEARCH EXECUTION SUCCESS seconds={elapsed:.3f}; signals and structural diagnostics VERIFIED; original-model/errorloop execution blocked by missing provenance',flush=True)
if __name__=='__main__':main()
