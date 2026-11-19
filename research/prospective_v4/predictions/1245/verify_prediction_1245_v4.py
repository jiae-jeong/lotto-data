"""Read-only, offline independent semantic/hash audit; never runs a prediction."""
import argparse,csv,hashlib,importlib.util,itertools,json,math,random,sys
from collections import Counter
from pathlib import Path
sys.dont_write_bytecode=True
EXPECTED_FREEZE='746efc843d53dff4e61394e26d458ea3f50c93e4'
EXPECTED_SEAL='6a018e3036187a26ac9bcffda9fd7379d65d86cde84514faa08f4ea349b0f4bb'
EXPECTED_RAW='243cd17e6b97a2d96709ddfc689a068038669341a52dcc0743c141d309e43b9f'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rows(p):
    with Path(p).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def numbers(r):return tuple(int(r['no'+str(i)]) for i in range(1,7))
def same(a,b):return math.isclose(float(a),float(b),rel_tol=1e-13,abs_tol=1e-13)
def validate(root,pre_seal=False):
    root=Path(root).resolve();v4=root.parents[1];repo=v4.parents[1]
    sys.path.insert(0,str(v4))
    spec=importlib.util.spec_from_file_location('freeze_verifier',v4/'verify_freeze_v4.py');fv=importlib.util.module_from_spec(spec);spec.loader.exec_module(fv)
    fv.verify(v4,EXPECTED_SEAL)
    raw=repo/'lotto_data.csv';assert sha(raw)==EXPECTED_RAW
    data=rows(raw);assert len(data)==1244 and [int(r['round']) for r in data]==list(range(1,1245))
    for r in data:
        ns=numbers(r);bonus=int(r['bonus']);assert len(set(ns))==6 and all(1<=x<=45 for x in ns) and bonus in range(1,46) and bonus not in ns
    rules=json.loads((v4/'RULES_V4.json').read_text(encoding='utf-8'))
    summary=json.loads((root/'PREDICTION_1245_V4.json').read_text(encoding='utf-8'))
    engine=json.loads((root/'ENGINE_PREDICTION_1245_V4.json').read_text(encoding='utf-8'))
    assert summary['target']==1245 and summary['training_cutoff']==1244 and summary['freeze_commit']==EXPECTED_FREEZE and summary['raw_data_sha256']==EXPECTED_RAW
    assert summary['freeze_seal_sha256']==EXPECTED_SEAL and summary['status']=='REGISTERED_UNEVALUATED'
    assert summary['actual_result']=='NOT READ / NOT USED' and summary['actual_numbers'] is None and summary['result_rows_read'] is False
    assert summary['execution_kind']=='official' and engine['result_rows_read'] is False and engine['target_round']==1245
    assert summary['modes']==engine['modes'] and summary['frozen_engine_result_sha256']==sha(root/'ENGINE_PREDICTION_1245_V4.json')
    capture=json.loads((root/'FROZEN_SCORE_CAPTURE_1245_V4.json').read_text(encoding='utf-8'))
    assert capture['target']==1245 and capture['training_cutoff']==1244 and capture['actual_result']=='NOT READ / NOT USED'
    modelrows=rows(root/'MODEL_PREDICTIONS_1245_V4.csv');candrows=rows(root/'CANDIDATES_1245_V4.csv');finalrows=rows(root/'FINAL_THREE_LINES_1245_V4.csv');diags=rows(root/'STRUCTURE_DIAGNOSTICS_1245_V4.csv');nr=rows(root/'NUMBER_SCORES_1245_V4.csv');ts=rows(root/'TICKET_SCORES_1245_V4.csv');trace=rows(root/'SELECTION_TRACE_1245_V4.csv')
    assert (len(modelrows),len(candrows),len(finalrows),len(diags),len(nr),len(ts),len(trace))==(16,592,6,592,720,20518,222)
    for file in root.glob('*.csv'):
        for row in rows(file):
            assert int(row['target'])==1245 and int(row['training_cutoff'])==1244,file.name
            if 'no1' in row:
                ns=numbers(row);assert len(set(ns))==6 and all(1<=x<=45 for x in ns) and ns==tuple(sorted(ns))
    all_portfolios={}
    for mode in rules['window_modes']:
        cap=capture['modes'][mode];rec=summary['modes'][mode]
        assert cap['training_end']==rec['training_end']==1244 and cap['training_start']==rec['training_start']==(1 if mode=='expanding' else 945)
        train=data if mode=='expanding' else data[-300:]
        scores={mid:{int(x):float(s) for x,s in v.items()} for mid,v in cap['number_scores'].items()}
        struct={tuple(r['numbers']):r['score'] for r in cap['structure_bank_scores']};assert len(struct)==10000
        rng=random.Random(rules['candidate_bank']['seed']);bank=set()
        while len(bank)<10000:bank.add(tuple(sorted(rng.sample(range(1,46),6))))
        assert set(struct)==bank
        groups={};predictions={}
        for mid in rules['active_model_ids']:
            cr=sorted([r for r in candrows if r['mode']==mode and r['model_id']==mid],key=lambda r:int(r['candidate_rank']))
            assert len(cr)==37 and [int(r['candidate_rank']) for r in cr]==list(range(1,38))
            actual=[numbers(r) for r in cr];assert len(set(actual))==37
            if mid in scores:
                ss=scores[mid];order=sorted(range(1,46),key=lambda n:(-ss[n],n));top=tuple(sorted(order[:6]));pool={top}
                for old in top:
                    for new in order[6:12]:pool.add(tuple(sorted((set(top)-{old})|{new})))
                expected=sorted(pool,key=lambda q:(-sum(ss[x] for x in q),q))[:37];predictions[mid]=top
                for row in cr:assert same(row['ticket_score'],sum(ss[x] for x in numbers(row)))
                for row in [r for r in nr if r['mode']==mode and r['model_id']==mid]:
                    x=int(row['number']);assert same(row['score'],ss[x]) and int(row['number_rank'])==order.index(x)+1
            elif mid=='V4_S':
                expected=sorted(struct,key=lambda q:(-struct[q],q))[:37];predictions[mid]=expected[0]
                for row in cr:assert same(row['ticket_score'],struct[numbers(row)])
                full=sorted([r for r in ts if r['mode']==mode and r['model_id']==mid],key=lambda r:int(r['bank_rank']))
                assert [numbers(r) for r in full]==sorted(struct,key=lambda q:(-struct[q],q))
                assert all(same(r['ticket_score'],struct[numbers(r)]) for r in full)
            else:
                seed=int.from_bytes(hashlib.sha256(f"{rules['null_seed']}|1245|{mode}".encode()).digest()[:8],'big');rng=random.Random(seed);expected=[]
                while len(expected)<37:
                    ticket=tuple(sorted(rng.sample(range(1,46),6)))
                    if ticket not in expected:expected.append(ticket)
                predictions[mid]=expected[0]
                assert all(not row['ticket_score'] for row in cr)
            assert actual==expected and list(map(tuple,rec['candidates'][mid]))==expected
            mr=[r for r in modelrows if r['mode']==mode and r['model_id']==mid];assert len(mr)==1 and numbers(mr[0])==predictions[mid] and int(mr[0]['training_rows'])==len(train)
            assert tuple(rec['model_predictions'][mid])==predictions[mid]
            groups[mid]=expected
        chosen=[]
        fr=sorted([r for r in finalrows if r['mode']==mode],key=lambda r:int(r['line']));assert len(fr)==3
        for idx,mid in enumerate(rules['portfolio']['model_order']):
            available=[q for q in groups[mid] if q not in chosen]
            acceptable=[q for q in available if all(len(set(q)&set(old))<=2 for old in chosen)]
            q=acceptable[0] if acceptable else min(available,key=lambda q:(sum(len(set(q)&set(old)) for old in chosen),max([len(set(q)&set(old)) for old in chosen] or [0]),groups[mid].index(q),q))
            assert numbers(fr[idx])==q and fr[idx]['model_id']==mid and int(fr[idx]['candidate_rank'])==groups[mid].index(q)+1
            assert fr[idx]['fallback']==str(not bool(acceptable))
            tr=[r for r in trace if r['mode']==mode and int(r['portfolio_line'])==idx+1]
            assert len(tr)==37 and sum(r['selected']=='True' for r in tr)==1
            for row in tr:
                ticket=tuple(json.loads(row['numbers']));ols=[len(set(ticket)&set(old)) for old in chosen]
                assert json.loads(row['overlaps'])==ols and (row['selected']=='True')==(ticket==q) and (row['acceptable']=='True')==(ticket in acceptable)
            chosen.append(q)
        assert chosen==list(map(tuple,rec['portfolio'])) and len(set(chosen))==3
        assert rec['overlaps']==[len(set(a)&set(b)) for a,b in itertools.combinations(chosen,2)]
        all_portfolios[mode]=chosen
        previous=set(numbers(train[-1]));pc=Counter(p for r in train for p in itertools.combinations(sorted(numbers(r)),2));tc=Counter(p for r in train for p in itertools.combinations(sorted(numbers(r)),3));freq=Counter(x for r in train for x in numbers(r))
        for row in [r for r in diags if r['mode']==mode]:
            q=tuple(json.loads(row['numbers']));gaps=[b-a for a,b in zip(q,q[1:])]
            assert row['diagnostic_only']=='True' and row['veto_applied']=='False'
            assert int(row['odd'])==sum(x%2 for x in q) and int(row['even'])==6-sum(x%2 for x in q)
            assert int(row['low'])==sum(x<=22 for x in q) and int(row['high'])==sum(x>=23 for x in q)
            assert int(row['sum'])==sum(q) and int(row['sum_bin'])==sum(q)//30 and json.loads(row['gaps'])==gaps
            assert int(row['consecutive_count'])==gaps.count(1) and int(row['cluster_count'])==1+sum(g>5 for g in gaps)
            assert json.loads(row['bands_1_10_11_20_21_30_31_40_41_45'])==[sum(lo<=x<=hi for x in q) for lo,hi in [(1,10),(11,20),(21,30),(31,40),(41,45)]]
            assert json.loads(row['last_digits'])==[x%10 for x in q] and int(row['ending_repeat_excess'])==6-len(set(x%10 for x in q))
            assert int(row['previous_draw_overlap'])==len(set(q)&previous)
            details=json.loads(row['pairs']);triplets=json.loads(row['triples'])
            assert [tuple(r['pair']) for r in details]==list(itertools.combinations(q,2)) and len(details)==15
            assert [tuple(r['triple']) for r in triplets]==list(itertools.combinations(q,3)) and len(triplets)==20
            for d in details:
                a,b=d['pair'];expected=(5/6)*(45/44)*freq[a]*freq[b]/len(train)
                assert d['training_count']==pc[(a,b)] and same(d['expected_count_frozen_pair_formula'],expected) and same(d['residual_z'],(pc[(a,b)]-expected)/math.sqrt(max(expected,1e-12)))
            assert all(d['training_count']==tc[tuple(d['triple'])] for d in triplets)
    baseline=json.loads((root/'RANDOM_BASELINE_1245_V4.json').read_text(encoding='utf-8'))
    assert baseline['source_sha256']==sha(v4/'RANDOM_BASELINE_V4.json') and baseline['observed_performance'] is None and baseline['superiority_claim'] is False
    for k in range(7):assert same(baseline['exact_pmf'][str(k)]['probability'],math.comb(6,k)*math.comb(39,6-k)/math.comb(45,6))
    hash_count=0
    if not pre_seal:
        manifest=rows(root/'PREDICTION_MANIFEST_1245_V4.csv');seal=json.loads((root/'PREDICTION_SEAL_1245_V4.json').read_text(encoding='utf-8'))
        assert seal['target']==1245 and seal['training_cutoff']==1244 and seal['freeze_commit']==EXPECTED_FREEZE and seal['freeze_seal_sha256']==EXPECTED_SEAL and seal['raw_data_sha256']==EXPECTED_RAW
        assert seal['actual_result']=='NOT READ / NOT USED' and seal['status']=='REGISTERED_UNEVALUATED' and seal['official_run_count']==1
        expected_names={p.name for p in root.iterdir() if p.is_file()}-{'PREDICTION_MANIFEST_1245_V4.csv','PREDICTION_SEAL_1245_V4.json'}
        assert {r['file'] for r in manifest}==expected_names
        for r in manifest:assert sha(root/r['file'])==r['sha256'] and (root/r['file']).stat().st_size==int(r['bytes'])
        assert {r['file'] for r in seal['artifacts']}==expected_names|{'PREDICTION_MANIFEST_1245_V4.csv'}
        for r in seal['artifacts']:assert sha(root/r['file'])==r['sha256'] and (root/r['file']).stat().st_size==r['bytes']
        hash_count=len(seal['artifacts'])
    return {'verification':'PASS','target':1245,'training_cutoff':1244,'freeze_verification':'PASS','raw_integrity':'PASS','model_mode_records':16,'candidate_tickets':592,'unique_portfolio_lines_each_mode':3,'structure_veto_count':0,'number_scores':720,'ticket_scores':20518,'trace_rows':222,'actual_result':'NOT READ / NOT USED','actual_nonuse_verification_method':'input pinned to cutoff1244; no outcome input/network retrieval in engine or runner; actual_numbers=null; result_rows_read=false; not comparison against unknown winning numbers','status':'REGISTERED_UNEVALUATED','hash_records_checked':hash_count,'portfolios':all_portfolios}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',default=str(Path(__file__).parent));p.add_argument('--pre-seal',action='store_true');a=p.parse_args();print(json.dumps(validate(a.root,a.pre_seal),sort_keys=True))
