"""Write-once prospective purchase and outcome event helpers (no recommendations)."""
from __future__ import annotations

import gzip
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
E030_REL = Path("analysis/2026-10-14/gha_38512512127_1/E030_PROSPECTIVE_SIGNAL_FREEZE_v1/FROZEN_SIGNALS_1246.json")
E045_REL = Path("analysis/2026-10-14/E045_PROSPECTIVE_RANDOM5_BASELINE_v1")
LEDGER_ROOT = Path("analysis/prospective_v1")


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def digest_file(path: Path) -> str:
    return digest_bytes(path.read_bytes())


def _validate_lines(lines: list[list[int]], count: int) -> list[list[int]]:
    if len(lines) != count:
        raise ValueError(f"expected exactly {count} lines; got {len(lines)}")
    clean = []
    for i, line in enumerate(lines, 1):
        nums = sorted(int(x) for x in line)
        if len(nums) != 6 or len(set(nums)) != 6 or nums[0] < 1 or nums[-1] > 45:
            raise ValueError(f"line {i} must contain six distinct integers in 1..45")
        clean.append(nums)
    if count > 1 and len({tuple(x) for x in clean}) != count:
        raise ValueError("ticket lines must be distinct")
    return clean


def seal_purchase(root: Path, target_round: int, lines: list[list[int]], metadata: dict,
                  draw_at_utc: str) -> Path:
    """Create a per-round purchase record before draw time; never replaces an event."""
    now = datetime.now(timezone.utc)
    draw_at = datetime.fromisoformat(draw_at_utc.replace("Z", "+00:00"))
    if now >= draw_at:
        raise ValueError("purchase record must be sealed before the registered draw time")
    clean = _validate_lines(lines, 5)
    if metadata.get("purchase") is not True or metadata.get("sealed_before_draw") is not True:
        raise ValueError("purchase=true and sealed_before_draw=true evidence are required")
    if not metadata.get("source_evidence"):
        raise ValueError("source_evidence must identify the real purchase evidence")
    line_hashes = [digest_bytes(json.dumps(x, separators=(",", ":")).encode()) for x in clean]
    provenance = metadata.get("line_provenance") or [{} for _ in clean]
    if len(provenance) != 5:
        raise ValueError("line_provenance must have one record per purchased line")
    line_provenance = []
    for i, record in enumerate(provenance):
        line_provenance.append({"source_model": record.get("source_model", "unknown"),
                                "model_version": record.get("model_version", "unknown"),
                                "training_cutoff": record.get("training_cutoff", "unknown"),
                                "selection_score": record.get("selection_score", "unknown"),
                                "selection_reason": record.get("selection_reason", "unknown"),
                                "line_sha256": line_hashes[i]})
    bundle = {"study_id": "E044_REAL_PURCHASE_FIVE_LINE_LEDGER_v1", "target_round": int(target_round),
              "purchase_timestamp_utc": now.isoformat(), "lines": clean,
              "line_provenance": line_provenance, "line_sha256": line_hashes,
              "bundle_sha256": "computed_over_bundle_without_this_field", "selection_score": metadata.get("selection_score", "unknown"),
              "selection_reason": metadata.get("selection_reason", "unknown"), "purchase": True,
              "sealed_before_draw": True, "source_evidence": metadata["source_evidence"], "draw_at_utc": draw_at.isoformat()}
    bundle_payload = dict(bundle)
    bundle_payload.pop("bundle_sha256")
    bundle_sha = digest_bytes(json.dumps(bundle_payload, sort_keys=True, separators=(",", ":")).encode())
    bundle["bundle_sha256"] = bundle_sha
    path = root / LEDGER_ROOT / "purchases" / f"ROUND_{target_round}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(bundle, stream, ensure_ascii=False, indent=2); stream.write("\n")
    return path


def verify_purchase_bundle(path: Path) -> dict:
    bundle = json.loads(path.read_text(encoding="utf-8"))
    expected = bundle.get("bundle_sha256")
    payload = dict(bundle); payload.pop("bundle_sha256", None)
    if digest_bytes(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()) != expected:
        raise ValueError("purchase bundle SHA mismatch")
    lines = _validate_lines(bundle["lines"], 5)
    for i, line in enumerate(lines):
        digest = digest_bytes(json.dumps(line, separators=(",", ":")).encode())
        if digest != bundle["line_sha256"][i] or digest != bundle["line_provenance"][i]["line_sha256"]:
            raise ValueError(f"purchase line {i+1} SHA mismatch")
    return bundle


