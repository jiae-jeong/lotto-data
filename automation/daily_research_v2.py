#!/usr/bin/env python3
"""Consume an unfinished registered question; validate evidence before completion."""
from __future__ import annotations
import argparse
import csv
import json
import os
import re
import subprocess
import sys
import tempfile
import traceback
import itertools
import statistics
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import research_engine_v2 as engine

def validate_completion(output, task_id):
    output = Path(output)
    record = json.loads((output / 'COMPLETION.json').read_text(encoding='utf-8'))
    verification = json.loads((output / 'VERIFICATION.json').read_text(encoding='utf-8'))
    if record.get('task_id') != task_id or record.get('classification') != 'NEW_STUDY' or record.get('status') != 'COMPLETE':
        raise ValueError('Invalid completion identity/classification')
    if record.get('validation') != 'PASS' or record.get('executed_cases', 0) < 1 or verification.get('status') != 'PASS':
        raise ValueError('No executed, validated contribution')
    if not record.get('novelty') or not record.get('protected_files_unchanged') or record.get('future_predictions') != 0:
        raise ValueError('Novelty, preservation or no-recommendation gate failed')
    if record.get('report') != 'REPORT.md':
        raise ValueError('Unexpected report path')
    frozen = json.loads((output / 'FROZEN_SPEC.json').read_text(encoding='utf-8'))
    if frozen['task']['id'] != task_id or engine.digest(output / 'ENGINE_SOURCE.py') != frozen['code_sha256']:
        raise ValueError('Frozen study/code identity mismatch')
    spec = frozen.get('study_spec') or frozen.get('task', {}).get('spec')
    if spec:
        required_spec = ['study_id','kind','research_question','data_cutoff','target_rounds','training_cutoff_rule',
                         'primary_metric','secondary_metrics','comparator','baseline','multiplicity_correction',
                         'block_stability','tie_break','expected_output_files','expected_record_counts','novelty_signature']
        missing = [key for key in required_spec if key not in spec]
        if missing: raise ValueError('Frozen task spec missing: ' + ', '.join(missing))
        if spec['study_id'] != task_id or spec['kind'] != frozen['task']['kind']:
            raise ValueError('Frozen task spec identity mismatch')
        for name in spec['expected_output_files']:
            path = output / name
            if path.parent != output or not path.is_file() or path.is_symlink():
                raise ValueError('Expected study output missing or unsafe: ' + name)
        for name, expected in spec['expected_record_counts'].items():
            rows = engine.readcsv(output / name)
            if len(rows) != int(expected):
                raise ValueError(f'Frozen record count mismatch for {name}: {len(rows)} != {expected}')
        source_hashes = frozen.get('source_file_sha256', {})
        for source_name, source_sha in source_hashes.items():
            source_copy = output / ('ENGINE_SOURCE.py' if source_name == 'research_engine_v2.py' else 'EXPANDED_ENGINE_SOURCE.py')
            if not source_copy.is_file() or engine.digest(source_copy) != source_sha:
                raise ValueError('Frozen study source hash mismatch: ' + source_name)
    else:
        # Backward-compatible replay of E010-E012 outputs registered before task-spec contracts.
        kind = frozen['task']['kind']
        if kind == 'power':
            cases = engine.readcsv(output / 'EXACT_TAIL_POWER.csv')
            if len(cases) != 24 or record['executed_cases'] != 24 or verification.get('exact_binomial_cases') != 24:
                raise ValueError('Power study did not execute its registered cases')
        elif kind in ['family', 'tail']:
            expected_cases = (3 if kind == 'family' else 2) * 645
            predictions = engine.readcsv(output / 'PREDICTIONS.csv')
            expected_records = (12 if kind == 'family' else 11) * 645
            if record['executed_cases'] != expected_cases or len(predictions) != expected_records or verification.get('prediction_records_checked') != expected_records:
                raise ValueError('Forecast study did not execute its registered targets')
            if any(int(r['training_through_round']) >= int(r['target_round']) for r in predictions):
                raise ValueError('Future information in recorded forecasts')
        else:
            raise ValueError('Unsupported legacy research specification')
    report = (output / record['report']).read_text(encoding='utf-8')
    if not all(label in report for label in ['MAINTENANCE/RECHECK', 'NEW STUDY', 'NEW FINDING', 'NEXT TEST']):
        raise ValueError('Required research report sections missing')
    manifest = engine.readcsv(output / 'SHA256_MANIFEST.csv')
    expected = {p.name for p in output.iterdir() if p.is_file()} - {'SHA256_MANIFEST.csv'}
    if {r['file'] for r in manifest} != expected or len(manifest) != len(expected):
        raise ValueError('Missing or unexpected evidence files')
    for r in manifest:
        path = output / r['file']
        if path.parent != output or path.is_symlink(): raise ValueError('Unsafe artifact path')
        valid_raw = engine.raw_size(path) == int(r['bytes']) and engine.raw_digest(path) == r['sha256']
        valid_portable = engine.portable_size(path) == int(r['bytes']) and engine.digest(path) == r['sha256']
        if not (valid_raw or valid_portable):
            raise ValueError('Evidence hash mismatch')
    return record

