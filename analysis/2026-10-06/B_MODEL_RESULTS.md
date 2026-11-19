# B 모델 롤링 워크포워드 백테스트 — 2026-10-06

데이터 1~1244회. 예측 t는 t-1까지의 정보만 사용. 총 평가 레코드 33408(중첩 holdout 포함).

## 기준선
균등 6/45: 평균 적중 0.800000, 분산 0.614545, 2+ 17.5308%, 3+ 2.3834%, 4+ 0.1393%, 5+ 0.0029%.

## 비중첩 50회 블록 7개 / 350회 예측

| 모델 | 분류 | 평균 | 2+ | 기준선 대비 평균 | 기준선 대비 2+ | 우세 블록 |
|---|---|---:|---:|---:|---:|---:|
| long_frequency | ADDITIONAL VALIDATION | 0.737 | 14.86% | -0.063 | -2.67pp | 2/7 |
| current_gap | ADDITIONAL VALIDATION | 0.774 | 15.71% | -0.026 | -1.82pp | 4/7 |
| frequency_plus_gap | ADDITIONAL VALIDATION | 0.829 | 20.57% | +0.029 | +3.04pp | 5/7 |
| recent_momentum | ADDITIONAL VALIDATION | 0.746 | 14.57% | -0.054 | -2.96pp | 3/7 |
| structure_profile | ADDITIONAL VALIDATION | 0.851 | 19.14% | +0.051 | +1.61pp | 4/7 |
| pair_association | ADDITIONAL VALIDATION | 0.834 | 18.00% | +0.034 | +0.47pp | 4/7 |
| triple_association | ADDITIONAL VALIDATION | 0.826 | 18.57% | +0.026 | +1.04pp | 5/7 |
| combined_equal_rank | HOLD | 0.803 | 18.57% | +0.003 | +1.04pp | 3/7 |

KEEP 없음.

## 해석
- frequency_plus_gap, structure_profile, pair_association, triple_association은 일부 긍정 신호가 있으나 사전 KEEP 기준 미충족.
- combined_equal_rank는 기준선에 매우 가까워 HOLD.
- long_frequency 및 recent_momentum은 전체적으로 기준선보다 낮았으나 사전 REDUCE 기준도 충족하지 못해 ADDITIONAL VALIDATION.
- 통계적 유의성 검정/신뢰구간/다중검정 보정은 수행하지 않음.

## 시간 변화
frequency_plus_gap은 7개 블록 중 5개에서 평균 적중 기준 우세. structure_profile 4/7, pair 4/7, triple 5/7.
최근 블록에서도 frequency_plus_gap 1151~1200: 0.880 / 2+ 24.0%; structure_profile 0.820 / 20.0%; triple 0.880 / 20.0%. 이는 추가 검증 대상이지 예측력 확정이 아님.

## 다음 검증
- frequency_plus_gap / structure_profile / pair / triple을 독립 기간 및 추가 walk-forward에서 재검증.
- 과거 추천/오답노트의 신호 사용과 비교.
- 유의성/신뢰구간을 별도로 계산.
- C 결합에는 반복 검증 전 신호를 자동 채택하지 않음.

추천번호는 생성하지 않음.
