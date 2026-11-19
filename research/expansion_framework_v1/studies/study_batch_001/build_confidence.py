"""Deterministic bootstrap summaries for mean-hit uncertainty."""
import csv,random,statistics
from pathlib import Path
HERE=Path(__file__).resolve().parent
def read(p):
 with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def write(name,rows):
 with (HERE/name).open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main():
 rows=read(HERE/'walkforward_predictions.csv');out=[];rng=random.Random(20261008)
 for model in sorted({r['model'] for r in rows}):
  for label,lo,hi in [('overall_201_1244',201,1244),('recent200',1045,1244),('recent100',1145,1244),('recent50',1195,1244)]:
   h=[int(r['hits']) for r in rows if r['model']==model and lo<=int(r['target_round'])<=hi];n=len(h);means=[]; rates=[]
   for _ in range(2000):
    sample=[h[rng.randrange(n)] for _ in range(n)];means.append(statistics.mean(sample));rates.append(sum(x>=2 for x in sample)/n)
   means.sort();rates.sort();out.append({'model':model,'window':label,'n':n,'bootstrap_replicates':2000,'seed':20261008,'mean_hits':statistics.mean(h),'mean_ci95_low':means[49],'mean_ci95_high':means[1949],'rate_ge_2':sum(x>=2 for x in h)/n,'rate_ge_2_ci95_low':rates[49],'rate_ge_2_ci95_high':rates[1949]})
 write('bootstrap_confidence_intervals.csv',out)
 print('BOOTSTRAP_OK',len(out))
if __name__=='__main__':main()
