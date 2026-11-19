#!/usr/bin/env python3
"""Preregistered H1250-A/B independent research; no recommendation lines are emitted."""
from __future__ import annotations
import csv, hashlib, importlib.util, itertools, json, math, random, statistics, sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "lotto_data.csv"
PREREG = ROOT / "research/weekly_purchase/1250/H1250_AB_PREREGISTRATION_2026-11-10_V2.json"
QUEUE = ROOT / "automation/research_queue_v2.json"
V42_PATH = ROOT / "automation/today_frozen_signal_partition_v42.py"
B_PATH = ROOT / "research/1245_final_pipeline_v3/recovered_original_assets/b_model_backtest.py"
AC_PATH = ROOT / "automation/recovered_models_v2.py"
V12_PATH = ROOT / "automation/today_raw_signal_meta_v12.py"
V18_PATH = ROOT / "automation/today_interaction_adagrad_v18.py"
KST = timezone(timedelta(hours=9))
EXPECTED_DATA_SHA256 = "a5996af8b842799d777beae0abeef9767f79726870e4d78d6683dfb0fe4802e7"
ALLOCATORS = ("rr", "contig", "snake", "paired")
RANKERS = ("H", "G", "C", "M", "P", "T")
PRIMARY_METRICS = ("max_hits", "any2", "any3", "winning_union_coverage")


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def git_blob_sha(path):
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def import_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_draws():
    with DATA.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    draws = []
    for row in rows:
        nums = tuple(sorted(int(row[f"no{i}"]) for i in range(1, 7)))
        assert len(nums) == 6 and len(set(nums)) == 6, f"invalid main numbers at round {row.get('round')}"
        assert all(1 <= n <= 45 for n in nums), f"out-of-range number at round {row.get('round')}"
        draws.append({"round": int(row["round"]), "date": row["date"], "nums": nums})
    assert [d["round"] for d in draws] == list(range(1, len(draws) + 1)), "round gap/duplicate"
    assert len(draws) == 1249 and draws[-1]["round"] == 1249, "preregistered cutoff mismatch"
    return draws


def load_and_validate_contract():
    prereg = load_json(PREREG)
    assert prereg["status"] == "SPEC_FROZEN_IMPLEMENTATION_PENDING"
    assert prereg["target_round"] == 1250 and prereg["data_cutoff"] == 1249
    assert prereg["scope"]["warmup_targets"] == "201..400 inclusive"
    assert prereg["scope"]["outer_targets"] == "401..1249 inclusive"
    assert prereg["scope"]["outer_target_count"] == 849
    gate = prereg["shared_protocol"]["strict_gate"]
    assert gate["threshold_changes"] == "PROHIBITED"
    reporting = prereg["shared_protocol"]["reporting"]
    assert reporting["no_recommendation_numbers"] is True
    assert reporting["no_final_purchase_lines"] is True
    assert reporting["no_auto_promotion"] is True
    plan = prereg["execution_plan"]
    assert plan["workflow_mode"] == "workflow_dispatch_only; do not add or change schedules"
    assert plan["implementation_entrypoint"] == "automation/h1250_ab_research_v2.py"
    assert plan["workflow_entrypoint"] == ".github/workflows/h1250-ab-research-v2.yml"
    implementation_hash = plan["implementation_code_hash"]
    assert implementation_hash not in ("PENDING", "", None)
    assert git_blob_sha(Path(__file__).resolve()) == implementation_hash

    queue = load_json(QUEUE)
    tasks = {task["id"]: task for task in queue["tasks"]}
    for task_id in ("E043_H1250_A_FIXED_BANK_ALLOCATOR_v1", "E044_H1250_B_DYNAMIC_CANDIDATE_RANKING_v2"):
        task = tasks[task_id]
        assert task["spec"]["execution_entrypoint"] == "automation/h1250_ab_research_v2.py"
        assert task["spec"]["workflow_entrypoint"] == ".github/workflows/h1250-ab-research-v2.yml"
        assert task["spec"]["data_cutoff"] == 1249

    draws = load_draws()
    expected = dict(prereg["shared_protocol"]["frozen_dependency_blobs"])
    expected[prereg["shared_protocol"]["candidate_generator"]["source"]] = prereg["shared_protocol"]["candidate_generator"]["source_blob_sha"]
    actual = {}
    for rel, expected_sha in expected.items():
        path = ROOT / rel
        assert path.is_file(), f"missing frozen dependency: {rel}"
        actual[rel] = git_blob_sha(path)
        assert actual[rel] == expected_sha, f"frozen dependency changed: {rel}"
    data_sha = sha256_bytes(DATA.read_bytes())
    assert data_sha == prereg["data_sha256"] == EXPECTED_DATA_SHA256, "data SHA256 mismatch"

    v42 = import_module(V42_PATH, "h1250_v42")
    for name, pattern in prereg["H1250_A"]["allocator_patterns"].items():
        assert pattern == v42.PAT[name], f"allocator pattern drift: {name}"
    assert tuple(prereg["H1250_B"]["rankers"]) == RANKERS
    assert prereg["shared_protocol"]["candidate_generator"]["rolling_signal_window"] == 300
    return prereg, draws, {"git_blob_sha": actual, "data_sha256": data_sha}, v42


