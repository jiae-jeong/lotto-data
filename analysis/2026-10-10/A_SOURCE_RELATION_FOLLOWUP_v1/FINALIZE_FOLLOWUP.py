from pathlib import Path
import csv, datetime, hashlib, importlib.util, json, math
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('followup',ROOT/'work/a_source_relation_followup_20261010.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
OUT=m.OUT
assert m.read(OUT/'FINAL_VERIFICATION.json')['status']=='PASS'
replay=ROOT/'work/A_SOURCE_RELATION_DETERMINISM_20261010_v1'
assert m.read(replay/'DETERMINISM_VERIFICATION.json')['status']=='PASS'
for n in ['DETERMINISM_VERIFICATION.json','STDOUT.log','STDERR.log','GIT_READONLY_REPLAY.log']:
    dest=OUT/'reproduction_verification'/n;dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open('xb') as f:f.write((replay/n).read_bytes())
for src,name in [(ROOT/'work/replay_relation_followup_20261010.py','REPLAY_FOLLOWUP.py'),(Path(__file__),'FINALIZE_FOLLOWUP.py')]:
    with (OUT/name).open('xb') as f:f.write(src.read_bytes())
intake=m.read(OUT/'OLDER_CHAT_EVIDENCE_INTAKE.json')
catalog=[]
for msg in intake['selected_verbatim_messages']:
    catalog.append(dict(thread_title=msg['title'],thread_id=msg['thread_id'],message_id=msg['message_id'],message_utc=datetime.datetime.fromtimestamp(msg['started_at'],datetime.timezone.utc).isoformat(),source_type=msg['evidence_type'],stored_source='OLDER_CHAT_EVIDENCE_INTAKE.json',source_file_sha256=m.sha(OUT/'OLDER_CHAT_EVIDENCE_INTAKE.json'),message_utf8_sha256=hashlib.sha256(msg['text'].encode('utf-8')).hexdigest(),primary_code='NOT FOUND',model_formula='NOT RECORDED',weights='NOT RECORDED',cutoff='NOT RECORDED',eligible_model_evaluation=False))
m.table(OUT/'ADDITIONAL_SOURCE_EVIDENCE_CATALOG.csv',catalog)
# These cited p-values are approximate historical claims, not exact outputs.
allrows=m.rows(OUT/'PAIR_TRIPLE_MULTIPLICITY_ALL.csv');summary=m.rows(OUT/'MULTIPLICITY_SUMMARY.csv')
compare=[]
for r,numbers,quoted,tol in [(2,'11-21',.00106,.000005),(3,'33-37-40',.000474,.0000005)]:
    row=next(x for x in allrows if int(x['order'])==r and x['numbers']==numbers);actual=float(row['raw_upper_tail_p'])
    compare.append(dict(order=r,numbers=numbers,quoted_approximate_p=quoted,current_exact_p=actual,delta=actual-quoted,quote_rounding_tolerance=tol,status='MATCH_WITHIN_QUOTED_PRECISION' if abs(actual-quoted)<=tol else 'MISMATCH',cause='UNCONFIRMED; historical code, data and tail convention not authenticated',adjusted_conclusion='No family Bonferroni significance in current computation'))
m.table(OUT/'QUOTED_PVALUE_COMPARISON.csv',compare)
# Independently check the recorded relation-window variance using conditional probabilities.
selections=m.rows(OUT/'TOP10_RELATION_WALKFORWARD_SELECTED.csv');checks=[]
for row in m.rows(OUT/'TOP10_RELATION_WALKFORWARD_SUMMARY.csv'):
    r=int(row['order']);anchor=int(row['anchor']);q=math.comb(6,r)/math.comb(45,r)
    selected=[set(map(int,x['numbers'].split('-'))) for x in selections if int(x['order'])==r and int(x['anchor'])==anchor]
    var=10*q*(1-q)
    for i in range(10):
        for j in range(i+1,10):
            additional=len(selected[j]-selected[i]);conditional=math.comb(6-r,additional)/math.comb(45-r,additional)
            var+=2*(q*conditional-q*q)
    computed=math.sqrt(100*var);actual=float(row['exact_null_sd']);assert abs(computed-actual)<1e-12
    checks.append(dict(order=r,anchor=anchor,recorded_exact_null_sd=actual,independent_conditional_null_sd=computed,status='PASS'))
m.table(OUT/'NULL_COVARIANCE_VERIFICATION.csv',checks)
scorecards=[]
for item,status,execution,source in [
    ('A_MODEL_ORIGINAL','NOT FOUND','NOT EXECUTED','Previous repository/local search plus returned historical chat messages; exact source absent'),
    ('C_MODEL_ORIGINAL','NOT FOUND','NOT EXECUTED','Related S/V4 models preserved, not substituted for legacy C'),
    ('CONTRARIAN_MODEL_ORIGINAL','NOT FOUND','NOT EXECUTED','Exact historical formula absent'),
    ('B_V1','REPRODUCED','Prior completed B audit; NOT RERUN','2892b0d4424c72554612d464b7a7093f814e3fc3'),
    ('B_RANDOM_BASELINE','MONTE_CARLO_VERIFIED','Prior completed Monte Carlo; NOT RERUN','fa5b248b190b204da60f509afa26ffaa0bbe77af'),
    ('INDEPENDENT_SIGNALS_STRUCTURE','VERIFIED','Prior completed independent run; hash rechecked','b6643b225e62ece4428216c363027b3a82c7d9cb'),
    ('PAIR_TRIPLE_MULTIPLICITY','VERIFIED','New executed exact all-relation test','PAIR_TRIPLE_MULTIPLICITY_ALL.csv'),
    ('TOP10_RELATION_WALKFORWARD','VERIFIED','New executed past-only relation-occurrence test; no ticket performance','TOP10_RELATION_WALKFORWARD_SUMMARY.csv'),
    ('1244_SECONDARY_QUOTED_ARITHMETIC','VERIFIED','New mechanical set comparison; not authentic pre-outcome source','POSTDRAW_QUOTED_1244_ARITHMETIC.json'),
    ('ORIGINAL_RECOMMENDATION_CLOSEDLOOP','NOT EXECUTED','Pre-outcome source / model identity / cutoff missing','One postdraw quotation is not eligible'),
    ('STRUCTURE_FILTER_TICKET_ALLOW_VETO','NOT EXECUTED','Replacement/allocation policy absent; no new candidate generation','Prior structure incidence/event-probability studies preserved')]:
    scorecards.append(dict(item=item,status=status,execution=execution,source=source,mean_hits='NOT CALCULATED THIS RUN',ticket_hit_distribution='NOT CALCULATED THIS RUN',predictive_edge='INSUFFICIENT EVIDENCE',recommendation_rule_changed=False))
m.table(OUT/'MODEL_SIGNAL_SCORECARD_ADDENDUM.csv',scorecards)
with (OUT/'REPRODUCTION_NOTES.md').open('x',encoding='utf-8') as f:
    f.write('''# 재현 검증 및 명령 보충

공식 과학 계산과 독립 verification은 각각 종료 코드 0이다. 추가 재현 검증에서 계산/관계 선택/인용 대조 결과 11개 파일이 byte-identical이었다. 타임스탬프와 보고서 경로를 담은 파일은 byte-identical 비교 대상에서 제외했다.

RUN_FOLLOWUP.py는 실제 실행한 workspace orchestration 코드로서 work/ 위치를 기준으로 경로를 찾는다. 산출물 폴더에 보존한 복사본을 그 위치에서 단독 실행하면 경로 기준이 다르므로 직접 실행하지 않는다. FOLLOWUP_REPORT.md의 일반 재현 명령은 이 workspace 경로 보정 없이 사용할 수 없다. 이번 검증은 REPLAY_FOLLOWUP.py의 I/O 어댑터로 실제 수행했고, 통계/선별 규칙은 수정하지 않았다.

실제 사용한 명령:

```powershell
& 'C:\\Users\\admin\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe' 'work\\replay_relation_followup_20261010.py' --root 'C:\\Users\\admin\\Documents\\Codex\\2026-10-09\\6-45-jiae-jeong-lotto-data' --output 'C:\\Users\\admin\\Documents\\Codex\\2026-10-09\\6-45-jiae-jeong-lotto-data\\work\\A_SOURCE_RELATION_DETERMINISM_20261010_v1'
```

다시 실행하려면 --output만 새로 존재하지 않는 폴더로 지정해야 한다. 어댑터는 기존 workspace state/기준 산출물과 실행 원본 코드의 SHA-256을 검증한다. 다른 PC에서 단독 실행 가능한 패키징은 NOT EXECUTED이다.

과거 인용의 p값은 현재 exact 계산과 해당 표기 정밀도에서 불일치한다. 원인에 대한 원본 증거가 없으므로 UNCONFIRMED이다. 이 불일치는 현재 보정 후 채택 근거가 없다는 결론을 바꾸지 않는다. 수치 차이를 맞추려고 입력/규칙을 변경하지 않았다.
''')
meta=dict(status='PASS',new_csv_count=len(list(OUT.glob('*.csv'))),deterministic_outputs=11,independent_conditional_covariance_checks=10,existing_original_files_changed=0,existing_original_B_A_hashes_preserved=True,actual_1245='NOT READ / NOT USED',created_utc=m.now(),limitations=['A/C/contrarian originals NOT FOUND','Pre-outcome original recommendation missing; closedloop NOT EXECUTED','Some historic quoted numbers MISMATCH with cause UNCONFIRMED','Workspace-specific reproduction; portable single-folder packaging NOT EXECUTED'])
for p in OUT.glob('*.csv'):
    with p.open(encoding='utf-8',newline='') as f:
        rr=csv.DictReader(f);assert len(rr.fieldnames)==len(set(rr.fieldnames))
        for x in rr:assert None not in x and all(v is not None for v in x.values())
m.preserve(m.read(m.STATE));m.write(OUT/'PACKAGING_VERIFICATION.json',meta)
m.package()
print('PACKAGE_PASS '+str(len(list(OUT.rglob('*'))))+' members including directories')
