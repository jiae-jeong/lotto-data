#!/usr/bin/env python3
from __future__ import annotations

import csv
import importlib.util
import itertools
import json
import random
import statistics
import sys
from collections import Counter, deque
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'lotto_data.csv'
B_SOURCE = ROOT / 'research/1245_final_pipeline_v3/recovered_original_assets/b_model_backtest.py'
AC_SOURCE = ROOT / 'automation/recovered_models_v2.py'
KST = timezone(timedelta(hours=9))

B_NAMES = (
    'long_frequency', 'current_gap', 'frequency_plus_gap', 'recent_momentum',
    'structure_profile', 'pair_association', 'triple_association', 'combined_equal_rank',
)
AC_NAMES = ('A_v2', 'C_v2', 'contrarian_v2')
MODELS = B_NAMES + AC_NAMES
ROLL = 200
PRIOR_N = 75
RANDOM_PER_TARGET = 120
BLOCK = 50
BOOT = 4000
BASE_MEAN = 0.8
BASE_GE2 = 0.17530810086113546

ROLES = [
    ('consensus', MODELS),
    ('relation', ('pair_association', 'triple_association', 'structure_profile', 'combined_equal_rank')),
    ('frequency_gap', ('long_frequency', 'current_gap', 'frequency_plus_gap')),
    ('recent_structure', ('recent_momentum', 'structure_profile', 'combined_equal_rank')),
    ('ac_crosscheck', ('A_v2', 'C_v2', 'contrarian_v2', 'long_frequency')),
]


