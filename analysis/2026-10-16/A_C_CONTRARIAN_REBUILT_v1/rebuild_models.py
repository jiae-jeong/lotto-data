from __future__ import annotations
import csv, math, random, statistics, hashlib, json
from collections import Counter, deque
from itertools import combinations
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
INPUT=ROOT/'lotto_data.csv'
OUT=Path(__file__).resolve().parent
N=45; P=6/45; START=201; START_C=401; END=1245
BANK_SEED=20261016; BANK_SIZE=5000; BOOT_SEED=20261016
COMPONENTS=['long_frequency','recent100_frequency','current_gap','pair_residual_node']
WEIGHTS={'long_frequency':0.35,'recent100_frequency':0.25,'current_gap':0.20,'pair_residual_node':0.20}
CATS=['odd','low','sum_bin','bands','consecutive','end_repeat','cluster','overlap']


def load():
    with INPUT.open(newline='',encoding='utf-8-sig') as f: rr=list(csv.DictReader(f))
    ds=[]
    for r in rr:
        rnd=int(r['round'])
        if rnd>END: continue
        ds.append({'round':rnd,'date':r['date'],'nums':tuple(sorted(int(r[f'no{i}']) for i in range(1,7))),'bonus':int(r['bonus'])})
    assert [d['round'] for d in ds]==list(range(1,END+1)); return ds

def rank(v):
    order=sorted(range(N),key=lambda i:(-v[i],i)); out=[0.0]*N
    for j,i in enumerate(order): out[i]=N-j
    return out

def top6(v): return tuple(sorted(sorted(range(1,N+1),key=lambda x:(-v[x-1],x))[:6]))
def hit(a,b): return len(set(a)&set(b))

