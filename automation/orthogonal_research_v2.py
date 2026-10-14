"""Pre-registered E030-E035 prospective freeze, orthogonal signal and null-control studies."""
from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import random
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "analysis/2026-10-12/lotto_data_1_1245_snapshot.csv"
B_CACHE = ROOT / "analysis/2026-10-12/REGIME_DYNAMIC_NESTED_v1/base_predictions_reused.csv"
PREREG = ROOT / "automation/orthogonal_research_v2_prereg.json"
E026_PRED = ROOT / "analysis/2026-10-14/E026_INDEPENDENT_MODEL_WALKFORWARD_v1/PREDICTIONS.csv"
E026_SIGNAL_IDS = ("CALENDAR_SEASON_CONDITIONAL_v1", "PREVIOUS_SUM_REGIME_CONDITIONAL_v1")
B_MODELS = ("long_frequency", "current_gap", "frequency_plus_gap", "recent_momentum",
            "structure_profile", "pair_association", "triple_association", "combined_equal_rank")
FAMILIES = ("CROSS_FIT_RESIDUAL_SIGNAL", "DRAW_STATE_TRANSITION",
            "ONLINE_CHANGE_POINT_SCORE", "DIRICHLET_GAP_TICKET_GENERATOR")


def sha(path: Path) -> str:
    data = path.read_bytes()
    if path.suffix.lower() in {".csv", ".json", ".md", ".py", ".txt", ".yml", ".yaml"}:
        data = data.replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def raw_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = fields or (list(rows[0]) if rows else [])
    with path.open("x", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="raise")
        w.writeheader(); w.writerows(rows)


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as f:
        json.dump(value, f, ensure_ascii=False, indent=2); f.write("\n")


def load_data() -> list[dict]:
    rows = read_csv(DATA)
    if len(rows) != 1245:
        raise ValueError(f"canonical snapshot rows={len(rows)}; expected 1245")
    out = []
    for expected, row in enumerate(rows, 1):
        rnd = int(row["round"])
        if rnd != expected:
            raise ValueError(f"round continuity: row {expected} has round {rnd}")
        date = datetime.strptime(row["date"], "%Y.%m.%d").date()
        nums = tuple(int(row[f"no{i}"]) for i in range(1, 7))
        bonus = int(row["bonus"])
        if len(set(nums)) != 6 or any(n < 1 or n > 45 for n in nums):
            raise ValueError(f"round {rnd}: invalid main numbers {nums}")
        if bonus < 1 or bonus > 45 or bonus in nums:
            raise ValueError(f"round {rnd}: invalid bonus {bonus}")
        if out and date <= out[-1]["date"]:
            raise ValueError(f"round {rnd}: date not strictly increasing")
        out.append({"round": rnd, "date": date, "numbers": tuple(sorted(nums)), "bonus": bonus})
    return out


def parse_nums(value: str) -> tuple[int, ...]:
    nums = tuple(sorted(int(v) for v in value.replace(",", " ").split()))
    if len(nums) != 6 or len(set(nums)) != 6 or min(nums) < 1 or max(nums) > 45:
        raise ValueError(f"invalid cached ticket: {value!r}")
    return nums


def load_b() -> dict[tuple[int, str], tuple[int, ...]]:
    lookup = {}
    for row in read_csv(B_CACHE):
        t = int(row["target_round"]); model = row["model"]
        if model in B_MODELS:
            key = (t, model)
            if key in lookup: raise ValueError(f"duplicate B cache key {key}")
            if int(row["training_through_round"]) != t - 1:
                raise ValueError(f"B cache leakage at target {t}")
            lookup[key] = parse_nums(row["predicted_numbers"])
    for t in range(601, 1246):
        for model in B_MODELS:
            if (t, model) not in lookup: raise ValueError(f"missing B cache {t}/{model}")
    return lookup


def _sum_bin(total: int) -> int:
    return 0 if total < 120 else 1 if total < 145 else 2 if total < 170 else 3


def _season(month: int) -> int:
    return 0 if month in (12, 1, 2) else 1 if month in (3, 4, 5) else 2 if month in (6, 7, 8) else 3


def _ticket(scores: np.ndarray) -> tuple[int, ...]:
    # Stable, frozen tie break: higher score, then lower number.
    return tuple(sorted((np.argsort(-scores, kind="stable")[:6] + 1).tolist()))


def _state(nums: tuple[int, ...]) -> tuple[int, int, int, int]:
    total = sum(nums); odd = sum(n % 2 for n in nums); low = sum(n <= 22 for n in nums)
    consec = sum(b == a + 1 for a, b in zip(nums, nums[1:]))
    return (_sum_bin(total), 0 if odd <= 2 else 1 if odd <= 4 else 2,
            0 if low <= 2 else 1 if low <= 4 else 2,
            0 if consec == 0 else 1 if consec == 1 else 2)


def _pearson(a: np.ndarray, b: np.ndarray) -> float:
    if float(np.std(a)) == 0.0 or float(np.std(b)) == 0.0: return 0.0
    return float(np.corrcoef(a, b)[0, 1])


def _crossfit_residual_scores(draws: list[dict], b: dict, target: int,
                              precomputed: dict[int, np.ndarray]) -> np.ndarray:
    # Each residual for historical round u was generated by a B-only ridge fit through u-1.
    regime = _sum_bin(sum(draws[target - 2]["numbers"]))
    selected = [u for u in range(201, target) if _sum_bin(sum(draws[u - 2]["numbers"])) == regime]
    if not selected: selected = list(range(201, target))
    if not selected:
        raise ValueError(f"no prior cross-fit residuals available at target {target}")
    return np.mean(np.stack([precomputed[u] for u in selected]), axis=0)


