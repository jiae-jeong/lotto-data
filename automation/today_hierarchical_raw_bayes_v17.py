#!/usr/bin/env python3
from __future__ import annotations
import csv,importlib.util,itertools,json,random,statistics
from collections import Counter,defaultdict
from datetime import datetime,timezone,timedelta
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'lotto_data.csv'
B_SOURCE=ROOT/'research/1245_final_pipeline_v3/recovered_original_assets/b_model_backtest.py'
AC_SOURCE=ROOT/'automation/recovered_models_v2.py'
V12_SOURCE=ROOT/'automation/today_raw_signal_meta_v12.py'
OUT=ROOT/'analysis/2026-10-23/TODAY_HIERARCHICAL_RAW_BAYES_1247_V17.json'
KST=timezone(timedelta(hours=9))
B=('long_frequency','current_gap','frequency_plus_gap','recent_momentum','structure_profile','pair_association','triple_association','combined_equal_rank')
AC=('A_v2','C_v2','contrarian_v2')
MODELS=B+AC
BASE=6/45
ROLES=('total','consensus','gap_recent','relation','frequency_stability')
TEST_NULL=160;BLOCK=50;BOOT=5000;SEED=202610240900

def imp(path,name):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def load_draws():
 out=[]
 with DATA.open(encoding='utf-8-sig') as f:
  for r in csv.DictReader(f):out.append({'round':int(r['round']),'date':r['date'],'nums':tuple(sorted(int(r[f'no{i}']) for i in range(1,7)))})
 assert out[-1]['round']==1246 and [x['round'] for x in out]==list(range(1,1247));return out

