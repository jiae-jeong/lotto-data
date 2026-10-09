# B 모델 재현성 및 오류 검증 — 2026-10-09 / v1

## 결론

**현재 B-v1 코드를 수정하지 않고 실제 실행했으며, CSV4개가 기존 복구 저장본과 바이트 단위로 재현되었습니다.** 실행은 이번 로그의 UTC 시각에 실제 수행했습니다. 이 사실은 실행 증거 없이 작성된 이전 “오늘 재실행” 주장을 소급해 확인해 주지 않습니다. 과거2026-10-06 실행 자체의 콘솔/환경/시각은 이번 재현으로 입증되지 않습니다.

예측 우위 또는 당첨확률 향상이 입증되었다는 판정은 하지 않습니다. 분류는 소스의 기술적 스크리닝 결과이며 통계적 검정이 아닙니다. V3는 `SEALED V3 GATE NOT PASSED`로 유지됩니다.

## 1. 항목별 상태

| 항목 | 상태 | 실제 확인 범위 |
|---|---|---|
| 기존 자료 보존 | VERIFIED | 기존 B 관련 68개 파일의 경로·수정시간·크기·SHA 기록 및 실행 후 일치. 원본 dirty Git 상태도 동일. |
| 입력 데이터 | VERIFIED | 정확히1~1244,1244행. 회차누락/중복/본번호·bonus 오류0. 실행 입력은 아래 isolated 경로. |
| 코드 버전 | VERIFIED | 현재 소스 수정0. source/data 해시는 OUTPUT_SHA256.csv 기준과 일치. 고정 상수는 아래에 기록. |
| 실제 B 재실행 | REPRODUCED | 2026-10-09T11:45:48.792859+00:00 ~ 2026-10-09T11:46:48.158901+00:00; 59.375s; exit0, stderr0bytes; 요청한5개 산출물 생성. |
| 누수 및 scoring | VERIFIED | 33408행 target=cutoff+1 및 적중/구조점수 재검산.17회차×8모델=136개 runtime prefix guard/미래행 변조 검사 PASS. |
| 이론 기준선 | VERIFIED | Hypergeometric PMF/평균/분산/2+..6+ 독립 유리수 계산과 source baseline()/전체256 metric 행 일치. |
| MASTER 실제 랜덤 생성 | NOT EXECUTED | B-v1은 실제 random comparator를 생성하지 않음. MC3줄 별도 검증은 제안만 기록; 아직 실행하지 않음. |
| 기존 CSV 비교 | REPRODUCED | CSV4개 전체 bytes/SHA/rows 모두 기존 저장본 및 historical manifest 일치. 모델 분류·50회 블록·0..6·2+..5+ 모두 재현. |
| 과거 전체 보고서 파일 | MISMATCH | 새 report와 패키지 regenerated report는 경로/개행을 정규화하면 동일하지만 파일 SHA는 다름. 숫자 불일치 아님. |
| 정확한 과거 report 원본 | NOT FOUND | pinned historical report hash를 가진 원본 미확보; 동일 원본 보고서를 복원했다고 말할 수 없음. |
| 33408 구조 | REPRODUCED | 8모델×4176중첩 records/model=33408.8352고유 target/model;1044회차. 분류350회차/model. |
| 상이한B0.7743/0.7571/random0.8065 | NOT FOUND | 현재 로컬·패키지·reachable Git refs에서 해당 세 값의 원본 코드/실행 산출물·분모·seed 근거 미확보. 원인 미확인. |
| rolling300 B 실행 | NOT EXECUTED | 현재 B-v1 소스에는 fixed rolling300 훈련 모드 없음. rolling-origin expanding만 실제 실행. |
| 과거 원자료 전체 통계 연구 | NOT EXECUTED | 번호별 누적/최근10·30·50·100/pair·triple 일반 연구표를 이 코드가 재생성하지 않음. 내부 B feature와 별도 B-score slice 검산 범위만 완료. |
| 추천번호/1245 결과 | NOT EXECUTED | 1245 실제 결과 조회/사용0, 새1245 추천·조합 생성0. 과거201~1244 backtest tickets만 생성. |
| Git commit/push | NOT EXECUTED | 이번 요청의 재현 검증 산출물은 새 outputs 버전 디렉터리에 저장; 기존 repository와 automation 변경0. |

## 2. 실제 입력 및 코드 고정

