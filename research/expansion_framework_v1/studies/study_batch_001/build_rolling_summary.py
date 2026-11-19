"""Persist rolling-window study summary and explicit classifications."""
import csv
from pathlib import Path
P=Path(__file__).resolve().parent
def read(n):
 with (P/n).open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def write(n,rows):
 with (P/n).open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main():
 metrics=read('rolling300_metrics.csv');write('rolling300_study_results.csv',metrics)
 rows=[]
 for r in metrics:
  d=float(r['delta_mean_vs_random']);rate=float(r['rate_ge_2']);base=float(r['baseline_rate_ge_2']);rows.append({'model':r['model'],'window':r['window'],'status':'WEAK' if d<=0 else 'HOLD','mean_hits':r['mean_hits'],'baseline_mean':r['baseline_mean_hits'],'mean_delta':d,'rate_ge_2':rate,'baseline_rate_ge_2':base,'rate_ge_2_delta':rate-base,'interpretation':'Rolling 300, post-hoc descriptive only; no prospective confirmation'})
 write('rolling300_failure_registry.csv',rows);print(f'ROLLING_SUMMARY_OK metrics={len(metrics)}')
if __name__=='__main__':main()
