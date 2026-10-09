"""Offline verification of past replay, fixed decision and sealed original purchase rows."""
import argparse,csv,hashlib,importlib.util,itertools,json,math,sys
from pathlib import Path
import numpy as np
sys.dont_write_bytecode=True
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rows(p):
    with Path(p).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def close(a,b):return math.isclose(float(a),float(b),rel_tol=1e-12,abs_tol=1e-12)
def validate(root,deep=False,pre_seal=False):
    root=Path(root).resolve();v4=root.parents[1];repo=v4.parents[1];sys.path.insert(0,str(root));sys.path.insert(0,str(v4))
    from mode_analysis_1245_v4 import summary,random_summary,vector,paired_statistics,decide,random_portfolios
    lock=json.loads((root/'MODE_SELECTION_PRERUN_LOCK_1245_V4.json').read_text(encoding='utf-8'))
    for r in lock['fixed_files']:assert sha(root/r['file'])==r['sha256']
    cfg=json.loads((root/'MODE_SELECTION_CONFIG_1245_V4.json').read_text(encoding='utf-8'))
    assert cfg['historical_first_target']==1045 and cfg['historical_last_target']==1244 and cfg['historical_target_count']==200
    assert cfg['prediction_commit']=='c8782a6063c6148fea0d7292b2a5c1a61fe2b974' and cfg['freeze_commit']=='746efc843d53dff4e61394e26d458ea3f50c93e4'
    assert sha(repo/'lotto_data.csv')==cfg['raw_data_sha256']=='243cd17e6b97a2d96709ddfc689a068038669341a52dcc0743c141d309e43b9f'
    sp=importlib.util.spec_from_file_location('frozen_engine',v4/'prospective_engine_v4.py');e=importlib.util.module_from_spec(sp);sp.loader.exec_module(e)
    e.verify(v4,cfg['freeze_seal_sha256']);rules=json.loads((v4/'RULES_V4.json').read_text());draws=e.load_training(repo/'lotto_data.csv',1245,rules)
    assert sha(v4/'predictions/1245/PREDICTION_SEAL_1245_V4.json')==cfg['prediction_seal_sha256']
    assert sha(v4/'predictions/1245/FINAL_THREE_LINES_1245_V4.csv')=='7ce371fe06a2e4b88f249d264e528b518e6da2fe9f54afc52fda0b26551279a0'
    pred=json.loads((v4/'predictions/1245/PREDICTION_1245_V4.json').read_text());assert pred['actual_numbers'] is None and pred['actual_result']=='NOT READ / NOT USED'
    back=rows(root/'MODE_BACKTEST_1245_V4.csv');null=rows(root/'MODE_RANDOM_BASELINE_1245_V4.csv');blocks=rows(root/'MODE_BLOCK_STABILITY_1245_V4.csv')
    assert len(back)==400 and len(null)==200 and len(blocks)==8
    records={mode:sorted([r for r in back if r['mode']==mode],key=lambda r:int(r['historical_target'])) for mode in ['expanding','rolling300']}
    for mode,rs in records.items():
        assert [int(r['historical_target']) for r in rs]==list(range(1045,1245))
        for r in rs:
            t=int(r['historical_target']);history=draws[:t-1];train=history if mode=='expanding' else history[-300:];actual=set(draws[t-1]['numbers'])
            assert int(r['decision_target'])==1245 and int(r['training_end'])==t-1 and int(r['training_start'])==train[0]['round'] and int(r['training_rows'])==len(train)
            assert r['training_semantic_sha256']==e.canonical(train) and r['frozen_engine_sha256']==sha(v4/'prospective_engine_v4.py')
            assert json.loads(r['actual_historical_numbers'])==sorted(actual) and r['target1245_actual']=='NOT READ / NOT USED'
            lines=[tuple(json.loads(r['line_'+m])) for m in ['G','C','S']];assert len(set(lines))==3
            for q in lines:assert len(q)==len(set(q))==6 and all(n in range(1,46) for n in q)
            hits=[len(set(q)&actual) for q in lines];ol=[len(set(a)&set(b)) for a,b in itertools.combinations(lines,2)]
            assert hits==[int(r['hits_'+m]) for m in ['G','C','S']]
            assert int(r['portfolio_max_hits'])==max(hits) and int(r['portfolio_3plus'])==int(max(hits)>=3) and int(r['portfolio_4plus'])==int(max(hits)>=4) and close(r['mean_ticket_hits'],sum(hits)/3)
            assert json.loads(r['pair_overlaps'])==ol and int(r['union_coverage'])==len(set(x for q in lines for x in q))
    assert [int(r['historical_target']) for r in null]==list(range(1045,1245))
    for r in null:
        R=int(r['replicates']);assert R==10000 and int(r['tickets'])==3*R and r['target1245_actual']=='NOT READ / NOT USED'
        hist=[int(r['hit_count_'+str(k)]) for k in range(7)];maxhist=[int(r['portfolio_max_count_'+str(k)]) for k in range(7)]
        assert sum(hist)==3*R and sum(maxhist)==R and close(r['mean_ticket_hits'],sum(k*n for k,n in enumerate(hist))/(3*R))
        assert int(r['portfolio_3plus_count'])==sum(maxhist[3:]) and int(r['portfolio_4plus_count'])==sum(maxhist[4:])
    stats=json.loads((root/'MODE_STATISTICAL_TESTS_1245_V4.json').read_text());fresh=paired_statistics(vector(records['expanding']),vector(records['rolling300']),cfg)
    for key in ['primary_tests','mode_block_bootstrap_95_ci','secondary_mcnemar']:assert stats[key]==fresh[key],key
    mode,kind,tr,totals,bs,rn=decide(records,null,fresh,cfg)
    decision=json.loads((root/'PRIMARY_PURCHASE_DECISION_1245_V4.json').read_text());assert decision['PRIMARY_PURCHASE_MODE_1245']==mode and decision['selection_type']==kind and decision['selection_trace']==tr
    assert decision['all_200_target_summary']==totals and decision['random_200_target_summary']==rn and decision['actual_result']=='NOT READ / NOT USED'
    saved=json.loads((root/'MODE_SUMMARY_1245_V4.json').read_text());assert saved['modes']==totals and saved['random']==rn
    for n in [50,100,200]:
        assert saved['windows'][str(n)]['modes']=={m:summary(r[-n:]) for m,r in records.items()}
        assert saved['windows'][str(n)]['random']==random_summary(null[-n:])
    for r in blocks:
        i=int(r['block'])-1;s=summary(records[r['mode']][i*50:(i+1)*50]);assert int(r['first_target'])==1045+i*50 and int(r['last_target'])==1094+i*50
        for k in ['mean_ticket_hits','portfolio_3plus_count','portfolio_4plus_count','portfolio_max_hits_sum']:assert close(r[k],s[k])
    original=rows(v4/'predictions/1245/FINAL_THREE_LINES_1245_V4.csv');chosen=rows(root/'PRIMARY_PURCHASE_LINES_1245_V4.csv')
    assert chosen==[r for r in original if r['mode']==mode] and len(chosen)==3
    lines=[[int(r['no'+str(i)]) for i in range(1,7)] for r in chosen];assert lines==decision['PRIMARY_PURCHASE_LINES_1245'] and decision['new_target1245_numbers_generated'] is False
    if kind.startswith('DETERMINISTIC'):
        # Independent tuple construction of the user's five fixed tie-break steps.
        def key(m):
            rs=records[m];counts=[sum(int(r['portfolio_3plus']) for r in rs[i:i+50]) for i in range(0,200,50)];variance=(4*sum(c*c for c in counts)-sum(counts)**2)
            return (sum(int(r['portfolio_3plus']) for r in rs),sum(int(r['portfolio_max_hits']) for r in rs),sum(int(r['hits_'+k]) for r in rs for k in ['G','C','S']),-variance,m=='expanding')
        assert max(records,key=key)==mode
    anchors=[];random_anchors=[]
    if deep:
        bank=e.bank(rules)
        for t in [1045,1094,1095,1144,1145,1194,1195,1244]:
            history=draws[:t-1]
            for m in records:
                train=history if m=='expanding' else history[-300:];scores,struct=e.fit(train,bank,rules);groups=e.candidates(scores,struct,bank,t,m,rules);tickets,trace=e.portfolio(groups,rules)
                r=records[m][t-1045];assert tickets==[tuple(json.loads(r['line_'+k])) for k in ['G','C','S']] and trace==json.loads(r['selection_trace'])
                anchors.append({'target':t,'mode':m,'match':True})
        for t in [1045,1144,1244]:
            tickets,meta=random_portfolios(t,10000,cfg['random_seed']);r=null[t-1045];assert meta['tickets_sha256']==r['simulation_tickets_sha256']
            mask=np.zeros(46,dtype=bool);mask[draws[t-1]['numbers']]=True;hits=mask[tickets].sum(axis=2);mx=hits.max(axis=1)
            assert [int((hits==k).sum()) for k in range(7)]==[int(r['hit_count_'+str(k)]) for k in range(7)]
            assert [int((mx==k).sum()) for k in range(7)]==[int(r['portfolio_max_count_'+str(k)]) for k in range(7)]
            assert all((tickets[:,i,:,None]==tickets[:,j,None,:]).any(axis=2).sum(axis=1).max()<=2 for i,j in [(0,1),(0,2),(1,2)])
            random_anchors.append({'target':t,'portfolios':10000,'match':True})
    hash_count=0
    if not pre_seal:
        seal=json.loads((root/'MODE_SELECTION_SEAL_1245_V4.json').read_text());assert seal['target']==1245 and seal['selected_primary_mode']==mode and seal['final_three_lines']==lines
        assert seal['actual_result']=='NOT READ / NOT USED' and seal['prediction_commit']==cfg['prediction_commit']
        expected={p.name for p in root.iterdir() if p.is_file()}-{'MODE_SELECTION_SEAL_1245_V4.json','MODE_SELECTION_MANIFEST_1245_V4.csv'}
        manifest=rows(root/'MODE_SELECTION_MANIFEST_1245_V4.csv');assert {r['file'] for r in manifest}==expected
        for r in manifest:assert sha(root/r['file'])==r['sha256'] and (root/r['file']).stat().st_size==int(r['bytes'])
        assert {r['file'] for r in seal['artifacts']}==expected|{'MODE_SELECTION_MANIFEST_1245_V4.csv'}
        for r in seal['artifacts']:assert sha(root/r['file'])==r['sha256'];hash_count+=1
    return {'verification':'PASS','historical_targets':[1045,1244],'targets_each_mode':200,'tickets_each_mode':600,'random_portfolios':2000000,'existing_six_lines_unchanged':True,'selected_mode':mode,'selection_type':kind,'selected_lines':lines,'actual1245':'NOT READ / NOT USED','hash_records_checked':hash_count,'deep_model_anchors':anchors,'deep_random_anchors':random_anchors,'statistics_recomputed':True,'no_new_target1245_prediction':True}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',default=str(Path(__file__).parent));p.add_argument('--deep',action='store_true');p.add_argument('--pre-seal',action='store_true');a=p.parse_args();print(json.dumps(validate(a.root,a.deep,a.pre_seal),sort_keys=True))