def _prequential_residuals(draws: list[dict], b: dict) -> dict[int, np.ndarray]:
    # Sufficient statistics keep each B-only model fit strictly before its target.
    xtx = np.zeros((8, 8), dtype=float); xty = np.zeros((8,), dtype=float)
    ridge = np.eye(8) * 20.0; ridge[0, 0] = 0.0
    out = {}
    # Frozen B OOS predictions begin at target 201 in the preserved cache.
    for u in range(201, 1245):
        X = np.zeros((45, 8), dtype=float); X[:, 0] = 1.0
        for j, model in enumerate(B_MODELS[:7], 1):
            for n in b[u, model]: X[n - 1, j] = 1.0
        if u == 201:
            predicted = np.full(45, 6.0 / 45.0)
        else:
            beta = np.linalg.solve(xtx + ridge, xty)
            predicted = np.clip(X @ beta, 0.0, 1.0)
        y = np.zeros(45); y[np.array(draws[u - 1]["numbers"]) - 1] = 1.0
        out[u] = y - predicted
        xtx += X.T @ X; xty += X.T @ y
    return out


def _transition_scores(draws: list[dict], target: int) -> np.ndarray:
    current = _state(draws[target - 2]["numbers"])
    numerator = np.zeros(45); denominator = 0.0
    global_counts = np.zeros(45)
    for u in range(2, target):
        previous = _state(draws[u - 2]["numbers"])
        distance = sum(a != b for a, b in zip(current, previous))
        weight = 0.5 ** distance
        denominator += weight
        for n in draws[u - 1]["numbers"]: numerator[n - 1] += weight
        for n in draws[u - 1]["numbers"]: global_counts[n - 1] += 1
    global_rate = global_counts / max(1, target - 2)
    return (numerator + 30.0 * global_rate) / (denominator + 30.0)


def _change_point_scores(draws: list[dict], target: int) -> np.ndarray:
    history = draws[max(0, target - 1 - 300):target - 1]
    n = len(history); scores = np.zeros(45)
    if n < 80: return scores
    y = np.zeros((n, 45), dtype=np.int8)
    for i, d in enumerate(history): y[i, np.array(d["numbers"]) - 1] = 1
    prefix = np.vstack([np.zeros(45), np.cumsum(y, axis=0)])
    total = prefix[-1]
    for j in range(45):
        best_gain = 0.0; best_diff = 0.0
        for split in range(40, n - 39):
            a = int(prefix[split, j]); bcount = int(total[j] - a)
            n1, n2 = split, n - split
            p0 = (a + bcount) / n
            p1 = a / n1; p2 = bcount / n2
            def ll(k, m, p):
                p = min(1 - 1e-12, max(1e-12, p))
                return k * math.log(p) + (m - k) * math.log(1 - p)
            gain = 2.0 * (ll(a, n1, p1) + ll(bcount, n2, p2) - ll(a + bcount, n, p0))
            if gain > best_gain + 1e-12:
                best_gain = gain; best_diff = p2 - p1
        if best_gain > math.log(n): scores[j] = best_diff * math.sqrt(2.0 * best_gain)
    return scores


def _gap_ticket(draws: list[dict], target: int, seed: int, candidates: int = 2000) -> tuple[int, ...]:
    window = draws[max(0, target - 1 - 300):target - 1]
    gap_rows = []
    for d in window:
        nums = d["numbers"]
        gap_rows.append((nums[0] - 1, *(b - a - 1 for a, b in zip(nums, nums[1:])), 45 - nums[-1]))
    means = np.mean(np.asarray(gap_rows, dtype=float), axis=0) if gap_rows else np.full(7, 39 / 7)
    alpha = 1.0 + 20.0 * means / 39.0
    rng = random.Random(seed + target)
    best = None; best_score = -math.inf
    for _ in range(candidates):
        nums = tuple(sorted(rng.sample(range(1, 46), 6)))
        gaps = (nums[0] - 1, *(b - a - 1 for a, b in zip(nums, nums[1:])), 45 - nums[-1])
        score = math.lgamma(40) - sum(math.lgamma(g + 1) for g in gaps)
        score += sum(math.lgamma(float(alpha[j]) + gaps[j]) - math.lgamma(float(alpha[j])) for j in range(7))
        score -= math.lgamma(float(alpha.sum()) + 39) - math.lgamma(float(alpha.sum()))
        if score > best_score + 1e-12 or (abs(score - best_score) <= 1e-12 and (best is None or nums < best)):
            best, best_score = nums, score
    assert best is not None
    return best


def _candidate_predictions(draws: list[dict], b: dict) -> dict[tuple[int, str], tuple[int, ...]]:
    residuals = _prequential_residuals(draws, b)
    out = {}
    for t in range(601, 1246):
        residual = _crossfit_residual_scores(draws, b, t, residuals)
        transition = _transition_scores(draws, t)
        cp = _change_point_scores(draws, t)
        gap = _gap_ticket(draws, t, 2026101604)
        out[t, FAMILIES[0]] = _ticket(residual)
        out[t, FAMILIES[1]] = _ticket(transition)
        out[t, FAMILIES[2]] = _ticket(cp)
        out[t, FAMILIES[3]] = gap
    return out


def _candidate_scores(draws: list[dict], b: dict, t: int, residuals: dict[int, np.ndarray]) -> dict[str, np.ndarray]:
    return {
        FAMILIES[0]: _crossfit_residual_scores(draws, b, t, residuals),
        FAMILIES[1]: _transition_scores(draws, t),
        FAMILIES[2]: _change_point_scores(draws, t),
    }


