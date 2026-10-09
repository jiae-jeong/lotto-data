# A/C 원본 조사 및 관계 신호 추가 검증

시작 HEAD: `b6643b225e62ece4428216c363027b3a82c7d9cb`. 입력: 1~1244회, SHA-256 `243cd17e6b97a2d96709ddfc689a068038669341a52dcc0743c141d309e43b9f`.
이번 새 실행 시작 UTC: 2026-10-09T15:06:15.520153+00:00. 기존 B 및 2026-10-09 신호 연구는 재실행하거나 수정하지 않았다.

## 실제 추가로 확보한 증거

앱의 과거 대화 조회로 2026-10-04 사후 복습에서 1244회 추천 한 줄을 인용한 메시지를 찾았다.
본번호 대조 결과 3개(13, 18, 38)이며 보너스는 포함하지 않는다.
이는 추첨 전 추천 메시지 원본이 아니다. 원본 추천 시각, 모델 및 cutoff/선택 이유는 NOT RECORDED.
폐쇄루프 모델 성과에는 합산하지 않았다. 다른 다섯 줄도 추정하지 않았다.

조회된 과거 대화는 각 5개 반환 turn만 제공했고 next_cursor는 없었다. 전체 과거 메시지가 검색됐다는 뜻으로 해석하지 않았다.
과거 대화 URL의 브라우저 조회는 로그아웃 홈으로 이동하여 원문 접근에 실패했다. 로그인/메시지 전송/자동화 변경은 하지 않았다.
기존 보고서의 SOURCE NOT FOUND는 저장소/로컬 검색 범위 결과로 보존하고, 이번 사후 인용 발견을 별도 provenance로 추가한다.

## 실제 관계 검정

전체 pair/triple 15,180개를 모두 다시 계수했다. 이전 v2 전체 횟수와 전부 일치했다.
귀무가설은 독립 균등 6/45 회차. 단측 exact binomial 상위 꼬리를 계산하고 family Bonferroni/Holm 및 전체 15,180개 Bonferroni를 적용했다.
[
  {
    "order": 2,
    "family_size": 990,
    "total_observed_relation_occurrences": 18660,
    "max_count": 34,
    "min_raw_p": 0.0009655413635828089,
    "min_bonferroni_family_p": 0.9558859499469808,
    "min_holm_family_p": 0.9558859499469808,
    "raw_p_below_005": 40,
    "bonferroni_family_significant": 0,
    "holm_family_significant": 0,
    "bonferroni_combined_significant": 0
  },
  {
    "order": 3,
    "family_size": 14190,
    "total_observed_relation_occurrences": 24880,
    "max_count": 8,
    "min_raw_p": 0.00046751079043044655,
    "min_bonferroni_family_p": 1,
    "min_holm_family_p": 1,
    "raw_p_below_005": 425,
    "bonferroni_family_significant": 0,
    "holm_family_significant": 0,
    "bonferroni_combined_significant": 0
  }
]

family 및 전체 Bonferroni 기준을 통과한 관계는 0개이다.
이는 사후 co-occurrence 검정이다. 이 계산만으로 예측 우위를 입증하거나 관계를 추천 규칙에 편입할 수 없다.
최근 구간 다중선택과 프로젝트의 다른 신호 탐색은 이 검정 family에 포함되지 않았다.

## 새로운 관계 walk-forward

