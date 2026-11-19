# Study Batch 001 — 신규 모델 walk-forward 연구

- 데이터: `C:\Users\user\Documents\Codex\2026-10-06\cloud-x20\work\lotto-data\lotto_data.csv` (1~1244회, 전량 연속성 검증; 입력 loader가 1244회까지만 읽음)
- 예측 평가: 목표 201~1244, expanding 1-step-ahead, 각 t는 1~t-1만 학습에 전달.
- 가설/실험 수: 8 / 8; 신규 모델 계열: 8; 신규 변수군: 8. Expanding 1,044×8=8,352건, rolling300 744×8=5,952건, 합계 14,304 walk-forward predictions.
- 전체 평가 회차: 1,044 unique targets. 실패(전체 평균이 random 이하) 5; HOLD(전체 평균 초과) 3; PROMISING 0.
- 모든 연구는 이번 프로젝트 기존 결과 확인 후 설계된 사후 연구로 `POST_HOC_ONLY`; holdout은 untouched가 아닙니다.

## 기존 연구와 중복 점검

기존 `research_registry.csv`는 템플릿(기등록 평가 가설 없음)이었고 `model_family_catalog.csv`의 8개 B모델 계열을 확인했습니다. 신규 8개는 multi-window frequency, gap regime hazard, momentum state transition, conditional probability, structure transition, pair residual, triple residual, family-balanced hybrid입니다. 원시 빈도·관계 신호를 재사용하므로 완전히 독립적인 증거라고 보지 않습니다.

## 모델별 성능

| 순위 | 모델 | 평균 | 2+ | 3+ | 4+ | 5+ | 6 | Δ 평균 | Δ 2+ |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | family_balanced_hybrid | 0.8103 | 18.39% | 2.30% | 0.00% | 0.00% | 0.00% | +0.0103 | +0.86% |
| 2 | pair_residual_node | 0.8046 | 16.38% | 2.20% | 0.38% | 0.00% | 0.00% | +0.0046 | -1.15% |
| 3 | triple_residual_node | 0.8027 | 16.28% | 2.11% | 0.38% | 0.00% | 0.00% | +0.0027 | -1.25% |
| 4 | momentum_state_transition | 0.7969 | 18.58% | 2.11% | 0.10% | 0.00% | 0.00% | -0.0031 | +1.05% |
| 5 | conditional_probability | 0.7950 | 18.58% | 2.59% | 0.10% | 0.00% | 0.00% | -0.0050 | +1.05% |
| 6 | multi_window_frequency | 0.7845 | 16.76% | 2.59% | 0.10% | 0.00% | 0.00% | -0.0155 | -0.77% |
| 7 | gap_regime_hazard | 0.7787 | 17.53% | 1.82% | 0.10% | 0.00% | 0.00% | -0.0213 | -0.00% |
| 8 | structure_transition | 0.7730 | 17.15% | 3.45% | 0.00% | 0.00% | 0.00% | -0.0270 | -0.39% |

정확 균등 무작위 기준선: 평균 0.800000, 2+ 17.5308%, 3+ 2.3834%, 4+ 0.1393%, 5+ 0.0029%, 6 0.000012%.

## 최근 구간 및 chronological blocks

`model_metrics.csv`에 overall, recent 200/100/50, 그리고 네 chronological block의 모든 지표가 있습니다. Holdout 구간은 연구 후 선택한 최근 관점이므로 독립 검증이 아닙니다.

별도 rolling300 결과는 `rolling300_predictions.csv`와 `rolling300_metrics.csv`에 있습니다 (targets 501~1244, cutoff 직전 300회만 학습). rolling 전체에서 gap_regime_hazard 평균 0.8280 (+0.0280 vs random, 2+ 19.22%), pair_residual_node 0.8132, triple_residual_node 0.8118이 평균 기준을 넘었습니다. 특히 gap 모델은 최근200/100/50 평균이 각각 0.925/0.920/0.940으로 높지만 expanding 최근200/100/50에서는 0.750/0.650/0.460으로 크게 낮았습니다. 같은 가설이 창 설정에 따라 급변하므로 regime 안정성이나 과적합/우연 가능성을 우선 의심해야 하며, 유망 신호로 취급하지 않았습니다.

