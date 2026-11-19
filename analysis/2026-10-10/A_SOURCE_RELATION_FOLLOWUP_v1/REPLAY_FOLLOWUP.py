"""Workspace reproduction adapter; no signal/statistical rule modifications."""
from pathlib import Path
import argparse, contextlib, csv, hashlib, importlib.util, json, sys

p=argparse.ArgumentParser()
p.add_argument('--root',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
args=p.parse_args()
root=args.root.resolve(); dest=args.output.resolve()
assert not dest.exists(), 'Choose a new output directory. Existing files cannot be overwritten.'
source=root/'outputs/A_SOURCE_RELATION_FOLLOWUP_20261010_v1'
spec=importlib.util.spec_from_file_location('followup',root/'work/a_source_relation_followup_20261010.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
assert hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest()==hashlib.sha256((source/'RUN_FOLLOWUP.py').read_bytes()).hexdigest()
m.ROOT=root;m.OUT=dest;m.WT=root/'work/primary_mode_1245_v4_clean_20261009';m.PRIOR=root/'outputs/A_ERRORLOOP_C_RESEARCH_20261009_v2'
m.STATE=root/'work/A_SOURCE_RELATION_FOLLOWUP_STATE_20261010_v1.json';m.REPLAY=True
dest.mkdir(exist_ok=False);m.g.LOG=dest/'GIT_READONLY_REPLAY.log'
for name in ['FOLLOWUP_CONFIG.json','FOLLOWUP_PROTOCOL.md','RUN_FOLLOWUP.py','OLDER_CHAT_EVIDENCE_INTAKE.json','EXECUTION_PLAN_SEAL.json']:
    with (dest/name).open('xb') as f:f.write((source/name).read_bytes())
with (dest/'STDOUT.log').open('x',encoding='utf-8') as stdout,(dest/'STDERR.log').open('x',encoding='utf-8') as stderr:
    with contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(stderr):m.research();m.verify()
names=['PAIR_TRIPLE_MULTIPLICITY_ALL.csv','MULTIPLICITY_SUMMARY.csv','QUOTED_RELATION_COUNT_COMPARISON.csv','TOP10_RELATION_WALKFORWARD_SELECTED.csv','TOP10_RELATION_WALKFORWARD_DAILY.csv','TOP10_RELATION_WALKFORWARD_SUMMARY.csv','POSTDRAW_QUOTED_1244_ARITHMETIC.json','POSTDRAW_QUOTED_1244_NUMBER_MATCH.csv','HYPOTHESIS_REGISTRY_ADDENDUM.csv','STATUS_CLASSIFICATION.json','DATA_INTEGRITY.json']
checks=[]
for n in names:
    h=lambda x:hashlib.sha256(x.read_bytes()).hexdigest()
    assert h(source/n)==h(dest/n), n
    checks.append(dict(file=n,official_sha256=h(source/n),replay_sha256=h(dest/n),status='BYTE_IDENTICAL'))
with (dest/'DETERMINISM_VERIFICATION.json').open('x',encoding='utf-8') as f:json.dump(dict(status='PASS',interpretation='Reproduction verification only; no new model/selection tuning',checks=checks),f,ensure_ascii=False,indent=2)
print('REPLAY_VERIFICATION_PASS '+str(len(checks))+' byte-identical numerical/source outputs')