def preflight():
    prereg, draws, hashes, _ = load_and_validate_contract()
    print(json.dumps({
        "status": "PREFLIGHT_PASS",
        "data_cutoff": draws[-1]["round"],
        "draw_count": len(draws),
        "data_sha256": hashes["data_sha256"],
        "frozen_dependency_count": len(hashes["git_blob_sha"]),
        "allocator_contract": list(prereg["H1250_A"]["allocator_patterns"]),
        "rankers": list(prereg["H1250_B"]["rankers"]),
        "H1250_B_adaptive_selection_objective": prereg["H1250_B"]["adaptive_policy"]["objective"],
    }, ensure_ascii=False))


def zscore(scores):
    values = list(scores.values())
    mu, sd = statistics.mean(values), statistics.pstdev(values) or 1.0
    return {n: (value - mu) / sd for n, value in scores.items()}


def update_adagrad(v18, features, weights, squared_gradients, actual, shrink, gradient_decay):
    grad = [0.0] * len(weights)
    for number in range(1, 46):
        vector = v18.design(features[number])
        y = 1.0 if number in actual else 0.0
        probability = v18.sigmoid(sum(a * b for a, b in zip(weights, vector)))
        for j, value in enumerate(vector):
            grad[j] += (probability - y) * value
    for j in range(len(weights)):
        if j > 0:
            weights[j] *= shrink
        g = grad[j] / 45.0 + (0.0 if j == 0 else 0.0025 * weights[j])
        squared_gradients[j] = gradient_decay * squared_gradients[j] + g * g
        weights[j] -= 0.035 * g / math.sqrt(squared_gradients[j] + 1e-8)
    return weights, squared_gradients


def portfolio_metrics(v42, lines, actual):
    result = v42.met(lines, actual)
    assert len(lines) == 5 and all(len(set(line)) == 6 for line in lines)
    union = set().union(*(set(line) for line in lines))
    assert len(union) == 30 and int(result["union_size"]) == 30
    return result


def portfolio_hash(lines):
    canonical = json.dumps([list(line) for line in lines], separators=(",", ":"))
    return sha256_bytes(canonical.encode("utf-8"))


def bank_hash(core, tail):
    canonical = json.dumps({"core6": list(core), "tail24": list(tail)}, separators=(",", ":"))
    return sha256_bytes(canonical.encode("utf-8"))


def objective_a(metrics):
    return (
        float(metrics["max_hits"]) + 0.85 * float(metrics["any2"])
        + 1.35 * float(metrics["any3"]) + 0.10 * float(metrics["winning_union_coverage"])
    )


def select_prior_only_a(history, prior_n, tie_order):
    assert len(history) >= prior_n
    prior = history[-prior_n:]
    scores = {name: statistics.mean(objective_a(row["a_metrics"][name]) for row in prior) for name in tie_order}
    chosen = min(tie_order, key=lambda name: (-scores[name], tie_order.index(name)))
    return chosen, scores, prior[0]["target"], prior[-1]["target"]


def select_prior_only_b(history, prior_n, tie_order, recall_ks):
    """Choose a tail ranker using only prior completed targets and macro recall@K."""
    assert len(history) >= prior_n
    prior = history[-prior_n:]
    scores = {
        name: statistics.mean(
            statistics.mean(float(row["b_recall_k"][name][str(k)]) / 6.0 for k in recall_ks)
            for row in prior
        )
        for name in tie_order
    }
    chosen = min(tie_order, key=lambda name: (-scores[name], tie_order.index(name)))
    degenerate = max(scores.values()) - min(scores.values()) <= 1e-12
    return chosen, scores, prior[0]["target"], prior[-1]["target"], degenerate


def moving_block_bootstrap_ci(values, alpha, seed, reps, block_length):
    """Circular moving-block bootstrap; retain all n observations per replicate."""
    n = len(values)
    assert n >= block_length
    blocks_needed = math.ceil(n / block_length)
    remainder = n % block_length
    prefix = [0.0]
    for value in values:
        prefix.append(prefix[-1] + float(value))

    def block_sum(start):
        end = start + block_length
        if end <= n:
            return prefix[end] - prefix[start]
        return (prefix[n] - prefix[start]) + prefix[end - n]

    rng = random.Random(seed)
    means = []
    for _ in range(reps):
        total = 0.0
        for block_i in range(blocks_needed):
            start = rng.randrange(n)
            total += block_sum(start)
            if remainder and block_i == blocks_needed - 1:
                total -= float(values[(start + block_length - 1) % n])
        means.append(total / n)
    means.sort()
    return [
        means[int((alpha / 2.0) * (reps - 1))],
        means[int((1.0 - alpha / 2.0) * (reps - 1))],
    ]


def block_stability_rows(policy_name, rows, null, block_length):
    out = []
    for metric in PRIMARY_METRICS:
        diffs = [float(row[metric]) - float(null[metric]) for row in rows]
        for i in range(0, len(diffs), block_length):
            block = diffs[i:i + block_length]
            out.append({
                "policy": policy_name, "metric": metric,
                "target_start": int(rows[i]["target_round"]),
                "target_end": int(rows[i + len(block) - 1]["target_round"]),
                "n": len(block), "mean_delta_vs_exact_null": statistics.mean(block),
                "positive": statistics.mean(block) > 0,
            })
    return out


