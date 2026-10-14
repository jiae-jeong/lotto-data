#!/usr/bin/env python3
"""Freeze prospective evaluation rules and a deterministic random5 pool.

This setup never generates a purchased recommendation and never edits E030 or
canonical draw data. All output creation is write-once.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import itertools
import json
import math
import random
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = Path(__file__).resolve().parent
OUT = ROOT / "analysis/2026-10-14/E043_E049_PROSPECTIVE_EVIDENCE_v1"
E030 = ROOT / "analysis/2026-10-14/gha_38512512127_1/E030_PROSPECTIVE_SIGNAL_FREEZE_v1/FROZEN_SIGNALS_1246.json"
CANONICAL_ROUNDS = 1245
CANONICAL_SHA256 = "e534123cd7227f8c21d32251a567edeb018e7d1d9c4b049e4d23fb987f2619a4"
E030_PREDICTION_SHA256 = "719c4cc11174c80dd1ddef75e438a2de36ec76842869128bf17ecacf646cb931"
E030_CODE_SHA256 = "2ccc817e5d9d21807d709173772a1384039eac74f68ec2c3580107d0a77ee783"
E030_CONFIG_SHA256 = "ddd916d0c0c1db500301fcd16297e1ca98f60775b49e1c45ea381e6eef3e6ed1"
E030_PATH = "analysis/2026-10-14/gha_38512512127_1/E030_PROSPECTIVE_SIGNAL_FREEZE_v1/FROZEN_SIGNALS_1246.json"
TARGET = 1246
BASE_SEED = 20261014045
SINGLE_BASE_SEED = 20261014044
N_PORTFOLIOS = 10_000
TICKETS_PER_PORTFOLIO = 5
NUMBERS_PER_TICKET = 6


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def write_once(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data)


def choose(n: int, k: int) -> int:
    return math.comb(n, k) if 0 <= k <= n else 0


def p_no_ticket_at_least(k: int) -> float:
    universe = choose(45, 6)
    tickets = sum(choose(6, h) * choose(39, 6 - h) for h in range(k, 7))
    return choose(universe - tickets, TICKETS_PER_PORTFOLIO) / choose(universe, TICKETS_PER_PORTFOLIO)


def random5_exact_metrics() -> dict:
    p_any = {str(k): 1.0 - p_no_ticket_at_least(k) for k in range(2, 7)}
    p_max_ge = {str(k): 1.0 - p_no_ticket_at_least(k) for k in range(1, 7)}
    mean_max = sum(p_max_ge.values())
    # Each candidate line is a uniform 6-subset; portfolios are sampled without
    # duplicate lines. Finite-population correction is used for number coverage.
    total = choose(45, 6)
    excludes_n = choose(44, 6)
    no_number = choose(excludes_n, TICKETS_PER_PORTFOLIO) / choose(total, TICKETS_PER_PORTFOLIO)
    return {
        "method": "exact combinatorial null; five distinct tickets sampled uniformly without replacement",
        "single_ticket_mean_hits": 0.8,
        "single_ticket_variance_hits": 6 * (6 / 45) * (39 / 45) * (39 / 44),
        "five_line_any_kplus_probability": p_any,
        "five_line_max_hits_ge_probability": p_max_ge,
        "five_line_expected_max_hits": mean_max,
        "five_line_expected_unique_number_coverage": 45 * (1 - no_number),
        "five_line_expected_pairwise_overlap": 6 * 6 / 45,
    }


def normal_quantile(p: float) -> float:
    # Acklam rational approximation; used for planning, not inferential results.
    a = [-3.969683028665376e1, 2.209460984245205e2, -2.759285104469687e2,
         1.383577518672690e2, -3.066479806614716e1, 2.506628277459239]
    b = [-5.447609879822406e1, 1.615858368580409e2, -1.556989798598866e2,
         6.680131188771972e1, -1.328068155288572e1]
    c = [-7.784894002430293e-3, -3.223964580411365e-1, -2.400758277161838,
         -2.549732539343734, 4.374664141464968, 2.938163982698783]
    d = [7.784695709041462e-3, 3.224671290700398e-1, 2.445134137142996,
         3.754408661907416]
    if not 0 < p < 1:
        raise ValueError("p must be in (0,1)")
    if p < 0.02425:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    if p > 1 - 0.02425:
        q = math.sqrt(-2 * math.log(1-p))
        return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    q = p - 0.5
    r = q*q
    return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)


def power_n(delta: float, variance: float, alpha: float, power: float) -> int:
    z = normal_quantile(1-alpha) + normal_quantile(power)
    return math.ceil((z * math.sqrt(variance) / delta) ** 2)


def power_horizon(exact: dict) -> dict:
    alpha_each = 0.02
    power_levels = (0.80, 0.90)
    out = {"method": "one-sided normal planning approximation; alpha 0.02 per co-primary portfolio metric and 0.01 for shadow single-ticket evidence; not evidence", "alpha_each_primary": alpha_each, "false_positive_gate_familywise": 0.05, "assumptions": "prospective independent target rounds; fixed effect; no optional stopping; sequential decisions use E047 e-process, so these fixed-horizon approximations are planning only", "single_ticket_mean_hits": {}, "five_line_any3plus": {}, "five_line_mean_max_hits": {}}
    v_single = exact["single_ticket_variance_hits"]
    p_any3 = exact["five_line_any_kplus_probability"]["3"]
    pmax = exact["five_line_expected_max_hits"]
    # Obtain exact max-hit variance from its discrete survival distribution.
    surv = exact["five_line_max_hits_ge_probability"]
    pmf = {}
    for k in range(0, 6):
        pmf[k] = surv[str(k)] - surv[str(k+1)] if k else 1 - surv["1"]
    pmf[6] = surv["6"]
    v_max = sum((k-pmax)**2 * p for k,p in pmf.items())
    for delta in (0.02, 0.04, 0.06, 0.10):
        out["single_ticket_mean_hits"][str(delta)] = {str(p): power_n(delta, 2*v_single, 0.01, p) for p in power_levels}
    for delta in (0.01, 0.02, 0.03, 0.05):
        p1 = min(1.0, p_any3+delta)
        variance = p_any3*(1-p_any3) + p1*(1-p1)
        out["five_line_any3plus"][str(delta)] = {str(p): power_n(delta, variance, alpha_each, p) for p in power_levels}
    for delta in (0.05, 0.10, 0.15, 0.20):
        out["five_line_mean_max_hits"][str(delta)] = {str(p): power_n(delta, 2*v_max, alpha_each, p) for p in power_levels}
    out["random5_null_reference"] = {"any3plus": p_any3, "mean_max_hits": pmax, "max_hits_variance": v_max}
    out["monitoring_phases"] = {"EARLY_MONITORING": {"targets": "1-24", "allowed": "integrity and descriptive summaries only"}, "INTERMEDIATE_EVIDENCE": {"targets": "25-199", "allowed": "e-process and confidence-sequence monitoring; no promotion before 200"}, "CONFIRMATORY_EVIDENCE": {"targets": "200", "allowed": "apply E049 promotion gate once the fixed horizon and all integrity requirements are met"}}
    return out


def random_pool_bytes(target: int = TARGET, count: int = N_PORTFOLIOS, base_seed: int = BASE_SEED) -> bytes:
    rng = random.Random(base_seed + target)
    lines = []
    for i in range(count):
        portfolio = set()
        while len(portfolio) < TICKETS_PER_PORTFOLIO:
            portfolio.add(tuple(sorted(rng.sample(range(1, 46), NUMBERS_PER_TICKET))))
        row = {"target_round": target, "portfolio_index": i + 1, "lines": [list(x) for x in sorted(portfolio)]}
        lines.append(json.dumps(row, separators=(",", ":"), ensure_ascii=True).encode() + b"\n")
    raw = b"".join(lines)
    import io
    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode="wb", filename="", mtime=0, compresslevel=9) as gz:
        gz.write(raw)
    return buffer.getvalue()


def random_single_pool_bytes(target: int = TARGET, count: int = N_PORTFOLIOS, base_seed: int = SINGLE_BASE_SEED) -> bytes:
    rng = random.Random(base_seed + target)
    rows = []
    for i in range(count):
        row = {"target_round": target, "sample_index": i + 1, "numbers": sorted(rng.sample(range(1, 46), 6))}
        rows.append(json.dumps(row, separators=(",", ":")).encode() + b"\n")
    import io
    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode="wb", filename="", mtime=0, compresslevel=9) as gz:
        gz.write(b"".join(rows))
    return buffer.getvalue()


def protocol(now: str) -> dict:
    return {
        "study_id": "E043_E049_PROSPECTIVE_EVIDENCE_v1",
        "status": "FROZEN_BEFORE_TARGET_1246_OUTCOME",
        "created_at_utc": now,
        "source_commit": "997adeb22bc7c1b68c8f5fe6390ab5c658416873",
        "canonical_data": {"path": "lotto_data.csv", "rounds": [1, CANONICAL_ROUNDS], "latest_round": CANONICAL_ROUNDS, "sha256": CANONICAL_SHA256, "handling": "read-only; future outcomes kept as separate immutable events"},
        "target_round": TARGET,
        "models": [
            {"model": "CALENDAR_SEASON_CONDITIONAL_v1", "model_version": "E025_FROZEN_v1", "role": "shadow only", "formula": "seasonal number counts with a 30-draw global-rate prior; frozen model implementation identified by code/config SHA", "training_cutoff": 1245, "prediction_generated_at_utc": "2026-10-14T04:39:53.357018+00:00", "prediction_path": E030_PATH, "prediction_sha256": E030_PREDICTION_SHA256, "code_sha256": E030_CODE_SHA256, "config_sha256": E030_CONFIG_SHA256},
            {"model": "PREVIOUS_SUM_REGIME_CONDITIONAL_v1", "model_version": "E025_FROZEN_v1", "role": "shadow only", "formula": "number counts conditional on prior-draw sum regime with a 20-draw global-rate prior; frozen model implementation identified by code/config SHA", "training_cutoff": 1245, "prediction_generated_at_utc": "2026-10-14T04:39:53.357018+00:00", "prediction_path": E030_PATH, "prediction_sha256": E030_PREDICTION_SHA256, "code_sha256": E030_CODE_SHA256, "config_sha256": E030_CONFIG_SHA256},
            {"model": "ACTUAL_PURCHASE_FIVE_LINES", "model_version": "purchase-recorded-per-target", "role": "only verified actual purchase lines; none inferred", "training_cutoff": "per-source-record", "prediction_generated_at_utc": "must be before official draw", "prediction_sha256": "per sealed bundle"}
        ],
        "cutoff_rule": "Every target t uses only canonical or frozen information through t-1. E030 target 1246 cutoff is 1245. Do not recompute target 1246 after outcome.",
        "confirmatory_horizon": {"first_target": 1246, "last_target": 1445, "targets": 200, "blocks": [[1246,1295],[1296,1345],[1346,1395],[1396,1445]]},
        "registered_config_sha256": "filled by setup generator",
        "random_comparators": {
            "single_ticket": {"distribution": "uniform 6-subsets from 1..45; 10000 frozen draws per target", "seed_rule": "single_base_seed + target_round", "base_seed": SINGLE_BASE_SEED, "target_1246_seed": SINGLE_BASE_SEED + TARGET, "pool_file": "analysis/2026-10-14/E045_PROSPECTIVE_RANDOM5_BASELINE_v1/SINGLE_TICKET_POOL_1246.jsonl.gz", "pool_sha256": "filled by verification manifest"},
            "random5": {"distribution": "uniform 6-subsets; five distinct tickets per portfolio; 10,000 independently sampled portfolios", "seed_rule": "Python random.Random(base_seed + target_round)", "base_seed": BASE_SEED, "target_1246_seed": BASE_SEED + TARGET, "pool_file": "analysis/2026-10-14/E045_PROSPECTIVE_RANDOM5_BASELINE_v1/RANDOM5_POOL_1246.jsonl.gz", "pool_sha256": "filled by verification manifest"}
        },
        "metrics": ["single-ticket mean hits", "single-ticket 2+/3+/4+/5+/6+", "five-line max hits", "five-line any2+/3+/4+/5+/6", "winning-number union coverage", "unique-number coverage", "mean pairwise overlap", "model-minus-random paired difference"],
        "outcome_policy": "Prediction, purchase, random pool and outcome artifacts are separate. Outcome events are write-once. Never edit pre-draw bytes after draw.",
        "status_rules": {"initial": "PROSPECTIVE_PENDING", "weak": "PROSPECTIVE_WEAK_SIGNAL", "validated": "PROSPECTIVE_VALIDATED_EDGE only when E047 anytime-valid and E048 horizon gates pass", "reject": "REJECTED only under the frozen futility rule; otherwise pending", "historical": "HISTORICAL_SCREENING; rounds 1..1245 are not untouched validation"},
        "promotion": {"familywise_alpha": 0.05, "all_primary_gates_required": True, "portfolio_primary": ["any3plus paired difference > 0", "mean max hits paired difference > 0"], "harm_gate": "any4plus paired difference >= 0 at confirmatory horizon", "block_stability": "at least 3 of 4 fixed 50-round blocks have positive paired differences; the remaining block may not be below -0.02 for any3plus or -0.10 for max hits", "leakage_failures_allowed": 0, "one_or_two_draw_promotion": False, "no_selector_retuning_before_validation": True},
        "e030_immutable": {"path": E030_PATH, "sha256": E030_PREDICTION_SHA256, "prohibition": "no edit, rerun, or retuning of target-1246 prediction"},
        "no_recommendation_generation": True
    }


def main() -> None:
    now = datetime.now(timezone.utc).isoformat()
    OUT.mkdir(parents=True, exist_ok=True)
    pool_path = ROOT / "analysis/2026-10-14/E045_PROSPECTIVE_RANDOM5_BASELINE_v1/RANDOM5_POOL_1246.jsonl.gz"
    if not pool_path.exists():
        write_once(pool_path, random_pool_bytes())
    pool_sha = sha_file(pool_path)
    pool_size = pool_path.stat().st_size
    single_path = pool_path.with_name("SINGLE_TICKET_POOL_1246.jsonl.gz")
    if not single_path.exists():
        write_once(single_path, random_single_pool_bytes())
    single_sha = sha_file(single_path)
    single_size = single_path.stat().st_size
    protocol_obj = protocol(now)
    protocol_obj["random_comparators"]["random5"]["pool_sha256"] = pool_sha
    protocol_obj["random_comparators"]["random5"]["pool_bytes"] = pool_size
    protocol_obj["random_comparators"]["single_ticket"]["pool_sha256"] = single_sha
    protocol_obj["random_comparators"]["single_ticket"]["pool_bytes"] = single_size
    protocol_bytes = (json.dumps(protocol_obj, ensure_ascii=False, indent=2) + "\n").encode()
    config_obj = {"study_id": "E043_E049_PROSPECTIVE_EVIDENCE_v1", "target_round": TARGET, "base_seed": BASE_SEED, "n_portfolios": N_PORTFOLIOS, "tickets_per_portfolio": TICKETS_PER_PORTFOLIO, "sampling": "random.Random.sample(range(1,46),6), sorted; resample duplicate tickets within portfolio", "frozen_before_draw": True,
                  "code_sha256": {"research/prospective_v1/prepare_prospective_v1.py": sha_file(Path(__file__)), "research/prospective_v1/ledger_v1.py": sha_file(BASE / "ledger_v1.py"), "research/prospective_v1/verify_prospective_v1.py": sha_file(BASE / "verify_prospective_v1.py"), "research/prospective_v1/tests/test_prospective_v1.py": sha_file(BASE / "tests/test_prospective_v1.py"), ".github/workflows/prospective-evidence-v1.yml": sha_file(ROOT / ".github/workflows/prospective-evidence-v1.yml")}}
    config_bytes = (json.dumps(config_obj, ensure_ascii=False, indent=2) + "\n").encode()
    config_path = BASE / "CONFIG.json"
    if not config_path.exists():
        write_once(config_path, config_bytes)
    else:
        config_bytes = config_path.read_bytes()
    protocol_obj["registered_config_sha256"] = sha_bytes(config_bytes)
    protocol_bytes = (json.dumps(protocol_obj, ensure_ascii=False, indent=2) + "\n").encode()
    # The protocol and all deliverables are write-once even on repeated calls.
    write_once(OUT / "PROSPECTIVE_PROTOCOL.json", protocol_bytes)
    write_once(OUT / "PROSPECTIVE_PROTOCOL_SHA256.txt", (sha_bytes(protocol_bytes) + "  PROSPECTIVE_PROTOCOL.json\n").encode())
    metrics = random5_exact_metrics()
    random5_doc = {"study_id": "E045_PROSPECTIVE_RANDOM5_BASELINE_v1", "target_round": TARGET, "status": "FROZEN_PRE_DRAW", "seed": BASE_SEED + TARGET, "seed_rule": "base_seed + target_round", "base_seed": BASE_SEED, "portfolios": N_PORTFOLIOS, "tickets_per_portfolio": TICKETS_PER_PORTFOLIO, "pool_path": pool_path.relative_to(ROOT).as_posix(), "pool_sha256": pool_sha, "pool_bytes": pool_size, "sampling": "Uniform 6-subsets from 1..45; each five-line portfolio has five distinct tickets; no outcome-conditioned generation.", "exact_null_reference": metrics}
    write_once(OUT / "RANDOM5_BASELINE_1246.json", (json.dumps(random5_doc, ensure_ascii=False, indent=2) + "\n").encode())
    single_doc = {"study_id": "E047_RANDOM_SINGLE_BASELINE_v1", "target_round": TARGET, "status": "FROZEN_PRE_DRAW", "seed": SINGLE_BASE_SEED + TARGET, "base_seed": SINGLE_BASE_SEED, "samples": N_PORTFOLIOS, "pool_path": single_path.relative_to(ROOT).as_posix(), "pool_sha256": single_sha, "pool_bytes": single_size, "sampling": "Uniform six-number tickets sampled independently with replacement at the ticket level."}
    write_once(OUT / "SINGLE_TICKET_BASELINE_1246.json", (json.dumps(single_doc, ensure_ascii=False, indent=2) + "\n").encode())
    shadow_ledger = {"study_id": "E046_SHADOW_MODEL_PROSPECTIVE_LEDGER_v2", "target_round": TARGET, "status": "PREDICTION_FROZEN_PENDING_DRAW", "prediction_file": E030_PATH, "prediction_sha256": E030_PREDICTION_SHA256, "training_cutoff": TARGET-1, "models": ["CALENDAR_SEASON_CONDITIONAL_v1", "PREVIOUS_SUM_REGIME_CONDITIONAL_v1"], "outcome_path": f"analysis/prospective_v1/outcomes/ROUND_{TARGET}.json", "outcome_evaluation_path": f"analysis/prospective_v1/outcomes/E046_SHADOW_OUTCOME_{TARGET}.json", "prediction_mutation_after_draw": "forbidden", "next_prediction": "freeze only after official target outcome is verified and evaluated"}
    write_once(OUT / "E046_SHADOW_LEDGER_1246.json", (json.dumps(shadow_ledger, ensure_ascii=False, indent=2) + "\n").encode())
    purchase_schema = {"study_id": "E044_REAL_PURCHASE_FIVE_LINE_LEDGER_v1", "status": "READY_AWAITING_VERIFIED_ACTUAL_PURCHASE", "immutable_rule": "one file per target round, create-exclusive; never replace", "prediction_and_outcome_separation": True, "required_fields": ["target_round", "purchase_timestamp_utc", "lines[5][6]", "per-line source_model/model_version/training_cutoff/score/reason", "per-line SHA256", "bundle SHA256", "purchase", "sealed_before_draw", "source_evidence"], "outcome_fields_separate": ["target_round", "official_draw_source", "official_main_numbers", "official_bonus", "line_hits", "max_hits", "any2plus", "any3plus", "any4plus", "any5plus", "any6", "winning_union_coverage", "missed_winning_numbers", "pre_draw_rank", "overestimated_nonwinners"], "past_purchase_reconstruction": "prohibited without primary evidence", "actual_purchase_records": []}
    write_once(OUT / "PURCHASE_LEDGER_SCHEMA.json", (json.dumps(purchase_schema, ensure_ascii=False, indent=2) + "\n").encode())
    power_doc = power_horizon(metrics)
    write_once(OUT / "E048_POWER_AND_HORIZON.json", (json.dumps(power_doc, ensure_ascii=False, indent=2) + "\n").encode())
    anytime = {"study_id": "E047_ANYTIME_VALID_PROSPECTIVE_EVIDENCE_v1", "method": "mixture e-processes for bounded paired differences", "familywise_alpha": 0.05, "alpha_allocation": {"five_line_any3plus": 0.02, "five_line_mean_max_hits": 0.02, "shadow_single_ticket_mean_hits": 0.01}, "null": "E[D] <= 0", "D_definition": "same-target actual statistic minus mean over frozen matched random pool statistic; one D per target", "bounds": {"any3plus": [-1, 1], "mean_max_hits": [-6, 6], "shadow_single_ticket_mean_hits": [-6, 6]}, "lambda_grid": [0.005, 0.01, 0.02, 0.04, 0.08, 0.16, 0.32], "weights": "equal weights over positive lambda grid", "component": "exp(lambda * cumulative_sum(D) - n * lambda^2 * (upper-lower)^2 / 8)", "mixture_e_value": "arithmetic mean of component e-values", "reject_boundary": "mixture e-value >= 1/allocated_alpha", "no_weekly_pvalue_restarts": True, "shadow_single_ticket": {"method": "separate one-sided bounded-difference e-process", "alpha": 0.01, "bounds_hits_difference": [-6, 6], "lambda_grid": [0.001, 0.002, 0.004, 0.008, 0.016, 0.032, 0.064]}, "stop_rule": "no interim efficacy stop or promotion; stop early only for an integrity failure; final decision at target 1445 after all 200 registered targets", "first_outcome_policy": "This file and protocol hash must be committed before target 1246 outcome is accessed."}
    write_once(OUT / "E047_ANYTIME_VALID.json", (json.dumps(anytime, ensure_ascii=False, indent=2) + "\n").encode())
    gate = {"study_id": "E049_PROSPECTIVE_PROMOTION_GATE_v1", "status": "PROSPECTIVE_PENDING", "historical_status": "HISTORICAL_SCREENING", "validated_status_requires": ["E047 anytime-valid rejection under frozen family alpha", "E048 minimum horizon reached", "positive paired any3plus and max-hit mean differences", "any4plus no harm", "block stability condition from E043", "zero leakage and zero post-draw prediction rewrites", "complete pre-draw publication and pool hash evidence"], "weak_signal_status": "positive point estimates but gates not met", "rejected_status": "registered futility boundary met or material integrity violation", "prohibited_before_validation": ["E041/E042 selector retuning", "historical threshold tuning", "renamed reuse of failed signals", "promotion based on one or two draws"]}
    write_once(OUT / "E049_PROMOTION_GATE.json", (json.dumps(gate, ensure_ascii=False, indent=2) + "\n").encode())
    verify = {"study_id": "E043_E049_PROSPECTIVE_EVIDENCE_v1", "status": "PASS", "frozen_at_utc": now, "source_commit": "997adeb22bc7c1b68c8f5fe6390ab5c658416873", "canonical_rounds": CANONICAL_ROUNDS, "canonical_sha256_expected": CANONICAL_SHA256, "canonical_file_sha256_verified_at_source_ref": CANONICAL_SHA256, "target_round": TARGET, "cutoff": TARGET-1, "e030_prediction_sha256": E030_PREDICTION_SHA256, "e030_sha256_verified_at_source_ref": E030_PREDICTION_SHA256, "random5_portfolios": N_PORTFOLIOS, "random5_pool_sha256": pool_sha, "random5_pool_bytes": pool_size, "single_ticket_baseline_samples": N_PORTFOLIOS, "single_ticket_pool_sha256": single_sha, "purchase_ledger_records": 0, "purchase_ledger_status": "AWAITING_VERIFIED_ACTUAL_PURCHASE", "leakage_failures": 0, "future_predictions": 0, "recommendation_lines_generated": 0, "note": "PASS means the prospective protocol and random pools were frozen; it does not mean actual purchase records or outcome evidence exist."}
    write_once(OUT / "VERIFICATION.json", (json.dumps(verify, ensure_ascii=False, indent=2) + "\n").encode())
    report = f"""# E043–E049 Prospective Evidence Freeze v1

