#!/usr/bin/env python3
from __future__ import annotations
import csv,importlib.util,itertools,json,random,statistics,math
from collections import Counter,deque
from datetime import datetime,timezone,timedelta
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'lotto_data.csv';B_SOURCE=ROOT/'research/1245_final_pipeline_v3/recovered_original_assets/b_model_backtest.py';AC_SOURCE=ROOT/'automation/recovered_models_v2.py';V12_SOURCE=ROOT/'automation/today_raw_signal_meta_v12.py';V18_SOURCE=ROOT/'automation/today_interaction_adagrad_v18.py'
OUT=ROOT/'analysis/2026-10-30/TODAY_MULTIWINDOW_RANK_1248_V30.json';KST=timezone(timedelta(hours=9))
TEST_NULL=240;BLOCK=50;BOOT=7000;SEED=202610300900;ROLL=150;LR=.035;L2=.0025
CFG={'slow':(1.0,1.0),'medium':(.9995,.999),'fast':(.9975,.992)}
EXTRA_NAMES=('recent10','recent30','recent100','mom10_30','mom30_100','balanced')
def imp(p,n):s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def load():
 o=[]
 with DATA.open(encoding='utf-8-sig') as f:
  for r in csv.DictReader(f):o.append({'round':int(r['round']),'nums':tuple(sorted(int(r[f'no{i}']) for i in range(1,7)))})
 assert o[-1]['round']==1247 and [x['round'] for x in o]==list(range(1,1248));return o
def z(v):
 m=statistics.mean(v);s=statistics.pstdev(v) or 1.0;return [(x-m)/s for x in v]
def extras(draws,idx,freq):
 vals={w:[0]*45 for w in (10,30,100)}
 for w in vals:
  for d in draws[max(0,idx-w):idx]:
   for n in d['nums']:vals[w][n-1]+=1
 z10,z30,z100=map(z,(vals[10],vals[30],vals[100]));zf=z([float(x) for x in freq])
 m1030=z([vals[10][i]/max(1,min(10,idx))-vals[30][i]/max(1,min(30,idx)) for i in range(45)])
 m30100=z([vals[30][i]/max(1,min(30,idx))-vals[100][i]/max(1,min(100,idx)) for i in range(45)])
 bal=z([(zf[i]+z30[i]+m30100[i])/3 for i in range(45)])
 return {n:[z10[n-1],z30[n-1],z100[n-1],m1030[n-1],m30100[n-1],bal[n-1]] for n in range(1,46)}
def design(v18,base,ex):
 out=list(v18.design(base));out+=list(ex);out += [q*q for q in ex];out += [ex[i]*ex[j] for i in range(len(ex)) for j in range(i+1,len(ex))];vote_share=base[12];out += [vote_share*q for q in ex];return out
def predict(v18,X,E,w):return {n:sum(a*b for a,b in zip(w,design(v18,X[n],E[n]))) for n in X}
def update(v18,X,E,w,g2,actual,shrink,gdec):
 grad=[0.0]*len(w)
 for n in range(1,46):
  f=design(v18,X[n],E[n]);y=1.0 if n in actual else 0.0;p=v18.sigmoid(sum(a*b for a,b in zip(w,f)))
  for j,x in enumerate(f):grad[j]+=(p-y)*x
 for j in range(len(w)):
  if j>0:w[j]*=shrink
  gr=grad[j]/45.0+(0 if j==0 else L2*w[j]);g2[j]=gdec*g2[j]+gr*gr;w[j]-=LR*gr/math.sqrt(g2[j]+1e-8)
 return w,g2
def zscore(sc):
 vals=list(sc.values());m=statistics.mean(vals);s=statistics.pstdev(vals) or 1.0;return {n:(v-m)/s for n,v in sc.items()}
def ranked_hybrid(slow,blend):
 core=sorted(range(1,46),key=lambda n:(-slow[n],n))[:6];tail=sorted((n for n in range(1,46) if n not in core),key=lambda n:(-blend[n],n))[:24];return core+tail
