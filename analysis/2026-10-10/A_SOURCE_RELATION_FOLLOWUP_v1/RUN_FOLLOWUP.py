from pathlib import Path
import argparse, collections, csv, datetime, hashlib, importlib.util, itertools, json, math, os, shutil, subprocess, sys, time, urllib.request

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = Path(__file__).resolve().parents[1]
WT = ROOT / 'work/primary_mode_1245_v4_clean_20261009'
OUT = ROOT / 'outputs/A_SOURCE_RELATION_FOLLOWUP_20261010_v1'
PRIOR = ROOT / 'outputs/A_ERRORLOOP_C_RESEARCH_20261009_v2'
REL = 'analysis/2026-10-10/A_SOURCE_RELATION_FOLLOWUP_v1'
STATE = ROOT / 'work/A_SOURCE_RELATION_FOLLOWUP_STATE_20261010_v1.json'
PYTHON = sys.executable
RAW_SHA = '243cd17e6b97a2d96709ddfc689a068038669341a52dcc0743c141d309e43b9f'
REPLAY = False
spec = importlib.util.spec_from_file_location('git_auth', ROOT / 'work/finalize_b_model_git_restore_20261009.py')
g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
g.LOG = ROOT / 'outputs/A_SOURCE_RELATION_PUBLICATION_20261010_v1.log'

def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def write(p, obj):
    with p.open('x', encoding='utf-8', newline='\n') as f: json.dump(obj, f, ensure_ascii=False, indent=2); f.write('\n')
def table(p, rows, fields=None):
    with p.open('x', encoding='utf-8', newline='') as f:
        w=csv.DictWriter(f, fieldnames=fields or list(rows[0]), lineterminator='\n'); w.writeheader(); w.writerows(rows)
def rows(p):
    with p.open(encoding='utf-8-sig', newline='') as f: return list(csv.DictReader(f))
def snap(p):
    return {f.relative_to(p).as_posix():dict(sha256=sha(f), bytes=f.stat().st_size, mtime_ns=f.stat().st_mtime_ns) for f in p.rglob('*') if f.is_file() and '.git' not in f.parts}
def save(s): STATE.write_text(json.dumps(s, ensure_ascii=False, indent=2)+'\n',encoding='utf-8')
def preserve(s, added=False):
    for n,v in s['tracked_snapshot'].items():
        p=WT/n; assert p.is_file() and dict(sha256=sha(p),bytes=p.stat().st_size,mtime_ns=p.stat().st_mtime_ns)==v, n
    if not added: assert snap(WT)==s['tracked_snapshot']
    for label in ['prior_a','b_audit','b_random']:
        assert snap(Path(s['preserved_paths'][label]))==s[label], label
    g.original_preserved(s)
def data():
    p=WT/'lotto_data.csv'; assert sha(p)==RAW_SHA
    r=rows(p); assert len(r)==1244 and [int(x['round']) for x in r]==list(range(1,1245))
    draws=[]
    for x in r:
        ns=tuple(sorted(int(x['no'+str(i)]) for i in range(1,7))); b=int(x['bonus'])
        assert len(set(ns))==6 and all(1<=n<=45 for n in ns) and 1<=b<=45 and b not in ns
        draws.append(ns)
    return r,draws
def binomial_tails(n,q):
    pmf=[math.exp(n*math.log1p(-q))]
    for k in range(n): pmf.append(pmf[-1]*(n-k)/(k+1)*q/(1-q))
    total=math.fsum(pmf); assert abs(total-1)<1e-11
    tail=[0.]*(n+1); accum=0.
    for k in range(n,-1,-1): accum+=pmf[k]; tail[k]=min(1.,accum)
    return tail
def count_rel(draws,r):
    c=collections.Counter()
    for d in draws: c.update(itertools.combinations(d,r))
    return c