| 모델 | 구간 | n | 평균 | 2+ | 평균 차이 |
|---|---|---:|---:|---:|---:|
| multi_window_frequency | recent200 | 200 | 0.7500 | 15.50% | -0.0500 |
| multi_window_frequency | recent100 | 100 | 0.7200 | 12.00% | -0.0800 |
| multi_window_frequency | recent50 | 50 | 0.7800 | 10.00% | -0.0200 |
| gap_regime_hazard | recent200 | 200 | 0.7500 | 14.50% | -0.0500 |
| gap_regime_hazard | recent100 | 100 | 0.6500 | 9.00% | -0.1500 |
| gap_regime_hazard | recent50 | 50 | 0.4600 | 2.00% | -0.3400 |
| momentum_state_transition | recent200 | 200 | 0.7400 | 15.00% | -0.0600 |
| momentum_state_transition | recent100 | 100 | 0.7500 | 13.00% | -0.0500 |
| momentum_state_transition | recent50 | 50 | 0.7200 | 10.00% | -0.0800 |
| conditional_probability | recent200 | 200 | 0.7900 | 19.00% | -0.0100 |
| conditional_probability | recent100 | 100 | 0.7400 | 17.00% | -0.0600 |
| conditional_probability | recent50 | 50 | 0.6400 | 16.00% | -0.1600 |
| structure_transition | recent200 | 200 | 0.6800 | 16.00% | -0.1200 |
| structure_transition | recent100 | 100 | 0.6500 | 13.00% | -0.1500 |
| structure_transition | recent50 | 50 | 0.5400 | 10.00% | -0.2600 |
| pair_residual_node | recent200 | 200 | 0.8250 | 17.50% | +0.0250 |
| pair_residual_node | recent100 | 100 | 0.7800 | 17.00% | -0.0200 |
| pair_residual_node | recent50 | 50 | 0.9000 | 22.00% | +0.1000 |
| triple_residual_node | recent200 | 200 | 0.8100 | 16.50% | +0.0100 |
| triple_residual_node | recent100 | 100 | 0.7600 | 16.00% | -0.0400 |
| triple_residual_node | recent50 | 50 | 0.8400 | 20.00% | +0.0400 |
| family_balanced_hybrid | recent200 | 200 | 0.7850 | 17.00% | -0.0150 |
| family_balanced_hybrid | recent100 | 100 | 0.7700 | 17.00% | -0.0300 |
| family_balanced_hybrid | recent50 | 50 | 0.7200 | 16.00% | -0.0800 |

## 질문별 답변

1. 새로운 정보: 후보 정의상 다른 시간창 결합·전이·조건부 hazard·구조전이 특징을 시험했지만, 이 자료에서 B-v1보다 독립적인 예측 정보가 확인됐다고 결론 내릴 수 없습니다.
2. Random 초과: expanding 전체 평균은 family_balanced_hybrid, pair_residual_node, triple_residual_node에서 소폭 초과했고 rolling300은 gap/pair/triple에서 초과했습니다. 구간 간 생존이 일관되지 않고 전체 평균 bootstrap 95% 구간이 기준값 0.8을 포함하며, 동시 탐색 및 사후 설계가 있어 반복 가능한 신호로 인정하지 않았습니다.
3. 최근 유지: expanding과 rolling의 gap 결과가 반대로 움직이고, 대부분 모델의 recent50/100/200이 일관되지 않아 유지된다고 판단할 수 없습니다.
4. Holdout 유지: untouched holdout은 이번 데이터 안에 남겨두지 않았습니다. 최근 구간은 가설 구성 후 살핀 사후 holdout입니다.
5. B-v1 독립성: 신규 모델 간 중복도는 `model_correlation.csv`, 기존 B-v1과의 비교는 `b_model_comparison.csv`에 기록했습니다. pair/triple residual 티켓은 기존 B-v1 관계 모델과 평균 약 1.64개 번호가 겹치고 평균 hit correlation 약 0.14였으며, 완전히 독립적인 증거는 아닙니다.
6. 과적합/우연: recent windows, 여러 변형, 다중 pair/triple 탐색, 불균형 구조 전이, 반복된 조건 검색이 selection bias를 유발할 수 있습니다. PROMISING은 0입니다.
7. 다음 연구: 이번 정의를 사전등록된 고정 규칙으로 동결하고 신규 회차가 추가된 뒤 untouched prospective 평가를 수행합니다. 조건부/구조 모델은 표본수를 늘리고 calibration을 검토합니다.

## 실패 및 다음 단계

모든 모델과 구간의 분류는 `failure_registry.csv`에 저장했습니다. 전체 random 이하 모델은 WEAK, 초과 모델도 HOLD에 머물며 생존 승격은 없습니다. 1245회 추천번호 또는 최종 구매번호는 생성하지 않았습니다.

## 시간·조건부·구조·관계 진단

- `number_temporal_features.csv`: 45개 번호별 10/20/30/50/100/200/300회 출현 수·비율·장기 차이, 창 방향 일관성, 평균/중앙 재출현 간격, 즉시/1회 skip/2회 이상 skip, 최근20 상태 전환.
- `conditional_number_transitions.csv`: 번호별 직전 회차 포함 여부, 최근3/5회 출현횟수, 최근10회 hot/cold 조건별 다음 회차 포함률과 Wilson 95% 구간. 표본 30 미만 플래그와 cutoff 규칙도 기록.
- `structure_transition_analysis.csv`: 홀짝 수, 저/고 수, 합계 구간, 5구간 분포, 연속쌍, 끝수 중복, 직전 회차 overlap, cluster의 현재→다음 상태 전이확률·marginal 차이·표본수.
- `pair_triple_temporal_stability.csv`: 990 pair와 14,190 triple 각각의 전체/최근50/100/200/전후반 빈도 및 회차당 변화. 537/990 pair는 최근50에 한 번 이상 나왔고, 968/14,190 triple도 최근50에 한 번 이상 나왔습니다. 희소 관계가 많고 다중비교 보정이 없어 이는 탐색량이지 예측 근거가 아닙니다.
- `bootstrap_confidence_intervals.csv`: seed 20261008로 모델별 overall/recent200/100/50 평균 hit와 2+ 비율을 2,000회 bootstrap한 95% 구간. 단순 재표집은 시계열 의존을 보존하지 않으므로 참고용입니다.
- `study_results.csv`는 expanding 모델별 기간별 요약, `walkforward_predictions.csv`는 8,352건 상세입니다. rolling 추가 결과는 별도 파일입니다. 두 prediction 파일에서 cutoff 위반 0건이며 목표 회차는 201~1244에 한정됩니다.