def _make_random(draws: list[dict], seed: int, reps: int = 100) -> dict[int, list[tuple[int, ...]]]:
    out = {}
    for t in range(601, 1246):
        rng = random.Random(seed + t * 1009)
        out[t] = [tuple(sorted(rng.sample(range(1, 46), 6))) for _ in range(reps)]
    return out


def _hits(ticket: tuple[int, ...], actual: tuple[int, ...]) -> int:
    return len(set(ticket) & set(actual))


def _metrics(hits: list[int]) -> dict:
    a = np.asarray(hits, dtype=float); n = len(a)
    return {"n": n, "mean_hits": float(a.mean()), "variance_hits": float(a.var()),
            "hits_0": int(np.sum(a == 0)), "hits_1": int(np.sum(a == 1)),
            "hits_2": int(np.sum(a == 2)), "hits_3": int(np.sum(a == 3)),
            "hits_4": int(np.sum(a == 4)), "hits_5": int(np.sum(a == 5)), "hits_6": int(np.sum(a == 6)),
            "rate_2plus": float(np.mean(a >= 2)), "rate_3plus": float(np.mean(a >= 3)),
            "rate_4plus": float(np.mean(a >= 4)), "rate_5plus": float(np.mean(a >= 5)),
            "rate_6": float(np.mean(a == 6))}


def _bootstrap(d: np.ndarray, seed: int, reps: int = 2000, block: int = 20) -> dict:
    rng = np.random.default_rng(seed); n = len(d); blocks = math.ceil(n / block)
    starts = rng.integers(0, n, size=(reps, blocks))
    offsets = np.arange(block); indices = (starts[:, :, None] + offsets) % n
    indices = indices.reshape(reps, -1)[:, :n]
    draws = d[indices].mean(axis=1)
    return {"estimate": float(d.mean()), "ci95_low": float(np.quantile(draws, .025)),
            "ci95_high": float(np.quantile(draws, .975)),
            "p_greater": float((1 + np.sum(draws <= 0)) / (reps + 1)),
            "bootstrap_reps": reps, "block_length": block}


def _holm(pvals: list[float]) -> list[float]:
    order = sorted(range(len(pvals)), key=lambda i: pvals[i]); m = len(pvals); adj = [1.0] * m; running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (m - rank) * pvals[i])); adj[i] = running
    return adj


def _write_completion(folder: Path, study: str, cases: int, extra: dict | None = None) -> None:
    write_json(folder / "COMPLETION.json", {"study_id": study, "status": "COMPLETE",
        "executed_cases": cases, "completed_at_utc": datetime.now(timezone.utc).isoformat(), **(extra or {})})


def _write_report(folder: Path, title: str, body: str) -> None:
    with (folder / "REPORT.md").open("x", encoding="utf-8", newline="\n") as f:
        f.write(f"# {title}\n\n{body.strip()}\n")


def _make_e030(draws: list[dict], date_root: Path) -> int:
    folder = date_root / "E030_PROSPECTIVE_SIGNAL_FREEZE_v1"
    folder.mkdir(parents=True, exist_ok=False)
    config_sha = sha(PREREG); code_sha = sha(Path(__file__))
    last_date = draws[-1]["date"]; target_date = last_date + timedelta(days=7)
    current_season = _season(target_date.month); global_rate = np.zeros(45); seasonal = np.zeros(45)
    season_count = 0; reg = _sum_bin(sum(draws[-1]["numbers"])); conditioned = np.zeros(45); reg_count = 0
    for i, d in enumerate(draws):
        for n in d["numbers"]: global_rate[n - 1] += 1
        if _season(d["date"].month) == current_season:
            season_count += 1
            for n in d["numbers"]: seasonal[n - 1] += 1
        if i > 0 and _sum_bin(sum(draws[i - 1]["numbers"])) == reg:
            reg_count += 1
            for n in d["numbers"]: conditioned[n - 1] += 1
    global_rate /= len(draws)
    seasonal_scores = (seasonal + 30.0 * global_rate) / (season_count + 30.0)
    sum_scores = (conditioned + 20.0 * global_rate) / (reg_count + 20.0)
    signals = [
        {"signal": E026_SIGNAL_IDS[0], "formula_version": "E025_FROZEN_v1", "numbers": _ticket(seasonal_scores),
         "score_order": (np.argsort(-seasonal_scores, kind="stable") + 1).tolist()},
        {"signal": E026_SIGNAL_IDS[1], "formula_version": "E025_FROZEN_v1", "numbers": _ticket(sum_scores),
         "score_order": (np.argsort(-sum_scores, kind="stable") + 1).tolist()},
    ]
    frozen = {"status": "FROZEN_PROSPECTIVE_SHADOW_ONLY", "target_round": 1246,
        "training_through_round": 1245, "canonical_data_sha256": sha(DATA),
        "config_sha256": config_sha, "code_sha256": code_sha,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "target_draw_date_assumption": target_date.isoformat(), "signals": signals,
        "editing_policy": "immutable after generation; corrections require a new version and reason",
        "purchase_recommendation": False}
    write_json(folder / "FROZEN_SIGNALS_1246.json", frozen)
    pred_sha = sha(folder / "FROZEN_SIGNALS_1246.json")
    write_csv(folder / "PROSPECTIVE_LEDGER.csv", [{"target_round": 1246, "training_through_round": 1245,
        "signal": x["signal"], "model_version": x["formula_version"], "prediction_file": "FROZEN_SIGNALS_1246.json",
        "prediction_sha256": pred_sha, "generated_at_utc": frozen["generated_at_utc"],
        "status": "PENDING_DRAW", "actual_numbers": "", "hits": "", "result": ""} for x in signals])
    write_json(folder / "VERIFICATION.json", {"status": "PASS", "frozen_signals": 2,
        "target_round": 1246, "training_through_round": 1245, "config_sha256": config_sha,
        "code_sha256": code_sha, "prediction_sha256": pred_sha, "leakage_failures": 0,
        "future_predictions": 0, "purchase_recommendation": False})
    _write_report(folder, "E030 — Prospective signal freeze", "The two E026 independence survivors were frozen without retuning. A shadow-only forecast ledger is pending the next draw; the forecast is not a purchase recommendation.")
    return 2


