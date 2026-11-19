# B 모델 실제 균등 무작위 기준선 검증 — 2026-10-09 / v1

## 결론

**실제 균등 6/45 티켓3,500,000개를 생성하여, B와 동일한350개 과거 회차에서 비교했습니다.** 기존 B 코드·CSV·보고서·분류를 변경하지 않았습니다. 번호추천 결과를 생성하지 않았습니다.

- B 감사 보존 commit: `2892b0d4424c72554612d464b7a7093f814e3fc3`. 당시 remote main과 일치,43개 원격 파일SHA 재검증PASS.
- Random 실행:exit0,stderr0bytes,3.047초. UTC `2026-10-09T12:19:28.964844+00:00` ~ `2026-10-09T12:19:31.996585+00:00`.
- Random pooled mean: **0.800745714286**, variance:**0.614839443910**.
- Random mean95%MC CI: **[0.799924238192, 0.801567190380]**. 이론 mean0.8을 포함합니다.
- 판정:실행·집계는 `MONTE_CARLO_VERIFIED`;B의 검증된 예측우위는 `INSUFFICIENT EVIDENCE`. 기존 `combined_equal_rank=HOLD`,나머지7모델 `ADDITIONAL VALIDATION` 유지.

## 1. 상태 구분

| 항목 | 상태 | 근거 |
|---|---|---|
| B reproducibility preservation | REPRODUCED | 33408records,byte-identical4CSV and original screening classes are frozen in separate reference JSON. |
| GitHub B audit storage | VERIFIED | 43files,commit=remote main;all43downloaded raw Git blobs hash verified. |
| Actual uniform ticket baseline | MONTE_CARLO_VERIFIED | Seed20261009,350targets x10000tickets=3500000actual comparisons,exit0,stderr0bytes. |
| Matched350-target comparison | VERIFIED | Exactlyseven specified non-overlapping50round blocks and8Bmodels,all aggregates checked. |
| Original historical full report bytes | NOT FOUND | Inherited issue;regenerated report path/EOL hashes differ(MISMATCH) but reproduced CSV evidence remains unchanged. |
| Historical0.7743/0.7571/0.8065 trio | NOT FOUND | UNRESOLVED_HISTORICAL_RESULT;causeunknown,excluded,noaveraging. |
| B predictive superiority | INSUFFICIENT EVIDENCE | Observedpositive/negative differences and varyingblocks;primary mean/rate2CIcontain theoreticalbaseline;Holm16all1.0;posthoclimitations. |
| Precise6-hit rate empirical estimation | INSUFFICIENT EVIDENCE | 3.5million yields expected0.43six-hit events;observed1six-hit;precision remains limited. |
| 1245actual/newpurchase tickets | NOT EXECUTED | No1245actualread/use,newrecommendationorfinalthree-linegeneration. |
| Prior report file hash | MISMATCH | Historical full report original hashunavailable;thisnewreportdoesnotalterBcsvreproduction. |

## 2. 비교 설계 및 실제 실행