def start():
    assert not STATE.exists() and not OUT.exists()
    s=dict(original_snapshot=g.snapshot(), original_head=g.git(g.REPO,'rev-parse','HEAD'),original_status=g.git(g.REPO,'status','--porcelain=v1','--untracked-files=all'),home_config_sha256=sha(g.HOME_CONFIG) if g.HOME_CONFIG.exists() else None)
    g.git(g.REPO,'status','--short','--branch'); g.git(g.REPO,'diff','--stat'); g.git(g.REPO,'diff','--cached','--stat')
    assert g.git(WT,'status','--porcelain=v1')==''
    g.git(WT,'-c','http.sslBackend=openssl','fetch','origin','main')
    head=g.git(WT,'rev-parse','HEAD'); remote=g.git(WT,'-c','http.sslBackend=openssl','ls-remote','origin','refs/heads/main').split()[0]
    assert head==remote==g.git(WT,'rev-parse','origin/main')=='b6643b225e62ece4428216c363027b3a82c7d9cb'
    s.update(start_head=head, worktree=str(WT),phase='started', tracked_snapshot=snap(WT), preserved_paths=dict(prior_a=str(PRIOR),b_audit=str(ROOT/'outputs/B_MODEL_REPRODUCTION_20261009_v1'),b_random=str(ROOT/'outputs/B_RANDOM_BASELINE_20261009_v1')))
    for k,p in s['preserved_paths'].items():s[k]=snap(Path(p))
    OUT.mkdir(exist_ok=False);save(s)
    write(OUT/'START_STATE.json', {k:s[k] for k in ['start_head','worktree','original_head','original_status']}|dict(created_utc=now(),existing_files_changed=0,actual_1245='NOT READ / NOT USED',B_rerun='NOT EXECUTED; frozen reference only'))
    source=ROOT/'work/OLDER_CHAT_EVIDENCE_INTAKE_20261009_v1.json'
    with (OUT/'OLDER_CHAT_EVIDENCE_INTAKE.json').open('xb') as f:f.write(source.read_bytes())
    attachments=[Path(r'C:\Users\admin\.codex\attachments')/x/'붙여넣은 텍스트.txt' for x in ['98938037-5bcd-41e6-a275-9266ee258edb','9bd67f57-f960-4de8-bd06-241042f9d789','4ab8437d-9dca-4969-9bd9-e0e69f652249']]
    att=[dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size) for p in attachments]
    assert len(set(x['sha256'] for x in att))==1
    write(OUT/'ATTACHMENT_IDENTITY.json',dict(status='PASS',attachments=att,handling='Same task continuation; prior research is not repeated'))
    cfg=dict(data_path=str(WT/'lotto_data.csv'),raw_sha256=RAW_SHA,cutoff=1244,range=[1,1244],orders=[2,3],families={'2':990,'3':14190,'combined':15180},alpha=.05,null='Independent draws, uniformly chosen six distinct numbers from 1..45',probability='comb(6,r)/comb(45,r)',test='one-sided exact binomial upper tail P(X >= observed), n=1244',multiple_testing=['Bonferroni within each family','Holm within each family','Bonferroni across both families'],zeros='All possible pairs/triples, including zero counts',windows_for_inference='Overall only; nested recent windows remain prior descriptive evidence',top10_walkforward=dict(anchors=[400,600,800,1000,1100],horizon=100,training='1..anchor inclusive',selection='Top ten relations by past count descending, then lexicographic tuple ascending',metric='sum of selected relation occurrences over future 100 draws, not ticket hit performance',baseline='100*10*comb(6,r)/comb(45,r)',uncertainty='Null variance includes covariance of overlapping selected relations; separate independent future draws',overlap='The five evaluation windows are disjoint',status='New retrospective calculation; earlier conversational claims are not executable originals'),seed=None,quote_audit='Only verify cited 1244 arithmetic against pinned raw data. Not eligible for primary pre-outcome recommendation or closed-loop model evaluation',actual_1245='NOT READ / NOT USED',existing_model_rules='UNCHANGED',hypothesis='H003 continuation and new H007 arithmetic-workflow evidence; no recommendation use')
    write(OUT/'FOLLOWUP_CONFIG.json',cfg)
    with (OUT/'FOLLOWUP_PROTOCOL.md').open('x',encoding='utf-8') as f:
        f.write('# 추가 원본 조사 및 관계 신호 검증\n\n이 버전은 기존 2026-10-09 연구를 변경하지 않는 추가 검증이다. 한국시간 자정 이후 생성되므로 2026-10-10 경로를 사용한다.\n\n실행 전에 설정과 코드 해시를 고정한다. 1~1244회 전체의 가능한 pair 990개 및 triple 14,190개를 모두 검사한다. 귀무가설은 각 회차 독립 균등 6/45 추출이다. 단측 binomial 상위 꼬리, family Bonferroni 및 Holm, 전체 15,180개 Bonferroni를 계산한다. 최근 구간은 이번 유의성 검정에서 선택하지 않는다. 다른 선행 신호/구간 탐색까지 포함한 전체 프로젝트 검정 수는 이 보정에 포함되지 않는다. 이 결과는 사후 통계이며 예측력 검증이 아니다.\n\n추가 관계 walk-forward는 anchor 400/600/800/1000/1100에서 그 회차까지의 출현 횟수로 top 10 관계를 고른다. 동률은 번호 튜플 오름차순이다. 평가 구간은 각각 다음 100회로 서로 겹치지 않는다. 결과는 관계 출현 횟수이며 추천 티켓 적중 성능으로 바꾸어 해석하지 않는다. 과거 대화의 선별 동률 처리 및 원본 코드가 없으므로 숫자가 같아도 과거 실행 재현으로 인정하지 않는다.\n\n1244회 인용 추천은 추첨 후 대화에 등장한 2차 기록이다. 당시 모델/추천 시각/cutoff/선정 및 제외 이유는 NOT RECORDED. 번호 대조만 실시한다. 원본 사전추천으로 인증하거나 A/B/C 성과에 합산하지 않는다. 전체 6줄이나 누락 이유를 추정하지 않는다.\n\nB는 기존 검증 결과만 참조한다. 1245 실제 결과 조회/사용 및 신규 추천/후보 생성은 하지 않는다. 기존 파일, V3/V4 및 자동화 설정을 변경하지 않는다.\n')
    with (OUT/'RUN_FOLLOWUP.py').open('xb') as f:f.write(Path(__file__).read_bytes())
    fixed=['FOLLOWUP_CONFIG.json','FOLLOWUP_PROTOCOL.md','RUN_FOLLOWUP.py','OLDER_CHAT_EVIDENCE_INTAKE.json']
    write(OUT/'EXECUTION_PLAN_SEAL.json',dict(created_utc=now(),git_base=head,actual_1245='NOT READ / NOT USED',prior_report_already_read=True,registration='Fixed before this run; retrospective, not prospective',artifacts={n:sha(OUT/n) for n in fixed}))
    preserve(s); print('PRE_EXECUTION_RULES_FIXED',flush=True)