def _candidate_rank_scores(draws: list[dict], b: dict, predictions: dict, target: int, family: str) -> np.ndarray:
    # For ticket-output families, use a deterministic membership rank (selected=1, unselected=0).
    scores = np.zeros(45)
    for n in predictions[target, family]: scores[n - 1] = 1.0
    return scores


def _screen_and_write_e031(draws, b, predictions, folder: Path) -> list[str]:
    rows = []; survivors = []
    for family in FAMILIES:
        corr_by_b = []; jac_by_b = []
        for model in B_MODELS:
            corr = []; jac = []
            for t in range(601, 1246):
                ticket = set(predictions[t, family]); bticket = set(b[t, model])
                ranks = np.empty(45); ordered = sorted(range(1, 46), key=lambda n: (-float(n in ticket), n))
                for rank, n in enumerate(ordered, 1): ranks[n - 1] = rank
                mask = np.array([float(n in bticket) for n in range(1, 46)])
                corr.append(abs(_pearson(ranks, mask)))
                jac.append(len(ticket & bticket) / len(ticket | bticket))
            corr_by_b.append(float(np.mean(corr))); jac_by_b.append(float(np.mean(jac)))
        avg_corr=float(np.mean(corr_by_b)); mean_j=float(np.mean(jac_by_b)); max_j=float(np.max(jac_by_b))
        keep=avg_corr < .20 and mean_j < .20 and max_j < .35
        if keep: survivors.append(family)
        rows.append({"signal": family, "targets": 645, "mean_abs_ticket_membership_corr": avg_corr,
            "mean_top6_jaccard": mean_j, "max_component_mean_jaccard": max_j,
            "status": "SURVIVES_INDEPENDENCE_SCREEN" if keep else "DROPPED_AS_B_REDUNDANT"})
    write_csv(folder / "INDEPENDENCE_SCREEN.csv", rows)
    pred_rows=[]
    for t in range(601,1246):
        for family in FAMILIES:
            ticket=predictions[t,family]
            pred_rows.append({"target_round":t,"training_through_round":t-1,"signal":family,
                "predicted_numbers":" ".join(map(str,ticket)),"future_prediction":False})
    write_csv(folder / "PREDICTIONS.csv", pred_rows)
    write_json(folder / "VERIFICATION.json", {"status":"PASS","target_count":645,"candidate_families":4,
        "survivors":survivors,"cutoff_violations":0,"future_predictions":0,
        "screen_uses_target_outcomes":False})
    return survivors


