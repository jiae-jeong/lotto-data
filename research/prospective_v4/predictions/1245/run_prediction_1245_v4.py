"""Write-once observation wrapper; model computations are exclusively frozen V4.
The profile hook only observes function returns, without replacing model functions.
Verification replays are explicitly NOT additional official runs.
"""
import argparse, csv, hashlib, importlib.util, itertools, json, math, platform, sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
sys.dont_write_bytecode=True
FREEZE_COMMIT='746efc843d53dff4e61394e26d458ea3f50c93e4'
FREEZE_SHA='6a018e3036187a26ac9bcffda9fd7379d65d86cde84514faa08f4ea349b0f4bb'
RAW_SHA='243cd17e6b97a2d96709ddfc689a068038669341a52dcc0743c141d309e43b9f'

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write_json(p,obj):
    with Path(p).open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,indent=2,sort_keys=True);f.write('\n')
def write_csv(p,rows):
    assert rows
    with Path(p).open('x',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
def encoded(obj):return json.dumps(obj,separators=(',',':'),sort_keys=True)
def run(data,out,kind):
    assert kind in ('official','determinism_verification_only')
    source=Path(__file__).resolve().parents[2]
    sys.path.insert(0,str(source))
    spec=importlib.util.spec_from_file_location('frozen_engine',source/'prospective_engine_v4.py')
    e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
    assert platform.python_version_tuple()[:2]==('3','12'),'Frozen candidate RNG specifies Python 3.12'
    assert digest(data)==RAW_SHA
    rules=json.loads((source/'RULES_V4.json').read_text(encoding='utf-8'))
    models=list(csv.DictReader((source/'MODEL_MANIFEST_V4.csv').open(encoding='utf-8',newline='')))
    metadata={r['model_id']:r for r in models}
    assert set(metadata)==set(rules['active_model_ids'])
    captured=[]
    engine_file=str(source/'prospective_engine_v4.py')
    def observe(frame,event,value):
        if event=='return' and frame.f_code.co_name=='fit' and frame.f_code.co_filename==engine_file:
            scores,struct=value
            captured.append({'scores':scores,'structure':struct,'train':frame.f_locals['train']})
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    assert not (out/'ENGINE_PREDICTION_1245_V4.json').exists(),'Refuse a second run at an existing output'
    started=datetime.now(timezone.utc).isoformat()
    sys.setprofile(observe)
    try:result=e.predict(data,1245,out/'ENGINE_PREDICTION_1245_V4.json',FREEZE_SHA)
    finally:sys.setprofile(None)
    assert len(captured)==len(rules['window_modes'])==2
    write_json(out/'FROZEN_SCORE_CAPTURE_1245_V4.json',{'target':1245,'training_cutoff':1244,'actual_result':'NOT READ / NOT USED','modes':{mode:{'training_start':cap['train'][0]['round'],'training_end':cap['train'][-1]['round'],'number_scores':cap['scores'],'structure_bank_scores':[{'numbers':list(q),'score':cap['structure'][q]} for q in sorted(cap['structure'])]} for mode,cap in zip(rules['window_modes'],captured)}})
    node_rows=[];model_rows=[];candidate_rows=[];ticket_rows=[];final_rows=[];trace_rows=[];diagnostics=[];audit={}
    common={'target':1245,'training_cutoff':1244,'version':'prospective_v4','status':'REGISTERED_UNEVALUATED','raw_data_sha256':RAW_SHA,'freeze_commit':FREEZE_COMMIT,'freeze_seal_sha256':FREEZE_SHA}
    for mode,cap in zip(rules['window_modes'],captured):
        rec=result['modes'][mode];train=cap['train'];scores=cap['scores'];struct=cap['structure'];groups=rec['candidates']
        assert rec['training_end']==1244 and train[-1]['round']==1244
        assert rec['training_start']==(1 if mode=='expanding' else 945)
        freq=Counter(x for d in train for x in d['numbers'])
        pairs=Counter(q for d in train for q in itertools.combinations(d['numbers'],2))
        triples=Counter(q for d in train for q in itertools.combinations(d['numbers'],3))
        orders={mid:sorted(range(1,46),key=lambda x:(-ss[x],x)) for mid,ss in scores.items()}
        rank_struct={q:i+1 for i,q in enumerate(sorted(struct,key=lambda q:(-struct[q],q)))}
        null_seed=int.from_bytes(hashlib.sha256(f"{rules['null_seed']}|1245|{mode}".encode()).digest()[:8],'big')
        def ticket_score(mid,q):return sum(scores[mid][x] for x in q) if mid in scores else struct[tuple(q)] if mid=='V4_S' else None
        def score_type(mid):return 'sum_node_scores' if mid in scores else 'eight_feature_log_likelihood' if mid=='V4_S' else 'uniform_generation_order_no_learned_score'
        for mid in rules['active_model_ids']:
            group=groups[mid];pred=tuple(rec['model_predictions'][mid])
            assert len(group)==37 and len(set(map(tuple,group)))==37
            audit[mode+'|'+mid]={'candidates':37,'duplicates_within_model':0,'training_start':rec['training_start'],'training_end':1244}
            for x in range(1,46):
                ss=scores[mid][x] if mid in scores else (6/45 if mid=='V4_U' else '')
                nr=orders[mid].index(x)+1 if mid in orders else ''
                node_rows.append({**common,'mode':mode,'model_id':mid,'model_version':metadata[mid]['version'],'number':x,'score':ss,'number_rank':nr,'score_kind':'frozen_learned_node_score' if mid in scores else 'uniform_inclusion_probability_not_rank' if mid=='V4_U' else 'NOT_DEFINED_TICKET_ONLY_MODEL','in_model_prediction':int(x in pred)})
            model_rows.append({**common,'mode':mode,'model_id':mid,'model_version':metadata[mid]['version'],'training_start':rec['training_start'],'training_rows':len(train),**{'no'+str(i+1):x for i,x in enumerate(pred)},'ticket_score':ticket_score(mid,pred),'score_kind':score_type(mid),'candidate_rank':list(map(tuple,group)).index(pred)+1,'number_ranking':encoded(orders.get(mid,[])),'top_numbers_by_score':encoded(orders[mid][:6]) if mid in orders else 'NOT_DEFINED_NODE_RANKING','seed':null_seed if mid=='V4_U' else rules['candidate_bank']['seed'] if mid=='V4_S' else 'NO_RANDOM_SEED','seed_derivation':f"SHA256({rules['null_seed']}|1245|{mode}) first8 big-endian" if mid=='V4_U' else 'fixed_candidate_bank' if mid=='V4_S' else 'deterministic_counts'})
            for rank,q in enumerate(group,1):
                q=tuple(q);cid=f'{mode}:{mid}:{rank:02d}'
                row={**common,'mode':mode,'model_id':mid,'candidate_id':cid,'candidate_rank':rank,**{'no'+str(i+1):x for i,x in enumerate(q)},'ticket_score':ticket_score(mid,q),'score_kind':score_type(mid),'bank_rank':rank_struct[q] if mid=='V4_S' else '','selected_portfolio_line':next((i+1 for i,(line,tr) in enumerate(zip(rec['portfolio'],rec['selection_trace'])) if tuple(line)==q and tr['model']==mid),'')}
                candidate_rows.append(row)
                if mid!='V4_S':ticket_rows.append(row)
                rel=e.relations(q,train[-1]['numbers'])
                pair_details=[]
                for a,b in rel['pairs']:
                    ex=(5/6)*(45/44)*freq[a]*freq[b]/len(train)
                    pair_details.append({'pair':[a,b],'training_count':pairs[(a,b)],'expected_count_frozen_pair_formula':ex,'residual_z':(pairs[(a,b)]-ex)/math.sqrt(max(ex,1e-12))})
                diagnostics.append({**common,'mode':mode,'model_id':mid,'candidate_id':cid,'candidate_rank':rank,'selected_portfolio_line':row['selected_portfolio_line'],'diagnostic_only':True,'veto_applied':False,'numbers':encoded(q),'pairs':encoded(pair_details),'triples':encoded([{'triple':list(t),'training_count':triples[t]} for t in rel['triples']]),'gaps':encoded(rel['gaps']),'consecutive_count':rel['consecutive'],'odd':rel['odd'],'even':6-rel['odd'],'low':rel['low'],'high':rel['high'],'sum':rel['sum'],'sum_bin':rel['sum_bin'],'bands_1_10_11_20_21_30_31_40_41_45':encoded(rel['bands']),'last_digits':encoded(rel['last_digits']),'ending_counts':encoded(dict(sorted(Counter(x%10 for x in q).items()))),'ending_repeat_excess':rel['end_repeat'],'previous_draw_overlap':rel['overlap'],'cluster_count':rel['cluster']})
        for q in sorted(struct,key=lambda q:(-struct[q],q)):
            ticket_rows.append({**common,'mode':mode,'model_id':'V4_S','candidate_id':f'{mode}:V4_S:bank:{rank_struct[q]:05d}','candidate_rank':rank_struct[q],**{'no'+str(i+1):x for i,x in enumerate(q)},'ticket_score':struct[q],'score_kind':'eight_feature_log_likelihood','bank_rank':rank_struct[q],'selected_portfolio_line':next((i+1 for i,(line,tr) in enumerate(zip(rec['portfolio'],rec['selection_trace'])) if tuple(line)==q and tr['model']=='V4_S'),'')})
        chosen=[]
        for line_no,(q,tr) in enumerate(zip(rec['portfolio'],rec['selection_trace']),1):
            q=tuple(q);mid=tr['model'];group=list(map(tuple,groups[mid]));rel=e.relations(q,train[-1]['numbers'])
            overlaps=[len(set(q)&set(old)) for old in chosen]
            final_rows.append({**common,'mode':mode,'line':line_no,'model_id':mid,'candidate_id':f"{mode}:{mid}:{tr['candidate_rank']:02d}",'candidate_rank':tr['candidate_rank'],'ticket_score':ticket_score(mid,q),'score_kind':score_type(mid),'fallback':tr['fallback'],**{'no'+str(i+1):x for i,x in enumerate(q)},'overlaps_with_previous_lines':encoded(overlaps),'pair_intersection_with_other_lines':encoded([sorted(set(q)&set(other)) for j,other in enumerate(rec['portfolio']) if j!=line_no-1]),'gaps':encoded(rel['gaps']),'consecutive_count':rel['consecutive'],'odd':rel['odd'],'even':6-rel['odd'],'low':rel['low'],'high':rel['high'],'sum':rel['sum'],'bands':encoded(rel['bands']),'last_digits':encoded(rel['last_digits']),'ending_repeat_excess':rel['end_repeat'],'cluster_count':rel['cluster'],'diagnostic_only':True,'veto_applied':False})
            available=[t for t in group if t not in chosen]
            acceptable=[t for t in available if all(len(set(t)&set(old))<=rules['portfolio']['maximum_pair_overlap'] for old in chosen)]
            for rank,t in enumerate(group,1):
                ol=[len(set(t)&set(old)) for old in chosen]
                trace_rows.append({**common,'mode':mode,'portfolio_line':line_no,'model_id':mid,'candidate_rank':rank,'candidate_id':f'{mode}:{mid}:{rank:02d}','numbers':encoded(t),'score':ticket_score(mid,t),'earlier_lines':encoded(chosen),'overlaps':encoded(ol),'duplicate_of_earlier_line':t in chosen,'acceptable':t in acceptable,'selected':t==q,'fallback_used_for_line':tr['fallback'],'reason':'selected_by_frozen_fallback' if t==q and tr['fallback'] else 'highest_ranked_acceptable' if t==q else 'duplicate_ticket' if t in chosen else 'overlap_above_2' if t not in acceptable else 'lower_candidate_rank','fallback_key':encoded([sum(ol),max(ol or [0]),rank-1,t])})
            assert tr['fallback']==(not bool(acceptable))
            chosen.append(q)
        assert len(set(chosen))==3
        audit[mode+'|portfolio']={'distinct_tickets':3,'pair_intersections':rec['overlaps'],'pair_jaccard':[len(set(a)&set(b))/len(set(a)|set(b)) for a,b in itertools.combinations(chosen,2)],'union_coverage':len(set(itertools.chain.from_iterable(chosen))),'fallback_count':sum(t['fallback'] for t in rec['selection_trace']),'structure_veto_count':0}
        all_candidates=[tuple(q) for g in groups.values() for q in g]
        audit[mode+'|cross_model']={'total':len(all_candidates),'unique':len(set(all_candidates)),'shared_candidates_descriptive_only':len(all_candidates)-len(set(all_candidates))}
    write_csv(out/'MODEL_PREDICTIONS_1245_V4.csv',model_rows)
    write_csv(out/'NUMBER_SCORES_1245_V4.csv',node_rows)
    write_csv(out/'CANDIDATES_1245_V4.csv',candidate_rows)
    write_csv(out/'TICKET_SCORES_1245_V4.csv',ticket_rows)
    write_csv(out/'FINAL_THREE_LINES_1245_V4.csv',final_rows)
    write_csv(out/'SELECTION_TRACE_1245_V4.csv',trace_rows)
    write_csv(out/'STRUCTURE_DIAGNOSTICS_1245_V4.csv',diagnostics)
    write_json(out/'CANDIDATE_AUDIT_1245_V4.json',{**common,'audits':audit})
    baseline={'target':1245,'training_cutoff':1244,'status':'REGISTERED_UNEVALUATED','source_file':'../../RANDOM_BASELINE_V4.json','source_sha256':digest(source/'RANDOM_BASELINE_V4.json'),'exact_pmf':{str(k):{'numerator':math.comb(6,k)*math.comb(39,6-k),'denominator':math.comb(45,6),'probability':math.comb(6,k)*math.comb(39,6-k)/math.comb(45,6)} for k in range(7)},'expected_hits':0.8,'actual_result':'NOT READ / NOT USED','observed_performance':None,'superiority_claim':False,'portfolio_dependence':'three lines are not independent; no independent-line win claim'}
    write_json(out/'RANDOM_BASELINE_1245_V4.json',baseline)
    summary={**common,'official_run_generated_at_utc':started,'engine_created_at_utc':result['created_at_utc'],'execution_kind':kind,'actual_result':'NOT READ / NOT USED','result_rows_read':False,'actual_numbers':None,'frozen_engine_result_file':'ENGINE_PREDICTION_1245_V4.json','frozen_engine_result_sha256':digest(out/'ENGINE_PREDICTION_1245_V4.json'),'modes':result['modes'],'model_ids':rules['active_model_ids'],'model_versions':{mid:metadata[mid]['version'] for mid in metadata},'python_version':platform.python_version(),'frozen_engine_sha256':digest(source/'prospective_engine_v4.py'),'rules_sha256':digest(source/'RULES_V4.json'),'model_manifest_sha256':digest(source/'MODEL_MANIFEST_V4.csv'),'run_command':[sys.executable,str(Path(__file__).resolve()),'--data',str(Path(data).resolve()),'--output-dir',str(out.resolve()),'--execution-kind',kind],'uniform_seed_formula':f"first8 big-endian SHA256({rules['null_seed']}|1245|mode)",'structure_bank_seed':rules['candidate_bank']['seed'],'notes':'One portfolio per mode; no primary mode invented. Structure diagnostics never veto. Score-only wrapper does not change frozen functions.'}
    write_json(out/'PREDICTION_1245_V4.json',summary)
    readme=f'''# V4 prediction registration: draw 1245

Status: REGISTERED_UNEVALUATED. Actual result: NOT READ / NOT USED.
Freeze commit: {FREEZE_COMMIT}
Freeze seal SHA-256: {FREEZE_SHA}
Data cutoff: 1244; raw SHA-256: {RAW_SHA}.
Execution kind: {kind}. Generated UTC: {started}.

The immutable frozen engine was called once in this invocation for both registered modes and all eight models. A Python profile return observer captures scores without replacing or modifying model computations. Reproduction invocation must use determinism_verification_only in a separate output directory; it is not another official selection.

Both expanding and rolling300 portfolios are preserved because the freeze defines one three-line portfolio per mode and does not name a primary buying mode. This prediction never replaces historical V3 candidate lines. Portfolio order G, C, S; equal weights; overlap <=2 priority and frozen fallback. All structure diagnostics are descriptive, with no veto or manual substitutions.

Number scores/ranks are defined for F/G/C/M/P/T. U has equal inclusion probability and seed generation order, not a learned number ranking. S ranks tickets, not individual numbers; those undefined fields remain explicit. Full 10,000-bank S ticket scores are preserved for each mode.

Artifacts require raw/freeze hashes and independent verification before publication. No actual target outcome input or score is present. Publication commit/time and independent pre-draw eligibility are recorded externally to avoid circular Git/hash references. Commit timestamps alone are not independent deadline proof. V3 remains SEALED V3 GATE NOT PASSED.

Reproduction example: python run_prediction_1245_v4.py --data <frozen-repository>/lotto_data.csv --output-dir <fresh-verification-directory> --execution-kind determinism_verification_only
'''
    with (out/'README_1245_V4.md').open('x',encoding='utf-8',newline='\n') as f:f.write(readme)
    print(encoded({'execution_kind':kind,'target':1245,'models':8,'modes':2,'model_predictions':len(model_rows),'candidate_tickets':len(candidate_rows),'portfolio_lines':len(final_rows),'scores':len(node_rows),'ticket_scores':len(ticket_rows),'status':'REGISTERED_UNEVALUATED','actual':'NOT READ / NOT USED','portfolios':{mode:result['modes'][mode]['portfolio'] for mode in rules['window_modes']}}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data',required=True);p.add_argument('--output-dir',required=True);p.add_argument('--execution-kind',required=True,choices=['official','determinism_verification_only']);a=p.parse_args();run(a.data,a.output_dir,a.execution_kind)