- 읽은 저장본: `C:\Users\admin\Documents\Codex\2026-10-09\6-45-jiae-jeong-lotto-data\work\primary_mode_1245_v4_clean_20261009\lotto_data.csv`
- 실제 실행 입력: `C:\Users\admin\Documents\Codex\2026-10-09\6-45-jiae-jeong-lotto-data\work\b_model_reproduction_20261009_v1\sandbox\work\lotto-data\lotto_data.csv`
- 입력 SHA-256: `243cd17e6b97a2d96709ddfc689a068038669341a52dcc0743c141d309e43b9f`
- 실행 소스 저장본: `C:\Users\admin\Documents\Codex\2026-10-09\6-45-jiae-jeong-lotto-data\work\primary_mode_1245_v4_clean_20261009\research\1245_final_pipeline_v3\recovered_original_assets\b_model_backtest.py`
- 실제 실행 소스: `C:\Users\admin\Documents\Codex\2026-10-09\6-45-jiae-jeong-lotto-data\work\b_model_reproduction_20261009_v1\sandbox\scripts\b_model_backtest.py`
- 소스 SHA-256: `3ecf4fb805c2448e49c39e01174b3a112d4865c7ff1a31157437515b78be47cb`
- Python: `3.12.14 (main, Aug 25 2026, 14:01:42) [MSC v.1944 64 bit (AMD64)]`
- 입력1244행, min1/max1244, 누락0/중복0/추가회차0; 각행6개 서로 다른 본번호1..45; bonus1..45 및 본번호 중복0.
- 원본 dirty repo의 CRLF CSV와 LF 입력은 parsing 후 모든 행/필드가 동일. 파일 해시가 다른 이유는 실제 개행 차이이며, 원본을 변환하지 않았습니다.
- 기존 파일 수정시간은 `EXISTING_ASSET_METADATA.csv`에 UTC/ns로 보존했습니다. checkout/download 수정시간을 과거 연구 실행시간으로 해석하지 않습니다.

### 고정 상수

```json
{
  "ANCHORS": [
    200,
    400,
    600,
    800,
    1000,
    1100,
    1150,
    1200
  ],
  "HORIZONS": [
    10,
    25,
    50,
    "to_end"
  ],
  "RECENT_WINDOW": 50,
  "STRUCTURE_BANK_SEED": 20261006,
  "STRUCTURE_BANK_SIZE": 10000,
  "MODEL_NAMES": [
    "long_frequency",
    "current_gap",
    "frequency_plus_gap",
    "recent_momentum",
    "structure_profile",
    "pair_association",
    "triple_association",
    "combined_equal_rank"
  ]
}
```

## 3. 실제 실행 명령과 로그

```powershell
& "C:\Users\admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" "C:\Users\admin\Documents\Codex\2026-10-09\6-45-jiae-jeong-lotto-data\work\b_model_reproduction_20261009_v1\sandbox\scripts\b_model_backtest.py"
```

- 시작UTC: `2026-10-09T11:45:48.792859+00:00` / 종료UTC: `2026-10-09T11:46:48.158901+00:00`
- 소요시간: 59.375초 / 종료코드:0 / stderr:0bytes.
- 변경 없는 소스의 hardcoded 입력 경로에 맞춘 새 sandbox를 구성하고 outputs 디렉터리를 미리 생성했습니다. 소스의 ROOT/INPUT/OUT 변수를 수정하거나 기존 연구 폴더에서 출력을 생성하지 않았습니다.
- 실제 stdout: `EXECUTION_STDOUT.log`; 실제 stderr: `EXECUTION_STDERR.log`; command/UTC/exit: `EXECUTION_RESULT.json`.
- 별도 diagnostic은 복구 위치에서 실행시 input FileNotFoundError(exit1)를 실제 확인했습니다. 이는 성공한 sandbox 백테스트와 구분된 실패 경로 진단이며 추가 성능 실행이 아닙니다.

