# E047 — 실제 구매기록의 후보 도달·조합 배치 분해

**분류:** 탐색적 사후 진단. 확증 검증·모델 승격·strict PASS 근거가 아님.

## 오늘의 새 연구 질문
실제 구매가 확인된 1247·1248회에서 당첨번호가 사전 지정된 6개 기준 랭커의 TOP10/15/20/25/30에 얼마나 도달했는지, 실제 구매 포트폴리오가 그중 몇 개를 담았는지, 담긴 번호가 최선 한 줄에 얼마나 모였는지를 분리했다.

## 원본 및 무결성
- 원자료: `lotto_data.csv`, 회차 1~1249 연속 1,249개 행
- Git blob: `d012ac7f2395e70466f0c50b71b949515dea1def`
- 독립 재계산 SHA-256: `a5996af8b842799d777beae0abeef9767f79726870e4d78d6683dfb0fe4802e7` — 저장소의 11/14 기준 해시와 일치
- 빈 물리 행 2개는 회차 레코드 수 계산에서 제외. 번호 6개 고유성·1~45 범위·보너스 분리·회차 연속성 검사 통과
- 1247은 cutoff 1246, 1248은 cutoff 1247만 사용. 대상 회차 당첨번호는 순위 계산 이후에만 대조
- 1246은 두 개의 상충하는 사전 추천 세트와 영수증 부재로 제외. 1245 오류 집계는 구매 영수증이 확인되지 않은 V4 추천이므로 실제 구매 표본에 포함하지 않음

## 실제 구매 포트폴리오 결과

| 회차 | 실제 티켓 수 | 포트폴리오 고유 번호 | 당첨번호의 포트폴리오 포함 | 줄별 적중 | 최다 적중 | 포트폴리오 포함수−최다 적중 |
|---|---:|---:|---:|---|---:|---:|
| 1247 | 5 | 16 | 3/6 | 2, 1, 2, 1, 1 | 2 | 1 |
| 1248 | 5 | 18 | 5/6 | 3, 1, 2, 1, 1 | 3 | 2 |

## 기준 랭커의 후보 도달

각 랭커의 셀은 해당 K 안에 포함된 실제 당첨번호 수(6개 중)다. 무작위 균등 K-부분집합의 정확한 기대 포함수는 K=10/15/20/25/30에서 각각 1.333/2.000/2.667/3.333/4.000개다. 두 회차의 단일 결과이므로 차이를 유의성이나 일반화된 우위로 해석하지 않는다.

### 1247회

| 기준 랭커 | @10 | @15 | @20 | @25 | @30 |
|---|---:|---:|---:|---:|---:|
| recent30 | 2 | 2 | 2 | 2 | 3 |
| gap | 3 | 4 | 4 | 4 | 4 |
| momentum | 0 | 0 | 0 | 2 | 2 |
| balanced | 2 | 3 | 4 | 5 | 5 |
| contrarian | 4 | 4 | 4 | 4 | 4 |
| consensus | 3 | 3 | 3 | 3 | 3 |
| 6개 랭커의 TOP-K 합집합 | **6** | **6** | **6** | **6** | **6** |

### 1248회

| 기준 랭커 | @10 | @15 | @20 | @25 | @30 |
|---|---:|---:|---:|---:|---:|
| recent30 | 2 | 4 | 4 | 4 | 4 |
| gap | 0 | 1 | 1 | 1 | 3 |
| momentum | 3 | 3 | 5 | 6 | 6 |
| balanced | 1 | 2 | 2 | 3 | 4 |
| contrarian | 0 | 1 | 1 | 2 | 2 |
| consensus | 2 | 3 | 4 | 5 | 5 |
| 6개 랭커의 TOP-K 합집합 | **4** | **5** | **6** | **6** | **6** |

## 조합기 기하를 보존한 정확 무작위 기준
각 실제 5줄의 번호-줄 포함관계를 incidence mask로 묶어 다변량 초기하분포로 계산했다. 두 포트폴리오 각각에서 가능한 `C(45,6)=8,145,060`개 당첨 집합을 전부 계수했고, 분모 일치 검증을 통과했다.

| 회차 | 기하 보존 null 평균 max-hit | null any2+ | null any3+ | null any4+ | null 기대 union coverage |
|---|---:|---:|---:|---:|---:|
| 1247 | 1.5437 | 0.5001 | 0.0954 | 0.0064 | 2.1333 |
| 1248 | 1.6271 | 0.5507 | 0.1057 | 0.0069 | 2.4000 |

이 값은 각 회차의 고정된 티켓 중복 기하에 대한 정확 기준선이다. 실제 관측은 회차당 한 번뿐이므로 null 평균보다 높았다는 사실만으로 모델 우위나 성능 개선을 주장하지 않는다.

## 새로 확인된 점과 한계
1. 두 회차 모두 여섯 기준 랭커를 합친 TOP30 도달 집합에는 실제 당첨번호 6개가 모두 존재했다.
2. 그런데 실제 구매 포트폴리오 포함은 1247회 3/6, 1248회 5/6에 그쳤다. 기준 신호 도달과 실제 구매 집합 사이에 차이가 있었다.
3. 실제 구매 집합에 들어온 번호도 한 줄에 모이지 않았다. 포트폴리오 포함수와 최다 한 줄 적중의 차이는 각각 1개, 2개였다.
4. 다만 여섯 기준 랭커는 당시 실제 선택기의 완전한 동결 후보은행과 동일하지 않다. 따라서 특정 후보 필터가 실제로 탈락시켰다고 인과적으로 단정할 수 없다. 이는 '기준 신호 도달 ↔ 실제 구매 포함 ↔ 줄 배치'의 진단이다.
5. 표본은 구매기록이 검증된 두 회차뿐이다. 1244~1248은 오염된 live-history 진단이며 깨끗한 홀드아웃이 아니다.

## 운영 영향
- 후보 recall과 포트폴리오 배치 지표를 별도 유지한다.
- 기존 모델·가중치·gate·구매 정책은 변경하지 않는다.
- 1250회 strict status는 저장소의 최신 기록대로 `STRICT_PASS_NOT_READY`; 이 연구는 그 상태를 바꾸지 않는다.
- 1251회부터 적용되는 3줄 정책의 E045 역사 검증도 strict FAIL이며, E046은 설계 전용이다. 이번 5줄 과거 진단은 3줄 구매 준비도 근거로 전용하지 않는다.

## 다음 검증 과제
1. 실제 선택기의 당시 candidate-bank 및 단계별 selection trace 원본이 추가 확보되는지 추적해 인과적 탈락 원인을 검증한다.
2. 1246회 구매 영수증 또는 권위 있는 전달 원본이 확보되기 전까지 canonical aggregate에서 제외한다.
3. 1251+ prospective confirmation의 최소 표본 수와 완료 규칙은 정책 소유자의 사전 결정 없이는 채택하지 않는다.


---

## Provenance correction — 2026-11-14

The original E047 preregistration and result files are preserved unchanged. A subsequent provenance audit found no receipt or explicit user confirmation establishing that either preserved line set was actually purchased. Round 1247 has multiple competing preserved five-line versions; round 1248 has both a fallback file and a distinct V54 final artifact.

Accordingly, the metrics above must be interpreted only as descriptive diagnostics of the two preserved line sets, not as outcomes of actual purchased tickets. E047 is not an actual-purchase learning record, not confirmatory evidence, and not eligible for model promotion or STRICT_PASS. See E047_ACTUAL_PURCHASE_PROVENANCE_CORRECTION_20261114.json and the append-only research/DELIVERY_LOG.md correction.
