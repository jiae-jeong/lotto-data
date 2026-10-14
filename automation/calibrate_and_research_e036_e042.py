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


def e036(folder: Path, nrep: int, draws: list[tuple[int, ...]],
         predictions: dict[str, list[tuple[int, ...]]]) -> tuple[dict, list[dict]]:
    """Calibrate on four genuinely distinct generators and never on aligned outcomes.

    The permutation mechanisms use E037's frozen pre-target tickets but randomly
    reassign observed outcomes; they do not inspect the aligned candidate results.
    The two synthetic mechanisms use exact uniform-ticket null draws.
    """
    rng = np.random.default_rng(SEED)
    targets = 1245 - TARGET_START + 1
    family_count = len(FAMILIES)
    calibration = nrep // 2
    verification = nrep - calibration
    target_ix = np.arange(targets)
    outcomes = np.zeros((targets, 45), dtype=np.int8)
    pred = np.zeros((family_count, targets, 45), dtype=np.int8)
    random_tickets = np.zeros((targets, 100, 45), dtype=np.int8)
    for i, t in enumerate(range(TARGET_START, 1246)):
        for number in draws[t - 1]: outcomes[i, number - 1] = 1
        for fi, family in enumerate(FAMILIES):
            for number in predictions[family][i]: pred[fi, i, number - 1] = 1
        rr = random.Random(SEED + t * 31)
        for j in range(100):
            for number in rr.sample(range(1, 46), 6): random_tickets[i, j, number - 1] = 1

    # Pairwise candidate/outcome and random-ticket/outcome hit matrices permit
    # actual target-label permutation and block permutation without resampling
    # or changing candidate predictions.
    candidate_hit = (pred.reshape(family_count * targets, 45) @ outcomes.T).reshape(family_count, targets, targets)
    random_hit = (random_tickets.reshape(targets * 100, 45) @ outcomes.T).reshape(targets, 100, targets)
    random_mean = random_hit.mean(axis=1)
    random_3 = (random_hit >= 3).mean(axis=1)
    random_4 = (random_hit >= 4).mean(axis=1)
    block_groups = [np.arange(s, min(s + 20, targets)) for s in range(0, targets, 20)]

    def statistic(delta_mean: np.ndarray, delta_3: np.ndarray, delta_4: np.ndarray) -> np.ndarray:
        by_family = np.maximum.reduce((delta_mean / .03, delta_3 / .01, delta_4 / .003))
        return by_family.max(axis=1)

    rows: list[dict] = []
    calibrated: dict[str, float] = {}
    verification_counts: dict[str, dict] = {}
    for mechanism in NULL_MECHANISMS:
        split_stats: dict[str, np.ndarray] = {}
        for split, reps in (("CALIBRATION", calibration), ("INDEPENDENT_VERIFICATION", verification)):
            dm = np.zeros((reps, family_count)); d3 = np.zeros_like(dm); d4 = np.zeros_like(dm)
            for r in range(reps):
                if mechanism in {"EXACT_UNIFORM_TICKET", "SIGNAL_RANK_RANDOM_SCORE"}:
                    if mechanism == "EXACT_UNIFORM_TICKET":
                        # Exact ticket/draw null: hypergeometric hit counts, six
                        # independent registered families, 100 random comparator lines.
                        model_hits = rng.hypergeometric(6, 39, 6, size=(targets, family_count))
                        baseline_hits = rng.hypergeometric(6, 39, 6, size=(targets, 100))
                        dm[r] = model_hits.mean(axis=0) - baseline_hits.mean()
                        d3[r] = (model_hits >= 3).mean(axis=0) - (baseline_hits >= 3).mean()
                        d4[r] = (model_hits >= 4).mean(axis=0) - (baseline_hits >= 4).mean()
                    else:
                        # Independent random-score rankings select actual six-number
                        # tickets against the observed target draws; comparator tickets
                        # are the same 100 random lines used for each target.
                        scores = rng.random((family_count, targets, 45))
                        chosen = np.argpartition(scores, -6, axis=2)[:, :, -6:]
                        target_outcomes = np.broadcast_to(outcomes[None, :, :],
                                                         (family_count, targets, 45))
                        model_hits = np.take_along_axis(target_outcomes, chosen, axis=2).sum(axis=2)
                        base = random_hit[target_ix, :, target_ix]
                        dm[r] = model_hits.mean(axis=1) - base.mean(axis=1).mean()
                        d3[r] = (model_hits >= 3).mean(axis=1) - (base >= 3).mean(axis=1).mean()
                        d4[r] = (model_hits >= 4).mean(axis=1) - (base >= 4).mean(axis=1).mean()
                else:
                    if mechanism == "TARGET_OUTCOME_PERMUTATION":
                        outcome_order = rng.permutation(targets)
                    else:
                        order = rng.permutation(len(block_groups))
                        outcome_order = np.concatenate([block_groups[j] for j in order])
                    model_hits = candidate_hit[:, target_ix, outcome_order]
                    base_mean = random_mean[target_ix, outcome_order]
                    base3 = random_3[target_ix, outcome_order]
                    base4 = random_4[target_ix, outcome_order]
                    dm[r] = model_hits.mean(axis=1) - base_mean.mean()
                    d3[r] = (model_hits >= 3).mean(axis=1) - base3.mean()
                    d4[r] = (model_hits >= 4).mean(axis=1) - base4.mean()
            stats = statistic(dm, d3, d4)
            split_stats[split] = stats
            for i in range(reps):
                rows.append({"mechanism": mechanism, "split": split, "replicate": i + 1,
                             "max_delta_mean_hits": f"{dm[i].max():.8f}",
                             "max_delta_rate_3plus": f"{d3[i].max():.8f}",
                             "max_delta_rate_4plus": f"{d4[i].max():.8f}",
                             "null_candidate_families": family_count,
                             "max_registered_stat": f"{stats[i]:.8f}"})
        threshold = float(np.quantile(split_stats["CALIBRATION"], .99, method="higher"))
        val = split_stats["INDEPENDENT_VERIFICATION"]
        false_count = int(np.sum(val >= threshold)); fpr = false_count / len(val)
        calibrated[mechanism] = threshold
        verification_counts[mechanism] = {"false_promotions": false_count, "verification_replicates": len(val),
                                          "false_promotion_rate": fpr, "pass_le_5pct": fpr <= .05}
    thresholds = dict(calibrated)
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
            "calibration_uses_unpermuted_candidate_target_pairing": False,
            "permutation_sources": "Observed target outcomes are permuted or block-permuted relative to frozen t-1 candidate tickets; unpermuted candidate hit alignment is not scored.",
            "supersedes_prior_run": "gha_38518699993_1",
            "supersession_reason": "The earlier run used hypergeometric hit-array permutations rather than distinct outcome-level permutation and random-score generators.",
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


