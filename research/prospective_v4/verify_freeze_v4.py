"""Read-only verification of the new V4 freeze; never invokes V3."""
import argparse, csv, hashlib, json
from pathlib import Path

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def verify(root, expected_seal_sha=None):
    root=Path(root).resolve(); seal_path=root/'V4_FREEZE_SEAL.json'
    if expected_seal_sha and sha(seal_path)!=expected_seal_sha:raise ValueError('Seal SHA mismatch')
    seal=json.loads(seal_path.read_text(encoding='utf-8'))
    assert seal['version']=='prospective_v4' and seal['historical_v3_status']=='SEALED V3 GATE NOT PASSED'
    assert seal['future_result_read_before_freeze'] is False
    for record in seal['fixed_files']:
        path=root/record['path'];assert path.resolve().is_relative_to(root)
        assert sha(path)==record['sha256'] and path.stat().st_size==record['bytes'],str(path)
    manifest=list(csv.DictReader((root/'SHA256_MANIFEST_V4.csv').open(encoding='utf-8',newline='')))
    for r in manifest:assert sha(root/r['path'])==r['sha256']
    assert {r['path'] for r in manifest}=={r['path'] for r in seal['fixed_files'] if r['path']!='SHA256_MANIFEST_V4.csv'}
    data=list(csv.DictReader((root/'DATA_MANIFEST_V4.csv').open(encoding='utf-8',newline='')))
    for r in data:
        if r['origin']=='github_main':assert sha(root.parents[1]/r['repository_path'])==r['sha256'],r['repository_path']
    model_ids={r['model_id'] for r in csv.DictReader((root/'MODEL_MANIFEST_V4.csv').open(encoding='utf-8',newline=''))}
    rules=json.loads((root/'RULES_V4.json').read_text())
    assert model_ids==set(rules['active_model_ids'])
    return seal

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',default=str(Path(__file__).parent));p.add_argument('--expected-seal-sha')
    a=p.parse_args();s=verify(a.root,a.expected_seal_sha)
    print(json.dumps({'V4_FREEZE':'PASS','fixed_files':len(s['fixed_files']),'V3':'SEALED V3 GATE NOT PASSED','base_commit':s['base_commit']},ensure_ascii=False))
