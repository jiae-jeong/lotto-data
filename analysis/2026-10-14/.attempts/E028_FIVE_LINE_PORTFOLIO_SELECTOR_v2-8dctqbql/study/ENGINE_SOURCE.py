"""Registered, reproducible research jobs; historical data, no recommendations."""
from __future__ import annotations
import csv
import hashlib
import json
import math
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

COMPONENTS = ['long_frequency', 'current_gap', 'frequency_plus_gap', 'recent_momentum',
              'structure_profile', 'pair_association', 'triple_association']
ENSEMBLE = 'combined_equal_rank'
CACHE = 'analysis/2026-10-12/REGIME_DYNAMIC_NESTED_v1/base_predictions_reused.csv'
DATA = 'analysis/2026-10-12/lotto_data_1_1245_snapshot.csv'
DATA_SHA = 'e534123cd7227f8c21d32251a567edeb018e7d1d9c4b049e4d23fb987f2619a4'
MODELS = COMPONENTS + [ENSEMBLE]

def experiment_signature(task):
    """Question names, dates and cosmetic source changes cannot create novelty."""
    recipes = {
        'family': {'dataset': DATA_SHA, 'targets': [601, 1245],
                   'drop_hybrid': [1, 1, 0, 1, 1, 1, 1], 'family_balance': [1, 1, 0, 1, 1, .5, .5],
                   'geometry': 'current-ticket 1/(1+sum(other-overlap/6))', 'number_tie': 'lower'},
        'tail': {'dataset': DATA_SHA, 'targets': [601, 1245], 'exponents': [0., .5, 1., 2.],
                 'objectives': [3, 4], 'nested_past_targets': 200, 'ties': 'other tail; mean; lower exponent'},
        'power': {'lottery': [45, 6], 'tails': [3, 4], 'effects': [1.5, 2.],
                  'samples': [200, 500, 1000, 2000, 5000, 10000], 'alpha': .05 / 4}}
    if task['kind'] in recipes:
        payload = recipes[task['kind']]
    else:
        spec = task.get('spec') or {}
        if not spec.get('novelty_signature'):
            raise ValueError('New study requires a frozen novelty_signature')
        payload = {'kind': task['kind'],
                   'data_cutoff': spec.get('data_cutoff'), 'target_rounds': spec.get('target_rounds'),
                   'training_cutoff_rule': spec.get('training_cutoff_rule'),
                   'primary_metric': spec.get('primary_metric'), 'secondary_metrics': spec.get('secondary_metrics'),
                   'comparator': spec.get('comparator'), 'baseline': spec.get('baseline'),
                   'multiplicity_correction': spec.get('multiplicity_correction'),
                   'block_stability': spec.get('block_stability'), 'tie_break': spec.get('tie_break'),
                   'novelty_signature': spec['novelty_signature']}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def digest(path):
    path = Path(path)
    content = path.read_bytes()
    if path.suffix.lower() in {'.csv','.json','.md','.py','.txt','.yml','.yaml','.log'}:
        content = content.replace(b'\r\n', b'\n')
    return hashlib.sha256(content).hexdigest()

def raw_digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def raw_size(path):
    return Path(path).stat().st_size

def portable_size(path):
    path = Path(path)
    content = path.read_bytes()
    if path.suffix.lower() in {'.csv','.json','.md','.py','.txt','.yml','.yaml','.log'}:
        content = content.replace(b'\r\n', b'\n')
    return len(content)

def readcsv(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))

def jsonfile(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n')

def csvfile(path, records):
    if not records:
        raise ValueError('Empty research artifact')
    with Path(path).open('x', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]), lineterminator='\n')
        writer.writeheader(); writer.writerows(records)

