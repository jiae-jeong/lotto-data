from __future__ import annotations
import argparse, csv, importlib.util, sys
from pathlib import Path
from walkforward_core import load_draws_through,evaluate_expanding,summarize

p=argparse.ArgumentParser(description="Run one preregistered hypothesis using leakage-safe walk-forward.")
p.add_argument("--data",required=True)
p.add_argument("--through-round",type=int,required=True)
p.add_argument("--model",required=True,help="Path to a study module implementing predict(train_draws)")
p.add_argument("--first-target",type=int,required=True)
p.add_argument("--last-target",type=int,required=True)
p.add_argument("--min-training-rounds",type=int,default=200)
p.add_argument("--rolling-window",type=int,default=0,help="0 means expanding; otherwise use only latest N training draws")
p.add_argument("--output-csv",required=True)
a=p.parse_args()
out=Path(a.output_csv)
if out.exists(): raise SystemExit(f"Refusing to overwrite existing output: {out}")
spec=importlib.util.spec_from_file_location("study_model",a.model)
if spec is None or spec.loader is None: raise SystemExit(f"Cannot load model module: {a.model}")
mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod)
if not callable(getattr(mod,"predict",None)): raise SystemExit("Model module must define predict(train_draws)")
draws=load_draws_through(a.data,a.through_round)
rows=evaluate_expanding(draws,mod.predict,a.first_target,a.last_target,a.min_training_rounds,a.rolling_window or None)
metrics=summarize(rows)
with out.open("x",newline="",encoding="utf-8-sig") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
print(f"WROTE {out}; metrics={metrics}")
