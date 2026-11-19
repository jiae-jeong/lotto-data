# 2026-11-18 로또 일일 연구 보고

## 오늘의 신규 연구 — E070: E069 구현 일치성 감사와 후보/포트폴리오 2단계 분리

오늘의 핵심 질문은 E069가 사전등록한 수식 그대로 실행됐는지, 그리고 등록된 수식을 그대로 구현했을 때 후보선정 recall과 3줄 포트폴리오 성과가 각각 어떤지였다. E070은 결과를 본 뒤의 역사 자료 보정 감사이므로 **prospective confirmation이나 clean holdout으로 취급하지 않는다.**

- 사전등록: [E070 preregistration](../weekly_purchase/1251/E070_E069_IMPLEMENTATION_AND_CANDIDATE_STAGE_AUDIT_PREREG_20261118.json)
- 재현 runner: [E070 Python runner](../../automation/e070_e069_candidate_stage_audit_v1.py)
- 실계산 결과: [RESULTS.json](../../analysis/2026-11-18/E070_E069_IMPLEMENTATION_AND_CANDIDATE_STAGE_AUDIT_v1/RESULTS.json)
- 당첨번호 후보 탈락 추적: [MISS_TRACE_TOP30.csv](../../analysis/2026-11-18/E070_E069_IMPLEMENTATION_AND_CANDIDATE_STAGE_AUDIT_v1/MISS_TRACE_TOP30.csv)
- 보고서: [E070 report](../../analysis/2026-11-18/E070_E069_IMPLEMENTATION_AND_CANDIDATE_STAGE_AUDIT_v1/REPORT.md)

### 1. E069 구현 불일치 발견

E069 사전등록은 고정 prior (6/45), strength 45를 명시했다.

`(success + 45*(6/45)) / (exposure + 45)`

하지만 실제 [E069 runner](../../automation/three_line_previous_draw_membership_e069.py)는 번호별 장기 출현율을 prior로 사용했다.

`(success + 45*global_frequency_rate) / (exposure + 45)`

따라서 **E069 실행은 사전등록 수식과 일치하지 않았다.** 기존 E069의 `VERIFICATION.json=PASS`는 해시·cutoff·행 수·조합 기하를 확인했지만 점수 함수가 사전등록 수식과 같은지는 검사하지 않았다. 단위 테스트에도 prior 수식 일치성 검사가 없었다.

원본 E069 파일과 실행 결과는 덮어쓰지 않았다. 기존 결과는 실행된 empirical-frequency-prior 변형의 역사적 진단으로만 남기고, 등록된 E069 가설의 유효한 실험 결과로 승격하지 않는다.

### 2. 원자료·cutoff 감사

- `lotto_data.csv`: 1~1250회 연속 1,250개 유효 행, Git blob `66431d711919f179e4cb1349e2f7295c68a8735e`, 기록된 SHA-256 `7203238dae69ce281c59e6a0928cc187b11d88ed342685cd2dd2f214f063b3c2`
- E069 결과: target 401~1250, 850행, `training_through_round=t-1` 위반 0, 3줄 union18 기하 위반 0
- E070 등록 수식 재계산: cutoff 위반 0, 포트폴리오 기하 위반 0
- 1244~1249회는 이미 노출된 live-history 진단 구간이며 clean holdout이 아니다.

### 3. 후보선정 단계 — 등록 수식의 candidate_recall@K

비교 기준은 정확한 무작위 기대 (K/45). 850 targets, 50-target moving-block bootstrap 4,000회, 5개 K에 Bonferroni (alpha=0.01)을 적용했다.

| K | 후보 recall | 무작위 기대 | 차이 | 보정 CI | 양의 50회 블록 |
|---:|---:|---:|---:|---:|---:|
| 10 | 21.608% | 22.222% | -0.614 pp | [-1.850, +0.641] pp | 4/17 |
| 15 | 32.431% | 33.333% | -0.902 pp | [-2.157, +0.373] pp | 5/17 |
| 20 | 44.059% | 44.444% | -0.386 pp | [-1.778, +1.124] pp | 6/17 |
| 25 | 55.294% | 55.556% | -0.261 pp | [-1.556, +0.993] pp | 7/17 |
| 30 | 66.098% | 66.667% | -0.569 pp | [-2.216, +1.157] pp | 6/17 |

5개 구간 모두 보정 CI가 0을 포함했다. 후보선정 신호의 무작위 대비 우위는 확인되지 않았다.

TOP30에서 탈락한 당첨번호 발생은 총 1,729건이었다. 그중 직전 회차 본번호에 있었던 경우 216건, 없었던 경우 1,513건이다. 순위 31~35 / 36~40 / 41~45에 각각 608 / 562 / 559건이 있었다. 개별 회차·번호별 순위, 직전회차 membership, exposure, success는 MISS_TRACE에 보존했다.

### 4. 조합/포트폴리오 단계 — 등록 수식의 3줄 결과

변경하지 않은 E045 disjoint selector로 3줄·union18을 만들고 exact geometry-matched null과 비교했다.

| 지표 | 관측 평균 | 정확 무작위 null | 차이 | 보정 CI |
|---|---:|---:|---:|---:|
| max_hits | 1.496471 | 1.514256 | -0.017786 | [-0.076609, +0.042214] |
| any2 | 0.460000 | 0.474976 | -0.014976 | [-0.062035, +0.030906] |
| any3 | 0.072941 | 0.071355 | +0.001586 | [-0.016061, +0.019233] |
| winning union coverage | 2.363529 | 2.400000 | -0.036471 | [-0.125882, +0.060000] |