def imp(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_draws():
    out = []
    with DATA.open(encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            out.append({
                'round': int(row['round']),
                'date': row['date'],
                'nums': tuple(sorted(int(row[f'no{i}']) for i in range(1, 7))),
            })
    assert out, 'lotto_data.csv is empty'
    assert [x['round'] for x in out] == list(range(1, out[-1]['round'] + 1)), 'round sequence gap'
    return out


def reliability(hist):
    hs = list(hist)[-ROLL:]
    n = len(hs)
    if n == 0:
        return 1.0
    mean = (sum(hs) + PRIOR_N * BASE_MEAN) / (n + PRIOR_N)
    ge2 = (sum(h >= 2 for h in hs) + PRIOR_N * BASE_GE2) / (n + PRIOR_N)
    raw = 1.0 + 2.8 * (mean - BASE_MEAN) + 1.2 * (ge2 - BASE_GE2)
    return max(0.35, min(1.65, raw))


def global_support(preds, hists):
    rel = {m: reliability(hists[m]) for m in MODELS}
    den = sum(rel.values())
    score = {n: sum(rel[m] for m in MODELS if n in preds[m]) / den for n in range(1, 46)}
    return score, rel


def role_score(role_models, preds, rel, gscore):
    den = sum(rel[m] for m in role_models)
    rs = {n: sum(rel[m] for m in role_models if n in preds[m]) / den for n in range(1, 46)}
    return {n: 0.78 * rs[n] + 0.22 * gscore[n] for n in range(1, 46)}


def choose_ticket(score, gscore, prior_lines, role_name):
    # Deterministic selection only: enumerate candidate combinations and take the highest-scoring one.
    pool = sorted(range(1, 46), key=lambda n: (-score[n], -gscore[n], n))[:16]
    best = None
    for ticket in itertools.combinations(pool, 6):
        if prior_lines and tuple(sorted(ticket)) in prior_lines:
            continue
        odd = sum(n % 2 for n in ticket)
        low = sum(n <= 22 for n in ticket)
        bands = len({(n - 1) // 10 for n in ticket})
        consecutive = sum(b - a == 1 for a, b in zip(ticket, ticket[1:]))
        value = sum(score[n] for n in ticket)
        value -= 0.022 * abs(odd - 3) + 0.020 * abs(low - 3) + 0.010 * max(0, consecutive - 2)
        value += 0.004 * bands
        if prior_lines:
            load = {n: sum(n in x for x in prior_lines) for n in ticket}
            value -= sum(0.016 * load[n] for n in ticket if gscore[n] < 0.30)
        if role_name == 'ac_crosscheck' and prior_lines:
            value -= 0.018 * max(len(set(ticket) & set(x)) for x in prior_lines)
        key = (value, tuple(-n for n in ticket))
        if best is None or key > best[0]:
            best = (key, ticket)
    assert best is not None
    return tuple(sorted(best[1]))


def build_portfolio(preds, hists):
    gscore, rel = global_support(preds, hists)
    lines, details = [], []
    for role_name, role_models in ROLES:
        rs = role_score(role_models, preds, rel, gscore)
        ticket = choose_ticket(rs, gscore, lines, role_name)
        lines.append(ticket)
        details.append({
            'role': role_name,
            'models': list(role_models),
            'ticket': list(ticket),
            'numbers': [
                {
                    'number': n,
                    'role_score': rs[n],
                    'global_support': gscore[n],
                    'supporting_models': [m for m in MODELS if n in preds[m]],
                }
                for n in ticket
            ],
        })
    assert len(lines) == 5 and len({tuple(x) for x in lines}) == 5
    return lines, details, rel, gscore


def metrics(lines, actual):
    sets = [set(x) for x in lines]
    hits = [len(s & actual) for s in sets]
    union = set().union(*sets)
    overlaps = [len(sets[i] & sets[j]) for i in range(5) for j in range(i + 1, 5)]
    return {
        'max_hits': max(hits),
        'any2': int(max(hits) >= 2),
        'any3': int(max(hits) >= 3),
        'any4': int(max(hits) >= 4),
        'any5': int(max(hits) >= 5),
        'any6': int(max(hits) >= 6),
        'winning_union_coverage': len(union & actual),
        'union_size': len(union),
        'mean_overlap': statistics.mean(overlaps),
        'max_overlap': max(overlaps),
    }


def permuted(lines, rng):
    # Randomness is used only for the matched null comparator, never for final ticket selection.
    labels = list(range(1, 46))
    shuffled = labels[:]
    rng.shuffle(shuffled)
    mapping = dict(zip(labels, shuffled))
    return [tuple(sorted(mapping[n] for n in row)) for row in lines]


def bootstrap_ci(diffs, alpha, seed):
    blocks = [diffs[i:i + BLOCK] for i in range(0, len(diffs), BLOCK)]
    rng = random.Random(seed)
    reps = []
    for _ in range(BOOT):
        sampled = [blocks[rng.randrange(len(blocks))] for __ in range(len(blocks))]
        flat = [x for block in sampled for x in block]
        reps.append(statistics.mean(flat))
    reps.sort()
    lo = reps[int((alpha / 2) * (len(reps) - 1))]
    hi = reps[int((1 - alpha / 2) * (len(reps) - 1))]
    return [lo, hi]


def positive_block_share(diffs):
    vals = [statistics.mean(diffs[i:i + BLOCK]) for i in range(0, len(diffs), BLOCK)]
    return sum(v > 0 for v in vals) / len(vals)


def avg(rows, key):
    return statistics.mean(float(row[key]) for row in rows)


def main():
    run_date = sys.argv[1] if len(sys.argv) > 1 else datetime.now(KST).date().isoformat()
    draws = load_draws()
    cutoff = draws[-1]['round']
    target = cutoff + 1
    seed = 202600000000 + target
    outdir = ROOT / 'analysis' / run_date
    outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / f'FIVE_ROLE_RESEARCH_{target}_V9.json'

    b = imp(B_SOURCE, 'b_v9')
    ac = imp(AC_SOURCE, 'ac_v9')
    bank = b.feature_structure_bank(b.make_structure_bank())
    freq = [0] * 45
    last = [0] * 45
    pair_counts = Counter()
    triple_counts = Counter()
    profiles = [Counter() for _ in range(6)]

    warmup = min(200, len(draws))
    assert warmup == 200, 'at least 200 historical draws required'
    for draw in draws[:warmup]:
        for x in draw['nums']:
            freq[x - 1] += 1
            last[x - 1] = draw['round']
        pair_counts.update(itertools.combinations(draw['nums'], 2))
        triple_counts.update(itertools.combinations(draw['nums'], 3))
        profile = b.structure_profile(draw['nums'], None)
        for i, value in enumerate(profile[:5]):
            profiles[i][value] += 1
    for i in range(1, warmup):
        profiles[5][b.structure_profile(draws[i]['nums'], draws[i - 1]['nums'])[5]] += 1

    hists = {m: deque(maxlen=ROLL) for m in MODELS}
    observed, null_rows = [], []
    diffs = {k: [] for k in ('max_hits', 'any2', 'any3', 'winning_union_coverage')}
    current = current_details = current_rel = current_g = current_preds = None

    for idx in range(warmup, len(draws) + 1):
        hist = [x['nums'] for x in draws[:idx]]
        preds = {
            **b.predictions_for_round(draws, idx, freq, last, pair_counts, triple_counts, profiles, bank),
            **ac.predict(hist),
        }
        lines, details, rel, gscore = build_portfolio(preds, hists)
        if idx == len(draws):
            current, current_details, current_rel, current_g, current_preds = lines, details, rel, gscore, preds
            break

        actual = set(draws[idx]['nums'])
        hist_target = idx + 1
        if hist_target >= 401:
            om = metrics(lines, actual)
            om['target'] = hist_target
            observed.append(om)
            rng = random.Random(seed + hist_target)
            null_metrics = [metrics(permuted(lines, rng), actual) for _ in range(RANDOM_PER_TARGET)]
            mean_null = {k: statistics.mean(float(x[k]) for x in null_metrics) for k in null_metrics[0]}
            mean_null['target'] = hist_target
            null_rows.append(mean_null)
            for k in diffs:
                diffs[k].append(float(om[k]) - mean_null[k])

        for model in MODELS:
            hists[model].append(len(set(preds[model]) & actual))

        draw = draws[idx]
        for x in draw['nums']:
            freq[x - 1] += 1
            last[x - 1] = draw['round']
        pair_counts.update(itertools.combinations(draw['nums'], 2))
        triple_counts.update(itertools.combinations(draw['nums'], 3))
        profile = b.structure_profile(draw['nums'], draws[idx - 1]['nums'])
        for i, value in enumerate(profile):
            profiles[i][value] += 1

    keys = ['max_hits', 'any2', 'any3', 'any4', 'any5', 'any6', 'winning_union_coverage', 'union_size', 'mean_overlap', 'max_overlap']
    score = {
        'policy': {k: avg(observed, k) for k in keys},
        'matched_label_permutation': {k: avg(null_rows, k) for k in keys},
    }
    score['delta'] = {k: score['policy'][k] - score['matched_label_permutation'][k] for k in keys}

    alpha = 0.05 / 4
    inference = {}
    for j, k in enumerate(diffs):
        inference[k] = {
            'adjusted_ci_delta': bootstrap_ci(diffs[k], alpha, seed + 9000 + j),
            'positive_50_round_block_share': positive_block_share(diffs[k]),
        }
    inference['strict_portfolio_pass'] = (
        inference['max_hits']['adjusted_ci_delta'][0] > 0
        and inference['any2']['adjusted_ci_delta'][0] > 0
        and inference['any3']['adjusted_ci_delta'][0] > 0
        and inference['any2']['positive_50_round_block_share'] >= 0.65
    )

    final_lines = [list(x) for x in current]
    integrity = {
        'five_distinct_lines': len(final_lines) == 5 and len({tuple(x) for x in final_lines}) == 5,
        'six_numbers_each': all(len(x) == 6 for x in final_lines),
        'range_unique_sorted': all(x == sorted(x) and len(set(x)) == 6 and all(1 <= n <= 45 for n in x) for x in final_lines),
        'five_distinct_roles': len({x['role'] for x in current_details}) == 5,
        'selection_uses_randomness': False,
        'random_fallback_allowed': False,
        'union_size': len({n for row in final_lines for n in row}),
    }
    assert integrity['five_distinct_lines']
    assert integrity['six_numbers_each']
    assert integrity['range_unique_sorted']
    assert integrity['five_distinct_roles']
    assert integrity['selection_uses_randomness'] is False
    assert integrity['random_fallback_allowed'] is False

    failed_gates = [
        k for k in ('max_hits', 'any2', 'any3')
        if inference[k]['adjusted_ci_delta'][0] <= 0
    ]
    if inference['any2']['positive_50_round_block_share'] < 0.65:
        failed_gates.append('any2_block_stability')

    payload = {
        'created_kst': datetime.now(KST).isoformat(),
        'run_date_kst': run_date,
        'target_round': target,
        'data_cutoff': cutoff,
        'policy': 'ADAPTIVE_FIVE_ROLE_NONRANDOM_PORTFOLIO_V9',
        'no_future_leakage': True,
        'selection_rule': 'Each role deterministically scores all candidate combinations from historical-only model predictions and trailing historical reliability. Randomness is prohibited in final selection and allowed only in the matched null comparator.',
        'roles': current_details,
        'model_reliability': current_rel,
        'current_model_predictions': {m: list(current_preds[m]) for m in MODELS},
        'global_number_support': {str(n): current_g[n] for n in range(1, 46)},
        'final_lines': final_lines,
        'walkforward_targets': len(observed),
        'random_comparator': 'Random permutation of labels 1..45 applied jointly to the five deterministic tickets; comparator only, never a source of purchase numbers.',
        'random_per_target': RANDOM_PER_TARGET,
        'scorecard': score,
        'inference': inference,
        'integrity': integrity,
        'learning_status': 'STRICT_PASS' if inference['strict_portfolio_pass'] else 'ITERATE_NEXT_CYCLE_WITH_FAILED_GATES_RECORDED',
        'failed_gates': failed_gates,
        'classification': 'STRICTLY_VALIDATED_RESEARCH_PORTFOLIO' if inference['strict_portfolio_pass'] else 'RESEARCH_BASED_NONRANDOM_CANDIDATE_UNVALIDATED_EDGE',
    }
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({
        'status': 'PASS',
        'target': target,
        'data_cutoff': cutoff,
        'strict_pass': inference['strict_portfolio_pass'],
        'failed_gates': failed_gates,
        'final_lines': final_lines,
        'roles': [x['role'] for x in current_details],
        'selection_uses_randomness': False,
        'output': str(out.relative_to(ROOT)),
    }, ensure_ascii=False))


if __name__ == '__main__':
    main()
