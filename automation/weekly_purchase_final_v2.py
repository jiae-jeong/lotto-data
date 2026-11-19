#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import itertools
import json
import random
import statistics
import sys
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "lotto_data.csv"
OUTROOT = ROOT / "research" / "weekly_purchase"
POLICY = "WEEKLY_FIVE_TICKET_PORTFOLIO_V2_PROTOCOL_FULL"
SEED = 2026102302
KST = timezone(timedelta(hours=9))
FAMILIES = ("recent30", "gap", "momentum", "balanced", "contrarian", "consensus")
CANDIDATES_PER_FAMILY = 4
BACKTEST_TARGETS = 200
RANDOM_BUNDLES_PER_TARGET = 200


def load():
    rows = []
    with DATA.open(encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            rows.append((int(r["round"]), [int(r[f"no{i}"]) for i in range(1, 7)], int(r["bonus"])))
    rounds = [r[0] for r in rows]
    assert rounds == list(range(1, max(rounds) + 1)) and len(rounds) == len(set(rounds))
    for _, nums, bonus in rows:
        assert len(nums) == 6 and len(set(nums)) == 6 and all(1 <= n <= 45 for n in nums)
        assert 1 <= bonus <= 45 and bonus not in nums
    return rows


def z(vals):
    xs = list(vals.values())
    m = statistics.mean(xs)
    sd = statistics.pstdev(xs) or 1.0
    return {k: (v - m) / sd for k, v in vals.items()}


def features(hist):
    draws = [x[1] for x in hist]
    f30 = Counter(n for d in draws[-30:] for n in d)
    f10 = Counter(n for d in draws[-10:] for n in d)
    fprev20 = Counter(n for d in draws[-30:-10] for n in d)
    gap = {}
    for n in range(1, 46):
        g = 0
        for d in reversed(draws):
            if n in d:
                break
            g += 1
        gap[n] = g
    recent30 = z({n: f30[n] for n in range(1, 46)})
    zgap = z(gap)
    momentum = z({n: f10[n] / 10 - fprev20[n] / 20 for n in range(1, 46)})
    balanced = {n: (recent30[n] + zgap[n]) / 2 for n in range(1, 46)}
    contrarian = {n: (-recent30[n] + zgap[n]) / 2 for n in range(1, 46)}
    consensus = {n: statistics.mean([recent30[n], zgap[n], momentum[n], balanced[n], contrarian[n]]) for n in range(1, 46)}
    return {
        "recent30": recent30,
        "gap": zgap,
        "momentum": momentum,
        "balanced": balanced,
        "contrarian": contrarian,
        "consensus": consensus,
    }


def candidate_bank(score, limit=CANDIDATES_PER_FAMILY):
    ranked = sorted(range(1, 46), key=lambda n: (-score[n], n))
    pool = ranked[:13]
    combos = []
    for c in itertools.combinations(pool, 6):
        combos.append((sum(score[n] for n in c), tuple(sorted(c))))
    combos.sort(key=lambda x: (-x[0], x[1]))
    return [c for _, c in combos[:limit]]


def candidate_pool(hist):
    fs = features(hist)
    raw = []
    for family in FAMILIES:
        for rank, ticket in enumerate(candidate_bank(fs[family])):
            # Rank quality is predeclared and outcome-blind. No target result is used.
            quality = CANDIDATES_PER_FAMILY - rank
            raw.append({"family": family, "rank": rank + 1, "ticket": ticket, "quality": quality})
    # Keep the strongest provenance for duplicate tickets, deterministically.
    dedup = {}
    for c in raw:
        t = c["ticket"]
        key = (c["quality"], -FAMILIES.index(c["family"]), -c["rank"])
        if t not in dedup or key > dedup[t][0]:
            dedup[t] = (key, c)
    out = [x[1] for x in dedup.values()]
    out.sort(key=lambda c: (-c["quality"], FAMILIES.index(c["family"]), c["rank"], c["ticket"]))
    if len(out) < 5:
        raise RuntimeError(f"candidate pool too small: {len(out)}")
    return out


def portfolio_metrics(tickets, actual=None):
    union = set().union(*(set(t) for t in tickets))
    overlaps = [len(set(a) & set(b)) for a, b in itertools.combinations(tickets, 2)]
    counts = Counter(n for t in tickets for n in t)
    out = {
        "ticket_union_size": len(union),
        "pairwise_overlaps": overlaps,
        "mean_pair_overlap": statistics.mean(overlaps),
        "max_pair_overlap": max(overlaps),
        "numbers_reused_3plus": sum(v >= 3 for v in counts.values()),
        "total_reuse_beyond_two": sum(max(0, v - 2) for v in counts.values()),
    }
    if actual is not None:
        hs = [len(set(t) & set(actual)) for t in tickets]
        out.update(
            {
                "line_hits": hs,
                "max_hits": max(hs),
                "any_2plus": int(max(hs) >= 2),
                "any_3plus": int(max(hs) >= 3),
                "any_4plus": int(max(hs) >= 4),
                "any_5plus": int(max(hs) >= 5),
                "any_6": int(max(hs) >= 6),
                "winning_union_coverage": len(union & set(actual)),
            }
        )
    return out


def portfolio_objective(combo):
    tickets = [c["ticket"] for c in combo]
    m = portfolio_metrics(tickets)
    quality = sum(c["quality"] for c in combo)
    overlap_sum = sum(m["pairwise_overlaps"])
    overlap_excess = sum(max(0, x - 2) ** 2 for x in m["pairwise_overlaps"])
    # V2 change: reward broader union coverage and explicitly punish repeated reuse.
    score = (
        1.00 * quality
        + 1.15 * m["ticket_union_size"]
        - 0.55 * overlap_sum
        - 3.00 * overlap_excess
        - 2.00 * m["total_reuse_beyond_two"]
    )
    return score, m


def select(hist):
    pool = candidate_pool(hist)
    best = None
    for idxs in itertools.combinations(range(len(pool)), 5):
        combo = [pool[i] for i in idxs]
        tickets = [c["ticket"] for c in combo]
        score, met = portfolio_objective(combo)
        # A soft operational preference, not a manual patch: among equal-score states,
        # favor larger union and lower maximum overlap.
        tie = (score, met["ticket_union_size"], -met["max_pair_overlap"], -met["total_reuse_beyond_two"], tuple(tickets))
        if best is None or tie > best[0]:
            best = (tie, combo, met)
    combo = best[1]
    tickets = [list(c["ticket"]) for c in combo]
    sources = [{"family": c["family"], "candidate_rank": c["rank"], "quality": c["quality"]} for c in combo]
    return tickets, sources, best[2], len(pool)


def result_metrics(tickets, win):
    m = portfolio_metrics([tuple(t) for t in tickets], actual=set(win))
    return {
        "max_hits": m["max_hits"],
        "any_2plus": m["any_2plus"],
        "any_3plus": m["any_3plus"],
        "any_4plus": m["any_4plus"],
        "any_5plus": m["any_5plus"],
        "any_6": m["any_6"],
        "winning_union_coverage": m["winning_union_coverage"],
        "ticket_union_size": m["ticket_union_size"],
        "mean_pair_overlap": m["mean_pair_overlap"],
        "max_pair_overlap": m["max_pair_overlap"],
    }


def backtest(rows):
    start = max(200, len(rows) - BACKTEST_TARGETS)
    policy = []
    random_rows = []
    universe = list(range(1, 46))
    for i in range(start, len(rows)):
        tickets, _, _, _ = select(rows[:i])
        actual = rows[i][1]
        policy.append(result_metrics(tickets, actual))
        rng = random.Random(SEED + rows[i][0])
        for _ in range(RANDOM_BUNDLES_PER_TARGET):
            rb = [sorted(rng.sample(universe, 6)) for __ in range(5)]
            random_rows.append(result_metrics(rb, actual))
    keys = ["max_hits", "any_2plus", "any_3plus", "any_4plus", "any_5plus", "any_6", "winning_union_coverage", "ticket_union_size", "mean_pair_overlap", "max_pair_overlap"]
    avg = lambda arr, k: statistics.mean(float(x[k]) for x in arr)
    return {
        "targets": len(policy),
        "random_bundles_per_target": RANDOM_BUNDLES_PER_TARGET,
        "policy": {k: avg(policy, k) for k in keys},
        "matched_uniform_random": {k: avg(random_rows, k) for k in keys},
        "delta_policy_minus_random": {k: avg(policy, k) - avg(random_rows, k) for k in keys},
    }


def validate(tickets):
    return (
        len(tickets) == 5
        and len({tuple(t) for t in tickets}) == 5
        and all(len(t) == 6 and len(set(t)) == 6 and t == sorted(t) and all(isinstance(n, int) and 1 <= n <= 45 for n in t) for t in tickets)
    )


def full_protocol_gate(date, run_dir):
    audit_path = run_dir / "PROTOCOL_AUDIT.json"
    vpath = run_dir / "VERIFICATION.json"
    if not audit_path.exists() or not vpath.exists():
        raise RuntimeError("protocol audit evidence missing")
    audit = json.loads(audit_path.read_text(encoding="utf-8-sig"))
    v = json.loads(vpath.read_text(encoding="utf-8-sig"))
    if audit.get("protocol_status") != "FULL_COMPLETE" or v.get("protocol_status") != "FULL_COMPLETE":
        raise RuntimeError(f"weekly output blocked: protocol_status={audit.get('protocol_status')}/{v.get('protocol_status')}")
    required = {
        "full_compute_execution",
        "external_two_source_crosscheck",
        "historical_errornote_aggregate_present",
        "historical_errornote_closed_loop_complete",
        "full_signal_scorecard",
        "numeric_13_section_report",
    }
    checks = audit.get("protocol_checks", {})
    if not required.issubset(checks) or not all(checks[k] for k in required):
        raise RuntimeError(f"weekly output blocked: failed protocol checks {checks}")
    return audit, v


def main():
    date = sys.argv[1] if len(sys.argv) > 1 else datetime.now(KST).date().isoformat()
    run_dir = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else max((ROOT / "analysis" / date).glob("MASTER_FULL_V5_*"), key=lambda p: p.stat().st_mtime)
    audit, verification = full_protocol_gate(date, run_dir)
    rows = load()
    cutoff = rows[-1][0]
    target = cutoff + 1
    if int(verification.get("data_cutoff", -1)) != cutoff:
        raise RuntimeError("audit/data cutoff mismatch")

    tickets, sources, structural, candidate_count = select(rows)
    assert validate(tickets)
    validator_1 = "PASS"
    bt = backtest(rows)
    assert validate(tickets)
    validator_2 = "PASS"

    display = "\n".join(" ".join(map(str, t)) for t in tickets)
    parsed = [[int(x) for x in line.split()] for line in display.splitlines()]
    assert parsed == tickets and validate(parsed)

    payload = {
        "target_round": target,
        "created_kst": datetime.now(KST).isoformat(),
        "data_cutoff": cutoff,
        "data_sha256": hashlib.sha256(DATA.read_bytes()).hexdigest(),
        "policy_version": POLICY,
        "classification": "PRIMARY_WEEKLY_PURCHASE_POLICY_PROTOCOL_FULL",
        "protocol_status": audit["protocol_status"],
        "protocol_checks": audit["protocol_checks"],
        "protocol_run_dir": str(run_dir.relative_to(ROOT)),
        "candidate_pool_size": candidate_count,
        "selection_sources": sources,
        "final_lines": tickets,
        "portfolio": {
            "unique_number_coverage": structural["ticket_union_size"],
            "pairwise_overlaps": structural["pairwise_overlaps"],
            "mean_pair_overlap": structural["mean_pair_overlap"],
            "max_pair_overlap": structural["max_pair_overlap"],
            "numbers_reused_3plus": structural["numbers_reused_3plus"],
            "total_reuse_beyond_two": structural["total_reuse_beyond_two"],
        },
        "historical_matched_random_backtest": bt,
        "integrity": {
            "validator_1": validator_1,
            "validator_2": validator_2,
            "final_text_parse": "PASS",
            "line_count": 5,
            "numbers_per_line": 6,
            "range_1_45": "PASS",
            "within_line_unique": "PASS",
            "duplicate_ticket": "PASS",
            "stored_vs_display": None,
        },
        "v2_change_note": "The five tickets are selected jointly from a predeclared multi-signal candidate pool. Compared with V1, the objective increases reward for union coverage and adds explicit penalties for number reuse beyond two appearances and excessive pairwise overlap. No missed 1246 winning number is manually forced into 1247.",
        "freeze_payload_sha256": None,
    }
    canon = json.dumps({k: v for k, v in payload.items() if k != "freeze_payload_sha256"}, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    payload["freeze_payload_sha256"] = hashlib.sha256(canon).hexdigest()

    outdir = OUTROOT / str(target)
    outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / f"FINAL_FIVE_LINES_{target}_{date.replace('-', '')}_PROTOCOL_FULL_V2.json"
    if out.exists():
        existing = json.loads(out.read_text(encoding="utf-8-sig"))
        if existing.get("final_lines") != tickets or existing.get("freeze_payload_sha256") != payload["freeze_payload_sha256"]:
            raise RuntimeError(f"write-once collision with different payload: {out}")
    else:
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    stored = json.loads(out.read_text(encoding="utf-8-sig"))
    assert stored["final_lines"] == parsed == tickets
    assert validate(stored["final_lines"])
    stored["integrity"]["stored_vs_display"] = "PASS"
    # Do not rewrite after freeze. The terminal PASS is established by this reread.
    print(json.dumps({
        "status": "PASS",
        "protocol_status": audit["protocol_status"],
        "target": target,
        "cutoff": cutoff,
        "policy": POLICY,
        "final_lines": tickets,
        "portfolio_unique_coverage": structural["ticket_union_size"],
        "portfolio_max_overlap": structural["max_pair_overlap"],
        "validator_1": validator_1,
        "validator_2": validator_2,
        "final_text_parse": "PASS",
        "stored_vs_display": "PASS",
        "output": str(out),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
