# 2026-11-19 로또 일일 연구 보고

## 오늘의 신규 연구 — E076: 과거 추천 실패를 후보선정과 조합기로 분리

오늘의 질문은 보존된 사전 추천 원본에서 당첨번호를 후보 union에 넣지 못한 실패와, union에는 넣었지만 한 줄에 모으지 못한 실패를 구분할 수 있는지였다. 기존 1245~1248회 오답노트는 개별 설명 위주였으므로, 여섯 개의 보존 원본을 같은 방식으로 재계산해 두 단계를 분리했다.

- 사전등록: [E076 preregistration](../weekly_purchase/1251/E076_HISTORICAL_RECOMMENDATION_CANDIDATE_VS_ALLOCATOR_DECOMPOSITION_PREREG_20261119.json)
- 계산 결과: [RESULTS.json](../../analysis/2026-11-19/E076_HISTORICAL_RECOMMENDATION_CANDIDATE_VS_ALLOCATOR_DECOMPOSITION_v1/RESULTS.json)
- 줄별 적중 분해: [LINE_HIT_DECOMPOSITION.csv](../../analysis/2026-11-19/E076_HISTORICAL_RECOMMENDATION_CANDIDATE_VS_ALLOCATOR_DECOMPOSITION_v1/LINE_HIT_DECOMPOSITION.csv)
- 보고서: [E076 report](../../analysis/2026-11-19/E076_HISTORICAL_RECOMMENDATION_CANDIDATE_VS_ALLOCATOR_DECOMPOSITION_v1/REPORT.md)
- SHA-256 manifest: [manifest](../../analysis/2026-11-19/E076_HISTORICAL_RECOMMENDATION_CANDIDATE_VS_ALLOCATOR_DECOMPOSITION_v1/SHA256_MANIFEST.json)

### 1. 데이터와 원본 확인

- `lotto_data.csv`: 1~1250회 연속 1,250개 행, Git blob `66431d711919f179e4cb1349e2f7295c68a8735e`, SHA-256 `7203238dae69ce281c59e6a0928cc187b11d88ed342685cd2dd2f214f063b3c2`
- 여섯 개 추천 원본의 blob SHA가 사전등록과 일치했고, 각 target cutoff는 target-1과 일치했다.
- 본번호 6개, 번호 범위, 보너스 분리, 줄 수·줄별 고유성 검증 PASS.
- 구매확인 registry는 confirmed purchase 0건이다. 따라서 아래 원본은 보존된 사전 추천 artifact이지, 구매 영수증으로 확인된 실제 구매본이 아니다.
- 1249회 사전 봉인 원본은 이번에도 확보하지 못했다. 사후 복원·추정하지 않았다.

### 2. 실제 계산 결과

| 보존 원본 | 줄 수 | Union 크기 | Union에 들어온 당첨번호 | 후보 recall | 최고 적중 | 줄별 적중 |
|---|---:|---:|---:|---:|---:|---|
| 1245 V4 primary | 3 | 15 | 1/6 | 16.7% | 1 | 0/0/1 |
| 1246 V2 decision | 5 | 21 | 2/6 | 33.3% | 1 | 1/0/1/0/0 |
| 1246 fallback | 5 | 21 | 4/6 | 66.7% | 1 | 1/1/1/1/1 |
| 1247 protocol V3 | 5 | 30 | 5/6 | 83.3% | 3 | 1/3/0/0/1 |
| 1248 V54-labelled | 5 | 30 | 3/6 | 50.0% | 1 | 0/1/1/0/1 |
| 1248 fallback | 5 | 18 | 5/6 | 83.3% | 3 | 3/1/2/1/1 |

### 3. 후보선정 실패와 조합기 실패 분리

- 여섯 artifact 중 5개는 union 안에 당첨번호가 2개 이상 있어 2+가 후보 단계에서 가능했다. 실제 2+ 줄은 2개뿐이어서 나머지 3개는 조합 단계에서 기회를 잃었다.
- 4개 artifact는 union 안에 당첨번호가 3개 이상 있어 3+가 후보 단계에서 가능했다. 실제 3+ 줄은 2개였고, 나머지 2개는 줄 구성 단계에서 놓쳤다.
- 3개 artifact는 union에 당첨번호 4개 이상을 담았지만, 어느 것도 4+ 줄을 만들지 못했다.
- 1245 원본은 union에 당첨번호가 1개뿐이어서 2+ 자체가 후보 단계에서 불가능했다.
- 1246 fallback은 union에 4개를 포함했지만 각 줄에 1개씩 흩어져 있었다. 1248 V54-labelled 원본도 union에 3개를 포함했지만 최고 적중은 1개였다.

이는 후보 recall과 줄별 집중도를 분리해야 한다는 운영 구조를 뒷받침하는 사례 분류다. 다만 표본은 6개 artifact/4개 회차이며, 같은 회차의 대체 원본이 포함돼 독립 관측치가 아니다. 줄 수와 union geometry도 다르다. 따라서 통합 적중률, p-value, 신뢰구간, 랜덤 대비 우위는 계산하거나 주장하지 않았다.