def struct(ns,prev=()):
    ns=tuple(ns); gaps=[b-a for a,b in zip(ns,ns[1:])]; bands=tuple(sum(lo<=v<=hi for v in ns) for lo,hi in [(1,10),(11,20),(21,30),(31,40),(41,45)]); ends=Counter(v%10 for v in ns)
    return {'odd':sum(v%2 for v in ns),'low':sum(v<=22 for v in ns),'sum_bin':sum(ns)//20,'bands':bands,'consecutive':sum(g==1 for g in gaps),'end_repeat':sum(c-1 for c in ends.values() if c>1),'cluster':1+sum(g>5 for g in gaps),'overlap':len(set(ns)&set(prev))}

def make_bank():
    rng=random.Random(BANK_SEED); s=set()
    while len(s)<BANK_SIZE: s.add(tuple(sorted(rng.sample(range(1,46),6))))
    bank=sorted(s); static=[]
    for q in bank:
        p=struct(q,()); static.append((p['odd'],p['low'],p['sum_bin'],p['bands'],p['consecutive'],p['end_repeat'],p['cluster']))
    return bank,static

def pair_node(freq,pc,n):
    s=[0.0]*N
    for a,b in combinations(range(1,46),2):
        e=max((5/6)*(45/44)*freq[a]*freq[b]/n,1e-12); z=(pc[(a,b)]-e)/math.sqrt(e); s[a-1]+=z; s[b-1]+=z
    return s

def baseline():
    den=math.comb(45,6); probs=[math.comb(6,k)*math.comb(39,6-k)/den for k in range(7)]; return probs,sum(k*probs[k] for k in range(7))
def mean(xs): return sum(xs)/len(xs) if xs else 0.0

def mbci(vals,block=25,reps=2500,seed=1):
    n=len(vals); rng=random.Random(seed); starts=list(range(n-block+1)); arr=[]
    for _ in range(reps):
        s=[]
        while len(s)<n:
            j=rng.choice(starts); s.extend(vals[j:j+block])
        arr.append(sum(s[:n])/n)
    arr.sort(); return arr[int(.025*reps)],arr[int(.975*reps)-1]

def main():
    draws=load(); bank,bstatic=make_bank(); profiles=[]; prev=()
    for d in draws: profiles.append(struct(d['nums'],prev)); prev=d['nums']
    supports={c:set() for c in CATS}
    for st in bstatic:
        for c,v in zip(CATS[:-1],st): supports[c].add(v)
    supports['overlap']=set(range(7))

    freq=Counter(); pc=Counter(); last={x:0 for x in range(1,46)}; recent=deque(); recent_count=Counter(); scount={c:Counter() for c in CATS}
    for idx,d in enumerate(draws[:START-1]):
        for x in d['nums']: freq[x]+=1; last[x]=d['round']
        pc.update(combinations(d['nums'],2)); recent.append(d['nums'])
        for x in d['nums']: recent_count[x]+=1
        if len(recent)>100:
            old=recent.popleft()
            for x in old: recent_count[x]-=1
        p=profiles[idx]
        for c in CATS: scount[c][p[c]]+=1

    comp_hits={k:[] for k in COMPONENTS}; rows=[]; cval=[]
    for target in range(START,END+1):
        n=target-1; actual=draws[target-1]['nums']; prevnums=draws[target-2]['nums']
        long=[float(freq[x]) for x in range(1,46)]; rec=[float(recent_count[x]) for x in range(1,46)]; gap=[float((target-1)-last[x] if last[x] else target-1) for x in range(1,46)]; pair=pair_node(freq,pc,n)
        scores={'long_frequency':long,'recent100_frequency':rec,'current_gap':gap,'pair_residual_node':pair}
        tickets={k:top6(v) for k,v in scores.items()}
        for k in COMPONENTS: comp_hits[k].append(hit(tickets[k],actual))
        ranks={k:rank(scores[k]) for k in COMPONENTS}; ascore=[sum(WEIGHTS[k]*ranks[k][i] for k in COMPONENTS) for i in range(N)]; at=top6(ascore)
        rows.append({'model':'A_REBUILT_v1','target_round':target,'training_through':target-1,'predicted_numbers':' '.join(map(str,at)),'actual_numbers':' '.join(map(str,actual)),'hits':hit(at,actual),'active_signals':';'.join(COMPONENTS),'note':'recovered weights 0.35/0.25/0.20/0.20; deterministic rank normalization reconstructed'})

        maps={}
        for c in CATS:
            K=len(supports[c]); maps[c]={v:-math.log((scount[c][v]+1)/(n+K)) for v in supports[c]}
        pset=set(prevnums); bestkey=None; bestq=None; bestr=0.0
        for q,st in zip(bank,bstatic):
            ov=len(pset.intersection(q)); r=(maps['odd'][st[0]]+maps['low'][st[1]]+maps['sum_bin'][st[2]]+maps['bands'][st[3]]+maps['consecutive'][st[4]]+maps['end_repeat'][st[5]]+maps['cluster'][st[6]]+maps['overlap'][ov])
            key=(r,tuple(-x for x in q))
            if bestkey is None or key>bestkey: bestkey=key; bestq=q; bestr=r
        rows.append({'model':'CONTRARIAN_REBUILT_v1','target_round':target,'training_through':target-1,'predicted_numbers':' '.join(map(str,bestq)),'actual_numbers':' '.join(map(str,actual)),'hits':hit(bestq,actual),'active_signals':';'.join(CATS),'note':f'fixed bank seed={BANK_SEED}; size={BANK_SIZE}; structural surprisal={bestr:.6f}'})

        if target>=START_C:
            active=[]; details=[]; idxcur=target-START
            for k in COMPONENTS:
                hist=comp_hits[k][max(0,idxcur-200):idxcur]
                m=mean(hist); bms=[mean(hist[i:i+50]) for i in range(0,len(hist),50) if hist[i:i+50]]; good=sum(x>=0.8 for x in bms); req=max(1,math.ceil(len(bms)/2)); survive=(m>=0.8 and good>=req); details.append((k,m,good,len(bms),survive))
                if survive: active.append(k)
            fallback=False
            if not active:
                order={k:i for i,k in enumerate(COMPONENTS)}; active=[max(details,key=lambda z:(z[1],z[2],-order[z[0]]))[0]]; fallback=True
            cr={k:ranks[k] for k in active}; cs=[sum(cr[k][i] for k in active)/len(active) for i in range(N)]; ct=top6(cs)
            rows.append({'model':'C_REBUILT_v1','target_round':target,'training_through':target-1,'predicted_numbers':' '.join(map(str,ct)),'actual_numbers':' '.join(map(str,actual)),'hits':hit(ct,actual),'active_signals':';'.join(active),'note':'nested trailing-200 validation; mean>=0.8 and >=half nonoverlap 50-blocks >=0.8; equal-rank combine; fallback='+str(fallback)})
            for k,m,g,nb,survive in details: cval.append({'target_round':target,'component':k,'trailing200_mean':m,'positive_blocks':g,'total_blocks':nb,'survives':survive,'selected':k in active,'fallback':fallback})

        d=draws[target-1]
        for x in d['nums']: freq[x]+=1; last[x]=target
        pc.update(combinations(d['nums'],2)); recent.append(d['nums'])
        for x in d['nums']: recent_count[x]+=1
        if len(recent)>100:
            old=recent.popleft()
            for x in old: recent_count[x]-=1
        p=profiles[target-1]
        for c in CATS: scount[c][p[c]]+=1

    pf=['model','target_round','training_through','predicted_numbers','actual_numbers','hits','active_signals','note']
    with (OUT/'walkforward_predictions.csv').open('w',newline='',encoding='utf-8-sig') as f: w=csv.DictWriter(f,fieldnames=pf);w.writeheader();w.writerows(rows)
    with (OUT/'c_nested_validation.csv').open('w',newline='',encoding='utf-8-sig') as f: w=csv.DictWriter(f,fieldnames=list(cval[0]));w.writeheader();w.writerows(cval)
    probs,bm=baseline(); metrics=[]
    for model in ['A_REBUILT_v1','C_REBUILT_v1','CONTRARIAN_REBUILT_v1']:
        lows=[401] if model=='C_REBUILT_v1' else [201,401]
        for lo in lows:
            hs=[int(r['hits']) for r in rows if r['model']==model and lo<=r['target_round']<=END]; c=Counter(hs); ci=mbci([h-bm for h in hs],seed=BOOT_SEED+lo+len(model)); metrics.append({'model':model,'window':f'{lo}-{END}','n':len(hs),'mean_hits':mean(hs),'variance_hits':statistics.pvariance(hs),'hits_0':c[0],'hits_1':c[1],'hits_2':c[2],'hits_3':c[3],'hits_4':c[4],'hits_5':c[5],'hits_6':c[6],'rate_ge_2':sum(h>=2 for h in hs)/len(hs),'rate_ge_3':sum(h>=3 for h in hs)/len(hs),'rate_ge_4':sum(h>=4 for h in hs)/len(hs),'rate_ge_5':sum(h>=5 for h in hs)/len(hs),'rate_exact_6':sum(h==6 for h in hs)/len(hs),'baseline_mean':bm,'delta_mean_vs_random':mean(hs)-bm,'delta_ci95_low':ci[0],'delta_ci95_high':ci[1]})
    with (OUT/'metrics.csv').open('w',newline='',encoding='utf-8-sig') as f: w=csv.DictWriter(f,fieldnames=list(metrics[0]));w.writeheader();w.writerows(metrics)
    spec={'version':'A_C_CONTRARIAN_REBUILT_v1','date':'2026-10-16','data_rounds':'1-1245','no_1246_prediction_generated':True,'classification':'functional reconstruction; not claimed as missing legacy executable identity','A_REBUILT_v1':{'weights':WEIGHTS,'normalization':'deterministic within-component rank 45..1; lower-number tie','pair_formula':'S006 residual node E=(5/6)*(45/44)*F_a*F_b/n; z=(O-E)/sqrt(E)'},'C_REBUILT_v1':{'rule':'At target t use only prior component hit records. Trailing <=200 mean >=0.8 and at least half nonoverlap <=50 blocks mean >=0.8; equal-rank blend survivors; if none, best prior mean component.'},'CONTRARIAN_REBUILT_v1':{'seed':BANK_SEED,'bank_size':BANK_SIZE,'score':'sum structural surprisal -log Laplace-smoothed empirical P(feature) for odd,low,sum_bin,bands,consecutive,end_repeat,cluster,overlap'},'baseline':{'mean':bm,'probabilities':probs}}
    (OUT/'spec.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=['# A/C/Contrarian functional reconstruction v1','','Executable successors reconstructed from recovered historical concepts plus surviving exact lineage. Not presented as byte-identical legacy source.','','## Walk-forward results','','| Model / window | N | Mean hits | Delta vs 0.8 | 95% moving-block CI | 2+ | 3+ | 4+ |','|---|---:|---:|---:|---:|---:|---:|---:|']
    for r in metrics: lines.append(f"| {r['model']} {r['window']} | {r['n']} | {r['mean_hits']:.6f} | {r['delta_mean_vs_random']:+.6f} | [{r['delta_ci95_low']:+.6f}, {r['delta_ci95_high']:+.6f}] | {r['rate_ge_2']:.4%} | {r['rate_ge_3']:.4%} | {r['rate_ge_4']:.4%} |")
    lines+=['','## Leakage checks','- Every target t uses draw data only through t-1.','- C model selection uses only component hit records strictly before t.','- State is updated with target actual only after all target forecasts are written.','- No 1246 candidate/final line is generated.','','## Reconstruction boundaries','- A historical 35/25/20/20 weights are preserved exactly. Missing legacy scale normalization is explicitly reconstructed with rank normalization.','- C historical principle is operationalized as nested repeated validation; no historical numeric C weights were invented.','- Contrarian historical atypical-structure role is operationalized as a fixed-bank structural-surprisal model.']
    (OUT/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    assert all(int(r['training_through'])==int(r['target_round'])-1 for r in rows); assert max(int(r['target_round']) for r in rows)==1245
    man=[]
    for p in sorted(OUT.iterdir()):
        if p.name!='MANIFEST.sha256': man.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}")
    (OUT/'MANIFEST.sha256').write_text('\n'.join(man)+'\n',encoding='utf-8')
    print('PRED_ROWS',len(rows),'CVAL_ROWS',len(cval))
    for r in metrics: print(r['model'],r['window'],'n',r['n'],'mean',round(r['mean_hits'],6),'delta',round(r['delta_mean_vs_random'],6),'2+',round(r['rate_ge_2'],6),'3+',round(r['rate_ge_3'],6),'4+',round(r['rate_ge_4'],6),'CI',round(r['delta_ci95_low'],6),round(r['delta_ci95_high'],6))

if __name__=='__main__': main()
