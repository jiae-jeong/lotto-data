#!/usr/bin/env python3
import os
from pathlib import Path
p=Path(__file__).resolve().parent/'today_twostage_rank_ticket_v67.py'
src=p.read_text(encoding='utf-8')
mode=os.environ.get('V69_MODE','recall_any3')
os.environ['V67_MODE']=mode
src=src.replace('TODAY_TWOSTAGE_RANK_TICKET_{mode}_1248_V67.json','TODAY_TWOSTAGE_OVERLAP_{mode}_1248_V69.json')
src=src.replace("'TWOSTAGE_RANK_TICKET_V67'","'TWOSTAGE_OVERLAP_V69'")
needle="exec(compile(s,str(p),'exec'),globals(),globals())"
patch=r'''# V69: replace disjoint ticket geometry by preregistered overlap family and exact geometry-specific nulls.
oldpat="""PAT={
 'rr':[[0,4,8,12,16,20],[1,5,9,13,17,21],[2,6,10,14,18,22],[3,7,11,15,19,23]],
 'contig':[[0,1,2,3,4,5],[6,7,8,9,10,11],[12,13,14,15,16,17],[18,19,20,21,22,23]],
 'snake':[[0,7,8,15,16,23],[1,6,9,14,17,22],[2,5,10,13,18,21],[3,4,11,12,19,20]],
 'paired':[[0,1,8,9,16,17],[2,3,10,11,18,19],[4,5,12,13,20,21],[6,7,14,15,22,23]]}"""
newpat="PAT={k:None for k in ('repeat1','repeat2','top5x2','top6x2','top10x2','top3x3')}"
assert oldpat in s;s=s.replace(oldpat,newpat)
oldlines="""def lines(core,tail_order,pat):
 L=[tuple(sorted(core))]+[tuple(sorted(tail_order[j] for j in p)) for p in PAT[pat]]
 assert len(L)==5 and len(set(L))==5 and len(set().union(*map(set,L)))==30 and all(len(x)==6 for x in L);return L"""
newlines="""def template(pat):
 if pat=='repeat1': return [[0]+[1+i+5*j for j in range(5)] for i in range(5)]
 if pat=='repeat2': return [[0,1]+[2+i+5*j for j in range(4)] for i in range(5)]
 if pat=='top5x2': return [[i,(i+1)%5]+[5+i+5*j for j in range(4)] for i in range(5)]
 if pat in ('top6x2','top10x2'):
  k=6 if pat=='top6x2' else 10;g=[[] for _ in range(5)]
  for r in range(k):g[r%5].append(r);g[(r+2)%5].append(r)
  u=k
  for i in range(5):
   while len(g[i])<6:g[i].append(u);u+=1
  return g
 g=[[0],[0,1],[0,1,2],[1,2],[2]];u=3
 for i in range(5):
  while len(g[i])<6:g[i].append(u);u+=1
 return g

def lines(core,tail_order,pat):
 order=list(core)+list(tail_order);L=[tuple(sorted(order[j] for j in q)) for q in template(pat)]
 assert len(L)==5 and len(set(L))==5 and all(len(x)==6 and len(set(x))==6 for x in L);return L"""
assert oldlines in s;s=s.replace(oldlines,newlines)
start=s.index('def exact_null_disjoint30():');end=s.index('NULL=exact_null_disjoint30()',start)+len('NULL=exact_null_disjoint30()')
newnull="""def exact_null_geometry(pat):
 L=[tuple(j+1 for j in q) for q in template(pat)];counts=[0]*32
 for n in range(1,46):
  mask=0
  for i,q in enumerate(L):
   if n in q:mask|=1<<i
  counts[mask]+=1
 dp={(0,0,0,0,0,0,0):1}
 for mask,c in enumerate(counts):
  if not c:continue
  nd={}
  for st,w in dp.items():
   k,*rest=st;hits=rest[:5];cov=rest[5]
   for j in range(min(c,6-k)+1):
    mult=math.comb(c,j);nh=[hits[i]+(j if mask&(1<<i) else 0) for i in range(5)];ns=(k+j,*nh,cov+(j if mask else 0));nd[ns]=nd.get(ns,0)+w*mult
  dp=nd
 total=math.comb(45,6);u=len(set().union(*map(set,L)));a={'max_hits':0.,'any2':0.,'any3':0.,'any4':0.,'winning_union_coverage':0.,'union_size':float(u)}
 for st,w in dp.items():
  if st[0]!=6:continue
  h=st[1:6];cov=st[6];m=max(h);pr=w/total;a['max_hits']+=pr*m;a['any2']+=pr*(m>=2);a['any3']+=pr*(m>=3);a['any4']+=pr*(m>=4);a['winning_union_coverage']+=pr*cov
 return a
NULLS={n:exact_null_geometry(n.split(':',1)[1]) for n in NAMES}"""
s=s[:start]+newnull+s[end:]
s=s.replace("v=[float(q[k])-float(NULL[k]) for q in list(hist[n])[-150:]]","v=[float(q[k])-float(NULLS[n][k]) for q in list(hist[n])[-150:]]")
s=s.replace("hist={k:deque(maxlen=150) for k in NAMES};rankhist={r:deque(maxlen=150) for r in RANKMODES};locked_rank='base';locked='base|H:rr';obs=[];diff=", "hist={k:deque(maxlen=150) for k in NAMES};rankhist={r:deque(maxlen=150) for r in RANKMODES};locked_rank='base';locked='base|H:repeat1';obs=[];nullobs=[];diff=")
s=s.replace("chosen='base|H:rr'","chosen='base|H:repeat1'")
oldobs="""  if target>=401:
   count[chosen]+=1;om=met(L,actual);obs.append(om)
   for k in diff:diff[k].append(float(om[k])-NULL[k])"""
newobs="""  if target>=401:
   count[chosen]+=1;om=met(L,actual);sn=NULLS[chosen];obs.append(om);nullobs.append(sn)
   for k in diff:diff[k].append(float(om[k])-float(sn[k]))"""
assert oldobs in s;s=s.replace(oldobs,newobs)
oldscore="score={'policy':{k:avg(obs,k) for k in keys},'matched_exact_label_null':dict(NULL)}"
newscore="score={'policy':{k:avg(obs,k) for k in keys},'matched_exact_label_null':{k:statistics.mean(float(x[k]) for x in nullobs) for k in keys}}"
assert oldscore in s;s=s.replace(oldscore,newscore)
s=s.replace("'union_size':30};break","'union_size':len(set().union(*map(set,L)))};break")
s=s.replace("'selection':'V67 {mode}: stage1 chooses rank family using only prior top30 recall delta vs exact random expectation 4.0; stage2 chooses H/M x disjoint geometry within that frozen rank using prior ticket deltas; both locked for next 50 targets.'",f"'selection':'V69 {mode}: stage1 chooses rank family from prior top30 recall only; stage2 chooses H/M x overlap geometry within that rank from prior geometry-specific exact-null deltas; both locked for next 50 targets.'")
s=s.replace("'partition_signals':'Stage2 uses H plus frozen rolling300 V4_M only; all ticket geometries remain disjoint union30 with identical exact null'","'partition_signals':'Stage2 uses H plus frozen rolling300 V4_M; overlap geometries use their own exact matched-label null'")
exec(compile(s,str(p),'exec'),globals(),globals())'''
assert needle in src
src=src.replace(needle,patch)
exec(compile(src,str(p),'exec'),globals(),globals())