def completed_tasks(root, archive):
    completed = {}
    locations = [Path(root) / 'analysis']
    if archive: locations.append(Path(archive))
    for location in locations:
        if not location.exists(): continue
        for path in location.rglob('COMPLETION.json'):
            record = json.loads(path.read_text(encoding='utf-8'))
            if re.fullmatch(r'E\d{3}_[A-Za-z0-9_]+', record.get('task_id', '')):
                validate_completion(path.parent, record['task_id'])
                completed[record['task_id']] = str(path.parent)
    return completed

def publication_paths(root, result):
    """Return only this run's validated studies, report, and preserved attempts."""
    root = Path(root).resolve()
    analysis = (root / 'analysis').resolve()
    paths = []
    study_paths = [item['path'] for item in result.get('completed_now', [])]
    prior = result.get('already_completed', {})
    study_paths.extend(prior[task_id] for task_id in result.get('completed_today_before_run', []) if task_id in prior)
    for item_path in study_paths:
        path = Path(item_path).resolve()
        if not path.is_relative_to(analysis) or not (path / 'COMPLETION.json').is_file():
            raise ValueError('Unsafe or incomplete study publication path')
        paths.append(str(path.relative_to(root)))
    report = Path(result['daily_master_report']).resolve()
    if not report.is_relative_to(analysis) or not report.is_file():
        raise ValueError('Unsafe or missing daily master report')
    paths.append(str(report.relative_to(root)))
    for daily_report in report.parent.glob('DAILY_MASTER_REPORT_*.md'):
        paths.append(str(daily_report.resolve().relative_to(root)))
    attempts_root = report.parent / '.attempts'
    if attempts_root.exists():
        for attempt_dir in attempts_root.iterdir():
            if attempt_dir.is_dir() and (attempt_dir / 'FAILURE.json').is_file():
                path = attempt_dir.resolve()
                if not path.is_relative_to(analysis):
                    raise ValueError('Unsafe preserved attempt directory')
                paths.append(str(path.relative_to(root)))
    for attempt in result.get('preserved_attempts', []):
        path = Path(attempt).resolve()
        if not path.is_relative_to(analysis):
            raise ValueError('Unsafe attempt path')
        if path.exists():
            paths.append(str(path.relative_to(root)))
    return sorted(set(paths))

def _validate_task(task):
    safe_id = re.fullmatch(r'E\d{3}_[A-Za-z0-9_]+', task.get('id', ''))
    if not safe_id or not task.get('question') or not task.get('novelty'):
        raise ValueError('Unregistered/unsafe research task')
    legacy = task.get('kind') in ['family', 'tail', 'power'] and not task.get('spec')
    if legacy: return
    spec = task.get('spec')
    required = ['study_id','kind','research_question','data_cutoff','target_rounds','training_cutoff_rule','primary_metric',
                'secondary_metrics','comparator','baseline','multiplicity_correction','block_stability','tie_break',
                'expected_output_files','expected_record_counts','novelty_signature','study_class']
    if not isinstance(spec, dict) or any(k not in spec for k in required):
        raise ValueError(f"Task {task['id']} lacks complete frozen task specification")
    if spec['study_id'] != task['id'] or spec['kind'] != task['kind'] or spec['research_question'] != task['question']:
        raise ValueError(f"Task {task['id']} does not match frozen specification")
    if spec['study_class'] not in ['empirical','theory','blocked']:
        raise ValueError(f"Task {task['id']} has invalid study_class")
    engine.experiment_signature(task)


