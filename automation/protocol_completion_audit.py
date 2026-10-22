#!/usr/bin/env python3
"""Post-run audit for the user's full LOTTO_PROJECT_PROTOCOL.

This deliberately separates computational execution from protocol completeness.
A run may be computationally complete while the overall daily study remains
PROTOCOL_PARTIAL because provenance, source cross-checks, or requested signal
scorecards are incomplete.

No candidate/recommendation/final lotto lines are generated or printed.
"""
import csv
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

COMPUTE_REQUIRED = {
    "latest_data_integrity",
    "fresh_cumulative_stats",
    "B_full_walkforward",
    "fresh_random_baseline",
    "historical_source_search",
    "A_full_walkforward",
    "C_full_walkforward",
    "contrarian_full_walkforward",
    "AC_contrarian_leakage",
    "successor_scorecard_complete",
    "successor_random_comparison",
    "successor_block_stability",
    "successor_signal_ablation",
    "five_ticket_portfolio_walkforward",
    "five_ticket_matched_random_baseline",
    "model_scorecard_complete",
    "hypothesis_registry_written",
}


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_csv(path):
    return list(csv.DictReader(path.open(encoding="utf-8-sig")))


def pct(x):
    return f"{100.0 * float(x):.3f}%"


def fmt(x, n=6):
    return f"{float(x):.{n}f}"