def build_family_predictions(draws: list[tuple[int, ...]]) -> dict[str, list[tuple[int, ...]]]:
    predictions: dict[str, list[tuple[int, ...]]] = {f: [] for f in FAMILIES}
    for t in range(TARGET_START, 1246):
        train = draws[:t - 1]
        for family in FAMILIES:
            predictions[family].append(ticket(family_scores(train, family)))
    return predictions


def e037(draws: list[tuple[int, ...]], folder: Path, gate_pass: bool,
         predictions: dict[str, list[tuple[int, ...]]]) -> list[dict]:
    targets = list(range(TARGET_START, 1246))
    random_rows = []
    pred_rows = []
    hits_by_family = {f: [] for f in FAMILIES}
    random_by_target = []
    for target_index, t in enumerate(targets):
        train = draws[:t - 1]
        actual = draws[t - 1]
        for family in FAMILIES:
            ticket_numbers = predictions[family][target_index]
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
    predictions = build_family_predictions(draws)
    gate, _ = e036(gate_folder, nrep, draws, predictions)
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
    tests = e037(draws, family_folder, gate["status"] == "CALIBRATED", predictions)
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
               "supersedes_prior_run": "gha_38518699993_1",
               "supersession_reason": "E036 null mechanisms were reimplemented at outcome/ticket level; prior run is retained but not treated as final calibration.",
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
