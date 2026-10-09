"""Fixed historical replay and mode decision. No network, no new 1245 prediction."""
import csv,datetime,hashlib,importlib.util,json,math,platform,sys,time
from pathlib import Path
import numpy as np
sys.dont_write_bytecode=True
from mode_analysis_1245_v4 import random_portfolios,summary,random_summary,vector,paired_statistics,decide,relationship_diagnostics
HERE=Path(__file__).resolve().parent;V4=HERE.parents[1];REPO=V4.parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write_json(name,obj):
    with (HERE/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,indent=2,sort_keys=True,allow_nan=False);f.write('\n')
def write_csv(name,rows):
    with (HERE/name).open('x',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
def encoded(obj):return json.dumps(obj,sort_keys=True,separators=(',',':'))
def csvrows(p):
    with Path(p).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def main():
    lock=json.loads((HERE/'MODE_SELECTION_PRERUN_LOCK_1245_V4.json').read_text(encoding='utf-8'))
    for r in lock['fixed_files']:assert sha(HERE/r['file'])==r['sha256'],r['file']
    cfg=json.loads((HERE/'MODE_SELECTION_CONFIG_1245_V4.json').read_text(encoding='utf-8'))
    assert np.__version__==cfg['numpy_version'] and platform.python_version_tuple()[:2]==('3','12')
    assert sha(REPO/'lotto_data.csv')==cfg['raw_data_sha256']
    sys.path.insert(0,str(V4));sp=importlib.util.spec_from_file_location('frozen_engine',V4/'prospective_engine_v4.py');e=importlib.util.module_from_spec(sp);sp.loader.exec_module(e)
    e.verify(V4,cfg['freeze_seal_sha256']);rules=json.loads((V4/'RULES_V4.json').read_text(encoding='utf-8'))
    draws=e.load_training(REPO/'lotto_data.csv',1245,rules);assert len(draws)==1244
    bank=e.bank(rules);records={m:[] for m in rules['window_modes']};nullrows=[];started=datetime.datetime.now(datetime.timezone.utc).isoformat()
    runlog=(HERE/'EXECUTION_LOG_1245_V4.log').open('x',encoding='utf-8',newline='\n')
    def log(text):runlog.write(text+'\n');runlog.flush();print(text,flush=True)
    log('PRERUN_PROTOCOL_CONFIG_CODE_LOCK_SHA256='+sha(HERE/'MODE_SELECTION_PRERUN_LOCK_1245_V4.json'))
    log('RUN_STARTED_UTC='+started+'; historical_targets=1045..1244; ACTUAL_1245=NOT READ / NOT USED; outcome inputs historical only')
    sinks={}
    for name in ['MODE_BACKTEST_1245_V4.csv','MODE_RANDOM_BASELINE_1245_V4.csv']:sinks[name]=(HERE/name).open('x',encoding='utf-8',newline='')
    writers={};fallbacks={m:0 for m in records}
    def append(name,row):
        if name not in writers:
            writers[name]=csv.DictWriter(sinks[name],fieldnames=list(row),lineterminator='\n');writers[name].writeheader()
        writers[name].writerow(row);sinks[name].flush()
    try:
        for t in range(cfg['historical_first_target'],cfg['historical_last_target']+1):
            assert t<=1244;history=draws[:t-1];actual=set(draws[t-1]['numbers'])
            for mode in rules['window_modes']:
                train=history if mode=='expanding' else history[-rules['rolling_window']:]
                assert max(d['round'] for d in train)==t-1 and all(d['round']<t for d in train)
                scores,struct=e.fit(train,bank,rules);groups=e.candidates(scores,struct,bank,t,mode,rules);lines,trace=e.portfolio(groups,rules)
                hits=[len(set(q)&actual) for q in lines];ol=[len(set(a)&set(b)) for i,a in enumerate(lines) for b in lines[i+1:]]
                row={'decision_target':1245,'historical_target':t,'mode':mode,'training_start':train[0]['round'],'training_end':t-1,'training_rows':len(train),'training_semantic_sha256':e.canonical(train),'frozen_engine_sha256':sha(V4/'prospective_engine_v4.py'),'raw_data_sha256':cfg['raw_data_sha256'],'actual_historical_numbers':encoded(sorted(actual)),'line_G':encoded(lines[0]),'line_C':encoded(lines[1]),'line_S':encoded(lines[2]),'hits_G':hits[0],'hits_C':hits[1],'hits_S':hits[2],'mean_ticket_hits':sum(hits)/3,'portfolio_max_hits':max(hits),'portfolio_3plus':int(max(hits)>=3),'portfolio_4plus':int(max(hits)>=4),'pair_overlaps':encoded(ol),'mean_pair_overlap':sum(ol)/3,'union_coverage':len(set(x for q in lines for x in q)),'selection_trace':encoded(trace),'candidate_groups_sha256':hashlib.sha256(encoded(groups).encode()).hexdigest(),'target1245_actual':'NOT READ / NOT USED'}
                records[mode].append(row);append('MODE_BACKTEST_1245_V4.csv',row);fallbacks[mode]+=sum(r['fallback'] for r in trace)
            tickets,meta=random_portfolios(t,cfg['random_replicates_per_target'],cfg['random_seed'])
            mask=np.zeros(46,dtype=bool);mask[list(actual)]=True;hits=mask[tickets].sum(axis=2);mx=hits.max(axis=1);dist=np.bincount(hits.ravel(),minlength=7);R=len(tickets)
            ordered=np.sort(tickets.reshape(R,18),axis=1);coverage=1+(ordered[:,1:]!=ordered[:,:-1]).sum(axis=1)
            ol=np.stack([(tickets[:,i,:,None]==tickets[:,j,None,:]).any(axis=2).sum(axis=1) for i,j in [(0,1),(0,2),(1,2)]],axis=1)
            nr={'decision_target':1245,'historical_target':t,'baseline':'uniform_3_lists_37_candidates_frozen_portfolio_rule','replicates':R,'tickets':R*3,'seed_master':cfg['random_seed'],'seed_derived':meta['seed'],'mean_ticket_hits':float(hits.mean()),**{'hit_count_'+str(k):int(dist[k]) for k in range(7)},'ticket_2plus_rate':float((hits>=2).mean()),'ticket_3plus_rate':float((hits>=3).mean()),'ticket_4plus_rate':float((hits>=4).mean()),'portfolio_3plus_count':int((mx>=3).sum()),'portfolio_4plus_count':int((mx>=4).sum()),'portfolio_3plus_rate':float((mx>=3).mean()),'portfolio_4plus_rate':float((mx>=4).mean()),'portfolio_max_hits_mean':float(mx.mean()),**{'portfolio_max_count_'+str(k):int((mx==k).sum()) for k in range(7)},'mean_union_coverage':float(coverage.mean()),'mean_pair_overlap':float(ol.mean()),'fallback_count':meta['fallbacks'],'within_list_duplicate_resamples':meta['within_list_duplicate_resamples'],'simulation_tickets_sha256':meta['tickets_sha256'],'exact_ticket_expected_hits':.8,'target1245_actual':'NOT READ / NOT USED'}
            nullrows.append(nr);append('MODE_RANDOM_BASELINE_1245_V4.csv',nr)
            if (t-cfg['historical_first_target']+1)%10==0:log('PROGRESS targets='+str(t-cfg['historical_first_target']+1)+'/200; last_historical_target='+str(t)+'; all training cutoff=t-1; random portfolios per target='+str(R))
    finally:
        for f in sinks.values():f.close()
    stats=paired_statistics(vector(records['expanding']),vector(records['rolling300']),cfg)
    chosen,kind,selection,totals,blocks,randomtotal=decide(records,nullrows,stats,cfg)
    stats['relationships']={m:relationship_diagnostics(r) for m,r in records.items()}
    stats['all_200_target_random_deltas']={m:{k:totals[m][k]-(.8 if k=='mean_ticket_hits' else randomtotal[k]) for k in ['mean_ticket_hits','portfolio_3plus_rate','portfolio_4plus_rate','portfolio_max_hits_mean']} for m in totals}
    write_json('MODE_STATISTICAL_TESTS_1245_V4.json',stats)
    windows={str(n):{'modes':{m:summary(r[-n:]) for m,r in records.items()},'random':random_summary(nullrows[-n:]),'use':'overlapping descriptive windows, not independent evidence'} for n in [50,100,200]}
    write_json('MODE_SUMMARY_1245_V4.json',{'decision_target':1245,'historical_targets':[1045,1244],'modes':totals,'random':randomtotal,'windows':windows,'fallback_counts':fallbacks,'target1245_actual':'NOT READ / NOT USED','prospective_model_status':'REGISTERED_UNEVALUATED'})
    br=[]
    for i in range(4):
        lo=1045+i*50;hi=lo+49;rn=random_summary(nullrows[i*50:(i+1)*50])
        for mode in records:
            sm=blocks[mode][i];br.append({'decision_target':1245,'block':i+1,'first_target':lo,'last_target':hi,'mode':mode,'targets':50,'tickets':150,'mean_ticket_hits':sm['mean_ticket_hits'],'portfolio_3plus_count':sm['portfolio_3plus_count'],'portfolio_4plus_count':sm['portfolio_4plus_count'],'portfolio_3plus_rate':sm['portfolio_3plus_rate'],'portfolio_4plus_rate':sm['portfolio_4plus_rate'],'portfolio_max_hits_sum':sm['portfolio_max_hits_sum'],'hit_distribution':encoded(sm['hit_distribution_0_to_6']),'random_portfolio_3plus_rate':rn['portfolio_3plus_rate'],'random_portfolio_4plus_rate':rn['portfolio_4plus_rate'],'mean_hits_delta_to_exact_random':sm['mean_ticket_hits']-.8,'portfolio_3plus_delta_to_random':sm['portfolio_3plus_rate']-rn['portfolio_3plus_rate'],'portfolio_4plus_delta_to_random':sm['portfolio_4plus_rate']-rn['portfolio_4plus_rate']})
    write_csv('MODE_BLOCK_STABILITY_1245_V4.csv',br)
    contribution=[]
    for mode,r in records.items():
        for n in [50,100,200]:
            for mid in ['G','C','S']:
                hh=[int(q['hits_'+mid]) for q in r[-n:]]
                contribution.append({'decision_target':1245,'mode':mode,'model':'V4_'+mid,'recent_targets':n,'tickets':n,'mean_hits':sum(hh)/n,'hit_distribution':encoded([hh.count(k) for k in range(7)]),'ticket_3plus_count':sum(h>=3 for h in hh),'ticket_4plus_count':sum(h>=4 for h in hh),'unique_responsibility_for_portfolio_3plus':sum(int(q['hits_'+mid])>=3 and all(int(q['hits_'+other])<3 for other in ['G','C','S'] if other!=mid) for q in r[-n:])})
    write_csv('MODE_MODEL_CONTRIBUTIONS_1245_V4.csv',contribution)
    original=csvrows(V4/'predictions/1245/FINAL_THREE_LINES_1245_V4.csv');purchase=[r for r in original if r['mode']==chosen];assert len(purchase)==3
    write_csv('PRIMARY_PURCHASE_LINES_1245_V4.csv',purchase)
    decision={'target':1245,'training_cutoff':1244,'PRIMARY_PURCHASE_MODE_1245':chosen,'PRIMARY_PURCHASE_LINES_1245':[[int(r['no'+str(i)]) for i in range(1,7)] for r in purchase],'selection_type':kind,'selection_trace':selection,'historical_evaluation_targets':[1045,1244],'historical_target_count':200,'prediction_commit':cfg['prediction_commit'],'freeze_commit':cfg['freeze_commit'],'prediction_seal_sha256':cfg['prediction_seal_sha256'],'raw_data_sha256':cfg['raw_data_sha256'],'source_final_lines_sha256':sha(V4/'predictions/1245/FINAL_THREE_LINES_1245_V4.csv'),'prerun_lock_sha256':sha(HERE/'MODE_SELECTION_PRERUN_LOCK_1245_V4.json'),'all_200_target_summary':totals,'random_200_target_summary':randomtotal,'prospective_model_status':'REGISTERED_UNEVALUATED','new_target1245_numbers_generated':False,'actual_result':'NOT READ / NOT USED','created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'limitations':'Historical V4 design reused these data; mode selection is an additional pre-target decision, not untouched holdout validation or amendment of frozen future evaluation criteria.'}
    write_json('PRIMARY_PURCHASE_DECISION_1245_V4.json',decision)
    for r in lock['fixed_files']:assert sha(HERE/r['file'])==r['sha256']
    log('COMPARISON_SUCCESS: targets200; model portfolios400; random portfolios2000000; PRIMARY_PURCHASE_MODE_1245='+chosen+'; type='+kind+'; actual1245 NOT READ / NOT USED')
    log('PRIMARY_PURCHASE_LINES_1245='+encoded(decision['PRIMARY_PURCHASE_LINES_1245']));runlog.close()
    print(encoded({'historical_range':[1045,1244],'selected_primary_mode':chosen,'selection_type':kind,'summary':totals,'random':randomtotal,'decision_lines':decision['PRIMARY_PURCHASE_LINES_1245']}),flush=True)
if __name__=='__main__':main()
