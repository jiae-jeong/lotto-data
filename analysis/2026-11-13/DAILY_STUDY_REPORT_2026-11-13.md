# 일일 로또 연구 보고 — 2026-11-13

## 1. 오늘의 신규 연구

**실제 구매 5줄의 후보선정 실패와 조합/배치 실패를 조건부 정확계산으로 분리했다.**

기존 11/12 exact-null audit는 고정된 30개 후보은행을 다섯 개의 서로 겹치지 않는 6개 티켓으로 나눈 경우를 검증했다. 오늘은 그와 다른 질문으로, GitHub에서 실제 구매 원본이 확인되는 1247·1248회 두 포트폴리오의 실제 티켓 중복 구조를 그대로 고정하고, 후보은행에 남은 당첨번호 수를 조건으로 모든 가능한 당첨 배치를 정확 열거했다. 1244~1249회는 이미 노출된 live-history 진단자료이며 untouched holdout으로 취급하지 않았다.

## 2. 오늘 실제 실행한 계산

- 1247·1248회 canonical ACTUAL_PURCHASE 원본을 확인하고, 1246회는 서로 다른 사전 기록 두 개와 구매 영수증 부재로 계속 제외했다.
- 1247·1248회 각각에 대해 5줄의 고유번호 합집합 크기, 합집합 안에 남은 당첨번호 수, 줄별 적중분포, `max_hit`, any2+/any3+/any4+, 중복 당첨번호 노출 수, (M-max\_hit)를 계산했다.
- 후보/합집합 단계는 고정 합집합 크기 (U)의 정확한 초기하분포 (X\sim\operatorname{Hypergeometric}(45,U,6))로 비교했다.
- 조합/배치 단계는 실제 티켓 중복 기하를 고정한 뒤 `C(U,M)`개 부분집합을 전수 열거했다: 1247회 560개, 1248회 8,568개. Monte Carlo 근사값이 아니라 정확 열거 결과다.
- lotto_data.csv 원문 SHA-256을 오늘 다시 계산해 preregistered SHA-256과 대조했다.
- H1250 V2 preregistration, runner, 6개 frozen dependency, workflow blob의 Git blob SHA를 재확인했다.

## 3. 실제 수치 결과

| 회차 | 5줄 합집합 고유수 | 합집합에 포함된 당첨수 | 합집합 회수율 | 누락 당첨수 | 줄별 적중분포 | max_hit | any2+ | any3+ | any4+ | 중복 당첨 노출 | (M-max\_hit) |
|---|---:|---:|---:|---:|---|---:|---|---|---|---:|---:|
| 1247 | 16 | 3/6 | 50.0% | 3 | 2,1,2,1,1 | 2 | O | X | X | 4 | 1 |
| 1248 | 18 | 5/6 | 83.3% | 1 | 3,1,2,1,1 | 3 | O | O | X | 3 | 2 |

### 후보/합집합 단계의 정확 무작위 기준

- 1247: (U=16), 무작위 고정 16개 집합의 기대 당첨수는 2.1333개. 관측된 3개 이상을 얻을 확률은 정확히 **35.8480%**.
- 1248: (U=18), 기대 당첨수는 2.4000개. 관측된 5개 이상을 얻을 확률은 정확히 **3.0681%**.

1248의 단일 회차 3.07% 꼬리값은 설명용 진단치다. 이미 노출된 한 회차이고 사후 관측값이므로 모델 우위·유의성·재현성을 주장하지 않는다.

### 조합/배치 단계의 조건부 정확 기준

| 지표 | 1247회 (560개 열거) | 1248회 (8,568개 열거) |
|---|---:|---:|
| 조건부 기대 max_hit | 2.0411 | 2.7875 |
| 조건부 P(any2+) | 88.2143% | 100.0000% |
| 조건부 P(any3+) | 15.8929% | 67.7521% |
| 조건부 P(any4+) | 0.0000% | 10.6443% |
| 조건부 기대 당첨번호 노출횟수 | 5.6250 | 8.3333 |
| 관측 노출횟수 이상일 확률 | 28.3929% | 72.8758% |