def load_panel(root):
    root = Path(root)
    if digest(root / DATA) != DATA_SHA:
        raise ValueError('Verified snapshot SHA changed; register a new data specification')
    draws = readcsv(root / DATA)
    if [int(r['round']) for r in draws] != list(range(1, 1246)):
        raise ValueError('Incomplete snapshot')
    actual = {}
    for row in draws:
        numbers = tuple(sorted(int(row[f'no{i}']) for i in range(1, 7)))
        bonus = int(row['bonus'])
        if len(set(numbers)) != 6 or not all(1 <= n <= 45 for n in numbers) or bonus in numbers or not 1 <= bonus <= 45:
            raise ValueError('Invalid draw')
        actual[int(row['round'])] = numbers
    manifest = readcsv(root / 'analysis/2026-10-12/REGIME_DYNAMIC_NESTED_v1/FINAL_SHA256_MANIFEST.csv')
    cache_record = next(r for r in manifest if r['file'] == 'base_predictions_reused.csv')
    if raw_digest(root / CACHE) != cache_record['sha256'] or raw_size(root / CACHE) != int(cache_record['bytes']):
        raise ValueError('Published component-cache hash mismatch')
    lookup = {}
    for row in readcsv(root / CACHE):
        t = int(row['target_round']); m = row['model']
        pred = tuple(map(int, row['predicted_numbers'].split()))
        if (t, m) in lookup or m not in MODELS or not 201 <= t <= 1245 or int(row['training_through_round']) != t - 1:
            raise ValueError('Duplicate, invalid model or future cutoff')
        if len(set(pred)) != 6 or not all(1 <= n <= 45 for n in pred):
            raise ValueError('Invalid component ticket')
        if tuple(map(int, row['actual_numbers'].split())) != actual[t] or len(set(pred) & set(actual[t])) != int(row['hits']):
            raise ValueError('Component outcome mismatch')
        lookup[t, m] = pred
    if set(lookup) != {(t, m) for t in range(201, 1246) for m in MODELS}:
        raise ValueError('Missing component forecasts')
    return actual, lookup

def ticket_vote(tickets, weights):
    score = {n: 0.0 for n in range(1, 46)}
    for ticket, weight in zip(tickets, weights):
        for n in ticket:
            score[n] += float(weight)
    return tuple(sorted(sorted(score, key=lambda n: (-score[n], n))[:6]))

def overlap_weights(tickets, exponent):
    return [(1 + sum(len(set(a) & set(b)) / 6 for j, b in enumerate(tickets) if j != i)) ** (-exponent)
            for i, a in enumerate(tickets)]

def tail_choice(prior, objective):
    """Each prior row is a past out-of-sample reward for four frozen weights."""
    if len(prior) != 200:
        raise ValueError('Nested validation must contain exactly 200 past targets')
    return max(range(4), key=lambda j: (sum(r[j] >= objective for r in prior),
        sum(r[j] >= (4 if objective == 3 else 3) for r in prior), sum(r[j] for r in prior), -j))

def metrics(values):
    n = len(values); mean = sum(values) / n
    return {'n': n, 'mean_hits': mean, 'variance_hits_population': sum((h - mean) ** 2 for h in values) / n,
            **{f'hits_{k}_count': values.count(k) for k in range(7)},
            **{f'rate_ge_{k}': sum(h >= k for h in values) / n for k in [2, 3, 4, 5, 6]}}

def pmf():
    return [math.comb(6, k) * math.comb(39, 6 - k) / math.comb(45, 6) for k in range(7)]

def binomial_mass(n, p):
    logs = [math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)
            + k * math.log(p) + (n - k) * math.log1p(-p) for k in range(n + 1)]
    highest = max(logs); values = [math.exp(v - highest) for v in logs]
    total = math.fsum(values)
    return [v / total for v in values]

def exact_binomial(n, count, p):
    mass = binomial_mass(n, p)
    return min(1., math.fsum(v for v in mass if v <= mass[count] * (1 + 1e-10)))

def holm(records, field='p_raw'):
    maximum = 0.0
    for rank, index in enumerate(sorted(range(len(records)), key=lambda i: records[i][field])):
        maximum = max(maximum, min(1., records[index][field] * (len(records) - rank)))
        records[index]['holm_p'] = maximum

