"""Study batch 001: preregistered family-diverse lottery experiments.

Reads rounds 1..1244 only and writes exclusively to this new batch directory.
All hypotheses are post-hoc to the wider project review, hence never promoted
as predictive evidence without prospective validation.
"""
from __future__ import annotations
import csv, math, random, statistics, hashlib
from collections import Counter
from itertools import combinations
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
FRAMEWORK=HERE.parents[1]
ROOT=HERE.parents[3]
sys.path.insert(0,str(FRAMEWORK))
from walkforward_core import load_draws_through, exact_random_baseline
DATA=Path(r"C:\Users\user\Documents\Codex\2026-10-06\cloud-x20\work\lotto-data\lotto_data.csv")
OLD=Path(r"C:\Users\user\Documents\Codex\2026-10-06\cloud-x20\outputs")
MODELS=[
('S001','multi_window_frequency','multi_window_frequency','sum of per-window standardized rates: last 10/30/100/300; equal window weights; top six, ties lower number'),
('S002','gap_regime_hazard','gap_time','empirical next-occurrence rate by current age regime [0,1,2,3-5,6-10,11+], Beta(20, prior 6/45) shrinkage; top six'),
('S003','momentum_state_transition','momentum','smoothed P(number next | hot/cold transition from prior20 to recent20), pooled only from historical transitions; top six'),
('S004','conditional_probability','conditional','per-number Beta(30, prior 6/45) probability conditioned on its count in trailing 10 draws; top six'),
('S005','structure_transition','structure_transition','fixed candidate bank seed=20261008,size=5000; Laplace-smoothed marginal log likelihood of target structure given previous-round structure; lexical bank tie-break'),
('S006','pair_residual_node','pair_relation_residual','sum over number partners of standardized pair residual O-E, E conditional on single-number marginals; top six'),
('S007','triple_residual_node','triple_relation_residual','sum over triples containing number of standardized triple residual O-E, E conditional on single-number marginals; top six'),
('S008','family_balanced_hybrid','hybrid','equal rank blend of S001-S007 family scores; deterministic lower-number tie-break; shared inputs acknowledged'),
]
BASE=exact_random_baseline()
def source_prefix_sha256(path, through_round=1244):
    """Hash header and exactly the first requested data rows; never consume later rows."""
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for _ in range(through_round+1):
            line=stream.readline()
            if not line: raise ValueError('Raw CSV ended before requested hash cutoff')
            digest.update(line)
    return digest.hexdigest()
def write(name,rows):
 if not rows: raise ValueError('Refusing empty output '+name)
 # This batch directory is reserved for these run products; old project files are outside it.
 with (HERE/name).open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def top(score): return tuple(sorted(sorted(range(1,46),key=lambda x:(-score[x-1],x))[:6]))
def rank(score):
 order=sorted(range(45),key=lambda i:(-score[i],i)); out=[0.]*45
 for j,i in enumerate(order):out[i]=45-j
 return out
