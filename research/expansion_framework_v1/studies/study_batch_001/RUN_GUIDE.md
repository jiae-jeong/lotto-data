# Study Batch 001 재실행 방법

프로젝트 루트에서 bundled Python으로 다음을 순서대로 실행한다.

```powershell
python outputs/research_expansion_framework_v1/studies/study_batch_001/run_batch.py
python outputs/research_expansion_framework_v1/studies/study_batch_001/build_diagnostics.py
python outputs/research_expansion_framework_v1/studies/study_batch_001/build_confidence.py
python outputs/research_expansion_framework_v1/studies/study_batch_001/run_rolling300.py
python outputs/research_expansion_framework_v1/studies/study_batch_001/build_rolling_summary.py
```

실제 실행은 연결된 Python 3 절대경로를 사용했다. 모든 분석기는 지정한 원자료에서 1244회까지만 입력으로 로드한다. 첫 명령은 이 배치 폴더의 결과물을 재생성하고, 기존 B-model/원자료/다른 outputs는 쓰지 않는다. 연구 규칙·seed·tie-break 및 cutoff는 `run_batch.py`에 명시되어 있다.

실험은 기존 결과를 확인한 후 설계된 사후 탐색이다. 지표를 확인한 다음 우수 모델만 재평가하지 않았으며, 독립 prospective 검증 전까지 `PROMISING`으로 분류하지 않는다.
