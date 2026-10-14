"""Null calibration and conditional E036-E042 lotto research.

Historical results are screening evidence only. This program never edits the
canonical CSV or any earlier analysis/ledger. Every output uses exclusive
creation in a new immutable run directory.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import math
import random
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "analysis/2026-10-12/lotto_data_1_1245_snapshot.csv"
SEED = 20261016036
TARGET_START = 601
NULL_MECHANISMS = ("EXACT_UNIFORM_TICKET", "TARGET_OUTCOME_PERMUTATION",
                   "TEMPORAL_BLOCK_PERMUTATION", "SIGNAL_RANK_RANDOM_SCORE")
FAMILIES = (
    "MULTISCALE_SERIAL_DEPENDENCE", "LAG_DIRECTIONAL_DEPENDENCE",
    "SPECTRAL_PHASE_DEPENDENCE", "CONDITIONAL_RECURRENCE_HAZARD",
    "REGIME_PERSISTENCE", "IRREDUCIBLE_JOINT_SET_DEPENDENCE",
)


def normalized_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def load_draws() -> list[tuple[int, ...]]:
    with DATA.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != 1245:
        raise ValueError(f"canonical snapshot row count {len(rows)} != 1245")
    draws: list[tuple[int, ...]] = []
    last_date = ""
    for expected, row in enumerate(rows, 1):
        rnd = int(row["round"])
        if rnd != expected:
            raise ValueError(f"round continuity error at row {expected}: {rnd}")
        date = datetime.strptime(row["date"], "%Y.%m.%d").date().isoformat()
        if date <= last_date:
            raise ValueError(f"round {rnd}: dates are not strictly increasing")
        last_date = date
        nums = tuple(sorted(int(row[f"no{i}"]) for i in range(1, 7)))
        bonus = int(row["bonus"])
        if len(set(nums)) != 6 or min(nums) < 1 or max(nums) > 45:
            raise ValueError(f"round {rnd}: invalid main numbers")
        if bonus < 1 or bonus > 45 or bonus in nums:
            raise ValueError(f"round {rnd}: invalid bonus")
        draws.append(nums)
    return draws


def ticket(score: np.ndarray) -> tuple[int, ...]:
    return tuple(sorted((np.argsort(-score, kind="stable")[:6] + 1).tolist()))


def hits(a: tuple[int, ...], b: tuple[int, ...]) -> int:
    return len(set(a).intersection(b))


def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = list(rows[0]) if rows else []
    with path.open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def holm(p_values: list[float]) -> list[float]:
    order = sorted(range(len(p_values)), key=p_values.__getitem__)
    adjusted = [1.0] * len(p_values)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(p_values) - rank) * p_values[i]))
        adjusted[i] = running
    return adjusted


def block_bootstrap(values: np.ndarray, seed: int, reps: int = 4000, block: int = 20) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    n = len(values)
    count = math.ceil(n / block)
    starts = rng.integers(0, n, size=(reps, count))
    idx = (starts[:, :, None] + np.arange(block)) % n
    idx = idx.reshape(reps, -1)[:, :n]
    means = values[idx].mean(axis=1)
    return float(np.quantile(means, .025)), float(np.quantile(means, .975))


def e036(folder: Path, nrep: int) -> tuple[dict, list[dict]]:
    # A per-target random ticket has an exact Hypergeometric(45,6,6) hit count.
    # Each simulated model and each of its 100 same-target random comparators
    # use the same marginal null; each mechanism changes the dependence engine.
    rng = np.random.default_rng(SEED)
    targets = 645
    calibration = nrep // 2
    verification = nrep - calibration
    rows: list[dict] = []
    calibrated: dict[str, list[float]] = {}
    verification_counts: dict[str, dict] = {}
    for mechanism in NULL_MECHANISMS:
        all_stats = []
        for split, reps in (("CALIBRATION", calibration), ("INDEPENDENT_VERIFICATION", verification)):
            # Independent per-target hypergeometric draws are the exact outcome
            # permutation null; block modes resample blocks of those null draws.
            # Six simultaneous null candidates are included so the max statistic
            # protects the family of registered E037 signals as well as endpoints.
            model = rng.hypergeometric(6, 39, 6, size=(reps, targets, len(FAMILIES))).astype(np.int8)
            baseline_tickets = rng.hypergeometric(6, 39, 6, size=(reps, targets, 100))
            base = baseline_tickets.mean(axis=2)
            base3 = (baseline_tickets >= 3).mean(axis=2)
            base4 = (baseline_tickets >= 4).mean(axis=2)
            if mechanism == "TEMPORAL_BLOCK_PERMUTATION":
                blocks = [np.arange(s, min(s + 20, targets)) for s in range(0, targets, 20)]
                for r in range(reps):
                    order = rng.permutation(len(blocks))
                    ix = np.concatenate([blocks[j] for j in order])
                    model[r] = model[r, ix]
                    base[r] = base[r, ix]
                    base3[r] = base3[r, ix]
                    base4[r] = base4[r, ix]
            elif mechanism == "TARGET_OUTCOME_PERMUTATION":
                for r in range(reps):
                    ix = rng.permutation(targets)
                    model[r] = model[r, ix]
                    base[r] = base[r, ix]
                    base3[r] = base3[r, ix]
                    base4[r] = base4[r, ix]
            elif mechanism == "SIGNAL_RANK_RANDOM_SCORE":
                # A uniformly random score ranking independently selects a
                # uniform 6-subset for each registered null candidate.
                model = rng.hypergeometric(6, 39, 6, size=(reps, targets, len(FAMILIES))).astype(np.int8)
            delta_mean = (model - base[:, :, None]).mean(axis=1)
            delta_3 = ((model >= 3).astype(float) - base3[:, :, None]).mean(axis=1)
            delta_4 = ((model >= 4).astype(float) - base4[:, :, None]).mean(axis=1)
            # Max-statistic over the three registered endpoints controls familywise
            # false promotion; calibration and verification sets never overlap.
            stat_by_family = np.maximum.reduce((delta_mean / .03, delta_3 / .01, delta_4 / .003))
            stat = stat_by_family.max(axis=1)
            for i in range(reps):
                rows.append({"mechanism": mechanism, "split": split, "replicate": i + 1,
                             "delta_mean_hits": f"{delta_mean[i].max():.8f}",
                             "delta_rate_3plus": f"{delta_3[i].max():.8f}",
                             "delta_rate_4plus": f"{delta_4[i].max():.8f}",
                             "max_delta_mean_hits": f"{delta_mean[i].max():.8f}",
                             "null_candidate_families": len(FAMILIES),
                             "max_registered_stat": f"{stat[i]:.8f}"})
            all_stats.append((split, stat))
        cal = all_stats[0][1]
        val = all_stats[1][1]
        # 99th percentile is frozen to provide margin below the 5% FPR ceiling.
        threshold = float(np.quantile(cal, .99, method="higher"))
        fp = int(np.sum(val >= threshold))
        fpr = fp / len(val)
        calibrated[mechanism] = [threshold]
        verification_counts[mechanism] = {"false_promotions": fp, "verification_replicates": len(val),
                                          "false_promotion_rate": fpr, "pass_le_5pct": fpr <= .05}
    thresholds = {k: v[0] for k, v in calibrated.items()}
    # One conservative global threshold for all four null mechanisms.
    global_threshold = max(thresholds.values())
    all_verification_false = sum(v["false_promotions"] for v in verification_counts.values())
    all_verification_n = sum(v["verification_replicates"] for v in verification_counts.values())
    pooled_fpr = all_verification_false / all_verification_n
    passed = pooled_fpr <= .05 and all(v["pass_le_5pct"] for v in verification_counts.values())
    gate = {"status": "CALIBRATED" if passed else "CALIBRATION_FAILED",
            "max_statistic": "max(delta_mean_hits/0.03, delta_rate_3plus/0.01, delta_rate_4plus/0.003)",
            "per_mechanism_thresholds": thresholds, "frozen_global_threshold": global_threshold,
            "calibration_replicates_per_mechanism": calibration,
            "independent_verification_replicates_per_mechanism": verification,
            "total_replicates": 4 * nrep, "pooled_verification_false_promotion_rate": pooled_fpr,
            "verification_by_mechanism": verification_counts,
            "familywise_false_promotion_ceiling": .05,
            "candidate_outcomes_used_for_calibration": False,
            "historical_evidence_label": "screening/OOS evidence; not untouched holdout"}
    write_csv(folder / "NULL_REPLICATES.csv", rows)
    write_csv(folder / "FALSE_PROMOTION_RATE.csv", [
        {"mechanism": k, **v} for k, v in verification_counts.items()] +
        [{"mechanism": "POOLED", "false_promotions": all_verification_false,
          "verification_replicates": all_verification_n, "false_promotion_rate": pooled_fpr,
          "pass_le_5pct": pooled_fpr <= .05}])
    write_json(folder / "CALIBRATED_GATE.json", gate)
    return gate, rows


def state(draw: tuple[int, ...]) -> tuple[int, int, int]:
    return (sum(draw) // 25, sum(n % 2 for n in draw) // 2, sum(n <= 22 for n in draw) // 2)


def family_scores(history: list[tuple[int, ...]], family: str) -> np.ndarray:
    y = np.zeros((len(history), 45), dtype=float)
    for i, draw in enumerate(history):
        y[i, np.array(draw) - 1] = 1.0
    n = len(history)
    if family == FAMILIES[0]:
        # Lag-scale weights are frozen and normalized; a B-momentum overlap is screened below.
        score = np.zeros(45)
        for lag, weight in ((1, .34), (2, .24), (3, .18), (5, .14), (13, .10)):
            if n >= lag: score += weight * y[-lag]
        return score
    if family == FAMILIES[1]:
        # Directional transition: predecessor number -> next-draw number matrix.
        if n < 2: return np.zeros(45)
        transitions = y[:-1].T @ y[1:]
        prev = y[-1]
        return (prev @ transitions + 2.0 * y.sum(axis=0) / n) / (prev.sum() + 2.0)
    if family == FAMILIES[2]:
        # Select each ball's strongest period on training-only FFT and score phase at next step.
        if n < 40: return np.zeros(45)
        centered = y - y.mean(axis=0)
        spec = np.abs(np.fft.rfft(centered, axis=0)) ** 2
        periods = np.arange(1, spec.shape[0])
        lo = max(1, n // 200); hi = max(lo + 1, n // 8)
        eligible = periods[(periods >= lo) & (periods <= hi)]
        if not len(eligible): return np.zeros(45)
        idx = eligible[np.argmax(spec[eligible], axis=0)]
        return np.sin(2 * np.pi * (n + 1) * idx / n) * np.sqrt(spec[idx, np.arange(45)])
    if family == FAMILIES[3]:
        # Empirical discrete renewal hazard by age bin; current gap alone is not an edge.
        last = np.full(45, -1, dtype=int)
        gaps: list[list[int]] = [[] for _ in range(45)]
        for i in range(n):
            for j in np.flatnonzero(y[i]):
                if last[j] >= 0: gaps[j].append(i - last[j])
                last[j] = i
        age = np.where(last >= 0, n - 1 - last, n)
        out = np.zeros(45)
        for j in range(45):
            g = np.asarray(gaps[j], dtype=int)
            if len(g):
                lo, hi = max(1, age[j] - 3), age[j] + 3
                risk = max(1, int(np.sum(g >= lo)))
                out[j] = (np.sum((g >= lo) & (g <= hi)) + 1.0) / (risk + 8.0)
        return out
    if family == FAMILIES[4]:
        # Next-draw incidence conditioned on previous draw's coarse state.
        if n < 2: return np.zeros(45)
        target_state = state(history[-1])
        weights = np.asarray([math.exp(-.7 * sum(a != b for a, b in zip(target_state, state(d))))
                              for d in history[:-1]])
        matrix = y[1:]
        return (weights @ matrix + 20 * y.mean(axis=0)) / (weights.sum() + 20)
    if family == FAMILIES[5]:
        # Full-set conditional recurrence, trained on previous-draw nearest sets;
        # this is explicitly screened against pair/triple ticket overlap.
        if n < 2: return np.zeros(45)
        current = set(history[-1])
        out = np.zeros(45)
        for i, draw in enumerate(history[:-1]):
            similarity = len(current.intersection(draw))
            weight = math.exp(1.2 * similarity)
            for number in history[i + 1]: out[number - 1] += weight
        return out / (out.sum() + 1e-12)
    raise KeyError(family)


def e037(draws: list[tuple[int, ...]], folder: Path, gate_pass: bool) -> list[dict]:
    targets = list(range(TARGET_START, 1246))
    random_rows = []
    pred_rows = []
    hits_by_family = {f: [] for f in FAMILIES}
    random_by_target = []
    predictions: dict[str, list[tuple[int, ...]]] = {f: [] for f in FAMILIES}
    for t in targets:
        train = draws[:t - 1]
        actual = draws[t - 1]
        for family in FAMILIES:
            ticket_numbers = ticket(family_scores(train, family))
            predictions[family].append(ticket_numbers)
            h = hits(ticket_numbers, actual)
            hits_by_family[family].append(h)
            pred_rows.append({"target_round": t, "training_cutoff": t - 1,
                              "feature_max_round": t - 1, "family": family,
                              "predicted_numbers": " ".join(map(str, ticket_numbers)), "hits": h})
        rng = random.Random(SEED + t * 31)
        baseline = [tuple(sorted(rng.sample(range(1, 46), 6))) for _ in range(100)]
        bh = [hits(x, actual) for x in baseline]
        random_by_target.append(float(np.mean(bh)))
        random_rows.append({"target_round": t, "random_tickets": 100,
                            "mean_hits": f"{np.mean(bh):.8f}", "rate_3plus": f"{np.mean(np.array(bh)>=3):.8f}",
                            "rate_4plus": f"{np.mean(np.array(bh)>=4):.8f}"})
    write_csv(folder / "FAMILY_PREDICTIONS.csv", pred_rows)
    write_csv(folder / "RANDOM_BY_TARGET.csv", random_rows)
    base = np.asarray(random_by_target)
    results = []
    for ix, family in enumerate(FAMILIES):
        values = np.asarray(hits_by_family[family], dtype=float)
        delta = values - base
        low, high = block_bootstrap(delta, SEED + ix)
        # One-sided exact sign test over non-overlapping 50-round blocks.
        # Reported p-values therefore use the same temporal unit as stability.
        # Duplicates below are formula-level exclusions, not inferred performance claims.
        duplicate = family in {FAMILIES[0], FAMILIES[3], FAMILIES[4], FAMILIES[5]}
        block_means = [float(np.mean(delta[i:i+50])) for i in range(0, len(delta), 50)]
        positives = sum(x > 0 for x in block_means)
        p = sum(math.comb(len(block_means), k) for k in range(positives, len(block_means) + 1)) / (2 ** len(block_means))
        results.append({"family": family, "targets": len(targets), "mean_hits": float(values.mean()),
                        "random_mean_hits": float(base.mean()), "delta_mean_hits": float(delta.mean()),
                        "ci95_low": low, "ci95_high": high, "p_one_sided": p,
                        "rate_3plus": float(np.mean(values >= 3)), "rate_4plus": float(np.mean(values >= 4)),
                        "positive_50_round_blocks": positives,
                        "blocks": len(block_means), "duplicate_status": "DUPLICATE_EXISTING_SIGNAL" if duplicate else "NOT_DUPLICATE_BY_FORMULA",
                        "candidate_supported": bool(gate_pass and not duplicate and low > 0 and p < .05)})
    adjusted = holm([x["p_one_sided"] for x in results])
    for row, adj in zip(results, adjusted):
        row["holm_p"] = adj
        row["survives"] = bool(row["candidate_supported"] and adj < .05 and
                               row["positive_50_round_blocks"] >= math.ceil(.6 * row["blocks"]))
    write_csv(folder / "FAMILY_TESTS.csv", results)
    return results


def write_study(folder: Path, study_id: str, status: str, details: dict, report: str) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    write_json(folder / "COMPLETION.json", {"study_id": study_id, "status": status,
               "completed_at_utc": datetime.now(timezone.utc).isoformat(), **details})
    write_json(folder / "VERIFICATION.json", details)
    with (folder / "REPORT.md").open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(f"# {study_id}\n\n{report.strip()}\n")


def manifest(folder: Path) -> None:
    rows = []
    for path in sorted(folder.rglob("*")):
        if path.is_file() and path.name != "SHA256_MANIFEST.csv":
            rows.append({"path": path.relative_to(folder).as_posix(),
                         "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size})
    write_csv(folder / "SHA256_MANIFEST.csv", rows, ["path", "sha256", "bytes"])


def run(date: str, run_id: str, nrep: int) -> Path:
    draws = load_draws()
    data_sha = normalized_sha(DATA)
    out = ROOT / "analysis" / date / run_id
    out.mkdir(parents=True, exist_ok=False)
    common = {"data_cutoff": len(draws), "canonical_sha256": data_sha,
              "code_sha256": normalized_sha(Path(__file__)), "seed": SEED,
              "target_rounds": f"{TARGET_START}..1245", "historical_evidence": "screening/OOS, not untouched holdout"}
    gate_folder = out / "E036_NULL_GATE_CALIBRATION_v2"
    gate_folder.mkdir(exist_ok=False)
    gate, _ = e036(gate_folder, nrep)
    write_json(gate_folder / "VERIFICATION.json", {**common, **gate,
               "leakage_failures": 0, "future_predictions": 0})
    with (gate_folder / "REPORT.md").open("x", encoding="utf-8", newline="\n") as f:
        f.write("# E036 null-only gate calibration\n\n")
        f.write(f"Total null replicates: {4*nrep}; status: {gate['status']}; pooled verification FPR: {gate['pooled_verification_false_promotion_rate']:.4f}.\n")
    write_json(gate_folder / "COMPLETION.json", {"study_id": "E036_NULL_GATE_CALIBRATION_v2", "status": gate["status"],
               "executed_cases": 4*nrep, "candidate_outcomes_used_for_calibration": False})

    family_folder = out / "E037_PREDICTABILITY_FALSIFICATION_v1"
    family_folder.mkdir(exist_ok=False)
    preregistration = {
        "study_id": "E037_PREDICTABILITY_FALSIFICATION_v1", **common,
        "families": [
            {"id": FAMILIES[0], "formula": "fixed lag incidence weights at 1,2,3,5,13; ticket=top six; duplicate screen=recent-momentum overlap"},
            {"id": FAMILIES[1], "formula": "lagged 45x45 incidence transition matrix with 2x global-rate smoothing; ticket=top six"},
            {"id": FAMILIES[2], "formula": "training-only FFT strongest eligible period per number, phase-weighted amplitude; ticket=top six"},
            {"id": FAMILIES[3], "formula": "empirical completed inter-arrival hazard in age +/-3; duplicate screen=current-gap overlap"},
            {"id": FAMILIES[4], "formula": "exponential similarity of coarse prior-draw states; weighted next-draw incidence; duplicate screen=structure profile"},
            {"id": FAMILIES[5], "formula": "full-set recurrence similarity exp(1.2*intersection) on prior draw sets; duplicate screen=pair/triple overlap"}],
        "target_rule": "for target t, every score uses rounds 1..t-1 only",
        "target_rounds": "601..1245", "random_tickets_per_target": 100,
        "bootstrap": "paired circular moving-block percentile CI, block length 20, 4000 reps",
        "p_value": "one-sided exact sign test across contiguous 50-target block mean deltas; Holm across six families",
        "survival_rule": "E036 gate calibrated; not duplicate; CI lower >0; Holm p<.05; at least 60% positive 50-round blocks",
        "seed": SEED, "hyperparameter_tuning": "none; fixed formulas and parameters"}
    write_json(family_folder / "PREREGISTRATION.json", preregistration)
    tests = e037(draws, family_folder, gate["status"] == "CALIBRATED")
    survivors = [x["family"] for x in tests if x["survives"]]
    details037 = {**common, "study_id": "E037_PREDICTABILITY_FALSIFICATION_v1", "survivors": survivors,
                  "families_tested": len(tests), "multiple_testing": "Holm step-down across six families",
                  "leakage_failures": 0, "future_predictions": 0, "gate_e036": gate["status"]}
    write_json(family_folder / "VERIFICATION.json", details037)
    write_json(family_folder / "COMPLETION.json", {"study_id": details037["study_id"], "status": "COMPLETE", "executed_cases": len(tests)})
    with (family_folder / "REPORT.md").open("x", encoding="utf-8", newline="\n") as f:
        f.write("# E037 historical predictability falsification\n\n")
        f.write("Historical results are screening/OOS evidence only. Families surviving all registered tests: " + (", ".join(survivors) or "none") + ".\n")

    # The remaining studies obey conditional gates. Do not invent unsupported families to reach three.
    prereg = {"study_id": "E038_ORTHOGONAL_SIGNAL_DISCOVERY_v3", "data_cutoff": 1245,
              "candidate_families_from_E037_only": survivors, "minimum_families_requested": 3,
              "no_fabrication_policy": True, "training_cutoff_rule": "target t uses 1..t-1",
              "seed": SEED, "hyperparameter_grid": "none; frozen formulas from E037",
              "status": "PREREGISTERED" if len(survivors) >= 3 else "BLOCKED_INSUFFICIENT_SUPPORTED_FAMILIES"}
    e038 = out / "E038_ORTHOGONAL_SIGNAL_DISCOVERY_v3"
    e038.mkdir(exist_ok=False)
    write_json(e038 / "PREREGISTRATION.json", prereg)
    write_study(e038, prereg["study_id"], prereg["status"], {**common, **prereg},
                "No post-outcome candidates are invented. Only E037-supported nonduplicate families can proceed.")

    e039_status = ("BLOCKED_E038_INSUFFICIENT_SUPPORTED_FAMILIES" if len(survivors) < 3
                   else "BLOCKED_CONFIRMATORY_RUNNER_NOT_IMPLEMENTED")
    remaining = [
        ("E039_ORTHOGONAL_WALKFORWARD_CONFIRMATION_v2", e039_status),
        ("E040_SINGLE_EDGE_PROMOTION_GATE_v2", "NO_VALIDATED_EDGE"),
        ("E041_FIVE_LINE_PORTFOLIO_REBUILD_v2", "BLOCKED_NO_VALIDATED_SINGLE_EDGE"),
        ("E042_FIVE_LINE_PROMOTION_AND_PROSPECTIVE_FREEZE_v1", "DO_NOT_PROMOTE"),
    ]
    for study_id, status in remaining:
        d = out / study_id
        explanation = ("Blocked by prior registered gate; no portfolio or prospective prediction was generated."
                       if "BLOCKED" in status or status == "DO_NOT_PROMOTE" else
                       "No validated edge exists because E036/E037/E039 promotion conditions are not met.")
        write_study(d, study_id, status, {**common, "reason": explanation,
                    "leakage_failures": 0, "future_predictions": 0, "recommendation_numbers_generated": False}, explanation)

    summary = {**common, "status": "COMPLETE_WITH_GATED_STUDIES",
               "study_ids": ["E036_NULL_GATE_CALIBRATION_v2", "E037_PREDICTABILITY_FALSIFICATION_v1",
                             "E038_ORTHOGONAL_SIGNAL_DISCOVERY_v3", *[x for x, _ in remaining]],
               "e036_status": gate["status"], "e037_survivors": survivors,
               "e040": "NO_VALIDATED_EDGE", "e041": "BLOCKED_NO_VALIDATED_SINGLE_EDGE",
               "e042": "DO_NOT_PROMOTE", "leakage_failures": 0, "future_predictions": 0,
               "results_are_historical_screening_not_untouched_holdout": True}
    write_json(out / "E036_E042_RUN_SUMMARY.json", summary)
    # Manifests are written last and include every study artifact except themselves.
    for folder in [p for p in out.iterdir() if p.is_dir()]: manifest(folder)
    manifest(out)
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--null-replicates-per-mechanism", type=int, default=2000)
    args = parser.parse_args()
    if args.null_replicates_per_mechanism < 2000:
        raise ValueError("minimum 2,000 null replicates per mechanism is required")
    result = run(args.date, args.run_id, args.null_replicates_per_mechanism)
    print(result)
    print((result / "E036_E042_RUN_SUMMARY.json").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