def comparison_tests(series, primary):
    import numpy as np
    if np.__version__ != '2.3.5':
        raise RuntimeError('Empirical bootstrap requires frozen NumPy 2.3.5; use independent stdlib fallback')
    names = list(series); hs = np.asarray([series[name] for name in names]).T
    n = len(hs); features = np.stack([hs, hs >= 2, hs >= 3, hs >= 4], axis=2).astype(float)
    rng = np.random.Generator(np.random.PCG64(2026101210))
    starts = rng.integers(0, n, size=(10000, math.ceil(n / 20)))
    indices = ((starts[:, :, None] + np.arange(20)) % n).reshape(10000, -1)[:, :n]
    weights = np.zeros((10000, n), dtype=np.int16)
    np.add.at(weights, (np.arange(10000)[:, None], indices), 1)
    boot = (weights.astype(float) @ features.reshape(n, -1) / n).reshape(10000, len(names), 4)
    observed = features.mean(axis=0); probability = np.asarray(pmf()); total = np.array([1.])
    for _ in range(n): total = np.convolve(total, probability)
    total /= total.sum()
    baseline = [float(probability @ np.arange(7))] + [float(probability[k:].sum()) for k in [2, 3, 4]]
    result = []
    for name in primary:
        i = names.index(name)
        for other in ['UNIFORM_EXACT', ENSEMBLE, 'EQUAL_VOTE_7']:
            for m, metric in enumerate(['mean_hits', 'rate_ge_2', 'rate_ge_3', 'rate_ge_4']):
                if other == 'UNIFORM_EXACT':
                    delta = float(observed[i, m] - baseline[m]); samples = boot[:, i, m] - baseline[m]
                    count = int(features[:, i, m].sum())
                    p = min(1., 2 * min(float(total[:count + 1].sum()), float(total[count:].sum()))) if m == 0 else exact_binomial(n, count, baseline[m])
                else:
                    j = names.index(other); delta = float(observed[i, m] - observed[j, m])
                    samples = boot[:, i, m] - boot[:, j, m]
                    p = float((1 + (np.abs(samples - delta) >= abs(delta) - 1e-12).sum()) / 10001)
                result.append({'policy': name, 'comparator': other, 'metric': metric, 'delta': delta,
                               'ci95_low': float(np.quantile(samples, .025)), 'ci95_high': float(np.quantile(samples, .975)), 'p_raw': p})
    holm(result)
    return result

def protect(root):
    names = subprocess.check_output(['git', 'ls-files', '-z'], cwd=root).decode().split('\0')
    return {name: digest(Path(root) / name) for name in names if name}

def check_protection(root, original):
    changed = [p for p, h in original.items() if not (Path(root) / p).is_file() or digest(Path(root) / p) != h]
    if changed: raise ValueError('Protected repository files changed: ' + ', '.join(changed))