def _daily_master_report(root, date, result):
    data = Path(root) / 'lotto_data.csv'
    rows = engine.readcsv(data)
    rounds = [int(r['round']) for r in rows]
    integrity = rounds == list(range(1, len(rounds)+1)) and len(set(rounds)) == len(rounds)
    counts = {n:0 for n in range(1,46)}; gaps={n:[] for n in range(1,46)}; last={n:0 for n in range(1,46)}
    draws=[]
    for row in rows:
        nums=tuple(int(row[f'no{i}']) for i in range(1,7)); bonus=int(row['bonus']); r=int(row['round'])
        if len(set(nums))!=6 or any(n<1 or n>45 for n in nums) or bonus<1 or bonus>45 or bonus in nums:
            raise ValueError(f"Daily MASTER integrity failure at round {r}")
        for n in nums:
            counts[n]+=1
            if last[n]: gaps[n].append(r-last[n])
            last[n]=r
        draws.append((r, nums))
    pair=Counter(); triple=Counter(); odd=Counter(); low=Counter(); sums=[]; consecutive=Counter(); bands=Counter()
    for _,nums in draws:
        pair.update(itertools.combinations(nums,2)); triple.update(itertools.combinations(nums,3))
        odd[sum(n%2 for n in nums)]+=1; low[sum(n<=22 for n in nums)]+=1; sums.append(sum(nums))
        consecutive[sum(b==a+1 for a,b in zip(sorted(nums),sorted(nums)[1:]))]+=1
        bands.update(("1-10" if n<=10 else "11-20" if n<=20 else "21-30" if n<=30 else "31-40" if n<=40 else "41-45") for n in nums)
    latest=rows[-1]; latest_round=int(latest['round']); latest_date=latest['date']
    winfreq=[]
    for w in (10,30,50,100):
        sub=draws[-min(w,len(draws)):]; cf=Counter(n for _,nums in sub for n in nums)
        winfreq.append((w,cf))
    rec_roots=['research/prospective_v4/decisions','analysis']
    purchase_files=[p.relative_to(root).as_posix() for directory in rec_roots for p in (Path(root)/directory).rglob('*PURCHASE*LINES*.csv')]
    if not purchase_files:
        recommendation_status='SOURCE NOT RECOVERED in historical recommendation/analysis paths; no recommendation inferred from backtest predictions.'
    else:
        recommendation_status='Candidate sealed/purchase artifacts found: '+', '.join(purchase_files)+'; these are not assumed to be actual purchased tickets without provenance.'
    lines=[f'# Daily MASTER validation — {date}','',
      '1. Data basis / integrity','',f'- Recomputed from `lotto_data.csv`: {len(rows)} rows, rounds 1..{latest_round}; continuity/uniqueness={integrity}; latest stored date={latest_date}.','',
      '2. Newly calculated findings','',f'- Integrity hash: {engine.digest(data)}. Pair/triple relations recalculated: {len(pair)} distinct pairs, {len(triple)} distinct triples.','',
      '3. Cumulative number analysis','',json.dumps(counts,ensure_ascii=False),'',
      '4. Long vs recent 10/30/50/100','', '| Window | Top counts (number=count) |','|---:|---|']
    for w,cf in winfreq: lines.append(f"|{w}|"+'; '.join(f'{n}={cf[n]}' for n in sorted(cf,key=lambda x:(-cf[x],x))[:10])+'|')
    lines += ['', '5. Gap / nonappearance','',json.dumps({str(n):{'current':latest_round-last[n],'mean_completed_gap':statistics.mean(gaps[n]) if gaps[n] else None} for n in range(1,46)},ensure_ascii=False),'',
      '6. Structure / relation','',json.dumps({'odd_count':dict(odd),'low_count':dict(low),'sum_mean':statistics.mean(sums),'consecutive_pair_count':dict(consecutive),'band_number_counts':dict(bands),'top_pairs':pair.most_common(20),'top_triples':triple.most_common(20)},ensure_ascii=False),'',
      '7. A model','', 'Legacy integrated A source: SOURCE NOT RECOVERED; signal inventory above is descriptive recalculation only.','',
      '8. B + random','', 'B full walk-forward: NOT RUN TODAY by the master validation path. E013/E014 studies reuse the frozen OOS cache and do not count as a B reproduction. Random simulation status is recorded in the new-study outputs, not inferred from prior results.','',
      '9. C model','', 'Legacy integrated C source: SOURCE NOT RECOVERED.','',
      '10. Contrarian','', 'Legacy integrated contrarian source: SOURCE NOT RECOVERED; no substitute model is represented as legacy.','',
      '11. Historical recommendation / mistake notes','', recommendation_status,'',
      '12. Prior hypothesis revalidation','', 'Prior E010–E012 studies are not recounted as new studies. New queue study results and explicit statuses are in the run result/individual research outputs.','',
      '13. Limits / not computed','', 'Exact legacy A/C/contrarian models, fully sourced purchase history, and a fresh full B rerun are not claimed unless corresponding execution evidence exists.','',
      f"- RESEARCH_QUOTA_STATUS: {result['research_quota_status']} ({result.get('successful_studies_today',len(result['completed_now']))} successful studies, {result.get('empirical_studies_today',result['empirical_successes'])} empirical).",'',
      f"- MASTER_STATUS: {result['master_status']}; this quota runner does not execute the full MASTER checklist.",'']
    return '\n'.join(lines)


