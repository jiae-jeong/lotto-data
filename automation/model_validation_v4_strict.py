#!/usr/bin/env python3
from __future__ import annotations

import csv
import importlib.util
import json
import math
import random
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'lotto_data.csv'
V3 = ROOT / 'automation' / 'weekly_purchase_final_v3.py'
OUTROOT = ROOT / 'analysis'
KST = timezone(timedelta(hours=9))
START_TARGET_INDEX = 200
BLOCK_SIZE = 100
RANDOM_DIVERSIFIED_BUNDLES = 1000
BOOTSTRAP_REPS = 3000
SEED = 202610231107
PRIMARY = ('any_2plus', 'max_hits', 'winning_union_coverage')
SECONDARY = ('any_3plus', 'any_4plus')


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def exact_single_ticket_baseline():
    den = math.comb(45, 6)
    probs = {k: math.comb(6, k) * math.comb(39, 6-k) / den for k in range(7)}
    return {
        'mean_hits': sum(k * probs[k] for k in probs),
        'rate_ge2': sum(probs[k] for k in range(2, 7)),
        'rate_ge3': sum(probs[k] for k in range(3, 7)),
        'rate_ge4': sum(probs[k] for k in range(4, 7)),
        'rate_ge5': sum(probs[k] for k in range(5, 7)),
        'rate_ge6': probs[6],
        'hit_probabilities': probs,
    }


def ci_bootstrap(deltas, reps=BOOTSTRAP_REPS, seed=SEED):
    rng = random.Random(seed)
    n = len(deltas)
    vals = []
    for _ in range(reps):
        vals.append(sum(deltas[rng.randrange(n)] for __ in range(n)) / n)
    vals.sort()
    lo = vals[int(0.025 * reps)]
    hi = vals[min(reps-1, int(0.975 * reps))]
    return [lo, hi]


def summarize_model_ticket(records, model_name, baseline):
    hits = [r['single_hits'][model_name] for r in records]
    obs = {
        'mean_hits': statistics.mean(hits),
        'rate_ge2': statistics.mean(int(h >= 2) for h in hits),
        'rate_ge3': statistics.mean(int(h >= 3) for h in hits),
        'rate_ge4': statistics.mean(int(h >= 4) for h in hits),
        'rate_ge5': statistics.mean(int(h >= 5) for h in hits),
        'rate_ge6': statistics.mean(int(h >= 6) for h in hits),
    }
    out = {'observed': obs, 'exact_uniform_random': {k: baseline[k] for k in obs}, 'delta': {}, 'bootstrap_95ci_delta': {}}
    for j, k in enumerate(obs):
        base = baseline[k]
        if k == 'mean_hits': per = [h - base for h in hits]
        else:
            threshold = int(k[-1])
            per = [int(h >= threshold) - base for h in hits]
        out['delta'][k] = obs[k] - base
        out['bootstrap_95ci_delta'][k] = ci_bootstrap(per, seed=SEED + 100*j + sum(ord(c) for c in model_name))
    return out


def block_summaries(records):
    out = []
    for bi in range(0, len(records), BLOCK_SIZE):
        block = records[bi:bi+BLOCK_SIZE]
        if not block:
            continue
        row = {'start_round': block[0]['target'], 'end_round': block[-1]['target'], 'n': len(block)}
        for k in PRIMARY + SECONDARY:
            row[f'delta_{k}'] = statistics.mean(r['portfolio_model'][k] - r['diversified_random_mean'][k] for r in block)
        out.append(row)
    return out


def strict_portfolio_gate(global_metrics, blocks):
    # A predictive portfolio must beat the structure-matched 30-unique random baseline,
    # not ordinary five-ticket random. Require statistically positive primary metrics.
    primary_ci_positive = all(global_metrics[k]['bootstrap_95ci_delta'][0] > 0 for k in PRIMARY)
    primary_mean_positive = all(global_metrics[k]['delta'] > 0 for k in PRIMARY)
    positive_block_share = {}
    for k in PRIMARY:
        vals = [b[f'delta_{k}'] for b in blocks]
        positive_block_share[k] = sum(v > 0 for v in vals) / len(vals)
    block_stability = all(positive_block_share[k] >= 0.70 for k in PRIMARY)
    secondary_noninferior = all(global_metrics[k]['bootstrap_95ci_delta'][1] >= 0 for k in SECONDARY)
    passed = primary_ci_positive and primary_mean_positive and block_stability and secondary_noninferior
    return {
        'status': 'PASS' if passed else 'FAIL',
        'primary_metrics': list(PRIMARY),
        'secondary_metrics': list(SECONDARY),
        'criteria': {
            'primary_mean_delta_gt_0': primary_mean_positive,
            'primary_bootstrap_95ci_lower_gt_0': primary_ci_positive,
            'primary_positive_block_share_ge_70pct': block_stability,
            'secondary_ci_not_strictly_below_zero': secondary_noninferior,
        },
        'positive_block_share': positive_block_share,
    }