def predictor_study(root, out, task):
    actual, lookup = load_panel(root)
    schemes = {}; candidates = {}; candidate_hits = []
    for t in range(201, 1246):
        tickets = [lookup[t, m] for m in COMPONENTS]
        weighted = [ticket_vote(tickets, overlap_weights(tickets, power)) for power in [0., .5, 1., 2.]]
        candidates[t] = weighted
        candidate_hits.append([len(set(q) & set(actual[t])) for q in weighted])
        schemes[t] = {
            'EQUAL_VOTE_7': weighted[0],
            'DROP_HYBRID_VOTE_6': ticket_vote(tickets, [1, 1, 0, 1, 1, 1, 1]),
            'FAMILY_BALANCED_5': ticket_vote(tickets, [1, 1, 0, 1, 1, .5, .5]),
            'OVERLAP_WEIGHTED_7': weighted[2]}
    series = {m: [] for m in MODELS + ['EQUAL_VOTE_7']}; records = []; trace = []
    primary = ['DROP_HYBRID_VOTE_6', 'FAMILY_BALANCED_5', 'OVERLAP_WEIGHTED_7'] if task['kind'] == 'family' else ['NESTED_TAIL_3', 'NESTED_TAIL_4']
    series.update({m: [] for m in primary})
    for t in range(601, 1246):
        selected = {m: lookup[t, m] for m in MODELS}
        selected['EQUAL_VOTE_7'] = schemes[t]['EQUAL_VOTE_7']
        if task['kind'] == 'family':
            selected.update({m: schemes[t][m] for m in primary})
        else:
            i = t - 201; prior = candidate_hits[i - 200:i]
            for goal, name in [(3, 'NESTED_TAIL_3'), (4, 'NESTED_TAIL_4')]:
                choice = tail_choice(prior, goal)
                selected[name] = candidates[t][choice]
                trace.append({'policy': name, 'target_round': t, 'inner_start': t - 200,
                              'inner_end': t - 1, 'inner_n': 200, 'exponent_index': choice,
                              'exponent': [0., .5, 1., 2.][choice], 'objective': goal})
        for name, q in selected.items():
            hit = len(set(q) & set(actual[t])); series[name].append(hit)
            records.append({'policy': name, 'target_round': t, 'training_through_round': t - 1,
                            'predicted_numbers': ' '.join(map(str, q)), 'actual_numbers': ' '.join(map(str, actual[t])), 'hits': hit})
    scorecard = [{'policy': name, **metrics(values)} for name, values in series.items()]
    tests = comparison_tests(series, primary)
    csvfile(out / 'PREDICTIONS.csv', records); csvfile(out / 'METRICS.csv', scorecard)
    csvfile(out / 'COMPARISONS.csv', tests)
    if trace:
        csvfile(out / 'NESTED_TRACE.csv', trace)
        csvfile(out / 'PAST_CANDIDATE_REWARDS.csv', [dict(target_round=i + 201, **{f'lambda_{j}': int(h) for j, h in enumerate(row)}) for i, row in enumerate(candidate_hits)])
    # Independent replay uses explicit membership scoring, not ticket_vote.
    seen = set()
    for row in records:
        name = row['policy']; t = row['target_round']; key = name, t
        assert key not in seen; seen.add(key)
        nums = tuple(map(int, row['predicted_numbers'].split()))
        assert len(set(nums)) == 6 and all(1 <= n <= 45 for n in nums)
        assert row['training_through_round'] == t - 1
        assert row['hits'] == len(set(nums) & set(actual[t]))
        if name in primary and task['kind'] == 'family':
            tickets = [lookup[t, m] for m in COMPONENTS]
            if name == 'DROP_HYBRID_VOTE_6': weights = [1, 1, 0, 1, 1, 1, 1]
            elif name == 'FAMILY_BALANCED_5': weights = [1, 1, 0, 1, 1, .5, .5]
            else: weights = [1 / (1 + sum(len(set(q) & set(other)) / 6 for j, other in enumerate(tickets) if i != j)) for i, q in enumerate(tickets)]
            rank = sorted(range(1, 46), key=lambda n: (-sum(w for q, w in zip(tickets, weights) if n in q), n))
            assert nums == tuple(sorted(rank[:6]))
    for row in trace:
        t = row['target_round']; prior = candidate_hits[t - 201 - 200:t - 201]; goal = row['objective']
        independently = sorted(range(4), key=lambda j: (sum(r[j] >= goal for r in prior),
            sum(r[j] >= (4 if goal == 3 else 3) for r in prior), sum(r[j] for r in prior), -j))[-1]
        assert independently == row['exponent_index']
        altered = [r[:] for r in candidate_hits]; altered[t - 201:] = [[6] * 4] * (1246 - t)
        assert tail_choice(altered[t - 201 - 200:t - 201], goal) == independently
    verification = {'status': 'PASS', 'prediction_records_checked': len(records), 'unique_targets': 645,
                    'independent_weight_predictions': len(primary) * 645 if task['kind'] == 'family' else 0,
                    'independent_nested_decisions': len(trace), 'future_mutation_checks': len(trace), 'future_predictions': 0}
    jsonfile(out / 'VERIFICATION.json', verification)
    lines = ['# ' + task['question'], '', '## NEW STUDY', '',
             'POST_HOC_EXPLORATORY. Frozen B component cache, targets 601..1245, n=645. All tickets use only pre-target forecasts; nested settings use the preceding 200 out-of-sample rewards. No future prediction or recommendation.', '',
             '| Policy | Mean | 2+ | 3+ | 4+ |', '|---|---:|---:|---:|---:|']
    for r in scorecard: lines.append(f"|{r['policy']}|{r['mean_hits']:.6f}|{r['rate_ge_2']:.3%}|{r['rate_ge_3']:.3%}|{r['rate_ge_4']:.3%}|")
    lines += ['', '| UNIFORM_EXACT | 0.800000 | 17.531% | 2.383% | 0.139% |', '', '## NEW FINDING', '']
    for name in primary:
        r = next(r for r in scorecard if r['policy'] == name)
        passed = [r for r in tests if r['policy'] == name and r['holm_p'] < .05 and r['delta'] > 0]
        lines.append(f"- {name}: mean={r['mean_hits']:.6f}; 3+={r['hits_3_count'] + r['hits_4_count'] + r['hits_5_count'] + r['hits_6_count']} draws; 4+={r['hits_4_count'] + r['hits_5_count'] + r['hits_6_count']} draws; positive Holm<.05 comparisons={len(passed)}. No predictive promotion.")
    lines += ['', 'Family grouping is semantic, not a claim of statistical independence. B pair/triple greedy tickets differ from batch001 residual-node tickets. Current-ticket overlap weights never use the current outcome. Bootstrap length20, 10000 replicates; conditional on observed fitted policy paths. Holm covers all primary policies x3 controls x4 metrics in this registered job. Historical design selection is not removed by correction.', '',
              '## MAINTENANCE/RECHECK', '', 'Verified snapshot and published cache hashes, cutoff and outcomes. Existing B/Monte Carlo/H001/H002/regime studies were read and reused as controls, not repeated as new studies.', '',
              '## NEXT TEST', '', 'Retain failed hypotheses. Independently test tail-oriented weight selection, then exact high-tail sample-size/precision, or a new preregistered hypothesis. Do not rerun this same job on the same data as a new daily contribution. Future evaluation requires pre-draw registration.']
    with (out / 'REPORT.md').open('x', encoding='utf-8') as f: f.write('\n'.join(lines) + '\n')
    return {'executed_cases': len(primary) * 645, 'verification': verification, 'positive_adjusted_comparisons': sum(r['holm_p'] < .05 and r['delta'] > 0 for r in tests)}