anchor 400/600/800/1000/1100까지의 데이터만 이용해 출현 횟수 상위 10개 관계를 선택했다. 동률은 번호 튜플 오름차순.
평가는 다음 100회씩, 최대 1200회까지이며 다섯 구간은 비중첩이다. 1245회는 포함하지 않는다.
관계 출현 횟수와 정확 균등 기대치 및 관계 중복을 반영한 귀무분산을 저장했다. 6개 티켓이나 후보는 생성하지 않았다.
[
  {
    "order": 2,
    "anchor": 400,
    "training_through_round": 400,
    "target_start": 401,
    "target_end": 500,
    "selected_relation_count": 10,
    "actual_relation_occurrences": 12,
    "exact_null_expected": 15.151515151515152,
    "exact_null_sd": 4.047151987808241,
    "descriptive_null_z": -0.7786994807728667,
    "prior_quoted_occurrences": 8,
    "numeric_comparison": "MISMATCH",
    "prior_execution_reproduced": "NO; original tie rule/code unavailable",
    "status": "VERIFIED new retrospective computation; not ticket prediction performance"
  },
  {
    "order": 2,
    "anchor": 600,
    "training_through_round": 600,
    "target_start": 601,
    "target_end": 700,
    "selected_relation_count": 10,
    "actual_relation_occurrences": 16,
    "exact_null_expected": 15.151515151515152,
    "exact_null_sd": 4.174500474658443,
    "descriptive_null_z": 0.2032542225436615,
    "prior_quoted_occurrences": 16,
    "numeric_comparison": "MATCH",
    "prior_execution_reproduced": "NO; original tie rule/code unavailable",
    "status": "VERIFIED new retrospective computation; not ticket prediction performance"
  },
  {
    "order": 2,
    "anchor": 800,
    "training_through_round": 800,
    "target_start": 801,
    "target_end": 900,
    "selected_relation_count": 10,
    "actual_relation_occurrences": 13,
    "exact_null_expected": 15.151515151515152,
    "exact_null_sd": 3.8140743256443366,
    "descriptive_null_z": -0.5640989052177642,
    "prior_quoted_occurrences": 12,
    "numeric_comparison": "MISMATCH",
    "prior_execution_reproduced": "NO; original tie rule/code unavailable",
    "status": "VERIFIED new retrospective computation; not ticket prediction performance"
  },
  {
    "order": 2,
    "anchor": 1000,
    "training_through_round": 1000,
    "target_start": 1001,
    "target_end": 1100,
    "selected_relation_count": 10,
    "actual_relation_occurrences": 20,
    "exact_null_expected": 15.151515151515152,
    "exact_null_sd": 3.8820961427804677,
    "descriptive_null_z": 1.2489347687850474,
    "prior_quoted_occurrences": 19,
    "numeric_comparison": "MISMATCH",
    "prior_execution_reproduced": "NO; original tie rule/code unavailable",
    "status": "VERIFIED new retrospective computation; not ticket prediction performance"
  },
  {
    "order": 2,
    "anchor": 1100,
    "training_through_round": 1100,
    "target_start": 1101,
    "target_end": 1200,
    "selected_relation_count": 10,
    "actual_relation_occurrences": 16,
    "exact_null_expected": 15.151515151515152,
    "exact_null_sd": 3.77960437234024,
    "descriptive_null_z": 0.22449038706119562,
    "prior_quoted_occurrences": 16,
    "numeric_comparison": "MATCH",
    "prior_execution_reproduced": "NO; original tie rule/code unavailable",
    "status": "VERIFIED new retrospective computation; not ticket prediction performance"
  },
  {
    "order": 3,
    "anchor": 400,
    "training_through_round": 400,
    "target_start": 401,
    "target_end": 500,
    "selected_relation_count": 10,
    "actual_relation_occurrences": 1,
    "exact_null_expected": 1.4094432699083863,
    "exact_null_sd": 1.1821109848621738,
    "descriptive_null_z": -0.3463661831686004,
    "prior_quoted_occurrences": 1,
    "numeric_comparison": "MATCH",
    "prior_execution_reproduced": "NO; original tie rule/code unavailable",
    "status": "VERIFIED new retrospective computation; not ticket prediction performance"
  },
  {
    "order": 3,
    "anchor": 600,
    "training_through_round": 600,
    "target_start": 601,
    "target_end": 700,
    "selected_relation_count": 10,
    "actual_relation_occurrences": 0,
    "exact_null_expected": 1.4094432699083863,
    "exact_null_sd": 1.1990025349105344,
    "descriptive_null_z": -1.1755131693808756,
    "prior_quoted_occurrences": 2,
    "numeric_comparison": "MISMATCH",
    "prior_execution_reproduced": "NO; original tie rule/code unavailable",
    "status": "VERIFIED new retrospective computation; not ticket prediction performance"
  },
  {
    "order": 3,
    "anchor": 800,
    "training_through_round": 800,
    "target_start": 801,
    "target_end": 900,
    "selected_relation_count": 10,
    "actual_relation_occurrences": 0,
    "exact_null_expected": 1.4094432699083863,
    "exact_null_sd": 1.1909888182926174,
    "descriptive_null_z": -1.1834227561673851,
    "prior_quoted_occurrences": 1,
    "numeric_comparison": "MISMATCH",
    "prior_execution_reproduced": "NO; original tie rule/code unavailable",
    "status": "VERIFIED new retrospective computation; not ticket prediction performance"
  },
  {
    "order": 3,
    "anchor": 1000,
    "training_through_round": 1000,
    "target_start": 1001,
    "target_end": 1100,
    "selected_relation_count": 10,
    "actual_relation_occurrences": 1,
    "exact_null_expected": 1.4094432699083863,
    "exact_null_sd": 1.2001999773935441,
    "descriptive_null_z": -0.3411458737047871,
    "prior_quoted_occurrences": 1,
    "numeric_comparison": "MATCH",
    "prior_execution_reproduced": "NO; original tie rule/code unavailable",
    "status": "VERIFIED new retrospective computation; not ticket prediction performance"
  },
  {
    "order": 3,
    "anchor": 1100,
    "training_through_round": 1100,
    "target_start": 1101,
    "target_end": 1200,
    "selected_relation_count": 10,
    "actual_relation_occurrences": 0,
    "exact_null_expected": 1.4094432699083863,
    "exact_null_sd": 1.2097368481798323,
    "descriptive_null_z": -1.1650825318159332,
    "prior_quoted_occurrences": 0,
    "numeric_comparison": "MATCH",
    "prior_execution_reproduced": "NO; original tie rule/code unavailable",
    "status": "VERIFIED new retrospective computation; not ticket prediction performance"
  }
]

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