def main():
    date = sys.argv[1] if len(sys.argv) > 1 else datetime.now(KST).date().isoformat()
    v3 = load_module(V3, 'weekly_v3_validation')
    rows = v3.load_rows()
    model = v3.load_models()
    assert rows[-1][0] == 1246

    records = []
    model_names = ('A_v2', 'C_v2', 'contrarian_v2')
    for i in range(START_TARGET_INDEX, len(rows)):
        hist = rows[:i]
        target, actual, _bonus = rows[i]
        assert hist[-1][0] == target - 1
        draws = [x[1] for x in hist]
        pred = model.predict(draws)
        single_hits = {name: len(set(pred[name]) & set(actual)) for name in model_names}

        portfolio, _source = v3.model_guided(hist, model)
        pm = v3.metrics(portfolio, actual)
        rng = random.Random(SEED + target)
        rand_metrics = []
        for _ in range(RANDOM_DIVERSIFIED_BUNDLES):
            rand_metrics.append(v3.random_diversified(actual, rng))
        keys = list(pm.keys())
        rm = {k: statistics.mean(float(x[k]) for x in rand_metrics) for k in keys}
        records.append({
            'target': target,
            'training_through': target - 1,
            'single_hits': single_hits,
            'portfolio_model': pm,
            'diversified_random_mean': rm,
        })

    baseline = exact_single_ticket_baseline()
    single = {name: summarize_model_ticket(records, name, baseline) for name in model_names}

    portfolio_metrics = {}
    for j, k in enumerate(PRIMARY + SECONDARY):
        model_mean = statistics.mean(float(r['portfolio_model'][k]) for r in records)
        random_mean = statistics.mean(float(r['diversified_random_mean'][k]) for r in records)
        deltas = [float(r['portfolio_model'][k]) - float(r['diversified_random_mean'][k]) for r in records]
        portfolio_metrics[k] = {
            'model_mean': model_mean,
            'diversity_matched_random_mean': random_mean,
            'delta': model_mean - random_mean,
            'bootstrap_95ci_delta': ci_bootstrap(deltas, seed=SEED + 1000 + j),
        }

    blocks = block_summaries(records)
    gate = strict_portfolio_gate(portfolio_metrics, blocks)

    single_any_edge = any(
        single[name]['bootstrap_95ci_delta']['mean_hits'][0] > 0
        and single[name]['bootstrap_95ci_delta']['rate_ge2'][0] > 0
        for name in model_names
    )

    result = {
        'date_kst': date,
        'data_cutoff': rows[-1][0],
        'targets': len(records),
        'target_range': [records[0]['target'], records[-1]['target']],
        'leakage_rule': 'For target t, every prediction uses only rounds <= t-1.',
        'single_ticket_models': single,
        'single_ticket_predictive_edge_found': single_any_edge,
        'portfolio_model': {
            'definition': 'V3 model_guided 30-unique portfolio',
            'comparison_baseline': 'uniform random 30 unique numbers, randomly partitioned into five 6-number tickets',
            'random_bundles_per_target': RANDOM_DIVERSIFIED_BUNDLES,
            'metrics': portfolio_metrics,
            'nonoverlap_time_blocks': blocks,
            'strict_promotion_gate': gate,
        },
        'verdict': 'MODEL_VALIDATED' if (single_any_edge and gate['status'] == 'PASS') else 'NO_VALIDATED_PREDICTIVE_EDGE',
        'interpretation': '30-unique coverage is a portfolio-structure property. It is not predictive evidence unless the model-guided 30-number set beats a 30-unique random baseline on untouched time-ordered targets with positive confidence bounds.',
    }

    outdir = OUTROOT / date
    outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / 'MODEL_VALIDATION_V4_STRICT.json'
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'PASS', 'verdict': result['verdict'], 'targets': len(records), 'portfolio_gate': gate['status'], 'single_ticket_edge': single_any_edge, 'output': str(out)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
