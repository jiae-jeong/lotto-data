# A_C_CONTRARIAN_REBUILT_v1

2026-10-16에 복구된 과거 개념과 살아 있는 실행 계보를 바탕으로 실제 실행 가능한 A/C/콘트라리언 후속 모델을 복원한 패키지입니다.

## 중요한 구분

이 버전은 사라진 옛 실행파일을 동일 바이트로 되살린 것이 아닙니다. 과거 대화에서 복구된 정의와 가중치, 그리고 저장소에 남아 있는 정확한 S006/구조 계보를 이용해 빈 구현 부분을 명시적으로 재구성한 `REBUILT_v1`입니다. 따라서 옛 성과를 소급해 주장하지 않습니다.

## 모델

- `A_REBUILT_v1`: 복구된 35/25/20/20 가중치(장기 빈도 / 최근100 / gap / pair)를 그대로 유지. 서로 다른 척도는 번호별 rank 45..1로 정규화하고 작은 번호 tie-break를 사용합니다. pair는 살아 있는 S006 residual-node 공식을 사용합니다.
- `C_REBUILT_v1`: 각 target t에서 t 이전에 실제로 발생한 component walk-forward 적중만 사용합니다. 최근 최대 200개 target의 평균이 0.8 이상이고, 비중첩 50개 블록 중 절반 이상이 평균 0.8 이상인 component만 살아남깁니다. 살아남은 신호는 동일 rank 가중으로 결합하며, 전부 탈락하면 과거 평균이 가장 높은 하나만 fallback으로 사용합니다.
- `CONTRARIAN_REBUILT_v1`: 고정 seed 20261016, 후보은행 5,000개. 홀짝, 저/고, 합계구간, 5구간 분포, 연속수, 끝수반복, 군집, 직전회차 중복의 Laplace-smoothed 구조 희소도 합을 최대화하여 비전형 구조 가설을 별도로 검증합니다.

## 실행

저장소 루트의 `lotto_data.csv`가 1~1245회를 포함한 상태에서:

```bash
python analysis/2026-10-16/A_C_CONTRARIAN_REBUILT_v1/rebuild_models.py
```

스크립트는 1245까지만 읽도록 고정되어 있으며 1246 후보를 만들지 않습니다.

## 보존된 출력

- `metrics.csv`: 워크포워드 요약
- `REPORT.md`: 핵심 결과/누수검사
- `EXECUTION_PROOF.json`: 행 수, C 선택통계, 원본 SHA-256, 2회 재실행 결정성 확인
- `walkforward_predictions.csv.gz.b64`: 2,935개 예측행 원자료의 gzip+base64 보존본
- `c_nested_validation.csv.gz.b64`: 3,380개 C nested validation 원자료의 gzip+base64 보존본

복원 명령 예시:

```bash
base64 -d walkforward_predictions.csv.gz.b64 | gzip -d > walkforward_predictions.csv
base64 -d c_nested_validation.csv.gz.b64 | gzip -d > c_nested_validation.csv
```

## 실행 결과 요약

| Model / window | Mean hits | Delta vs random 0.8 | 95% moving-block CI |
|---|---:|---:|---:|
| A_REBUILT_v1 201-1245 | 0.792344 | -0.007656 | [-0.046890, +0.035407] |
| A_REBUILT_v1 401-1245 | 0.802367 | +0.002367 | [-0.042604, +0.050888] |
| C_REBUILT_v1 401-1245 | 0.781065 | -0.018935 | [-0.078107, +0.040237] |
| CONTRARIAN_REBUILT_v1 201-1245 | 0.802871 | +0.002871 | [-0.045933, +0.046890] |
| CONTRARIAN_REBUILT_v1 401-1245 | 0.815385 | +0.015385 | [-0.034320, +0.066272] |

모든 신뢰구간이 0을 포함하므로 예측 우위가 검증되었다고 판정하지 않습니다. 이 패키지의 핵심 성과는 A/C/콘트라리언이 다시 실제 코드로 작동하고, 동일 입력에서 결정적으로 재현되며, 향후 개선을 위한 독립 모델 축이 복구되었다는 점입니다.
