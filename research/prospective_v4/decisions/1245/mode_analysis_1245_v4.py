"""Pre-run fixed analysis/decision rules. Never accesses a target-1245 outcome."""
import hashlib,itertools,json,math
import numpy as np
METRICS=['portfolio_3plus','portfolio_4plus','portfolio_max_hits','mean_ticket_hits']
def uniform_tickets(rng,n):return np.sort(np.argpartition(rng.random((n,45)),5,axis=1)[:,:6],axis=1).astype(np.uint8)+1
def random_portfolios(target,count,seed):
    # Uniform ordered unique candidate-list prefixes; unseen suffixes cannot affect greedy choice.
    # The same frozen distinctness/overlap/fallback rule is applied, without any outcome input.
    derived=int.from_bytes(hashlib.sha256(f'{seed}|historical_target|{target}'.encode()).digest()[:8],'big')
    rng=np.random.Generator(np.random.PCG64(derived));out=np.empty((count,3,6),dtype=np.uint8)
    out[:,0]=uniform_tickets(rng,count);fallbacks=0;duplicates=0
    for slot in (1,2):
        history=np.zeros((count,37,6),dtype=np.uint8);ranks=np.zeros(count,dtype=int);active=np.arange(count)
        while len(active):
            q=uniform_tickets(rng,len(active))
            duplicated=((history[active]==q[:,None,:]).all(axis=2)).any(axis=1)
            duplicates+=int(duplicated.sum());good=~duplicated;ids=active[good];qs=q[good]
            history[ids,ranks[ids]]=qs;ranks[ids]+=1
            overlaps=(qs[:,None,:,None]==out[ids,:slot,None,:]).any(axis=3).sum(axis=2)
            acceptable=(overlaps<=2).all(axis=1)
            out[ids[acceptable],slot]=qs[acceptable]
            failed=ids[~acceptable];terminal=failed[ranks[failed]==37]
            for i in terminal:
                previous=[tuple(t) for t in out[i,:slot]]
                candidates=[tuple(t) for t in history[i] if tuple(t) not in previous]
                chosen=min(candidates,key=lambda t:(sum(len(set(t)&set(old)) for old in previous),max(len(set(t)&set(old)) for old in previous),next(j for j,q in enumerate(history[i]) if tuple(q)==t),t))
                out[i,slot]=chosen;fallbacks+=1
            active=np.concatenate((active[duplicated],failed[ranks[failed]<37]))
    return out,{'seed':derived,'fallbacks':fallbacks,'within_list_duplicate_resamples':duplicates,'tickets_sha256':hashlib.sha256(out.tobytes()).hexdigest()}
def vector(records):return np.array([[float(r['portfolio_3plus']),float(r['portfolio_4plus']),float(r['portfolio_max_hits']),float(r['mean_ticket_hits'])] for r in records])
def summary(records):
    hits=[int(r['hits_'+m]) for r in records for m in ('G','C','S')];n=len(records)
    dist=[hits.count(i) for i in range(7)]
    return {'targets':n,'tickets':len(hits),'total_hits':sum(hits),'mean_ticket_hits':sum(hits)/len(hits),'hit_distribution_0_to_6':dist,'ticket_2plus_rate':sum(h>=2 for h in hits)/len(hits),'ticket_3plus_rate':sum(h>=3 for h in hits)/len(hits),'ticket_4plus_rate':sum(h>=4 for h in hits)/len(hits),'portfolio_3plus_count':sum(int(r['portfolio_3plus']) for r in records),'portfolio_4plus_count':sum(int(r['portfolio_4plus']) for r in records),'portfolio_3plus_rate':sum(int(r['portfolio_3plus']) for r in records)/n,'portfolio_4plus_rate':sum(int(r['portfolio_4plus']) for r in records)/n,'portfolio_max_hits_sum':sum(int(r['portfolio_max_hits']) for r in records),'portfolio_max_hits_mean':sum(int(r['portfolio_max_hits']) for r in records)/n,'mean_union_coverage':float(np.mean([float(r['union_coverage']) for r in records])),'mean_pair_overlap':float(np.mean([float(r['mean_pair_overlap']) for r in records]))}