def run(root, output_root, queue, result_file, run_date=None, min_successful_studies=2,
        max_successful_studies=3, required_empirical_studies=1, archive=None):
    root = Path(root).resolve(); output_root = Path(output_root).resolve()
    date = run_date or datetime.now(ZoneInfo('Asia/Seoul')).date().isoformat()
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', date): raise ValueError('Invalid local run date')
    datetime.strptime(date, '%Y-%m-%d')
    if min_successful_studies < 1 or max_successful_studies < min_successful_studies:
        raise ValueError('Invalid successful-study bounds')
    if required_empirical_studies < 1 or required_empirical_studies > min_successful_studies:
        raise ValueError('Empirical study requirement must be between 1 and the minimum')
    task_list = json.loads(Path(queue).read_text(encoding='utf-8'))['tasks']
    identifiers = [task['id'] for task in task_list]
    if len(set(identifiers)) != len(identifiers): raise ValueError('Duplicate research IDs')
    for task in task_list:
        _validate_task(task)
    signatures = [engine.experiment_signature(task) for task in task_list]
    if len(set(signatures)) != len(signatures): raise ValueError('Same experiment registered under different names')
    done = completed_tasks(root, archive)
    date_root = output_root / date
    today_done = {}
    today_empirical = 0
    for task_id, location in done.items():
        if Path(location).resolve().parent != date_root.resolve():
            continue
        frozen_today = json.loads((Path(location) / 'FROZEN_SPEC.json').read_text(encoding='utf-8'))
        study_class = (frozen_today.get('study_spec') or {}).get('study_class')
        # Legacy E010-E012 outputs predate the daily gate and are never counted as today's new work.
        if study_class not in ['empirical','theory']:
            continue
        today_done[task_id] = location
        if study_class == 'empirical':
            today_empirical += 1
    completed_signatures = {}
    for task_id, location in done.items():
        frozen = json.loads((Path(location) / 'FROZEN_SPEC.json').read_text(encoding='utf-8'))
        signature = frozen.get('experiment_signature') or engine.experiment_signature(frozen['task'])
        completed_signatures[signature] = task_id
    equivalent = {task['id']: completed_signatures[engine.experiment_signature(task)] for task in task_list
                  if task['id'] not in done and engine.experiment_signature(task) in completed_signatures}
    pending = [task for task in task_list if task['id'] not in done and task['id'] not in equivalent]
    result = {'date': date, 'timezone': 'Asia/Seoul', 'already_completed': done,
              'completed_today_before_run': sorted(today_done),
              'completed_now': [], 'empirical_successes': 0, 'skipped_equivalent_questions': equivalent,
              'failed_attempts': [], 'blocked_tasks': [], 'status': 'NO_NEW_STUDY',
              'minimum_successful_studies': min_successful_studies,'maximum_successful_studies':max_successful_studies,
              'required_empirical_studies':required_empirical_studies}
    if result_file and Path(result_file).exists(): raise FileExistsError('Refuse to overwrite runner evidence')
    protected = engine.protect(root)
    date_root.mkdir(parents=True, exist_ok=True)
    attempts_root = date_root / '.attempts'; attempts_root.mkdir(parents=True, exist_ok=True)
    for task in pending:
        if len(today_done) + len(result['completed_now']) >= max_successful_studies: break
        if task.get('spec', {}).get('study_class') == 'blocked':
            result['blocked_tasks'].append({'task_id':task['id'],'status':task['spec'].get('blocked_status','BLOCKED_SOURCE_MISSING'),
                                           'reason':task['spec'].get('blocked_reason','Source prerequisite not recovered')})
            continue
        # Every attempt is outside published output paths until independently validated.
        attempt = Path(tempfile.mkdtemp(prefix=task['id'] + '-', dir=attempts_root))
        output = attempt / 'study'
        stage = 'engine_execution'
        try:
            engine.run(root, output, task)
            stage = 'completion_validation'
            record = validate_completion(output, task['id'])
            destination = date_root / task['id']
            if destination.exists(): raise FileExistsError('Existing study path is protected')
            stage = 'publication_promotion'
            os.rename(output, destination)
            attempt.rmdir()
            is_empirical = task.get('spec', {}).get('study_class') == 'empirical'
            result['completed_now'].append({'task_id': task['id'], 'path': str(destination), 'executed_cases': record['executed_cases'],
                                            'study_class':'empirical' if is_empirical else 'theory'})
            if is_empirical: result['empirical_successes'] += 1
        except Exception as error:
            failed_stage=stage
            stage='protection_check'
            engine.check_protection(root, protected)
            stage='failure_record'
            attempt_record = {'task_id': task['id'], 'error_type': type(error).__name__, 'reason': str(error),
                'traceback':traceback.format_exc(), 'data_cutoff':task.get('spec',{}).get('data_cutoff'),
                'failing_stage':failed_stage,'protected_files_unchanged':True,'recovery_attempted':'Advanced to next independent registered task',
                'retryable':True,'user_action_required':False,'preserved_attempt':str(attempt)}
            result['failed_attempts'].append(attempt_record)
            engine.jsonfile(attempt / 'FAILURE.json', attempt_record)
            # Advance to an independent registered question, including stdlib fallback.
    successful_today = len(today_done) + len(result['completed_now'])
    empirical_today = today_empirical + result['empirical_successes']
    result['successful_studies_today'] = successful_today
    result['empirical_studies_today'] = empirical_today
    if successful_today >= min_successful_studies and empirical_today >= required_empirical_studies:
        result['research_quota_status'] = 'RESEARCH_QUOTA_COMPLETE'
        result['master_status'] = 'NOT_ASSESSED_BY_QUOTA_RUNNER'
        result['status'] = result['research_quota_status']
    elif not pending or successful_today < min_successful_studies:
        result['research_quota_status'] = 'INSUFFICIENT_RESEARCH_QUEUE'
        result['master_status'] = 'NOT_ASSESSED_BY_QUOTA_RUNNER'
        result['status'] = result['research_quota_status']
    else:
        result['research_quota_status'] = 'RESEARCH_QUOTA_PARTIAL'
        result['master_status'] = 'NOT_ASSESSED_BY_QUOTA_RUNNER'
        result['status'] = result['research_quota_status']
    report_name = f"DAILY_MASTER_REPORT_{datetime.now().strftime('%H%M%S_%f')}.md"
    report_path = date_root / report_name
    with report_path.open('x', encoding='utf-8') as stream:
        stream.write(_daily_master_report(root, date, result))
    result['daily_master_report'] = str(report_path)
    result['preserved_attempts'] = [r['preserved_attempt'] for r in result['failed_attempts']]
    if result_file:
        engine.jsonfile(result_file, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['research_quota_status'] == 'RESEARCH_QUOTA_COMPLETE' else 3

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--repository', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output-root', type=Path)
    parser.add_argument('--queue', type=Path, default=Path(__file__).with_name('research_queue_v2.json'))
    parser.add_argument('--result-file', type=Path)
    parser.add_argument('--run-date')
    parser.add_argument('--min-successful-studies', type=int, default=2)
    parser.add_argument('--max-successful-studies', type=int, default=3)
    parser.add_argument('--required-empirical-studies', type=int, default=1)
    parser.add_argument('--archive', type=Path)
    args = parser.parse_args()
    output_root = args.output_root or args.repository / 'analysis'
    output_root.mkdir(parents=True, exist_ok=True)
    raise SystemExit(run(args.repository, output_root, args.queue, args.result_file, args.run_date,
        args.min_successful_studies,args.max_successful_studies,args.required_empirical_studies,args.archive))