### 4. 해석과 프로젝트 영향

1. 후보 union의 당첨번호 회수율이 낮으면 조합기만 바꿔서는 2+/3+를 만들 수 없다.
2. 후보 union에 2~4개가 들어와도 한 줄에 모이지 않으면 포트폴리오 목적함수의 꼬리성과로 연결되지 않는다.
3. 따라서 다음 검증은 candidate recall gate와 allocator tail metrics를 분리하고, 동일 cutoff·동일 줄 수·동일 union geometry에서 평가해야 한다.
4. 1247 V3는 사후 모델 검증 리뷰에서 strict promotion이 거절됐다. 1248 fallback은 strict gate FAIL로 명시돼 있다. 개별 회차의 3+ 관측을 모델 우위로 승격하지 않는다.
5. 1245~1248 및 1244~1249 노출 구간은 live-history 진단 자료다. clean holdout이나 prospective confirmation으로 취급하지 않는다.

## 유지 중인 연구 — E075

E045의 frozen selector는 score-ranked combination order에서 연속쌍 패널티와 tie-break를 계산하지만, 사전등록은 정렬된 6개 티켓 기준을 요구한다. E075는 이 구현 불일치를 고치는 paired legacy-vs-corrected 연구로 이미 사전등록됐다.

- v1 첫 시도: 독립 used-set 미적용으로 union18 검증 전 실패
- v2 두 번째 시도: 계산 및 manifest는 완료했지만 warmup 포함 selector decision 수를 verifier가 잘못 기대해 post-run 검증 실패
- v3: warmup 1,050 target × 3 roles = 3,150 selector decisions로 검증 범위를 수정한 사전등록 및 trigger 파일 존재
- 현재 queue 상태: `PREREGISTERED_PENDING_DEDICATED_WORKFLOW`; v3 최종 결과 파일은 아직 확인되지 않았다.

E075 원본·실패 기록은 보존했고, E076은 별도의 역사 추천 오류 분해로 진행했다.

## 금요일 1251 준비 상태

- 최신 cutoff: 1250
- 1251 정책: 3줄 × 6개
- 기존 strict gate: 네 지표의 보정 moving-block CI 하한 모두 0 초과, any2 양의 비중첩 50-target block share 최소 0.65, 잔여 블록 유지, prospective confirmation 필요
- 2026-11-18 최신 model gate: `STRICT_FAIL`, 검증 모델 0개
- prospective minimum target count/completion rule: 미정
- 최종 3줄, fallback, freeze/seal: 생성 금지 및 미생성

E076은 역사 추천 오류를 분류한 진단이며 구매 적격성을 부여하지 않는다. E075 결과가 도착해도 역사 strict gate를 통과했다는 사실만으로 prospective confirmation을 대체하지 않는다.

## 오늘의 판정

- NEW STUDY: E076 historical recommendation candidate-vs-allocator decomposition — 실제 계산 완료
- NEW FINDING: 후보 단계에서 2+/3+가 가능했던 artifact 중 상당수가 조합 단계에서 실패했다. 후보 recall과 line concentration은 별도 평가해야 한다.
- MAINTENANCE/RECHECK: MASTER protocol, AGENTS, 1250 remediation plan, 원본 추천 기록, cutoff/hash, 1251 policy/gate 확인
- DAILY MASTER: PARTIAL — E075 실행 결과와 prospective confirmation 규칙이 아직 미완료
- BUY READINESS: STRICT_FAIL / NOT READY
- 후보번호·구매조합·fallback·freeze/seal: 생성하지 않음

## 다음 연구 1~3개

1. E075 v3 dedicated workflow의 실제 완료 여부와 결과/manifest를 확인하고 legacy/corrected를 별도로 감사한다.
2. E046 design-only power 결과를 바탕으로 prospective confirmation minimum/completion rule의 비구속 정책안을 검토하되, 승인 전에는 채택하지 않는다.
3. 1249 사전 봉인 원본은 GitHub와 검색 가능한 원본에서 계속 확인하되, 없으면 NOT FOUND를 유지하고 재구성하지 않는다.

## 최신 회차 교차확인

1250회(2026-11-14) 결과는 연합뉴스의 동행복권 발표 인용 보도와 별도 결과 조회 자료에서 교차 확인했다. 두 자료 모두 동일한 1250회 결과와 보너스 번호를 표시한다. GitHub 원자료의 마지막 회차 및 cutoff 1250과 일치하며, 11월 19일 현재 1251회 추첨 전이므로 데이터 추가는 없다.

- [연합뉴스, 2026-11-14 20:49](https://www.yna.co.kr/view/AKR20261114047000002)
- [LottoLottery 1250회 결과](https://www.lottolottery.co.kr/results/1250)