def strict_gate(policy_name, rows, null, alpha, block_length, bootstrap_reps, seed):
    diffs = {
        metric: [float(row[metric]) - float(null[metric]) for row in rows]
        for metric in PRIMARY_METRICS
    }
    intervals = {
        metric: moving_block_bootstrap_ci(
            diffs[metric], alpha, seed + index, bootstrap_reps, block_length
        )
        for index, metric in enumerate(PRIMARY_METRICS)
    }
    any2_blocks = [
        statistics.mean(diffs["any2"][i:i + block_length])
        for i in range(0, len(diffs["any2"]), block_length)
    ]
    positive_share = sum(value > 0 for value in any2_blocks) / len(any2_blocks)
    failed = [metric for metric in PRIMARY_METRICS if intervals[metric][0] <= 0]
    if positive_share < 0.65:
        failed.append("any2_block_stability")
    return {
        "policy": policy_name, "n_outer_targets": len(rows),
        "strict_portfolio_pass": not failed, "failed_gates": failed,
        "alpha_family": 0.05, "alpha_per_metric": alpha,
        "bootstrap": {
            "method": "circular_moving_block_bootstrap", "block_length": block_length,
            "replicates": bootstrap_reps, "seed_base": seed, "residual_observation_retained": True,
        },
        "adjusted_ci_delta_vs_exact_null": intervals,
        "any2_positive_nonoverlapping_50_target_block_share": positive_share,
        "any2_block_count_including_final_remainder": len(any2_blocks),
        "exact_null": {metric: float(null[metric]) for metric in PRIMARY_METRICS},
        "no_auto_promotion": True, "no_recommendation_numbers": True,
    }


def mean_metrics(rows, metric_names):
    return {metric: statistics.mean(float(row[metric]) for row in rows) for metric in metric_names}


def write_csv(path, rows, fields=None):
    rows = list(rows)
    if fields is None:
        assert rows, f"cannot infer fields for empty file {path}"
        fields = list(rows[0].keys())
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_manifest(directory):
    manifest = directory / "SHA256_MANIFEST.csv"
    files = sorted(
        (p for p in directory.iterdir() if p.is_file() and p.name != manifest.name),
        key=lambda p: p.name,
    )
    rows = [
        {"path": p.name, "sha256": sha256_bytes(p.read_bytes()), "bytes": p.stat().st_size}
        for p in files
    ]
    write_csv(manifest, rows, ["path", "sha256", "bytes"])
    with manifest.open(encoding="utf-8-sig", newline="") as stream:
        checked = list(csv.DictReader(stream))
    assert len(checked) == len(files)
    assert len({row["path"] for row in checked}) == len(checked)
    assert {row["path"] for row in checked} == {p.name for p in files}
    by_name = {p.name: p for p in files}
    for row in checked:
        p = by_name[row["path"]]
        assert p.stat().st_size == int(row["bytes"])
        assert sha256_bytes(p.read_bytes()) == row["sha256"]
    return {"entries": len(checked), "status": "PASS", "manifest_sha256": sha256_bytes(manifest.read_bytes())}


