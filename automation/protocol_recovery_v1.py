#!/usr/bin/env python3
"""Recover protocol evidence from explicitly confirmed purchases and cutoff-safe tests.

This script does not generate a purchase recommendation. Preserved filenames, displayed
recommendations, and pre-draw FINAL artifacts are not proof of purchase. Only sources
listed in PURCHASE_CONFIRMATION_REGISTRY.json with a valid source hash and explicit
receipt or user-confirmation evidence enter the actual-purchase aggregate.
"""
from __future__ import annotations

import csv
import hashlib
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
        return "PRESERVED_PURCHASE_NAMED_NOT_CONFIRMED"
    if name.startswith("FINAL_FIVE_LINES"):
        return "PRESERVED_FINAL_PREDRAW_NOT_CONFIRMED"
    return "OTHER"


def _candidate_paths():
    base = ROOT / "research" / "weekly_purchase"
    found = set(base.glob("*/ACTUAL_PURCHASE_FIVE_LINES*.json"))
    found.update(base.glob("*/FINAL_FIVE_LINES*.json"))
    return sorted(found)


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _normalize_five_lines(value):
    if not isinstance(value, list) or len(value) != 5:
        return None
    normalized = []
    for line in value:
        if (
            not isinstance(line, list)
            or len(line) != 6
            or any(not isinstance(n, int) or not 1 <= n <= 45 for n in line)
            or len(set(line)) != 6
        ):
            return None
        normalized.append(tuple(sorted(line)))
    return tuple(normalized)


def _load_purchase_confirmation_registry():
    path = ROOT / "research" / "PURCHASE_CONFIRMATION_REGISTRY.json"
    if not path.is_file():
        return {"schema_version": 1, "confirmed_purchases": []}, "MISSING"
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if payload.get("schema_version") != 1 or not isinstance(payload.get("confirmed_purchases"), list):
        raise ValueError("unsupported purchase confirmation registry schema")
    return payload, ("PRESENT_WITH_ENTRIES" if payload["confirmed_purchases"] else "PRESENT_EMPTY")


def _prospective_first_prize_sources(target):
    base = ROOT / "research" / "prospective_v4" / "decisions" / str(target)
    found = []
    for path in sorted(base.glob("FIRST_PRIZE_PURCHASE_*_V*.json")):
        try:
            obj = json.loads(path.read_text(encoding="utf-8-sig"))
            if int(obj.get("target_round", path.parent.name)) != target:
                continue
            if obj.get("supersedes_purchase_only_v1_for_actual_purchase") is not True:
                continue
            lines = _normalize_five_lines(obj.get("actual_purchase_final_5"))
            if lines is None:
                continue
            found.append({
                "path": str(path.relative_to(ROOT)),
                "role": "FIRST_PRIZE_PRE_DRAW_PURCHASE_DESIGN",
                "line_set": [list(line) for line in lines],
                "source_sha256": _sha256_file(path),
            })
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            continue
    return found


