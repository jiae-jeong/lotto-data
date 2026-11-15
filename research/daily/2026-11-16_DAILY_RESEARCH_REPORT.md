# 2026-11-16 로또 일일 연구 보고

## 오늘의 신규 연구 — E057 3줄 strict gate의 무작위 오통과율

오늘은 예측모델을 새로 만들거나 과거 성적표를 반복하지 않고, 1251회부터 적용하는 3줄 전용 strict gate 자체가 정확한 무작위 기준에서 얼마나 자주 잘못 통과하는지 별도로 검증했어.

- [E057 사전등록](https://github.com/jiae-jeong/lotto-data/blob/main/research/weekly_purchase/1251/E057_THREE_LINE_NULL_GATE_CALIBRATION_PREREG_20261116.json)
- [E057 결과 보고서](https://github.com/jiae-jeong/lotto-data/blob/main/analysis/2026-11-16/codemode_20261116_0805/E057_THREE_LINE_NULL_GATE_CALIBRATION_v1/REPORT.md)
- [실제 계산 결과](https://github.com/jiae-jeong/lotto-data/blob/main/analysis/2026-11-16/codemode_20261116_0805/E057_THREE_LINE_NULL_GATE_CALIBRATION_v1/INFERENCE.json)
- [검증 결과](https://github.com/jiae-jeong/lotto-data/blob/main/analysis/2026-11-16/codemode_20261116_0805/E057_THREE_LINE_NULL_GATE_CALIBRATION_v1/VERIFICATION.json)

### 실제 계산

- 1~1250회 원자료 1,250행: 연속 회차·본번호 6개 고유성·1~45 범위·보너스 분리 검사 통과
- 평가 구간: 401~1250회, 850 target
- 무작위 3줄 포트폴리오: 1,000개 독립 trajectory × 850회 = 850,000개
- 지표별 moving-block bootstrap 4,000회, 블록 길이 50, 총 17개 블록
- 정확한 union18 null의 네 기대값을 조합론으로 독립 재계산했고 E045 고정값과 최대 오차는 1.78e-15
- 3줄·각 6개·서로 겹치지 않는 union18 위반: 0건

### 결과

**1,000개 무작위 trajectory 중 1개만 전체 strict gate를 통과했어.**

- 공동 오통과율: 0.10%
- 95% Wilson 구간: 0.0177%~0.5643%
- 기존 familywise 상한: 5%
- any2 양의 50회 블록 비율 조건만 통과한 trajectory는 118/1,000(11.8%)이었지만, 네 개 보정 CI까지 동시에 요구하자 공동 통과는 1개로 줄었어.

이 결과는 현재 gate가 이번에 사전등록한 독립 균등 무작위 disjoint-union18 null에서 보수적으로 작동한다는 뜻이야. 지속성 있는 비예측 신호 등 다른 null 메커니즘까지 검증한 것은 아니고, 어떤 예측모델의 우위도 증명하지 않아. 임계값·유의수준·블록 길이·비교 기준은 바꾸지 않았어.

## 후보선정·포트폴리오 현황

- 오늘 candidate_recall@10/15/20/25/30 모델 성적표는 새로 계산하지 않았어. 최신 11/15 후보선정 결과를 그대로 유지하며, E051 pair-context는 무작위 대비 안정적 우위를 확인하지 못했어.
- 3줄 포트폴리오의 역사적 strict gate는 여전히 FAIL이야. E054 rolling concentration도 max-hit/any2/any3/union 네 지표의 점추정 차이가 모두 음수였고, any2 양의 50회 블록은 6/17(35.29%)이었어.
- E055 triple recent-strength 지속성은 상관 -0.309, bootstrap 구간 [-0.612, -0.018], 무작위 꼬리확률 0.826으로 예측 신호가 지지되지 않았어.
- E056 H005_FIX는 구조 벡터의 구현 오류를 분리 수정했지만 WEAK 판정이야. 전체 평균 적중만 약간 높았고 최근 100/50회 성과는 낮아 승격하지 않았어.
- 보조 점검으로 B 단일티켓 8개 모델의 trailing-100 평균 적중 선택기를 950 target에 적용했지만, 평균 0.7947·any2 17.47%·any3 1.47%로 정확 무작위 기대(0.8·17.53%·2.38%)를 넘지 못했어. E052가 이미 3줄 trailing-performance selector를 검증했으므로 이 결과는 독립 축이나 구매 근거로 취급하지 않아. [보조 계산 기록](https://github.com/jiae-jeong/lotto-data/blob/main/analysis/2026-11-16/codemode_20261116_0805/E057_THREE_LINE_NULL_GATE_CALIBRATION_v1/AUXILIARY_SINGLE_TICKET_SELECTOR_CROSSCHECK.json)

## 과거 원본 추천·오답노트 및 구매 증빙 감사

현재 대화/첨부에는 원본 파일이 별도 첨부되지 않았고, GitHub 원본에서 1245~1248 추천·복습·오답 기록을 확인했어.

- 1245: V4 사전 추천 3줄과 원본 오답노트가 보존돼 있지만 영수증은 없어.
- 1246: V1/V2 및 별도 fallback 사전 추천 세트가 함께 보존돼 있고 서로 다르며, 영수증으로 실제 구매본을 특정할 수 없어.
- 1247/1248: 파일명이 ACTUAL_PURCHASE인 기록이 있지만 11/14 provenance correction에서 구매 영수증 또는 명시적 확인이 없다고 정정돼 있어.
- 1249/1250: DELIVERY_LOG에도 구매 확인이 없다고 기록돼 있어.
- PURCHASE_CONFIRMATION_REGISTRY의 confirmed_purchases는 현재 0건이야.

따라서 이전 보고에서 1247·1248을 실제 구매라고 표현한 것은 잘못이야. 이 기록들은 보존된 추천/후보 세트의 사후 진단일 뿐, 검증된 구매 성적이 아니야. 1244~1249는 이미 노출된 live-history 진단 구간이며 깨끗한 홀드아웃으로 부르지 않아.

원본 근거:
- [1245 원본 오답노트](https://github.com/jiae-jeong/lotto-data/blob/main/analysis/2026-10-11/ROUND_1245_REVIEW.md)
- [1245 오답 집계](https://github.com/jiae-jeong/lotto-data/blob/main/analysis/2026-10-14/E020_TAIL_DISTRIBUTION_DECOMPOSITION_v1/ERROR_NOTE_1245_AGGREGATE.csv)
- [1246 원본 복습](https://github.com/jiae-jeong/lotto-data/blob/main/analysis/2026-10-18/ROUND_1246_REVIEW.md)
- [1247/1248 구매 증빙 정정](https://github.com/jiae-jeong/lotto-data/blob/main/research/daily/E047_ACTUAL_PURCHASE_PROVENANCE_CORRECTION_20261114.json)
- [구매 확인 registry](https://github.com/jiae-jeong/lotto-data/blob/main/research/PURCHASE_CONFIRMATION_REGISTRY.json)
- [전달 이력](https://github.com/jiae-jeong/lotto-data/blob/main/research/DELIVERY_LOG.md)

## 통과·실패 및 남은 문제

- E057 null gate calibration: PASS (등록된 null 메커니즘 한정)
- 예측모델 strict PASS: 0개
- 1251 구매 readiness: STRICT_FAIL / NOT READY
- Prospective confirmation의 최소 target 수와 완료 규칙: 아직 정책에 명시되지 않음
- E043/E044: 1250용 5줄 연구만을 위한 전용 workflow dispatch 대기 상태이며 3줄 구매 자격과 무관
- E017/E018: 원본 후보은행/당시 per-number rank vector/복수의 인증 구매기록이 부족해 계속 blocked

## 다음 연구 1~3개

1. 독립된 persistent/block-correlated null 메커니즘을 별도 사전등록해 E057의 null calibration 범위를 확장하되 strict gate는 그대로 유지.
2. prospective confirmation 최소 target 수와 완료 규칙을 구매 정책에 사전 명시하기 전까지 strict-ready를 만들지 않기.
3. E043/E044는 전용 workflow dispatch가 가능한 실행 경로에서 원본 preregistration 그대로 수행하고, 결과는 5줄 역사 진단에만 보관하기.

오늘은 gate의 무작위 오통과율을 실제 계산했을 뿐, 예측력이 있는 모델을 찾았다고 주장하지 않아. 구매용 최종 3줄은 생성·출력하지 않았고 freeze/seal도 만들지 않았어.


## 2026-11-16 추가 실계산 — E058/E059

### E058 persistent non-predictive null
- 1,000 trajectories, 850,000 portfolios, 4,000 moving-block bootstrap replicates per metric/trajectory.
- Null process: each of three lines retains 3/6 numbers per transition; union retention is 9/18; target outcomes are not used to generate portfolios.
- Strict-gate false passes: 0/1,000 (0.00%); 95% Wilson interval 0.0000%-0.3827%.
- Mean any2 lag-1 autocorrelation: -0.000733; all empirical null means were within 2 trajectory-level MCSE of exact expectations.
- This is a single persistent-null calibration only, not predictive evidence and not a reason to change the gate.

### E059 E054 candidate-stage decomposition
- Reproduced frozen E054 regime/HHI/exposure and all score SHA-256 values on 850/850 targets.
- Candidate recall TOP10/15/20/25/30: 21.667% / 32.569% / 43.059% / 54.902% / 66.039%.
- Exact random expectations: 22.222% / 33.333% / 44.444% / 55.556% / 66.667%.
- All five adjusted moving-block intervals include zero; no candidate-stage advantage is established over random or recent30.
- Winner miss trace: 5,100 winner instances, with regime-specific success/exposure, E054 rank/score, recent30 rank, and cutoff margins preserved.

The E058 parser preflight repair and E059 verification-summary repair were both technical-only; source data, cutoff, model scores, thresholds, and inference were unchanged. The original failure records remain preserved with separate addenda.

Detailed supplement: [2026-11-16 E058/E059 daily research supplement](https://github.com/jiae-jeong/lotto-data/blob/main/research/daily/2026-11-16_E058_E059_SUPPLEMENT.md)

1251 remains STRICT_FAIL / NOT READY. No candidate numbers or final purchase lines were generated; no fallback, freeze, or seal was created.
