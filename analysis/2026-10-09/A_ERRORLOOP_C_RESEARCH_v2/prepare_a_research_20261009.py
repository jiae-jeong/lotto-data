from pathlib import Path
import json,csv,hashlib,datetime,subprocess,shutil,ast,re
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/A_ERRORLOOP_C_RESEARCH_20261009_v1';WT=ROOT/'work/primary_mode_1245_v4_clean_20261009'
GIT=r'C:\Users\admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\git\cmd\git.exe'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def js(name,x):
    with (OUT/name).open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
def write(name,rr,fields):
    with (OUT/name).open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(rr)
# Do not publish unrelated personal documents or authentication log excerpts from the wide filename scan.
# Preserve the initial scan privately; published inventories include project-related paths only.
private=ROOT/'work/A_SOURCE_SEARCH_PRIVATE_INITIAL_20261009_v1';private.mkdir(exist_ok=False)
for name in ['LOCAL_SOURCE_FILE_INVENTORY.csv','SOURCE_KEYWORD_HITS.csv','SPECIFIC_MODEL_AND_RECOMMENDATION_HITS.csv']:
    p=OUT/name;shutil.copy2(p,private/name)
    with p.open(encoding='utf-8',newline='') as f:reader=csv.DictReader(f);fields=reader.fieldnames;data=list(reader)
    keep=[r for r in data if (r['path'].startswith('git:') or str(ROOT) in r['path']) and not ('AUTH' in Path(r['path']).name.upper() and Path(r['path']).suffix=='.log')]
    write(name,keep,fields)
    print(name+f': {len(data)} scanned; {len(keep)} published project entries; unrelated/auth excerpt exclusions preserved privately')
catalog=[]
selected=['LOTTO_PROJECT_PROTOCOL.md','lotto_project_state_2026-10-06.md','research/expansion_framework_v1/studies/study_batch_001/run_batch.py','research/expansion_framework_v1/studies/study_batch_001/study_registry.csv','research/expansion_framework_v1/studies/study_batch_001/model_metrics.csv','research/expansion_framework_v1/studies/study_batch_001/rolling300_study_results.csv','research/expansion_framework_v1/studies/study_batch_001/failure_registry.csv','research/expansion_framework_v1/studies/study_batch_001/surviving_models.csv','research/1245_final_pipeline_v3/prepare_1245_final_three_lines_v3.py','research/prospective_v4/prospective_engine_v4.py','research/prospective_v4/MODEL_MANIFEST_V4.csv','research/prospective_v4/RESEARCH_REGISTRY_V4.csv','research/prospective_v4/predictions/1245/FINAL_THREE_LINES_1245_V4.csv']
for rel in selected:
    p=WT/rel;st=p.stat();history=subprocess.check_output([GIT,'-C',str(WT),'log','--all','--format=%H|%aI|%s','--',rel]).decode('utf-8').strip()
    classification='POLICY ONLY: no original A/C formula or weights' if rel in selected[:2] else 'RELATED S/V3/V4 source; not authenticated legacy A/C/contrarian or past purchase'
    catalog.append(dict(path=rel,sha256=sha(p),bytes=st.st_size,created_utc=datetime.datetime.fromtimestamp(st.st_ctime,datetime.timezone.utc).isoformat(),modified_utc=datetime.datetime.fromtimestamp(st.st_mtime,datetime.timezone.utc).isoformat(),git_history=history,classification=classification,legacy_model_identity='NOT ESTABLISHED',legacy_actual_recommendation_link='NOT FOUND'))
