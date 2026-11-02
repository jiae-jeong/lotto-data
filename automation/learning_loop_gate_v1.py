#!/usr/bin/env python3
"""Enforce the learning-loop invariants required by the lotto research protocol.

This gate runs after the normal protocol recovery/audit. It does not generate
purchase numbers. It verifies that the daily study learns from the lines that
were actually delivered/purchased and that candidate recall is measured
separately from ticket construction.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KS = {10, 15, 20, 25, 30}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: learning_loop_gate_v1.py YYYY-MM-DD RUN_DIR")
    date = sys.argv[1]
    run_dir = Path(sys.argv[2]).resolve()
    dated = ROOT / "analysis" / date

    hist_path = dated / "HISTORICAL_CLOSED_LOOP_STATUS.json"
    recall_status_path = dated / "CANDIDATE_RECALL_STATUS.json"
    recall_score_path = dated / "CANDIDATE_RECALL_SCORECARD.csv"
    audit_path = run_dir / "PROTOCOL_AUDIT.json"
    verification_path = run_dir / "VERIFICATION.json"
    report_path = run_dir / "PROTOCOL_AUDIT_13_SECTION.md"

    required_paths = [hist_path, recall_status_path, recall_score_path, audit_path, verification_path, report_path]
    missing = [str(p.relative_to(ROOT)) for p in required_paths if not p.exists()]
    if missing:
        print(json.dumps({"status": "FAIL", "missing": missing}, ensure_ascii=False))
        raise SystemExit(2)

    hist = load_json(hist_path)
    recall = load_json(recall_status_path)
    audit = load_json(audit_path)
    verification = load_json(verification_path)
    score_rows = list(csv.DictReader(recall_score_path.open(encoding="utf-8-sig")))

    reviews = hist.get("reviews", [])
    latest = reviews[-1] if reviews else {}
    cutoff = int(verification.get("data_cutoff", -1))

    expected_rows = len(recall.get("signals", [])) * len(recall.get("k_values", []))
    row_ks = {int(r["k"]) for r in score_rows} if score_rows else set()
    score_targets = {int(r["targets"]) for r in score_rows} if score_rows else set()

    checks = {
        "actual_purchase_precedence": hist.get("actual_purchase_precedence") is True,
        "latest_review_has_failure_decomposition": (
            bool(latest)
            and "candidate_recall_failure" in latest
            and "ticket_construction_gap" in latest
            and "source_role" in latest
        ),
        "candidate_recall_status_present": bool(recall),
        "candidate_recall_cutoff_matches_master": int(recall.get("data_cutoff", -2)) == cutoff,
        "candidate_recall_no_future_leakage": recall.get("no_future_leakage") is True,
        "candidate_recall_required_k": set(map(int, recall.get("k_values", []))) == KS,
        "candidate_recall_scorecard_complete": bool(score_rows) and len(score_rows) == expected_rows and row_ks == KS,
        "candidate_recall_targets_consistent": len(score_targets) == 1 and next(iter(score_targets), -1) == int(recall.get("targets", -2)),
        "candidate_recall_matched_random_run": int(recall.get("matched_random_sets_total", 0)) > 0,
        "whole_history_not_overstated": hist.get("whole_history_complete") is False,
    }

    # Verify that if an ACTUAL_PURCHASE artifact exists for the latest completed
    # round, the closed-loop source actually uses it rather than a later research artifact.
    actual_purchase_source_ok = True
    if latest:
        target = int(latest["target_round"])
        actuals = sorted((ROOT / "research" / "weekly_purchase" / str(target)).glob("ACTUAL_PURCHASE_FIVE_LINES*.json"))
        if actuals:
            actual_purchase_source_ok = latest.get("source_role") == "ACTUAL_PURCHASE" and str(latest.get("source", "")).startswith(
                f"research/weekly_purchase/{target}/ACTUAL_PURCHASE_FIVE_LINES"
            )
    checks["actual_purchase_source_is_canonical"] = actual_purchase_source_ok

    # Candidate recall summary contains no candidate identities.
    best_by_k = {}
    for k in sorted(KS):
        rows = [r for r in score_rows if int(r["k"]) == k]
        if rows:
            best = max(rows, key=lambda r: float(r["delta_recall_vs_random"]))
            best_by_k[str(k)] = {
                "signal": best["signal"],
                "mean_recall": float(best["mean_recall"]),
                "random_mean_recall": float(best["random_mean_recall"]),
                "delta_recall_vs_random": float(best["delta_recall_vs_random"]),
            }

    gate_ok = all(checks.values())
    gate = {
        "date": date,
        "status": "PASS" if gate_ok else "FAIL",
        "data_cutoff": cutoff,
        "checks": checks,
        "historical_preserved_scope_complete": bool(hist.get("closed_loop_complete")),
        "whole_history_complete": bool(hist.get("whole_history_complete")),
        "latest_review": {
            "target_round": latest.get("target_round"),
            "source": latest.get("source"),
            "source_role": latest.get("source_role"),
            "candidate_recall_failure": latest.get("candidate_recall_failure"),
            "ticket_construction_gap": latest.get("ticket_construction_gap"),
            "winning_union_coverage": latest.get("winning_union_coverage"),
            "max_hits": latest.get("max_hits"),
        },
        "candidate_recall": {
            "targets": recall.get("targets"),
            "matched_random_sets_total": recall.get("matched_random_sets_total"),
            "best_delta_by_k": best_by_k,
        },
        "policy": "Candidate recall and ticket construction are separate learning stages. Actual delivered/purchased lines are canonical for post-draw learning.",
    }
    gate_path = dated / "LEARNING_LOOP_GATE.json"
    gate_path.write_text(json.dumps(gate, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Strengthen the existing protocol audit without pretending missing legacy
    # recommendation history has been recovered.
    audit.setdefault("protocol_checks", {}).update({
        "actual_purchase_learning_record": checks["actual_purchase_precedence"] and checks["actual_purchase_source_is_canonical"],
        "candidate_recall_separate_stage": all(
            checks[k] for k in (
                "candidate_recall_status_present",
                "candidate_recall_cutoff_matches_master",
                "candidate_recall_no_future_leakage",
                "candidate_recall_required_k",
                "candidate_recall_scorecard_complete",
                "candidate_recall_targets_consistent",
                "candidate_recall_matched_random_run",
            )
        ),
        "whole_history_limitation_explicit": checks["whole_history_not_overstated"],
    })
    audit["learning_loop_gate"] = str(gate_path.relative_to(ROOT))
    if not all(audit["protocol_checks"].values()):
        audit["protocol_status"] = "PROTOCOL_PARTIAL"
    audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    verification.setdefault("protocol_checks", {}).update(audit["protocol_checks"])
    verification["learning_loop_gate"] = str(gate_path.relative_to(ROOT))
    if audit["protocol_status"] != "FULL_COMPLETE":
        verification["protocol_status"] = "PROTOCOL_PARTIAL"
        verification["status"] = "PROTOCOL_PARTIAL"
    verification_path.write_text(json.dumps(verification, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report = report_path.read_text(encoding="utf-8")
    report = report.replace(
        f"- Historical closed-loop fully complete: {hist.get('closed_loop_complete') }.",
        f"- Preserved weekly-purchase scope complete: {hist.get('closed_loop_complete')}; whole historical recommendation archive complete: {hist.get('whole_history_complete')}."
    )
    insert = (
        "\n### Learning-loop correction\n"
        f"- Actual delivered/purchase artifact precedence: {checks['actual_purchase_source_is_canonical']}.\n"
        f"- Candidate recall is measured separately at K=10/15/20/25/30 over {recall.get('targets')} cutoff-safe targets, with {recall.get('matched_random_sets_total')} matched-random candidate sets.\n"
        f"- Latest preserved review failure split: candidate_recall_failure={latest.get('candidate_recall_failure')}; ticket_construction_gap={latest.get('ticket_construction_gap')}.\n"
        f"- Whole historical recommendation archive complete: {hist.get('whole_history_complete')} (legacy/missing originals are not reconstructed).\n"
    )
    report += insert
    report_path.write_text(report, encoding="utf-8")

    print(json.dumps(gate, ensure_ascii=False))
    if not gate_ok:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