```text
Rows=1244; prediction_records=33408; anchors=[200, 400, 600, 800, 1000, 1100, 1150, 1200]
Random baseline mean=0.800000; variance=0.614545; p_ge2=0.175308
long_frequency: ADDITIONAL VALIDATION; blocks+=2/7; delta_mean=-0.063; delta_ge2_pp=-2.67
current_gap: ADDITIONAL VALIDATION; blocks+=4/7; delta_mean=-0.026; delta_ge2_pp=-1.82
frequency_plus_gap: ADDITIONAL VALIDATION; blocks+=5/7; delta_mean=+0.029; delta_ge2_pp=+3.04
recent_momentum: ADDITIONAL VALIDATION; blocks+=3/7; delta_mean=-0.054; delta_ge2_pp=-2.96
structure_profile: ADDITIONAL VALIDATION; blocks+=4/7; delta_mean=+0.051; delta_ge2_pp=+1.61
pair_association: ADDITIONAL VALIDATION; blocks+=4/7; delta_mean=+0.034; delta_ge2_pp=+0.47
triple_association: ADDITIONAL VALIDATION; blocks+=5/7; delta_mean=+0.026; delta_ge2_pp=+1.04
combined_equal_rank: HOLD; blocks+=3/7; delta_mean=+0.003; delta_ge2_pp=+1.04
Outputs: C:\Users\admin\Documents\Codex\2026-10-09\6-45-jiae-jeong-lotto-data\work\b_model_reproduction_20261009_v1\sandbox\outputs
```

## 4. 재현된 모델별 성적 — 비중첩7블록×50=350회차/model

| 모델 | 평균 | 분산 | 2+ | 3+ | 4+ | 5+ | 0/1/2/3/4/5/6 적중수 | 우세블록 | 분류 |
|---|---:|---:|---:|---:|---:|---:|---|---:|---|
| long_frequency | 0.737142857 | 0.633763265 | 14.8571% | 3.1429% | 0.2857% | 0.0000% | 156/142/41/10/1/0/0 | 2/7 | ADDITIONAL VALIDATION |
| current_gap | 0.774285714 | 0.523338776 | 15.7143% | 0.8571% | 0.0000% | 0.0000% | 137/158/52/3/0/0/0 | 4/7 | ADDITIONAL VALIDATION |
| frequency_plus_gap | 0.828571429 | 0.639183673 | 20.5714% | 1.7143% | 0.2857% | 0.0000% | 139/139/66/5/1/0/0 | 5/7 | ADDITIONAL VALIDATION |
| recent_momentum | 0.745714286 | 0.526767347 | 14.5714% | 1.1429% | 0.0000% | 0.0000% | 144/155/47/4/0/0/0 | 3/7 | ADDITIONAL VALIDATION |
| structure_profile | 0.851428571 | 0.640783673 | 19.1429% | 2.8571% | 0.2857% | 0.0000% | 130/153/57/9/1/0/0 | 4/7 | ADDITIONAL VALIDATION |
| pair_association | 0.834285714 | 0.543967347 | 18.0000% | 1.1429% | 0.0000% | 0.0000% | 125/162/59/4/0/0/0 | 4/7 | ADDITIONAL VALIDATION |
| triple_association | 0.825714286 | 0.595338776 | 18.5714% | 2.0000% | 0.0000% | 0.0000% | 133/152/58/7/0/0/0 | 5/7 | ADDITIONAL VALIDATION |
| combined_equal_rank | 0.802857143 | 0.592563265 | 18.5714% | 1.1429% | 0.2857% | 0.0000% | 139/146/61/3/1/0/0 | 3/7 | HOLD |

- 이 .828571/.851429 값은 전체1044 targets나 중첩4176 records/model의 평균이 아닌 **선택된 비중첩350 targets/model**의 pooled 평균입니다.
- 기존 `B_MODEL_RESULTS.md`의8모델 표도 표기 정밀도에서 일치합니다. 네CSV 전체행 비교와 별도 집계 재검산을 완료했으므로 단지 위 평균만 맞춘 것이 아닙니다.
- 평균/분산·0..6분포·2+/3+/4+/5+는 holdout metrics의256개 anchor×horizon×model group마다 재검산했습니다.
- 50회 블록 실제 구간:201~250,401~450,601~650,801~850,1001~1050,1101~1150,1151~1200.56개 block×model 결과가 기존과 일치합니다.

### 전체50회 블록 평균 적중