write('SOURCE_EVIDENCE_CATALOG.csv',catalog,list(catalog[0]))
fsck=subprocess.run([GIT,'-C',str(WT),'fsck','--full','--unreachable','--no-reflogs'],capture_output=True)
(OUT/'GIT_UNREACHABLE_OBJECT_CHECK.log').write_text('COMMAND: git fsck --full --unreachable --no-reflogs\nEXIT: '+str(fsck.returncode)+'\nSTDOUT:\n'+fsck.stdout.decode(errors='replace')+'\nSTDERR:\n'+fsck.stderr.decode(errors='replace'),encoding='utf-8')
print('Git unreachable object check exit='+str(fsck.returncode)+' output bytes='+str(len(fsck.stdout)))
js('SOURCE_SEARCH_VERDICT.json',dict(A_MODEL_ORIGINAL='NOT FOUND',C_MODEL_ORIGINAL='NOT FOUND',CONTRARIAN_MODEL_ORIGINAL='NOT FOUND',actual_recommendation_sources_rounds_1_1244='SOURCE NOT FOUND',scope='Accessible current PC project files and all reachable Git refs/versions; remote has only main. Unreachable object check logged.',no_formula_reconstruction=True,no_backtest_rows_relabelled_as_purchase=True,related_versions_found=['B-v1','S001-S008 study_batch_001','V3 select_portfolio','V4 models / portfolio'],historical_1245_prediction_artifacts='EXISTING SEALED EVIDENCE ONLY; actual not read; not scored',not_found_is_not_proof_of_nonexistence=True))
finding='''# Related source formulas and inspect-only findings

## Identity and provenance

`LOTTO_PROJECT_PROTOCOL.md` sections 3/5/6 prescribe separated A signals, C combinations of repeatedly verified signals, and research of atypical structures. They do not specify executable legacy A/C/contrarian formulas, weights or selection rules. Local/hash/history metadata are in SOURCE_EVIDENCE_CATALOG.csv. The old `C:\\Users\\user` folders do not exist on this PC. The current remote has only main. Accessible historical backtest predictions do not prove that recommendations were published at those times.

- A_MODEL_ORIGINAL = NOT FOUND. Original A walk-forward = NOT EXECUTED.
- C_MODEL_ORIGINAL = NOT FOUND. Original C walk-forward = NOT EXECUTED.
- CONTRARIAN_MODEL_ORIGINAL = NOT FOUND. Original contrarian purchase performance = NOT EXECUTED.
- Actual recommendation/error-note originals for rounds 1..1244 = SOURCE NOT FOUND. No missed-number reasons or purchase performance were invented.
- The `model_a` column in correlations denotes the first member of a pair of compared models. `V4_C` is a registered V4 ID. Neither is proof of legacy A/C identity.

## Related versions actually found (preserved, NOT executed in this task)

Study batch 001 `run_batch.py` registers S001..S008, using 1..t-1 for historical targets 201..1244; fixed rolling300 results cover 501..1244. These are post-hoc experiments; all eight surviving-model entries are NONE_PROMOTED. The original absolute source paths are on a missing old user profile.

- S001: equal average of standardized frequencies at windows 10/30/100/300, top-six score ordering with lower-number ties.
- S002: pooled age-regime termination/risk counters, Beta prior strength 20 and prior probability 6/45; top-six scores. Definition in source is preserved, not retuned.
- S003: hot/cold transitions from previous20 to current20; (historical transition hits +20*6/45)/(transition exposure+20).
- S004: next occurrence conditioned on trailing10 count; (hits+30*6/45)/(exposure+30).
- S005: bank seed 20261008, size5000; sum of eight Laplace-smoothed structure transition log probabilities; lexical tie-breaking. The bank is NOT generated today.
- S006: pair residual sums at each node; E=(5/6)*(45/44)*F_a*F_b/n; residual=(O-E)/sqrt(E).
- S007: triple residual sums; E=(5*4/6^2)*(45^2/(44*43))*F_a*F_b*F_c/n^2.
- S008: source computes six rank vectors (S001,S002,S003,S004,S006,S007), then appends **45 constant vectors** in a loop over numbers: each vector has every column 45 if that loop's number belongs to the S005 ticket, else every column 0. There are always six positive constant vectors. Therefore s8[i]=(sum of six ranks at i +270)/51. The structure contribution is constant across all number columns and cannot change their relative ordering. This is a VERIFIED algebraic/code-inspection finding, not a newly executed historical S008 backtest. No original file is fixed here.

V3 `select_portfolio` is a distinct related selector: frequency/gap/momentum/conditional/structure/relationship six-family rank consensus, averaging S006/S007 as one relationship family and excluding S008 as a duplicate hybrid; supplemental distinct-family tickets minimize the tuple (-structure_coverage,-union_coverage,total_overlap,left_id,right_id). This implementation is not relabelled as recovered legacy C. V3 gate remains SEALED V3 GATE NOT PASSED; V3 check-only was not run.

V4 formulas and sealed 1245 predictions remain unchanged; V4_C is not relabelled as the old C model. No 1245 result, candidate generation, purchase-line generation or automation change occurs in this research.
'''
(OUT/'RELATED_SOURCE_CODE_FINDINGS.md').write_text(finding,encoding='utf-8')
for src,name in [('run_a_signal_research_20261009.py','run_independent_signal_research.py'),('search_a_sources_20261009.py','search_original_sources.py')]:
    p=ROOT/'work'/src;compile(p.read_text(encoding='utf-8'),str(p),'exec');shutil.copyfile(p,OUT/name)