- 고정 random seed:`20261009`;bootstrap seed:`20261010`;PCG64+SeedSequence([seed,target]).
- 대상:201~250,401~450,601~650,801~850,1001~1050,1101~1150,1151~1200. 회차당10,000개,블록당500,000개,총3,500,000개. 제외회차 없음.
- 실제 난수6개를1..45에서 뽑고,중복번호가 있으면 그 sextuple을 폐기하여 다시 뽑았습니다. 정렬된6개 subset마다6!개의 동일확률 원상이 있으므로 균등한 비복원6/45티켓입니다. 모든 accepted row의 범위/중복 검사 수행.
- 실제 티켓과 해당 과거 회차 본번호의 교집합으로 적중을 셌습니다. hypergeometric 적중수를 직접 난수추출하여 실행한 척하지 않았습니다.
- 입력은 재현 감사의 `EXECUTED_INPUT_lotto_data.csv`,SHA `243cd17e6b97a2d96709ddfc689a068038669341a52dcc0743c141d309e43b9f`,최대1244. 평가 target최대1200.1245실제 결과 사용0.
- B는 재현 CSV에서horizon50과 지정7anchors만 읽은2,800개 모델×회차 레코드(8×350)를 사용했습니다. 예측을 다시 조정하거나Bcode를 import/실행하지 않았습니다.
- 이론기준mean0.8/variance0.614545454545 및 정확PMF는 분석 참조값이며,Monte Carlo 실행 데이터와 별도입니다.
- 표본수 근거:meanMC SE약0.000419,95%반폭약0.000821. rare6hits의기대횟수약0.43이므로6+의정밀한경험확률 추정에는 충분하지 않습니다.
- 공식MC 비교수3,500,000은 고정seed로 한 번의 실행에서 생성했습니다.7개 표본target의stream을 재생성하는 검증은determinism verification이며,공식 표본수에 더하거나 seed를 바꿔 유리한 결과를 고르지 않았습니다.
- raw ticket numbers는 구매·후보 산출물로 저장하지 않았습니다. per-target 집계와sorted-int16 little-endian 티켓stream SHA를 저장했고,config/code/환경으로 재생성 가능합니다.

```powershell
& "C:\Users\admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" "C:\Users\admin\Documents\Codex\2026-10-09\6-45-jiae-jeong-lotto-data\outputs\B_RANDOM_BASELINE_20261009_v1\run_b_random_baseline.py"
```

```text
START UTC=2026-10-09T12:19:29.402520+00:00 seed=20261009 targets=350 tickets_per_target=10000
BLOCK 1/7 [201, 250] completed comparisons=500000
BLOCK 2/7 [401, 450] completed comparisons=1000000
BLOCK 3/7 [601, 650] completed comparisons=1500000
BLOCK 4/7 [801, 850] completed comparisons=2000000
BLOCK 5/7 [1001, 1050] completed comparisons=2500000
BLOCK 6/7 [1101, 1150] completed comparisons=3000000
BLOCK 7/7 [1151, 1200] completed comparisons=3500000
COMPLETE comparisons=3500000 mean=0.800745714286 variance=0.614839443910 elapsed=2.562s
Existing B classifications preserved;predictive evidence INSUFFICIENT EVIDENCE;actual1245 NOT READ / NOT USED
```

## 3. Random pooled0~6분포

| k | 실제Count | MonteCarlo확률 | 이론확률 | 차이 | MC Wilson95%CI |
|---:|---:|---:|---:|---:|---|
| 0 | 1400364 | 0.400104000000 | 0.400564636725 | -0.000460636725 | [0.399590848637,0.400617370647] |
| 1 | 1485365 | 0.424390000000 | 0.424127262414 | +0.000262737586 | [0.423872284744,0.424907881229] |
| 2 | 530548 | 0.151585142857 | 0.151474022291 | +0.000111120566 | [0.151209820668,0.151961229858] |
| 3 | 78838 | 0.022525142857 | 0.022440595895 | +0.000084546962 | [0.022370212566,0.022681121261] |
| 4 | 4791 | 0.001368857143 | 0.001364630831 | +0.000004226311 | [0.001330666277,0.001408142562] |
| 5 | 93 | 0.000026571429 | 0.000028729070 | -0.000002157642 | [0.000021692099,0.000032548258] |
| 6 | 1 | 0.000000285714 | 0.000000122774 | +0.000000162940 | [0.000000050436,0.000001618551] |

