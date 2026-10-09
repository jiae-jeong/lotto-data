from pathlib import Path
import csv, hashlib, json
A=Path(__file__).resolve().parent
manifest=list(csv.DictReader((A/'AUDIT_SHA256.csv').open(encoding='utf-8-sig',newline='')))
for r in manifest:
    p=A/r['file']
    assert p.is_file() and p.stat().st_size==int(r['bytes'])
    assert hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256'],r['file']
listed={r['file'] for r in manifest}
actual={p.relative_to(A).as_posix() for p in A.rglob('*') if p.is_file() and p.name!='AUDIT_SHA256.csv' and '__pycache__' not in p.parts}
assert listed==actual
core=json.loads((A/'CORE_VERIFICATION.json').read_text(encoding='utf-8'))
assert core['actual_unmodified_run'] and core['exit_code']==0 and core['records']==33408 and core['csv_reproduced_byte_identical']==4
data=list(csv.DictReader((A/'EXECUTED_INPUT_lotto_data.csv').open(encoding='utf-8-sig',newline='')))
assert [int(r['round']) for r in data]==list(range(1,1245))
for r in data:
    ns=[int(r['no'+str(i)]) for i in range(1,7)]; bonus=int(r['bonus'])
    assert len(set(ns))==6 and all(1<=n<=45 for n in ns) and 1<=bonus<=45 and bonus not in ns
rows=list(csv.DictReader((A/'b_model_predictions.csv').open(encoding='utf-8-sig',newline='')))
assert len(rows)==33408
assert all(int(r['target_round'])==int(r['training_through_round'])+1 and int(r['target_round'])<=1244 for r in rows)
assert not core['actual_1245_read'] and not core['new_1245_predictions_generated']
print(json.dumps(dict(status='PASS',manifest_files=len(manifest),raw_rows=len(data),max_raw_round=1244,B_output_records=len(rows),actual_1245='NOT READ / NOT USED',new_1245_predictions=False),indent=2))