def build_historical_closed_loop(rows, dated):
    by_round = {r["round"]: r for r in rows}
    cutoff = rows[-1]["round"]
    candidates = []
    invalid = []
    for path in _candidate_paths():
        try:
            obj = json.loads(path.read_text(encoding="utf-8-sig"))
            target = int(obj.get("target_round", path.parent.name))
            if target > cutoff:
                continue
            lines = _normalize_five_lines(obj.get("final_lines"))
            if lines is None:
                invalid.append({
                    "path": str(path.relative_to(ROOT)),
                    "target": target,
                    "reason": "invalid_or_missing_five_line_payload",
                })
                continue
            candidates.append({
                "path": str(path.relative_to(ROOT)),
                "path_abs": path,
                "target": target,
                "obj": obj,
                "role": _artifact_role(path),
                "lines": lines,
                "source_sha256": _sha256_file(path),
            })
        except Exception as exc:
            invalid.append({
                "path": str(path.relative_to(ROOT)),
                "valid": False,
                "reason": f"parse:{exc}",
            })

    grouped = {}
    candidate_by_path = {}
    for candidate in candidates:
        grouped.setdefault(candidate["target"], []).append(candidate)
        candidate_by_path[candidate["path"]] = candidate

    registry_path = ROOT / "research" / "PURCHASE_CONFIRMATION_REGISTRY.json"
    try:
        registry, registry_status = _load_purchase_confirmation_registry()
    except Exception as exc:
        registry = {"schema_version": 1, "confirmed_purchases": []}
        registry_status = "INVALID"
        invalid.append({
            "path": str(registry_path.relative_to(ROOT)),
            "reason": f"purchase_confirmation_registry_invalid:{exc}",
        })

    confirmed_by_target = {}
    ambiguous_registry_targets = set()
    for index, entry in enumerate(registry.get("confirmed_purchases", [])):
        if not isinstance(entry, dict):
            invalid.append({"registry_entry": index, "reason": "entry_not_object"})
            continue
        if entry.get("confirmation_status") != "CONFIRMED":
            continue
        try:
            target = int(entry["target_round"])
            source_path = str(entry["source_path"])
            source_sha256 = str(entry["source_sha256"]).lower()
            evidence_type = str(entry["evidence_type"]).upper()
            evidence_reference = str(entry["evidence_reference"]).strip()
            if not evidence_reference:
                raise ValueError("missing_evidence_reference")
            if evidence_type == "EXPLICIT_USER_CONFIRMATION":
                if entry.get("confirmed_by_user") is not True:
                    raise ValueError("explicit_confirmation_not_user_confirmed")
            elif evidence_type == "RECEIPT":
                ref_path = Path(evidence_reference)
                if ref_path.is_absolute() or ".." in ref_path.parts:
                    raise ValueError("unsafe_receipt_reference")
                receipt_path = ROOT / ref_path
                if not receipt_path.is_file() or receipt_path.is_symlink():
                    raise ValueError("receipt_evidence_file_missing")
            else:
                raise ValueError("unsupported_evidence_type")
            candidate = candidate_by_path.get(source_path)
            if candidate is None:
                raise ValueError("confirmed_source_not_in_preserved_purchase_candidates")
            if candidate["target"] != target:
                raise ValueError("confirmed_source_target_mismatch")
            if candidate["source_sha256"] != source_sha256:
                raise ValueError("confirmed_source_sha256_mismatch")
            if target > cutoff or target not in by_round:
                raise ValueError("confirmed_target_outside_verified_draw_data")
            if target in confirmed_by_target:
                ambiguous_registry_targets.add(target)
                confirmed_by_target.pop(target, None)
                raise ValueError("multiple_confirmed_sources_for_target")
            confirmed_by_target[target] = entry
        except (KeyError, TypeError, ValueError) as exc:
            try:
                bad_target = int(entry.get("target_round", -1))
                if bad_target >= 0:
                    ambiguous_registry_targets.add(bad_target)
                    confirmed_by_target.pop(bad_target, None)
            except (TypeError, ValueError):
                bad_target = None
            invalid.append({
                "registry_entry": index,
                "target_round": bad_target,
                "reason": str(exc),
            })

    reviews = []
    all_hits = []
    source_conflicts = []
    unconfirmed = []

    for target in sorted(grouped):
        entries = grouped[target]
        external_sources = _prospective_first_prize_sources(target)
        line_sources = []
        for candidate in entries:
            line_sources.append({
                "path": candidate["path"],
                "role": candidate["role"],
                "line_set": [list(line) for line in candidate["lines"]],
                "source_sha256": candidate["source_sha256"],
            })
        line_sources.extend(external_sources)

        confirmation = confirmed_by_target.get(target)
        if confirmation is None or target in ambiguous_registry_targets:
            distinct_sets = {
                tuple(tuple(line) for line in source["line_set"])
                for source in line_sources
            }
            unconfirmed_record = {
                "target_round": target,
                "status": "PURCHASE_NOT_CONFIRMED",
                "sources": line_sources,
                "distinct_line_set_count": len(distinct_sets),
                "purchase_confirmation_evidence": "NOT_FOUND",
                "receipt_evidence": "NOT_FOUND",
                "aggregate_action": "EXCLUDED_FROM_PURCHASE_AGGREGATE",
            }
            unconfirmed.append(unconfirmed_record)
            if len(distinct_sets) > 1:
                source_conflicts.append({
                    "target_round": target,
                    "status": "EXCLUDED_UNRESOLVED",
                    "reason": (
                        "Multiple preserved pre-draw line sets exist and no explicit user "
                        "confirmation or receipt identifies which set was purchased."
                    ),
                    "sources": line_sources,
                    "purchase_confirmation_evidence": "NOT_FOUND",
                    "receipt_evidence": "NOT_FOUND",
                    "aggregate_action": "EXCLUDED_FROM_SINGLE_CANONICAL_AGGREGATE",
                })
            continue

        source_path = str(confirmation["source_path"])
        candidate = candidate_by_path[source_path]
        obj = candidate["obj"]
        tickets = obj.get("final_lines")
        training_cutoff = obj.get("training_cutoff", obj.get("data_cutoff"))
        valid = (
            _normalize_five_lines(tickets) is not None
            and training_cutoff is not None
            and int(training_cutoff) < target
        )
        if not valid:
            invalid.append({
                "path": source_path,
                "target": target,
                "reason": "confirmed_source_integrity_or_cutoff_failure",
            })
            continue

        actual = set(by_round[target]["nums"])
        hits = [len(set(ticket) & actual) for ticket in tickets]
        all_hits.extend(hits)
        union = set().union(*(set(ticket) for ticket in tickets))
        union_hits = len(union & actual)
        max_hits = max(hits)
        reviews.append({
            "target_round": target,
            "source": source_path,
            "source_role": "ACTUAL_PURCHASE_CONFIRMED",
            "source_sha256": candidate["source_sha256"],
            "purchase_confirmation": {
                "confirmation_status": confirmation["confirmation_status"],
                "evidence_type": confirmation["evidence_type"],
                "evidence_reference": confirmation["evidence_reference"],
            },
            "training_cutoff": int(training_cutoff),
            "winning_numbers": by_round[target]["nums"],
            "bonus": by_round[target]["bonus"],
            "line_hits": hits,
            "max_hits": max_hits,
            "winning_union_coverage": union_hits,
            "ticket_union_size": len(union),
            "candidate_recall_failure": union_hits < 6,
            "ticket_construction_gap": max(0, union_hits - max_hits),
            "alternative_preserved_versions": max(0, len(line_sources) - 1),
            "all_preserved_sources": sorted(source["path"] for source in line_sources),
        })

    for target in sorted(set(confirmed_by_target) - set(grouped)):
        invalid.append({
            "target_round": target,
            "reason": "confirmed_target_has_no_preserved_candidate_group",
        })

    dist = {str(k): sum(hit == k for hit in all_hits) for k in range(7)}
    verified_lines = len(all_hits)
    completed_preserved_targets = len(grouped)
    scope_complete = (
        bool(reviews)
        and not invalid
        and not source_conflicts
        and not unconfirmed
        and len(reviews) == completed_preserved_targets
    )
    latest = reviews[-1] if reviews else None
    conflict_rounds = sorted(int(item["target_round"]) for item in source_conflicts)
    if not reviews:
        purchase_status = "NO_CONFIRMED_PURCHASES"
    elif unconfirmed or source_conflicts or invalid:
        purchase_status = "PARTIAL_CONFIRMED_PURCHASES"
    else:
        purchase_status = "CONFIRMED_PURCHASES_AVAILABLE"

    if source_conflicts:
        closed_loop_status = "PARTIAL_UNRESOLVED_SOURCE_CONFLICTS"
    elif unconfirmed:
        closed_loop_status = "PARTIAL_PURCHASE_NOT_CONFIRMED"
    elif invalid:
        closed_loop_status = "PARTIAL_INVALID_RECORDS"
    elif scope_complete:
        closed_loop_status = "COMPLETE_WITHIN_PRESERVED_SCOPE"
    else:
        closed_loop_status = "NO_CONFIRMED_PURCHASE_RECORDS"

    confirmed_sources = [
        {
            "target_round": review["target_round"],
            "source_path": review["source"],
            "source_sha256": review["source_sha256"],
            "evidence_type": review["purchase_confirmation"]["evidence_type"],
            "evidence_reference": review["purchase_confirmation"]["evidence_reference"],
        }
        for review in reviews
    ]
    payload = {
        "generated_kst": datetime.now(KST).isoformat(),
        "scope": (
            "Only sources explicitly confirmed by the user or backed by a preserved receipt "
            "in PURCHASE_CONFIRMATION_REGISTRY.json are included in the actual-purchase aggregate. "
            "Filenames, displayed recommendations, and pre-draw FINAL artifacts alone do not prove purchase."
        ),
        "data_cutoff": cutoff,
        "purchase_confirmation_status": purchase_status,
        "purchase_confirmation_registry": {
            "path": str(registry_path.relative_to(ROOT)),
            "status": registry_status,
            "confirmed_entry_count": len(confirmed_sources),
        },
        "completed_preserved_targets_found": completed_preserved_targets,
        "unconfirmed_purchase_target_count": len(unconfirmed),
        "verified_round_count": len(reviews),
        "verified_purchase_lines": verified_lines,
        "aggregate_hit_distribution": dist,
        "mean_main_hits_per_line": statistics.mean(all_hits) if all_hits else None,
        "rate_ge2": sum(hit >= 2 for hit in all_hits) / verified_lines if verified_lines else None,
        "rate_ge3": sum(hit >= 3 for hit in all_hits) / verified_lines if verified_lines else None,
        "rate_ge4": sum(hit >= 4 for hit in all_hits) / verified_lines if verified_lines else None,
        "closed_loop_complete": scope_complete,
        "closed_loop_status": closed_loop_status,
        "whole_history_complete": False,
        "whole_history_note": (
            "Legacy/older recommendation formats outside the discovered weekly_purchase artifacts "
            "are not proven complete and must not be described as the full historical closed loop."
        ),
        "actual_purchase_precedence": True,
        "confirmed_purchase_sources": confirmed_sources,
        "unconfirmed_preserved_line_sources": unconfirmed,
        "invalid_or_unreviewable_preserved_records": invalid,
        "unresolved_source_conflicts": source_conflicts,
        "excluded_conflict_rounds": conflict_rounds,
        "reviews": reviews,
        "error_note": {
            "latest_completed_review": latest["target_round"] if latest else None,
            "candidate_recall_failure": latest["candidate_recall_failure"] if latest else None,
            "ticket_construction_gap": latest["ticket_construction_gap"] if latest else None,
            "finding": (
                "No purchase-confirmed records are available; preserved recommendation/fallback "
                "line sets are excluded from actual-purchase learning."
                if latest is None
                else (
                    "Both candidate recall and ticket construction need separate diagnosis."
                    if latest["candidate_recall_failure"] and latest["ticket_construction_gap"] > 0
                    else "Use the measured recall/construction fields; do not force a diagnosis beyond preserved evidence."
                )
            ),
            "action_for_next_policy": (
                "Learn only from source lines explicitly confirmed as purchased or backed by a receipt; "
                "never infer purchase from filenames or pre-draw artifacts."
            ),
            "unresolved_source_conflict_rounds": conflict_rounds,
            "provenance_action": (
                "Keep unconfirmed and conflicting preserved line sets out of the canonical aggregate "
                "until explicit purchase confirmation or receipt evidence resolves them."
            ),
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
    result["execution_status"] = "EVIDENCE_WRITTEN_WITH_PARTIAL_SCOPE" if result["status"] == "PARTIAL" else "EVIDENCE_WRITTEN"
    print(json.dumps(result, ensure_ascii=False))
    # A documented provenance limitation is a valid partial result, not a failed process.


if __name__ == "__main__":
    main()
