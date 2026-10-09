from pathlib import Path
import json,csv,hashlib,datetime,shutil,sys,subprocess
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/A_ERRORLOOP_C_RESEARCH_20261009_v2';WT=ROOT/'work/primary_mode_1245_v4_clean_20261009'
def rr(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert json.loads((OUT/'FINAL_VERIFICATION.json').read_text(encoding='utf-8'))['status']=='PASS'
issues=rr(OUT/'PRIOR_ARTIFACT_FORMAT_ISSUES.csv')
with (OUT/'PACKAGING_AND_SOURCE_LIMITATIONS.md').open('x',encoding='utf-8') as f:
    f.write('# Packaging and additional preserved evidence\n\n')
    f.write('The main numerical run v1 failed at duplicate-key CSV serialization; its code/plan/stdout/full stderr are preserved. New v2 changes only that serialization and succeeds. No seed or analytical threshold was tuned.\n\n')
    f.write('Report preparation attempt1 failed before writing the report due to the platform cp949 default; explicit UTF-8 fixed the read. Attempt2 failed while inventorying blank fields in an older CSV; attempt3 treats missing fields as source quality issues and succeeds. These are packaging failures, not a rerun or adjustment of numerical results. Logs are preserved.\n\n')
    f.write(f'{len(issues)} rows with missing CSV fields were found in the pre-existing V3 independent-validation artifact(s). They are recorded in PRIOR_ARTIFACT_FORMAT_ISSUES.csv; the old files were not repaired, overwritten or used as authentic purchase records. This reinforces the source/reproducibility limitation.\n\n')
    f.write('No fair ticket-level veto-vs-allow replacement policy was registered or executed. The computed diagnostic is only winning-structure coverage loss and historical event-probability calibration. All legacy-source error-loop claims remain blocked.\n\n')
    f.write('The final SHA manifest is made after execution/report log streams are closed. The preliminary manifest is preserved separately and is NOT the final integrity authority. No pre-existing B/research/prediction/raw/automation file changed.\n')
with (OUT/'REPRODUCTION_COMMANDS.md').open('x',encoding='utf-8') as f:
    f.write('# Actual commands and safe reproduction\n\n')
    f.write('Actual invocations are recorded in ACTUAL_EXECUTION_RESULT.json, EXTENSION_EXECUTION_RESULT.json and execution logs. The compiled source search ran `python work/search_a_sources_20261009.py`; scope/metadata are in SOURCE_SEARCH_EXECUTION_RECORD.json.\n\n')
    f.write('Scientific engine takes `--repo PATH --out NEW_EMPTY_VERSION_DIR`. Copy the pinned code/config/protocol, START_STATE/source-search evidence and corresponding execution plan seal to a fresh version directory first; it uses exclusive file creation and refuses to overwrite existing outputs. The --repo input must have the exact raw hash and frozen B/MC references. No A/B/C model code is executed by the engine.\n\n')
    f.write('Do not invoke it with this completed directory as --out. The preserved extension/verifier scripts record their actual original paths; adapt paths only in a new version before freezing/running it. Do not label a new source search as recovered originals without exact provenance. No V3 check-only, new tickets or 1245 outcomes are needed.\n\n')
    f.write('Git publication uses the existing authenticated local Git CLI and per-command OpenSSL, exact new paths, byte-preserving staged-blob checks, normal fast-forward push and independent raw GitHub HTTPS downloads. User Git global config is unchanged.\n')
# Full stderr from the first exec-tool report attempt, preserved verbatim rather than inferred.
with (OUT/'REPORT_PREPARATION_ATTEMPT_1_FULL_STDERR.log').open('x',encoding='utf-8') as f:
    f.write('Verbatim exec-tool stderr transcript (the first attempt was not redirected to a file):\n')
    f.write('Traceback (most recent call last):\n  File "C:\\Users\\admin\\Documents\\Codex\\2026-10-09\\6-45-jiae-jeong-lotto-data\\work\\report_a_research_20261009.py", line 10, in <module>\n    source=json.loads((OUT/\'SEARCH_SCOPE_AND_ERRORS.json\').read_text());start=json.loads((OUT/\'START_STATE.json\').read_text())[\'start_head\']\n                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File "C:\\Users\\admin\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\Lib\\pathlib.py", line 1028, in read_text\n    return f.read()\n           ^^^^^^^^\nUnicodeDecodeError: \'cp949\' codec can\'t decode byte 0xeb in position 2196: illegal multibyte sequence\n')
shutil.copyfile(Path(__file__),OUT/'finalize_research_bundle.py')
csvchecks=[]
for p in OUT.rglob('*.csv'):
    if p.name=='SHA256_MANIFEST.csv':continue
    with p.open(encoding='utf-8-sig',newline='') as f:
        rd=csv.DictReader(f);count=0
        for row in rd:
            assert None not in row and all(v is not None for v in row.values()),p.name
            count+=1
        csvchecks.append(dict(file=p.relative_to(OUT).as_posix(),rows=count,status='PASS: fixed schema, empty values distinct from missing columns'))
with (OUT/'NEW_CSV_SCHEMA_VERIFICATION.csv').open('x',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(csvchecks[0]),lineterminator='\n');w.writeheader();w.writerows(csvchecks)
with (OUT/'PACKAGING_VERIFICATION.json').open('x',encoding='utf-8') as f:json.dump(dict(status='PASS',completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),new_CSV_schemas_checked=len(csvchecks),prior_source_missing_field_rows=len(issues),numerical_outputs_unchanged_since_independent_verification=True,final_verification='PASS',old_files_changed=0,source_unavailable_tasks_not_declared_complete=True),f,indent=2);f.write('\n')
# Rename only our preliminary, uncommitted manifest. All original project/B evidence is untouched.
old=OUT/'SHA256_MANIFEST.csv';new=OUT/'PRELIMINARY_SHA256_MANIFEST_BEFORE_LOG_CLOSURE.csv';assert old.is_file() and not new.exists();old.rename(new)
with (OUT/'SHA256_MANIFEST.csv').open('x',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['file','bytes','sha256'],lineterminator='\n');w.writeheader()
    for p in sorted(OUT.rglob('*')):
        if p.is_file() and p.name!='SHA256_MANIFEST.csv':w.writerow(dict(file=p.relative_to(OUT).as_posix(),bytes=p.stat().st_size,sha256=sha(p)))
for x in rr(OUT/'SHA256_MANIFEST.csv'):assert sha(OUT/x['file'])==x['sha256'] and (OUT/x['file']).stat().st_size==int(x['bytes'])
print('FINAL BUNDLE PASS files='+str(sum(p.is_file() for p in OUT.rglob('*')))+'; CSV schema checks='+str(len(csvchecks))+'; preserved prior missing-field rows='+str(len(issues))+'; manifest='+sha(OUT/'SHA256_MANIFEST.csv'))