| 모델 | 201–250 | 401–450 | 601–650 | 801–850 | 1001–1050 | 1101–1150 | 1151–1200 |
|---|---:|---:|---:|---:|---:|---:|---:|
| long_frequency | 0.800 | 0.840 | 0.680 | 0.520 | 0.840 | 0.780 | 0.700 |
| current_gap | 0.840 | 0.960 | 0.980 | 0.680 | 0.720 | 0.420 | 0.820 |
| frequency_plus_gap | 0.820 | 0.860 | 0.820 | 0.800 | 0.940 | 0.680 | 0.880 |
| recent_momentum | 0.840 | 1.020 | 0.660 | 0.920 | 0.580 | 0.660 | 0.540 |
| structure_profile | 0.980 | 1.120 | 0.680 | 0.680 | 0.800 | 0.880 | 0.820 |
| pair_association | 0.740 | 0.840 | 0.780 | 0.900 | 0.960 | 0.880 | 0.740 |
| triple_association | 0.740 | 0.920 | 0.820 | 0.880 | 0.840 | 0.700 | 0.880 |
| combined_equal_rank | 0.700 | 0.940 | 0.760 | 0.840 | 0.980 | 0.660 | 0.740 |

- 최근10/30/50/100/200 및 고유201~1244 성적은 오늘 생성된 CSV를 중복 제거하여 **별도 audit 계산**한 `AUDIT_UNIQUE_AND_RECENT_B_SCORES.csv`에 보존했습니다. 원래 B-v1 출력/분류와 provenance를 구분합니다. 이 결과를 과거 임시 분석의 재현으로 간주하지 않습니다.

## 5. 33,408 레코드 계산 근거

| anchor | 10 | 25 | 50(cap) | to_end | 모델당 | 8모델 전체 |
|---:|---:|---:|---:|---:|---:|---:|
| 200 | 10 | 25 | 50 | 1044 | 1129 | 9032 |
| 400 | 10 | 25 | 50 | 844 | 929 | 7432 |
| 600 | 10 | 25 | 50 | 644 | 729 | 5832 |
| 800 | 10 | 25 | 50 | 444 | 529 | 4232 |
| 1000 | 10 | 25 | 50 | 244 | 329 | 2632 |
| 1100 | 10 | 25 | 50 | 144 | 229 | 1832 |
| 1150 | 10 | 25 | 50 | 94 | 179 | 1432 |
| 1200 | 10 | 25 | 44 | 44 | 123 | 984 |

`(1129+929+729+529+329+229+179+123)×8 = 4176×8 = 33408`

- horizon50 atanchor1200 iscap44. to_end at1200 also44, so those target/model rows duplicate each other.
- 고유 target/model 레코드8352=(1244−200)×8. 고유 평가 회차1044. 중첩 holdout33408행을 독립 표본으로 간주하면 안 됩니다.

## 6. 누수·평가 검산

- 전체33408행 모두 `target_round=training_through_round+1`, target201..1244. 최대 training round1243.
- 입력의 실제 과거 번호를 통해 모든 실제 적중수와6개 구조조건 점수를 다시 계산했습니다. 여러 anchor/horizon에서 반복되는 동일 target/model의 예측도 동일합니다.
- main()은1..200에서 feature를 초기화하고 target t의 예측을 계산한 뒤 t회 관측치로 counters를 갱신합니다. horizon내 이전 target 결과를 이후 target에 사용하는 expanding walk-forward이며, 전체 horizon의 미래 관측을 미리 넣지 않습니다.
- recent/earlier slices는 모두 train_n 미만 인덱스에서 끝납니다. frequency/last_seen/pair/triple/profile counters를 각 표본의1..t−1에서 독립 재구축했습니다. structure 후보 bank는 고정 seed로 생성되어 관측 결과를 입력으로 사용하지 않습니다.
- runtime sample targets: `[201, 372, 395, 401, 485, 595, 601, 610, 674, 801, 885, 1001, 1101, 1145, 1151, 1201, 1244]`
- 17회차×8모델=136개 예측에서 미래 인덱스 접근을 즉시 실패시키는 guard를 통과하고, t..1244행을 sentinel로 교체해도 같은 예측이 나왔습니다. 원래 실행 CSV와도 전부 일치했습니다.
- 샘플마다 frequency 총수6n, pair 총수15n, triple 총수20n, 고정 구조 profile n개, 이전회차 overlap profile n−1개를 확인했습니다.
- 전체 record 검사 및 표본 동적 검사가 모두 PASS지만, 이를 모든 잠재적 연구 편향이나 prospective 우위의 증명으로 확대하지 않습니다.

## 7. 랜덤 기준 — 정확한 hypergeometric

`P(K=k)=C(6,k)C(39,6−k)/C(45,6)`, `C(45,6)=8,145,060`