def find_row(rows, key, value):
    for r in rows:
        if r.get(key) == value:
            return r
    raise KeyError(f"{key}={value} not found")


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: protocol_completion_audit.py YYYY-MM-DD RUN_DIR")
    date = sys.argv[1]
    run_dir = Path(sys.argv[2]).resolve()
    dated = ROOT / "analysis" / date
    vpath = run_dir / "VERIFICATION.json"
    v = load_json(vpath)

    missing_compute_keys = sorted(COMPUTE_REQUIRED - set(v.get("mandatory_checks", {})))
    failed_compute_keys = sorted(
        k for k in COMPUTE_REQUIRED
        if not v.get("mandatory_checks", {}).get(k, False)
    )
    compute_ok = not missing_compute_keys and not failed_compute_keys

    ext_path = dated / "EXTERNAL_DATA_CROSSCHECK.json"
    ext = load_json(ext_path) if ext_path.exists() else {}
    fallback_sources = ext.get("fallback_sources", [])
    external_ok = bool(
        ext
        and len(fallback_sources) >= 2
        and ext.get("independent_fallback_sources_agree") is True
        and ext.get("repo_vs_fallback_round_and_date_match") is True
        and int(ext.get("repo_data_cutoff", -1)) == int(v.get("data_cutoff", -2))
    )

    hist_path = dated / "HISTORICAL_CLOSED_LOOP_STATUS.json"
    hist = load_json(hist_path) if hist_path.exists() else {}
    historical_aggregate_present = bool(
        hist
        and int(hist.get("verified_round_count", 0)) > 0
        and int(hist.get("verified_purchase_lines", 0)) > 0
        and sum(int(x) for x in hist.get("aggregate_hit_distribution", {}).values())
        == int(hist.get("verified_purchase_lines", -1))
    )
    historical_closed_loop_ok = bool(hist.get("closed_loop_complete") is True)

    signal_path = dated / "FULL_SIGNAL_SCORECARD_STATUS.json"
    sig = load_json(signal_path) if signal_path.exists() else {}
    full_signal_ok = bool(sig.get("full_signal_scorecard_complete") is True)

    base = ROOT / v["base_v4"]
    successor = load_csv(run_dir / "AC_CONTRARIAN_SCORECARD.csv")
    b_rows = load_csv(base / "B_MODEL_SCORECARD.csv")
    structures = load_csv(base / "STRUCTURE_WINDOWS.csv")
    long_recent = load_csv(base / "LONG_RECENT_CATEGORIES.csv")
    num_rows = load_csv(base / "NUMBER_FULL_STATS.csv")
    portfolio = load_json(run_dir / "FIVE_TICKET_PORTFOLIO_SCORECARD.json")
    run_summary = load_json(base / "RUN_SUMMARY.json")

    a = find_row(successor, "model", "A_v2")
    c = find_row(successor, "model", "C_v2")
    contra = find_row(successor, "model", "contrarian_v2")
    b_combined = find_row(b_rows, "model", "combined_equal_rank")
    b_pair = find_row(b_rows, "model", "pair_association")
    b_triple = find_row(b_rows, "model", "triple_association")
    full_struct = find_row(structures, "window", "full")

    counts = [int(r["count"]) for r in num_rows]
    current_gaps = [int(r["current_gap"]) for r in num_rows]
    historical_gaps = [int(r["historical_max_gap"]) for r in num_rows]
    lr = {r["window"]: r for r in long_recent}

    odd_dist = json.loads(full_struct["odd_distribution"])
    consecutive_dist = json.loads(full_struct["consecutive_adj_distribution"])
    ending_dist = json.loads(full_struct["repeated_ending_classes"])
    concentration = json.loads(full_struct["range_concentration"])
    draws = int(full_struct["draws"])
    has_consecutive = 1 - int(consecutive_dist.get("0", 0)) / draws
    has_repeated_ending = 1 - int(ending_dist.get("0", 0)) / draws
    concentrated_3plus = sum(int(vv) for kk, vv in concentration.items() if int(kk) >= 3) / draws

    protocol_checks = {
        "full_compute_execution": compute_ok,
        "external_two_source_crosscheck": external_ok,
        "historical_errornote_aggregate_present": historical_aggregate_present,
        "historical_errornote_closed_loop_complete": historical_closed_loop_ok,
        "full_signal_scorecard": full_signal_ok,
        "numeric_13_section_report": True,
    }
    protocol_complete = all(protocol_checks.values())
    compute_status = "FULL_COMPUTE_COMPLETE" if compute_ok else "COMPUTE_PARTIAL"
    protocol_status = "FULL_COMPLETE" if protocol_complete else "PROTOCOL_PARTIAL"

    report = f"""# DAILY MASTER protocol audit — {date}

Overall protocol status: **{protocol_status}**  
Compute status: **{compute_status}**

## 1. 오늘 데이터 기준/원자료 확보·검증/전일 대비 추가회차
- Data cutoff: {v.get('data_cutoff')}.
- Core integrity gate: {v.get('mandatory_checks', {}).get('latest_data_integrity')}.
- External independent fallback sources checked: {len(fallback_sources)}; agreement={external_ok}.
- Official source attempt state is preserved separately in `EXTERNAL_DATA_CROSSCHECK.json` rather than silently replaced.

## 2. 오늘 실제 새로 계산한 핵심 발견 3~7개
- A_v2 mean hits {fmt(a['mean_hits'])}; matched-random delta {fmt(a['delta_mean'])}.
- C_v2 mean hits {fmt(c['mean_hits'])}; matched-random delta {fmt(c['delta_mean'])}.
- Contrarian_v2 mean hits {fmt(contra['mean_hits'])}; matched-random delta {fmt(contra['delta_mean'])}.
- B combined mean hits {fmt(b_combined['mean_hits'])}; matched-random delta {fmt(b_combined['delta_mean'])}.
- B pair mean delta {fmt(b_pair['delta_mean'])}; B triple mean delta {fmt(b_triple['delta_mean'])}; multiple-testing survivors remain pair={run_summary['pair']['q_lt_0_05']}, triple={run_summary['triple']['q_lt_0_05']}.
- Research-only five-ticket policy any-2+ delta vs matched random: {fmt(portfolio['any_ge2']['delta'])}; union-coverage delta {fmt(portfolio['winning_union_coverage']['delta'])}; it is not promoted to weekly policy.

## 3. 전체 누적 번호 분석
- Number appearance counts across 1–45: min {min(counts)}, max {max(counts)}, spread {max(counts)-min(counts)} over {draws} draws.
- This section reports aggregate distribution only; daily output does not print candidate identities.

## 4. 장기 vs 10/30/50/100 비교표
| window | long-strong/recent-weak | long-weak/recent-strong |
|---:|---:|---:|
| 10 | {lr['10']['long_strong_recent_weak']} | {lr['10']['long_weak_recent_strong']} |
| 30 | {lr['30']['long_strong_recent_weak']} | {lr['30']['long_weak_recent_strong']} |
| 50 | {lr['50']['long_strong_recent_weak']} | {lr['50']['long_weak_recent_strong']} |
| 100 | {lr['100']['long_strong_recent_weak']} | {lr['100']['long_weak_recent_strong']} |

## 5. 간격·미출현
- Current-gap maximum: {max(current_gaps)} draws.
- Historical maximum gap found in the dataset: {max(historical_gaps)} draws.
- Gap is therefore kept as a tested signal, not promoted from current extremeness alone.

## 6. 구조·관계
- Full-history mean sum: {fmt(full_struct['sum_mean'], 3)}.
- At least one consecutive adjacency: {pct(has_consecutive)}.
- At least one repeated ending class: {pct(has_repeated_ending)}.
- 3+ numbers concentrated in one configured range: {pct(concentrated_3plus)}.
- Mean previous-draw overlap: {fmt(full_struct['previous_overlap_mean'], 3)}.
- Pair universe {run_summary['pair']['universe']}, q<.05 survivors {run_summary['pair']['q_lt_0_05']}; triple universe {run_summary['triple']['universe']}, survivors {run_summary['triple']['q_lt_0_05']}.

## 7. A 모델
- n={a['n']}; mean={fmt(a['mean_hits'])}; variance={fmt(a['variance'])}; random={fmt(a['random_mean_same_targets'])}; delta={fmt(a['delta_mean'])}.
- 2+={pct(a['rate_ge2'])}, 3+={pct(a['rate_ge3'])}, 4+={pct(a['rate_ge4'])}, 5+={pct(a['rate_ge5'])}, 6={pct(a['rate_ge6'])}.

## 8. B 실제 백테스트 + 랜덤 기준
- targets={run_summary['B']['targets']}; prediction records={run_summary['B']['prediction_records']}; random tickets={run_summary['B']['random_tickets']}; leakage failures={run_summary['B']['leakage_failures']}.
- Combined delta vs random={fmt(b_combined['delta_mean'])}; pair delta={fmt(b_pair['delta_mean'])}; triple delta={fmt(b_triple['delta_mean'])}.

## 9. C 모델
- n={c['n']}; mean={fmt(c['mean_hits'])}; variance={fmt(c['variance'])}; random={fmt(c['random_mean_same_targets'])}; delta={fmt(c['delta_mean'])}.
- 2+={pct(c['rate_ge2'])}, 3+={pct(c['rate_ge3'])}, 4+={pct(c['rate_ge4'])}, 5+={pct(c['rate_ge5'])}, 6={pct(c['rate_ge6'])}.

## 10. 역발상
- n={contra['n']}; mean={fmt(contra['mean_hits'])}; variance={fmt(contra['variance'])}; random={fmt(contra['random_mean_same_targets'])}; delta={fmt(contra['delta_mean'])}.
- 2+={pct(contra['rate_ge2'])}, 3+={pct(contra['rate_ge3'])}, 4+={pct(contra['rate_ge4'])}, 5+={pct(contra['rate_ge5'])}, 6={pct(contra['rate_ge6'])}.

## 11. 누적 추천·오답노트
- Verified authentic/recoverable review rounds currently aggregated: {hist.get('verified_round_count', 0)}.
- Verified purchase lines: {hist.get('verified_purchase_lines', 0)}; mean main hits/line={hist.get('mean_main_hits_per_line', 'NA')}.
- 2+ rate={hist.get('rate_ge2', 'NA')}; 3+={hist.get('rate_ge3', 'NA')}; 4+={hist.get('rate_ge4', 'NA')}.
- Closed-loop provenance complete={historical_closed_loop_ok}. Missing older originals and incomplete per-winning-number exclusion reasons are not reconstructed.

## 12. 이전 가설 재검증
- Pair/triple remain `MORE_TEST`: their B mean deltas can be positive while multiple-testing survivors are zero.
- The research-only five-ticket diversity diagnostic remains unpromoted because its any-2+, any-3+, union coverage and redundancy metrics do not justify promotion against matched random.
- No weight is changed automatically from one ablation run.

## 13. 데이터 한계/미계산 항목
- External source cross-check complete: {external_ok}.
- Historical closed-loop fully complete: {historical_closed_loop_ok}.
- Full per-dimension signal scorecard complete: {full_signal_ok}.
- Structural dimensions still not individually isolated in cutoff-safe contribution tests: {', '.join(sig.get('partially_covered_inside_structure_profile_but_not_isolated', [])) or 'none'}.
- Therefore overall daily study status is **{protocol_status}**, not FULL_COMPLETE, unless every protocol gate becomes true.

No candidate/recommendation/final lines were generated by this audit.
"""
    report_path = run_dir / "PROTOCOL_AUDIT_13_SECTION.md"
    report_path.write_text(report, encoding="utf-8")

    v["compute_status"] = compute_status
    v["protocol_status"] = protocol_status
    v["status"] = protocol_status
    v["protocol_checks"] = protocol_checks
    v["protocol_missing"] = [k for k, ok in protocol_checks.items() if not ok]
    v["protocol_evidence"] = {
        "external_crosscheck": str(ext_path.relative_to(ROOT)) if ext_path.exists() else None,
        "historical_closed_loop": str(hist_path.relative_to(ROOT)) if hist_path.exists() else None,
        "full_signal_scorecard": str(signal_path.relative_to(ROOT)) if signal_path.exists() else None,
        "numeric_report": str(report_path.relative_to(ROOT)),
    }
    vpath.write_text(json.dumps(v, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    audit = {
        "date": date,
        "compute_status": compute_status,
        "protocol_status": protocol_status,
        "protocol_checks": protocol_checks,
        "missing_compute_keys": missing_compute_keys,
        "failed_compute_keys": failed_compute_keys,
        "protocol_missing": v["protocol_missing"],
    }
    (run_dir / "PROTOCOL_AUDIT.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(audit, ensure_ascii=False))
    if not compute_ok:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