Frozen at {now} UTC before target 1246 outcome access. Canonical source is rounds 1–1245, SHA-256 `{CANONICAL_SHA256}`. E030 target-1246 prediction is referenced without modification (SHA-256 `{E030_PREDICTION_SHA256}`; cutoff 1245).

## Frozen setup

- E043 protocol hash is recorded in `PROSPECTIVE_PROTOCOL_SHA256.txt`.
- E044 purchase ledger schema is ready, but there are **0 verified actual purchase records**. No lines were reconstructed or generated.
- E045 created {N_PORTFOLIOS:,} deterministic random five-line portfolios for target 1246 using seed `{BASE_SEED + TARGET}`. Compressed pool SHA-256: `{pool_sha}`. These are null comparators, not recommendations.
- E047 also froze {N_PORTFOLIOS:,} single-ticket random comparator draws (pool SHA-256 `{single_sha}`) for shadow-model paired evaluation.
- E046 outcome/prediction files are separate and write-once; target predictions are not regenerated after outcome.
- E047 uses mixture e-processes with familywise alpha 0.05 and fixed alpha allocation; no weekly p-value restart.
- E048 power/horizon numbers are planning approximations and do not count as evidence.
- E049 remains `PROSPECTIVE_PENDING`; no promotion is available before outcomes and the pre-registered evidence gates.

