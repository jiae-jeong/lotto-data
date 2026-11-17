# 2026-11-17 로또 일일 연구 기록

## 오늘의 신규 연구: E065 후보선정 recall 불확실성 감사

기존 11/17 candidate scorecard를 확인한 뒤 수행한 **사후(exploratory) robustness audit**다. 추첨 결과를 보지 않은 독립 확증 실험이나 사전등록 실험으로 포장하지 않는다.

- 원자료: `lotto_data.csv`, cutoff 1250, 1,250개 회차
- Git blob: `66431d711919f179e4cb1349e2f7295c68a8735e`
- canonical SHA-256: `7203238dae69ce281c59e6a0928cc187b11d88ed342685cd2dd2f214f063b3c2`
- 평가: 201~1250회, 1,050 targets
- 신호 6종 × TOP10/15/20/25/30 = 30개 비교
- 후보 baseline: 균등 무작위 K개 후보의 정확한 기대 recall (K/45)
- 불확실성: 50-target 비중첩 블록 21개, 지표별 20,000회 block bootstrap, family alpha 0.05 / Bonferroni 30 tests

### 실제 계산 결과

- 30개 모든 Bonferroni-adjusted moving-block CI의 하한이 0을 넘지 못했다. **후보선정 신호 strict 통과 0개**.
- 가장 큰 양의 점추정은 balanced TOP10의 +0.508 percentage points였으나 양의 블록은 11/21에 그쳤고 CI가 0을 포함했다.
- consensus TOP15는 +0.492 pp, 양의 블록 14/21이었으나 역시 CI가 0을 포함했다.
- 가장 큰 음의 점추정은 contrarian TOP25 -1.238 pp, 양의 블록 5/21이었다. 이 역시 CI가 0을 포함해 폐기 확정이 아닌 보류/추가검증 상태다.
- 기존 scorecard 평균 recall은 30개 중 29개가 독립 재계산과 부동소수점 허용오차 내에서 일치했다. momentum TOP10만 2 winner-candidate hits 차이(0.031746 pp)가 남았다. 원인 미확정이며 이 한 칸은 재현성 이슈로 표시한다.

이 결과로 어떤 신호도 승격하지 않는다. 1244~1249회는 이미 노출된 live-history 진단 자료이고 clean holdout이나 prospective confirmation이 아니다.

상세 계산 결과: [E065 JSON](../analysis/2026-11-17/E065_CANDIDATE_RECALL_UNCERTAINTY_AUDIT.json)  
재현 코드: [E065 runner](../automation/candidate_recall_uncertainty_audit_e065_v1.js)

## 후보선정 단계와 포트폴리오 단계 분리

- 후보 단계: E065에서 recall@K 30개 비교 모두 불확실성 기준 미통과.
- 3줄 포트폴리오 단계: target 1251 cutoff 1250의 E045 historical strict gate는 FAIL. max-hit delta -0.022492, any2 -0.007917, any3 -0.012531, union coverage -0.016471; any2 양의 50-target block 비율 47.06%(8/17)로 65% 기준 미달.
- 11/17 five-ticket research-only diagnostic은 max-hit 1.6629 vs matched random 1.7288, any2 0.5743 vs 0.6182, any3 0.0943 vs 0.1136, union coverage 2.8467 vs 3.0661이었다. 이 5줄 실험은 target 1251의 3줄 구매 정책 자격이 없다.
- B single-ticket walk-forward는 1,050 targets, leakage failures 0이지만 11-model strict validation 결과 validated model 0개다. Pair/triple 다중비교 보정 통과도 0개.

## 과거 추천 원본·오답노트 탐색 결과

현재 대화/첨부에는 별도 원본 첨부가 없다. GitHub에서 다음을 확인했다.

- 1245: V4 pre-draw seal/최종 3줄 원본과 1245 오답노트가 확인됨. 원본 복습은 [ROUND_1245_REVIEW.md](../analysis/2026-10-11/ROUND_1245_REVIEW.md). 추첨 결과 대비 줄별 0, 0, 1 hit; 이 기록은 해당 회차의 보존된 추천 원본 진단이다.
- 1246: [FINAL_FIVE_LINES_1246](../research/weekly_purchase/1246/FINAL_FIVE_LINES_1246_20261016.json)와 [FIRST_PRIZE_PURCHASE_1246_V2](../research/prospective_v4/decisions/1246/FIRST_PRIZE_PURCHASE_1246_V2.json)가 서로 다른 사전 원본이다. [ROUND_1246_REVIEW.md](../analysis/2026-10-18/ROUND_1246_REVIEW.md)는 V2 purchase-design 원본을 기록하지만 구매 영수증은 없어 실제 구매본을 확정하지 않는다.
- 1247: 5개의 서로 다른 보존 line set이 있어 어느 하나도 실제 구매본으로 선택하지 않는다.
- 1248: fallback 5줄과 V54 strict-pass final 5줄이 서로 다르며, 구매 확인은 없다.
- 1249: 추첨 전 sealed original recommendation artifact는 현재 검색 범위에서 확인되지 않았다. 대화 기반 전달 로그를 원본으로 복원하지 않는다.
- 1250: delivery JSON의 evidence correction은 요청/전달 증빙을 미확정으로 정정했다. 중간 후보 기록으로만 보존한다.
- `PURCHASE_CONFIRMATION_REGISTRY.json` confirmed purchases는 0건이다. 실제 구매 학습 aggregate는 아직 만들 수 없다.

## 데이터·무결성

- 1~1250회 연속, 본번호 6개 고유·1~45, 보너스 분리 검증.
- CSV 내부 물리 공백행 2개는 파서에서만 제외했고 원본을 수정하지 않았다.
- 1250회는 두 독립 보도 자료에서 결과가 일치한다. 공식 API endpoint 직접 retrieval은 확인되지 않았으므로 직접 조회했다고 주장하지 않는다.
- 1244~1249는 사전 노출된 live-history 구간으로 계속 오염 표시한다.

## 1250 remediation 및 1251 readiness

- V54/V83/V84/V85/V86은 모두 기존 strict gate FAIL. any2/any3 동시 robust gain champion은 확보되지 않았다.
- H1250-A/B는 target 1250용 5줄 연구 축이며 1251부터 적용하는 3줄 정책 증거로 전용하지 않는다.
- target 1251 status: `STRICT_FAIL`; validated three-line model 0, ready artifact 없음, prospective confirmation 미평가. prospective 최소 target 수와 completion rule도 정책에 아직 명시되지 않았다.
- fallback/random 승격, final lines 생성, freeze/seal은 모두 금지 상태다.

## 남은 과제

1. momentum TOP10의 2-hit 재현 차이를 원본 Python runner로 확인하고 원인 확정 전에는 scorecard를 수정하지 않는다.
2. 1251용 신규 연구는 allocator-only 또는 candidate-only 중 하나의 독립 가설만 사전고정하고, 같은 historical scorecard를 반복 탐색하지 않는다.
3. prospective confirmation 최소 target 수와 완료 규칙은 기존 strict gate를 바꾸지 않는 별도 정책 설계로만 검토한다. 승인·봉인 전에는 구매 readiness로 사용하지 않는다.

**오늘 결론:** E065 후보 recall 불확실성 감사는 실제 계산 완료, 예측 신호 승격 없음. 전체 MASTER daily status는 legacy A/C/contrarian 원본 미확보 및 실제 구매 기록 미확보로 `PROTOCOL_PARTIAL` 유지. 1251 구매 준비는 `STRICT_FAIL`이며 구매번호·fallback·freeze/seal을 생성하지 않았다.