| 적중k | 확률 | 백분율 |
|---:|---:|---:|
| 0 | 0.400564636724591 | 40.0564636725% |
| 1 | 0.424127262414273 | 42.4127262414% |
| 2 | 0.151474022290812 | 15.1474022291% |
| 3 | 0.0224405958949351 | 2.2440595895% |
| 4 | 0.00136463083144876 | 0.1364630831% |
| 5 | 2.87290701357633e-05 | 0.0028729070% |
| 6 | 1.22773803998988e-07 | 0.0000122774% |

- 평균: 0.800000000000 (`4/5`); 분산:0.614545454545 (`169/275`).

| 누적적중 | 정확확률 | 백분율 |
|---|---:|---:|
| 2+ | 0.175308100861135 | 17.5308100861% |
| 3+ | 0.0238340785703236 | 2.3834078570% |
| 4+ | 0.00139348267538852 | 0.1393482675% |
| 5+ | 2.88518439397623e-05 | 0.0028851844% |
| 6+ | 1.22773803998988e-07 | 0.0000122774% |

- source baseline() 및256개 metric행의 모든 기준값과 일치합니다. 이 기준은 **Monte Carlo 실행값이 아닙니다**.
- MASTER `LOTTO_PROJECT_PROTOCOL.md:109`의 “동일 조건의 균등 무작위 기준선을 실제 생성·계산한다” 요구를 현재 B 소스만으로 완전히 충족했다고 표시할 수 없습니다.
- 구조 모델의 random bank10000개는 점수 최대 후보를 고르는 검색 풀입니다. 그대로 uniform random baseline으로 취급하지 않습니다.
- **제안만 기록 / NOT EXECUTED:** seed20261009로201..1244 historical target마다 실제 uniform 랜덤 티켓을 생성한 별도 검증. B-v1과 같은 조건은1모델1티켓이므로 우선1티켓 비교가 맞습니다. 3줄 포트폴리오는 B의3줄 선정규칙을 먼저 지정한 경우에만 비교 가능합니다. Monte Carlo3줄10,000반복/target 계획은 기존 결과를 변경하지 않는 새 디렉터리에서 실행해야 합니다.

## 8. 과거 보고서 및 상이한 수치 조사

- 새 report SHA:b9e3804e02f2c4fed548222b77cf90ff58083d54f184cb4bbee0c5b20489994a
- 패키지 regenerated report SHA:4f3a02ba45ba7fb94498a7e23bb5307beff533ae322b6b47f303cce9465cd1b8
- 역사적 report 기대SHA:2d9314c793c6508f2d6d5aab983c74b271c5b0f6c042997cfff1079742cf0512
- 앞의 두 report는 입력 절대경로와 개행만 정규화하면 모든 본문이 일치합니다. 기대 역사적SHA 파일 자체는 찾지 못했습니다. 따라서 원본 보고서 동일성은 NOT FOUND / 신규 report whole-file hash는 MISMATCH이고, 수치 재현은 REPRODUCED입니다.
- 0.7743/0.7571/0.8065 분석의 원본·실행 로그·분모·seed 근거는 조사 범위에서 NOT FOUND. 원인은 **미확인**입니다.
- 조사한 현재 available research/analysis/work/outputs의 B 소스/보고서/scorecard, 다운로드한 recovery ZIP, Git `--all` reachable refs와 관련 이력을 `DIVERGENT_RESULT_INVESTIGATION.json`에 기록했습니다. 다른사용자 옛cloud-x20/B-model경로는 현재 PC에 존재하지 않습니다.
- 위치가 다른 B source는 CRLF 파일1개를 포함하지만, CRLF→LF만 정규화하면 모두 실행소스와 동일합니다. 서로 다른 모델 공식 버전을 발견했다고 말할 수 없습니다.
- 현재 pooled `current_gap`은0.774285714입니다. 이것이 과거 “frequency_plus_gap0.7743” 주장과 숫자가 유사하다는 이유로 잘못 표기된 원인이라고 확정하지 않습니다.
- 이론 random 평균은0.8이며0.8065가 아닙니다. 0.8065의 실험 분모·seed를 찾지 못했으므로 Monte Carlo 실현값으로 확정하지 않습니다.
- 350 비중첩평가 /1044고유평가 /4176중첩 rows/model은 실제로 서로 다른 집계입니다. 다만 이 차이가 미확보 임시 분석을 설명한다고 확정하지 않습니다.

