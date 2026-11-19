#!/usr/bin/env python3
from __future__ import annotations
import csv, json, math, itertools, statistics, random, hashlib, importlib.util, argparse
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'lotto_data.csv'
B_SOURCE=ROOT/'research/1245_final_pipeline_v3/recovered_original_assets/b_model_backtest.py'
WINDOWS=(10,30,50,100)
RANGES=((1,10),(11,20),(21,30),(31,40),(41,45))
MODEL_NAMES=('long_frequency','current_gap','frequency_plus_gap','recent_momentum','structure_profile','pair_association','triple_association','combined_equal_rank')


def write_csv(path, rows):
    if not rows: return
    with path.open('x',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def dump(path,obj): path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def read_validate():
    with DATA.open(encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
    exp=['round','date','no1','no2','no3','no4','no5','no6','bonus']
    if list(rows[0])!=exp: raise ValueError('unexpected columns')
    rounds=[int(r['round']) for r in rows]; errors=[]; draws=[]; bonuses=[]
    if rounds!=list(range(1,len(rows)+1)): errors.append('round sequence')
    if len(rounds)!=len(set(rounds)): errors.append('duplicate rounds')
    for r in rows:
        d=tuple(sorted(int(r[f'no{i}']) for i in range(1,7))); b=int(r['bonus'])
        if len(d)!=6 or len(set(d))!=6 or any(not 1<=x<=45 for x in d): errors.append(f"main {r['round']}")
        if not 1<=b<=45 or b in d: errors.append(f"bonus {r['round']}")
        draws.append(d); bonuses.append(b)
    if errors: raise ValueError('validation failed: '+','.join(errors[:10]))
    return rows,draws,bonuses,{'rows':len(rows),'first_round':rounds[0],'latest_round':rounds[-1],'latest_date':rows[-1]['date'],'integrity':'PASS','sha256':sha(DATA)}

def quantile(vals,q):
    s=sorted(vals); p=(len(s)-1)*q; lo=int(math.floor(p)); hi=int(math.ceil(p))
    return s[lo] if lo==hi else s[lo]*(hi-p)+s[hi]*(p-lo)

def number_analysis(draws,out):
    N=len(draws); base=6/45; full=[]; recent=[]
    for n in range(1,46):
        seen=[i+1 for i,d in enumerate(draws) if n in d]; dist=[b-a for a,b in zip(seen,seen[1:])]
        maxgap=max([seen[0]-1,*[x-1 for x in dist],N-seen[-1]]); c=len(seen)
        full.append({'number':n,'count':c,'rate':c/N,'expected_count':N*base,'delta_expected':c-N*base,'z_desc':(c-N*base)/math.sqrt(N*base*(1-base)),'last_seen':seen[-1],'current_gap':N-seen[-1],'historical_max_gap':maxgap,'mean_interappearance':statistics.mean(dist),'median_interappearance':statistics.median(dist),'sd_interappearance':statistics.pstdev(dist),'latest_interappearance':dist[-1]})
        for w in WINDOWS:
            wc=sum(n in d for d in draws[-w:]); rr=wc/w; fr=c/N; den=math.sqrt(max(1e-12,fr*(1-fr)*(1/w+1/N)))
            recent.append({'number':n,'window':w,'count':wc,'rate':rr,'full_rate':fr,'delta':rr-fr,'std_delta':(rr-fr)/den})
    write_csv(out/'NUMBER_FULL_STATS.csv',full);write_csv(out/'NUMBER_WINDOW_COMPARISON.csv',recent)
    fq25,fq75=quantile([r['count'] for r in full],.25),quantile([r['count'] for r in full],.75); cats=[]
    for w in WINDOWS:
        wr=[r for r in recent if r['window']==w]; q25,q75=quantile([r['count'] for r in wr],.25),quantile([r['count'] for r in wr],.75)
        cats.append({'window':w,'long_strong_recent_weak':sum(a['count']>=fq75 and b['count']<=q25 for a,b in zip(full,wr)),'long_weak_recent_strong':sum(a['count']<=fq25 and b['count']>=q75 for a,b in zip(full,wr)),'recent_q25_count':q25,'recent_q75_count':q75})
    write_csv(out/'LONG_RECENT_CATEGORIES.csv',cats)
    return full,recent,cats

def structure(draws, prev=None):
    odd=Counter();low=Counter();consec=Counter();runs=Counter();endsrep=Counter();maxend=Counter();rangeconc=Counter();sums=[];gaps=[];over=[];band=[0]*5
    for i,d in enumerate(draws):
        odd[sum(x%2 for x in d)]+=1;low[sum(x<=22 for x in d)]+=1;sums.append(sum(d))
        bc=[sum(a<=x<=b for x in d) for a,b in RANGES];rangeconc[max(bc)]+=1
        for j,c in enumerate(bc): band[j]+=c
        gs=[b-a for a,b in zip(d,d[1:])];gaps.extend(gs);consec[sum(g==1 for g in gs)]+=1
        run=mx=1
        for g in gs: run=run+1 if g==1 else 1; mx=max(mx,run)
        runs[mx]+=1; ec=Counter(x%10 for x in d);endsrep[sum(c>1 for c in ec.values())]+=1;maxend[max(ec.values())]+=1
        pd=draws[i-1] if i else prev
        if pd is not None: over.append(len(set(d)&set(pd)))
    return {'draws':len(draws),'sum_mean':statistics.mean(sums),'sum_sd':statistics.pstdev(sums),'odd_distribution':json.dumps(dict(sorted(odd.items()))),'low_1_22_distribution':json.dumps(dict(sorted(low.items()))),'band_number_totals':json.dumps(band),'range_concentration':json.dumps(dict(sorted(rangeconc.items()))),'consecutive_adj_distribution':json.dumps(dict(sorted(consec.items()))),'longest_run_distribution':json.dumps(dict(sorted(runs.items()))),'repeated_ending_classes':json.dumps(dict(sorted(endsrep.items()))),'max_same_ending':json.dumps(dict(sorted(maxend.items()))),'gap_mean':statistics.mean(gaps),'gap_sd':statistics.pstdev(gaps),'previous_overlap_mean':statistics.mean(over) if over else None,'previous_overlap_distribution':json.dumps(dict(sorted(Counter(over).items())))}

def binom_two(n,p,k,cache):
    if k in cache:return cache[k]
    probs=[(1-p)**n]
    for i in range(n):probs.append(probs[-1]*(n-i)/(i+1)*p/(1-p))
    v=min(1.0,2*min(sum(probs[:k+1]),sum(probs[k:])));cache[k]=v;return v

def bh(ps):
    order=sorted(range(len(ps)),key=ps.__getitem__);q=[1.0]*len(ps);run=1.0;m=len(ps)
    for pos in range(m-1,-1,-1):
        ix=order[pos];run=min(run,ps[ix]*m/(pos+1));q[ix]=min(1.0,run)
    return q

def relation(draws,k,out,name):
    N=len(draws);ctr=Counter(t for d in draws for t in itertools.combinations(d,k));wins={w:Counter(t for d in draws[-w:] for t in itertools.combinations(d,k)) for w in WINDOWS};prob=math.comb(45-k,6-k)/math.comb(45,6);expected=N*prob;last={}
    for i,d in enumerate(draws,1):
        for t in itertools.combinations(d,k):last[t]=i
    rows=[];ps=[];cache={}
    for t in itertools.combinations(range(1,46),k):
        c=ctr[t];p=binom_two(N,prob,c,cache);ps.append(p);rows.append({'combination':'-'.join(map(str,t)),'full_count':c,'expected_count':expected,'delta':c-expected,'p_two_sided':p,'last_seen':last.get(t,0),'current_gap':N-last.get(t,0),**{f'recent_{w}':wins[w][t] for w in WINDOWS}})
    qs=bh(ps)
    for r,q in zip(rows,qs):r['q_bh']=q
    write_csv(out/f'{name}_STATS.csv',rows)
    return {'universe':len(rows),'q_lt_0_05':sum(q<.05 for q in qs),'min_q':min(qs)}

def load_b():
    spec=importlib.util.spec_from_file_location('bsource',B_SOURCE);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod

def b_walkforward(rows,draws,out,seed,random_per_target):
    b=load_b(); data=[{'round':i+1,'date':rows[i]['date'],'nums':draws[i]} for i in range(len(draws))]
    if len(data)<201: raise ValueError('not enough draws')
    bank=b.feature_structure_bank(b.make_structure_bank());freq=[0]*45;last=[0]*45;pc=Counter();tc=Counter();profiles=[Counter() for _ in range(6)]
    for d in data[:200]:
        for x in d['nums']:freq[x-1]+=1;last[x-1]=d['round']
        pc.update(itertools.combinations(d['nums'],2));tc.update(itertools.combinations(d['nums'],3));pr=b.structure_profile(d['nums'],None)
        for i,v in enumerate(pr[:5]):profiles[i][v]+=1
    for i in range(1,200):profiles[5][b.structure_profile(data[i]['nums'],data[i-1]['nums'])[5]]+=1
    preds=[];rng=random.Random(seed);random_rows=[];model_hits=defaultdict(list);blocks=defaultdict(list);leak=0
    for train_n in range(200,len(data)):
        target=train_n+1; forecast=b.predictions_for_round(data,train_n,freq,last,pc,tc,profiles,bank);actual=set(data[train_n]['nums']);prev=data[train_n-1]['nums'];actual_prof=b.structure_profile(tuple(sorted(actual)),prev)
        hist=[0]*7
        for _ in range(random_per_target):hist[len(set(rng.sample(range(1,46),6))&actual)]+=1
        rmean=sum(k*hist[k] for k in range(7))/random_per_target;random_rows.append({'target_round':target,'random_tickets':random_per_target,'mean_hits':rmean,**{f'hits_{k}':hist[k] for k in range(7)}})
        for model,ticket in forecast.items():
            hits=len(set(ticket)&actual);pp=b.structure_profile(ticket,prev);sm=sum(pp[i]==actual_prof[i] for i in range(6));preds.append({'target_round':target,'training_through_round':train_n,'model':model,'hits':hits,'structure_conditions_matched':sm,'structure_full_match':int(sm==6)}); model_hits[model].append((target,hits,rmean,sm,int(sm==6)))
            if train_n>=target:leak+=1
        d=data[train_n]
        for x in d['nums']:freq[x-1]+=1;last[x-1]=d['round']
        pc.update(itertools.combinations(d['nums'],2));tc.update(itertools.combinations(d['nums'],3));pr=b.structure_profile(d['nums'],data[train_n-1]['nums'])
        for i,v in enumerate(pr):profiles[i][v]+=1
    write_csv(out/'B_PREDICTIONS_UNIQUE.csv',preds);write_csv(out/'RANDOM_BY_TARGET.csv',random_rows)
    metrics=[]
    for model,vals in sorted(model_hits.items()):
        hs=[x[1] for x in vals];rm=[x[2] for x in vals]; hist=Counter(hs);n=len(hs);mu=statistics.mean(hs)
        metrics.append({'model':model,'n':n,'mean_hits':mu,'variance':statistics.pvariance(hs),'random_mean_same_targets':statistics.mean(rm),'delta_mean':mu-statistics.mean(rm),'rate_ge2':sum(x>=2 for x in hs)/n,'rate_ge3':sum(x>=3 for x in hs)/n,'rate_ge4':sum(x>=4 for x in hs)/n,'rate_ge5':sum(x>=5 for x in hs)/n,'rate_ge6':sum(x>=6 for x in hs)/n,'structure_conditions_mean':statistics.mean(x[3] for x in vals),'structure_full_match_rate':statistics.mean(x[4] for x in vals),**{f'hits_{k}_count':hist[k] for k in range(7)}})
        start=201
        while start<=len(data):
            end=min(start+49,len(data));sub=[x for x in vals if start<=x[0]<=end]
            if sub: blocks[model].append({'model':model,'start':start,'end':end,'n':len(sub),'mean_hits':statistics.mean(x[1] for x in sub),'random_mean':statistics.mean(x[2] for x in sub),'delta_mean':statistics.mean(x[1]-x[2] for x in sub),'rate_ge3':sum(x[1]>=3 for x in sub)/len(sub),'rate_ge4':sum(x[1]>=4 for x in sub)/len(sub)})
            start+=50
    write_csv(out/'B_MODEL_SCORECARD.csv',metrics);write_csv(out/'B_NONOVERLAP_50_BLOCKS.csv',[r for m in MODEL_NAMES for r in blocks[m]])
    exact_probs,exact_mean,exact_var=b.baseline();dump(out/'RANDOM_EXACT_BASELINE.json',{'probabilities_0_to_6':exact_probs,'mean':exact_mean,'variance':exact_var})
    dump(out/'B_LEAKAGE_CHECK.json',{'prediction_records':len(preds),'targets':len(data)-200,'leakage_failures':leak,'rule':'training_through_round = target_round-1'})
    return {'prediction_records':len(preds),'targets':len(data)-200,'random_tickets':(len(data)-200)*random_per_target,'leakage_failures':leak,'metrics':metrics}

def source_inventory(out):
    patterns=('recommend','purchase','error','mistake','review');records=[]
    for base in (ROOT/'analysis',ROOT/'research'):
        if not base.exists():continue
        for p in base.rglob('*'):
            if p.is_file() and any(x in p.name.lower() for x in patterns):records.append({'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)})
    write_csv(out/'HISTORICAL_SOURCE_INVENTORY.csv',records)
    return len(records)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--date');ap.add_argument('--random-per-target',type=int,default=1000);args=ap.parse_args();date=args.date or datetime.now().astimezone().date().isoformat()
    out=ROOT/'analysis'/date/f"MASTER_FULL_V4_{datetime.now().astimezone().strftime('%H%M%S_%f')}";out.mkdir(parents=True,exist_ok=False)
    rows,draws,bonus,data=read_validate();dump(out/'DATA_VALIDATION.json',data)
    full,recent,cats=number_analysis(draws,out); structs=[{'window':'full',**structure(draws)}]+[{'window':str(w),**structure(draws[-w:],draws[-w-1] if len(draws)>w else None)} for w in WINDOWS];write_csv(out/'STRUCTURE_WINDOWS.csv',structs)
    prs=relation(draws,2,out,'PAIR');trs=relation(draws,3,out,'TRIPLE');b=b_walkforward(rows,draws,out,int(date.replace('-','')),args.random_per_target);inv=source_inventory(out)
    status={'A_integrated':'NOT_EXECUTED_SOURCE_NOT_RECOVERED','C_integrated':'NOT_EXECUTED_SOURCE_NOT_RECOVERED','contrarian_integrated':'NOT_EXECUTED_SOURCE_NOT_RECOVERED','B':'EXECUTED','random':'EXECUTED','pair_triple':'EXECUTED','historical_source_search':'EXECUTED'};dump(out/'MODEL_STATUS.json',status)
    summary={'data':data,'long_recent_categories':cats,'pair':prs,'triple':trs,'B':{k:v for k,v in b.items() if k!='metrics'},'historical_source_candidates':inv,'status':'MASTER_PARTIAL'};dump(out/'RUN_SUMMARY.json',summary)
    lines=[f'# Daily MASTER full execution — {date}','',f"1. Data: rounds 1..{data['latest_round']} ({data['rows']} rows), integrity PASS.",f"2. Fresh calculations: number/gap/windows, structure, {prs['universe']} pairs, {trs['universe']} triples, B walk-forward, {b['random_tickets']} random tickets.",'3. Full cumulative number analysis: see NUMBER_FULL_STATS.csv.','4. Long vs 10/30/50/100: see NUMBER_WINDOW_COMPARISON.csv and LONG_RECENT_CATEGORIES.csv.','5. Gap/nonappearance: included in NUMBER_FULL_STATS.csv.','6. Structure/relations: see STRUCTURE_WINDOWS.csv, PAIR_STATS.csv, TRIPLE_STATS.csv.',f"7. A model: {status['A_integrated']}; component inventories recalculated but not represented as integrated A.",'8. B model: actually rerun today; see B_MODEL_SCORECARD.csv and B_NONOVERLAP_50_BLOCKS.csv; fresh random baseline actually generated.',f"9. C model: {status['C_integrated']}.",f"10. Contrarian: {status['contrarian_integrated']}; atypical structures retained in descriptive structure calculations.",f'11. Historical recommendation/error-note source search: {inv} candidate files inventoried; no performance inferred without provenance.','12. Hypotheses: no signal promoted from this daily rerun; existing hold/reject states are not overridden.','13. Limits: integrated A/C/contrarian unavailable, therefore FULL COMPLETE is not claimed.','',f"Pair BH q<.05 survivors: {prs['q_lt_0_05']}; triple survivors: {trs['q_lt_0_05']}; B leakage failures: {b['leakage_failures']}. No candidate/recommendation/final lines generated."]
    (out/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    completion={'study_id':'DAILY_MASTER_FULL_V4','status':'PARTIAL','data_cutoff':data['latest_round'],'executed':True,'recommendation_generation':False};dump(out/'COMPLETION.json',completion)
    verification={'status':'PASS','data_integrity':data['integrity'],'pair_universe':prs['universe'],'triple_universe':trs['universe'],'b_prediction_records':b['prediction_records'],'random_tickets':b['random_tickets'],'leakage_failures':b['leakage_failures'],'recommendation_generation':False};dump(out/'VERIFICATION.json',verification)
    manifest=[]
    for p in sorted(out.iterdir()):
        if p.is_file() and p.name!='SHA256_MANIFEST.csv':manifest.append({'file':p.name,'bytes':p.stat().st_size,'sha256':sha(p)})
    write_csv(out/'SHA256_MANIFEST.csv',manifest)
    print('RUN_DIR='+str(out.relative_to(ROOT)));print(json.dumps(verification))
if __name__=='__main__':main()
