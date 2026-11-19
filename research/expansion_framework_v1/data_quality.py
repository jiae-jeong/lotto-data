from __future__ import annotations
import argparse
from walkforward_core import load_draws_through

p=argparse.ArgumentParser(description="Read-only 6/45 source data quality check.")
p.add_argument("--data",required=True)
p.add_argument("--through-round",type=int,required=True,help="Read exactly rounds 1..N; later rows are never requested")
a=p.parse_args()
try:
    draws=load_draws_through(a.data,a.through_round)
except Exception as e:
    print(f"DATA_QUALITY=FAIL: {e}")
    raise SystemExit(2)
dates=[d.date for d in draws]
print(f"DATA_QUALITY=PASS rounds=1..{draws[-1].round} rows={len(draws)}")
print(f"columns required: round,date,no1..no6; bonus validated when present")
print(f"date range: {dates[0]} .. {dates[-1]}; unique dates={len(set(dates))}")
if len(set(dates))!=len(dates):
    print("WARNING: duplicate dates found")