cfg=dict(version='A_ERRORLOOP_C_RESEARCH_20261009_v1',raw_sha256='243cd17e6b97a2d96709ddfc689a068038669341a52dcc0743c141d309e43b9f',cutoff=1244,recent_windows=[10,30,50,100],time_blocks='1..50 through 1151..1200 (24 full50); 1201..1244 partial44',historical_targets=[1045,1244],prior_strength=20,mode_windows={'expanding':'all prior event observations','rolling300':'most recent300 event observations'},random_baseline='Exact combinatorial structural probabilities; previous B MC frozen reference only',seed=None,definitions={'low':'1..22','bands':'1..10;11..20;21..30;31..40;41..45','odd_imbalance':'odd<=1 or odd>=5','low_high_imbalance':'low<=1 or low>=5','extreme_sum':'sum<=90 or sum>=186; fixed symmetric thresholds around138','narrow_cluster':'any3 sorted numbers with max-min<=4','large_gap':'any adjacent sorted distance>=15','clusters':'adjacent distance<=2; separated when >2','multiple_previous_overlap':'>=2','end_multiplicity':'number mod10','consecutive_pairs':'count of adjacent sorted distance1, including within runs','gap':'current wait=cutoff-last occurrence; completed interval=next occurrence-prior occurrence; completed nonappearance=interval-1','recent_mean_gap':'completed intervals ending in window, plus separately intervals wholly inside window; censoring noted','direction':'recent rate minus disjoint preceding prefix; overlapping recent windows not independent'},forecast_claim='Post-hoc event probability / veto coverage diagnostic, not ticket performance or untouched holdout',no_ticket_generation=True,no_B_rerun=True,no_1245_result=True)
js('RESEARCH_CONFIG.json',cfg)
protocol='''# Independent A signals / related C / structure study protocol v1

Fixed before this numerical run. This is a retrospective descriptive research version, not a recovered A model or a prospective prediction.

- Input: only the pinned CSV rounds1..1244; exact hash in RESEARCH_CONFIG.json. No external lottery API, website or 1245 result is requested.
- Independently compute all45 single-number signals, all990 pairs and14190 triples for overall/recent10/30/50/100; report zero counts and sparsity. Definitions and thresholds are fixed in config. Recent directions compare with the disjoint earlier prefix; recent windows overlap and are not independent replications.
- Completed gaps, current waiting times and censored intervals are kept separate. Completed gaps wholly within short windows are length-biased by truncation; no due-number claim is made.
- Compute per-draw and distributional odd/low/bands/sum/consecutive/endings/gaps/clusters/previous-overlap metrics. First draw has no previous-overlap context and is excluded from that denominator.
- Time stability: 24 complete50-draw blocks plus one partial44 block (reported separately). Descriptive slopes/variability do not establish prediction performance.
- For13 predefined atypical structures calculate exact combinatorial probabilities without generating candidate tickets. Historical target1045..1244 uses only event observations through t-1; expanding and rolling300 probabilities=(event_count+20*exact_probability)/(exposure+20). Paired Brier/logloss differences are exploratory (26 comparisons); normal CIs ignore possible temporal dependence and do not authorize promotion.
- Hypothetical veto coverage: allow-all retains all observed winning structures; reject-property loses the fraction displaying that property. This is coverage, not purchase return, accuracy or fair replacement-ticket performance. No candidate replacement/allocation rule exists, so that separate holdout comparison remains NOT EXECUTED.
- Authentic original A/C/contrarian formulas and contemporaneous recommendation provenance are required before those model/error-loop tests. Historical backtest rows, V4 IDs and future1245 predictions are excluded as substitutes.
- B and MC are hash-verified frozen references. No B rerun, code edits, retuning, new candidates, final lines, automation updates or legacy-file changes.
- New hypotheses only; no recommendation use. Evidence of a predictive edge remains INSUFFICIENT EVIDENCE.
'''
(OUT/'RESEARCH_PROTOCOL.md').write_text(protocol,encoding='utf-8')
js('EXECUTION_PLAN_SEAL.json',dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),start_head=json.loads((OUT/'START_STATE.json').read_text())['start_head'],files={n:sha(OUT/n) for n in ['run_independent_signal_research.py','RESEARCH_CONFIG.json','RESEARCH_PROTOCOL.md']},historical_target_max=1244,actual_1245='NOT READ / NOT USED',no_candidate_generation=True))
print('Protocol/config/code fixed before numerical run; originals preserved')