def power_study(root, out, task):
    probabilities = pmf(); records = []
    for goal in [3, 4]:
        p0 = sum(probabilities[goal:])
        for n in [200, 500, 1000, 2000, 5000, 10000]:
            null = binomial_mass(n, p0)
            upper = [0.] * (n + 2)
            for k in range(n, -1, -1): upper[k] = upper[k + 1] + null[k]
            critical = next((k for k in range(n + 1) if upper[k] <= .05 / 4), n + 1)
            for multiplier in [1.5, 2.]:
                alternative = binomial_mass(n, p0 * multiplier)
                records.append({'threshold': goal, 'n_targets': n, 'uniform_rate': p0,
                    'alternative_multiplier': multiplier, 'alternative_rate': p0 * multiplier,
                    'family_alpha': .05 / 4, 'critical_event_count': critical,
                    'exact_false_positive_rate': upper[critical], 'exact_power': math.fsum(alternative[critical:]),
                    'expected_null_events': n * p0})
    for r in records:
        assert 0 <= r['exact_power'] <= 1.0000000001 and r['exact_false_positive_rate'] <= .05 / 4 + 1e-12
    csvfile(out / 'EXACT_TAIL_POWER.csv', records)
    verification = {'status': 'PASS', 'exact_binomial_cases': len(records), 'null_error_bound': 'PASS', 'future_predictions': 0}
    jsonfile(out / 'VERIFICATION.json', verification)
    lines = ['# ' + task['question'], '', '## NEW STUDY', '',
             'Exact binomial power for 3+/4+ at 1.5x and 2x uniform probabilities, alpha=.05/4. No Monte Carlo, SciPy or NumPy dependency. This is a new uncertainty/sample-size design question, not a repeat of the large uniform baseline.', '',
             '| Tail | n | Effect | Critical count | Power |', '|---|---:|---:|---:|---:|']
    for r in records: lines.append(f"|{r['threshold']}+|{r['n_targets']}|{r['alternative_multiplier']}x|{r['critical_event_count']}|{r['exact_power']:.3%}|")
    lines += ['', '## NEW FINDING', '', 'Finite high-tail samples can be substantially underpowered even at doubled event probability. Values above are exact under independent fair draws; they are not evidence any model achieves the hypothetical alternative.', '',
              '## MAINTENANCE/RECHECK', '', 'Exact hypergeometric reference, analytically specified hypothetical effects. This independent theory/design study needs no external data, historical cache, model implementation, NumPy, or large random simulation.', '',
              '## NEXT TEST', '', 'Choose a future confirmatory sample size before outcomes and retain multiplicity control; do not claim 200 targets suffice for 4+ superiority without power evidence.']
    with (out / 'REPORT.md').open('x', encoding='utf-8') as f: f.write('\n'.join(lines) + '\n')
    return {'executed_cases': len(records), 'verification': verification, 'positive_adjusted_comparisons': 0}

