# 2026-10-12 — 연구 해석 및 이어가기 상태 v1

## NEW STUDY

최근 모델 성과의 변화가 다음 회차에 유지되는지, 그리고 최근 성과로 모델과 설정을 선택하는 과정 자체가 고정 모델보다 나은지를 시험했다. 일곱 B component 중 모델을 고르는 세 전략과 설정 후보 12개를 평가 전에 고정했다. 모델의 과거 좋은 구간을 그대로 미래 성과로 간주하지 않고, 각 역사적 목표 회차에서 모델 선택과 창/임계값 선택을 모두 이전 회차 성과로 수행했다.

데이터는 pinned `857bea9a7b258c2033f7e752808bb3e52d6de9eb`의 검증 snapshot 1~1245회이다. 실제 신규 외부 평가: 601~1245회 645회, 세 전략 1,935건. 내부 정책 평가 10,140건. 고정 정책·동일가중·단일 균등 스트림을 포함한 신규 티켓 평가 5,160건. 무작위 기준선의 대규모 Monte Carlo 재실행은 하지 않았다.

## NEW FINDING

1. **선택한 모델의 직전 성과와 다음 회차 성과가 크게 다르다.** D001이 선택한 component의 직전 창 평균은 0.93744였지만 다음 회차 평균은 0.76434였다. D002도 0.91002 → 0.78605였다. 이는 선택에 사용한 창의 높은 성과를 out-of-window evidence로 취급하면 안 된다는 실제 실패 분해다. 이 차이를 미래 성과를 본 뒤 보정 가중치로 사용하지 않았다.

2. **국면 감지가 동적 선택을 개선했다는 증거가 없다.** D003의 평균은 0.73953, 2+는 15.04%, 3+는 0.775%, 4+는 0.155%였다. 평균 상승 국면에 실제로 전환한 것은 165/645회였고, 480회는 미감지 fallback으로 기존 combined_equal_rank를 사용했다. 국면 전환 조건이 단순 최근 최고 모델 추격을 막아도, 이 정의에서는 예측 성과가 개선되지 않았다.

3. **2+를 최적화하는 것과 고적중 꼬리 개선은 같은 일이 아니다.** D002는 고정 combined_equal_rank보다 평균 +0.04031이었지만, 정확 random 평균보다 -0.01395였다. 2+는 16.12%로 uniform 17.53%보다 낮고, 3+도 1.395%로 uniform 2.383%보다 낮았다. 동일가중 seven-ticket 대조군 대비 평균 +0.01705의 paired block-bootstrap 95% CI는 [-0.05271, +0.08837]로 0을 포함한다.

4. **최근 소구간 호조는 전체 결과와 함께 봐야 한다.** D002의 최근100/50 평균은 모두 0.84, 1201~1245 역사 slice 평균은 0.86667였다. 그러나 최근200은 0.76이고 같은 역사 slice의 2+는 15.56%로 무작위보다 낮았다. 최근100/50의 호조를 이유로 이 전략을 채택하지 않았다. 모든 slice는 retrospective이며 untouched가 아니다.

5. **모델별 감지 결과는 일관되지 않는다.** 고정 창50/z≥1.5 진단에서 current_gap의 상승 국면 70회 다음 평균은 0.9였지만 frequency_plus_gap의 39회는 0.51282, triple의 35회는 0.74286이었다. 이 모델별 차이는 사후 진단이고 correlated comparison이다. 여기서 current_gap만 골라 재평가하거나 신규 추천 규칙으로 승격하지 않았다.

6. **세 전략 모두 WEAK로 보존한다.** 이번 positive-edge 검정 family 12개의 Holm 보정 p는 모두 1.0이다. 두 ensemble과의 paired 비교 24개도 보정 후 통과 0개이다. 이는 예측 우위의 증거가 없다는 뜻이다. 모든 가능한 regime 알고리즘이 무효임을 입증한 것은 아니다. 4+ 사건 0~1개로 고적중 개선을 판단할 표본도 부족하다. 결과를 보고 창/threshold/모델군을 수정하지 않았다.