def execute():
    prereg, draws, hashes, v42 = load_and_validate_contract()
    b = import_module(B_PATH, "h1250_b")
    ac = import_module(AC_PATH, "h1250_ac")
    v12 = import_module(V12_PATH, "h1250_v12")
    v18 = import_module(V18_PATH, "h1250_v18")

    a_spec, b_spec = prereg["H1250_A"], prereg["H1250_B"]
    gate_spec = prereg["shared_protocol"]["strict_gate"]
    block_length = int(gate_spec["block_length"])
    prior_n = 150
    alpha = float(gate_spec["alpha_per_metric"])
    bootstrap_reps = int(gate_spec["bootstrap_replicates"])
    conditional_repeats = int(a_spec["conditional_random_partitions_per_target"])
    random_banks = int(b_spec["random_candidate_banks_per_target"])
    random_bank_size = int(b_spec["random_candidate_bank_size"])
    recall_ks = list(b_spec["candidate_recall_k"])
    seed_a, seed_b = int(a_spec["random_seed"]), int(b_spec["random_seed"])
    cfg = {"slow": (1.0, 1.0), "medium": (0.9995, 0.999), "fast": (0.9975, 0.992)}
    assert block_length == 50 and bootstrap_reps == 7000 and alpha == 0.0125
    assert tuple(cfg) == ("slow", "medium", "fast")
    assert set(a_spec["allocator_patterns"]) == set(ALLOCATORS)
    assert tuple(b_spec["rankers"]) == RANKERS
    assert b_spec["adaptive_policy"]["objective"] == "Highest equal-weight macro-average candidate recall fraction across K=10,15,20,25,30 over the prior 150 completed targets."

    bank = b.feature_structure_bank(b.make_structure_bank())
    freq, last_seen = [0] * 45, [0] * 45
    pair_counts, triple_counts = Counter(), Counter()
    profiles = [Counter() for _ in range(6)]
    for draw in draws[:200]:
        nums = draw["nums"]
        for number in nums:
            freq[number - 1] += 1
            last_seen[number - 1] = draw["round"]
        pair_counts.update(itertools.combinations(nums, 2))
        triple_counts.update(itertools.combinations(nums, 3))
        profile = b.structure_profile(nums, None)
        for i, value in enumerate(profile[:5]):
            profiles[i][value] += 1
    for index in range(1, 200):
        profile = b.structure_profile(draws[index]["nums"], draws[index - 1]["nums"])
        profiles[5][profile[5]] += 1

    dim = len(v18.feature_names())
    p0 = 6 / 45
    states = {
        name: {"weights": [math.log(p0 / (1 - p0))] + [0.0] * (dim - 1),
               "squared_gradients": [0.0] * dim}
        for name in cfg
    }

    history, outer_a_rows, outer_b_rows = [], [], []
    outer_recall_rows, prediction_rows = [], []
    conditional_random_rows, random_bank_rows = [], []
    winner_trace_a_rows, winner_trace_b_rows = [], []
    adaptive_rows, b_degenerate_decisions = [], []
    b_recall30_invariance_failures = 0
    warmup_candidate_count = 0
    a_current, b_current = "rr", "H"

    for idx in range(200, len(draws)):
        target, training_through = idx + 1, idx
        assert training_through == target - 1
        history_draws = [row["nums"] for row in draws[:idx]]
        assert len(history_draws) == training_through

        # Candidate generation is completed before the target outcome is read.
        preds = {
            **b.predictions_for_round(draws, idx, freq, last_seen, pair_counts, triple_counts, profiles, bank),
            **ac.predict(history_draws),
        }
        raw = v12.raw_features(draws, idx, freq, last_seen, pair_counts, triple_counts, preds)
        scores = {name: v18.predict(raw, state["weights"]) for name, state in states.items()}
        zscores = {name: zscore(scores[name]) for name in cfg}
        blend = {number: statistics.mean(zscores[name][number] for name in cfg) for number in range(1, 46)}
        ranked = v42.ranked_hybrid(scores["slow"], blend)
        core, tail = list(ranked[:6]), list(ranked[6:])
        assert len(core) == 6 and len(tail) == 24 and len(set(core + tail)) == 30
        bank_digest = bank_hash(core, tail)

        rolling = [row["nums"] for row in draws[max(0, idx - 300):idx]]
        frozen = v42.frozen_scores(rolling)
        tail_orders = {"H": tail}
        for ranker in RANKERS[1:]:
            tail_orders[ranker] = sorted(tail, key=lambda number: (-frozen[ranker][number], number))
        a_lines = {allocator: v42.lines(core, tail, allocator) for allocator in ALLOCATORS}
        b_lines = {ranker: v42.lines(core, tail_orders[ranker], "rr") for ranker in RANKERS}

        decision_made = False
        prior_start = prior_end = None
        decision_scores = {}
        decision_source = "carry_forward"
        if target >= 401 and (target - 401) % block_length == 0:
            decision_made = True
            if target == 401:
                a_current, b_current = "rr", "H"
                decision_source = "frozen_first_outer_block"
            else:
                a_current, a_scores, prior_start, prior_end = select_prior_only_a(history, prior_n, ALLOCATORS)
                b_current, b_scores, b_prior_start, b_prior_end, degenerate = select_prior_only_b(history, prior_n, RANKERS, recall_ks)
                assert (prior_start, prior_end) == (b_prior_start, b_prior_end)
                decision_scores = {"A_allocator_objective": a_scores, "B_macro_candidate_recall": b_scores}
                decision_source = "immediately_preceding_150_completed_targets"
                b_degenerate_decisions.append(degenerate)

        # Only after selection is frozen do we read the current target outcome.
        actual = set(draws[idx]["nums"])
        a_metrics = {allocator: portfolio_metrics(v42, a_lines[allocator], actual) for allocator in ALLOCATORS}
        b_metrics = {ranker: portfolio_metrics(v42, b_lines[ranker], actual) for ranker in RANKERS}
        b_recall30, b_recall_k, recall_for_target = {}, {}, []
        for ranker in RANKERS:
            ordered = core + tail_orders[ranker]
            b_recall_k[ranker] = {}
            for k in recall_ks:
                found = len(set(ordered[:k]) & actual)
                b_recall_k[ranker][str(k)] = found
                if target >= 401:
                    recall_for_target.append({
                        "study_id": b_spec["study_id"], "target_round": target,
                        "training_through_round": training_through, "ranker": ranker, "k": k,
                        "winning_numbers_found": found, "recall_fraction": found / 6.0,
                        "exact_uniform_expected_found": 6.0 * k / 45.0,
                    })
            b_recall30[ranker] = b_recall_k[ranker]["30"]
        assert len(set(b_recall30.values())) == 1, "rankers changed candidate bank membership at K=30"

        history.append({"target": target, "a_metrics": a_metrics, "b_metrics": b_metrics, "b_recall30": b_recall30, "b_recall_k": b_recall_k})

        if target >= 401:
            core_set, tail_set = set(core), set(tail)
            slow_order = sorted(range(1, 46), key=lambda number: (-scores["slow"][number], number))
            slow_rank = {number: position + 1 for position, number in enumerate(slow_order)}
            blend_tail_all = sorted((number for number in range(1, 46) if number not in core_set), key=lambda number: (-blend[number], number))
            blend_tail_rank = {number: position + 1 for position, number in enumerate(blend_tail_all)}
            for allocator, lines_for_allocator in a_lines.items():
                candidate_order = core + tail
                candidate_rank = {number: position + 1 for position, number in enumerate(candidate_order)}
                ticket_index = {number: line_index + 1 for line_index, line in enumerate(lines_for_allocator) for number in line}
                line_hits = {line_index + 1: len(set(line) & actual) for line_index, line in enumerate(lines_for_allocator)}
                portfolio_max_hit = max(line_hits.values())
                portfolio_sha = portfolio_hash(lines_for_allocator)
                for winner in sorted(actual):
                    rank = candidate_rank.get(winner)
                    missed = [k for k in recall_ks if rank is None or rank > k]
                    stage = "SLOW_CORE6" if winner in core_set else "HYBRID_TAIL24" if winner in tail_set else "HYBRID_TAIL_EXCLUDED"
                    miss_stage = "FIXED_BANK_EXCLUSION" if rank is None else "RANKED_26_30" if rank > 25 else "RANKED_21_25" if rank > 20 else "RANKED_16_20" if rank > 15 else "RANKED_11_15" if rank > 10 else "RETAINED_TOP10"
                    line_no = ticket_index.get(winner)
                    winner_trace_a_rows.append({
                        "study_id": a_spec["study_id"], "target_round": target, "training_through_round": training_through,
                        "allocator": allocator, "winner_number": winner, "candidate_generator_stage": stage,
                        "slow_rank_all45": slow_rank[winner], "hybrid_blend_tail_rank_all39": blend_tail_rank.get(winner),
                        "candidate_rank_top30": rank, "candidate_bank_member": rank is not None,
                        "included_at_K10": bool(rank is not None and rank <= 10),
                        "included_at_K15": bool(rank is not None and rank <= 15),
                        "included_at_K20": bool(rank is not None and rank <= 20),
                        "included_at_K25": bool(rank is not None and rank <= 25),
                        "included_at_K30": bool(rank is not None and rank <= 30),
                        "missed_at_k_json": json.dumps(missed), "candidate_miss_stage": miss_stage,
                        "ticket_index": line_no, "ticket_line_hit_count": line_hits.get(line_no),
                        "portfolio_max_hit": portfolio_max_hit, "slow_score": scores["slow"][winner],
                        "blend_score": blend[winner], "medium_score": scores["medium"][winner],
                        "fast_score": scores["fast"][winner], "candidate_bank_sha256": bank_digest,
                        "portfolio_sha256": portfolio_sha,
                    })
            for ranker, lines_for_ranker in b_lines.items():
                candidate_order = core + tail_orders[ranker]
                candidate_rank = {number: position + 1 for position, number in enumerate(candidate_order)}
                tail_rank_variant = {number: position + 1 for position, number in enumerate(tail_orders[ranker])}
                ticket_index = {number: line_index + 1 for line_index, line in enumerate(lines_for_ranker) for number in line}
                line_hits = {line_index + 1: len(set(line) & actual) for line_index, line in enumerate(lines_for_ranker)}
                portfolio_max_hit = max(line_hits.values())
                portfolio_sha = portfolio_hash(lines_for_ranker)
                signal_name = {"H": "HYBRID_BLEND", "G": "GAP", "C": "RECENT_FREQUENCY", "M": "MOMENTUM", "P": "PAIR_ASSOCIATION", "T": "TRIPLE_ASSOCIATION"}[ranker]
                for winner in sorted(actual):
                    rank = candidate_rank.get(winner)
                    missed = [k for k in recall_ks if rank is None or rank > k]
                    stage = "SLOW_CORE6" if winner in core_set else "HYBRID_TAIL24" if winner in tail_set else "HYBRID_TAIL_EXCLUDED"
                    miss_stage = "FIXED_BANK_EXCLUSION" if rank is None else "RANKED_26_30" if rank > 25 else "RANKED_21_25" if rank > 20 else "RANKED_16_20" if rank > 15 else "RANKED_11_15" if rank > 10 else "RETAINED_TOP10"
                    line_no = ticket_index.get(winner)
                    ranker_score = blend[winner] if ranker == "H" else frozen[ranker][winner]
                    winner_trace_b_rows.append({
                        "study_id": b_spec["study_id"], "target_round": target, "training_through_round": training_through,
                        "ranker": ranker, "ranker_signal": signal_name, "winner_number": winner,
                        "candidate_generator_stage": stage, "slow_rank_all45": slow_rank[winner],
                        "hybrid_blend_tail_rank_all39": blend_tail_rank.get(winner),
                        "rank_within_tail24_under_ranker": tail_rank_variant.get(winner),
                        "candidate_rank_top30": rank, "candidate_bank_member": rank is not None,
                        "included_at_K10": bool(rank is not None and rank <= 10),
                        "included_at_K15": bool(rank is not None and rank <= 15),
                        "included_at_K20": bool(rank is not None and rank <= 20),
                        "included_at_K25": bool(rank is not None and rank <= 25),
                        "included_at_K30": bool(rank is not None and rank <= 30),
                        "missed_at_k_json": json.dumps(missed), "candidate_miss_stage": miss_stage,
                        "ticket_index": line_no, "ticket_line_hit_count": line_hits.get(line_no),
                        "portfolio_max_hit": portfolio_max_hit, "ranker_score": ranker_score,
                        "blend_score": blend[winner], "candidate_bank_sha256": bank_digest,
                        "portfolio_sha256": portfolio_sha,
                    })

            selected_a, selected_b = a_metrics[a_current], b_metrics[b_current]
            outer_a_rows.extend({
                "target_round": target, "training_through_round": training_through,
                "allocator": allocator, "candidate_bank_sha256": bank_digest,
                "portfolio_sha256": portfolio_hash(a_lines[allocator]), **a_metrics[allocator],
            } for allocator in ALLOCATORS)
            outer_b_rows.extend({
                "target_round": target, "training_through_round": training_through,
                "ranker": ranker, "candidate_bank_sha256": bank_digest,
                "portfolio_sha256": portfolio_hash(b_lines[ranker]), **b_metrics[ranker],
            } for ranker in RANKERS)
            outer_recall_rows.extend(recall_for_target)

            prediction_rows.append({
                "study_id": a_spec["study_id"], "target_round": target,
                "training_through_round": training_through, "variant": a_current,
                "candidate_bank_sha256": bank_digest, "portfolio_sha256": portfolio_hash(a_lines[a_current]),
                **selected_a,
            })
            prediction_rows.append({
                "study_id": b_spec["study_id"], "target_round": target,
                "training_through_round": training_through, "variant": b_current,
                "candidate_bank_sha256": bank_digest, "portfolio_sha256": portfolio_hash(b_lines[b_current]),
                **selected_b,
            })

            conditional_rng = random.Random(seed_a + target)
            conditional_samples = []
            for _ in range(conditional_repeats):
                randomized_tail = conditional_rng.sample(tail, len(tail))
                conditional_samples.append(portfolio_metrics(v42, v42.lines(core, randomized_tail, "rr"), actual))
            conditional_random_rows.append({
                "target_round": target, "training_through_round": training_through,
                "candidate_bank_sha256": bank_digest, "simulations": conditional_repeats,
                **mean_metrics(conditional_samples, PRIMARY_METRICS),
                **{
                    f"delta_adaptive_vs_conditional_random_{metric}": float(selected_a[metric]) - statistics.mean(float(sample[metric]) for sample in conditional_samples)
                    for metric in PRIMARY_METRICS
                },
            })

            random_rng = random.Random(seed_b + target)
            random_samples, random_recall30 = [], []
            for _ in range(random_banks):
                random_bank = random_rng.sample(range(1, 46), random_bank_size)
                random_core, random_tail = random_bank[:6], random_bank[6:]
                random_lines = v42.lines(random_core, random_tail, b_spec["random_candidate_allocator"])
                random_samples.append(portfolio_metrics(v42, random_lines, actual))
                random_recall30.append(len(set(random_bank) & actual))
            random_bank_rows.append({
                "target_round": target, "training_through_round": training_through,
                "simulations": random_banks, "candidate_bank_size": random_bank_size,
                "mean_random_bank_recall30": statistics.mean(random_recall30),
                **mean_metrics(random_samples, PRIMARY_METRICS),
                **{
                    f"delta_adaptive_vs_random_bank_{metric}": float(selected_b[metric]) - statistics.mean(float(sample[metric]) for sample in random_samples)
                    for metric in PRIMARY_METRICS
                },
            })

            block_start = 401 + ((target - 401) // block_length) * block_length
            adaptive_rows.append({
                "study_id": a_spec["study_id"], "target_round": target, "block_start": block_start,
                "decision_made": decision_made, "decision_source": decision_source,
                "selected_variant": a_current, "prior_start": prior_start, "prior_end": prior_end,
                "prior_n": prior_n if decision_source == "immediately_preceding_150_completed_targets" else 0,
                "selection_scores_json": json.dumps(decision_scores.get("A_allocator_objective", {}), sort_keys=True),
            })
            adaptive_rows.append({
                "study_id": b_spec["study_id"], "target_round": target, "block_start": block_start,
                "decision_made": decision_made, "decision_source": decision_source,
                "selected_variant": b_current, "prior_start": prior_start, "prior_end": prior_end,
                "prior_n": prior_n if decision_source == "immediately_preceding_150_completed_targets" else 0,
                "selection_scores_json": json.dumps(decision_scores.get("B_macro_candidate_recall", {}), sort_keys=True),
            })

        # Online state updates occur only after target scoring.
        for name, (shrink, gradient_decay) in cfg.items():
            states[name]["weights"], states[name]["squared_gradients"] = update_adagrad(
                v18, raw, states[name]["weights"], states[name]["squared_gradients"],
                actual, shrink, gradient_decay
            )
        draw = draws[idx]
        for number in draw["nums"]:
            freq[number - 1] += 1
            last_seen[number - 1] = draw["round"]
        pair_counts.update(itertools.combinations(draw["nums"], 2))
        triple_counts.update(itertools.combinations(draw["nums"], 3))
        profile = b.structure_profile(draw["nums"], draws[idx - 1]["nums"])
        for i, value in enumerate(profile):
            profiles[i][value] += 1
        if 201 <= target <= 400:
            warmup_candidate_count += 1

    assert len(history) == 1049 and warmup_candidate_count == 200
    assert len(outer_a_rows) == 849 * 4
    assert len(outer_b_rows) == 849 * 6
    assert len(outer_recall_rows) == 849 * 6 * 5
    assert len(prediction_rows) == 849 * 2
    assert len(adaptive_rows) == 849 * 2
    assert len(conditional_random_rows) == 849 and len(random_bank_rows) == 849

    a_by_target, b_by_target = {}, {}
    for row in outer_a_rows:
        a_by_target.setdefault(row["target_round"], {})[row["allocator"]] = row
    for row in outer_b_rows:
        b_by_target.setdefault(row["target_round"], {})[row["ranker"]] = row
    adaptive_a, adaptive_b = [], []
    for selection in adaptive_rows:
        target = selection["target_round"]
        if selection["study_id"] == a_spec["study_id"]:
            adaptive_a.append({"target_round": target, **a_by_target[target][selection["selected_variant"]]})
        else:
            adaptive_b.append({"target_round": target, **b_by_target[target][selection["selected_variant"]]})
    assert len(adaptive_a) == len(adaptive_b) == 849

    null = v42.exact_null_disjoint30()
    gate_a = strict_gate("H1250_A_PRIOR_ONLY_ADAPTIVE_ALLOCATOR", adaptive_a, null, alpha, block_length, bootstrap_reps, seed_a)
    gate_b = strict_gate("H1250_B_PRIOR_ONLY_ADAPTIVE_RANKER", adaptive_b, null, alpha, block_length, bootstrap_reps, seed_b)
    block_rows = (
        block_stability_rows("H1250_A_PRIOR_ONLY_ADAPTIVE_ALLOCATOR", adaptive_a, null, block_length)
        + block_stability_rows("H1250_B_PRIOR_ONLY_ADAPTIVE_RANKER", adaptive_b, null, block_length)
    )
    b_selector_degenerate = len(b_degenerate_decisions) > 0 and all(b_degenerate_decisions)
    b_selector_degenerate_decision_count = sum(bool(value) for value in b_degenerate_decisions)
    b_selector_non_degenerate_decision_count = sum(not bool(value) for value in b_degenerate_decisions)
    b_selected_ranker_counts = dict(Counter(
        row["selected_variant"] for row in adaptive_rows
        if row["study_id"] == b_spec["study_id"] and row["decision_made"]
    ))

    date = datetime.now(KST).date().isoformat()
    out_root = ROOT / "analysis" / date
    out_root.mkdir(parents=True, exist_ok=True)
    out = out_root / f"H1250_AB_20261110_V2_{datetime.now(KST).strftime('%H%M%S_%f')}"
    out.mkdir(parents=True, exist_ok=False)

    write_csv(out / "PREDICTIONS.csv", prediction_rows)
    write_csv(out / "GEOMETRY_METRICS.csv", outer_a_rows)
    write_csv(out / "RANKER_METRICS.csv", outer_b_rows)
    write_csv(out / "CANDIDATE_RECALL.csv", outer_recall_rows)
    write_csv(out / "ADAPTIVE_SELECTION.csv", adaptive_rows)
    write_csv(out / "CONDITIONAL_RANDOM.csv", conditional_random_rows)
    write_csv(out / "RANDOM_CANDIDATE_BANKS.csv", random_bank_rows)
    write_csv(out / "BLOCK_STABILITY.csv", block_rows)
    write_csv(out / "WINNER_TRACE_A.csv", winner_trace_a_rows)
    write_csv(out / "WINNER_TRACE_B.csv", winner_trace_b_rows)

    recall_summary = {}
    for k in recall_ks:
        for ranker in RANKERS:
            rows = [row for row in outer_recall_rows if row["ranker"] == ranker and int(row["k"]) == k]
            mean_found = statistics.mean(float(row["winning_numbers_found"]) for row in rows)
            recall_summary[f"{ranker}@{k}"] = {
                "mean_winning_numbers_found": mean_found,
                "mean_recall_fraction": mean_found / 6.0,
                "exact_uniform_expected_found": 6.0 * k / 45.0,
                "delta_vs_exact_uniform_expectation": mean_found - 6.0 * k / 45.0,
                "descriptive_only": True,
            }
    ranker_recall30_mean = {
        ranker: recall_summary[f"{ranker}@30"]["mean_winning_numbers_found"] for ranker in RANKERS
    }
    assert max(ranker_recall30_mean.values()) - min(ranker_recall30_mean.values()) <= 1e-12

    gate = {
        "data_cutoff": 1249, "target_range": [401, 1249], "outer_targets": 849,
        "exact_uniform_five_disjoint_ticket_union30_null": {m: float(null[m]) for m in PRIMARY_METRICS},
        "H1250_A": gate_a, "H1250_B": gate_b,
        "H1250_B_selector_diagnostic": {
            "ranker_recall30_invariant_for_all_targets": True,
            "adaptive_selection_objective": b_spec["adaptive_policy"]["objective"],
            "adaptive_selection_degenerate": b_selector_degenerate,
            "degenerate_decision_count": b_selector_degenerate_decision_count,
            "non_degenerate_decision_count": b_selector_non_degenerate_decision_count,
            "selected_ranker_counts": b_selected_ranker_counts,
            "reason": "Recall@30 is invariant because all rankers reorder the same fixed core6+tail24 set. The adaptive selector therefore uses the preregistered equal-weight macro recall fraction across K=10,15,20,25,30, calculated only on the prior 150 completed targets. If every prior score ties, the frozen H,G,C,M,P,T tie-break is retained and degeneracy is reported.",
            "no_posthoc_substitution": True,
        },
        "no_auto_promotion": True, "no_recommendation_numbers": True,
    }
    write_json(out / "STRICT_GATE.json", gate)

    report = [
        "# H1250-A/B preregistered independent research", "",
        f"- Run date (KST): {date}",
        "- Data cutoff: 1249",
        "- Outer evaluation: 401-1249 (849 targets)",
        "- Warm-up for prior-only selection: 201-400 (200 targets)",
        f"- Data SHA256: {hashes['data_sha256']}",
        "- Training rule: target t uses rounds 1..t-1; online updates occur only after scoring target t",
        "- Strict gate: four Bonferroni-adjusted moving-block CI lower bounds > 0, plus any2 positive 50-target block share >= 0.65",
        "", "## H1250-A - fixed candidate bank, allocator geometry only",
        f"- Adaptive strict PASS: {gate_a['strict_portfolio_pass']}",
        f"- Failed gates: {', '.join(gate_a['failed_gates']) if gate_a['failed_gates'] else 'none'}",
        "- Four allocator variants use the identical target-specific core6+tail24 bank.",
        "- WINNER_TRACE_A.csv records each winner's slow-core/blend-tail stage and ticket assignment under each allocator.",
        "- Conditional baseline: 200 random partitions of the same candidate bank per target.",
        "", "## H1250-B - fixed rr allocator, tail24 ranking only",
        f"- Adaptive strict PASS: {gate_b['strict_portfolio_pass']}",
        f"- Failed gates: {', '.join(gate_b['failed_gates']) if gate_b['failed_gates'] else 'none'}",
        "- Random baseline: 200 independent random 30-number candidate banks per target, rr allocated.",
        "- WINNER_TRACE_B.csv records each winner's fixed-bank stage, rank under each tail signal, K retention and rr ticket assignment.",
        "- Candidate recall@K is evaluated at all five preregistered K values; exact uniform expected winning-number count is 6K/45.",
        "- The prior-only B selector uses the equal-weight macro-average recall fraction across K=10,15,20,25,30 from the immediately preceding 150 completed targets.",
        "- Recall@30 is invariant across rankers because the same top30 membership is preserved; it remains an audit metric and cannot select a ranker alone.",
        "- Any remaining tied macro scores use the frozen H,G,C,M,P,T tie-break and are explicitly counted; no post-result substitution is permitted.",
        "", "## Interpretation",
        "- Execution success is not predictive-edge evidence.",
        "- No recommendation numbers or final purchase lines are included.",
        "- No strict threshold, alpha, block length, comparator or candidate family was changed.",
        "- Historical targets are retrospective nested validation, not untouched confirmation; only future draws are genuinely prospective.",
        "",
    ]
    (out / "REPORT.md").write_text("\n".join(report), encoding="utf-8")

    verification = {
        "status": "EXECUTION_VERIFIED",
        "study_ids": [a_spec["study_id"], b_spec["study_id"]],
        "data_cutoff": 1249, "data_sha256": hashes["data_sha256"],
        "target_range": [201, 1249], "warmup_targets": 200,
        "outer_target_range": [401, 1249], "outer_target_count": 849,
        "training_cutoff_rule": "training_through_round = target_round - 1",
        "future_leakage_failures": 0,
        "frozen_dependency_git_blob_checks": hashes["git_blob_sha"],
        "record_counts": {
            "PREDICTIONS.csv": len(prediction_rows), "GEOMETRY_METRICS.csv": len(outer_a_rows),
            "RANKER_METRICS.csv": len(outer_b_rows), "CANDIDATE_RECALL.csv": len(outer_recall_rows),
            "ADAPTIVE_SELECTION.csv": len(adaptive_rows), "CONDITIONAL_RANDOM.csv": len(conditional_random_rows),
            "RANDOM_CANDIDATE_BANKS.csv": len(random_bank_rows), "BLOCK_STABILITY.csv": len(block_rows),
            "WINNER_TRACE_A.csv": len(winner_trace_a_rows), "WINNER_TRACE_B.csv": len(winner_trace_b_rows),
        },
        "random_simulations": {
            "H1250_A_conditional_partitions": len(conditional_random_rows) * conditional_repeats,
            "H1250_B_random_candidate_banks": len(random_bank_rows) * random_banks,
        },
        "ranker_recall30_invariant": True,
        "H1250_B_adaptive_selection_objective": b_spec["adaptive_policy"]["objective"],
        "H1250_B_adaptive_selector_degenerate": b_selector_degenerate,
        "H1250_B_selector_degenerate_decision_count": b_selector_degenerate_decision_count,
        "H1250_B_selector_non_degenerate_decision_count": b_selector_non_degenerate_decision_count,
        "H1250_B_adaptive_selected_ranker_counts": b_selected_ranker_counts,
        "candidate_recall_descriptive_summary": recall_summary,
        "strict_portfolio_pass": {"H1250_A": gate_a["strict_portfolio_pass"], "H1250_B": gate_b["strict_portfolio_pass"]},
        "strict_pass_ready_created": False,
        "no_auto_promotion": True, "no_recommendation_numbers": True, "no_final_purchase_lines": True,
        "output_directory": str(out.relative_to(ROOT)),
    }
    # Manifest includes the final verification bytes; no circular self-hash is stored in VERIFICATION.json.
    verification["artifact_manifest"] = {"status": "PASS", "entries": 13}
    write_json(out / "VERIFICATION.json", verification)
    manifest = write_manifest(out)
    assert manifest["status"] == "PASS" and manifest["entries"] == 13
    print(json.dumps({
        "status": "EXECUTION_VERIFIED", "output_directory": str(out.relative_to(ROOT)),
        "data_cutoff": 1249, "outer_targets": 849, "future_leakage_failures": 0,
        "H1250_A_strict_pass": gate_a["strict_portfolio_pass"],
        "H1250_B_strict_pass": gate_b["strict_portfolio_pass"],
        "H1250_B_selector_degenerate": b_selector_degenerate,
        "H1250_B_selector_non_degenerate_decisions": b_selector_non_degenerate_decision_count,
        "H1250_B_selected_ranker_counts": b_selected_ranker_counts, "manifest": manifest,
    }, ensure_ascii=False))


if __name__ == "__main__":
    if "--preflight" in sys.argv:
        preflight()
    else:
        execute()
