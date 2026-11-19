# Research Expansion Framework v1

이 폴더는 기존 B-model v1 결과와 1245 파이프라인을 보존하면서 새 가설을 누적 연구하기 위한 별도 도구 모음입니다. 기존 결과는 읽기 전용 기준 자료이며, 신규 연구 산출물은 연구 ID가 포함된 새 경로로 저장합니다.

## 현재 프로젝트 점검

`project_audit.md`는 기준일의 읽기 전용 감사를 기록합니다. 기존 핵심 자산 24개의 파일 크기와 SHA-256을 `project_baseline_manifest.csv`에 고정했습니다. `audit_project.py`는 이후 이 자산들이 바뀌었는지, 원자료와 예측 산출물의 실제 회차가 맞는지, cutoff가 목표회차 직전인지 확인합니다.

현재 상태를 다시 점검하려면 프로젝트 루트에서 `python outputs/research_expansion_framework_v1/audit_project.py`를 실행합니다. 새 점검 보고서를 저장할 경우 기존 보고서를 덮어쓰지 않도록 새 경로를 지정합니다. 예: `--write-report outputs/research_expansion_framework_v1/project_audit_2026-10-09.md`.

현재 원자료는 회차 1~1244 연속, 번호 범위·날짜·보너스 검사를 통과했습니다. 전체 walk-forward 33,408행은 중첩 holdout 중복을 제거하면 8,352개의 회차×모델 예측이며, 최근 검증과 후보군 상세도 원자료 당첨번호와 일치했습니다. 1245 실제 결과는 존재하거나 사용된 것으로 취급하지 않습니다.

## 구성

- `walkforward_core.py`: 원자료 제한 읽기, expanding/rolling 평가, 조합 검증, 정확 무작위 기준선, 공통 지표.
- `data_quality.py`: 지정된 cutoff까지만 읽는 원자료 연속성·날짜·번호·보너스 검사.
- `run_study.py`: 연구 모듈의 `predict(train_draws)`를 walk-forward 평가하고 새 CSV를 생성.
- `hypothesis_template.py`: 가설 모듈 시작 서식.
- `study_template.md`: 사전 등록 및 결과 해석 서식.
- `research_registry.csv`: 장기 누적 가설 목록 템플릿.
- `model_family_catalog.csv`: 현재 B-model의 상관·정보 공유 계열 메모.
- `project_baseline_manifest.csv`: 기존 기준 자산 24개의 경로·크기·SHA-256.
- `audit_project.py`, `project_audit.md`: 읽기 전용 자산/데이터 감사.

## 새 연구 절차

1. 새 `research_id`를 만들고 `research_registry.csv` 또는 `study_template.md`에 가설, 변수, 계산법, cutoff, 검증기간, baseline, 과적합 위험을 사전 기록합니다.
2. `studies/<research_id>.py`에 `predict(train_draws)`를 구현합니다. predictor는 목표회차 이전 데이터만 받습니다. 기존 B-model 소스는 수정하지 않습니다.
3. 연구 시작 전 데이터 cutoff를 지정하고 검사합니다. 현재 기준 자료는 `C:\Users\user\Documents\Codex\2026-10-06\cloud-x20\work\lotto-data\lotto_data.csv`의 1~1244회입니다.
4. walk-forward 평가의 target 범위와 최소 학습 길이를 고정합니다. `run_study.py`는 목표 t의 예측 함수에 최대 t-1회차까지만 전달합니다.
5. CSV 결과를 연구 ID가 포함된 새 파일명으로 저장합니다. runner는 파일이 이미 있으면 덮어쓰지 않고 중단합니다.
6. 결과를 등록하고 FAILED/WEAK/HOLD/PROMISING/VALIDATION_REQUIRED 등으로 분류합니다. 성과가 낮은 결과도 유지합니다.

예시:

```powershell
python outputs/research_expansion_framework_v1/data_quality.py --data 'C:\Users\user\Documents\Codex\2026-10-06\cloud-x20\work\lotto-data\lotto_data.csv' --through-round 1244
python outputs/research_expansion_framework_v1/run_study.py --data 'C:\Users\user\Documents\Codex\2026-10-06\cloud-x20\work\lotto-data\lotto_data.csv' --through-round 1244 --model outputs/research_expansion_framework_v1/studies/EXP-0001.py --first-target 201 --last-target 1244 --min-training-rounds 200 --output-csv outputs/research_expansion_framework_v1/studies/EXP-0001_walkforward.csv
```

사용할 Python 실행 경로가 `python` 명령과 다르면 연결된 Python 3 실행 파일의 절대 경로를 사용합니다.

## 검증/독립성 원칙

- 무작위 기준선은 `C(45,6)` 균등조합의 정확한 초등하이퍼기하분포입니다.
- 기본 보고 지표는 n, 0~6 적중 분포, 평균·분산, 2+/3+/4+/5+/6 적중률입니다.
- recent holdout, untouched holdout, 실패 구간을 별도 구간으로 기록합니다. 여러 창을 본 뒤 유리한 창만 고르는 것은 post-hoc으로 표시합니다.
- 같은 빈도·gap·momentum 신호나 동일 회차의 hit 결과를 독립 표로 반복 가산하지 않습니다. 모델군 상관관계를 catalog에 표시하고, 후보번호 성과처럼 같은 outcome을 재사용하는 보조 통계는 별도 진단으로 분리합니다.
- 모델 티켓 성과와 조합 구성 성과를 분리합니다. 6개 조합은 predictor 내부에서 명시된 규칙으로 생성하며, 임의 후보 조합을 대량 탐색해 최댓값만 보고하지 않습니다.
- 어떤 결과도 당첨 보장이 아닙니다. 기술적 기준선 초과는 곧바로 검증된 예측력을 뜻하지 않습니다.

## 기존 자산 보호

- v1 결과물은 `project_baseline_manifest.csv`의 체크섬과 대조합니다. 수정이 필요하면 이 폴더의 기존 파일을 고치지 말고 새 버전 경로를 만듭니다.
- `audit_project.py`는 읽기 전용입니다. 보고서 기록은 `--write-report`와 새 경로를 지정해야 하며 이미 있는 파일은 덮어쓰지 않습니다.
- 장기 데이터가 늘면 과거 manifest를 갱신하지 말고 새 날짜/버전의 manifest를 생성해 변경 이력을 보존합니다.
