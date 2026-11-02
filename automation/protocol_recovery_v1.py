#!/usr/bin/env python3
"""Recover protocol evidence from authentic preserved records and cutoff-safe tests.

This script does not generate a purchase recommendation. It closes two evidence gaps:
1) review completed rounds using the recommendation that was actually delivered/purchased
   when such an artifact exists, otherwise the authentic pre-draw FINAL artifact;
2) score operational signal families with a cutoff-safe walk-forward and verify the
   existing model-level pair/triple and ablation evidence from the fresh MASTER run.
"""
from __future__ import annotations

import csv
import json
import statistics
import sys
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "lotto_data.csv"
KST = timezone(timedelta(hours=9))
ACTIVE_SIGNALS = ("recent30", "gap", "momentum", "balanced", "contrarian")


def load_rows():
    out = []
    with DATA.open(encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            out.append({
                "round": int(r["round"]),
                "date": r["date"],
                "nums": [int(r[f"no{i}"]) for i in range(1, 7)],
                "bonus": int(r["bonus"]),
            })
    rounds = [r["round"] for r in out]
    assert rounds == list(range(1, max(rounds) + 1))
    return out


def zscore(vals):
    xs = list(vals.values())
    mean = statistics.mean(xs)
    sd = statistics.pstdev(xs) or 1.0
    return {k: (v - mean) / sd for k, v in vals.items()}


def features(hist_nums):
    f30 = Counter(n for d in hist_nums[-30:] for n in d)
    f10 = Counter(n for d in hist_nums[-10:] for n in d)
    fprev20 = Counter(n for d in hist_nums[-30:-10] for n in d)
    gaps = {}
    for n in range(1, 46):
        g = 0
        for d in reversed(hist_nums):
            if n in d:
                break
            g += 1
        gaps[n] = g
    recent30 = zscore({n: f30[n] for n in range(1, 46)})
    gap = zscore(gaps)
    momentum = zscore({n: f10[n] / 10 - fprev20[n] / 20 for n in range(1, 46)})
    return {
        "recent30": recent30,
        "gap": gap,
        "momentum": momentum,
        "balanced": {n: (recent30[n] + gap[n]) / 2 for n in range(1, 46)},
        "contrarian": {n: (-recent30[n] + gap[n]) / 2 for n in range(1, 46)},
    }


def top_ticket(score):
    return sorted(sorted(range(1, 46), key=lambda n: (-score[n], n))[:6])


def write_csv(path, rows):
    rows = list(rows)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def _artifact_role(path: Path):
    name = path.name
    if name.startswith("ACTUAL_PURCHASE_FIVE_LINES"):
        return "ACTUAL_PURCHASE"
    if name.startswith("FINAL_FIVE_LINES"):
        return "FINAL_PREDRAW"
    return "OTHER"


def _candidate_paths():
    base = ROOT / "research" / "weekly_purchase"
    found = set(base.glob("*/ACTUAL_PURCHASE_FIVE_LINES*.json"))
    found.update(base.glob("*/FINAL_FIVE_LINES*.json"))
    return sorted(found)


def build_historical_closed_loop(rows, dated):
    by_round = {r["round"]: r for r in rows}
    cutoff = rows[-1]["round"]
    candidates = []
    for p in _candidate_paths():
        try:
            obj = json.loads(p.read_text(encoding="utf-8-sig"))
            target = int(obj.get("target_round", p.parent.name))
        except Exception as e:
            candidates.append({"path": str(p.relative_to(ROOT)), "valid": False, "reason": f"parse:{e}"})
            continue
        if target > cutoff:
            continue
        candidates.append({
            "path": str(p.relative_to(ROOT)),
            "target": target,
            "obj": obj,
            "valid": True,
            "role": _artifact_role(p),
        })

    grouped = {}
    invalid = []
    for c in candidates:
        if not c.get("valid"):
            invalid.append(c)
            continue
        grouped.setdefault(c["target"], []).append(c)

    reviews = []
    all_hits = []
    for target in sorted(grouped):
        entries = grouped[target]
        actual_purchase = sorted(
            (x for x in entries if x["role"] == "ACTUAL_PURCHASE"),
            key=lambda x: (x["obj"].get("created_kst", "9999"), x["path"]),
        )
        final_predraw = sorted(
            (x for x in entries if x["role"] == "FINAL_PREDRAW"),
            key=lambda x: (x["obj"].get("created_kst", x["obj"].get("recommendation_date_kst", "9999")), x["path"]),
        )
        # The real delivered/purchase artifact is the canonical learning record.
        # A later research/final artifact must never replace what the user actually received.
        c = actual_purchase[0] if actual_purchase else final_predraw[0]
        obj = c["obj"]
        tickets = obj.get("final_lines")
        training_cutoff = obj.get("training_cutoff", obj.get("data_cutoff"))
        valid = (
            target in by_round
            and isinstance(tickets, list)
            and len(tickets) == 5
            and all(
                isinstance(t, list) and len(t) == 6 and len(set(t)) == 6
                and all(isinstance(n, int) and 1 <= n <= 45 for n in t)
                for t in tickets
            )
            and training_cutoff is not None
            and int(training_cutoff) < target
        )
        if not valid:
            invalid.append({"path": c["path"], "target": target, "reason": "integrity_or_cutoff"})
            continue
        actual = set(by_round[target]["nums"])
        hits = [len(set(t) & actual) for t in tickets]
        all_hits.extend(hits)
        union = set().union(*(set(t) for t in tickets))
        union_hits = len(union & actual)
        max_hits = max(hits)
        reviews.append({
            "target_round": target,
            "source": c["path"],
            "source_role": c["role"],
            "training_cutoff": int(training_cutoff),
            "winning_numbers": by_round[target]["nums"],
            "bonus": by_round[target]["bonus"],
            "line_hits": hits,
            "max_hits": max_hits,
            "winning_union_coverage": union_hits,
            "ticket_union_size": len(union),
            "candidate_recall_failure": union_hits < 6,
            "ticket_construction_gap": max(0, union_hits - max_hits),
            "alternative_preserved_versions": max(0, len(entries) - 1),
            "all_preserved_sources": sorted(x["path"] for x in entries),
        })

    dist = {str(k): sum(h == k for h in all_hits) for k in range(7)}
    verified_lines = len(all_hits)
    completed_preserved_targets = len(grouped)
    scope_complete = bool(reviews) and not invalid and len(reviews) == completed_preserved_targets
    latest = reviews[-1] if reviews else None
    payload = {
        "generated_kst": datetime.now(KST).isoformat(),
        "scope": "completed rounds with preserved weekly_purchase artifacts; ACTUAL_PURCHASE is canonical when present, otherwise authentic pre-draw FINAL_FIVE_LINES; missing legacy/older originals are not reconstructed",
        "data_cutoff": cutoff,
        "completed_preserved_targets_found": completed_preserved_targets,
        "verified_round_count": len(reviews),
        "verified_purchase_lines": verified_lines,
        "aggregate_hit_distribution": dist,
        "mean_main_hits_per_line": statistics.mean(all_hits) if all_hits else None,
        "rate_ge2": sum(h >= 2 for h in all_hits) / verified_lines if verified_lines else None,
        "rate_ge3": sum(h >= 3 for h in all_hits) / verified_lines if verified_lines else None,
        "rate_ge4": sum(h >= 4 for h in all_hits) / verified_lines if verified_lines else None,
        "closed_loop_complete": scope_complete,
        "whole_history_complete": False,
        "whole_history_note": "Legacy/older recommendation formats outside the discovered weekly_purchase artifacts are not proven complete and must not be described as the full historical closed loop.",
        "actual_purchase_precedence": True,
        "invalid_or_unreviewable_preserved_records": invalid,
        "reviews": reviews,
        "error_note": {
            "latest_completed_review": latest["target_round"] if latest else None,
            "candidate_recall_failure": latest["candidate_recall_failure"] if latest else None,
            "ticket_construction_gap": latest["ticket_construction_gap"] if latest else None,
            "finding": (
                "Both candidate recall and ticket construction need separate diagnosis."
                if latest and latest["candidate_recall_failure"] and latest["ticket_construction_gap"] > 0
                else "Use the measured recall/construction fields; do not force a diagnosis beyond preserved evidence."
            ),
            "action_for_next_policy": "Evaluate candidate recall separately from allocator performance; never learn from a later artifact in place of the actual delivered/purchased lines."
        },
    }
    (dated / "HISTORICAL_CLOSED_LOOP_STATUS.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return payload


def build_signal_scorecard(rows, dated, run_dir):
    draws = [r["nums"] for r in rows]
    per_signal = {s: [] for s in ACTIVE_SIGNALS}
    for idx in range(200, len(draws)):
        hist = draws[:idx]
        actual = set(draws[idx])
        fs = features(hist)
        for s in ACTIVE_SIGNALS:
            ticket = top_ticket(fs[s])
            per_signal[s].append(len(set(ticket) & actual))

    signal_rows = []
    for s in ACTIVE_SIGNALS:
        hits = per_signal[s]
        signal_rows.append({
            "signal": s,
            "targets": len(hits),
            "mean_hits": statistics.mean(hits),
            "random_exact_mean_hits": 0.8,
            "delta_mean_vs_uniform_expectation": statistics.mean(hits) - 0.8,
            "rate_ge2": sum(h >= 2 for h in hits) / len(hits),
            "rate_ge3": sum(h >= 3 for h in hits) / len(hits),
            "rate_ge4": sum(h >= 4 for h in hits) / len(hits),
            "status": "MEASURED_CUTOFF_SAFE",
        })
    write_csv(dated / "FULL_SIGNAL_SCORECARD.csv", signal_rows)

    v = json.loads((run_dir / "VERIFICATION.json").read_text(encoding="utf-8-sig"))
    base = ROOT / v["base_v4"]
    ablation = list(csv.DictReader((run_dir / "AC_CONTRARIAN_SIGNAL_ABLATION.csv").open(encoding="utf-8-sig")))
    bscore = list(csv.DictReader((base / "B_MODEL_SCORECARD.csv").open(encoding="utf-8-sig")))
    ablation_models = {r["model"] for r in ablation}
    ablation_signals = {r["signal"] for r in ablation}
    bmodels = {r["model"] for r in bscore}
    active_ok = len(signal_rows) == len(ACTIVE_SIGNALS) and all(int(r["targets"]) == len(draws) - 200 for r in signal_rows)
    ablation_ok = len(ablation) == 12 and ablation_models == {"A_v2", "C_v2", "contrarian_v2"} and ablation_signals == {"long_frequency", "recent_100", "gap", "pair"}
    pair_triple_ok = {"pair_association", "triple_association"}.issubset(bmodels)
    complete = bool(active_ok and ablation_ok and pair_triple_ok and v.get("successor_leakage_failures", 1) == 0)
    status = {
        "generated_kst": datetime.now(KST).isoformat(),
        "full_signal_scorecard_complete": complete,
        "scope": "all signal families that directly affect the operational five-ticket selector, plus fresh A/C/contrarian ablations and B pair/triple model evidence",
        "active_weekly_signal_families": list(ACTIVE_SIGNALS),
        "active_weekly_signal_rows": len(signal_rows),
        "active_walkforward_targets_each": len(draws) - 200,
        "model_ablation_rows": len(ablation),
        "model_ablation_signals": sorted(ablation_signals),
        "pair_triple_scorecard_present": pair_triple_ok,
        "successor_leakage_failures": v.get("successor_leakage_failures"),
        "evidence": {
            "active_scorecard": str((dated / "FULL_SIGNAL_SCORECARD.csv").relative_to(ROOT)),
            "successor_ablation": str((run_dir / "AC_CONTRARIAN_SIGNAL_ABLATION.csv").relative_to(ROOT)),
            "b_model_scorecard": str((base / "B_MODEL_SCORECARD.csv").relative_to(ROOT)),
        },
        "partially_covered_inside_structure_profile_but_not_isolated": [],
        "integrity_note": "Every predictive signal row is evaluated only after constructing its ticket from prior draws."
    }
    (dated / "FULL_SIGNAL_SCORECARD_STATUS.json").write_text(
        json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return status


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: protocol_recovery_v1.py YYYY-MM-DD RUN_DIR")
    date = sys.argv[1]
    run_dir = Path(sys.argv[2]).resolve()
    dated = ROOT / "analysis" / date
    dated.mkdir(parents=True, exist_ok=True)
    rows = load_rows()
    hist = build_historical_closed_loop(rows, dated)
    sig = build_signal_scorecard(rows, dated, run_dir)
    result = {
        "status": "PASS" if hist["closed_loop_complete"] and sig["full_signal_scorecard_complete"] else "PARTIAL",
        "historical_closed_loop_complete": hist["closed_loop_complete"],
        "whole_history_complete": hist["whole_history_complete"],
        "actual_purchase_precedence": hist["actual_purchase_precedence"],
        "verified_round_count": hist["verified_round_count"],
        "verified_purchase_lines": hist["verified_purchase_lines"],
        "full_signal_scorecard_complete": sig["full_signal_scorecard_complete"],
    }
    print(json.dumps(result, ensure_ascii=False))
    if result["status"] != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
