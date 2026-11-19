#!/usr/bin/env python3
from __future__ import annotations
import csv, importlib.util, itertools, json, random, statistics
from collections import Counter, deque
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'lotto_data.csv'
B_SOURCE=ROOT/'research/1245_final_pipeline_v3/recovered_original_assets/b_model_backtest.py'
AC_SOURCE=ROOT/'automation/recovered_models_v2.py'
OUT=ROOT/'analysis/2026-10-23/TODAY_ADAPTIVE_EXPERTS_1247_V9.json'
KST=timezone(timedelta(hours=9))
B_NAMES=('long_frequency','current_gap','frequency_plus_gap','recent_momentum','structure_profile','pair_association','triple_association','combined_equal_rank')
AC_NAMES=('A_v2','C_v2','contrarian_v2')
MODELS=B_NAMES+AC_NAMES
ROLL=200; RANDOM_PER_TARGET=120; BLOCK=50; BOOT=4000; SEED=202610231620


def imp(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def load():
    out=[]
    with DATA.open(encoding='utf-8-sig') as f:
        for r in csv.DictReader(f): out.append({'round':int(r['round']),'nums':tuple(sorted(int(r[f'no{i}']) for i in range(1,7)))})
    assert out[-1]['round']==1246 and [x['round'] for x in out]==list(range(1,1247));return out

def rel(h):
    a=list(h)[-ROLL:]
    if not a:return 0.0
    mean=statistics.mean(a); ge2=statistics.mean(x>=2 for x in a); recent=statistics.mean(a[-50:]) if len(a)>=50 else mean
    return 0.60*mean+0.25*(2.0*ge2)+0.15*recent

def choose(preds,hists):
    scored=[]
    for m in MODELS: scored.append((rel(hists[m]),m,tuple(preds[m])))
    scored.sort(reverse=True)
    chosen=[]; used=set()
    while len(chosen)<5:
        best=None
        for s,m,t in scored:
            if t in used: continue
            ov=sum(len(set(t)&set(x[2])) for x in chosen)
            union_gain=len(set(t)-set().union(*(set(x[2]) for x in chosen))) if chosen else 6
            obj=s-0.055*ov+0.012*union_gain
            key=(obj,s,m)
            if best is None or key>best[0]: best=(key,(s,m,t))
        if best is None: break
        x=best[1]; chosen.append(x); used.add(x[2])
    assert len(chosen)==5
    return [x[2] for x in chosen],[x[1] for x in chosen],[x[0] for x in chosen]

def metrics(lines,actual):
    ss=[set(x) for x in lines];hits=[len(x&actual) for x in ss];u=set().union(*ss);ovs=[len(ss[i]&ss[j]) for i in range(5) for j in range(i+1,5)]
    return {'max_hits':max(hits),'any2':int(max(hits)>=2),'any3':int(max(hits)>=3),'any4':int(max(hits)>=4),'winning_union_coverage':len(u&actual),'union_size':len(u),'mean_overlap':statistics.mean(ovs),'max_overlap':max(ovs)}

def permuted(lines,rng):
    a=list(range(1,46));b=a[:];rng.shuffle(b);mp=dict(zip(a,b));return [tuple(sorted(mp[n] for n in row)) for row in lines]

def avg(rows,k):return statistics.mean(float(x[k]) for x in rows)
def ci(diffs,alpha,seed):
    blocks=[diffs[i:i+BLOCK] for i in range(0,len(diffs),BLOCK)];rng=random.Random(seed);reps=[]
    for _ in range(BOOT):
        bb=[blocks[rng.randrange(len(blocks))] for __ in range(len(blocks))];flat=[x for b in bb for x in b];reps.append(statistics.mean(flat))
    reps.sort();return [reps[int(alpha/2*(len(reps)-1))],reps[int((1-alpha/2)*(len(reps)-1))]]
def share(diffs):
    b=[statistics.mean(diffs[i:i+BLOCK]) for i in range(0,len(diffs),BLOCK)];return sum(x>0 for x in b)/len(b)

def main():
    draws=load();b=imp(B_SOURCE,'bv9');ac=imp(AC_SOURCE,'acv9');bank=b.feature_structure_bank(b.make_structure_bank())
    freq=[0]*45;last=[0]*45;pc=Counter();tc=Counter();prof=[Counter() for _ in range(6)]
    for d in draws[:200]:
        for x in d['nums']:freq[x-1]+=1;last[x-1]=d['round']
        pc.update(itertools.combinations(d['nums'],2));tc.update(itertools.combinations(d['nums'],3));p=b.structure_profile(d['nums'],None)
        for i,v in enumerate(p[:5]):prof[i][v]+=1
    for i in range(1,200):prof[5][b.structure_profile(draws[i]['nums'],draws[i-1]['nums'])[5]]+=1
    h={m:deque(maxlen=ROLL) for m in MODELS};obs=[];nul=[];diffs={k:[] for k in ('max_hits','any2','any3','winning_union_coverage')};cur=None;src=None;rs=None
    for idx in range(200,len(draws)+1):
        preds={**b.predictions_for_round(draws,idx,freq,last,pc,tc,prof,bank),**ac.predict([x['nums'] for x in draws[:idx]])}
        lines,sources,reliab=choose(preds,h)
        if idx==len(draws):cur=lines;src=sources;rs=reliab;break
        actual=set(draws[idx]['nums']);target=idx+1
        if target>=401:
            om=metrics(lines,actual);om['target']=target;obs.append(om);rng=random.Random(SEED+target);nr=[]
            for _ in range(RANDOM_PER_TARGET):nr.append(metrics(permuted(lines,rng),actual))
            nm={k:avg(nr,k) for k in nr[0]};nm['target']=target;nul.append(nm)
            for k in diffs:diffs[k].append(float(om[k])-nm[k])
        for m in MODELS:h[m].append(len(set(preds[m])&actual))
        d=draws[idx]
        for x in d['nums']:freq[x-1]+=1;last[x-1]=d['round']
        pc.update(itertools.combinations(d['nums'],2));tc.update(itertools.combinations(d['nums'],3));p=b.structure_profile(d['nums'],draws[idx-1]['nums'])
        for i,v in enumerate(p):prof[i][v]+=1
    keys=['max_hits','any2','any3','any4','winning_union_coverage','union_size','mean_overlap','max_overlap'];score={'policy':{k:avg(obs,k) for k in keys},'matched_label_permutation':{k:avg(nul,k) for k in keys}};score['delta']={k:score['policy'][k]-score['matched_label_permutation'][k] for k in keys}
    alpha=.05/4;inf={}
    for j,k in enumerate(diffs):inf[k]={'adjusted_ci_delta':ci(diffs[k],alpha,SEED+9000+j),'positive_50_round_block_share':share(diffs[k])}
    inf['strict_portfolio_pass']=(inf['max_hits']['adjusted_ci_delta'][0]>0 and inf['any2']['adjusted_ci_delta'][0]>0 and inf['any3']['adjusted_ci_delta'][0]>0 and inf['any2']['positive_50_round_block_share']>=.65)
    payload={'created_kst':datetime.now(KST).isoformat(),'target_round':1247,'data_cutoff':1246,'policy':'ADAPTIVE_EXPERT_SELECTION_V9','no_future_leakage':True,'selection_rule':'At each target, rank models only by prior rolling 200-round hit history; choose five distinct model tickets with fixed overlap penalty and union-gain reward.','sources':src,'source_scores':rs,'final_lines':[list(x) for x in cur],'walkforward_targets':len(obs),'random_comparator':'Joint random label permutation preserving exact five-ticket overlap structure and union size.','scorecard':score,'inference':inf,'classification':'STRICTLY_VALIDATED_RESEARCH_PORTFOLIO' if inf['strict_portfolio_pass'] else 'RESEARCH_BASED_ACTUAL_PURCHASE_CANDIDATE'}
    OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':'PASS','strict_pass':inf['strict_portfolio_pass'],'scorecard':score,'inference':inf,'sources':src,'final_lines':payload['final_lines']},ensure_ascii=False))
if __name__=='__main__':main()
