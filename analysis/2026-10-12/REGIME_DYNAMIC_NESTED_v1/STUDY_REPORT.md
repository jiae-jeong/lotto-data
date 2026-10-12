# Regime detection / dynamic model selection — 2026-10-12 v1

## NEW STUDY

질문: 목표 회차 이전에 관찰한 모델 성과의 상승 국면이 다음 회차에도 유지되는가? 창/임계값을 선택하는 과정까지 nested walk-forward하면 고정 B 및 동일가중 대조군보다 나은가?

기준 HEAD: `857bea9a7b258c2033f7e752808bb3e52d6de9eb`. 1~1245 검증 스냅샷 사용. 원본 1~1244와 prefix 동일. 기존 8,352개 B 예측은 재사용하고 누락된 1245 한 회차만 원본 B 함수를 호출했다.
3 신규 전략, 645개 outer 목표(601~1245), 1,935개 주평가 예측. 12개 내부 정책 ×845회=10,140개 inner 예측. 5개 고정/랜덤 대조군을 포함한 신규 티켓 평가 5,160개. 기존 B 8개 ×645회 대조는 재사용한 역사적 예측의 같은 구간 평가다.

D001은 평균 적중, D002는 2+ 목표, D003은 두 인접 창의 성과 변화 z 국면을 사용한다. 각 t의 내부 정책은 t-1 이전 성과만 보고 결정하며, 외부 정책은 t-200..t-1의 내부 정책 평가만 보고 설정을 선택한다. tie-break 고정.

**POST_HOC_EXPLORATORY**: 오늘 코드 평가 전에 규칙/hash를 봉인했지만 과거 결과 공개 후 설계했다. 최근/역사 holdout을 untouched라고 부르지 않는다. 최근 좋아 보이는 모델을 결과를 본 뒤 최종 선정하지 않는다. 모든 전략·블록·실패를 보고한다.

## NEW FINDING

| 전략/고정대조 | n | 평균 | 2+ | 3+ | 4+ | Δ평균 vs random |
|---|---:|---:|---:|---:|---:|---:|
|long_frequency|645|0.741085|15.5039%|2.7907%|0.0000%|-0.058915|
|current_gap|645|0.804651|17.3643%|1.3953%|0.0000%|+0.004651|
|frequency_plus_gap|645|0.801550|18.7597%|2.1705%|0.3101%|+0.001550|
|recent_momentum|645|0.714729|14.5736%|1.0853%|0.0000%|-0.085271|
|structure_profile|645|0.730233|16.1240%|1.7054%|0.0000%|-0.069767|
|pair_association|645|0.818605|19.2248%|1.0853%|0.0000%|+0.018605|
|triple_association|645|0.798450|17.6744%|2.1705%|0.0000%|-0.001550|
|combined_equal_rank|645|0.745736|14.8837%|1.5504%|0.3101%|-0.054264|
|equal_weight_ticket_vote|645|0.768992|16.7442%|2.0155%|0.3101%|-0.031008|
|uniform_seeded_stream|645|0.862016|21.0853%|3.2558%|0.1550%|+0.062016|
|fixed_mean_w50|645|0.745736|15.5039%|0.9302%|0.0000%|-0.054264|
|fixed_2plus_w50|645|0.734884|15.9690%|0.7752%|0.0000%|-0.065116|
|fixed_regime_w50_z1.5|645|0.730233|14.4186%|0.9302%|0.0000%|-0.069767|
|D001_nested_mean|645|0.764341|16.7442%|1.0853%|0.0000%|-0.035659|
|D002_nested_2plus|645|0.786047|16.1240%|1.3953%|0.1550%|-0.013953|
|D003_nested_regime|645|0.739535|15.0388%|0.7752%|0.1550%|-0.060465|
|exact uniform baseline|645|0.800000|17.5308%|2.3834%|0.1393%|0.000000|

### 주평가와 불확실성

- D001_nested_mean: WEAK; 평균 block-bootstrap 95% CI [0.7085, 0.8186]; 12검정 Holm 최소 p=1.000000. 추천 적용 없음.
- D002_nested_2plus: WEAK; 평균 block-bootstrap 95% CI [0.7318, 0.8403]; 12검정 Holm 최소 p=1.000000. 추천 적용 없음.
- D003_nested_regime: WEAK; 평균 block-bootstrap 95% CI [0.6853, 0.7953]; 12검정 Holm 최소 p=1.000000. 추천 적용 없음.

uniform 귀무가설은 독립 균등 6/45 추첨이다. 과거 정보로 선택한 6개 티켓의 조건부 hit 분포도 hypergeometric이다. 평균 합계의 정확 convolution과 2+/3+/4+ binomial 상위 꼬리를 계산했다. Holm12는 이번 3전략×4지표만 보정하며 전체 누적 탐색의 사후선택을 제거하지 않는다.
paired_comparisons.csv는 두 ensemble 대조군과의 paired 차이를 circular block20 bootstrap 5,000회로 계산한다. 24개 exploratory 검정에 Holm 적용. 시계열 재표집 CI는 참고 추정이며 adaptive process의 정확 재시뮬레이션 검정은 아니다.

