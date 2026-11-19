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


def _purchase_provenance_checks(hist):
    reviews = hist.get("reviews", [])
    confirmed_by_path = {
        item.get("source_path"): item
        for item in hist.get("confirmed_purchase_sources", [])
        if item.get("source_path")
    }
    unconfirmed_paths = {
        source.get("path")
        for target in hist.get("unconfirmed_preserved_line_sources", [])
        for source in target.get("sources", [])
        if source.get("path")
    }
    mismatches = []
    for review in reviews:
        source = review.get("source")
        confirmation = confirmed_by_path.get(source)
        if (
            review.get("source_role") != "ACTUAL_PURCHASE_CONFIRMED"
            or confirmation is None
            or review.get("source_sha256") != confirmation.get("source_sha256")
        ):
            mismatches.append({
                "target_round": review.get("target_round"),
                "source": source,
                "reason": "review_source_not_backed_by_matching_confirmation_registry_entry",
            })
    reviewed_paths = {review.get("source") for review in reviews}
    return {
        "source_is_canonical": not mismatches,
        "confirmation_evidence_available": bool(reviews) and not mismatches,
        "unconfirmed_sources_excluded": not bool(reviewed_paths & unconfirmed_paths),
        "source_mismatches": mismatches,
        "unconfirmed_source_count": len(unconfirmed_paths),
    }


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
    purchase = _purchase_provenance_checks(hist)

    expected_rows = len(recall.get("signals", [])) * len(recall.get("k_values", []))
    row_ks = {int(row["k"]) for row in score_rows} if score_rows else set()
    score_targets = {int(row["targets"]) for row in score_rows} if score_rows else set()

    source_conflicts = hist.get("unresolved_source_conflicts", [])
    reviewed_targets = {int(review["target_round"]) for review in reviews}
    conflict_targets = set()
    conflict_records_valid = isinstance(source_conflicts, list)
    for conflict in source_conflicts if isinstance(source_conflicts, list) else []:
        try:
            target = int(conflict["target_round"])
            sources = conflict.get("sources", [])
            valid_conflict = (
                conflict.get("status") == "EXCLUDED_UNRESOLVED"
                and target not in reviewed_targets
                and len(sources) >= 2
                and conflict.get("receipt_evidence") == "NOT_FOUND"
                and conflict.get("aggregate_action") == "EXCLUDED_FROM_SINGLE_CANONICAL_AGGREGATE"
            )
            conflict_records_valid = conflict_records_valid and valid_conflict
            conflict_targets.add(target)
        except (KeyError, TypeError, ValueError):
            conflict_records_valid = False

    checks = {
        "actual_purchase_precedence": hist.get("actual_purchase_precedence") is True,
        "actual_purchase_source_is_canonical": purchase["source_is_canonical"],
        "actual_purchase_confirmation_evidence_available": purchase["confirmation_evidence_available"],
        "unconfirmed_purchase_sources_excluded": purchase["unconfirmed_sources_excluded"],
        "latest_review_has_failure_decomposition": (
            bool(latest)
            and "candidate_recall_failure" in latest
            and "ticket_construction_gap" in latest
            and "source_role" in latest
        ),
        "all_reviews_have_failure_decomposition": bool(reviews) and all(
            "candidate_recall_failure" in review
            and "ticket_construction_gap" in review
            and "source_role" in review
            for review in reviews
        ),
        "candidate_recall_status_present": bool(recall),
        "candidate_recall_cutoff_matches_master": int(recall.get("data_cutoff", -2)) == cutoff,
        "candidate_recall_no_future_leakage": recall.get("no_future_leakage") is True,
        "candidate_recall_required_k": set(map(int, recall.get("k_values", []))) == KS,
        "candidate_recall_scorecard_complete": bool(score_rows) and len(score_rows) == expected_rows and row_ks == KS,
        "candidate_recall_targets_consistent": len(score_targets) == 1 and next(iter(score_targets), -1) == int(recall.get("targets", -2)),
        "candidate_recall_matched_random_run": int(recall.get("matched_random_sets_total", 0)) > 0,
        "whole_history_not_overstated": hist.get("whole_history_complete") is False,
        "historical_source_conflicts_disclosed_and_excluded": (
            conflict_records_valid
            and (not conflict_targets or hist.get("closed_loop_complete") is False)
        ),
    }

    # Absence of confirmed purchases is an evidence limitation, not an integrity failure.
    # It remains a protocol gap so DAILY MASTER cannot become FULL_COMPLETE.
    evidence_only_checks = {
        "actual_purchase_confirmation_evidence_available",
        "latest_review_has_failure_decomposition",
        "all_reviews_have_failure_decomposition",
    }
    gate_ok = all(value for key, value in checks.items() if key not in evidence_only_checks)

    best_by_k = {}
    for k in sorted(KS):
        rows = [row for row in score_rows if int(row["k"]) == k]
        if rows:
            best = max(rows, key=lambda row: float(row["delta_recall_vs_random"]))
            best_by_k[str(k)] = {
                "signal": best["signal"],
                "mean_recall": float(best["mean_recall"]),
                "random_mean_recall": float(best["random_mean_recall"]),
                "delta_recall_vs_random": float(best["delta_recall_vs_random"]),
                "delta_3plus_vs_random": float(best.get("delta_3plus_vs_random", 0.0) or 0.0),
                "delta_4plus_vs_random": float(best.get("delta_4plus_vs_random", 0.0) or 0.0),
            }

    gate = {
        "date": date,
        "status": "PASS" if gate_ok else "FAIL",
        "evidence_status": hist.get("purchase_confirmation_status", "UNSPECIFIED"),
        "actual_purchase_learning_status": (
            "AVAILABLE" if purchase["confirmation_evidence_available"]
            else "NOT_AVAILABLE_NO_PURCHASE_CONFIRMATION"
        ),
        "data_cutoff": cutoff,
        "checks": checks,
        "actual_purchase_source_mismatches": purchase["source_mismatches"],
        "unconfirmed_preserved_source_count": purchase["unconfirmed_source_count"],
        "historical_preserved_scope_complete": bool(hist.get("closed_loop_complete")),
        "unresolved_source_conflicts": source_conflicts,
        "excluded_conflict_rounds": sorted(conflict_targets),
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
        "policy": (
            "Only explicitly user-confirmed or receipt-backed purchased lines are canonical "
            "for post-draw learning. Filenames and preserved pre-draw recommendations do not prove purchase. "
            "Candidate recall and ticket construction remain separate stages."
        ),
    }
    gate_path = dated / "LEARNING_LOOP_GATE.json"
    gate_path.write_text(json.dumps(gate, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    purchase_learning_available = (
        purchase["confirmation_evidence_available"]
        and purchase["source_is_canonical"]
    )
    failure_decomposition_available = (
        bool(reviews) and checks["all_reviews_have_failure_decomposition"]
    )
    audit.setdefault("protocol_checks", {}).update({
        "actual_purchase_learning_record": purchase_learning_available,
        "failure_decomposition_present": failure_decomposition_available,
        "historical_source_conflicts_disclosed_and_excluded": checks["historical_source_conflicts_disclosed_and_excluded"],
        "candidate_recall_separate_stage": all(
            checks[key] for key in (
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
        "\n### Learning-loop provenance correction\n"
        f"- Purchase-confirmed records available: {purchase['confirmation_evidence_available']}.\n"
        f"- Verified actual-purchase aggregate: {hist.get('verified_round_count')} rounds / {hist.get('verified_purchase_lines')} lines.\n"
        f"- Preserved line-set targets without purchase confirmation excluded: {len(hist.get('unconfirmed_preserved_line_sources', []))}.\n"
        f"- Purchase confirmation registry: {hist.get('purchase_confirmation_registry', {}).get('path')} ({hist.get('purchase_confirmation_registry', {}).get('status')}).\n"
        "- A filename beginning with ACTUAL_PURCHASE is not proof of purchase; only registry-backed evidence enters the aggregate.\n"
        f"- Unconfirmed/conflicted target rounds excluded: {sorted(conflict_targets)}.\n"
        f"- Whole historical recommendation archive complete: {hist.get('whole_history_complete')}.\n"
    )
    report += insert
    report_path.write_text(report, encoding="utf-8")

    print(json.dumps(gate, ensure_ascii=False))
    if not gate_ok:
        raise SystemExit(2)


if __name__ == "__main__":
    main()


