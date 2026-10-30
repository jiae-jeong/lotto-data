import csv,json,math,random
from collections import Counter
D=[]
with open('lotto_data.csv',encoding='utf-8-sig') as f:
 r=csv.DictReader(f)
 for x in r:
  vals=list(x.values()); nums=[]
  for k,v in x.items():
   if k and any(z in k.lower() for z in ['bonus','보너스']): continue
   try:
    n=int(v)
    if 1<=n<=45: nums.append(n)
   except: pass
  # conservative: take six lottery-number-like values after excluding round where possible
  if len(nums)>=6: D.append(nums[-6:])
D=D[:1247]
# deterministic cutoff-safe ranking: multi-horizon frequency + gap diversification
hs=[60,150,300,600]
def rank(hist):
 sc={n:0.0 for n in range(1,46)}
 for h,w in zip(hs,[1.0,.8,.55,.3]):
  c=Counter(n for row in hist[-h:] for n in row)
  den=max(1,min(h,len(hist)))
  for n in sc: sc[n]+=w*c[n]/den
 last={n:-1 for n in sc}
 for i,row in enumerate(hist):
  for n in row:last[n]=i
 for n in sc: sc[n]+=.015*min(30,len(hist)-1-last[n])/30
 return sorted(sc,key=lambda n:(-sc[n],n))
def portfolio(order,mode):
 top=order[:30]
 if mode=='rr': return [sorted(top[i::5][:6]) for i in range(5)]
 if mode=='snake':
  bins=[[] for _ in range(5)]
  for j,n in enumerate(top): bins[(j//5)%2*4 + (j%5 if (j//5)%2==0 else -(j%5))].append(n)
  return [sorted(x[:6]) for x in bins]
 if mode=='contig': return [sorted(top[i*6:(i+1)*6]) for i in range(5)]
 # stride7 deterministic permutation
 p=[top[(j*7)%30] for j in range(30)]; return [sorted(p[i*6:(i+1)*6]) for i in range(5)]
def metrics(P,y):
 hs=[len(set(t)&set(y)) for t in P]; u=set().union(*map(set,P))
 return [max(hs),int(max(hs)>=2),int(max(hs)>=3),len(u&set(y))]
def exact_null(P):
 # matched union size=30; analytic/simulation deterministic comparator seed
 rng=random.Random(5401248); z=[0,0,0,0]; B=20000
 for _ in range(B):
  q=[]; pool=rng.sample(range(1,46),30)
  for i in range(5):q.append(pool[i*6:(i+1)*6])
  m=metrics(q,rng.sample(range(1,46),6))
  z=[a+b for a,b in zip(z,m)]
 return [a/B for a in z]
# prequential fixed finite modes; evaluate last 850 rounds after warmup
modes=['rr','snake','contig','stride7']; out={}
for mode in modes:
 rows=[]
 for t in range(397,len(D)):
  P=portfolio(rank(D[:t]),mode); rows.append(metrics(P,D[t]))
 avg=[sum(x[j] for x in rows)/len(rows) for j in range(4)]; null=exact_null(portfolio(rank(D),mode)); delta=[avg[j]-null[j] for j in range(4)]
 # conservative block stability and normal lower CI Bonferroni-like z=2.5
 cis=[]; shares=[]
 for j in range(4):
  dif=[]
  rng=random.Random(540000+j)
  for x in rows:
   # comparator expected proxy via null; paired outcome delta
   dif.append(x[j]-null[j])
  mu=sum(dif)/len(dif); var=sum((a-mu)**2 for a in dif)/(len(dif)-1); lo=mu-2.5*math.sqrt(var/len(dif)); cis.append(lo)
  bl=[sum(dif[k:k+50])/len(dif[k:k+50]) for k in range(0,len(dif),50) if len(dif[k:k+50])==50]; shares.append(sum(x>0 for x in bl)/len(bl))
 strict=all(x>0 for x in cis[:3]+[cis[3]]) and all(x>=.70 for x in shares[:3]+[shares[3]])
 out[mode]={'avg':avg,'null':null,'delta':delta,'ci_lower':cis,'block_positive_share':shares,'strict_portfolio_pass':strict,'lines':portfolio(rank(D),mode)}
best=next((m for m in modes if out[m]['strict_portfolio_pass']),None)
res={'target':1248,'cutoff':1247,'version':'V54','no_future_leakage':True,'randomness_final':False,'candidates':out,'strict_portfolio_pass':best is not None,'chosen':best,'lines':out[best]['lines'] if best else None}
print(json.dumps(res,ensure_ascii=False))
