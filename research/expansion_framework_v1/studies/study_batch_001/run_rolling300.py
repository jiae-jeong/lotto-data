"""Additional rolling 300-draw comparison for batch 001."""
import csv,importlib.util,statistics,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('batch_core',HERE/'run_batch.py');m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
def write(name,rows):
 with (HERE/name).open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main():
 draws=m.load_draws_through(m.DATA,1244);bank=m.candidate_bank();m.BASE_PROFILES={q:m.prof(q,()) for q in bank};rows=[]
 for target in range(501,1245):
  cutoff=target-1;start=max(0,cutoff-300);train=draws[start:cutoff];actual=set(draws[target-1].numbers);preds=m.make_models(train,bank)
  for mid,name,fam,rule in m.MODELS:
   ticket,scores=preds[name];rows.append({'research_id':mid,'model':name,'target_round':target,'training_start_round':train[0].round,'training_through_round':cutoff,'training_window_n':len(train),'window_mode':'rolling300','predicted_numbers':' '.join(map(str,ticket)),'actual_numbers':' '.join(map(str,sorted(actual))),'hits':len(set(ticket)&actual)})
 write('rolling300_predictions.csv',rows)
 out=[]
 for mid,name,fam,rule in m.MODELS:
  for label,lo,hi in [('rolling300_all_501_1244',501,1244),('rolling300_recent200',1045,1244),('rolling300_recent100',1145,1244),('rolling300_recent50',1195,1244)]:
   h=[int(r['hits']) for r in rows if r['model']==name and lo<=int(r['target_round'])<=hi];out.append({'research_id':mid,'model':name,'window':label,**m.stats(h)})
 write('rolling300_metrics.csv',out);print(f'ROLLING300_OK predictions={len(rows)} targets=501..1244')
if __name__=='__main__':main()