두 회차의 관측 max_hit와 배치 간격은 고정된 실제 티켓 구조에서 흔히 나오는 범위였다. 따라서 이 두 건만 보면 조합기가 당첨번호를 한 줄에 모으는 능력 자체가 특별히 나빴다고 볼 근거는 없다. 반면 30개 티켓 슬롯에 사용된 고유번호가 16개·18개에 그쳐, 후보/합집합 단계의 폭이 좁았고 당첨번호가 여러 줄에 반복 노출된 현상이 확인된다. 다만 두 회차의 진단만으로 넓은 합집합이나 분산 allocator가 더 낫다고 결론내릴 수는 없다.

## 4. 후보 recall 및 기존 모델 성적표

오늘 새 candidate ranking 모델은 만들거나 재선정하지 않았다. 최신 기존 scorecard(11/12, cutoff 1249)는 1,049개 대상 회차, matched random 209,800세트를 포함한다. K=10/15/20/25/30의 최고 평균 recall 차이는 각각 **+0.00552 / +0.00553 / +0.00327 / +0.00192 / +0.00405**였다. 그러나 K=25·30에서는 같은 scorecard의 3+ 포착률 차이가 음수였다. 평균 recall의 작은 양의 차이만으로 any2·any3 동시 robust gain을 주장하거나 champion으로 승격하지 않는다.

오늘 새로 계산한 두 actual-purchase 포트폴리오의 합집합 회수율(3/6, 5/6)은 `candidate_recall@K` scorecard와 다른 측정이다. 이를 TOP10/15/20/25/30 성적으로 섞지 않았다.

## 5. 데이터·사전등록·누수 감사

- 데이터 cutoff 1249, 1~1249회 연속 1,249행, 본번호 6개 중복 없음·1~45 범위 및 보너스 범위 검사 통과.
- Git blob SHA: `d012ac7f2395e70466f0c50b71b949515dea1def`.
- 오늘 재계산한 raw SHA-256: `a5996af8b842799d777beae0abeef9767f79726870e4d78d6683dfb0fe4802e7`; H1250 preregistered SHA-256과 일치.
- H1250 V2 preregistration의 runner 및 6개 frozen dependency가 모두 등록 blob SHA와 일치(7/7). workflow blob도 append-only post-registration audit와 일치.
- 단, hash/integrity PASS는 계산 실행 PASS 또는 predictive strict PASS가 아니다.
- 1244~1249회는 노출된 live-history 진단자료로만 취급했다.

## 6. 1250회 strict gate / 금요일 준비 판정

**STRICT_PASS_NOT_READY**

최신 저장된 1250 gate는 검증 모델 0개, ready file 없음, max_hits·any2·any3·winning_union_coverage·any2 block stability 다섯 항목 모두 미통과 상태다. H1250-A/B V2의 849-target outer runner와 7,000회 moving-block bootstrap은 아직 실행되지 않았다. 해당 workflow는 수동 dispatch 전용이며, 확인한 최근 100개 Actions run에서 해당 workflow run을 찾지 못했다. 연결된 GitHub 작업에는 workflow-dispatch 실행 기능이 노출되지 않았다.

따라서 오늘은 임계값을 낮추거나 fallback을 strict PASS로 승격하지 않았다. **1250회 strict PASS 모델이 없으므로 strict PASS 최종 구매 5줄을 내지 않는다.** final/fallback 조합도 새로 만들거나 출력하지 않았다.

## 7. 남은 미해결 문제와 다음 실험 1~3개