def _e032_negative_controls(draws, b, predictions, random_tickets, folder: Path) -> dict:
    # Four controls each pass all four candidate families through the same paired tests and
    # family-wise correction used for real candidates; no candidate is selected on test outcomes.
    targets=np.arange(601,1246); actual=np.array([draws[t-1]["numbers"] for t in targets],dtype=int)
    types=("PER_NUMBER_LABEL_PERMUTATION","WHOLE_DRAW_TARGET_SHUFFLE","UNINFORMATIVE_RANDOM_FEATURES","B_DISTRIBUTION_SYNTHETIC_SCORES")
    rows=[]; replicate_rows=[]
    for ci, control in enumerate(types):
        promoted=0; tested=0
        for rep in range(100):
            rng=np.random.default_rng(2026101605+ci*10000+rep)
            if control == "PER_NUMBER_LABEL_PERMUTATION":
                incidence=np.zeros((len(targets),45),dtype=np.int8)
                for i,row in enumerate(actual): incidence[i,np.asarray(row)-1]=1
                for n in range(45): incidence[:,n]=incidence[rng.permutation(len(targets)),n]
                ctrl_actual=np.zeros((len(targets),6),dtype=int)
                for i,row in enumerate(incidence):
                    ranked=sorted(range(45),key=lambda n:(-int(row[n]),float(rng.random()),n))
                    ctrl_actual[i]=np.asarray(sorted(n+1 for n in ranked[:6]))
            elif control == "WHOLE_DRAW_TARGET_SHUFFLE":
                ctrl_actual=actual[rng.permutation(len(actual))]
            else:
                ctrl_actual=actual
            control_predictions={}
            candidate_hits=np.zeros((len(targets),4),dtype=float)
            for i,t in enumerate(targets):
                for j,f in enumerate(FAMILIES):
                    if control == "B_DISTRIBUTION_SYNTHETIC_SCORES":
                        bvote=np.zeros(45)
                        for model in B_MODELS:
                            for n in b[t,model]: bvote[n-1]+=1
                        synthetic=rng.permutation(bvote)
                        order=np.argsort(-synthetic,kind="stable")
                        ticket=tuple(sorted((order[:6]+1).tolist()))
                    elif control == "UNINFORMATIVE_RANDOM_FEATURES":
                        random_scores=rng.normal(size=45)
                        ticket=_ticket(random_scores)
                    else:
                        ticket=predictions[t,f]
                    candidate_hits[i,j]=_hits(ticket,tuple(ctrl_actual[i]))
            rhits=np.array([[_hits(ticket,tuple(ctrl_actual[i])) for ticket in random_tickets[int(t)]] for i,t in enumerate(targets)],dtype=float)
            rmean=rhits.mean(axis=1); r3=np.mean(rhits>=3,axis=1)
            pair=[]
            for j,f in enumerate(FAMILIES):
                d=candidate_hits[:,j]-rmean; d3=(candidate_hits[:,j]>=3).astype(float)-r3
                boot=_bootstrap(d,2026101605+ci*10000+rep*10+j,reps=250,block=20)
                boot3=_bootstrap(d3,2026101606+ci*10000+rep*10+j,reps=250,block=20)
                pair.append((boot,boot3,d,d3))
            adj=_holm([x[0]["p_greater"] for x in pair])
            promoted_this_rep=False; promoted_families=[]
            for j,(boot,boot3,d,d3) in enumerate(pair):
                block_means=[float(np.mean(d[k:min(k+100,len(d))])) for k in range(0,len(d),100)]
                leave_blocks=[]
                for start in range(0,len(d),50):
                    mask=np.ones(len(d),dtype=bool); mask[start:min(start+50,len(d))]=False
                    leave_blocks.append(float(np.mean(d[mask])))
                passed=(boot["ci95_low"]>0 and adj[j]<.05 and boot3["estimate"]>=-.01 and
                    boot3["ci95_low"]>=-.02 and sum(x>0 for x in block_means)/len(block_means)>=.60 and
                    all(x>0 for x in leave_blocks))
                promoted_this_rep |= passed
                if passed: promoted_families.append(FAMILIES[j])
                replicate_rows.append({"control":control,"replicate":rep+1,"signal":FAMILIES[j],
                    "mean_delta":boot["estimate"],"mean_ci95_low":boot["ci95_low"],"mean_ci95_high":boot["ci95_high"],
                    "p_raw":boot["p_greater"],"p_holm":adj[j],"rate_3plus_delta":boot3["estimate"],
                    "rate_3plus_ci95_low":boot3["ci95_low"],"passed_same_promotion_gate":passed})
                tested += 1
            if promoted_this_rep: promoted+=1
            replicate_rows.append({"control":control,"replicate":rep+1,"signal":"ANY_FAMILY",
                "mean_delta":"","mean_ci95_low":"","mean_ci95_high":"","p_raw":"","p_holm":"",
                "rate_3plus_delta":"","rate_3plus_ci95_low":"","passed_same_promotion_gate":promoted_this_rep,
                "promoted_families":";".join(promoted_families)})
        rows.append({"control":control,"replicates":100,"candidate_tests":tested,
            "false_promotions":promoted,"false_promotion_rate":promoted/100,
            "maximum_allowed_rate":.05,
            "status":"PASS" if promoted/100<=.05 else "FAIL"})
    write_csv(folder/"NEGATIVE_CONTROL_RESULTS.csv",rows)
    write_csv(folder/"NEGATIVE_CONTROL_REPLICATES.csv",replicate_rows, fields=["control","replicate","signal",
        "mean_delta","mean_ci95_low","mean_ci95_high","p_raw","p_holm","rate_3plus_delta",
        "rate_3plus_ci95_low","passed_same_promotion_gate","promoted_families"])
    return {"controls":rows,"all_within_limit":all(x["status"]=="PASS" for x in rows)}