def research():
    s=read(STATE);assert s['phase']=='started' or REPLAY
    for n,h in read(OUT/'EXECUTION_PLAN_SEAL.json')['artifacts'].items():assert sha(OUT/n)==h
    started=now();t0=time.perf_counter();cfg=read(OUT/'FOLLOWUP_CONFIG.json'); raw,draws=data()
    assert cfg['raw_sha256']==RAW_SHA and cfg['cutoff']==1244
    print('INPUT: rows=1244 rounds=1..1244 SHA256='+RAW_SHA,flush=True)
    write(OUT/'DATA_INTEGRITY.json',dict(status='PASS',rows=1244,min_round=1,max_round=1244,missing_rounds=[],duplicate_rounds=[],main_range_duplicate_errors=0,bonus_errors=0,sha256=RAW_SHA))
    prior_counts={(int(x['order']),x['numbers']):int(x['count']) for x in rows(PRIOR/'PAIR_TRIPLE_WINDOW_SIGNALS.csv') if x['window']=='overall'}
    results=[]; summary=[]; counts={}
    for r in cfg['orders']:
        counts[r]=count_rel(draws,r);q=math.comb(6,r)/math.comb(45,r); tail=binomial_tails(1244,q);family=[]
        for ns in itertools.combinations(range(1,46),r):
            label='-'.join(map(str,ns)); k=counts[r][ns];assert k==prior_counts[r,label]
            family.append(dict(order=r,numbers=label,n_draws=1244,count=k,observed_rate=k/1244,exact_uniform_probability=q,expected_count=1244*q,raw_upper_tail_p=tail[k],family_size=math.comb(45,r),bonferroni_family_p=min(1,tail[k]*math.comb(45,r)),bonferroni_combined_p=min(1,tail[k]*15180),holm_family_p=None,cutoff=1244,status='VERIFIED; retrospective co-occurrence only'))
        ordered=sorted(family,key=lambda x:(x['raw_upper_tail_p'],x['numbers'])); prev=0
        for i,x in enumerate(ordered):prev=max(prev,(len(ordered)-i)*x['raw_upper_tail_p']);x['holm_family_p']=min(1,prev)
        summary.append(dict(order=r,family_size=len(family),total_observed_relation_occurrences=sum(x['count'] for x in family),max_count=max(x['count'] for x in family),min_raw_p=min(x['raw_upper_tail_p'] for x in family),min_bonferroni_family_p=min(x['bonferroni_family_p'] for x in family),min_holm_family_p=min(x['holm_family_p'] for x in family),raw_p_below_005=sum(x['raw_upper_tail_p']<.05 for x in family),bonferroni_family_significant=sum(x['bonferroni_family_p']<.05 for x in family),holm_family_significant=sum(x['holm_family_p']<.05 for x in family),bonferroni_combined_significant=sum(x['bonferroni_combined_p']<.05 for x in family)))
        results.extend(family);print('EXACT_MULTIPLICITY',json.dumps(summary[-1]),flush=True)
    table(OUT/'PAIR_TRIPLE_MULTIPLICITY_ALL.csv',results)
    table(OUT/'MULTIPLICITY_SUMMARY.csv',summary)
    claims={2:{(11,21):34,(33,40):33,(37,40):31,(6,38):31,(10,31):31,(12,24):31},3:{(33,37,40):8,(3,8,27):8,(1,3,27):8,(3,20,44):8,(12,34,42):8,(12,15,24):8}}
    table(OUT/'QUOTED_RELATION_COUNT_COMPARISON.csv',[dict(order=r,numbers='-'.join(map(str,ns)),quoted_count=v,new_actual_count=counts[r][ns],status='MATCH' if v==counts[r][ns] else 'MISMATCH',interpretation='Descriptive counts only; past execution/source authenticity is not established') for r,cs in claims.items() for ns,v in cs.items()])
    # Select only historical relations, never six-number recommendation tickets.
    daily=[]; wf=[]; selected=[]
    old={2:[8,16,12,19,16],3:[1,2,1,1,0]}
    for r in [2,3]:
        q=math.comb(6,r)/math.comb(45,r)
        for ai,a in enumerate(cfg['top10_walkforward']['anchors']):
            c=count_rel(draws[:a],r); top=sorted(itertools.combinations(range(1,46),r),key=lambda ns:(-c[ns],ns))[:10]
            sets=[set(ns) for ns in top];vs=[]
            for j,ns in enumerate(top):selected.append(dict(order=r,anchor=a,training_through_round=a,rank=j+1,numbers='-'.join(map(str,ns)),training_count=c[ns],selection='count descending then lexicographic ascending'))
            for target in range(a+1,a+101):
                actual=set(draws[target-1]);v=sum(ss<=actual for ss in sets);vs.append(v)
                daily.append(dict(order=r,anchor=a,target_round=target,training_through_round=a,relation_occurrences=v,baseline_expected_occurrences=10*q,selected_relation_count=10))
            var=10*q*(1-q)
            for i in range(10):
                for j in range(i+1,10):
                    union=len(sets[i]|sets[j]);p_joint=math.comb(6,union)/math.comb(45,union) if union<=6 else 0
                    var+=2*(p_joint-q*q)
            actual_total=sum(vs);expect=1000*q;sd=math.sqrt(100*var)
            wf.append(dict(order=r,anchor=a,training_through_round=a,target_start=a+1,target_end=a+100,selected_relation_count=10,actual_relation_occurrences=actual_total,exact_null_expected=expect,exact_null_sd=sd,descriptive_null_z=(actual_total-expect)/sd,prior_quoted_occurrences=old[r][ai],numeric_comparison='MATCH' if actual_total==old[r][ai] else 'MISMATCH',prior_execution_reproduced='NO; original tie rule/code unavailable',status='VERIFIED new retrospective computation; not ticket prediction performance'))
    table(OUT/'TOP10_RELATION_WALKFORWARD_SELECTED.csv',selected);table(OUT/'TOP10_RELATION_WALKFORWARD_DAILY.csv',daily);table(OUT/'TOP10_RELATION_WALKFORWARD_SUMMARY.csv',wf)
    # Match the quoted numbers to the actual text; this is not a new recommendation.
    intake=read(OUT/'OLDER_CHAT_EVIDENCE_INTAKE.json');msg=intake['selected_verbatim_messages'][0]
    assert '13 / 15 / 18 / 19 / 31 / 38' in msg['text'] and '1 / 13 / 18 / 26 / 34 / 38' in msg['text']
    ticket=[13,15,18,19,31,38];actual=list(draws[1243]);bonus=int(raw[1243]['bonus'])
    assert actual==[1,13,18,26,34,38] and bonus==25
    hits=sorted(set(ticket)&set(actual));missed=sorted(set(actual)-set(ticket));assert len(hits)==3
    audit=dict(target=1244,quoted_ticket=ticket,actual_numbers=actual,bonus=bonus,hits=hits,hit_count=len(hits),missed_actual=missed,bonus_in_ticket=bonus in ticket,quoted_message_id=msg['message_id'],quoted_thread_id=msg['thread_id'],quote_utc=datetime.datetime.fromtimestamp(msg['started_at'],datetime.timezone.utc).isoformat(),raw_data_sha256=RAW_SHA,arithmetic_status='VERIFIED',primary_pre_outcome_source='NOT FOUND',source_type='POST_DRAW_QUOTATION',eligible_for_closedloop=False,original_recommendation_time='NOT RECORDED',model='NOT RECORDED',version='NOT RECORDED',cutoff='NOT RECORDED',selection_reason='NOT RECORDED',exclusion_reason='NOT RECORDED',other_five_lines='SOURCE NOT FOUND',actual_1245='NOT READ / NOT USED')
    write(OUT/'POSTDRAW_QUOTED_1244_ARITHMETIC.json',audit)
    table(OUT/'POSTDRAW_QUOTED_1244_NUMBER_MATCH.csv',[dict(target=1244,quoted_number=n,main_hit=int(n in actual),bonus_hit=int(n==bonus),source_type='POST_DRAW_QUOTATION',eligible_for_closedloop=False) for n in ticket])
    statuses=dict(A_MODEL_ORIGINAL='NOT FOUND',C_MODEL_ORIGINAL='NOT FOUND',CONTRARIAN_ORIGINAL='NOT FOUND',historical_original_closedloop='NOT EXECUTED',quoted_1244_arithmetic='VERIFIED',pair_triple_multiplicity='VERIFIED',top10_relation_walkforward='VERIFIED NEW RETROSPECTIVE RUN; not past model reproduction',past_chat_model_performance='NOT FOUND executable original; not used',B='REPRODUCED prior frozen run, not rerun',B_MC='MONTE_CARLO_VERIFIED prior frozen run, not rerun',predictive_superiority='INSUFFICIENT EVIDENCE',actual_1245='NOT READ / NOT USED')
    write(OUT/'STATUS_CLASSIFICATION.json',statuses)
    table(OUT/'HYPOTHESIS_REGISTRY_ADDENDUM.csv',[
        dict(hypothesis_id='H003_CONTINUATION',evidence='All 990 pairs and 14190 triples independently counted and exact upper tails corrected',variables='relation counts, order, exact null, adjusted p',expected_direction='frequently observed relationships might exceed uniform co-occurrence',walkforward='top10 relation occurrences in five disjoint 100-round windows; no ticket allocation',random_baseline='exact uniform co-occurrence and covariance',temporal_stability='see TOP10_RELATION_WALKFORWARD_SUMMARY.csv; existing v2 window stability preserved',state='INSUFFICIENT EVIDENCE',recommendation_use='NO'),
        dict(hypothesis_id='H007_QUOTED_ARITHMETIC',evidence='1244 postdraw quotation contains 3 matching main numbers; source admits previous miscount',variables='quoted main numbers, pinned actual, source time, hit set',expected_direction='machine set intersection should prevent arithmetic miscount',walkforward='NOT EXECUTED; pre-outcome original/cutoff unavailable',random_baseline='NOT APPLICABLE to source arithmetic',temporal_stability='one secondary quotation only',state='NEW',recommendation_use='NO')])
    report=f'''# A/C 원본 조사 및 관계 신호 추가 검증

시작 HEAD: `{s['start_head']}`. 입력: 1~1244회, SHA-256 `{RAW_SHA}`.
이번 새 실행 시작 UTC: {started}. 기존 B 및 2026-10-09 신호 연구는 재실행하거나 수정하지 않았다.

## 실제 추가로 확보한 증거

앱의 과거 대화 조회로 2026-10-04 사후 복습에서 1244회 추천 한 줄을 인용한 메시지를 찾았다.
본번호 대조 결과 {len(hits)}개({', '.join(map(str,hits))})이며 보너스는 포함하지 않는다.
이는 추첨 전 추천 메시지 원본이 아니다. 원본 추천 시각, 모델 및 cutoff/선택 이유는 NOT RECORDED.
폐쇄루프 모델 성과에는 합산하지 않았다. 다른 다섯 줄도 추정하지 않았다.

조회된 과거 대화는 각 5개 반환 turn만 제공했고 next_cursor는 없었다. 전체 과거 메시지가 검색됐다는 뜻으로 해석하지 않았다.
과거 대화 URL의 브라우저 조회는 로그아웃 홈으로 이동하여 원문 접근에 실패했다. 로그인/메시지 전송/자동화 변경은 하지 않았다.
기존 보고서의 SOURCE NOT FOUND는 저장소/로컬 검색 범위 결과로 보존하고, 이번 사후 인용 발견을 별도 provenance로 추가한다.

## 실제 관계 검정

전체 pair/triple {len(results):,}개를 모두 다시 계수했다. 이전 v2 전체 횟수와 전부 일치했다.
귀무가설은 독립 균등 6/45 회차. 단측 exact binomial 상위 꼬리를 계산하고 family Bonferroni/Holm 및 전체 15,180개 Bonferroni를 적용했다.
{json.dumps(summary,ensure_ascii=False,indent=2)}

family 및 전체 Bonferroni 기준을 통과한 관계는 {sum(x['bonferroni_family_significant'] for x in summary)}개이다.
이는 사후 co-occurrence 검정이다. 이 계산만으로 예측 우위를 입증하거나 관계를 추천 규칙에 편입할 수 없다.
최근 구간 다중선택과 프로젝트의 다른 신호 탐색은 이 검정 family에 포함되지 않았다.

## 새로운 관계 walk-forward

anchor 400/600/800/1000/1100까지의 데이터만 이용해 출현 횟수 상위 10개 관계를 선택했다. 동률은 번호 튜플 오름차순.
평가는 다음 100회씩, 최대 1200회까지이며 다섯 구간은 비중첩이다. 1245회는 포함하지 않는다.
관계 출현 횟수와 정확 균등 기대치 및 관계 중복을 반영한 귀무분산을 저장했다. 6개 티켓이나 후보는 생성하지 않았다.
{json.dumps(wf,ensure_ascii=False,indent=2)}

과거 대화의 수치가 일부 일치해도 당시 원본 코드/동률 처리/실행 로그가 없으므로 과거 실행을 REPRODUCED로 표시하지 않았다.
과거 결합 모델의 1,890 적중 및 random 1,920.78은 대화의 주장으로만 보존하며 공식 평가에 사용하지 않았다.

## 상태 및 남은 작업

기존 A/C/contrarian 정확 원본: NOT FOUND. 해당 통합 모델 walk-forward: NOT EXECUTED.
개별 신호 및 구조 계산은 기존 커밋의 VERIFIED 결과이며 이번에는 보존 해시만 다시 검증한다.
실제 원본 기반 폐쇄루프: NOT EXECUTED. 사후 인용의 번호 대조만 VERIFIED.
구조 허용/제거의 공정한 대체 티켓 비교: NOT EXECUTED. 기존 구조 사건 walk-forward/coverage 진단을 보존한다.
B: 기존 REPRODUCED 및 MONTE_CARLO_VERIFIED 기준점 보존. 예측 우위 INSUFFICIENT EVIDENCE.
필요한 최소 자료는 추첨 전 추천 메시지 원문 또는 당시 저장 산출물, 대상 회차/시각/cutoff/모델 규칙/선정 이유다.
1245회 실제 결과는 NOT READ / NOT USED. 신규 추천/후보/최종 3줄 생성은 하지 않았다.

## 재현 명령

`python RUN_FOLLOWUP.py compute --output <new_empty_directory> --worktree <pinned_clean_repository>`
`python RUN_FOLLOWUP.py check --output <new_results_directory> --worktree <pinned_clean_repository>`
원래 공식 실행은 새 날짜 디렉터리에서 한 번 수행했다. 재현은 별도 빈 폴더를 이용해야 하며 기존 산출물을 덮어쓸 수 없다.
'''
    with (OUT/'FOLLOWUP_REPORT.md').open('x',encoding='utf-8') as f:f.write(report)
    preserve(s,added=REPLAY)
    write(OUT/'ACTUAL_EXECUTION_RESULT.json',dict(status='PASS',started_utc=started,completed_utc=now(),elapsed_seconds=time.perf_counter()-t0,pair_triple_rows=len(results),walkforward_daily_rows=len(daily),quoted_arithmetic_hits=3,actual_1245='NOT READ / NOT USED',existing_files_changed=0))
    print('RESEARCH_EXECUTION_PASS',flush=True)

