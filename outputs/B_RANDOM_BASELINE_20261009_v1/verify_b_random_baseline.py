"""Validate aggregates, matched targets, reference hashes and fixed-seed replay."""
from pathlib import Path
import csv, hashlib, importlib.util, json, math, sys, datetime
sys.dont_write_bytecode=True
A=Path(__file__).resolve().parent
R=A.parent/'B_MODEL_REPRODUCTION_20261009_v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def close(x,y):return math.isclose(float(x),float(y),rel_tol=1e-10,abs_tol=1e-12)
def check():
    cfg=json.loads((A/'RUN_CONFIG.json').read_text(encoding='utf-8')); seal=json.loads((A/'RUN_PLAN_SEAL.json').read_text(encoding='utf-8'))
    for name,value in seal['file_sha256'].items():assert sha(A/name)==value
    for name,value in cfg['reference_sha256'].items():assert sha(R/name)==value
    run=json.loads((A/'ACTUAL_EXECUTION_RESULT.json').read_text(encoding='utf-8'));assert run['exit_code']==0 and run['stderr_bytes']==0
    meta=json.loads((A/'RUN_METADATA.json').read_text(encoding='utf-8'));assert meta['mc_ticket_comparisons']==3500000 and meta['random_seed']==20261009
    raw=read(R/'EXECUTED_INPUT_lotto_data.csv');assert [int(r['round']) for r in raw]==list(range(1,1245))
    targets=[t for lo,hi in cfg['blocks'] for t in range(lo,hi+1)]; rows=read(A/'MC_TARGET_AGGREGATES.csv')
    assert [int(r['target_round']) for r in rows]==targets and len(rows)==350 and max(targets)==1200
    summary=read(A/'MC_BLOCK_AND_POOLED_SUMMARY.csv');assert len(summary)==8
    for s in summary:
        rr=rows if s['interval'].startswith('POOLED') else [r for r in rows if int(s['start_round'])<=int(r['target_round'])<=int(s['end_round'])]
        counts=[sum(int(r[f'hits_{k}_count']) for r in rr) for k in range(7)];n=sum(counts)
        mean=sum(k*c for k,c in enumerate(counts))/n;var=sum(k*k*c for k,c in enumerate(counts))/n-mean*mean
        assert n==len(rr)*10000==int(s['random_ticket_comparisons'])
        assert close(mean,s['mean_hits']) and close(var,s['variance_hits_population'])
        assert close(math.sqrt(var/n),s['mean_mc_se'])
        for k in range(7):assert int(s[f'hits_{k}_count'])==counts[k] and close(s[f'hits_{k}_rate'],counts[k]/n)
        for k in range(2,7):assert close(s[f'rate_ge_{k}'],sum(counts[k:])/n)
    frozen=json.loads((A/'B_REPRODUCTION_REFERENCE_FROZEN.json').read_text(encoding='utf-8'));classes=read(R/'b_model_classification.csv')
    comparisons=read(A/'B_VS_RANDOM_POOLED.csv');assert len(comparisons)==8
    for c in classes:
        m=next(r for r in comparisons if r['model']==c['model'])
        assert close(c['pooled_mean_hits'],m['mean_hits']) and close(c['pooled_rate_ge_2'],m['rate_ge_2'])
        assert frozen['classification'][c['model']]==c['classification'] and int(m['b_ticket_count'])==350
        for k in range(7):assert int(c[f'hits_{k}_count'])==int(m[f'hits_{k}_count'])
    assert len(read(A/'B_VS_RANDOM_BLOCKS.csv'))==56
    unresolved=json.loads((A/'UNRESOLVED_HISTORICAL_RESULT.json').read_text(encoding='utf-8'));assert unresolved['excluded_from_evaluation'] and not unresolved['merged_or_averaged']
    spec=importlib.util.spec_from_file_location('mc_replay',A/'run_b_random_baseline.py');engine=importlib.util.module_from_spec(spec);spec.loader.exec_module(engine)
    streams={int(r['target_round']):r for r in read(A/'RANDOM_TICKET_STREAM_HASHES.csv')}
    replays=[]
    for lo,hi in cfg['blocks']:
        actual=[int(raw[lo-1][f'no{i}']) for i in range(1,7)]
        counts,digest,rejected=engine.simulate_target(cfg['random_seed'],lo,10000,actual)
        record=next(r for r in rows if int(r['target_round'])==lo)
        assert digest==streams[lo]['sorted_int16_le_stream_sha256'] and rejected==int(streams[lo]['rejected_iid_sextuples'])
        assert counts.tolist()==[int(record[f'hits_{k}_count']) for k in range(7)]
        replays.append(dict(target_round=lo,stream_sha256=digest,counts_match=True,tickets=10000))
    result=dict(status='MONTE_CARLO_VERIFIED',checks='PASS',verified_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),official_random_comparisons=3500000,official_seed=20261009,matched_historical_targets=350,blocks=cfg['blocks'],target_1245_used=False,new_recommendations=False,original_B_hashes_match=True,B_classifications_unchanged=True,independent_aggregate_checks=True,determinism_verification_only_not_new_official_run=dict(targets=replays,tickets_replayed=70000),interpretation='INSUFFICIENT EVIDENCE of predictive superiority;Monte Carlo precision is distinct from350round B performance uncertainty.')
    return result
if __name__=='__main__':
    result=check()
    if '--write' in sys.argv:
        result['artifact_sha256']={p.name:sha(p) for p in sorted(A.iterdir()) if p.is_file() and p.name not in ['FINAL_VERIFICATION.json','SHA256_MANIFEST.csv']}
        with (A/'FINAL_VERIFICATION.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    if (A/'SHA256_MANIFEST.csv').exists():
        manifest=read(A/'SHA256_MANIFEST.csv')
        for r in manifest:assert sha(A/r['file'])==r['sha256'] and (A/r['file']).stat().st_size==int(r['bytes'])
        assert {r['file'] for r in manifest}=={p.name for p in A.iterdir() if p.is_file() and p.name!='SHA256_MANIFEST.csv'}
    print(json.dumps(result,indent=2))