def _e033_metrics(draws,b,predictions,survivors,random_tickets,folder:Path):
    rows=[]; paired=[]; baseline=[]; random_rows=[]; blocks=[]; influence=[]; predictions_out=[]
    targets=range(601,1246)
    for t in targets:
        actual=draws[t-1]["numbers"]
        rh=[_hits(ticket,actual) for ticket in random_tickets[t]]
        random_rows.extend({"target_round":t,"random_id":i+1,"ticket":" ".join(map(str,ticket)),"hits":h}
                           for i,(ticket,h) in enumerate(zip(random_tickets[t],rh)))
        baseline.append({"target_round":t,"random_mean_hits":float(np.mean(rh)),
            "random_rate_3plus":float(np.mean(np.array(rh)>=3)),"random_rate_4plus":float(np.mean(np.array(rh)>=4))})
        for model in B_MODELS:
            hits=_hits(b[t,model],actual)
            predictions_out.append({"target_round":t,"training_through_round":t-1,"model":model,
                "predicted_numbers":" ".join(map(str,b[t,model])),"hits":hits})
        for sig in E026_SIGNAL_IDS:
            pass
        for family in survivors:
            ticket=predictions[t,family]; h=_hits(ticket,actual)
            paired.append({"target_round":t,"signal":family,"hits":h,
                "random_mean_hits":float(np.mean(rh)),"rate_3plus":int(h>=3),
                "random_rate_3plus":float(np.mean(np.array(rh)>=3)),
                "rate_4plus":int(h>=4),"random_rate_4plus":float(np.mean(np.array(rh)>=4))})
            predictions_out.append({"target_round":t,"training_through_round":t-1,"model":family,
                "predicted_numbers":" ".join(map(str,ticket)),"hits":h})
    bysig={s:[x for x in paired if x["signal"]==s] for s in survivors}
    for s,rr in bysig.items():
        h=np.array([x["hits"] for x in rr],dtype=float); r=np.array([x["random_mean_hits"] for x in rr])
        d=h-r; b3=np.array([x["rate_3plus"]-x["random_rate_3plus"] for x in rr]); b4=np.array([x["rate_4plus"]-x["random_rate_4plus"] for x in rr])
        boot=_bootstrap(d,2026101601+len(rows)); boot3=_bootstrap(b3,2026101701+len(rows)); boot4=_bootstrap(b4,2026101801+len(rows))
        m=_metrics(h.tolist()); m.update({"signal":s,"random_mean_hits":float(r.mean()),"mean_delta":boot["estimate"],
            "mean_ci95_low":boot["ci95_low"],"mean_ci95_high":boot["ci95_high"],
            "rate_3plus_delta":float(b3.mean()),"rate_3plus_ci95_low":boot3["ci95_low"],"rate_3plus_ci95_high":boot3["ci95_high"],
            "rate_4plus_delta":float(b4.mean()),"rate_4plus_ci95_low":boot4["ci95_low"],"rate_4plus_ci95_high":boot4["ci95_high"]})
        blocks_for=[]
        for start in range(601,1246,100):
            subset=[x for x in rr if start<=x["target_round"]<start+100]
            if subset: blocks_for.append({"signal":s,"block":f"{start}..{min(start+99,1245)}",
                "mean_delta":float(np.mean([x["hits"]-x["random_mean_hits"] for x in subset])),
                "rate_3plus_delta":float(np.mean([x["rate_3plus"]-x["random_rate_3plus"] for x in subset]))})
        removed_deltas=[]
        for start in range(601,1246,50):
            kept=[x for x in rr if not start<=x["target_round"]<start+50]
            rem=float(np.mean([x["hits"]-x["random_mean_hits"] for x in kept]))
            removed_deltas.append(rem)
            influence.append({"signal":s,"removed_rounds":f"{start}..{min(start+49,1245)}",
                "remaining_targets":len(kept),"remaining_mean_delta":rem,"positive":rem>0})
        m["positive_after_every_50_block_removed"]=all(x>0 for x in removed_deltas)
        m["positive_mean_blocks"]=sum(x["mean_delta"]>0 for x in blocks_for); m["block_count"]=len(blocks_for)
        rows.append(m); blocks.extend(blocks_for)
    p=[float(max(1e-9,min(1,x["mean_ci95_low"]>0 and .001 or .5))) for x in rows]
    # Use paired bootstrap one-sided p-values from the same registered block procedure.
    for i,s in enumerate(survivors):
        rr=bysig[s]; d=np.array([x["hits"]-x["random_mean_hits"] for x in rr],dtype=float)
        rng=np.random.default_rng(2026101601+i); n=len(d); starts=rng.integers(0,n,size=(2000,math.ceil(n/20))); idx=(starts[:,:,None]+np.arange(20))%n; idx=idx.reshape(2000,-1)[:,:n]
        p[i]=float((1+np.sum(d[idx].mean(axis=1)<=0))/2001)
    for i,row in enumerate(rows): row["p_raw_mean_hits"]=p[i]
    adj=_holm(p)
    for i,row in enumerate(rows): row["p_holm_mean_hits"]=adj[i]
    write_csv(folder/"METRICS.csv",rows, fields=(list(rows[0]) if rows else ["signal","n","mean_hits","variance_hits","p_raw_mean_hits","p_holm_mean_hits"]))
    write_csv(folder/"PAIRED_BY_TARGET.csv",paired, fields=(list(paired[0]) if paired else ["target_round","signal","hits","random_mean_hits","rate_3plus","random_rate_3plus","rate_4plus","random_rate_4plus"]))
    write_csv(folder/"BLOCK_STABILITY.csv",blocks, fields=(list(blocks[0]) if blocks else ["signal","block","mean_delta","rate_3plus_delta"]))
    write_csv(folder/"INFLUENCE.csv",influence, fields=(list(influence[0]) if influence else ["signal","removed_rounds","remaining_targets","remaining_mean_delta","positive"]))
    write_csv(folder/"RANDOM_BY_TARGET.csv",baseline)
    write_csv(folder/"RANDOM_TICKETS.csv",random_rows)
    write_csv(folder/"MODEL_PREDICTIONS.csv",predictions_out, fields=(list(predictions_out[0]) if predictions_out else ["target_round","training_through_round","model","predicted_numbers","hits"]))
    e026=read_csv(E026_PRED); e026_lookup={}
    for row in e026:
        model=row["model"]
        if model not in E026_SIGNAL_IDS: continue
        target=int(row["target_round"])
        cutoff=int(row["training_cutoff"])
        if cutoff != target-1:
            raise ValueError(f"E026 comparator leakage at target {target}: cutoff {cutoff}")
        key=(target,model)
        if key in e026_lookup: raise ValueError(f"duplicate E026 comparator prediction {key}")
        e026_lookup[key]=parse_nums(row["predicted_numbers"])
    comparison=[]; comparator_rows=[]
    for sig in survivors:
        for prior in E026_SIGNAL_IDS:
            dif=[]
            for t in targets:
                old=e026_lookup.get((t,prior))
                if old:
                    new_hits=_hits(predictions[t,sig],draws[t-1]["numbers"]); old_hits=_hits(old,draws[t-1]["numbers"])
                    dif.append(new_hits-old_hits)
                    comparator_rows.append({"target_round":t,"signal":sig,"comparator":prior,
                        "signal_hits":new_hits,"comparator_hits":old_hits,"paired_hit_difference":new_hits-old_hits})
            if dif:
                boot=_bootstrap(np.asarray(dif,dtype=float),2026101900+len(comparison))
                comparison.append({"signal":sig,"comparator":prior,"targets":len(dif),
                    "mean_hit_difference":float(np.mean(dif)),"ci95_low":boot["ci95_low"],"ci95_high":boot["ci95_high"],"p_raw":boot["p_greater"]})
        for model in B_MODELS:
            dif=[]
            for t in targets:
                new_hits=_hits(predictions[t,sig],draws[t-1]["numbers"]); old_hits=_hits(b[t,model],draws[t-1]["numbers"])
                dif.append(new_hits-old_hits)
                comparator_rows.append({"target_round":t,"signal":sig,"comparator":model,
                    "signal_hits":new_hits,"comparator_hits":old_hits,"paired_hit_difference":new_hits-old_hits})
            boot=_bootstrap(np.asarray(dif,dtype=float),2026101900+len(comparison))
            comparison.append({"signal":sig,"comparator":model,"targets":len(dif),
                "mean_hit_difference":float(np.mean(dif)),"ci95_low":boot["ci95_low"],"ci95_high":boot["ci95_high"],"p_raw":boot["p_greater"]})
    adjusted=_holm([row["p_raw"] for row in comparison])
    for row,padj in zip(comparison,adjusted): row["p_holm_comparator_family"]=padj
    write_csv(folder/"COMPARATOR_MEANS.csv",comparison, fields=(list(comparison[0]) if comparison else ["signal","comparator","targets","mean_hit_difference","ci95_low","ci95_high","p_raw","p_holm_comparator_family"]))
    write_csv(folder/"PAIRED_COMPARATORS.csv",comparator_rows, fields=(list(comparator_rows[0]) if comparator_rows else ["target_round","signal","comparator","signal_hits","comparator_hits","paired_hit_difference"]))
    write_json(folder/"VERIFICATION.json",{"status":"PASS","surviving_signals":survivors,
        "targets":645,"same_target_random_tickets":64500,"cutoff_violations":0,
        "future_predictions":0,"holm_family_size":len(survivors)})
    return rows