def tails():
 return {'rr':[[6,10,14,18,22,26],[7,11,15,19,23,27],[8,12,16,20,24,28],[9,13,17,21,25,29]],'contig':[[6,7,8,9,10,11],[12,13,14,15,16,17],[18,19,20,21,22,23],[24,25,26,27,28,29]],'snake':[[6,13,14,21,22,29],[7,12,15,20,23,28],[8,11,16,19,24,27],[9,10,17,18,25,26]],'paired':[[6,7,14,15,22,23],[8,9,16,17,24,25],[10,11,18,19,26,27],[12,13,20,21,28,29]]}
def lines(r,t):return [tuple(sorted(r[:6]))]+[tuple(sorted(r[j] for j in p)) for p in t]
def met(L,a):
 h=[len(set(x)&a) for x in L];u=set().union(*map(set,L));return {'max_hits':max(h),'any2':int(max(h)>=2),'any3':int(max(h)>=3),'any4':int(max(h)>=4),'winning_union_coverage':len(u&a),'union_size':len(u)}
def perm(L,rng):
 labs=list(range(1,46));sh=labs[:];rng.shuffle(sh);mp=dict(zip(labs,sh));return [tuple(sorted(mp[n] for n in x)) for x in L]
def obj(h):
 if not h:return -999
 x=list(h)[-ROLL:];return statistics.mean(q['max_hits']+.85*q['any2']+1.35*q['any3'] for q in x)
def avg(rows,k):return statistics.mean(float(x[k]) for x in rows)
def ci(v,alpha,seed):
 blocks=[v[i:i+BLOCK] for i in range(0,len(v),BLOCK)];rng=random.Random(seed);re=[]
 for _ in range(BOOT):
  flat=[]
  for __ in range(len(blocks)):flat+=blocks[rng.randrange(len(blocks))]
  re.append(statistics.mean(flat))
 re.sort();return [re[int(alpha/2*(len(re)-1))],re[int((1-alpha/2)*(len(re)-1))]]
def share(v):
 b=[statistics.mean(v[i:i+BLOCK]) for i in range(0,len(v),BLOCK)];return sum(x>0 for x in b)/len(b),b