def _score_line(line: list[int], winning: set[int]) -> int:
    return len(set(line) & winning)


def evaluate_purchase(purchase_path: Path, actual: dict, output_path: Path) -> dict:
    purchase = json.loads(purchase_path.read_text(encoding="utf-8"))
    if int(purchase["target_round"]) != int(actual["target_round"]):
        raise ValueError("purchase and outcome target rounds differ")
    lines = _validate_lines(purchase["lines"], 5)
    winning = set(_validate_lines([actual["main_numbers"]], 1)[0])
    bonus = int(actual["bonus"])
    if not 1 <= bonus <= 45 or bonus in winning:
        raise ValueError("invalid official bonus")
    hits = [_score_line(line, winning) for line in lines]
    union = set().union(*(set(x) for x in lines))
    rank_map = actual.get("pre_draw_rank", {})
    score_map = actual.get("pre_draw_scores", {})
    outcome = {"study_id": "E044_PURCHASE_OUTCOME_v1", "target_round": actual["target_round"],
               "purchase_file_sha256": digest_file(purchase_path), "official_source_evidence": actual["source_evidence"],
               "official_main_numbers": sorted(winning), "official_bonus": bonus, "line_hits": hits,
               "max_hits": max(hits), "any2plus": any(x >= 2 for x in hits), "any3plus": any(x >= 3 for x in hits),
               "any4plus": any(x >= 4 for x in hits), "any5plus": any(x >= 5 for x in hits), "any6": any(x == 6 for x in hits),
               "winning_union_coverage": len(winning & union), "missed_winning_numbers": sorted(winning - union),
               "pre_draw_rank": {str(n): rank_map.get(str(n), rank_map.get(n)) for n in sorted(winning)} if rank_map else None,
               "overestimated_nonwinners": sorted(((int(n), float(score)) for n, score in score_map.items() if int(n) not in winning), key=lambda x: (-x[1], x[0]))[:10] if score_map else [],
               "bonus_in_lines": [bonus in x for x in lines], "outcome_recorded_at_utc": datetime.now(timezone.utc).isoformat()}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(outcome, stream, ensure_ascii=False, indent=2); stream.write("\n")
    return outcome


def read_random5_pool(path: Path, expected_sha256: str) -> list[dict]:
    if digest_file(path) != expected_sha256:
        raise ValueError("random5 pool SHA-256 mismatch")
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        rows = [json.loads(line) for line in stream if line.strip()]
    if len(rows) != 10_000:
        raise ValueError(f"random5 pool must contain 10000 portfolios; got {len(rows)}")
    for i, row in enumerate(rows, 1):
        if row["portfolio_index"] != i:
            raise ValueError("random5 portfolio indices are not contiguous")
        _validate_lines(row["lines"], 5)
    return rows


def evaluate_random5_pool(path: Path, expected_sha256: str, actual: dict, output_path: Path) -> dict:
    rows = read_random5_pool(path, expected_sha256)
    winning = set(_validate_lines([actual["main_numbers"]], 1)[0])
    metrics = []
    for row in rows:
        lines = row["lines"]
        hits = [_score_line(line, winning) for line in lines]
        union = set().union(*(set(x) for x in lines))
        overlaps = [len(set(lines[i]) & set(lines[j])) for i in range(5) for j in range(i+1, 5)]
        metrics.append({"portfolio_index": row["portfolio_index"], "max_hits": max(hits),
                        "any2plus": any(x >= 2 for x in hits), "any3plus": any(x >= 3 for x in hits),
                        "any4plus": any(x >= 4 for x in hits), "any5plus": any(x >= 5 for x in hits),
                        "any6": any(x == 6 for x in hits), "winning_union_coverage": len(winning & union),
                        "unique_number_coverage": len(union), "mean_pairwise_overlap": sum(overlaps)/len(overlaps)})
    keys = ["max_hits", "any2plus", "any3plus", "any4plus", "any5plus", "any6", "winning_union_coverage", "unique_number_coverage", "mean_pairwise_overlap"]
    means = {key: sum(float(row[key]) for row in metrics)/len(metrics) for key in keys}
    result = {"study_id": "E045_RANDOM5_OUTCOME_v1", "target_round": actual["target_round"],
              "pool_sha256": expected_sha256, "portfolios_evaluated": len(rows), "random5_metric_means": means,
              "random5_metrics_by_portfolio": metrics, "recorded_at_utc": datetime.now(timezone.utc).isoformat()}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, ensure_ascii=False, separators=(",", ":")); stream.write("\n")
    return result


