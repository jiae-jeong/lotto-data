"""Frozen, standard-library research predictors. No V3 imports or automatic outcome retrieval."""
import argparse, csv, hashlib, itertools, json, math, random, sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
sys.dont_write_bytecode=True
from verify_freeze_v4 import verify, sha

ROOT=Path(__file__).resolve().parent
P=6/45

def canonical(draws):
    return hashlib.sha256(json.dumps(draws,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def load_training(path,target,rules):
    draws=[]
    with Path(path).open(encoding='utf-8-sig',newline='') as f:
        reader=csv.reader(f);header=next(reader);ri=header.index('round')
        for row in reader:
            round_id=int(row[ri])
            if round_id>=target:raise ValueError('Input contains target/future row; outcome fields not interpreted')
            r=dict(zip(header,row));ns=sorted(int(r['no'+str(i)]) for i in range(1,7));bonus=int(r['bonus'])
            assert len(set(ns))==6 and all(1<=n<=45 for n in ns) and 1<=bonus<=45 and bonus not in ns
            draws.append({'round':round_id,'date':r['date'],'numbers':ns,'bonus':bonus})
    assert [d['round'] for d in draws]==list(range(1,target))
    assert canonical(draws[:1244])==rules['initial_semantic_sha256']
    return draws

def top(score):return tuple(sorted(sorted(range(1,46),key=lambda n:(-score[n],n))[:6]))
def agebin(age):return 0 if age==0 else 1 if age==1 else 2 if age==2 else 3 if age<=5 else 4 if age<=10 else 5
def profile(ticket,previous=()):
    ns=sorted(ticket);gaps=[b-a for a,b in zip(ns,ns[1:])];end=Counter(n%10 for n in ns)
    return {'odd':sum(n%2 for n in ns),'low':sum(n<=22 for n in ns),'sum_bin':sum(ns)//30,
        'bands':tuple(sum(lo<=n<=hi for n in ns) for lo,hi in [(1,10),(11,20),(21,30),(31,40),(41,45)]),
        'consecutive':sum(g==1 for g in gaps),'end_repeat':sum(v-1 for v in end.values()),
        'overlap':len(set(ns)&set(previous)),'cluster':1+sum(g>5 for g in gaps)}

def bank(rules):
    rng=random.Random(rules['candidate_bank']['seed']);seen=set()
    while len(seen)<rules['candidate_bank']['size']:seen.add(tuple(sorted(rng.sample(range(1,46),6))))
    return sorted(seen)

def fit(train,candidate_bank,rules):
    n=len(train);nums=[tuple(d['numbers']) for d in train];freq=Counter(x for q in nums for x in q)
    score={'V4_F':{x:freq[x] for x in range(1,46)}}
    risk=Counter();hit=Counter();seen={x:None for x in range(1,46)}
    for i,q in enumerate(nums):
        if i:
            for x in range(1,46):
                if seen[x] is None:continue
                b=agebin(i-1-seen[x]);risk[b]+=1;hit[b]+=int(x in q)
        for x in q:seen[x]=i
    strength=rules['shrinkage']['gap']
    score['V4_G']={x:(hit[agebin(n-1-seen[x] if seen[x] is not None else n)]+strength*P)/(risk[agebin(n-1-seen[x] if seen[x] is not None else n)]+strength) for x in range(1,46)}
    cr=Counter();ch=Counter();mr=Counter();mh=Counter()
    for i,q in enumerate(nums):
        if i>=10:
            c=Counter(x for old in nums[i-10:i] for x in old)
            for x in range(1,46):cr[c[x]]+=1;ch[c[x]]+=int(x in q)
        if i>=40:
            a=Counter(x for old in nums[i-40:i-20] for x in old);b=Counter(x for old in nums[i-20:i] for x in old)
            for x in range(1,46):state=(a[x]>20*P,b[x]>20*P);mr[state]+=1;mh[state]+=int(x in q)
    c=Counter(x for q in nums[-10:] for x in q);a=Counter(x for q in nums[-40:-20] for x in q);b=Counter(x for q in nums[-20:] for x in q)
    strength=rules['shrinkage']['conditional']
    score['V4_C']={x:(ch[c[x]]+strength*P)/(cr[c[x]]+strength) for x in range(1,46)}
    strength=rules['shrinkage']['momentum']
    score['V4_M']={x:(mh[(a[x]>20*P,b[x]>20*P)]+strength*P)/(mr[(a[x]>20*P,b[x]>20*P)]+strength) for x in range(1,46)}
    pc=Counter(p for q in nums for p in itertools.combinations(q,2));tc=Counter(p for q in nums for p in itertools.combinations(q,3))
    ps={x:0. for x in range(1,46)};ts=dict(ps)
    for pair in itertools.combinations(range(1,46),2):
        x,y=pair;e=(5/6)*(45/44)*freq[x]*freq[y]/n;z=(pc[pair]-e)/math.sqrt(max(e,1e-12))
        for x in pair:ps[x]+=z
    for triple in itertools.combinations(range(1,46),3):
        x,y,z=triple;e=(20/36)*(2025/1892)*freq[x]*freq[y]*freq[z]/(n*n);value=(tc[triple]-e)/math.sqrt(max(e,1e-12))
        for x in triple:ts[x]+=value
    score['V4_P']=ps;score['V4_T']=ts
    features=list(rules['structure_support_sizes']);counts={f:Counter() for f in features};den={f:Counter() for f in features}
    for i in range(2,n):
        prev=profile(nums[i-1],nums[i-2]);nxt=profile(nums[i],nums[i-1])
        for f in features:counts[f][(prev[f],nxt[f])]+=1;den[f][prev[f]]+=1
    latest=profile(nums[-1],nums[-2]);struct={}
    for ticket in candidate_bank:
        p=profile(ticket,nums[-1]);struct[ticket]=sum(math.log((counts[f][(latest[f],p[f])]+1)/(den[f][latest[f]]+rules['structure_support_sizes'][f])) for f in features)
    return score,struct

def candidates(score,struct,candidate_bank,target,mode,rules):
    result={};limit=rules['candidates_per_model']
    for mid,values in score.items():
        order=sorted(range(1,46),key=lambda x:(-values[x],x));ticket=top(values);choices={ticket}
        for old in ticket:
            for new in order[6:12]:choices.add(tuple(sorted((set(ticket)-{old})|{new})))
        result[mid]=sorted(choices,key=lambda q:(-sum(values[x] for x in q),q))[:limit]
    result['V4_S']=sorted(candidate_bank,key=lambda q:(-struct[q],q))[:limit]
    seed=int.from_bytes(hashlib.sha256(f"{rules['null_seed']}|{target}|{mode}".encode()).digest()[:8],'big')
    rng=random.Random(seed);null_choices=[]
    while len(null_choices)<limit:
        ticket=tuple(sorted(rng.sample(range(1,46),6)))
        if ticket not in null_choices:null_choices.append(ticket)
    result['V4_U']=null_choices
    return result

def portfolio(groups,rules):
    chosen=[];trace=[]
    for mid in rules['portfolio']['model_order']:
        available=[q for q in groups[mid] if q not in chosen]
        acceptable=[q for q in available if all(len(set(q)&set(old))<=rules['portfolio']['maximum_pair_overlap'] for old in chosen)]
        if acceptable:ticket=acceptable[0];fallback=False
        else:
            ticket=min(available,key=lambda q:(sum(len(set(q)&set(old)) for old in chosen),max([len(set(q)&set(old)) for old in chosen] or [0]),groups[mid].index(q),q));fallback=True
        chosen.append(ticket);trace.append({'model':mid,'fallback':fallback,'candidate_rank':groups[mid].index(ticket)+1})
    assert len(set(chosen))==3
    return chosen,trace

def relations(ticket,previous):
    ns=tuple(sorted(ticket));out=profile(ns,previous)
    out.update({'numbers':ns,'sum':sum(ns),'gaps':[b-a for a,b in zip(ns,ns[1:])],
        'pairs':list(itertools.combinations(ns,2)),'triples':list(itertools.combinations(ns,3)),
        'last_digits':[x%10 for x in ns],'high':sum(x>=23 for x in ns)})
    return out

def predict(data,target,output,expected_seal_sha=None):
    seal=verify(ROOT,expected_seal_sha);rules=json.loads((ROOT/'RULES_V4.json').read_text())
    assert target>=rules['first_prospective_target']
    draws=load_training(data,target,rules);candidate_bank=bank(rules);records={}
    for mode in rules['window_modes']:
        train=draws if mode=='expanding' else draws[-rules['rolling_window']:]
        assert train[-1]['round']==target-1
        scores,struct=fit(train,candidate_bank,rules);groups=candidates(scores,struct,candidate_bank,target,mode,rules);lines,trace=portfolio(groups,rules)
        records[mode]={'training_start':train[0]['round'],'training_end':target-1,'model_predictions':{mid:(top(scores[mid]) if mid in scores else group[0]) for mid,group in groups.items()},'candidates':groups,'portfolio':lines,'selection_trace':trace,'relations':[relations(q,train[-1]['numbers']) for q in lines], 'overlaps':[len(set(a)&set(b)) for a,b in itertools.combinations(lines,2)]}
    path=Path(output);assert not path.exists(),'Refuse overwrite'
    result={'version':'prospective_v4','classification':'EXPERIMENTAL_RESEARCH_ONLY_NO_VALIDATED_EDGE','created_at_utc':datetime.now(timezone.utc).isoformat(),'target_round':target,'training_input_sha256':sha(data),'freeze_base_commit':seal['base_commit'],'seal_sha256':sha(ROOT/'V4_FREEZE_SEAL.json'),'result_rows_read':False,'prospective_eligibility':'PENDING_PRE_DRAW_GIT_COMMIT_PROOF','modes':records}
    with path.open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--verify-freeze',action='store_true');parser.add_argument('--data');parser.add_argument('--target',type=int);parser.add_argument('--output');parser.add_argument('--expected-seal-sha')
    a=parser.parse_args()
    if a.verify_freeze:print(json.dumps({'freeze':'PASS','base_commit':verify(ROOT,a.expected_seal_sha)['base_commit']}))
    else:
        if not all((a.data,a.target,a.output)):parser.error('--data --target --output required')
        r=predict(a.data,a.target,a.output,a.expected_seal_sha);print(json.dumps({'target':r['target_round'],'output':a.output,'status':'experimental predictions generated; registration not yet proved'}))
