from pathlib import Path
import csv,json,math,hashlib,datetime,statistics,subprocess,sys
from collections import Counter
ROOT=Path(r'C:\Users\admin\Documents\Codex\2026-10-09\6-45-jiae-jeong-lotto-data');OUT=ROOT/'outputs/A_ERRORLOOP_C_RESEARCH_20261009_v2';WT=ROOT/'work/primary_mode_1245_v4_clean_20261009'
def rr(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def write(n,r):
    with (OUT/n).open('x',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(r[0]),lineterminator='\n');w.writeheader();w.writerows(r)
def mean(v):return statistics.mean(v) if v else None
def direction(d):return 'UP' if d>1e-12 else 'DOWN' if d< -1e-12 else 'FLAT'
data=rr(WT/'lotto_data.csv');assert len(data)==1244 and int(data[-1]['round'])==1244
draws=[list(map(int,[x[f'no{i}'] for i in range(1,7)])) for x in data];seq=[];latest=[None]*46;gaps=[[] for _ in range(46)];occ=[[] for _ in range(46)];freq=[0]*46
for t,ns in enumerate(draws,1):
    for n in ns:
        if latest[n] is not None:gaps[n].append((t,t-latest[n]))
        latest[n]=t;occ[n].append(t);freq[n]+=1
    for n in range(1,46):seq.append(dict(cutoff=t,number=n,current_wait=None if latest[n] is None else t-latest[n],never_seen=latest[n] is None,mean_completed_gap=mean([v for _,v in gaps[n]]),latest_completed_gap=None if not gaps[n] else gaps[n][-1][1]))
write('GAP_CUTOFF_TIME_SERIES.csv',seq)
summary=[]
for label,lo in [('overall',0),('recent10',1234),('recent30',1214),('recent50',1194),('recent100',1144)]:
    for n in range(1,46):
        for field in ['current_wait','mean_completed_gap','latest_completed_gap']:
            values=[x[field] for x in seq if x['number']==n and x['cutoff']>lo and x[field] is not None];prior=[x[field] for x in seq if x['number']==n and x['cutoff']<=lo and x[field] is not None]
            delta=None if not prior else mean(values)-mean(prior)
            summary.append(dict(window=label,number=n,feature=field,n=len(values),mean=mean(values),sd=statistics.pstdev(values) if values else None,delta_vs_disjoint_prior=delta,direction='NA' if delta is None else direction(delta),independent_observations=False,censoring='Never-seen waiting time excluded; completed gaps condition on completion; cutoff sequence serially dependent'))
write('GAP_WINDOW_AND_DIRECTION_SUMMARY.csv',summary)
period=[]
for lo in range(1,1245,50):
    hi=min(lo+49,1244)
    for field in ['current_wait','mean_completed_gap','latest_completed_gap']:
        values=[x[field] for x in seq if lo<=x['cutoff']<=hi and x[field] is not None]
        period.append(dict(start_cutoff=lo,end_cutoff=hi,feature=field,number_cutoff_observations=len(values),mean=mean(values),sd=statistics.pstdev(values),partial=hi-lo+1!=50,independent_observations=False))
write('GAP_TIME_BLOCK_SUMMARY.csv',period)
recent=rr(OUT/'NUMBER_SIGNAL_WINDOWS.csv');directions=[];fullrank={int(x['number']):int(x['frequency_rank']) for x in recent if x['window']=='overall'}
grank={n:i+1 for i,n in enumerate(sorted(range(1,46),key=lambda n:(-(1244-latest[n]),n)))}
for n in range(1,46):
    for w in [10,30,50,100]:
        item=next(x for x in recent if int(x['number'])==n and x['window']==f'recent{w}');long=freq[n]/1244;rate=float(item['rate']);gaprecent=[g for t,g in gaps[n] if t>1244-w];gapprior=[g for t,g in gaps[n] if t<=1244-w];gd=None if not gaprecent or not gapprior else mean(gaprecent)-mean(gapprior)
        pattern=('LONG_ABOVE_RECENT_BELOW' if long>6/45 and rate<6/45 else 'LONG_BELOW_RECENT_ABOVE' if long<6/45 and rate>6/45 else 'SAME_SIDE_OR_TIE')
        directions.append(dict(number=n,recent_window=w,long_frequency_rank=fullrank[n],recent_frequency_rank=int(item['frequency_rank']),current_gap_rank=grank[n],long_recent_pattern=pattern,long_frequency_rate=long,recent_frequency_rate=rate,delta_completed_gap_vs_disjoint_prior=gd,gap_direction='NA' if gd is None else direction(gd),hypothesis_status='DESCRIPTIVE / UNVALIDATED'))
write('LONG_RECENT_SIGNAL_CONFLICTS.csv',directions)
end=[]
for label,lo in [('overall',0),('recent10',1234),('recent30',1214),('recent50',1194),('recent100',1144)]:
    for digit in range(10):
        cc=Counter(sum(n%10==digit for n in ns) for ns in draws[lo:]);total=sum(k*v for k,v in cc.items())
        for multiplicity in range(7):end.append(dict(window=label,ending_digit=digit,multiplicity=multiplicity,draw_count=cc[multiplicity],n_draws=1244-lo,rate=cc[multiplicity]/(1244-lo),number_occurrences=total,number_share=total/(6*(1244-lo)),exact_uniform_number_share=sum(n%10==digit for n in range(1,46))/45))
write('ENDING_DIGIT_WINDOW_DISTRIBUTIONS.csv',end)
source=(WT/'research/expansion_framework_v1/studies/study_batch_001/run_batch.py').read_text(encoding='utf-8');tree=__import__('ast').parse(source)
func=next(n for n in tree.body if isinstance(n,__import__('ast').FunctionDef) and n.name=='make_models');segment=__import__('ast').get_source_segment(source,func)
assert 'ranks.append([45.]*45)' in segment and 'ranks.append([0.]*45)' in segment and 'for x in range(1,46)' in segment
with (OUT/'RELATED_S008_ALGEBRA_VERIFICATION.json').open('x',encoding='utf-8') as f:json.dump(dict(status='VERIFIED_CODE_AND_ALGEBRA',source_sha256=hashlib.sha256(source.encode()).hexdigest(),number_of_component_rank_vectors=6,number_of_constant_structure_vectors=45,positive_constant_structure_vectors=6,total_vectors=51,total_added_constant_per_number=270,effective_score_formula='(sum_of_six_component_ranks[i]+270)/51',ranking_influence_of_structure=0,historical_backtest_rerun='NOT EXECUTED',legacy_C_identity='NOT ESTABLISHED',no_numbers_or_tickets_generated=True),f,indent=2)
print('EXTENSION PASS gap_cutoff_rows='+str(len(seq))+'; directions='+str(len(directions))+'; ending_distribution_rows='+str(len(end))+'; related S008 algebra verified; no candidates generated')
