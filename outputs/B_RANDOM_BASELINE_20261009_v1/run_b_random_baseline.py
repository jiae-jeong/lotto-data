"""Separate actual-ticket Monte Carlo; never imports or changes the B model."""
from pathlib import Path
from collections import Counter, defaultdict
from fractions import Fraction
import csv, datetime, hashlib, json, math, statistics, sys, time
import numpy as np

A=Path(__file__).resolve().parent
REFERENCE=A.parent/'B_MODEL_REPRODUCTION_20261009_v1'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):
    with p.open(encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))
def save(name,obj):
    with (A/name).open('x',encoding='utf-8',newline='\n') as f: json.dump(obj,f,ensure_ascii=False,indent=2); f.write('\n')
def csvsave(name,rows):
    with (A/name).open('x',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
def wilson(k,n,z=1.959963984540054):
    p=k/n; d=1+z*z/n; c=(p+z*z/(2*n))/d; h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return max(0,c-h),min(1,c+h)
def stats(counts):
    n=int(sum(counts)); mean=sum(k*int(c) for k,c in enumerate(counts))/n
    v=sum(int(c)*(k-mean)**2 for k,c in enumerate(counts))/n
    return n,mean,v
def uniform_tickets(rng,n):
    # Conditional on distinctness, iid uniform ordered sextuples are uniform;
    # sorting maps each unordered subset from exactly6! equally likely tuples.
    tickets=rng.integers(1,46,size=(n,6),dtype=np.int16)
    rejected=0
    while True:
        tickets.sort(axis=1)
        bad=np.any(tickets[:,1:]==tickets[:,:-1],axis=1)
        failures=int(bad.sum()); rejected+=failures
        if not failures: break
        tickets[bad]=rng.integers(1,46,size=(failures,6),dtype=np.int16)
    assert tickets.min()>=1 and tickets.max()<=45 and not np.any(tickets[:,1:]==tickets[:,:-1])
    return tickets,rejected
def simulate_target(seed,target,repetitions,actual):
    rng=np.random.Generator(np.random.PCG64(np.random.SeedSequence([seed,target])))
    tickets,rejected=uniform_tickets(rng,repetitions)
    hits=np.isin(tickets,np.asarray(actual,dtype=np.int16)).sum(axis=1)
    counts=np.bincount(hits,minlength=7).astype(np.int64)
    digest=hashlib.sha256(tickets.astype('<i2',copy=False).tobytes(order='C')).hexdigest()
    return counts,digest,rejected

def main():
    started=datetime.datetime.now(datetime.timezone.utc).isoformat(); clock=time.monotonic()
    cfg=json.loads((A/'RUN_CONFIG.json').read_text())
    seal=json.loads((A/'RUN_PLAN_SEAL.json').read_text())
    for name,expected in seal['file_sha256'].items(): assert sha(A/name)==expected,name
    for name,expected in cfg['reference_sha256'].items(): assert sha(REFERENCE/name)==expected,name
    draws=read(REFERENCE/'EXECUTED_INPUT_lotto_data.csv')
    assert [int(r['round']) for r in draws]==list(range(1,1245))
    actuals={int(r['round']):[int(r[f'no{i}']) for i in range(1,7)] for r in draws}
    all_predictions=read(REFERENCE/'b_model_predictions.csv')
    b_rows=[r for r in all_predictions if r['horizon']=='50' and int(r['anchor_after_round']) in cfg['anchors']]
    assert len(b_rows)==2800
    models=cfg['model_names']; targets=[t for start,end in cfg['blocks'] for t in range(start,end+1)]
    assert len(set(targets))==len(targets)==350 and max(targets)==1200 and 1245 not in targets
    by_key={(int(r['target_round']),r['model']):r for r in b_rows}
    assert len(by_key)==2800
    B=np.array([[int(by_key[(t,m)]['hits']) for m in models] for t in targets],dtype=np.int16)
    for t in targets:
        for m in models:
            r=by_key[(t,m)]; assert int(r['training_through_round'])==t-1
            assert int(r['hits'])==len(set(map(int,r['predicted_numbers'].split()))&set(actuals[t]))
    denominator=math.comb(45,6)
    exact=[Fraction(math.comb(6,k)*math.comb(39,6-k),denominator) for k in range(7)]
    p=np.array([float(x) for x in exact]); exact_mean=.8; exact_var=float(Fraction(169,275))
    save('THEORETICAL_BASELINE.json',dict(formula='C(6,k)C(39,6-k)/C(45,6)',mean=exact_mean,variance=exact_var,pmf=p.tolist(),tail={str(k)+'+':float(p[k:].sum()) for k in range(2,7)},role='analytic reference; Monte Carlo below actually generates six-number tickets, not hypergeometric hits'))
    print(f'START UTC={started} seed={cfg["random_seed"]} targets={len(targets)} tickets_per_target={cfg["tickets_per_target"]}',flush=True)
    per_target=[]; streams=[]; pooled=np.zeros(7,dtype=np.int64); blocks={i:np.zeros(7,dtype=np.int64) for i in range(7)}; rejected_total=0
    for t in targets:
        block=next(i for i,(start,end) in enumerate(cfg['blocks']) if start<=t<=end)
        counts,digest,rejected=simulate_target(cfg['random_seed'],t,cfg['tickets_per_target'],actuals[t])
        assert int(counts.sum())==cfg['tickets_per_target']
        pooled+=counts; blocks[block]+=counts; rejected_total+=rejected
        n,mean,var=stats(counts)
        row=dict(target_round=t,block_start=cfg['blocks'][block][0],block_end=cfg['blocks'][block][1],random_ticket_comparisons=n,mean_hits=mean,variance_hits_population=var)
        for k in range(7): row[f'hits_{k}_count']=int(counts[k]); row[f'hits_{k}_rate']=float(counts[k]/n)
        for k in range(2,7): row[f'rate_ge_{k}']=float(counts[k:].sum()/n)
        per_target.append(row); streams.append(dict(target_round=t,ticket_count=n,sorted_int16_le_stream_sha256=digest,rejected_iid_sextuples=rejected))
        if t==cfg['blocks'][block][1]: print(f'BLOCK {block+1}/7 {cfg["blocks"][block]} completed comparisons={(block+1)*50*cfg["tickets_per_target"]}',flush=True)
    csvsave('MC_TARGET_AGGREGATES.csv',per_target); csvsave('RANDOM_TICKET_STREAM_HASHES.csv',streams)
    random_summary=[]
    for name,start,end,counts in [(f'BLOCK_{i+1}',*cfg['blocks'][i],blocks[i]) for i in range(7)]+[('POOLED_7_DISJOINT_BLOCKS',201,1200,pooled)]:
        n,mean,var=stats(counts); se=math.sqrt(var/n)
        fourth=sum(int(c)*(k-mean)**4 for k,c in enumerate(counts))/n
        variance_se=math.sqrt(max(0,fourth-var*var)/n)
        row=dict(interval=name,start_round=start,end_round=end,historical_targets=350 if name.startswith('POOLED') else 50,random_ticket_comparisons=n,mean_hits=mean,mean_mc_se=se,mean_ci95_low=mean-1.959963984540054*se,mean_ci95_high=mean+1.959963984540054*se,variance_hits_population=var,variance_mc_se=variance_se,variance_ci95_low=max(0,var-1.959963984540054*variance_se),variance_ci95_high=var+1.959963984540054*variance_se,mean_minus_theoretical=mean-exact_mean,variance_minus_theoretical=var-exact_var)
        for k in range(7):
            low,high=wilson(int(counts[k]),n)
            row.update({f'hits_{k}_count':int(counts[k]),f'hits_{k}_rate':float(counts[k]/n),f'hits_{k}_ci95_low':low,f'hits_{k}_ci95_high':high,f'hits_{k}_minus_theoretical':float(counts[k]/n-p[k])})
        for k in range(2,7):
            count=int(counts[k:].sum()); low,high=wilson(count,n)
            row.update({f'rate_ge_{k}':count/n,f'rate_ge_{k}_mc_se':math.sqrt((count/n)*(1-count/n)/n),f'rate_ge_{k}_ci95_low':low,f'rate_ge_{k}_ci95_high':high,f'rate_ge_{k}_minus_theoretical':count/n-float(p[k:].sum())})
        random_summary.append(row)
    csvsave('MC_BLOCK_AND_POOLED_SUMMARY.csv',random_summary)
    pooled_summary=random_summary[-1]
    # Independent draw assumptions and post-hoc selection limitations are recorded.
    brng=np.random.Generator(np.random.PCG64(cfg['bootstrap_seed']))
    weights=brng.multinomial(7,[1/7]*7,size=cfg['bootstrap_repetitions'])/7
    model_rows=[]; compare_blocks=[]; ptests=[]
    exact_sum=np.array([1.0])
    for _ in range(350): exact_sum=np.convolve(exact_sum,p)
    assert abs(exact_sum.sum()-1)<1e-10
    exact_binom=np.array([math.exp(math.lgamma(351)-math.lgamma(k+1)-math.lgamma(351-k)+k*math.log(float(p[2:].sum()))+(350-k)*math.log1p(-float(p[2:].sum()))) for k in range(351)])
    z=statistics.NormalDist().inv_cdf(.975); df=349
    tcrit=z+(z**3+z)/(4*df)+(5*z**5+16*z**3+3*z)/(96*df**2)+(3*z**7+19*z**5+17*z**3-15*z)/(384*df**3)
    for j,model in enumerate(models):
        hits=B[:,j]; counts=np.bincount(hits,minlength=7); n,mean,var=stats(counts)
        sample_var=float(np.var(hits,ddof=1)); se=math.sqrt(sample_var/n); mean_low,mean_high=mean-tcrit*se,mean+tcrit*se
        k2=int((hits>=2).sum()); r2=k2/n; low2,high2=wilson(k2,n)
        block_means=np.array([float(hits[i*50:(i+1)*50].mean()) for i in range(7)])
        block_rates=np.array([float((hits[i*50:(i+1)*50]>=2).mean()) for i in range(7)])
        boot_mean=weights@block_means; boot_rate=weights@block_rates
        qmean=np.quantile(boot_mean,[.025,.975]); qrate=np.quantile(boot_rate,[.025,.975])
        record=dict(model=model,status='INSUFFICIENT EVIDENCE',historical_targets=350,b_ticket_count=350,mc_ticket_comparisons=int(pooled.sum()),mean_hits=mean,variance_hits_population=var,mean_se_assuming_independent_rounds=se,mean_ci95_low=mean_low,mean_ci95_high=mean_high,mean_delta_theoretical=mean-exact_mean,mean_delta_ci95_low=mean_low-exact_mean,mean_delta_ci95_high=mean_high-exact_mean,mean_delta_mc=mean-pooled_summary['mean_hits'],mean_delta_mc_ci95_low=mean-z*math.sqrt(se*se+pooled_summary['mean_mc_se']**2)-pooled_summary['mean_hits'],mean_delta_mc_ci95_high=mean+z*math.sqrt(se*se+pooled_summary['mean_mc_se']**2)-pooled_summary['mean_hits'],rate_ge_2=r2,rate_ge_2_ci95_low=low2,rate_ge_2_ci95_high=high2,rate_ge_2_delta_theoretical=r2-float(p[2:].sum()),rate_ge_2_delta_ci95_low=low2-float(p[2:].sum()),rate_ge_2_delta_ci95_high=high2-float(p[2:].sum()),rate_ge_2_delta_mc=r2-pooled_summary['rate_ge_2'],block_mean_sd=float(block_means.std(ddof=1)),block_mean_min=float(block_means.min()),block_mean_max=float(block_means.max()),blocks_mean_above_exact=int((block_means>exact_mean).sum()),blocks_mean_above_mc=int(sum(block_means[i]>random_summary[i]['mean_hits'] for i in range(7))),block_bootstrap_mean_ci95_low=float(qmean[0]),block_bootstrap_mean_ci95_high=float(qmean[1]),block_bootstrap_mean_delta_ci95_low=float(qmean[0])-exact_mean,block_bootstrap_mean_delta_ci95_high=float(qmean[1])-exact_mean,block_bootstrap_rate_ge_2_ci95_low=float(qrate[0]),block_bootstrap_rate_ge_2_ci95_high=float(qrate[1]))
        for k in range(7): record[f'hits_{k}_count']=int(counts[k]); record[f'hits_{k}_rate']=float(counts[k]/n)
        for k in range(3,7): record[f'rate_ge_{k}']=float(counts[k:].sum()/n)
        observed_sum=int(hits.sum()); distance=abs(observed_sum-280)
        pmean=float(exact_sum[np.abs(np.arange(len(exact_sum))-280)>=distance].sum())
        observed_pmf=float(exact_binom[k2]); prate=float(exact_binom[exact_binom<=observed_pmf*(1+1e-12)].sum())
        ptests.extend([dict(model=model,metric='mean_hits',p_raw=min(1,pmean),method='Exact350-fold hypergeometric convolution;two-sided absolute distance from sum expectation280'),dict(model=model,metric='rate_ge_2',p_raw=min(1,prate),method='Exact two-sided probability-ordered Binomial(350,p_exact_2plus)')])
        model_rows.append(record)
        for i,(start,end) in enumerate(cfg['blocks']):
            hs=hits[i*50:(i+1)*50]; hist=np.bincount(hs,minlength=7)
            row=dict(model=model,block_start=start,block_end=end,b_historical_targets=50,b_mean_hits=float(hs.mean()),random_ticket_comparisons=random_summary[i]['random_ticket_comparisons'],random_mean_hits=random_summary[i]['mean_hits'],mean_delta_mc=float(hs.mean())-random_summary[i]['mean_hits'],mean_delta_theoretical=float(hs.mean())-exact_mean,b_rate_ge_2=float((hs>=2).mean()),random_rate_ge_2=random_summary[i]['rate_ge_2'],rate_ge_2_delta_mc=float((hs>=2).mean())-random_summary[i]['rate_ge_2'])
            for k in range(7): row[f'b_hits_{k}_count']=int(hist[k]); row[f'random_hits_{k}_count']=int(blocks[i][k])
            for k in range(3,7): row[f'b_rate_ge_{k}']=float((hs>=k).mean()); row[f'random_rate_ge_{k}']=random_summary[i][f'rate_ge_{k}']
            compare_blocks.append(row)
    order=sorted(range(len(ptests)),key=lambda i:ptests[i]['p_raw']); running=0
    for rank,i in enumerate(order):
        running=max(running,min(1,(len(ptests)-rank)*ptests[i]['p_raw']))
        ptests[i]['p_holm_16']=running; ptests[i]['exploratory_only']=True
    for row in model_rows:
        for metric in ['mean_hits','rate_ge_2']:
            test=next(t for t in ptests if t['model']==row['model'] and t['metric']==metric)
            row[metric+'_p_raw']=test['p_raw']; row[metric+'_p_holm_16']=test['p_holm_16']
    csvsave('B_VS_RANDOM_POOLED.csv',model_rows); csvsave('B_VS_RANDOM_BLOCKS.csv',compare_blocks)
    observed=np.r_[pooled[:5],pooled[5:].sum()]; expected=int(pooled.sum())*np.r_[p[:5],p[5:].sum()]
    chi=float(((observed-expected)**2/expected).sum()); x=chi/2
    q=math.erfc(math.sqrt(x))
    for a in [.5,1.5]: q+=math.exp(a*math.log(x)-x-math.lgamma(a+1)) if x else 0
    save('EXPLORATORY_STATISTICAL_TESTS.json',dict(status='INSUFFICIENT EVIDENCE',tests=ptests,family='8 models x2 metrics=16 tests, Holm family-wise correction',pvalue_scope='Exploratory historical tests; iid fair-draw assumption. Post-hoc models/evaluation selection remain uncorrected, no prospective proof.',confidence_intervals='Mean95% Student-t(Cornish-Fisher df349), rate2+Wilson; separately seven-whole-block percentile bootstrap20000. Blocks are disjoint;recent overlapping windows not counted.',mc_distribution_diagnostic=dict(pooled_bins='0,1,2,3,4,5+',chi_square=chi,df=5,p_approx=q,mean_null_z=(pooled_summary['mean_hits']-.8)/math.sqrt(exact_var/int(pooled.sum())),interpretation='Diagnostic only, never change seed/sample size based on this result. Rare6-hit precision is limited.')))
    elapsed=time.monotonic()-clock
    save('RUN_METADATA.json',dict(status='MONTE_CARLO_VERIFIED',start_utc=started,end_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),elapsed_seconds=elapsed,random_seed=cfg['random_seed'],bootstrap_seed=cfg['bootstrap_seed'],bootstrap_repetitions=cfg['bootstrap_repetitions'],historical_target_count=350,mc_ticket_comparisons=int(pooled.sum()),accepted_uniform_ticket_count=int(pooled.sum()),rejected_iid_sextuples=rejected_total,draw_max_round=1244,evaluation_max_round=1200,actual_1245='NOT READ / NOT USED',new_recommendations=False,python=sys.version,numpy=np.__version__,rng='PCG64/SeedSequence([seed,target])',uniform_sampler='iid6 integers1..45;reject repeated-number sextuples;sort valid tickets. No random hit-count shortcut.',raw_ticket_storage='No candidate/recommendation numbers emitted. Each actual random stream is reproducible from configuration/code and committed stream SHA;aggregated counts stored.',source_sha256=sha(Path(__file__)),config_sha256=sha(A/'RUN_CONFIG.json'),plan_seal_sha256=sha(A/'RUN_PLAN_SEAL.json')))
    print(f'COMPLETE comparisons={int(pooled.sum())} mean={pooled_summary["mean_hits"]:.12f} variance={pooled_summary["variance_hits_population"]:.12f} elapsed={elapsed:.3f}s',flush=True)
    print('Existing B classifications preserved;predictive evidence INSUFFICIENT EVIDENCE;actual1245 NOT READ / NOT USED',flush=True)

if __name__=='__main__': main()