1. H1250-A/B V2 runner를 원래 preregistration·cutoff·코드·seed·null·block design 그대로 실행할 수 있는 실행 경로를 확보한다. 1250 추첨 이후 실행되면 401~1249의 retrospective 분석일 뿐, 1250 prospective PASS로 소급하지 않는다.
2. 실제 구매 원본이 추가로 확보되는 회차만 대상으로 동일한 조건부 후보/allocator 분해를 누적한다. 1246 충돌과 과거 원본 미확보 회차는 임의 복원하지 않는다.
3. 1250 결과가 공개된 뒤에는 사전 봉인된 prospective artifact만 평가하고, 1251용 연구축·코드·계수·gate는 1250 결과를 본 뒤 소급 수정하지 않은 별도 사전등록으로 관리한다.

## 8. GitHub 보존

- [오늘의 exact conditional allocator JSON](https://github.com/jiae-jeong/lotto-data/blob/main/analysis/2026-11-13/ACTUAL_PURCHASE_CONDITIONAL_ALLOCATOR_AUDIT_2026-11-13.json)
- [오늘의 상세 audit report](https://github.com/jiae-jeong/lotto-data/blob/main/analysis/2026-11-13/ACTUAL_PURCHASE_CONDITIONAL_ALLOCATOR_AUDIT_2026-11-13.md)
- [1250 strict status 2026-11-13](https://github.com/jiae-jeong/lotto-data/blob/main/research/weekly_purchase/1250/STRICT_PASS_STATUS_1250_20261113.json)

원본 추천 기록·오답노트·기존 preregistration·freeze/seal 기록은 덮어쓰지 않았다. 오늘 보고서에는 후보번호와 최종 구매조합을 포함하지 않는다.

## 9. Anti-repetition gate 및 연구 queue 연결

오늘은 최근 완료된 연구를 주 연구로 반복하지 않았다. E010 family de-correlation, E011 nested 3+/4+ tail, E012 exact tail power, E013 component leave-one-out, E014 model agreement/disagreement, E015 two-component drop, E016 vote-depth calibration, E019 three-ticket coverage의 기존 완료·검증 기록을 확인했다. E010/E011의 보정 후 양의 비교는 각각 0건이었고, 10/12 nested regime selector D001~D003도 모두 WEAK로 남아 있어 해당 모델을 재선정하거나 임계값을 다시 탐색하지 않았다.

기존 E018 실제 구매 실패 분해는 1245 sealed source만 확보되어 있었고, 회차별 component rank vector가 없어 blocked 상태였다. 오늘은 canonical ACTUAL_PURCHASE 1247·1248 원본을 추가로 찾아 정확 조건부 allocator 분해를 수행했으므로 E018의 portfolio-level 진단은 부분 진전했다. 다만 당시 번호별 component rank 및 제외 사유 trace는 여전히 없어 signal-level inclusion/exclusion attribution은 미완료다. 누락 원본을 추정하지 않았다.

## 10. 과거 원본의 추가 구분

- 1244에서 찾은 단일 티켓 인용은 `POST_DRAW_QUOTATION`이며, 추첨 전 원본·당시 cutoff·모델·선정/제외 이유가 없어 폐쇄루프 성적에 포함하지 않았다.
- 1245는 봉인된 V4 모델 원본 3개와 error-note 집계가 있지만 실제 구매 영수증이 확인되지 않아 actual-purchase 표본으로 세지 않았다.
- 1248의 11/01 사후 오답노트 원본을 확인했다. 당시 이미 후보 합집합 누락과 조합 간격을 구분했으며, 오늘 계산은 여기에 정확 조건부 기준을 추가했다. 관측된 (M-max\_hit) 간격은 고정된 티켓 구조의 조건부 분포에서 흔한 값이므로, 간격이 존재한다는 사실만으로 allocator가 열등했다고 판단하지 않는다.

따라서 현재 확인 가능한 canonical actual-purchase 표본은 1247·1248 두 회차뿐이다. 1244 인용, 1245 모델 원본, 1246 충돌 기록을 실제 구매 결과로 합산하지 않았다.
