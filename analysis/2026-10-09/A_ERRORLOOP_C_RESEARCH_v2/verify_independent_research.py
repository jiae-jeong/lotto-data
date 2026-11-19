from pathlib import Path
import argparse,csv,json,math,statistics,hashlib,datetime,sys,subprocess,ast
from collections import Counter,defaultdict
from itertools import combinations
ROOT=Path(r'C:\Users\admin\Documents\Codex\2026-10-09\6-45-jiae-jeong-lotto-data');OUT=ROOT/'outputs/A_ERRORLOOP_C_RESEARCH_20261009_v2';WT=ROOT/'work/primary_mode_1245_v4_clean_20261009'
def rr(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def close(a,b):assert math.isclose(float(a),float(b),rel_tol=1e-11,abs_tol=1e-11),(a,b)
checks=[]
def passed(s):checks.append(s);print('PASS '+s,flush=True)
data=rr(WT/'lotto_data.csv');assert [int(x['round']) for x in data]==list(range(1,1245))
draws=[set(int(x[f'no{i}']) for i in range(1,7)) for x in data]
assert sha(WT/'lotto_data.csv')=='243cd17e6b97a2d96709ddfc689a068038669341a52dcc0743c141d309e43b9f'
assert all(len(s)==6 and min(s)>=1 and max(s)<=45 and 1<=int(x['bonus'])<=45 and int(x['bonus']) not in s for s,x in zip(draws,data))
passed('independent raw integrity 1..1244 and pinned SHA')
for sf in ['EXECUTION_PLAN_SEAL.json','SIGNAL_EXTENSION_SEAL.json']:
    seal=json.loads((OUT/sf).read_text())
    for f,h in seal['files'].items():assert sha(OUT/f)==h
assert json.loads((OUT/'ACTUAL_EXECUTION_RESULT.json').read_text())['exit_code']==0 and (OUT/'EXECUTION_STDERR.log').stat().st_size==0
assert json.loads((OUT/'EXTENSION_EXECUTION_RESULT.json').read_text())['exit_code']==0
assert json.loads((OUT/'failed_v1_evidence/ACTUAL_EXECUTION_RESULT.json').read_text())['exit_code']==1
passed('pre-run code/config seals; successful v2 and preserved failed v1')
freqrows=rr(OUT/'NUMBER_SIGNAL_WINDOWS.csv');assert len(freqrows)==225
for x in freqrows:
    lo=int(x['start_round'])-1;hi=int(x['end_round']);n=int(x['number']);sub=draws[lo:hi];occ=[t+1 for t,s in enumerate(draws) if n in s];co=sum(n in s for s in sub)
    assert int(x['count'])==co;close(x['rate'],co/len(sub));assert int(x['current_global_wait'])==1244-occ[-1]
    gaps=[b-a for a,b in zip(occ,occ[1:]) if lo<b<=hi]
    if gaps:close(x['mean_completed_gap_ending_in_window'],statistics.mean(gaps));assert int(x['latest_completed_gap_ending_in_window'])==gaps[-1]
    else:assert x['mean_completed_gap_ending_in_window']==''
    counts={i:sum(i in s for s in sub) for i in range(1,46)};ranking=sorted(counts,key=lambda i:(-counts[i],i));assert int(x['frequency_rank'])==ranking.index(n)+1
passed('225 independent single-number/window counts, ranks, completed/current gaps')
reld=rr(OUT/'PAIR_TRIPLE_WINDOW_SIGNALS.csv');assert len(reld)==75900
reference={}
for name,w in [('overall',1244),('recent10',10),('recent30',30),('recent50',50),('recent100',100)]:
    for order in [2,3]:reference[name,order]=Counter(k for s in draws[-w:] for k in combinations(sorted(s),order))
for x in reld:
    order=int(x['order']);key=tuple(map(int,x['numbers'].split('-')));count=reference[x['window'],order][key];assert int(x['count'])==count;close(x['rate'],count/int(x['n_draws']));close(x['exact_uniform_probability'],math.comb(6,order)/math.comb(45,order))
for order,total in [(2,18660),(3,24880)]:assert sum(int(x['count']) for x in reld if x['window']=='overall' and int(x['order'])==order)==total
passed('all 75900 pair/triple window records and exact marginal probabilities')
features=rr(OUT/'DRAW_STRUCTURE_FEATURES.csv');assert len(features)==1244
binary=[]
for i,(x,ns) in enumerate(zip(features,draws)):
    sn=sorted(ns);g=[b-a for a,b in zip(sn,sn[1:])];band=[sum(lo<=n<=hi for n in ns) for lo,hi in [(1,10),(11,20),(21,30),(31,40),(41,45)]];ends=Counter(n%10 for n in ns);ov=None if i==0 else len(ns&draws[i-1])
    numerical=dict(odd_count=sum(n%2 for n in ns),low_count=sum(n<=22 for n in ns),sum=sum(ns),span=sn[-1]-sn[0],min_gap=min(g),max_gap=max(g),consecutive_pairs=sum(v==1 for v in g),repeat_end_extra=6-len(ends),max_end_multiplicity=max(ends.values()),repeat_end_groups=sum(v>=2 for v in ends.values()),band_max=max(band))
    for f,v in numerical.items():assert int(x[f])==v
    for j,v in enumerate(band,1):assert int(x[f'band_{j}_count'])==v
    for j,v in enumerate(g,1):assert int(x[f'gap_{j}'])==v
    assert x['previous_overlap']==('' if ov is None else str(ov))
    bs=dict(consecutive_ge1=sum(v==1 for v in g)>=1,consecutive_ge2=sum(v==1 for v in g)>=2,band_ge3=max(band)>=3,band_ge4=max(band)>=4,odd_imbalance=numerical['odd_count'] in [0,1,5,6],low_high_imbalance=numerical['low_count'] in [0,1,5,6],repeated_end=len(ends)<6,end_multiplicity_ge3=max(ends.values())>=3,multiple_repeat_end_groups=sum(v>=2 for v in ends.values())>=2,extreme_sum=sum(ns)<=90 or sum(ns)>=186,narrow_three_span_le4=any(sn[j+2]-sn[j]<=4 for j in range(4)),large_gap_ge15=max(g)>=15,previous_overlap_ge2=None if ov is None else ov>=2)
    for f,v in bs.items():assert x[f]==('' if v is None else str(int(v)))
    binary.append(bs)
for x in rr(OUT/'CONTRARIAN_STRUCTURE_INCIDENCE.csv'):
    w=1244 if x['window']=='overall' else int(x['window'][6:]);values=[bs[x['structure']] for bs in binary[-w:] if bs[x['structure']] is not None];assert int(x['count'])==sum(values) and int(x['n'])==len(values);close(x['rate'],sum(values)/len(values))
passed('1244 independent draw structures, 65 incidence records and first-draw overlap missingness')
# Independent binary-position DP for adjacency, tight three-number clusters and internal large gaps.
den=math.comb(45,6);exact=json.loads((OUT/'EXACT_STRUCTURE_BASELINE.json').read_text())['probabilities']
dp={(0,0,0):1}
for pos in range(45):
    nd=defaultdict(int)
    for (k,prev,adj),count in dp.items():
        nd[k,0,adj]+=count
        if k<6:nd[k+1,1,min(2,adj+prev)]+=count
    dp=nd
close(exact['consecutive_ge1'],sum(v for (k,p,a),v in dp.items() if k==6 and a>=1)/den)
close(exact['consecutive_ge2'],sum(v for (k,p,a),v in dp.items() if k==6 and a>=2)/den)
dp={(0,0,0):1}
for pos in range(45):
    nd=defaultdict(int)
    for (k,mask,event),count in dp.items():
        nd[k,(mask<<1)&15,event]+=count
        if k<6:nd[k+1,((mask<<1)|1)&15,event or mask.bit_count()>=2]+=count
    dp=nd
close(exact['narrow_three_span_le4'],sum(v for (k,m,e),v in dp.items() if k==6 and e)/den)
dp={(0,0,0):1}
for pos in range(45):
    nd=defaultdict(int)
    for (k,gap,event),count in dp.items():
        nd[k,min(14,gap+1) if k else 0,event]+=count
        if k<6:nd[k+1,0,event or (k>=1 and gap>=14)]+=count
    dp=nd
close(exact['large_gap_ge15'],sum(v for (k,g,e),v in dp.items() if k==6 and e)/den)
for threshold in [3,4]:
    dp={(0,False):1}
    for size in [10,10,10,10,5]:
        nd=defaultdict(int)
        for (k,event),c in dp.items():
            for m in range(min(size,6-k)+1):nd[k+m,event or m>=threshold]+=c*math.comb(size,m)
        dp=nd
    close(exact[f'band_ge{threshold}'],dp[6,True]/den)
end_sizes=Counter(n%10 for n in range(1,46));dp={(0,0,False):1}
for size in end_sizes.values():
    nd=defaultdict(int)
    for (k,reps,triple),c in dp.items():
        for m in range(min(size,6-k)+1):nd[k+m,reps+(m>=2),triple or m>=3]+=c*math.comb(size,m)
    dp=nd
for f,condition in [('repeated_end',lambda r,t:r>=1),('multiple_repeat_end_groups',lambda r,t:r>=2),('end_multiplicity_ge3',lambda r,t:t)]:close(exact[f],sum(v for (k,r,t),v in dp.items() if k==6 and condition(r,t))/den)
for f,small in [('odd_imbalance',23),('low_high_imbalance',22)]:close(exact[f],sum(math.comb(small,k)*math.comb(45-small,6-k) for k in [0,1,5,6])/den)
close(exact['previous_overlap_ge2'],sum(math.comb(6,k)*math.comb(39,6-k) for k in range(2,7))/den)
sumdp=[[0]*271 for _ in range(7)];sumdp[0][0]=1
for n in range(1,46):
    for k in range(6,0,-1):
        for s in range(270,n-1,-1):sumdp[k][s]+=sumdp[k-1][s-n]
close(exact['extreme_sum'],sum(sumdp[6][s] for s in range(271) if s<=90 or s>=186)/den)
passed('all 13 exact structure baselines independently counted; no Monte Carlo or tickets generated')
forecast=rr(OUT/'STRUCTURE_WALKFORWARD_PROBABILITIES.csv');assert len(forecast)==5200
for x in forecast:
    t=int(x['target_round']);lo=int(x['training_start_round']);assert 1045<=t<=1244 and int(x['training_through_round'])==t-1
    assert lo==(1 if x['mode']=='expanding' else t-300)
    f=x['structure'];hist=[b[f] for b in binary[lo-1:t-1] if b[f] is not None];co=sum(hist);assert int(x['training_n'])==len(hist) and int(x['training_count'])==co
    p=(co+20*exact[f])/(len(hist)+20);close(x['predicted_probability'],p);y=int(binary[t-1][f]);assert int(x['actual_historical_structure'])==y;close(x['brier'],(p-y)**2)
for x in rr(OUT/'STRUCTURE_VETO_COVERAGE_DIAGNOSTIC.csv'):
    loss=sum(bool(b[x['structure']]) for b in binary[1044:1244])/200;close(x['coverage_loss'],loss);close(x['veto_winning_structure_coverage'],1-loss)
passed('5200 historical probability forecasts train strictly through t-1 and 13 coverage diagnoses')
gapseq=rr(OUT/'GAP_CUTOFF_TIME_SERIES.csv');assert len(gapseq)==55980;last={};intervals=defaultdict(list)
for t in range(1,1245):
    for n in draws[t-1]:
        if n in last:intervals[n].append(t-last[n])
        last[n]=t
    for n in range(1,46):
        x=gapseq[(t-1)*45+n-1];assert int(x['cutoff'])==t and int(x['number'])==n
        assert x['current_wait']==('' if n not in last else str(t-last[n]))
        if intervals[n]:close(x['mean_completed_gap'],statistics.mean(intervals[n]));assert int(x['latest_completed_gap'])==intervals[n][-1]
passed('55980 longitudinal gap records recomputed with prefix-only counters')
endrows=rr(OUT/'ENDING_DIGIT_WINDOW_DISTRIBUTIONS.csv');assert len(endrows)==350
for x in endrows:
    w=1244 if x['window']=='overall' else int(x['window'][6:]);digit=int(x['ending_digit']);m=int(x['multiplicity']);count=sum(sum(n%10==digit for n in s)==m for s in draws[-w:]);assert int(x['draw_count'])==count
passed('350 ending-digit multiplicity records')
verdict=json.loads((OUT/'SOURCE_SEARCH_VERDICT.json').read_text());assert all(verdict[k]=='NOT FOUND' for k in ['A_MODEL_ORIGINAL','C_MODEL_ORIGINAL','CONTRARIAN_MODEL_ORIGINAL'])
assert len(rr(OUT/'HISTORICAL_RECOMMENDATION_SOURCE_COVERAGE.csv'))==1244
assert json.loads((OUT/'ERRORLOOP_VERIFICATION_STATUS.json').read_text())['eligible_authentic_historical_recommendations']==0
assert len(rr(OUT/'NEW_HYPOTHESIS_REGISTRY.csv'))==6
assert all(x['recommendation_use']=='PROHIBITED until separately validated' for x in rr(OUT/'NEW_HYPOTHESIS_REGISTRY.csv'))
passed('missing legacy sources/error loop recorded; six hypotheses not adopted')
state=json.loads((ROOT/'work/A_RESEARCH_PUBLICATION_STATE_20261009_v1.json').read_text())
def snap(p):return {f.relative_to(p).as_posix():dict(sha256=sha(f),bytes=f.stat().st_size,mtime_ns=f.stat().st_mtime_ns) for f in p.rglob('*') if f.is_file() and '.git' not in f.parts}
assert snap(WT)==state['tracked_snapshot']
for name,key in [('B_MODEL_REPRODUCTION_20261009_v1','b_audit'),('B_RANDOM_BASELINE_20261009_v1','b_random')]:assert snap(ROOT/'outputs'/name)==state[key]
passed('all pre-existing worktree and frozen B/MC file content/size/mtime unchanged')
script=(OUT/'run_independent_signal_research.py').read_text();tree=ast.parse(script)
imports=[n for n in ast.walk(tree) if isinstance(n,(ast.Import,ast.ImportFrom))]
assert not any('prospective_engine' in ast.unparse(n) or 'b_model_backtest' in ast.unparse(n) for n in imports)
passed('no legacy model execution import; no result after1244 used in inputs')
result=dict(status='PASS',verified_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),checks=checks,cutoff=1244,actual_1245='NOT READ / NOT USED',new_tickets_or_candidates_generated=False,B_rerun=False,original_A_C_contrarian='NOT FOUND',authentic_errorloop='NOT EXECUTED; SOURCE NOT FOUND',predictive_advantage='INSUFFICIENT EVIDENCE',existing_tracked_file_changes=0,verification_limit='Statistical/counterfactual ticket performance not verified; source search covers accessible paths and reachable history only')
with (OUT/'FINAL_VERIFICATION.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print('FINAL VERIFICATION PASS; independent computations, preserved evidence and explicit missing-source limitations')