def run(root, output, task):
    root = Path(root).resolve(); out = Path(output).resolve()
    if out.exists(): raise FileExistsError('Refuse to overwrite study directory')
    protected = protect(root)
    out.mkdir(parents=True)
    expanded_source = Path(__file__).with_name('expanded_studies_v2.py')
    independent_source = Path(__file__).with_name('independent_signal_five_line_v1.py')
    source_hashes = {Path(__file__).name: digest(__file__)}
    if task['kind'] not in ['family', 'tail', 'power']:
        source_hashes[expanded_source.name] = digest(expanded_source)
    independent_kinds = {'independent_signal_discovery', 'independent_model_walkforward',
                         'five_line_candidate_bank', 'five_line_portfolio_selector',
                         'five_line_promotion_gate'}
    if task['kind'] in independent_kinds:
        source_hashes[independent_source.name] = digest(independent_source)
    frozen = {'task': task, 'study_spec': task.get('spec'), 'scope': 'POST_HOC_EXPLORATORY',
              'experiment_signature': experiment_signature(task),
              'data_sha256': digest(root / DATA) if task['kind'] != 'power' else None,
              'cache_sha256': digest(root / CACHE) if task['kind'] != 'power' else None,
              'code_sha256': digest(__file__), 'source_file_sha256': source_hashes,
              'expected_output_files': task.get('spec', {}).get('expected_output_files'),
              'expected_record_counts': task.get('spec', {}).get('expected_record_counts'),
              'created_utc': datetime.now(timezone.utc).isoformat(), 'first_target': 601, 'last_target': 1245,
              'weights': {'drop_hybrid': [1, 1, 0, 1, 1, 1, 1], 'family_balanced': [1, 1, 0, 1, 1, .5, .5]},
              'tail_exponents': [0., .5, 1., 2.], 'inner_targets': 200,
              'novelty': task['novelty'], 'prior_completed': 'B v1; large MC; H001/H002; relation tests; regime/dynamic v1'}
    jsonfile(out / 'FROZEN_SPEC.json', frozen)
    (out / 'ENGINE_SOURCE.py').write_bytes(Path(__file__).read_bytes())
    if task['kind'] not in ['family', 'tail', 'power']:
        (out / 'EXPANDED_ENGINE_SOURCE.py').write_bytes(expanded_source.read_bytes())
        if task['kind'] in independent_kinds:
            (out / 'INDEPENDENT_ENGINE_SOURCE.py').write_bytes(independent_source.read_bytes())
            from independent_signal_five_line_v1 import run_study
            result = run_study(root, out, task)
        else:
            from expanded_studies_v2 import run_study
            result = run_study(root, out, task)
    elif task['kind'] == 'power':
        result = power_study(root, out, task)
    else:
        result = predictor_study(root, out, task)
    check_protection(root, protected)
    if any(digest(Path(__file__).with_name(name)) != sha for name, sha in source_hashes.items()):
        raise ValueError('Research source changed during study')
    evidence = {'status': 'COMPLETE', 'classification': 'NEW_STUDY', 'task_id': task['id'],
                'question': task['question'], 'novelty': task['novelty'], 'executed_cases': result['executed_cases'],
                'validation': 'PASS', 'data_cutoff': None if task['kind'] == 'power' else 1245,
                'evidence': 'ANALYTIC_HYPOTHETICAL_EFFECTS' if task['kind'] == 'power' else 'POST_HOC_EXPLORATORY',
                'protected_existing_files': len(protected), 'protected_files_unchanged': True,
                'future_predictions': 0, 'result': result, 'report': 'REPORT.md',
                'completed_utc': datetime.now(timezone.utc).isoformat()}
    jsonfile(out / 'COMPLETION.json', evidence)
    csvfile(out / 'SHA256_MANIFEST.csv', [{'file': p.name, 'bytes': portable_size(p), 'sha256': digest(p)} for p in sorted(out.iterdir()) if p.is_file()])
    return evidence