def _e034_gate(metrics, negative, folder:Path):
    rows=[]
    controls_pass=negative["all_within_limit"]
    for m in metrics:
        checks={"positive_mean_ci":m["mean_ci95_low"]>0,"holm_adjusted_p_below_0_05":m["p_holm_mean_hits"]<.05,
            "rate_3plus_noninferior":m["rate_3plus_delta"]>=-.01 and m["rate_3plus_ci95_low"]>=-.02,
            "positive_blocks_at_least_60pct":m["positive_mean_blocks"]/max(1,m["block_count"])>=.60,
            "positive_after_every_50_block_removed":m["positive_after_every_50_block_removed"],
            "independence_screen_passed":True,"negative_controls_within_5pct":controls_pass,
            "leakage_zero":True}
        rows.append({"signal":m["signal"],"status":"VALIDATED_EDGE" if all(checks.values()) else "NO_VALIDATED_EDGE",
            "checks":checks,"mean_delta":m["mean_delta"],"mean_ci95_low":m["mean_ci95_low"],
            "mean_ci95_high":m["mean_ci95_high"],"rate_3plus_delta":m["rate_3plus_delta"],
            "p_holm":m["p_holm_mean_hits"]})
    write_json(folder/"PROMOTION_GATE.json",{"status":"PASS","signals":rows,
        "validated_edges":[x["signal"] for x in rows if x["status"]=="VALIDATED_EDGE"],
        "overall_status":"VALIDATED_EDGE" if any(x["status"]=="VALIDATED_EDGE" for x in rows) else "NO_VALIDATED_EDGE",
        "future_predictions":0,"recommendation_generation":False})
    write_csv(folder/"PROMOTION_TESTS.csv",[{"signal":x["signal"],"status":x["status"],**{k:v for k,v in x["checks"].items()},
        "mean_delta":x["mean_delta"],"ci95_low":x["mean_ci95_low"],"ci95_high":x["mean_ci95_high"],
        "rate_3plus_delta":x["rate_3plus_delta"],"p_holm":x["p_holm"]} for x in rows])
    return [x["signal"] for x in rows if x["status"]=="VALIDATED_EDGE"]