단일 seeded random 스트림의 관측 평균 0.86202는 한 realization이다. 그 값을 새 무작위 기대값으로 쓰거나 유리한 seed를 고르지 않았다. 정확 기대값은 여전히 0.8이다.

## MAINTENANCE/RECHECK

- 최신 원격 main 및 연구 checkout의 시작 HEAD가 지정 SHA와 일치했다. 기존 V3 checkout과 로컬 커밋은 유지했다.
- AGENTS.md와 LOTTO_PROJECT_PROTOCOL.md를 전체 읽었다. 10월9/10 연구, 10월12 기존 일일 보고서·automation, 가설/실패 registry, batch001과 V4의 누적 상태를 확인했다.
- snapshot 1,245행, 원자료 1,244행, 회차 연속성·본번호·범위·보너스 분리·snapshot 원본 prefix 일치를 검증했다.
- 기존 B 예측 33,408개 중 중첩 반복 25,056개를 제거하고 8,352개를 재사용했다. 원본 B 함수로 5개 cutoff의 40티켓을 확인했고, 1245 한 회차만 확장했다. 이를 오늘 B 전체 재현이라고 보고하지 않았다.
- 별도 검산 코드가 내부 정책 10,140건, nested 외부 선택 1,935건, 신규 티켓 적중 5,160건, 집계 지표 128행을 재계산해 모두 PASS했다. 동률과 regime fallback 합성 입력 검사도 PASS했다.
- 5개 목표 회차부터 이후의 실제 outcome을 모두 변조한 검사에서 해당 회차의 모델·설정 선택이 불변이었다. cutoff 위반 0건. 기존 추적 파일 352개 byte SHA 보존 PASS.
- 원자료와 기존 결과를 수정하지 않았다. 역사적 1245 outcome은 평가에 사용했으며 1245 결정은 1244까지만 사용했다. 1246 후보나 최종 구매번호는 생성하지 않았다.

## NEXT TEST

우선순위는 **ensemble de-correlation**과 **3+/4+ 목적의 별도 사전고정 비교**다. 기존 고정 모델 전체 성적의 사후 우승자를 새 모델로 취급하지 않는다. 같은 snapshot에서 오늘의 12개 정책을 다시 검색하거나 더 잘 맞는 임계값을 찾아 성과를 대체하지 않는다.

Prospective 평가를 시작한다면 이번 규칙을 새로운 미래 평가 protocol에 동결하고, 최초 미래 목표 1246부터 예측 artifact를 결과 발표 전에 봉인해야 한다. 오늘 보고서는 미래 예측 artifact를 만들지 않았으므로 현재 상태를 prospective 실행 완료로 표현하지 않는다.

이 배치는 새 연구 질문을 실제 시험하고 실패를 확인한 완료 연구다. 기존 A/C/contrarian 원본 부재와 전체 MASTER 항목은 별도의 미완료 상태로 유지한다. 기존 daily report의 반복 계산을 오늘 신규 성과로 승격하지 않는다.

## 재현 및 파일 안내

`run_study.py`는 pinned base checkout과 새 output 경로를 받아 사전 봉인, 신규 평가, 누수 검사, 결과를 기록한다. 기존 output을 덮어쓰지 않는다. `verify_study.py`는 저장된 CSV에서 별도 구현으로 선택과 적중을 검산한다. 새 재현 output에는 verifier를 복사한 뒤 실행한다.

```powershell
& 'C:\Users\user\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' .\run_study.py --repository '<857bea9 clean checkout>' --out '<new empty output directory>'
& 'C:\Users\user\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' .\verify_study.py --study '<new output directory>'
```

원천/설정/코드 SHA는 FROZEN_SPEC.json, 실행 결과는 RUN_METADATA.json과 VALIDATION_AUDIT.json, 독립 검산은 INDEPENDENT_VERIFICATION.json에 있다. 전체/최근/블록 지표는 model_metrics.csv, 모델 선택은 selection_trace.csv, 내부 성과는 inner_policy_walkforward.csv, 실패·보류 상태는 hypothesis_registry.csv 및 failure_registry.csv에 보존했다.