def qbins(values,q=4):
 order=sorted(range(len(values)),key=lambda i:(values[i],i));out=[0]*len(values)
 for rank,i in enumerate(order):out[i]=min(q-1,rank*q//len(values))
 return out

def cats_from_X(X,preds):
 vals={name:[X[n][idx] for n in range(1,46)] for name,idx in [('freq',13),('gap',14),('recent',15),('momentum',16),('pair',17),('triple',18)]}
 bins={k:qbins(v) for k,v in vals.items()};out={}
 for n in range(1,46):
  votes=[1 if n in preds[m] else 0 for m in MODELS];mask=sum(v<<i for i,v in enumerate(votes));vc=sum(votes);i=n-1
  out[n]={'vote':min(5,vc),'mask':mask,'freq':bins['freq'][i],'gap':bins['gap'][i],'recent':bins['recent'][i],'momentum':bins['momentum'][i],'pair':bins['pair'][i],'triple':bins['triple'][i],'prev':int(X[n][19]>0),'adj':int(X[n][20]>0)}
 return out

def post(stat,strength):
 w,t=stat;return (w+strength*BASE)/(t+strength)

def score_all(cats,unary,pair,exact,maskstat):
 role={r:{} for r in ROLES};details={}
 for n,c in cats.items():
  u={k:post(unary[(k,c[k])],150) for k in ('vote','freq','gap','recent','momentum','pair','triple','prev','adj')}
  pp={
   'vote_gap':post(pair[('vote_gap',c['vote'],c['gap'])],105),
   'vote_recent':post(pair[('vote_recent',c['vote'],c['recent'])],105),
   'vote_pair':post(pair[('vote_pair',c['vote'],c['pair'])],105),
   'gap_recent':post(pair[('gap_recent',c['gap'],c['recent'])],100),
   'momentum_recent':post(pair[('momentum_recent',c['momentum'],c['recent'])],100),
   'pair_triple':post(pair[('pair_triple',c['pair'],c['triple'])],100),
   'freq_gap':post(pair[('freq_gap',c['freq'],c['gap'])],100),
   'prev_adj':post(pair[('prev_adj',c['prev'],c['adj'])],100),
  }
  ex=post(exact[(c['vote'],c['gap'],c['recent'],c['pair'],c['triple'])],260);mk=post(maskstat[c['mask']],260)
  pairavg=statistics.mean(pp.values());unavg=statistics.mean(u.values())
  role['total'][n]=.30*unavg+.45*pairavg+.20*ex+.05*mk
  role['consensus'][n]=.30*u['vote']+.20*mk+.25*pp['vote_gap']+.25*pp['vote_recent']
  role['gap_recent'][n]=.20*u['gap']+.18*u['recent']+.14*u['momentum']+.22*pp['gap_recent']+.14*pp['momentum_recent']+.12*pp['vote_gap']
  role['relation'][n]=.22*u['pair']+.18*u['triple']+.24*pp['pair_triple']+.20*pp['vote_pair']+.16*u['vote']
  role['frequency_stability'][n]=.22*u['freq']+.20*u['gap']+.18*u['recent']+.18*pp['freq_gap']+.12*ex+.10*pp['prev_adj']
  details[n]={'categories':c,'unary':u,'pairs':pp,'exact':ex,'mask':mk,'role_scores':{r:role[r][n] for r in ROLES}}
 return role,details

def update(cats,actual,unary,pair,exact,maskstat):
 for n,c in cats.items():
  y=int(n in actual)
  for k in ('vote','freq','gap','recent','momentum','pair','triple','prev','adj'):unary[(k,c[k])][0]+=y;unary[(k,c[k])][1]+=1
  keys=[('vote_gap',c['vote'],c['gap']),('vote_recent',c['vote'],c['recent']),('vote_pair',c['vote'],c['pair']),('gap_recent',c['gap'],c['recent']),('momentum_recent',c['momentum'],c['recent']),('pair_triple',c['pair'],c['triple']),('freq_gap',c['freq'],c['gap']),('prev_adj',c['prev'],c['adj'])]
  for k in keys:pair[k][0]+=y;pair[k][1]+=1
  ek=(c['vote'],c['gap'],c['recent'],c['pair'],c['triple']);exact[ek][0]+=y;exact[ek][1]+=1;maskstat[c['mask']][0]+=y;maskstat[c['mask']][1]+=1

def ticket_for(score,used):
 pool=sorted(range(1,46),key=lambda n:(-score[n],n))[:12];best=None
 for t in itertools.combinations(pool,6):
  tt=tuple(sorted(t))
  if tt in used:continue
  odd=sum(n%2 for n in tt);low=sum(n<=22 for n in tt);cons=sum(b-a==1 for a,b in zip(tt,tt[1:]));bands=len({(n-1)//10 for n in tt})
  val=sum(score[n] for n in tt)-.0025*abs(odd-3)-.0020*abs(low-3)-.0015*max(0,cons-2)+.0005*bands
  key=(val,tuple(-n for n in tt))
  if best is None or key>best[0]:best=(key,tt)
 return best[1]

def build(role):
 lines=[];used=set()
 for r in ROLES:
  t=ticket_for(role[r],used);lines.append(t);used.add(t)
 return lines

def metrics(lines,actual):
 ss=[set(x) for x in lines];hits=[len(x&actual) for x in ss];u=set().union(*ss);ovs=[len(ss[i]&ss[j]) for i in range(5) for j in range(i+1,5)]
 return {'max_hits':max(hits),'any2':int(max(hits)>=2),'any3':int(max(hits)>=3),'any4':int(max(hits)>=4),'any5':int(max(hits)>=5),'any6':int(max(hits)>=6),'winning_union_coverage':len(u&actual),'union_size':len(u),'mean_overlap':statistics.mean(ovs),'max_overlap':max(ovs)}
def permuted(lines,rng):
 labs=list(range(1,46));sh=labs[:];rng.shuffle(sh);mp=dict(zip(labs,sh));return [tuple(sorted(mp[n] for n in row)) for row in lines]
def avg(rows,k):return statistics.mean(float(r[k]) for r in rows)
def ci(vals,alpha,seed):
 blocks=[vals[i:i+BLOCK] for i in range(0,len(vals),BLOCK)];rng=random.Random(seed);reps=[]
 for _ in range(BOOT):
  flat=[]
  for __ in range(len(blocks)):flat+=blocks[rng.randrange(len(blocks))]
  reps.append(statistics.mean(flat))
 reps.sort();return [reps[int(alpha/2*(len(reps)-1))],reps[int((1-alpha/2)*(len(reps)-1))]]
def posshare(vals):
 b=[statistics.mean(vals[i:i+BLOCK]) for i in range(0,len(vals),BLOCK)];return sum(x>0 for x in b)/len(b)

def main():
 draws=load_draws();b=imp(B_SOURCE,'bv17');ac=imp(AC_SOURCE,'acv17');v12=imp(V12_SOURCE,'v12v17');bank=b.feature_structure_bank(b.make_structure_bank());freq=[0]*45;last=[0]*45;pc=Counter();tc=Counter();profiles=[Counter() for _ in range(6)]
 for d in draws[:200]:
  for n in d['nums']:freq[n-1]+=1;last[n-1]=d['round']
  pc.update(itertools.combinations(d['nums'],2));tc.update(itertools.combinations(d['nums'],3));pr=b.structure_profile(d['nums'],None)
  for i,v in enumerate(pr[:5]):profiles[i][v]+=1
 for i in range(1,200):profiles[5][b.structure_profile(draws[i]['nums'],draws[i-1]['nums'])[5]]+=1
 unary=defaultdict(lambda:[0,0]);pair=defaultdict(lambda:[0,0]);exact=defaultdict(lambda:[0,0]);maskstat=defaultdict(lambda:[0,0]);obs=[];null=[];diffs={k:[] for k in ('max_hits','any2','any3','winning_union_coverage')};current=None
 for idx in range(200,len(draws)+1):
  hist=[q['nums'] for q in draws[:idx]];preds={**b.predictions_for_round(draws,idx,freq,last,pc,tc,profiles,bank),**ac.predict(hist)};X=v12.raw_features(draws,idx,freq,last,pc,tc,preds);cats=cats_from_X(X,preds);role,details=score_all(cats,unary,pair,exact,maskstat);lines=build(role)
  if idx==len(draws):current={'lines':[list(t) for t in lines],'roles':{ROLES[i]:list(lines[i]) for i in range(5)},'top_by_role':{r:sorted(range(1,46),key=lambda n:(-role[r][n],n))[:15] for r in ROLES},'number_details':{str(n):details[n] for n in details}};break
  actual=set(draws[idx]['nums']);target=idx+1
  if target>=401:
   om=metrics(lines,actual);om['target']=target;obs.append(om);rng=random.Random(SEED+target);samples=[metrics(permuted(lines,rng),actual) for _ in range(TEST_NULL)];nm={k:statistics.mean(float(q[k]) for q in samples) for k in samples[0]};nm['target']=target;null.append(nm)
   for k in diffs:diffs[k].append(float(om[k])-nm[k])
  update(cats,actual,unary,pair,exact,maskstat);d=draws[idx]
  for n in d['nums']:freq[n-1]+=1;last[n-1]=d['round']
  pc.update(itertools.combinations(d['nums'],2));tc.update(itertools.combinations(d['nums'],3));pr=b.structure_profile(d['nums'],draws[idx-1]['nums'])
  for i,v in enumerate(pr):profiles[i][v]+=1
 keys=['max_hits','any2','any3','any4','any5','any6','winning_union_coverage','union_size','mean_overlap','max_overlap'];score={'policy':{k:avg(obs,k) for k in keys},'matched_label_permutation':{k:avg(null,k) for k in keys}};score['delta']={k:score['policy'][k]-score['matched_label_permutation'][k] for k in keys};alpha=.05/4;inf={}
 for j,k in enumerate(diffs):inf[k]={'adjusted_ci_delta':ci(diffs[k],alpha,SEED+500+j),'positive_50_round_block_share':posshare(diffs[k])}
 inf['strict_portfolio_pass']=(inf['max_hits']['adjusted_ci_delta'][0]>0 and inf['any2']['adjusted_ci_delta'][0]>0 and inf['any3']['adjusted_ci_delta'][0]>0 and inf['any2']['positive_50_round_block_share']>=.65)
 payload={'created_kst':datetime.now(KST).isoformat(),'target_round':1247,'data_cutoff':1246,'policy':'HIERARCHICAL_DISCRETIZED_RAW_SIGNAL_BAYES_V17','no_future_leakage':True,'roles':ROLES,'feature_bins':'cross-sectional quartiles each target for freq/gap/recent/momentum/pair/triple; vote-count, support-mask, previous-member and adjacency categories','note':'All categorical posterior counts are updated only after the target resolves. Five lines are separately optimized from five learned role scores; strong-number repetition is allowed. Strict outer gate and matched joint label-permutation comparator unchanged.','current':current,'walkforward_targets':len(obs),'scorecard':score,'inference':inf,'final_status':'STRICT_PASS' if inf['strict_portfolio_pass'] else 'FAIL_SAME_GATE'};OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':'PASS','strict_pass':inf['strict_portfolio_pass'],'scorecard':score,'inference':inf,'current':{'lines':current['lines'],'roles':current['roles'],'top_by_role':current['top_by_role']}},ensure_ascii=False))
if __name__=='__main__':main()