def evaluate_shadow_prediction(root: Path, prediction_path: Path, prediction_sha256: str,
                               random_single_path: Path, random_single_sha256: str,
                               actual: dict, output_path: Path) -> dict:
    frozen_check = validate_frozen_prediction(root, prediction_path, int(actual["target_round"]), prediction_sha256, allow_outcome=True)
    prediction = json.loads(prediction_path.read_text(encoding="utf-8"))
    winning = set(_validate_lines([actual["main_numbers"]], 1)[0])
    if digest_file(random_single_path) != random_single_sha256:
        raise ValueError("single-ticket random pool SHA mismatch")
    with gzip.open(random_single_path, "rt", encoding="utf-8") as stream:
        random_rows = [json.loads(line) for line in stream if line.strip()]
    if len(random_rows) != 10_000:
        raise ValueError("single-ticket comparator pool must have 10000 rows")
    random_hits = [len(set(row["numbers"]) & winning) for row in random_rows]
    model_rows = []
    for signal in prediction.get("signals", []):
        numbers = _validate_lines([signal["numbers"]], 1)[0]
        hits = len(set(numbers) & winning)
        model_rows.append({"model": signal["signal"], "model_version": signal.get("formula_version", signal.get("model_version", "unknown")),
                           "model_hits": hits, "same_target_random_mean_hits": sum(random_hits)/len(random_hits),
                           "paired_difference_vs_random_mean": hits - sum(random_hits)/len(random_hits),
                           "random_2plus_rate": sum(x >= 2 for x in random_hits)/len(random_hits),
                           "random_3plus_rate": sum(x >= 3 for x in random_hits)/len(random_hits),
                           "random_4plus_rate": sum(x >= 4 for x in random_hits)/len(random_hits),
                           "random_5plus_rate": sum(x >= 5 for x in random_hits)/len(random_hits),
                           "random_6_rate": sum(x == 6 for x in random_hits)/len(random_hits)})
    result = {"study_id": "E046_SHADOW_MODEL_OUTCOME_v2", "target_round": actual["target_round"],
              "prediction_provenance": frozen_check, "prediction_file_sha256": prediction_sha256,
              "random_single_pool_sha256": random_single_sha256, "random_single_samples": len(random_hits),
              "official_source_evidence": actual["source_evidence"], "official_main_numbers": sorted(winning),
              "models": model_rows, "recorded_at_utc": datetime.now(timezone.utc).isoformat()}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2); stream.write("\n")
    return result


def write_outcome_event(root: Path, actual: dict) -> Path:
    """Accept only two independently identified sources; create immutable round event."""
    sources = actual.get("source_evidence", [])
    if len(sources) < 2 or len({x.get("source_type") for x in sources}) < 2:
        raise ValueError("two independent source-evidence records are required")
    hosts = {urlparse(str(x.get("url", ""))).netloc.lower() for x in sources}
    if "" in hosts or len(hosts) < 2:
        raise ValueError("independent sources must have distinct recorded source URLs/hosts")
    draw_at = datetime.fromisoformat(actual["draw_at_utc"].replace("Z", "+00:00"))
    if datetime.now(timezone.utc) < draw_at:
        raise ValueError("official outcome cannot be recorded before draw time")
    main = _validate_lines([actual["main_numbers"]], 1)[0]
    bonus = int(actual["bonus"])
    if not 1 <= bonus <= 45 or bonus in main:
        raise ValueError("invalid bonus number")
    event = {"study_id": "PROSPECTIVE_OFFICIAL_OUTCOME_v1", "target_round": int(actual["target_round"]),
             "draw_date": actual["draw_date"], "main_numbers": main, "bonus": bonus,
             "source_evidence": sources, "recorded_at_utc": datetime.now(timezone.utc).isoformat()}
    path = root / LEDGER_ROOT / "outcomes" / f"ROUND_{actual['target_round']}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(event, stream, ensure_ascii=False, indent=2); stream.write("\n")
    return path


