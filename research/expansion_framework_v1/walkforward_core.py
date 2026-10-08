"""Leakage-safe common utilities for research experiments; no model assumptions."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from collections import Counter
import csv, math, statistics

@dataclass(frozen=True)
class Draw:
    round: int
    date: str
    numbers: tuple[int, ...]
    bonus: int | None = None


def load_draws_through(path: str | Path, through_round: int) -> list[Draw]:
    """Read rounds 1..through_round only. Never request or parse the next row."""
    if through_round < 1:
        raise ValueError("through_round must be positive")
    draws=[]; previous_date=None
    with Path(path).open(newline="",encoding="utf-8-sig") as f:
        reader=csv.DictReader(f)
        required={"round","date",*(f"no{i}" for i in range(1,7))}
        missing=required-set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing columns: {sorted(missing)}")
        for expected in range(1,through_round+1):
            row=next(reader,None)
            if row is None:
                raise ValueError(f"Input ended before round {expected}")
            observed=int(row["round"])
            if observed!=expected:
                raise ValueError(f"Expected round {expected}, found {observed}; no draw values from this row were parsed")
            nums=tuple(int(row[f"no{i}"]) for i in range(1,7))
            if len(set(nums))!=6 or any(n<1 or n>45 for n in nums):
                raise ValueError(f"Invalid 6/45 numbers in round {expected}: {nums}")
            date=row["date"].strip()
            parsed_date=None
            for fmt in ("%Y.%m.%d","%Y-%m-%d","%Y/%m/%d"):
                try: parsed_date=datetime.strptime(date,fmt).date(); break
                except ValueError: pass
            if parsed_date is None: raise ValueError(f"Unsupported date in round {expected}: {date!r}")
            if previous_date is not None and parsed_date<=previous_date:
                raise ValueError(f"Duplicate or non-increasing draw date in round {expected}: {date!r}")
            previous_date=parsed_date
            bonus=int(row["bonus"]) if row.get("bonus","").strip() else None
            if bonus is not None and (bonus<1 or bonus>45 or bonus in nums):
                raise ValueError(f"Invalid bonus in round {expected}: {bonus}")
            draws.append(Draw(expected,date,tuple(sorted(nums)),bonus))
    return draws


def exact_random_baseline() -> dict:
    denominator=math.comb(45,6)
    probabilities=[math.comb(6,k)*math.comb(39,6-k)/denominator for k in range(7)]
    mean=sum(k*probabilities[k] for k in range(7))
    variance=sum((k-mean)**2*probabilities[k] for k in range(7))
    return {"probabilities":probabilities,"mean_hits":mean,"variance_hits":variance,
            "rate_ge_2":sum(probabilities[2:]),"rate_ge_3":sum(probabilities[3:]),
            "rate_ge_4":sum(probabilities[4:]),"rate_ge_5":sum(probabilities[5:]),
            "rate_exact_6":probabilities[6]}


def evaluate_expanding(draws: list[Draw], predictor, first_target: int,
                       last_target: int | None = None, min_training_rounds: int = 1,
                       rolling_window: int | None = None) -> list[dict]:
    """Predict target t by passing only draws strictly earlier than t to predictor."""
    last_target=last_target or draws[-1].round
    if [d.round for d in draws] != list(range(1,len(draws)+1)):
        raise ValueError("draws must be contiguous from round 1")
    if first_target<2 or last_target>len(draws) or first_target>last_target:
        raise ValueError("Invalid target interval")
    results=[]
    for target in range(first_target,last_target+1):
        cutoff=target-1
        start=max(0,cutoff-rolling_window) if rolling_window else 0
        train=tuple(draws[start:cutoff])
        if len(train)<min_training_rounds:
            continue
        if train[-1].round>=target:
            raise AssertionError("Leakage guard failed: training includes target/future draw")
        ticket=tuple(predictor(train))
        if len(ticket)!=6 or len(set(ticket))!=6 or any(not isinstance(n,int) or n<1 or n>45 for n in ticket):
            raise ValueError(f"Predictor returned invalid ticket for target {target}: {ticket}")
        actual=draws[target-1].numbers
        hits=len(set(ticket)&set(actual))
        results.append({"target_round":target,"training_through_round":cutoff,
                        "training_start_round":train[0].round,"predicted_numbers":" ".join(map(str,sorted(ticket))),
                        "actual_numbers":" ".join(map(str,actual)),"hits":hits})
    return results


def summarize(records: list[dict]) -> dict:
    if not records: raise ValueError("Cannot summarize an empty evaluation")
    hits=[int(r["hits"]) for r in records]
    baseline=exact_random_baseline()
    hist=Counter(hits); n=len(hits)
    out={"n":n,"mean_hits":statistics.mean(hits),"variance_hits_population":statistics.pvariance(hits)}
    for k in range(7): out[f"hits_{k}_count"]=hist[k]
    for k in range(2,6): out[f"rate_ge_{k}"]=sum(h>=k for h in hits)/n
    out["rate_exact_6"]=sum(h==6 for h in hits)/n
    out["baseline_mean_hits"]=baseline["mean_hits"]
    for k in range(2,6): out[f"baseline_rate_ge_{k}"]=baseline[f"rate_ge_{k}"]
    out["baseline_rate_exact_6"]=baseline["rate_exact_6"]
    out["delta_mean_vs_random"]=out["mean_hits"]-baseline["mean_hits"]
    return out