def random_summary(records):
    n=len(records);R=int(records[0]['replicates']);dist=[sum(int(r['hit_count_'+str(i)]) for r in records) for i in range(7)];tickets=n*R*3
    return {'targets':n,'replicates_per_target':R,'portfolio_simulations':n*R,'tickets':tickets,'mean_ticket_hits':sum(i*v for i,v in enumerate(dist))/tickets,'exact_mean_ticket_hits':0.8,'hit_distribution_0_to_6':dist,'ticket_2plus_rate':sum(dist[2:])/tickets,'ticket_3plus_rate':sum(dist[3:])/tickets,'ticket_4plus_rate':sum(dist[4:])/tickets,'portfolio_3plus_rate':float(np.mean([float(r['portfolio_3plus_rate']) for r in records])),'portfolio_4plus_rate':float(np.mean([float(r['portfolio_4plus_rate']) for r in records])),'portfolio_3plus_expected_targets':sum(float(r['portfolio_3plus_rate']) for r in records),'portfolio_4plus_expected_targets':sum(float(r['portfolio_4plus_rate']) for r in records),'portfolio_max_hits_mean':float(np.mean([float(r['portfolio_max_hits_mean']) for r in records])),'mean_union_coverage':float(np.mean([float(r['mean_union_coverage']) for r in records])),'mean_pair_overlap':float(np.mean([float(r['mean_pair_overlap']) for r in records])),'portfolio_3plus_monte_carlo_se':math.sqrt(sum(float(r['portfolio_3plus_rate'])*(1-float(r['portfolio_3plus_rate']))/R for r in records))/n,'portfolio_4plus_monte_carlo_se':math.sqrt(sum(float(r['portfolio_4plus_rate'])*(1-float(r['portfolio_4plus_rate']))/R for r in records))/n}
def holm(ps):
    order=sorted(range(len(ps)),key=lambda i:ps[i]);out=[0.]*len(ps);previous=0.
    for j,i in enumerate(order):previous=max(previous,min(1.,(len(ps)-j)*ps[i]));out[i]=previous
    return out
def mcnemar(a,b):
    left=int(((a==1)&(b==0)).sum());right=int(((a==0)&(b==1)).sum());n=left+right
    p=1. if n==0 else min(1.,2*sum(math.comb(n,k) for k in range(min(left,right)+1))/(2**n))
    return {'expanding_only':left,'rolling300_only':right,'discordant_targets':n,'two_sided_exact_p':p,'interpretation':'secondary paired binary diagnostic; temporal exchangeability not guaranteed'}
