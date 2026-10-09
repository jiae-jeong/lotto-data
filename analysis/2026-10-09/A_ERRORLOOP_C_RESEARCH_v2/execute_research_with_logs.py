from pathlib import Path
import subprocess,sys,json,datetime,time,shutil
ROOT=Path(r'C:\Users\admin\Documents\Codex\2026-10-09\6-45-jiae-jeong-lotto-data');OUT=ROOT/'outputs/A_ERRORLOOP_C_RESEARCH_20261009_v2';WT=ROOT/'work/primary_mode_1245_v4_clean_20261009'
cmd=[sys.executable,str(OUT/'run_independent_signal_research.py'),'--repo',str(WT),'--out',str(OUT)]
start=datetime.datetime.now(datetime.timezone.utc).isoformat();t=time.perf_counter()
with (OUT/'EXECUTION_STDOUT.log').open('xb') as stdout,(OUT/'EXECUTION_STDERR.log').open('xb') as stderr:r=subprocess.run(cmd,stdout=stdout,stderr=stderr)
result=dict(command=cmd,started_utc=start,ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),elapsed_seconds=time.perf_counter()-t,exit_code=r.returncode,stdout_bytes=(OUT/'EXECUTION_STDOUT.log').stat().st_size,stderr_bytes=(OUT/'EXECUTION_STDERR.log').stat().st_size)
with (OUT/'ACTUAL_EXECUTION_RESULT.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
shutil.copyfile(Path(__file__),OUT/'execute_research_with_logs.py')
print(json.dumps(result,ensure_ascii=False));print((OUT/'EXECUTION_STDOUT.log').read_text(encoding='utf-8'));print((OUT/'EXECUTION_STDERR.log').read_text(encoding='utf-8'))
sys.exit(r.returncode)