| 지표 | MC 값 | 이론값 | 차이 | MC95%CI |
|---|---:|---:|---:|---|
| mean | 0.800745714286 | 0.800000000000 | +0.000745714286 | [0.799924238192,0.801567190380] |
| variance | 0.614839443910 | 0.614545454545 | +0.000293989365 | [0.613914482908,0.615764404912] |
| 2+ | 0.175506000000 | 0.175308100861 | +0.000197899139 | [0.175107832833,0.175904879469] |
| 3+ | 0.023920857143 | 0.023834078570 | +0.000086778573 | [0.023761295999,0.024081463336] |
| 4+ | 0.001395714286 | 0.001393482675 | +0.000002231610 | [0.001357145815,0.001435377252] |
| 5+ | 0.000026857143 | 0.000028851844 | -0.000001994701 | [0.000021949005,0.000032862780] |
| 6+ | 0.000000285714 | 0.000000122774 | +0.000000162940 | [0.000000050436,0.000001618551] |

- MC rateCI는Wilson입니다. MeanCI는CLT,varianceCI는4차 central moment 기반 delta-method로 Monte Carlo오차를 기술합니다. 매우 희귀한6+는1회 관측되어 정밀한 경험확률 추정이 어렵습니다.
- 전체분포 diagnostic:χ²(5)=4.352349,p≈0.499878. bin5/6을5+로 합쳐 희소 기대도수를 완화했습니다. 이diagnostic을 이유로seed/표본수를 재선정하지 않았습니다.

## 4.7블록별Random

| 구간 | MC비교수 | mean | mean95%CI | 2+ | 3+ | 4+ | 5+ | 6+ |
|---|---:|---:|---|---:|---:|---:|---:|---:|
| 201–250 | 500000 | 0.801412000 | [0.799235930,0.803588070] | 17.568800% | 2.432600% | 0.139400% | 0.001800% | 0.000000% |
| 401–450 | 500000 | 0.800368000 | [0.798196906,0.802539094] | 17.553400% | 2.358400% | 0.134200% | 0.003600% | 0.000000% |
| 601–650 | 500000 | 0.801168000 | [0.798996371,0.803339629] | 17.544000% | 2.364600% | 0.148400% | 0.002000% | 0.000000% |
| 801–850 | 500000 | 0.800502000 | [0.798327266,0.802676734] | 17.552800% | 2.405000% | 0.140000% | 0.002600% | 0.000200% |
| 1001–1050 | 500000 | 0.798972000 | [0.796802293,0.801141707] | 17.502000% | 2.351200% | 0.129400% | 0.003400% | 0.000000% |
| 1101–1150 | 500000 | 0.800574000 | [0.798398593,0.802749407] | 17.514200% | 2.430200% | 0.143200% | 0.002800% | 0.000000% |
| 1151–1200 | 500000 | 0.802224000 | [0.800048711,0.804399289] | 17.619000% | 2.402600% | 0.142400% | 0.002600% | 0.000000% |

- 각 블록의0~6 counts/rates/CI/이론차이는 다음 파일에 보존했습니다: `MC_BLOCK_AND_POOLED_SUMMARY.csv`。target별 원시 집계는 `MC_TARGET_AGGREGATES.csv`입니다.

## 5.B8모델과 동일350회 비교

**B는350회×1티켓/model,random은동일350회×10,000티켓입니다.** random350만개를B의추가관측으로 취급하지 않습니다. 아래B CI의 분모는350이며,random의큰N은baseline계산오차만 줄입니다.

| 모델 | Bmean | Bmean95%CI | B−MCmean | 2+ | 2+95%CI | 원래분류 |
|---|---:|---|---:|---:|---|---|
| long_frequency | 0.737142857 | [0.653331,0.820955] | -0.063602857 | 14.8571% | [11.5133%,18.9641%] | ADDITIONAL VALIDATION |
| current_gap | 0.774285714 | [0.698124,0.850447] | -0.026460000 | 15.7143% | [12.2763%,19.8967%] | ADDITIONAL VALIDATION |
| frequency_plus_gap | 0.828571429 | [0.744402,0.912741] | +0.027825714 | 20.5714% | [16.6671%,25.1148%] | ADDITIONAL VALIDATION |
| recent_momentum | 0.745714286 | [0.669304,0.822125] | -0.055031429 | 14.5714% | [11.2598%,18.6523%] | ADDITIONAL VALIDATION |
| structure_profile | 0.851428571 | [0.767153,0.935704] | +0.050682857 | 19.1429% | [15.3649%,23.5908%] | ADDITIONAL VALIDATION |
| pair_association | 0.834285714 | [0.756638,0.911934] | +0.033540000 | 18.0000% | [14.3293%,22.3655%] | ADDITIONAL VALIDATION |
| triple_association | 0.825714286 | [0.744482,0.906946] | +0.024968571 | 18.5714% | [14.8464%,22.9788%] | ADDITIONAL VALIDATION |
| combined_equal_rank | 0.802857143 | [0.721815,0.883899] | +0.002111429 | 18.5714% | [14.8464%,22.9788%] | HOLD |

