from pathlib import Path
import csv, json, hashlib, os, re, subprocess, datetime, zipfile
ROOT=Path(__file__).resolve().parents[1]
WT=ROOT/'work/primary_mode_1245_v4_clean_20261009'
OUT=ROOT/'outputs/A_ERRORLOOP_C_RESEARCH_20261009_v1'
GIT=r'C:\Users\admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\git\cmd\git.exe'
EXT={'.py','.csv','.json','.md','.ps1','.txt','.log','.yaml','.yml','.toml'}
TERMS=['A_MODEL','model_a','a_model','A model','A 모델','C_MODEL','model_c','c_model','C model','C 모델','contrarian','콘트라리언','역발상','frequency','gap','structure','pair','triple','score','weight','prediction','recommendation','final','candidate','selected','lotto','오답','추천','최종','당첨','A/B/C']
SPECIFIC=re.compile(r'A_MODEL|\bmodel_a\b|\ba_model\b|A model|A 모델|C_MODEL|\bmodel_c\b|\bc_model\b|C model|C 모델|contrarian|콘트라리언|역발상|recommendation|오답|추천|최종',re.I)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def write(name,rows,fields):
    with (OUT/name).open('x',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(rows)
def git(*args):
    r=subprocess.run([GIT,'-C',str(WT),*args],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if r.returncode:raise RuntimeError(r.stderr.decode(errors='replace'))
    return r.stdout
inventory=[];unique={};errors=[];scopes=[]
def inspect(p,scope):
    try:
        raw=p.read_bytes();st=p.stat();h=sha(raw)
        inventory.append(dict(scope=scope,path=str(p),bytes=len(raw),sha256=h,created_utc=datetime.datetime.fromtimestamp(st.st_ctime,datetime.timezone.utc).isoformat(),modified_utc=datetime.datetime.fromtimestamp(st.st_mtime,datetime.timezone.utc).isoformat()))
        if p.name=='lotto_data.csv':
            # Only the pinned, pre-1245 input is allowed; other raw datasets are inventoried without decoding.
            if h!='243cd17e6b97a2d96709ddfc689a068038669341a52dcc0743c141d309e43b9f':return
        if re.search(r'actual.*1245|1245.*actual|result.*1245.*actual',p.name,re.I):return
        if h not in unique:unique[h]=(raw,str(p),scope)
    except (PermissionError,OSError) as e:errors.append(dict(path=str(p),error=repr(e)))
roots=[Path(r'C:\Users\admin\Documents\Codex'),Path(r'C:\Users\admin\Downloads'),Path(r'C:\Users\admin\Desktop'),Path(r'C:\Users\admin\Documents')]
seen=set()
for base in roots:
    scopes.append(dict(path=str(base),exists=base.exists(),method='recursive filename inventory; supported text extensions; SHA deduplicated content scan'))
    if not base.exists():continue
    for d,dirs,files in os.walk(base):
        dirs[:]=[x for x in dirs if x not in {'.git','node_modules','__pycache__','.venv','vendor','official_gh_2_102_0','A_ERRORLOOP_C_RESEARCH_20261009_v1'} and not x.startswith('A_RESEARCH_REMOTE')]
        for name in files:
            p=Path(d)/name
            if p.suffix.lower() not in EXT or p in seen:continue
            seen.add(p);inspect(p,'local')
for p in [Path(r'C:\Users\user\Documents\Codex\2026-10-06\cloud-x20'),Path(r'C:\Users\user\Documents\Codex\2026-10-08\b-model-backtest-py-b-1201')]:scopes.append(dict(path=str(p),exists=p.exists(),method='direct existence check'))
for profile in Path(r'C:\Users').iterdir():
    if profile.is_dir():
        p=profile/'Documents/Codex';scopes.append(dict(path=str(p),exists=p.exists(),method='other-profile Codex root check'))
        if p.exists() and p not in roots:
            for d,dirs,files in os.walk(p):
                dirs[:]=[x for x in dirs if x not in {'.git','node_modules','__pycache__'}]
                for name in files:
                    q=Path(d)/name
                    if q.suffix.lower() in EXT and q not in seen:seen.add(q);inspect(q,'other_profile')
# Record all reachable branches/tags and every distinct historical text blob, including deleted paths.
refs=git('for-each-ref','--format=%(refname) %(objectname)').decode()
commits=git('log','--all','--format=%H|%aI|%cI|%s').decode()
(OUT/'GIT_REFS_AND_COMMITS.txt').write_text(refs+'\n'+commits,encoding='utf-8')
gitrows=[]
for line in git('rev-list','--objects','--all').decode().splitlines():
    parts=line.split(' ',1)
    if len(parts)!=2:continue
    obj,path=parts
    if Path(path).suffix.lower() not in EXT:continue
    if git('cat-file','-t',obj).strip()!=b'blob':continue
    raw=git('cat-file','blob',obj);h=sha(raw)
    gitrows.append(dict(git_blob=obj,path=path,bytes=len(raw),sha256=h))
    if Path(path).name=='lotto_data.csv' and h!='243cd17e6b97a2d96709ddfc689a068038669341a52dcc0743c141d309e43b9f':continue
    if h not in unique:unique[h]=(raw,'git:'+obj+':'+path,'git_history')
# Existing package archive member names are inspected; no extraction, mutation or model execution.
packages=[]
for archive in [Path(r'C:\Users\admin\Downloads\lotto_b_model_recovery_package.zip')]:
    if archive.exists():
        with zipfile.ZipFile(archive) as z:
            for i in z.infolist():packages.append(dict(archive=str(archive),member=i.filename,bytes=i.file_size))
hits=[];specific=[];terms_count={t:0 for t in TERMS}
for h,(raw,path,scope) in unique.items():
    txt=raw.decode('utf-8-sig',errors='replace');lower=txt.lower();found={t:lower.count(t.lower()) for t in TERMS if t.lower() in lower}
    if not found:continue
    for t,c in found.items():terms_count[t]+=c
    excerpts=[]
    for n,line in enumerate(txt.splitlines(),1):
        if SPECIFIC.search(line):
            if len(excerpts)<8:excerpts.append(f'{n}: '+line[:300])
    rec=dict(path=path,scope=scope,sha256=h,keyword_counts=json.dumps(found,ensure_ascii=False),specific_excerpts=json.dumps(excerpts,ensure_ascii=False))
    hits.append(rec)
    if excerpts:specific.append(rec)
write('LOCAL_SOURCE_FILE_INVENTORY.csv',inventory,['scope','path','bytes','sha256','created_utc','modified_utc'])
write('GIT_HISTORICAL_BLOB_INVENTORY.csv',gitrows,['git_blob','path','bytes','sha256'])
write('SOURCE_KEYWORD_HITS.csv',hits,['path','scope','sha256','keyword_counts','specific_excerpts'])
write('SPECIFIC_MODEL_AND_RECOMMENDATION_HITS.csv',specific,['path','scope','sha256','keyword_counts','specific_excerpts'])
write('PACKAGE_MEMBER_INVENTORY.csv',packages,['archive','member','bytes'])
(OUT/'SEARCH_SCOPE_AND_ERRORS.json').write_text(json.dumps(dict(scopes=scopes,errors=errors,local_files=len(inventory),historical_blobs=len(gitrows),unique_text_contents=len(unique),keyword_counts=terms_count,scope_limitations=['Only accessible current PC files and all currently reachable repository refs; no old cloud PC or prior conversation originals.','Generic model_a CSV correlation column is not proof of legacy A identity.','V4_C and S008/V3 combination implementations do not establish legacy C provenance.','Historical backtest predictions are not evidence of contemporaneous purchase recommendations.','Unknown data CSV versions inventoried by hash only; no 1245 outcome queried.']),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(local_files=len(inventory),git_blobs=len(gitrows),unique_contents=len(unique),specific_hit_files=len(specific),errors=len(errors)),ensure_ascii=False))