모든 보정 CI 하한이 0을 넘지 못했고, any2 양의 비중첩 50회 블록은 4/17(23.53%)으로 요구치 65%에 미달했다. **역사 strict gate FAIL.** any4+ 비율 0.588%는 보조 기록만 하며 승격 근거로 쓰지 않는다.

### 5. 과거 추천 원본 및 오답노트

현재 대화/첨부에는 별도 원본 추천 파일이 없었다. GitHub에서 다음 원본을 확인했다.

- 1245: [V4 pre-draw seal](../prospective_v4/decisions/1245/MODE_SELECTION_SEAL_1245_V4.json), [pre-draw decision](../prospective_v4/decisions/1245/PRIMARY_PURCHASE_DECISION_1245_V4.json), [오답 리뷰](../../analysis/2026-10-11/ROUND_1245_REVIEW.md), [오답 집계](../../analysis/2026-10-14/E020_TAIL_DISTRIBUTION_DECOMPOSITION_v1/ERROR_NOTE_1245_AGGREGATE.csv)
- 1246: [보존된 5줄 V2 원본](../prospective_v4/decisions/1246/FIRST_PRIZE_PURCHASE_1246_V2.json), [다른 5줄 기록](../weekly_purchase/1246/FINAL_FIVE_LINES_1246_20261016.json), [오답 리뷰](../../analysis/2026-10-18/ROUND_1246_REVIEW.md)
- 1247: [V3 final](../weekly_purchase/1247/FINAL_FIVE_LINES_1247_20261023_PROTOCOL_FULL_V3.json), [검증 리뷰](../weekly_purchase/1247/MODEL_VALIDATION_REVIEW_20261023.json), [V6 rejection audit](../weekly_purchase/1247/V6_REJECTION_AUDIT.json). 서로 다른 보존 line set이 여러 개 있어 하나를 실제 구매본으로 임의 선택하지 않았다.
- 1248: [V54 strict-pass 명칭 파일](../weekly_purchase/1248/FINAL_FIVE_LINES_1248_20261030_V54_STRICT_PASS.json), [fallback 원본](../weekly_purchase/1248/ACTUAL_PURCHASE_FIVE_LINES_1248_20261030_FALLBACK_V1.json), [post-draw audit](2026-11-01_round1248_postdraw_audit.md). 두 line set은 다르며 fallback은 strict gate FAIL이었다.
- 1249: 추첨 전 sealed 원본을 찾지 못했다. 전달 로그의 대화 기반 기록을 원본 추천 파일로 복원하지 않았다.
- 1250: [delivery evidence correction](../weekly_purchase/1250/DELIVERY_1250_20261113_EVIDENCE_CORRECTION.json)에서 전달/요청 증빙을 미확정으로 정정했다. 후보 파일을 sealed final로 보지 않는다.
- [PURCHASE_CONFIRMATION_REGISTRY](../PURCHASE_CONFIRMATION_REGISTRY.json)의 confirmed purchases는 0건이다. 따라서 과거 추천 파일은 보존돼 있지만, 영수증/명시적 확인으로 검증된 실제 구매본은 현재 없다.

1245~1248은 사전 추천 및 사후 복습 자료로는 보존하되, 구매 영수증이 없는 상태에서 actual purchase라고 부르지 않는다.

### 6. 금요일 1251 준비 상태

- 1251부터 적용되는 정책은 3줄×6개다. 첫 전달 예정은 2026-11-20 08:00 KST, 준비 마감은 2026-11-19다.
- 2026-11-18 현재 `STRICT_FAIL`; 검증된 모델 0개, ready artifact 없음.
- prospective confirmation은 여전히 필수지만 최소 target 수와 완료 규칙이 정책에 지정되지 않았다.
- E046 design-only power grid에서는 가정한 1 SD 효과일 때 80% joint power 근처에 도달하는 지점이 1,000 targets였다. 0.25/0.5/0.75 SD는 grid 내 80%에 도달하지 못했다. 이는 모델 성과가 아니며, 정책 규칙으로 채택하지 않았다.
- strict gate, alpha, 블록 길이, null, threshold를 바꾸지 않았다. fallback/random을 최종으로 승격하지 않는다.

## 오늘의 판정

- NEW STUDY: E070 implementation-conformance + candidate/portfolio two-stage audit — 실제 계산 완료
- NEW FINDING: E069의 등록 prior와 실행 prior가 다름; 등록 수식 기준 후보 recall 및 포트폴리오 모두 strict PASS 없음
- MAINTENANCE/RECHECK: E069 source blobs, data cutoff, prediction row count, union18 geometry 재검증
- BUY READINESS: STRICT_FAIL / NOT READY
- 최종 구매 조합, fallback, freeze, seal: 생성하지 않음

## 다음 연구 1~3개

1. E069 원본을 수정하지 않고 fixed 6/45 prior를 정확히 구현한 별도 runner와 수식 단위 테스트를 추가한다.
2. E045 selector의 구조 penalty가 실제 숫자 연속을 계산하는지 score-order 영향 여부를 별도 기술 감사한다.
3. E046 설계 결과를 바탕으로 prospective confirmation 최소 target 수/완료 규칙을 별도 정책안으로 검토하되, 사용자 승인 전에는 채택하지 않는다.