- MeanCI:t(df349)의고정Cornish-Fisher근사;rate2+:Wilson. 이론기준선과 차이CI는각CI에서정확기준값을뺀것입니다. Monte Carlo baseline차이 meanCI는B 표본SE와MC SE를분리해합산한근사입니다.
- 원래 .828571429/.851428571/.802857143 및HOLD분류는 `B_REPRODUCTION_REFERENCE_FROZEN.json`에fullprecision과SHA로고정.0.7743/0.7571/0.8065는 UNRESOLVED_HISTORICAL_RESULT로배제되며혼합/평균하지않았습니다.

## 6.시기별변동성 및 불확실성

| 모델 | 7블록meanSD | min~max | exact0.8초과블록 | MC초과블록 | wholeblock bootstrap mean95%CI |
|---|---:|---|---:|---:|---|
| long_frequency | 0.114559 | 0.520–0.840 | 2/7 | 2/7 | [0.651429,0.805714] |
| current_gap | 0.191734 | 0.420–0.980 | 4/7 | 4/7 | [0.634286,0.894286] |
| frequency_plus_gap | 0.080711 | 0.680–0.940 | 5/7 | 5/7 | [0.771429,0.880000] |
| recent_momentum | 0.182104 | 0.540–1.020 | 3/7 | 3/7 | [0.625714,0.874286] |
| structure_profile | 0.159105 | 0.680–1.120 | 4/7 | 5/7 | [0.745714,0.965714] |
| pair_association | 0.084628 | 0.740–0.960 | 4/7 | 4/7 | [0.777143,0.891429] |
| triple_association | 0.079762 | 0.700–0.920 | 5/7 | 5/7 | [0.768571,0.877143] |
| combined_equal_rank | 0.121342 | 0.660–0.980 | 3/7 | 3/7 | [0.722857,0.888571] |

- bootstrap는고정seed20261010으로50회블록전체를7개복원추출하는20,000회percentile법입니다. 같은 가중치를8모델에적용하여모델상관을유지했습니다. 블록이7개뿐이므로안정성/불확실성추정도제한적입니다.
- 중첩window를독립증거로계산하지않았으며,각평가의350회/7블록만사용했습니다. 긴학습구간의모델의존성/시간상관은350행독립가정CI만으로전부반영되지않아wholeblock결과를병기했습니다.
- 구조모델의exact우세4/7과MC우세5/7차이는mean0.8인블록이작은MC잡음으로판정이바뀔수있기때문입니다. 이것을새로운안정적우위로해석하거나기존B분류를바꾸지않습니다.

## 7.탐색적통계검정과판정

- Mean:teststat=350회합계적중;정확hypergeometric PMF의350중convolution으로two-sided absolute-distance null검정.
- 2+:Binomial(350,exactp2+)의probability-ordered two-sided exact검정.8모델×2지표=16test family에Holm보정. 공정·독립추첨가정과미래정보를사용하지않는고정모델에대한탐색적검정입니다. 사후모델설계/기간선택편향을제거하지않습니다.
- **Holm16보정p모두1.0.** 350행meanCI와Wilson2+CI도모두이론기준선을포함합니다. 통계적으로검증된양의예측우위는INSUFFICIENT EVIDENCE입니다.