## 9. 발견한 실행·모델·문서 제한

- **PATH001 / VERIFIED**: Hardcoded script-parent ROOT expects ROOT/work/lotto-data/lotto_data.csv. Recovered source is stored elsewhere, so direct execution there would look under recovered assets parent rather than repository root. Provided exact expected tree in a new isolated sandbox, no source edits. 영향: Portability/preflight limitation, not a numerical mismatch.
- **PATH002 / VERIFIED**: Writes b_model_50_round_trends.csv before OUT.mkdir(). A clean missing outputs directory would cause FileNotFoundError. Created sandbox outputs directory before unmodified execution. 영향: Setup dependency. Verified via static order and separate isolated negative-path run; see ENVIRONMENT_FAILURE_CHECKS.json.
- **DATA001 / VERIFIED**: main() checks row count/round continuity only, not number ranges, unique six numbers or bonus. External INPUT_VALIDATION.json checked all input rows, with zero violations. 영향: Input validator incompleteness preserved in original source.
- **MODE001 / VERIFIED**: This source uses expanding training; rolling-origin target advancement is not a separate rolling300/rolling-window mode. Use exact mode terminology in this report. 영향: No fixed-window training backtest executed by B-v1.
- **STRUCT001 / VERIFIED**: Consecutive-draw overlap profile has n-1 observed transitions but uses denominator n+7; its category probabilities sum to (n+6)/(n+7), below1. No source/model changes; record as inherited specification issue. 영향: For a given cutoff this denominator contributes the same additive log constant to every bank ticket, so changing just denominator would not change ticket ranking. No changed-model performance run performed.
- **STRUCT002 / VERIFIED**: Band-vector smoothing uses210 weak compositions; 0-0-0-0-6 is impossible because band41..45 contains5 distinct numbers. Feasible category count is209. No source/model changes; record as inherited specification issue. 영향: Denominator factor is constant across tickets at a cutoff; no ranking impact from changing denominator alone.
- **DOC001 / VERIFIED**: One source report paragraph/comment says anchors200..1100 yet there are7 complete blocks and anchor1150 is included. Actual tested blocks recorded as201..250,401..450,601..650,801..850,1001..1050,1101..1150,1151..1200. 영향: Documentation typo; computational blocks match stored CSV.
- **STAT001 / VERIFIED**: 33408 output records repeat the same target/model prediction across overlapping horizons. Not33408 independent trials. 8352 unique target/model pairs;1044 unique historical targets; classification uses350 disjoint targets/model. 영향: Do not treat overlapping rows as independent evidence.
- **BASE001 / NOT EXECUTED**: No matched actual Monte Carlo random comparator in B-v1; random structure bank is optimized model search. Theoretical exact baseline independently verified; separate simulation proposed, not reported executed. 영향: MASTER actual-random-generation requirement not fully fulfilled by this source.
- **REPORT001 / NOT FOUND**: Exact historical b_model_backtest_report.md with pinned historical hash unavailable; package report is explicitly regenerated. Compare normalized regenerated report and stored short summary; preserve mismatch as such. 영향: CSV byte-for-byte reproduction does not prove historical report byte restoration.
- **OTHER001 / NOT FOUND**: Original evidence for B0.7743/B0.7571/random0.8065 trio not located. Leave cause unknown. Do not infer a proven code/data/interval change. 영향: Earlier conflicting result remains unaudited.
- **SCOPE001 / NOT EXECUTED**: Standalone descriptive raw-data cumulative/recent10/30/50/100 number frequencies and pair/triple research tables were not regenerated by this B-source command. Only B internal historical features and independent B-score audit slices were checked. 영향: Do not claim all prior raw research statistics were rerun today.

## 10. 파일 보존 및 Git 상태

- 실행 전후 B 관련68개 기존 파일의 size/mtime/SHA 일치. 그중 exact-source/CSV/old-report가 있는 경로를 모두 목록화했습니다.
- original repo HEAD:`6ee07c2a5bca8f7d5e714a6d48bc5a8b7fd9cf5d`; 새 main clean worktree HEAD:`f777d7888bce208fa7b196689278f41fec387caf`. 이번 작업에서 commit/push를 수행하지 않았습니다.
- 기존 원본 dirty 변경·미추적파일 보존. 최신 main worktree clean. 기존 V3/V4 freeze/prediction/decision/raw/automation 변경0.