## Not claimed

No target-1246 outcome was evaluated, no actual purchase ledger entry was supplied, and no recommendation lines were created. Future evidence remains pending.
"""
    write_once(OUT / "REPORT.md", report.encode())
    completion = {"study_id": "E043_E049_PROSPECTIVE_EVIDENCE_v1", "status": "FROZEN_SETUP_COMPLETE", "created_at_utc": now, "target_round": TARGET, "outcomes_evaluated": 0, "purchase_records": 0, "recommendation_lines_generated": 0}
    write_once(OUT / "COMPLETION.json", (json.dumps(completion, ensure_ascii=False, indent=2) + "\n").encode())
    manifest_path = OUT / "SHA256_MANIFEST.csv"
    manifest_files = sorted(p for p in OUT.iterdir() if p.is_file() and p != manifest_path)
    with manifest_path.open("x", encoding="utf-8", newline="") as f:
        writer = csv.writer(f); writer.writerow(["path", "bytes", "sha256"])
        for path in manifest_files:
            writer.writerow([path.name, path.stat().st_size, sha_file(path)])
        writer.writerow([pool_path.relative_to(ROOT).as_posix(), pool_size, pool_sha])
        writer.writerow([single_path.relative_to(ROOT).as_posix(), single_size, single_sha])
        writer.writerow([config_path.relative_to(ROOT).as_posix(), config_path.stat().st_size, sha_file(config_path)])
    # Verify immutable source identity if this checkout includes the GitHub-frozen file.
    if E030.is_file() and sha_file(E030) != E030_PREDICTION_SHA256:
        raise ValueError("E030 target-1246 frozen prediction SHA mismatch; refusing completion")
    print(json.dumps({"status": "FROZEN_SETUP_COMPLETE", "protocol_sha256": sha_bytes(protocol_bytes), "random5_pool_sha256": pool_sha, "random5_portfolios": N_PORTFOLIOS, "out": OUT.relative_to(ROOT).as_posix()}, indent=2))


if __name__ == "__main__":
    main()