def prof(ns,prev=()):
 gaps=[b-a for a,b in zip(ns,ns[1:])]
 bands=tuple(sum(lo<=v<=hi for v in ns) for lo,hi in [(1,10),(11,20),(21,30),(31,40),(41,45)])
 endings=Counter(v%10 for v in ns)
 clusters=1+sum(g>5 for g in gaps)
 return {'odd':sum(v%2 for v in ns),'low':sum(v<=22 for v in ns),'sum_bin':sum(ns)//30,'bands':bands,'consecutive':sum(g==1 for g in gaps),'end_repeat':sum(v-1 for v in endings.values() if v>1),'overlap':len(set(ns)&set(prev)),'cluster':clusters}
def candidate_bank():
 rng=random.Random(20261008);seen=set()
 while len(seen)<5000:seen.add(tuple(sorted(rng.sample(range(1,46),6))))
 return sorted(seen)
def make_models(train,bank):
 n=len(train); F=Counter(x for d in train for x in d.numbers); den=max(n,1); p=6/45
 occ={x:[d.round for d in train if x in d.numbers] for x in range(1,46)}
 gaps={x:(train[-1].round-occ[x][-1] if occ[x] else n) for x in range(1,46)}
 # Multi-window frequency rates standardized to each window's theoretical mean/SD.
 s1=[]
 for x in range(1,46):
  vals=[]
  for w in (10,30,100,300):
   ww=min(w,n); c=sum(x in d.numbers for d in train[-ww:]);mu=ww*p;sd=max(math.sqrt(ww*p*(1-p)),1e-9);vals.append((c-mu)/sd)
  s1.append(sum(vals)/4)
 # Gap regime occurrence hazard estimated from completed historical inter-arrivals.
 bins=lambda z: 0 if z==0 else 1 if z==1 else 2 if z==2 else 3 if z<=5 else 4 if z<=10 else 5
 risk=Counter();hits=Counter()
 for x in range(1,46):
  seq=occ[x]
  for a,b in zip(seq,seq[1:]):
   g=b-a
   for age in range(0,g):risk[bins(age)]+=1
   hits[bins(g)]+=1
 # Simplified hazard as interval termination by age-bin; shrink each rate to baseline.
 s2=[]
 for x in range(1,46):
  j=bins(gaps[x]);s2.append((hits[j]+20*p)/(risk[j]+20))
 # Hot/cold transition state counts, forward next-draw only.
 trans=Counter(); trans_hit=Counter()
 for i in range(40,n):
  prev20=Counter(z for d in train[i-40:i-20] for z in d.numbers); curr20=Counter(z for d in train[i-20:i] for z in d.numbers)
  for x in range(1,46):
   st=('H' if prev20[x]>20*p else 'C','H' if curr20[x]>20*p else 'C');trans[st]+=1
   if x in train[i].numbers:trans_hit[st]+=1
 prev20=Counter(z for d in train[-40:-20] for z in d.numbers) if n>=40 else Counter()
 curr20=Counter(z for d in train[-20:] for z in d.numbers)
 s3=[]
 for x in range(1,46):
  st=('H' if prev20[x]>20*p else 'C','H' if curr20[x]>20*p else 'C');s3.append((trans_hit[st]+20*p)/(trans[st]+20))
 # Conditional rate based on how many appearances in latest ten draws.
 cond=Counter();cond_hit=Counter()
 for i in range(10,n):
  prev=train[i-10:i]
  for x in range(1,46):
   state=sum(x in d.numbers for d in prev);cond[state]+=1
   if x in train[i].numbers:cond_hit[state]+=1
 s4=[]
 for x in range(1,46):
  state=sum(x in d.numbers for d in train[-10:]);s4.append((cond_hit[state]+30*p)/(cond[state]+30))
 # Structure transitions: categories from previous draw -> next draw's feature.
 cats=['odd','low','sum_bin','bands','consecutive','end_repeat','overlap','cluster'];
 prevprof=[prof(train[i-1].numbers,train[i-2].numbers if i>1 else ()) for i in range(1,n)]
 nextprof=[prof(train[i].numbers,train[i-1].numbers) for i in range(1,n)]
 trans_counts=[Counter() for _ in cats]; marg=[Counter() for _ in cats]; ntrans=max(0,n-1)
 for a,b in zip(prevprof,nextprof):
  for j,c in enumerate(cats):trans_counts[j][(a[c],b[c])]+=1;marg[j][b[c]]+=1
 latest=prof(train[-1].numbers,train[-2].numbers if n>1 else ())
 # finite, explicitly fixed random candidate bank; smooth transition likelihood
 structural=[]
 denominators=[]
 logmaps=[]
 for j,c in enumerate(cats):
  denominators.append(sum(v for (a,_),v in trans_counts[j].items() if a==latest[c]))
  possible=set(marg[j])|{BASE_PROFILES[q][c] for q in bank}
  if c=='overlap':possible.update(range(7))
  choices=max(1,len(possible))
  logmaps.append({v:math.log((trans_counts[j][(latest[c],v)]+1)/(denominators[j]+choices)) for v in possible})
 for ticket in bank:
  target=BASE_PROFILES[ticket].copy();target['overlap']=len(set(ticket)&set(train[-1].numbers))
  sc=sum(logmaps[j][target[c]] for j,c in enumerate(cats))
  structural.append((sc,ticket))
 s5ticket=max(structural,key=lambda z:(z[0],tuple(-x for x in z[1])))[1]
 # Pair and triple residuals; fixed marginals, no target data.
 pc=Counter();tc=Counter()
 for d in train:
  pc.update(combinations(d.numbers,2));tc.update(combinations(d.numbers,3))
 s6=[0.]*45;s7=[0.]*45
 for a,b in combinations(range(1,46),2):
  exp=max((5/6)*(45/44)*F[a]*F[b]/den,1e-12);z=(pc[(a,b)]-exp)/math.sqrt(exp);s6[a-1]+=z;s6[b-1]+=z
 for a,b,c in combinations(range(1,46),3):
  factor=(5*4/(6**2))*(45**2/(44*43));exp=max(factor*F[a]*F[b]*F[c]/(den**2),1e-12);z=(tc[(a,b,c)]-exp)/math.sqrt(exp);s7[a-1]+=z;s7[b-1]+=z;s7[c-1]+=z
 component=[s1,s2,s3,s4,s6,s7]
 # Hybrid averages within-family percentile ranks; structure ticket contributes a separate one-vote family.
 ranks=[rank(v) for v in component];
 for x in range(1,46):
  if x in s5ticket:ranks.append([45.]*45)
  else:ranks.append([0.]*45)
 s8=[sum(v[i] for v in ranks)/len(ranks) for i in range(45)]
 return {'multi_window_frequency':(top(s1),s1),'gap_regime_hazard':(top(s2),s2),'momentum_state_transition':(top(s3),s3),'conditional_probability':(top(s4),s4),'structure_transition':(s5ticket,[45. if i+1 in s5ticket else 0. for i in range(45)]),'pair_residual_node':(top(s6),s6),'triple_residual_node':(top(s7),s7),'family_balanced_hybrid':(top(s8),s8)}
def stats(h):
 n=len(h);c=Counter(h);mean=statistics.mean(h) if h else 0;var=statistics.pvariance(h) if h else 0
 return {'n':n,'mean_hits':mean,'variance_hits_population':var,**{f'hits_{i}_count':c[i] for i in range(7)},**{f'rate_ge_{i}':sum(x>=i for x in h)/n if n else 0 for i in range(2,6)},'rate_exact_6':sum(x==6 for x in h)/n if n else 0,'baseline_mean_hits':BASE['mean_hits'],'baseline_rate_ge_2':BASE['rate_ge_2'],'baseline_rate_ge_3':BASE['rate_ge_3'],'baseline_rate_ge_4':BASE['rate_ge_4'],'baseline_rate_ge_5':BASE['rate_ge_5'],'baseline_rate_exact_6':BASE['rate_exact_6'],'delta_mean_vs_random':mean-BASE['mean_hits'],'delta_rate_ge_2_vs_random':(sum(x>=2 for x in h)/n-BASE['rate_ge_2']) if n else 0}
def main():
 draws=load_draws_through(DATA,1244)
 # Confirm the registry template has no already evaluated batch hypotheses.
 reg_path=FRAMEWORK/'research_registry.csv'
 with reg_path.open(newline='',encoding='utf-8-sig') as f: prior=list(csv.DictReader(f))
 registered={r.get('research_id','') for r in prior if r.get('research_id')}
 dup=[m[0] for m in MODELS if m[0] in registered]
 if dup:raise ValueError(f'Research IDs already registered: {dup}')
 bank=candidate_bank();
 global BASE_PROFILES
 BASE_PROFILES={q:prof(q,()) for q in bank}
 rows=[]; score_memory={}
 for target in range(201,1245):
  train=draws[:target-1];actual=set(draws[target-1].numbers)
  predictions=make_models(train,bank)
  for mid,name,family,rule in MODELS:
   ticket,scores=predictions[name];hits=len(set(ticket)&actual)
   rows.append({'research_id':mid,'model':name,'model_family':family,'target_round':target,'training_start_round':1,'training_through_round':target-1,'window_mode':'expanding','predicted_numbers':' '.join(map(str,ticket)),'actual_numbers':' '.join(map(str,sorted(actual))),'hits':hits})
   score_memory.setdefault((name,target),scores)
 write('walkforward_predictions.csv',rows)
 # Aggregate metrics windows fixed before viewing results.
 windows={'overall_201_1244':(201,1244),'recent200':(1045,1244),'recent100':(1145,1244),'recent50':(1195,1244),'block_201_500':(201,500),'block_501_800':(501,800),'block_801_1100':(801,1100),'block_1101_1244':(1101,1244)}
 metrics=[]
 for mid,name,fam,rule in MODELS:
  for wn,(lo,hi) in windows.items():
   h=[int(r['hits']) for r in rows if r['model']==name and lo<=int(r['target_round'])<=hi]
   metrics.append({'research_id':mid,'model':name,'family':fam,'window':wn,**stats(h),'classification':'POST_HOC_ONLY / VALIDATION_REQUIRED'})
 write('model_metrics.csv',metrics)
 # Register all hypotheses before claiming outcomes; full methods included.
 regrows=[]
 for mid,name,fam,rule in MODELS:
  overall=next(r for r in metrics if r['model']==name and r['window']=='overall_201_1244'); recent=next(r for r in metrics if r['model']==name and r['window']=='recent100'); hold=next(r for r in metrics if r['model']==name and r['window']=='recent50')
  status='HOLD' if overall['delta_mean_vs_random']>0 and recent['delta_mean_vs_random']>0 and hold['delta_mean_vs_random']>0 else 'WEAK'
  regrows.append({'research_id':mid,'status':status,'hypothesis':f'{name} improves ticket hits using {fam} signals','model_family':fam,'independence_group':fam,'data_path':str(DATA),'data_sha256':source_prefix_sha256(DATA,1244),'round_range':'1-1244','features':rule,'calculation_method':rule,'train_cutoff_rule':'each target t receives rounds 1..t-1 only','validation_method':'expanding 1-step walk-forward','validation_rounds':'201-1244','holdout_rounds':'recent200/recent100/recent50 (all post-hoc, not untouched)','random_baseline':'exact hypergeometric C(6,k)C(39,6-k)/C(45,6)','baseline_mean_hits':BASE['mean_hits'],'baseline_rate_ge_2':BASE['rate_ge_2'],'baseline_rate_ge_3':BASE['rate_ge_3'],'baseline_rate_ge_4':BASE['rate_ge_4'],'baseline_rate_ge_5':BASE['rate_ge_5'],'baseline_rate_exact_6':BASE['rate_exact_6'],'n_predictions':overall['n'],'mean_hits':overall['mean_hits'],'variance_hits_population':overall['variance_hits_population'],'rate_ge_2':overall['rate_ge_2'],'rate_ge_3':overall['rate_ge_3'],'rate_ge_4':overall['rate_ge_4'],'rate_ge_5':overall['rate_ge_5'],'rate_exact_6':overall['rate_exact_6'],'recent_window_metrics':json_compact(recent),'holdout_metrics':json_compact(hold),'failure_segments':'See model_metrics.csv chronological blocks','multiple_testing_notes':'8 models, many windows and exploratory diagnostics; no multiplicity correction','selection_bias_notes':'POST_HOC_ONLY; model family selection after project review','overfit_risk':'HIGH','model_correlation_notes':'See model_correlation.csv; all share draw history','independent_validation':'No prospective untouched draw','conclusion':status,'next_research_direction':'Pre-register and test on future rounds; refine only after holdout','artifact_paths':'walkforward_predictions.csv;model_metrics.csv','created_at':'2026-10-08','revision_of':''})
 write('study_registry.csv',regrows)
 # Correlation and overlap vs B-v1 controls; original file read only.
 corr=[]
 for a,b in combinations([m[1] for m in MODELS],2):
  ra={int(r['target_round']):r for r in rows if r['model']==a};rb={int(r['target_round']):r for r in rows if r['model']==b};common=sorted(set(ra)&set(rb));ov=[];ha=[];hb=[]
  for t in common:ov.append(len(set(map(int,ra[t]['predicted_numbers'].split()))&set(map(int,rb[t]['predicted_numbers'].split()))));ha.append(int(ra[t]['hits']));hb.append(int(rb[t]['hits']))
  hc=statistics.correlation(ha,hb) if len(set(ha))>1 and len(set(hb))>1 else ''
  # Score correlation on the latest common target, for comparability without pooling scales.
  sa=score_memory[(a,1244)];sb=score_memory[(b,1244)];sc=statistics.correlation(sa,sb) if len(set(sa))>1 and len(set(sb))>1 else ''
  corr.append({'model_a':a,'model_b':b,'n':len(common),'mean_ticket_overlap':statistics.mean(ov),'mean_jaccard':statistics.mean(v/(12-v) if v<6 else 1 for v in ov),'hit_correlation':hc,'score_correlation_latest_round':sc})
 write('model_correlation.csv',corr)
 # Failures explicitly retained; classification never PROMISING from a single historical run.
 failures=[]
 for mid,name,fam,rule in MODELS:
  overall=next(r for r in metrics if r['model']==name and r['window']=='overall_201_1244')
  for wn in ['overall_201_1244','recent200','recent100','recent50','block_201_500','block_501_800','block_801_1100','block_1101_1244']:
   z=next(r for r in metrics if r['model']==name and r['window']==wn)
   failures.append({'research_id':mid,'model':name,'window':wn,'status':'WEAK' if z['delta_mean_vs_random']<=0 else 'HOLD','mean_hits':z['mean_hits'],'baseline_mean':BASE['mean_hits'],'mean_delta':z['delta_mean_vs_random'],'rate_ge2':z['rate_ge_2'],'baseline_rate_ge2':BASE['rate_ge_2'],'rate_ge2_delta':z['delta_rate_ge_2_vs_random'],'interpretation':'Historical descriptive result only; not evidence of predictive edge'})
 write('failure_registry.csv',failures)
 # Conservative survivor list: no promotions until prospective untouched validation.
 write('surviving_models.csv',[{'research_id':m[0],'model':m[1],'status':'NONE_PROMOTED','reason':'Post-hoc historical scan; require independent prospective validation'} for m in MODELS])
 report(metrics,rows,regrows,corr,failures)
 print(f'OK rounds={len(draws)} predictions={len(rows)} models={len(MODELS)} experiments={len(MODELS)} baseline_mean={BASE["mean_hits"]:.6f} output={HERE}')
def json_compact(r):return json.dumps({k:r[k] for k in ['n','mean_hits','rate_ge_2','rate_ge_3','rate_ge_4','rate_ge_5','rate_exact_6','delta_mean_vs_random','delta_rate_ge_2_vs_random']},ensure_ascii=False)
def report(metrics,rows,regs,corr,failures):
 overall=[r for r in metrics if r['window']=='overall_201_1244'];overall.sort(key=lambda r:(-r['mean_hits'],-r['rate_ge_2']))
 blocks=[r for r in metrics if r['window'].startswith('block_')]
 lines=['# Study Batch 001 — 신규 모델 walk-forward 연구','',f'- 데이터: `{DATA}` (1~1244회, 전량 연속성 검증; 입력 loader가 1244회까지만 읽음)','- 예측 평가: 목표 201~1244, expanding 1-step-ahead, 각 t는 1~t-1만 학습에 전달.','- 가설/실험 수: 8 / 8; 신규 모델 계열: 8; 신규 변수군: 8; 모델당 1,044 predictions; 총 walk-forward predictions: %s.'%len(rows),'- 전체 평가 회차: 1,044 unique targets. 실패(전체 평균이 random 이하) %d; HOLD(전체 평균 초과) %d; PROMISING 0.'%(sum(r['mean_hits']<=BASE['mean_hits'] for r in overall),sum(r['mean_hits']>BASE['mean_hits'] for r in overall)),'- 모든 연구는 이번 프로젝트 기존 결과 확인 후 설계된 사후 연구로 `POST_HOC_ONLY`; holdout은 untouched가 아닙니다.','', '## 기존 연구와 중복 점검','', '기존 `research_registry.csv`는 템플릿(기등록 평가 가설 없음)이었고 `model_family_catalog.csv`의 8개 B모델 계열을 확인했습니다. 신규 8개는 multi-window frequency, gap regime hazard, momentum state transition, conditional probability, structure transition, pair residual, triple residual, family-balanced hybrid입니다. 원시 빈도·관계 신호를 재사용하므로 완전히 독립적인 증거라고 보지 않습니다.','', '## 모델별 성능','', '| 순위 | 모델 | 평균 | 2+ | 3+ | 4+ | 5+ | 6 | Δ 평균 | Δ 2+ |','|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|']
 for i,r in enumerate(overall,1):lines.append(f"| {i} | {r['model']} | {r['mean_hits']:.4f} | {r['rate_ge_2']:.2%} | {r['rate_ge_3']:.2%} | {r['rate_ge_4']:.2%} | {r['rate_ge_5']:.2%} | {r['rate_exact_6']:.2%} | {r['delta_mean_vs_random']:+.4f} | {r['delta_rate_ge_2_vs_random']:+.2%} |")
 lines += ['',f"정확 균등 무작위 기준선: 평균 {BASE['mean_hits']:.6f}, 2+ {BASE['rate_ge_2']:.4%}, 3+ {BASE['rate_ge_3']:.4%}, 4+ {BASE['rate_ge_4']:.4%}, 5+ {BASE['rate_ge_5']:.4%}, 6 {BASE['rate_exact_6']:.6%}.",'','## 최근 구간 및 chronological blocks','','`model_metrics.csv`에 overall, recent 200/100/50, 그리고 네 chronological block의 모든 지표가 있습니다. Holdout 구간은 연구 후 선택한 최근 관점이므로 독립 검증이 아닙니다.','', '| 모델 | 구간 | n | 평균 | 2+ | 평균 차이 |','|---|---|---:|---:|---:|---:|']
 for r in metrics:
  if r['window'] in ['recent200','recent100','recent50']:lines.append(f"| {r['model']} | {r['window']} | {r['n']} | {r['mean_hits']:.4f} | {r['rate_ge_2']:.2%} | {r['delta_mean_vs_random']:+.4f} |")
 lines += ['', '## 질문별 답변','','1. 새로운 정보: 후보 정의상 다른 시간창 결합·전이·조건부 hazard·구조전이 특징을 시험했지만, 이 자료에서 B-v1보다 독립적인 예측 정보가 확인됐다고 결론 내릴 수 없습니다.','2. Random 초과: 전체 평균이나 2+가 초과한 모델이 있을 수 있으나 8개 동시 탐색과 과거 결과 확인 후 설계된 post-hoc이므로 반복 가능한 신호로 인정하지 않았습니다.','3. 최근 유지: recent50/100/200 결과가 모델별로 기록되어 있으며 구간 간 방향이 일치하지 않는 경우 안정적이라고 보지 않습니다.','4. Holdout 유지: untouched holdout은 이번 데이터 안에 남겨두지 않았습니다. 최근 구간은 가설 구성 후 살핀 사후 holdout입니다.','5. B-v1 독립성: ticket overlap/hit correlation 및 마지막 회차 score correlation을 `model_correlation.csv`에 기록했습니다. 주파수, gap, momentum, pair/triple 및 hybrid는 입력 정보가 공유됩니다.','6. 과적합/우연: recent windows, 여러 변형, 다중 pair/triple 탐색, 불균형 구조 전이, 반복된 조건 검색이 selection bias를 유발할 수 있습니다. PROMISING은 0입니다.','7. 다음 연구: 이번 정의를 사전등록된 고정 규칙으로 동결하고 신규 회차가 추가된 뒤 untouched prospective 평가를 수행합니다. 조건부/구조 모델은 표본수를 늘리고 calibration을 검토합니다.','', '## 실패 및 다음 단계','', '모든 모델과 구간의 분류는 `failure_registry.csv`에 저장했습니다. 전체 random 이하 모델은 WEAK, 초과 모델도 HOLD에 머물며 생존 승격은 없습니다. 1245회 추천번호 또는 최종 구매번호는 생성하지 않았습니다.','']
 (HERE/'STUDY_BATCH_001_REPORT.md').open('w',encoding='utf-8').write('\n'.join(lines))
if __name__=='__main__':
 import json
 main()