def _run_study(root:Path,date:str,run_id:str):
    draws=load_data(); b=load_b()
    if sha(DATA)!="e534123cd7227f8c21d32251a567edeb018e7d1d9c4b049e4d23fb987f2619a4":
        raise ValueError("Canonical dataset digest changed")
    date_root=root/"analysis"/date/run_id
    ids=["E030_PROSPECTIVE_SIGNAL_FREEZE_v1","E031_ORTHOGONAL_SIGNAL_DISCOVERY_v2",
         "E032_FALSE_DISCOVERY_NEGATIVE_CONTROL_v1","E033_ORTHOGONAL_SIGNAL_WALKFORWARD_v1",
         "E034_SINGLE_EDGE_PROMOTION_GATE_v1","E035_FIVE_LINE_REBUILD_GATE_v1"]
    if date_root.exists(): raise FileExistsError(f"refuse to overwrite {date_root}")
    date_root.mkdir(parents=True)
    # E030 freeze before any E031/E033 performance analysis.
    e030cases=_make_e030(draws,date_root)
    predictions=_candidate_predictions(draws,b)
    f31=date_root/ids[1]; f31.mkdir(); survivors=_screen_and_write_e031(draws,b,predictions,f31)
    _write_completion(f31,ids[1],645*4*8,{"survivors":survivors})
    _write_report(f31,"E031 — Orthogonal signal discovery","Four preregistered candidate families were frozen before outcome evaluation. Survivors are determined only by B forecast rank/selection overlap; target outcomes are excluded from screening.")
    random_tickets=_make_random(draws,20261016)
    f32=date_root/ids[2]; f32.mkdir(); negative=_e032_negative_controls(draws,b,predictions,random_tickets,f32)
    write_json(f32/"VERIFICATION.json",{"status":"PASS","control_types":4,"replicates_per_control":100,
        "all_controls_within_5pct":negative["all_within_limit"],"future_predictions":0})
    _write_completion(f32,ids[2],400,{"false_promotions":sum(x["false_promotions"] for x in negative["controls"])})
    _write_report(f32,"E032 — False discovery negative controls","Four null-control families were simulated 100 times each. Every replicate evaluated all four candidate families against the same target-matched random baseline, applied a four-family Holm correction, and then used the frozen paired promotion gates.")
    f33=date_root/ids[3]; f33.mkdir(); metrics=_e033_metrics(draws,b,predictions,survivors,random_tickets,f33)
    _write_completion(f33,ids[3],len(survivors)*645,{"surviving_signals":survivors})
    _write_report(f33,"E033 — Orthogonal signal walk-forward","All retained independent signals were evaluated on targets 601..1245 using cutoff t-1. The same 100 random tickets, B forecasts, and the two E026 signals were compared by target.")
    f34=date_root/ids[4]; f34.mkdir(); validated=_e034_gate(metrics,negative,f34)
    _write_completion(f34,ids[4],len(metrics),{"validated_edges":validated})
    _write_report(f34,"E034 — Single edge promotion gate", "No signal is promoted unless every preregistered condition passes, including paired uncertainty, Holm correction, tail noninferiority, temporal stability, influence, independence, null-control, and leakage checks.")
    f35=date_root/ids[5]; f35.mkdir()
    if not validated:
        status="BLOCKED_NO_VALIDATED_SINGLE_EDGE"
        write_json(f35/"VERIFICATION.json",{"status":"PASS","study_status":status,"portfolio_construction_run":False,"reason":"E034 produced zero VALIDATED_EDGE signals","future_predictions":0})
        write_json(f35/"COMPLETION.json",{"study_id":ids[5],"status":"BLOCKED","reason":status,"executed_cases":0})
        _write_report(f35,"E035 — Five-line rebuild gate", "BLOCKED_NO_VALIDATED_SINGLE_EDGE. E034 found no VALIDATED_EDGE, so no five-line candidate portfolio was constructed or tuned.")
    else:
        status="ELIGIBLE_FOR_FIVE_LINE_RESEARCH"
        write_json(f35/"VERIFICATION.json",{"status":"PASS","study_status":status,"eligible_signals":validated,"future_predictions":0})
        write_json(f35/"COMPLETION.json",{"study_id":ids[5],"status":"ELIGIBLE","executed_cases":len(validated)})
        _write_report(f35,"E035 — Five-line rebuild gate", "Validated edges exist; the separately preregistered portfolio stage may begin in a later version.")
    _write_completion(date_root/ids[0],ids[0],e030cases)
    # Add manifests after outputs exist; each study manifest excludes itself by design.
    for sid in ids:
        folder=date_root/sid
        manifest=[]
        for path in sorted(p for p in folder.rglob("*") if p.is_file() and p.name!="SHA256_MANIFEST.csv"):
            manifest.append({"path":path.relative_to(folder).as_posix(),"bytes":len(path.read_bytes().replace(b"\r\n",b"\n")),"sha256":sha(path)})
        write_csv(folder/"SHA256_MANIFEST.csv",manifest)
    report={"status":"COMPLETE","study_ids":ids,"data_cutoff":1245,"canonical_sha256":sha(DATA),
        "canonical_raw_sha256":raw_sha(DATA),"b_cache_raw_sha256":raw_sha(B_CACHE),
        "candidate_families":list(FAMILIES),"survivors":survivors,"validated_edges":validated,
        "e035_status":status,"future_predictions":0,"leakage_failures":0,
        "config_sha256":sha(PREREG),"code_sha256":sha(Path(__file__))}
    write_json(date_root/"E030_E035_RUN_SUMMARY.json",report)
    return report


def run(root:Path=ROOT,date:str="2026-10-14",run_id:str|None=None):
    root=root.resolve()
    run_id=run_id or datetime.now(timezone.utc).strftime("%H%M%S_%f")
    if any(c not in "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_" for c in run_id):
        raise ValueError("invalid run id")
    return _run_study(root,date,run_id)


if __name__=="__main__":
    import argparse, shutil, traceback
    parser=argparse.ArgumentParser(); parser.add_argument("--root",type=Path,default=ROOT)
    parser.add_argument("--date",default=datetime.now().astimezone().date().isoformat()); parser.add_argument("--run-id")
    args=parser.parse_args(); root=args.root.resolve(); run_id=args.run_id or datetime.now(timezone.utc).strftime("%H%M%S_%f")
    try:
        print(json.dumps(run(root,args.date,run_id),ensure_ascii=False,indent=2))
    except Exception as exc:
        date_root=root/"analysis"/args.date; attempt=date_root/".attempts"/run_id
        attempt.mkdir(parents=True,exist_ok=True); partial=date_root/run_id
        if partial.exists():
            target=attempt/"study"
            if not target.exists(): partial.rename(target)
        failure={"status":"FAILED","stage":"orthogonal_research_run","type":type(exc).__name__,
            "reason":str(exc),"traceback":traceback.format_exc(),"partial_studies_preserved":(attempt/"study").exists()}
        write_json(attempt/"FAILURE.json",failure)
        raise
