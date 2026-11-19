# 재현 검증 및 명령 보충

공식 과학 계산과 독립 verification은 각각 종료 코드 0이다. 추가 재현 검증에서 계산/관계 선택/인용 대조 결과 11개 파일이 byte-identical이었다. 타임스탬프와 보고서 경로를 담은 파일은 byte-identical 비교 대상에서 제외했다.

RUN_FOLLOWUP.py는 실제 실행한 workspace orchestration 코드로서 work/ 위치를 기준으로 경로를 찾는다. 산출물 폴더에 보존한 복사본을 그 위치에서 단독 실행하면 경로 기준이 다르므로 직접 실행하지 않는다. FOLLOWUP_REPORT.md의 일반 재현 명령은 이 workspace 경로 보정 없이 사용할 수 없다. 이번 검증은 REPLAY_FOLLOWUP.py의 I/O 어댑터로 실제 수행했고, 통계/선별 규칙은 수정하지 않았다.

실제 사용한 명령:

```powershell
& 'C:\Users\admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'work\replay_relation_followup_20261010.py' --root 'C:\Users\admin\Documents\Codex\2026-10-09\6-45-jiae-jeong-lotto-data' --output 'C:\Users\admin\Documents\Codex\2026-10-09\6-45-jiae-jeong-lotto-data\work\A_SOURCE_RELATION_DETERMINISM_20261010_v1'
```

다시 실행하려면 --output만 새로 존재하지 않는 폴더로 지정해야 한다. 어댑터는 기존 workspace state/기준 산출물과 실행 원본 코드의 SHA-256을 검증한다. 다른 PC에서 단독 실행 가능한 패키징은 NOT EXECUTED이다.

과거 인용의 p값은 현재 exact 계산과 해당 표기 정밀도에서 불일치한다. 원인에 대한 원본 증거가 없으므로 UNCONFIRMED이다. 이 불일치는 현재 보정 후 채택 근거가 없다는 결론을 바꾸지 않는다. 수치 차이를 맞추려고 입력/규칙을 변경하지 않았다.
