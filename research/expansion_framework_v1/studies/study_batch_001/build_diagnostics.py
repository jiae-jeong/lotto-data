"""Supplemental diagnostics for Study Batch 001; outputs are create-only."""
import csv,math,statistics
from collections import Counter,defaultdict
from itertools import combinations
from pathlib import Path
HERE=Path(__file__).resolve().parent
import sys
sys.path.insert(0,str(HERE.parents[1]))
from walkforward_core import load_draws_through
DATA=Path(r"C:\Users\user\Documents\Codex\2026-10-06\cloud-x20\work\lotto-data\lotto_data.csv")
OLD=Path(r"C:\Users\user\Documents\Codex\2026-10-06\cloud-x20\outputs")
def read(p):
 with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def write(name,rows):
 with (HERE/name).open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def wilson(k,n):
 if n==0:return ('','')
 z=1.959963984540054;p=k/n;d=1+z*z/n;c=(p+z*z/(2*n))/d;h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d;return c-h,c+h
def main():
 draws=[d.numbers for d in load_draws_through(DATA,1244)]
 if len(draws)!=1244:raise ValueError('Expected exactly 1244 draws')
 # Per-number multiscale counts and forward recurrence outcomes.
 nf=[]; cf=[]
 for x in range(1,46):
  occ=[i+1 for i,d in enumerate(draws) if x in d];ints=[b-a for a,b in zip(occ,occ[1:])]
  row={'number':x,'full_count':len(occ),'current_gap':1244-occ[-1]}
  for w in (10,20,30,50,100,200,300):
   c=sum(x in d for d in draws[-w:]);rate=c/w;row[f'last{w}_count']=c;row[f'last{w}_rate']=rate;row[f'last{w}_delta_vs_long']=rate-6/45
  deltas=[row[f'last{w}_delta_vs_long'] for w in (10,20,30,50,100,200,300)]
  row['window_sign_consistency']=sum(v>0 for v in deltas)/len(deltas);row['window_positive_count']=sum(v>0 for v in deltas);row['window_negative_count']=sum(v<0 for v in deltas)
  row['interarrival_mean']=statistics.mean(ints) if ints else '';row['interarrival_median']=statistics.median(ints) if ints else '';row['immediate_recurrence_count']=sum(g==1 for g in ints);row['one_skip_recurrence_count']=sum(g==2 for g in ints);row['two_plus_skip_recurrence_count']=sum(g>=3 for g in ints)
  # State movement from earlier 20 to latest 20, using only known history.
  a=sum(x in d for d in draws[-40:-20]);b=sum(x in d for d in draws[-20:]);row['prior20_count']=a;row['recent20_count']=b;row['state_transition']=('hot' if a>20*6/45 else 'cold')+'_to_'+('hot' if b>20*6/45 else 'cold');nf.append(row)
  cond_specs=[('prev1',lambda i: int(x in draws[i-1])),('recent3_count',lambda i:sum(x in d for d in draws[max(0,i-3):i])),('recent5_count',lambda i:sum(x in d for d in draws[max(0,i-5):i])),('recent10_state',lambda i:'hot' if sum(x in d for d in draws[max(0,i-10):i])>10*6/45 else 'cold')]
  for label,fn in cond_specs:
   accum=defaultdict(lambda:[0,0])
   for i in range(1,1244):
    state=fn(i);accum[state][0]+=1;accum[state][1]+=int(x in draws[i])
   for state,(n,s) in accum.items():
    lo,hi=wilson(s,n);cf.append({'number':x,'condition':label,'state':state,'n_condition':n,'next_draw_count':s,'conditional_rate':s/n if n else 0,'wilson95_low':lo,'wilson95_high':hi,'base_rate':6/45,'delta_vs_base':s/n-6/45 if n else 0,'small_sample':n<30,'cutoff_rule':'condition uses draws strictly before target'})
 write('number_temporal_features.csv',nf);write('conditional_number_transitions.csv',cf)
 # Structural next-step transitions across eight interpretable categories.
 def feature(d,prev):
  gs=[b-a for a,b in zip(d,d[1:])];ends=Counter(x%10 for x in d)
  return {'odd_even':'odd'+str(sum(x%2 for x in d)),'low_high':'low'+str(sum(x<=22 for x in d)),'sum_band':'sum'+str(sum(d)//30),'five_band':'-'.join(str(sum(lo<=x<=hi for x in d)) for lo,hi in [(1,10),(11,20),(21,30),(31,40),(41,45)]),'consecutive':'consecutive'+str(sum(g==1 for g in gs)),'end_repeat':'repeat'+str(sum(v-1 for v in ends.values() if v>1)),'overlap':'overlap'+str(len(set(d)&set(prev))),'cluster':'cluster'+str(1+sum(g>5 for g in gs))}
 trans=[]
 for key in ['odd_even','low_high','sum_band','five_band','consecutive','end_repeat','overlap','cluster']:
  c=Counter();by=Counter();marg=Counter()
  for i in range(1,len(draws)):
   a=feature(draws[i-1],draws[i-2] if i>1 else ())[key];b=feature(draws[i],draws[i-1])[key];c[a,b]+=1;by[a]+=1;marg[b]+=1
  for (a,b),n in sorted(c.items()):
   p=n/by[a];base=marg[b]/(len(draws)-1);lo,hi=wilson(n,by[a]);trans.append({'structure':key,'current_state':a,'next_state':b,'transition_n':n,'current_state_n':by[a],'transition_probability':p,'wilson95_low':lo,'wilson95_high':hi,'next_state_marginal':base,'delta_vs_marginal':p-base,'small_sample':by[a]<30})
 write('structure_transition_analysis.csv',trans)
 # Pair and triple temporal stability across fixed intervals.
 temporal=[]
 for size,label in [(2,'pair'),(3,'triple')]:
  sets=defaultdict(Counter)
  for i,d in enumerate(draws):
   q=i+1
   for c in combinations(d,size):
    sets['full'][c]+=1
    if q>1244-200:sets['last200'][c]+=1
    if q>1244-100:sets['last100'][c]+=1
    if q>1244-50:sets['last50'][c]+=1
    if q<=622:sets['first_half'][c]+=1
    else:sets['second_half'][c]+=1
  for c in combinations(range(1,46),size):
   full=sets['full'][c];row={'relationship':label,'numbers':'-'.join(map(str,c)),'full_count':full,'first_half_count':sets['first_half'][c],'second_half_count':sets['second_half'][c],'recent50_count':sets['last50'][c],'recent100_count':sets['last100'][c],'recent200_count':sets['last200'][c]}
   for k,n in [('recent50',50),('recent100',100),('recent200',200)]:row[k+'_per_draw']=sets[k][c]/n;row[k+'_delta_rate_vs_full']=sets[k][c]/n-full/1244
   row['half_change']=sets['second_half'][c]/622-sets['first_half'][c]/622;row['persisted_recent50']=int(full>0 and sets['last50'][c]>0);row['posthoc_multiple_testing']='Exploratory; no multiplicity correction';temporal.append(row)
 write('pair_triple_temporal_stability.csv',temporal)
 # Condense all model/window rows into requested study_results table.
 write('study_results.csv',read(HERE/'model_metrics.csv'))
 # Compare the same targets with immutable B-v1 source forecasts.
 new=read(HERE/'walkforward_predictions.csv');old=read(OLD/'b_model_predictions.csv');base={}
 for r in old:
  t=int(r['target_round']);m=r['model']
  if 201<=t<=1244 and int(r['training_through_round'])==t-1:base.setdefault((t,m),r)
 bymodel=defaultdict(list)
 for r in new:bymodel[r['model']].append(r)
 out=[]
 for name,rs in bymodel.items():
  for bm in sorted({m for _,m in base}):
   ovs=[];ha=[];hb=[]
   for r in rs:
    t=int(r['target_round']);b=base.get((t,bm))
    if not b:continue
    a_set=set(map(int,r['predicted_numbers'].split()));b_set=set(map(int,b['predicted_numbers'].replace(',',' ').split()));ovs.append(len(a_set&b_set));ha.append(int(r['hits']));hb.append(int(b['hits']))
   out.append({'new_model':name,'b_v1_model':bm,'n':len(ovs),'mean_ticket_overlap':statistics.mean(ovs),'mean_jaccard':statistics.mean(v/(12-v) if v<6 else 1 for v in ovs),'hit_correlation':statistics.correlation(ha,hb) if len(set(ha))>1 and len(set(hb))>1 else ''})
 write('b_model_comparison.csv',out)
 print(f'DIAGNOSTICS_OK conditional={len(cf)} structure_transitions={len(trans)} relationship_rows={len(temporal)} B_comparisons={len(out)}')
if __name__=='__main__':main()
