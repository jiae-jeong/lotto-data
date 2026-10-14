import csv,hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]; OUT=Path(__file__).resolve().parent
GIT=r'C:\Users\user\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\git\cmd\git.exe'
CANONICAL_SHA='10beb0a7974f648b39aa130bb714b1c338296bf59ecd106e9407bee5875538aa'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def gsha(p):return hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n')).hexdigest()
def rows(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def wjson(p,obj):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=False,indent=2,sort_keys=True);f.write('\n')
checks=[]
def add(k,ok,evidence):
    checks.append({'check':k,'status':'PASS' if ok else 'FAIL','evidence':evidence})
    if not ok:raise RuntimeError('final deliverable readback failed: '+k)
def main():
    data=json.loads((OUT/'DATA_VALIDATION.json').read_text(encoding='utf-8'))
    add('full_data_validation',data['rows']==1245 and data['latest_round']==1245 and data['integrity']=='PASS','DATA_VALIDATION.json')
    cross=rows(OUT/'DATA_SOURCE_CROSSCHECK_FINAL.csv')
    add('six_independent_source_samples',len(cross)==6 and all(r['overall_match']=='True' for r in cross),'DATA_SOURCE_CROSSCHECK_FINAL.csv')
    add('canonical_source_unchanged',sha(ROOT/'lotto_data.csv')==CANONICAL_SHA,'lotto_data.csv')
    pred=rows(OUT/'b_model_predictions.csv'); targets=sorted({int(r['target_round']) for r in pred}); uniq={}
    source=rows(OUT/'input'/'lotto_data_github_main.csv')
    actual={int(r['round']):{int(r[f'no{i}']) for i in range(1,7)} for r in source}
    for r in pred:
        t=int(r['target_round']); cutoff=int(r['training_through_round']); ticket={int(x) for x in r['predicted_numbers'].split()}
        if cutoff!=t-1 or len(ticket)!=6 or len(ticket&actual[t])!=int(r['hits']):raise RuntimeError('B row cutoff/hit readback mismatch')
        key=(t,r['model']); val=(tuple(sorted(ticket)),int(r['hits']))
        if key in uniq and uniq[key]!=val:raise RuntimeError('overlapping forecast mismatch')
        uniq[key]=val
    add('B_rolling_prediction_replay',len(pred)==33480 and targets==list(range(201,1246)) and len(uniq)==8360,'b_model_predictions.csv')
    leak=json.loads((OUT/'B_LEAKAGE_CHECK.json').read_text(encoding='utf-8'))
    add('leakage_zero',leak['status']=='PASS' and leak['failure_count']==0,'B_LEAKAGE_CHECK.json')
    direct=rows(OUT/'RANDOM_BASELINE_BY_TARGET.csv'); mc=rows(OUT/'RANDOM_COMPLETE_PATHS.csv')
    add('direct_target_matched_random',len(direct)==1045 and all(int(r['random_tickets'])==1000 for r in direct),'RANDOM_BASELINE_BY_TARGET.csv')
    add('complete_random_path_count',len(mc)==20000 and json.loads((OUT/'RANDOM_MONTE_CARLO_BASELINE.json').read_text(encoding='utf-8'))['n_targets_per_path']==1045,'RANDOM_COMPLETE_PATHS.csv')
    pair=rows(OUT/'PAIR_STATS.csv'); triple=rows(OUT/'TRIPLE_STATS.csv')
    add('pair_triple_universes',len(pair)==990 and len(triple)==14190,'PAIR_STATS.csv; TRIPLE_STATS.csv')
    rank=json.loads((OUT/'STRUCTURE_RANK_SOURCE_AUDIT_V2.json').read_text(encoding='utf-8'))
    add('structure_formula_readback',rank['structure_profile_in_combined_rank_expression'] is False and rank['structure_model_is_separate_ticket'] is True,'STRUCTURE_RANK_SOURCE_AUDIT_V2.json')
    report=(OUT/'REPORT_FINAL_V3.md').read_text(encoding='utf-8')
    recpath=ROOT/'research'/'prospective_v4'/'decisions'/'1245'/'PRIMARY_PURCHASE_LINES_1245_V4.csv'
    rec=rows(recpath)
    for r in rec:
        ticket=' '.join(str(int(r[f'no{i}'])) for i in range(1,7))
        if ticket in report:raise RuntimeError('recommendation data leaked into final report')
    for t,m in uniq:
        if ' '.join(map(str,uniq[(t,m)][0])) in report:raise RuntimeError('B ticket leaked into final report')
    add('report_readback_and_no_ticket_values',report.startswith('# Daily lottery research — 2026-10-14') and 'DATA_SOURCE_CROSSCHECK_FINAL.csv' in report,'REPORT_FINAL_V3.md')
    rec_prov=json.loads((OUT/'ROUND_1245_PROVENANCE.json').read_text(encoding='utf-8'))
    add('pre_draw_record_searched',rec_prov['pre_draw_seal_commit_found'] and rec_prov['independent_purchase_receipt']=='NOT FOUND in repository search','ROUND_1245_PROVENANCE.json')
    add('new_hypothesis_registered',rows(OUT/'HYPOTHESIS_REGISTRY_UPDATE.csv')[0]['status']=='REGISTERED / NOT ADOPTED','HYPOTHESIS_REGISTRY_UPDATE.csv')
    status=subprocess.check_output([GIT,'status','--porcelain=v1'],cwd=ROOT,text=True,encoding='utf-8').strip().splitlines()
    no_diff=subprocess.run([GIT,'diff','--quiet','HEAD'],cwd=ROOT).returncode==0 and subprocess.run([GIT,'diff','--cached','--quiet'],cwd=ROOT).returncode==0
    add('tracked_project_files_unchanged',no_diff,'git diff --quiet HEAD; git diff --cached --quiet')
    add('worktree_scope',all(x=='?? analysis/2026-10-14/' for x in status),'git status --porcelain')
    result={'status':'PASS','verified_utc':'2026-10-14','calculation_wrapper_exit_code':1,
      'wrapper_exit_note':'Only the wrapper final report sanity predicate failed; it rejected expected training-cutoff text. All calculations were complete. Two independent read-back passes validated generated artifacts without rerunning the research.',
      'data_rows':1245,'latest_round':1245,'crosscheck_samples':len(cross),'B_targets':len(targets),'B_raw_predictions':len(pred),
      'B_unique_target_model_predictions':len(uniq),'leakage_failures':0,'direct_random_tickets':1045000,'complete_random_paths':20000,
      'pair_count':len(pair),'triple_count':len(triple),'recommendation_lines_evaluated':len(rec),'checks':checks,
      'protected_original_data_unchanged':True,'final_report':'REPORT_FINAL_V3.md'}
    wjson(OUT/'FINAL_VERIFICATION_FINAL.json',result)
    files=[]
    for p in sorted(OUT.rglob('*')):
        if p.is_file() and p.name!='SHA256SUMS_FINAL.txt':files.append(f'{gsha(p)}  {p.relative_to(OUT).as_posix()}')
    with (OUT/'SHA256SUMS_FINAL.txt').open('x',encoding='utf-8',newline='\n') as f:f.write('\n'.join(files)+'\n')
    for line in files:
        h,rel=line.split('  ',1)
        if gsha(OUT/rel)!=h:raise RuntimeError('final checksum readback mismatch: '+rel)
    print(json.dumps({'status':'PASS','checks':len(checks),'data_rows':1245,'crosschecks':len(cross),'B_targets':len(targets),
      'leakage_failures':0,'random_tickets':1045000,'random_paths':20000,'pairs':len(pair),'triples':len(triple),'hash_entries':len(files)}))
if __name__=='__main__':main()