| 판정질문 | 이번결과 |
|---|---|
| 관측수치차이 | 양/음차이존재.예:frequency_plus_gap+0.027825714,structure_profile+0.050682857(meanvsMC). |
| 여러시기안정성 | 모델별2~5/7exact우세;블록간변동이있음.단일pooled점수만으로안정성확정불가. |
| 우연변동을넘는근거 | 주된CI는null포함,Holm검정유의하지않음,posthoc/7block한계.INSUFFICIENT EVIDENCE. |

## 8.자체검증·보존·실행오류

- 계획seal은MC실행전에config/code/reference/protocolSHA와UTC를기록했습니다. 공식실행후그seal과7개readonlyB입력SHA재검증PASS.
- 독립집계검산:350target,7block+pooled8row,8modelmean/rate/histogram,56blockcomparison과모든공식N확인.7target×10,000randomstream재생성은원래streamSHA와count모두같았습니다. 검증replay70,000은공식3,500,000에추가하지않습니다.
- 검증helper첫attempt는UTF8JSON을cp949로읽어실패했습니다.검증helper의readencoding만명시UTF8로수정후PASS; `VERIFICATION_ATTEMPT_1.log`보존. MC코드/조건/결과는수정/재실행하지않았습니다.
- 첫감사commit의defaultGitdiffcheck가CRLF를공백으로판정하여중단한기록을보존합니다.명령한정cr-at-eol검사에서실제공백검사통과및모든stagedbytesSHA일치후push.개행변환이나기존Bfile수정없음.
- V3봉인게이트의미복구사항은별도입니다.이번baseline으로V3게이트를PASS로바꾸지않으며자동화/알림설정변경0.

## 9.재현명령·파일

공식실행명령은위ACTUAL_EXECUTION_RESULT.json과동일합니다.재실행시이완료디렉터리를덮어쓰지말고새버전에실행code/config/reference를보존하여사용해야합니다.실행code는기존파일이있으면open(x)로중단합니다.

```powershell
& "C:\Users\admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" "C:\Users\admin\Documents\Codex\2026-10-09\6-45-jiae-jeong-lotto-data\outputs\B_RANDOM_BASELINE_20261009_v1\verify_b_random_baseline.py"
```

- `RUN_CONFIG.json`,`RUN_PLAN_SEAL.json`:seed,환경조건,대상구간,통계방법사전고정.
- `B_REPRODUCTION_REFERENCE_FROZEN.json`:현재B기준버전.
- `UNRESOLVED_HISTORICAL_RESULT.json`:미확보이전값격리.
- `MC_TARGET_AGGREGATES.csv`,`MC_BLOCK_AND_POOLED_SUMMARY.csv`:실제MC전수집계.
- `RANDOM_TICKET_STREAM_HASHES.csv`:각targetactualrandomticketstream재현해시.
- `B_VS_RANDOM_POOLED.csv`,`B_VS_RANDOM_BLOCKS.csv`:같은350회모델/블록비교및CI.
- `EXPLORATORY_STATISTICAL_TESTS.json`:16개raw/Holm검정과MC분포diagnostic.
- `EXECUTION_STDOUT.log`,`EXECUTION_STDERR.log`,`RUN_METADATA.json`,`ACTUAL_EXECUTION_RESULT.json`:실제실행로그와조건.
- `FINAL_VERIFICATION.json`,`SHA256_MANIFEST.csv`:검증결과와파일무결성. manifest는자기자신을제외합니다.

## 10.남은항목

1. 0.7743/0.7571/random0.8065의원본실행근거미확보;평가에미사용.
2. exacthistorical전체Breport원본미확보.새report와기존CSV재현을구분.
3. 5·6적중률의정밀한경험추정에는더많은표본이필요.이번seed/표본수를사후조정하지않음.
4. 독립prospective성능은이번과거350회검증으로입증되지않음.실제예측우위판정은보류.

**1245실제결과NOT READ / NOT USED. 신규추천번호·구매후보·최종3줄생성0.**