```text
## main...origin/main [ahead 1, behind 16]
 M research/1245_final_pipeline_v3/recover_and_run_20261009.py
 M research/1245_final_pipeline_v3/recovery_run_20261009/EXECUTION_REPORT.md
?? research/1245_final_pipeline_v3/SOURCE_ASSET_SEARCH_v2.md
?? research/1245_final_pipeline_v3/__pycache__/
?? research/1245_final_pipeline_v3/independent_validation_20261009.py
?? research/1245_final_pipeline_v3/independent_validation_20261009_independent/
?? research/1245_final_pipeline_v3/recovered_original_assets/
?? research/1245_final_pipeline_v3/source_asset_search_v2.log
?? research/expansion_framework_v1/__pycache__/
?? research/expansion_framework_v1/studies/study_batch_001/__pycache__/
```

```text
## seal-v4-primary-mode-1245-20261009
```

## 11. 산출물 해시와 재실행 안내

아래5개는 **오늘 실제 unmodified B-source 실행**에서 나온 출력입니다.

| 파일 | 크기bytes | SHA-256 |
|---|---:|---|
| b_model_predictions.csv | 3236859 | `088685b5c30275c2640dfda2001beb99cebf5855156ae54ad5e0f6f170cf39be` |
| b_model_holdout_metrics.csv | 113856 | `147765c9f3353deac5cc5c91e37ce0f80a7e4608c9e29738d4724130df5bc2a4` |
| b_model_classification.csv | 3509 | `2c7a8030b0129eef55137852a8e5e297d916239c46a8fc9bbe0e0c467ecf9ff2` |
| b_model_50_round_trends.csv | 6264 | `199bd09e71f9f7171b2c26ee68a7eb8afd40edcd17a1f8907dd09c2a4e7f57df` |
| b_model_backtest_report.md | 10972 | `b9e3804e02f2c4fed548222b77cf90ff58083d54f184cb4bbee0c5b20489994a` |

- 전체 신규 파일의SHA는 `AUDIT_SHA256.csv`에 기록합니다. manifest는 자기 자신을 제외합니다.
- `EXECUTED_b_model_backtest.py`와 `EXECUTED_INPUT_lotto_data.csv`는 실행 소스/입력의 byte-identical 보존 사본입니다. 기존 파일을 변환한 것이 아닙니다.
- 안전한 새버전 재실행: `RERUN_B_MODEL.ps1 -PythonExe <python 경로> -NewRoot <존재하지 않는 새폴더>`; 이미 존재하는 NewRoot이면 중단합니다. 실행 당시 소스/입력 해시와 같은 사본을 사용하며 hardcoded 경로를 새 sandbox에 제공합니다.
- 모델/데이터 수정이나 원본 코드 수정은 이번 작업에서 적용하지 않았습니다. 향후 문제를 고치면 별도 새 소스/결과 버전으로 관리해야 합니다.

## 12. 남은 최소 작업

1. 0.7743/0.7571/random0.8065를 산출한 원본 코드/CSV/실행로그 중 하나와 데이터SHA·구간·seed를 확보해야 원인 비교가 가능합니다.
2. exact historical report 원본 hash를 갖는 파일이 확보되면 새 사본과 whole-file 비교를 추가합니다.
3. MASTER 실제 랜덤 기준 검증은 동일1티켓 조건에서 seed/반복수/대상구간을 먼저 고정한 별도 MC 실행이 필요합니다. 3줄 비교를 원하면 B3줄 portfolio 규칙도 먼저 정의해야 합니다.
4. 경로/출력디렉터리 생성 순서/입력검사/구조정규화/문서 anchor오기는 보존된 B-v1과 분리한 새버전에서 고칠 수 있습니다. 이번 재현 결과에는 변경을 적용하지 않았습니다.

**1245 실제 결과는 읽거나 사용하지 않았습니다. 신규 추천번호나1245 최종조합도 생성하지 않았습니다.**

추가 실행 구분: RERUN_B_MODEL.ps1은 PowerShell parser 오류0만 확인했고, 이 도움스크립트를 통한 두 번째 전체 백테스트는 NOT EXECUTED입니다. 실제 전체 백테스트는 앞서 로그에 기록한 원본 Python 직접 명령1회이며, 이후 prefix 재계산은 누수 검증용 역사적 표본 replay입니다.