def verify():
    started=now(); s=read(STATE);raw,draws=data()
    for n,h in read(OUT/'EXECUTION_PLAN_SEAL.json')['artifacts'].items():assert sha(OUT/n)==h
    checks=[]
    for x in rows(PRIOR/'SHA256_MANIFEST.csv'):
        p=PRIOR/x['file'];assert sha(p)==x['sha256'] and p.stat().st_size==int(x['bytes']);checks.append(dict(group='prior_A',path=str(p),sha256=sha(p),status='PASS'))
    for x in rows(PRIOR/'FROZEN_B_REFERENCE_HASH_VERIFICATION.csv'):
        p=ROOT/x['path'];assert sha(p)==x['sha256'];checks.append(dict(group='frozen_B',path=str(p),sha256=sha(p),status='PASS'))
    prior_state=read(ROOT/'work/A_RESEARCH_PUBLICATION_STATE_20261009_v1.json')
    for n,v in prior_state['files'].items():
        p=WT/n;assert sha(p)==v['sha256'] and p.stat().st_size==v['bytes']
    mult=rows(OUT/'PAIR_TRIPLE_MULTIPLICITY_ALL.csv');assert len(mult)==15180
    independent={r:count_rel(draws,r) for r in [2,3]};maxerr=0.
    # Independent lgamma evaluation checks every distinct observed count, including zeros.
    independent_p={}
    for r in [2,3]:
        q=math.comb(6,r)/math.comb(45,r)
        for k in {int(x['count']) for x in mult if int(x['order'])==r}:
            independent_p[r,k]=min(1.,math.fsum(math.exp(math.lgamma(1245)-math.lgamma(j+1)-math.lgamma(1245-j)+j*math.log(q)+(1244-j)*math.log1p(-q)) for j in range(k,1245)))
    for x in mult:
        r=int(x['order']);ns=tuple(map(int,x['numbers'].split('-')));k=int(x['count']);assert k==independent[r][ns]
        expected=independent_p[r,k];err=abs(float(x['raw_upper_tail_p'])-expected);maxerr=max(maxerr,err);assert err<1e-10
        assert abs(float(x['bonferroni_family_p'])-min(1.,expected*math.comb(45,r)))<1e-8
        assert abs(float(x['bonferroni_combined_p'])-min(1.,expected*15180))<1e-8
        assert int(x['cutoff'])==1244
    for r in [2,3]:
        family=sorted([x for x in mult if int(x['order'])==r],key=lambda x:(float(x['raw_upper_tail_p']),x['numbers']));adj=0.
        for i,x in enumerate(family):adj=max(adj,(len(family)-i)*float(x['raw_upper_tail_p']));assert abs(float(x['holm_family_p'])-min(1.,adj))<1e-12
        assert sum(int(x['count']) for x in family)==1244*math.comb(6,r)
    selected=rows(OUT/'TOP10_RELATION_WALKFORWARD_SELECTED.csv');daily=rows(OUT/'TOP10_RELATION_WALKFORWARD_DAILY.csv');assert len(selected)==100 and len(daily)==1000
    for x in daily:
        r=int(x['order']);a=int(x['anchor']);target=int(x['target_round']);assert a<target<=a+100<=1200
        c=count_rel(draws[:a],r);top=sorted(itertools.combinations(range(1,46),r),key=lambda ns:(-c[ns],ns))[:10]
        assert int(x['relation_occurrences'])==sum(set(ns)<=set(draws[target-1]) for ns in top)
        recorded=sorted([y for y in selected if int(y['order'])==r and int(y['anchor'])==a],key=lambda y:int(y['rank']))
        assert [tuple(map(int,y['numbers'].split('-'))) for y in recorded]==top
    audit=read(OUT/'POSTDRAW_QUOTED_1244_ARITHMETIC.json');assert audit['hits']==sorted(set(audit['quoted_ticket'])&set(draws[1243])) and audit['hit_count']==3 and not audit['eligible_for_closedloop'] and audit['primary_pre_outcome_source']=='NOT FOUND'
    schemas=[]
    for p in OUT.glob('*.csv'):
        with p.open(encoding='utf-8',newline='') as f:
            rr=csv.DictReader(f); names=rr.fieldnames;assert names and len(names)==len(set(names));n=0
            for x in rr:assert None not in x and all(v is not None for v in x.values());n+=1
        schemas.append(dict(file=p.name,rows=n,columns=len(names),status='PASS'))
    table(OUT/'PRIOR_ARTIFACT_HASH_RECHECK.csv',checks);table(OUT/'CSV_SCHEMA_VERIFICATION.csv',schemas)
    preserve(s,added=REPLAY)
    write(OUT/'FINAL_VERIFICATION.json',dict(status='PASS',started_utc=started,completed_utc=now(),independent_tail_formula='lgamma sum, independently compared against recurrence',max_absolute_p_error=maxerr,verified_relation_rows=15180,verified_daily_walkforward_rows=1000,source_arithmetic_verified=True,closedloop_original_source='NOT FOUND',closedloop_execution='NOT EXECUTED',original_tracked_files_changed=0,prior_A_B_content_size_mtime_unchanged=True,actual_1245='NOT READ / NOT USED'))
    print('INDEPENDENT_VERIFICATION_PASS',flush=True)

