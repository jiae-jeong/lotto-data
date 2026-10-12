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
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import research_engine_v2 as engine

def validate_completion(output, task_id):
    output = Path(output)
    record = json.loads((output / 'COMPLETION.json').read_text())
    verification = json.loads((output / 'VERIFICATION.json').read_text())
    if record.get('task_id') != task_id or record.get('classification') != 'NEW_STUDY' or record.get('status') != 'COMPLETE':
        raise ValueError('Invalid completion identity/classification')
    if record.get('validation') != 'PASS' or record.get('executed_cases', 0) < 1 or verification.get('status') != 'PASS':
        raise ValueError('No executed, validated contribution')
    if not record.get('novelty') or not record.get('protected_files_unchanged') or record.get('future_predictions') != 0:
        raise ValueError('Novelty, preservation or no-recommendation gate failed')
    if record.get('report') != 'REPORT.md':
        raise ValueError('Unexpected report path')
    frozen = json.loads((output / 'FROZEN_SPEC.json').read_text())
    if frozen['task']['id'] != task_id or engine.digest(output / 'ENGINE_SOURCE.py') != frozen['code_sha256']:
        raise ValueError('Frozen study/code identity mismatch')
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
        raise ValueError('Unsupported research specification')
    report = (output / record['report']).read_text()
    if not all(label in report for label in ['MAINTENANCE/RECHECK', 'NEW STUDY', 'NEW FINDING', 'NEXT TEST']):
        raise ValueError('Required research report sections missing')
    manifest = engine.readcsv(output / 'SHA256_MANIFEST.csv')
    expected = {p.name for p in output.iterdir() if p.is_file()} - {'SHA256_MANIFEST.csv'}
    if {r['file'] for r in manifest} != expected or len(manifest) != len(expected):
        raise ValueError('Missing or unexpected evidence files')
    for r in manifest:
        path = output / r['file']
        if path.parent != output or path.is_symlink(): raise ValueError('Unsafe artifact path')
        if path.stat().st_size != int(r['bytes']) or engine.digest(path) != r['sha256']:
            raise ValueError('Evidence hash mismatch')
    return record

def completed_tasks(root, archive):
    completed = {}
    locations = [Path(root) / 'analysis']
    if archive: locations.append(Path(archive))
    for location in locations:
        if not location.exists(): continue
        for path in location.rglob('COMPLETION.json'):
            record = json.loads(path.read_text())
            if record.get('task_id', '').startswith(('E010_', 'E011_', 'E012_')):
                validate_completion(path.parent, record['task_id'])
                completed[record['task_id']] = str(path.parent)
    return completed

def run(root, output_root, queue, result_file, run_date=None, run_all=False, archive=None):
    root = Path(root).resolve(); output_root = Path(output_root).resolve()
    date = run_date or datetime.now(ZoneInfo('Asia/Seoul')).date().isoformat()
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', date): raise ValueError('Invalid local run date')
    datetime.strptime(date, '%Y-%m-%d')
    task_list = json.loads(Path(queue).read_text())['tasks']
    identifiers = [task['id'] for task in task_list]
    if len(set(identifiers)) != len(identifiers): raise ValueError('Duplicate research IDs')
    for task in task_list:
        if not re.fullmatch(r'[A-Za-z0-9_]+', task['id']) or task['kind'] not in ['family', 'tail', 'power'] or not task.get('question') or not task.get('novelty'):
            raise ValueError('Unregistered/unsafe research task')
    signatures = [engine.experiment_signature(task) for task in task_list]
    if len(set(signatures)) != len(signatures): raise ValueError('Same experiment registered under different names')
    done = completed_tasks(root, archive)
    completed_signatures = {}
    for task_id, location in done.items():
        frozen = json.loads((Path(location) / 'FROZEN_SPEC.json').read_text())
        signature = frozen.get('experiment_signature') or engine.experiment_signature(frozen['task'])
        completed_signatures[signature] = task_id
    equivalent = {task['id']: completed_signatures[engine.experiment_signature(task)] for task in task_list
                  if task['id'] not in done and engine.experiment_signature(task) in completed_signatures}
    pending = [task for task in task_list if task['id'] not in done and task['id'] not in equivalent]
    result = {'date': date, 'timezone': 'Asia/Seoul', 'already_completed': done,
              'completed_now': [], 'skipped_equivalent_questions': equivalent,
              'failed_attempts': [], 'status': 'NO_NEW_STUDY'}
    if result_file and Path(result_file).exists(): raise FileExistsError('Refuse to overwrite runner evidence')
    protected = engine.protect(root)
    for task in pending:
        # Every attempt is outside published output paths until independently validated.
        attempt = Path(tempfile.mkdtemp(prefix=task['id'] + '-', dir=output_root))
        output = attempt / 'study'
        try:
            engine.run(root, output, task)
            record = validate_completion(output, task['id'])
            destination = output_root / date / task['id']
            if destination.exists(): raise FileExistsError('Existing study path is protected')
            destination.parent.mkdir(parents=True, exist_ok=True)
            os.rename(output, destination)
            attempt.rmdir()
            result['completed_now'].append({'task_id': task['id'], 'path': str(destination), 'executed_cases': record['executed_cases']})
            result['status'] = 'COMPLETE'
            if not run_all: break
        except Exception as error:
            engine.check_protection(root, protected)
            attempt_record = {'task_id': task['id'], 'error_type': type(error).__name__, 'reason': str(error), 'preserved_attempt': str(attempt)}
            result['failed_attempts'].append(attempt_record)
            engine.jsonfile(attempt / 'FAILURE.json', attempt_record)
            # Advance to an independent registered question, including stdlib fallback.
    if result_file:
        engine.jsonfile(result_file, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['status'] == 'COMPLETE' else 3

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--repository', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output-root', type=Path)
    parser.add_argument('--queue', type=Path, default=Path(__file__).with_name('research_queue_v2.json'))
    parser.add_argument('--result-file', type=Path)
    parser.add_argument('--run-date')
    parser.add_argument('--run-all', action='store_true')
    parser.add_argument('--archive', type=Path)
    args = parser.parse_args()
    output_root = args.output_root or args.repository / 'analysis'
    output_root.mkdir(parents=True, exist_ok=True)
    raise SystemExit(run(args.repository, output_root, args.queue, args.result_file, args.run_date, args.run_all, args.archive))