### 최근 및 역사 holdout

| 전략 | 기간 | n | 평균 | 2+ | 3+ | 4+ |
|---|---|---:|---:|---:|---:|---:|
|D001_nested_mean|recent200|200|0.7100|15.50%|1.00%|0.00%|
|D001_nested_mean|recent100|100|0.7600|17.00%|1.00%|0.00%|
|D001_nested_mean|recent50|50|0.7400|16.00%|0.00%|0.00%|
|D001_nested_mean|historical_holdout_1201_1245|45|0.7556|15.56%|0.00%|0.00%|
|D002_nested_2plus|recent200|200|0.7600|14.00%|1.00%|0.00%|
|D002_nested_2plus|recent100|100|0.8400|16.00%|2.00%|0.00%|
|D002_nested_2plus|recent50|50|0.8400|16.00%|4.00%|0.00%|
|D002_nested_2plus|historical_holdout_1201_1245|45|0.8667|15.56%|4.44%|0.00%|
|D003_nested_regime|recent200|200|0.7200|14.50%|0.00%|0.00%|
|D003_nested_regime|recent100|100|0.7100|15.00%|0.00%|0.00%|
|D003_nested_regime|recent50|50|0.6600|10.00%|0.00%|0.00%|
|D003_nested_regime|historical_holdout_1201_1245|45|0.6889|11.11%|0.00%|0.00%|

### 국면의 실제 지속성

| B component | positive-change 표본 | 다음 평균 | 미감지 평균 |
|---|---:|---:|---:|
|long_frequency|29|0.5862068965517241|0.7483766233766234|
|current_gap|70|0.9|0.7930434782608695|
|frequency_plus_gap|39|0.5128205128205128|0.8201320132013201|
|recent_momentum|54|0.7407407407407407|0.7123519458544839|
|structure_profile|29|0.5172413793103449|0.7402597402597403|
|pair_association|56|0.8392857142857143|0.8166383701188455|
|triple_association|35|0.7428571428571429|0.8016393442622951|

감지 표본 30 미만은 SMALL_SAMPLE. 국면 감지는 각 모델별 z>=1.5/창50을 사전 고정한 진단이다. 서로 같은 추첨을 공유하는 모델 행을 독립 표본으로 풀링하지 않는다. 4+ 사건은 적어 이 지표만으로 국면 선택의 우위를 판정하지 않는다.
model_correlation.csv에는 28쌍의 hit correlation/티켓 overlap이 있다. 동적 모델은 한 component만 선택해 유사 모델을 독립 표로 가산하지 않는다. seven-ticket 동일가중은 중복 신호를 그대로 둔 명시적 대조군이며 B combined_equal_rank와 정의가 다르다.

## MAINTENANCE/RECHECK

최신 main/필수 문서 전체 읽기, 누적 결과 anti-repetition gate, 원자료·스냅샷 검증, 중첩 B 레코드 제거, 5개 prefix 40티켓 캐시 대조, 1245 단일 target 확장만 수행했다. B 전체 재현, 기존 대규모 MC, H001/H002, 관계 검정, 기본 통계 재실행을 신규 성과로 세지 않았다.
추적된 기존 파일 352개 hash 보존 PASS. 목표 이후 outcome을 변조해 5개 cutoff의 3개 전략 선택/설정 불변 PASS. leakage 위반 0. 예측 추천/최종 3줄 생성 없음. 1245 실제 결과는 이번 역사 평가 outcome으로만 사용; 1245 결정 입력은 <=1244이다.

## NEXT TEST

1. 이번 실패/보류를 유지하고, future1246+에서 별도 prospective protocol로 고정한 선택기만 평가한다. 미래 성과를 본 후 창/threshold 재선택 금지.
2. 성과 추세의 지속성이 불확실하면 계열 독립성과 ensemble de-correlation을 별도 가설로 검증한다. 원시 static 우승 모델을 사후 승격하지 않는다.
3. 3+/4+ 목표는 이번 2+ 최적화와 분리해 신규 사전 규칙·다중검정 범위를 정한 후 평가한다. 기존 known-outcome 구간을 untouched로 다시 명명하지 않는다.

## 실행 및 보존

재현: `python run_study.py --repository <clean pinned 857bea9 checkout> --out <new empty output directory>`; 기존 output 존재 시 거부. 필요한 런타임은 Python+NumPy. FROZEN_SPEC, trace, inner outcomes, CSV, source/input SHA, 실행 audit 보존.
Git DNS 차단은 permissioned fetch로 우회했고 최신 main 별도 checkout을 사용했다. SciPy가 없어 정확 null 계산은 NumPy/stdlib로 수행했다. 미확보 legacy A/C/contrarian 원본은 모델 선택에서 제외했으며 복원/추정하지 않았다. 이 연구 완료는 전체 MASTER 체크리스트나 예측 우위 확정을 뜻하지 않는다.