def logged(phase):
    cmd=[PYTHON,str(Path(__file__).resolve()),phase]
    with (OUT/(phase.upper()+'_STDOUT.log')).open('xb') as stdout,(OUT/(phase.upper()+'_STDERR.log')).open('xb') as stderr:
        result=subprocess.run(cmd,stdout=stdout,stderr=stderr)
    write(OUT/(phase.upper()+'_PROCESS_RESULT.json'),dict(command=cmd,exit_code=result.returncode,completed_utc=now(),stdout_sha256=sha(OUT/(phase.upper()+'_STDOUT.log')),stderr_sha256=sha(OUT/(phase.upper()+'_STDERR.log'))))
    print(phase+' EXIT '+str(result.returncode));assert result.returncode==0

def package():
    assert read(OUT/'FINAL_VERIFICATION.json')['status']=='PASS'
    allfiles=[p for p in OUT.rglob('*') if p.is_file()]
    table(OUT/'SHA256_MANIFEST.csv',[dict(file=p.relative_to(OUT).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(allfiles)])
    print('MANIFEST_FINALIZED '+str(len(allfiles))+' entries; self excluded, Git blob hash provides manifest identity')

def publish():
    s=read(STATE);assert s['phase']=='started'
    assert read(OUT/'FINAL_VERIFICATION.json')['status']=='PASS'
    for x in rows(OUT/'SHA256_MANIFEST.csv'):assert sha(OUT/x['file'])==x['sha256'] and (OUT/x['file']).stat().st_size==int(x['bytes'])
    preserve(s);assert g.git(WT,'status','--porcelain=v1')=='' and not (WT/REL).exists()
    assert g.git(WT,'-c','http.sslBackend=openssl','ls-remote','origin','refs/heads/main').split()[0]==s['start_head']
    files={}
    for p in sorted(OUT.rglob('*')):
        if p.is_file():
            dst=WT/REL/p.relative_to(OUT);dst.parent.mkdir(parents=True,exist_ok=True)
            with dst.open('xb') as f:f.write(p.read_bytes())
            assert sha(dst)==sha(p);files[dst.relative_to(WT).as_posix()]=dict(bytes=p.stat().st_size,sha256=sha(p))
    s['files']=files;save(s)
    g.git(WT,'-c','core.autocrlf=false','add','--',*files)
    assert sorted(g.git(WT,'diff','--cached','--name-only').splitlines())==sorted(files)
    assert all(x.startswith('A\t') for x in g.git(WT,'diff','--cached','--name-status').splitlines())
    g.git(WT,'-c','core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','diff','--cached','--check');g.git(WT,'diff','--cached','--stat')
    for n,v in files.items():
        b=g.git(WT,'show',':'+n,binary=True);assert len(b)==v['bytes'] and hashlib.sha256(b).hexdigest()==v['sha256']
    s['pre_commit_status']=g.git(WT,'status','--short','--branch');save(s)
    preserve(s,added=True)
    g.git(WT,'commit','-m','Preserve source provenance and multiplicity audit without changing frozen models')
    s.update(commit=g.git(WT,'rev-parse','HEAD'),phase='committed');save(s)
    assert g.git(WT,'rev-parse','HEAD^')==s['start_head'] and g.git(WT,'status','--porcelain=v1')==''
    assert g.git(WT,'-c','http.sslBackend=openssl','ls-remote','origin','refs/heads/main').split()[0]==s['start_head']
    g.git(WT,'-c','http.sslBackend=openssl','push','origin','HEAD:refs/heads/main');s['phase']='pushed';save(s)

def remote():
    s=read(STATE);assert s['phase']=='pushed'
    g.git(WT,'-c','http.sslBackend=openssl','fetch','origin','main')
    remote=g.git(WT,'-c','http.sslBackend=openssl','ls-remote','origin','refs/heads/main').split()[0]
    assert remote==s['commit']==g.git(WT,'rev-parse','origin/main')
    dest=ROOT/'work/A_SOURCE_RELATION_REMOTE_DOWNLOAD_20261010_v1';dest.mkdir(exist_ok=False);verification=[]
    for n,v in s['files'].items():
        url='https://raw.githubusercontent.com/jiae-jeong/lotto-data/'+s['commit']+'/'+n
        req=urllib.request.Request(url,headers={'User-Agent':'lotto-research-audit','Cache-Control':'no-cache'})
        p=dest/n;p.parent.mkdir(parents=True,exist_ok=True)
        with urllib.request.urlopen(req,timeout=45) as r,p.open('xb') as f:assert r.status==200;shutil.copyfileobj(r,f)
        assert sha(p)==v['sha256'] and p.stat().st_size==v['bytes']
        verification.append(dict(path=n,bytes=v['bytes'],local_sha256=v['sha256'],remote_sha256=sha(p),status='PASS'));g.log('REMOTE_HTTPS_HASH_PASS: '+n+' '+sha(p))
    assert g.git(WT,'-c','http.sslBackend=openssl','ls-remote','origin','refs/heads/main').split()[0]==s['commit']
    assert sorted(g.git(WT,'diff','--name-status',s['start_head'],s['commit']).splitlines())==sorted('A\t'+n for n in s['files'])
    preserve(s,added=True)
    s.update(remote_main=remote,phase='remote_verified',remote_verified_files=len(verification),git_status=g.git(WT,'status','--short','--branch'),existing_files_changed=0);save(s)
    write(ROOT/'outputs/A_SOURCE_RELATION_PUBLICATION_20261010_v1.json',s)
    table(ROOT/'outputs/A_SOURCE_RELATION_REMOTE_VERIFICATION_20261010_v1.csv',verification)
    report=['# 추가 연구 GitHub 저장 완료','',f"시작 HEAD: `{s['start_head']}`",f"종료 commit 및 remote main: `{s['commit']}`",'',f"신규 파일 {len(verification)}개 원격 HTTPS 재다운로드 SHA-256 및 크기 일치. 기존 파일 수정 0.",f"Git status: `{s['git_status']}`",'','실제 pair/triple 및 사후 인용 대조/독립 검증 PASS. A/C/contrarian 원본 NOT FOUND, 실제 사전추천 원본 기반 폐쇄루프 NOT EXECUTED. 1245 결과 NOT READ / NOT USED.','', '## 파일 목록 및 SHA-256','', '| 파일 | bytes | SHA-256 |','| --- | ---: | --- |']
    report.extend(f"| {x['path']} | {x['bytes']} | {x['remote_sha256']} |" for x in verification)
    with (ROOT/'outputs/A_SOURCE_RELATION_COMPLETION_20261010_v1.md').open('x',encoding='utf-8') as f:f.write('\n'.join(report)+'\n')
    g.log('FOLLOWUP_REMOTE_VERIFIED_COMPLETE '+remote)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['start','research','verify','run','package','publish','remote','compute','check']);parser.add_argument('--output',type=Path);parser.add_argument('--worktree',type=Path);args=parser.parse_args()
    if args.worktree: WT=args.worktree
    if args.output: OUT=args.output
    if args.phase=='compute':
        assert args.output and not OUT.exists(), 'Reproduction requires a NEW empty output directory'
        source=Path(__file__).resolve().parent
        if not (source/'FOLLOWUP_CONFIG.json').exists():source=ROOT/'outputs/A_SOURCE_RELATION_FOLLOWUP_20261010_v1'
        OUT.mkdir(exist_ok=False)
        for n in ['FOLLOWUP_CONFIG.json','FOLLOWUP_PROTOCOL.md','RUN_FOLLOWUP.py','OLDER_CHAT_EVIDENCE_INTAKE.json','EXECUTION_PLAN_SEAL.json']:
            with (OUT/n).open('xb') as f:f.write((source/n).read_bytes())
        REPLAY=True;research();verify()
    elif args.phase=='check':REPLAY=True;verify()
    elif args.phase=='run':logged('research');logged('verify')
    else:globals()[args.phase]()