def validate_frozen_prediction(root: Path, prediction_path: Path, target_round: int,
                               expected_sha256: str | None = None, allow_outcome: bool = False) -> dict:
    """Reject missing, changed, or cutoff-unsafe forecasts before outcome scoring."""
    if not allow_outcome and (root / LEDGER_ROOT / "outcomes" / f"ROUND_{target_round}.json").exists():
        raise ValueError("outcome already recorded; target prediction must not be regenerated")
    payload_bytes = prediction_path.read_bytes()
    sha = digest_bytes(payload_bytes)
    if expected_sha256 and sha != expected_sha256:
        raise ValueError("frozen prediction SHA mismatch")
    data = json.loads(payload_bytes.decode("utf-8"))
    if int(data.get("target_round", -1)) != int(target_round):
        raise ValueError("prediction target round mismatch")
    if int(data.get("training_through_round", data.get("training_cutoff", -1))) != int(target_round) - 1:
        raise ValueError("prediction cutoff must equal target_round - 1")
    if data.get("status") != "FROZEN_PROSPECTIVE_SHADOW_ONLY":
        raise ValueError("prediction is not marked as a frozen shadow forecast")
    return {"target_round": target_round, "training_cutoff": target_round-1, "prediction_sha256": sha, "leakage_failures": 0}


def mixture_e_value(differences: list[float], lower: float, upper: float,
                    lambdas: list[float]) -> float:
    """One-sided bounded-difference Hoeffding mixture e-value for H0: mean <= 0."""
    if lower >= upper or not lambdas or any(x <= 0 for x in lambdas):
        raise ValueError("invalid bounds or lambda grid")
    if any(not lower <= x <= upper for x in differences):
        raise ValueError("paired difference outside registered bounds")
    n = len(differences)
    total = sum(differences)
    values = [math.exp(max(-745.0, min(700.0, lam*total - n*lam*lam*(upper-lower)**2/8))) for lam in lambdas]
    return sum(values) / len(values)


def freeze_random_pools(root: Path, target_round: int, draw_at_utc: str,
                        base_seed_5: int = 20261014045,
                        base_seed_single: int = 20261014044) -> dict:
    """Freeze both comparator pools for a future round before its draw, create-exclusive."""
    from prepare_prospective_v1 import N_PORTFOLIOS, random_pool_bytes, random_single_pool_bytes
    draw_at = datetime.fromisoformat(draw_at_utc.replace("Z", "+00:00"))
    if datetime.now(timezone.utc) >= draw_at:
        raise ValueError("random comparator pools must be frozen before the registered draw time")
    if (root / LEDGER_ROOT / "outcomes" / f"ROUND_{target_round}.json").exists():
        raise ValueError("outcome exists; comparator pools cannot be generated after result access")
    run_date = datetime.now(timezone.utc).date().isoformat()
    folder = root / "analysis" / run_date / "E045_PROSPECTIVE_RANDOM5_BASELINE_v1" / f"ROUND_{target_round}"
    folder.mkdir(parents=True, exist_ok=True)
    five = folder / f"RANDOM5_POOL_{target_round}.jsonl.gz"
    single = folder / f"SINGLE_TICKET_POOL_{target_round}.jsonl.gz"
    seal_path = folder / f"RANDOM_BASELINE_SEAL_{target_round}.json"
    if five.exists() or single.exists() or seal_path.exists():
        raise FileExistsError(f"random baseline already exists for target {target_round}; never regenerate")
    five_bytes = random_pool_bytes(target_round, N_PORTFOLIOS, base_seed_5)
    single_bytes = random_single_pool_bytes(target_round, N_PORTFOLIOS, base_seed_single)
    with five.open("xb") as stream:
        stream.write(five_bytes)
    with single.open("xb") as stream:
        stream.write(single_bytes)
    seal = {"target_round": target_round, "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "draw_at_utc": draw_at.isoformat(), "random5_seed": base_seed_5 + target_round,
            "random5_path": five.relative_to(root).as_posix(), "random5_sha256": digest_file(five),
            "single_seed": base_seed_single + target_round, "single_path": single.relative_to(root).as_posix(),
            "single_sha256": digest_file(single), "portfolios_or_tickets": 10_000, "created_before_draw": True}
    with seal_path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(seal, stream, indent=2); stream.write("\n")
    return seal