def main():
 OUT.parent.mkdir(parents=True,exist_ok=True);draws=load();b=imp(B_SOURCE,'bv30');ac=imp(AC_SOURCE,'acv30');v12=imp(V12_SOURCE,'v12v30');v18=imp(V18_SOURCE,'v18v30');bank=b.feature_structure_bank(b.make_structure_bank());freq=[0]*45;last=[0]*45;pc=Counter();tc=Counter();prof=[Counter() for _ in range(6)]
 for d in draws[:200]:
  for n in d['nums']:freq[n-1]+=1;last[n-1]=d['round']
  pc.update(itertools.combinations(d['nums'],2));tc.update(itertools.combinations(d['nums'],3));pr=b.structure_profile(d['nums'],None)
  for i,v in enumerate(pr[:5]):prof[i][v]+=1
 for i in range(1,200):prof[5][b.structure_profile(draws[i]['nums'],draws[i-1]['nums'])[5]]+=1
 dummyX={n:[0.0]*23 for n in range(1,46)};dummyE={n:[0.0]*6 for n in range(1,46)};dim=len(design(v18,dummyX[1],dummyE[1]));p0=6/45;states={k:{'w':[math.log(p0/(1-p0))]+[0.0]*(dim-1),'g2':[0.0]*dim} for k in CFG};T=tails();hist={k:deque(maxlen=ROLL) for k in T};obs=[];nul=[];diff={k:[] for k in ('max_hits','any2','any3','winning_union_coverage')};count=Counter();current=None
 for idx in range(200,len(draws)+1):
  preds={**b.predictions_for_round(draws,idx,freq,last,pc,tc,prof,bank),**ac.predict([q['nums'] for q in draws[:idx]])};X=v12.raw_features(draws,idx,freq,last,pc,tc,preds);E=extras(draws,idx,freq);scores={k:predict(v18,X,E,s['w']) for k,s in states.items()};zs={k:zscore(v) for k,v in scores.items()};blend={n:sum(zs[k][n] for k in CFG)/len(CFG) for n in range(1,46)};r=ranked_hybrid(scores['slow'],blend);allL={k:lines(r,p) for k,p in T.items()};chosen='rr' if idx<320 else max(T,key=lambda k:(obj(hist[k]),k));L=allL[chosen]
  if idx==len(draws):current={'template':chosen,'template_scores':{k:obj(hist[k]) for k in T},'lines':[list(x) for x in L],'top6_slow_core':r[:6],'hybrid_top30':r};break
  actual=set(draws[idx]['nums']);target=idx+1
  for k,Q in allL.items():hist[k].append(met(Q,actual))
  if target>=401:
   count[chosen]+=1;om=met(L,actual);obs.append(om);rng=random.Random(SEED+target);sm=[met(perm(L,rng),actual) for _ in range(TEST_NULL)];nm={k:statistics.mean(float(q[k]) for q in sm) for k in sm[0]};nul.append(nm)
   for k in diff:diff[k].append(float(om[k])-nm[k])
  for k,(sh,gd) in CFG.items():states[k]['w'],states[k]['g2']=update(v18,X,E,states[k]['w'],states[k]['g2'],actual,sh,gd)
  d=draws[idx]
  for n in d['nums']:freq[n-1]+=1;last[n-1]=d['round']
  pc.update(itertools.combinations(d['nums'],2));tc.update(itertools.combinations(d['nums'],3));pr=b.structure_profile(d['nums'],draws[idx-1]['nums'])
  for i,v in enumerate(pr):prof[i][v]+=1
 keys=['max_hits','any2','any3','any4','winning_union_coverage','union_size'];score={'policy':{k:avg(obs,k) for k in keys},'matched_label_permutation':{k:avg(nul,k) for k in keys}};score['delta']={k:score['policy'][k]-score['matched_label_permutation'][k] for k in keys};alpha=.05/4;inf={}
 for j,k in enumerate(diff):
  s,bk=share(diff[k]);inf[k]={'adjusted_ci_delta':ci(diff[k],alpha,SEED+50+j),'positive_50_round_block_share':s,'block_deltas':bk}
 inf['strict_portfolio_pass']=inf['max_hits']['adjusted_ci_delta'][0]>0 and inf['any2']['adjusted_ci_delta'][0]>0 and inf['any3']['adjusted_ci_delta'][0]>0 and inf['any2']['positive_50_round_block_share']>=.65
 payload={'created_kst':datetime.now(KST).isoformat(),'target_round':1248,'data_cutoff':1247,'policy':'MULTIWINDOW_INTERACTION_HYBRID_V30','no_future_leakage':True,'extra_signals':list(EXTRA_NAMES),'feature_count':dim,'selection_rule':'V26 slow-core/blended-tail framework with added cutoff-safe recent10/recent30/recent100, 10v30 and 30v100 momentum, and balanced composite features learned online. Tail template uses prior rolling150 only. Strict gate unchanged.','template_selection_counts':dict(count),'current':current,'walkforward_targets':len(obs),'scorecard':score,'inference':inf,'final_status':'STRICT_PASS' if inf['strict_portfolio_pass'] else 'FAIL_SAME_GATE'};OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'strict_pass':inf['strict_portfolio_pass'],'scorecard':score,'current':current,'inference':{k:{'adjusted_ci_delta':v['adjusted_ci_delta'],'positive_50_round_block_share':v['positive_50_round_block_share']} for k,v in inf.items() if isinstance(v,dict)}},ensure_ascii=False))
if __name__=='__main__':main()