def paired_statistics(a,b,config):
    d=a-b;n=len(d);assert n==200;L=config['resampling_block_length'];B=config['bootstrap_replicates'];P=config['permutation_replicates']
    rng=np.random.Generator(np.random.PCG64(config['bootstrap_seed']))
    starts=rng.integers(0,n,size=(B,n//L));indices=(starts[:,:,None]+np.arange(L))%n
    boot=d[indices.reshape(B,n)].mean(axis=1);ci=np.quantile(boot,[.025,.975],axis=0).T
    rng=np.random.Generator(np.random.PCG64(config['permutation_seed']));blocks=d.reshape(n//L,L,4).sum(axis=1)
    signs=rng.choice(np.array([-1,1],dtype=np.int8),size=(P,n//L));flips=signs@blocks/n;observed=d.mean(axis=0)
    ps=[float((1+(np.abs(flips[:,i])>=abs(observed[i])-1e-14).sum())/(P+1)) for i in range(4)]
    adjusted=holm(ps);tests={}
    for i,name in enumerate(METRICS):
        sd=float(d[:,i].std(ddof=1));tests[name]={'expanding_minus_rolling300':float(observed[i]),'paired_block_bootstrap_95_ci':ci[i].tolist(),'paired_10_target_block_sign_flip_two_sided_p':ps[i],'holm_adjusted_p':adjusted[i],'paired_standardized_effect_dz':float(observed[i]/sd) if sd else None,'nonzero_target_differences':int((d[:,i]!=0).sum())}
    modeci={m:{name:np.quantile(v[indices.reshape(B,n)].mean(axis=1)[:,i],[.025,.975]).tolist() for i,name in enumerate(METRICS)} for m,v in [('expanding',a),('rolling300',b)]}
    return {'primary_family':METRICS,'alpha':config['alpha'],'block_length':L,'bootstrap_replicates':B,'bootstrap_seed':config['bootstrap_seed'],'permutation_replicates':P,'permutation_seed':config['permutation_seed'],'primary_tests':tests,'mode_block_bootstrap_95_ci':modeci,'secondary_mcnemar':{METRICS[i]:mcnemar(a[:,i],b[:,i]) for i in (0,1)},'limitations':'Retrospective reused data, 200 targets, rare 4+ events; block resampling only approximates dependence. No prospective predictive superiority is established.'}
def relationship_diagnostics(records):
    x=np.array([[float(r['mean_pair_overlap']),float(r['union_coverage'])] for r in records]);y=vector(records);out=[]
    for i,name in enumerate(['mean_pair_overlap','union_coverage']):
        for j,outcome in enumerate(METRICS):
            corr=float(np.corrcoef(x[:,i],y[:,j])[0,1]) if x[:,i].std()>0 and y[:,j].std()>0 else None
            out.append({'feature':name,'historical_outcome':outcome,'pearson_correlation':corr,'use':'diagnostic only; excluded from selection/tie-break'})
    return out
def decide(mode_records,random_records,stats,config):
    totals={m:summary(r) for m,r in mode_records.items()};randoms=random_summary(random_records)
    block_stats={m:[summary(r[i:i+50]) for i in range(0,200,50)] for m,r in mode_records.items()}
    rb=[random_summary(random_records[i:i+50]) for i in range(0,200,50)]
    support={};tests=stats['primary_tests']
    for mode,sign in [('expanding',1),('rolling300',-1)]:
        other='rolling300' if mode=='expanding' else 'expanding';t=totals[mode]
        conditions={}
        for metric in ['portfolio_3plus','portfolio_4plus','mean_ticket_hits']:
            test=tests[metric];ci=test['paired_block_bootstrap_95_ci']
            conditions[metric+'_positive_paired_delta']=sign*test['expanding_minus_rolling300']>0
            conditions[metric+'_holm_significant']=test['holm_adjusted_p']<config['alpha']
            conditions[metric+'_positive_ci']=(ci[0]>0 if sign==1 else ci[1]<0)
        conditions['nonnegative_max_hits_paired_delta']=sign*tests['portfolio_max_hits']['expanding_minus_rolling300']>=0
        conditions['overall_positive_random_delta']=t['portfolio_3plus_rate']>randoms['portfolio_3plus_rate'] and t['portfolio_4plus_rate']>randoms['portfolio_4plus_rate'] and t['mean_ticket_hits']>.8
        conditions['all_four_blocks_nonnegative_random_3plus_and_mean']=all(x['portfolio_3plus_rate']>=y['portfolio_3plus_rate'] and x['mean_ticket_hits']>=.8 for x,y in zip(block_stats[mode],rb))
        conditions['all_four_blocks_nonnegative_paired_3plus_and_mean']=all(x['portfolio_3plus_count']>=y['portfolio_3plus_count'] and x['mean_ticket_hits']>=y['mean_ticket_hits'] for x,y in zip(block_stats[mode],block_stats[other]))
        support[mode]={'conditions':conditions,'passed':all(conditions.values())}
    passing=[m for m,v in support.items() if v['passed']]
    if len(passing)==1:return passing[0],'HISTORICAL_COMPARISON_SUPPORTED_NOT_PROSPECTIVE_SUPERIORITY',{'support_gate':support,'tie_break_applied':False},totals,block_stats,randoms
    variance={m:(4*sum(x['portfolio_3plus_count']**2 for x in block_stats[m])-sum(x['portfolio_3plus_count'] for x in block_stats[m])**2)/40000 for m in totals}
    rules=[('portfolio_3plus_count',lambda m:totals[m]['portfolio_3plus_count']),('portfolio_max_hits_sum',lambda m:totals[m]['portfolio_max_hits_sum']),('mean_ticket_hits',lambda m:totals[m]['mean_ticket_hits']),('lower_four_block_portfolio_3plus_rate_variance',lambda m:-variance[m])]
    trace=[];chosen=None
    for name,get in rules:
        values={m:get(m) for m in totals};winner=max(values,key=values.get) if len(set(values.values()))>1 else None
        trace.append({'criterion':name,'values':values,'selected_if_unequal':winner})
        if winner:chosen=winner;break
    if chosen is None:chosen='expanding';trace.append({'criterion':'final_default_expanding','selected_if_unequal':'expanding'})
    return chosen,'DETERMINISTIC_TIE_BREAK_NO_VERIFIED_SUPERIORITY',{'support_gate':support,'tie_break_applied':True,'tie_break_trace':trace,'four_block_variance':variance},totals,block_stats,randoms
