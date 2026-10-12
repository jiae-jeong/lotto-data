"""Synthetic faults for completion, novelty, fallback and causality contracts."""
import contextlib
import io
import json
import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import daily_research_v2 as daily
import research_engine_v2 as engine

def fixture(output, task):
    output.mkdir(parents=True)
    (output / 'ENGINE_SOURCE.py').write_text('# Synthetic unit-test fixture; no scientific result\n')
    engine.jsonfile(output / 'FROZEN_SPEC.json', {'task': task, 'code_sha256': engine.digest(output / 'ENGINE_SOURCE.py')})
    engine.csvfile(output / 'EXACT_TAIL_POWER.csv', [{'synthetic_case': i} for i in range(24)])
    engine.jsonfile(output / 'VERIFICATION.json', {'status': 'PASS', 'exact_binomial_cases': 24})
    record = {'task_id': task['id'], 'status': 'COMPLETE', 'classification': 'NEW_STUDY',
              'validation': 'PASS', 'executed_cases': 24, 'novelty': 'SYNTHETIC UNIT-TEST ONLY',
              'protected_files_unchanged': True, 'future_predictions': 0, 'report': 'REPORT.md'}
    engine.jsonfile(output / 'COMPLETION.json', record)
    (output / 'REPORT.md').write_text('MAINTENANCE/RECHECK\nNEW STUDY\nNEW FINDING\nNEXT TEST\nSynthetic unit-test fixture only.\n')
    engine.csvfile(output / 'SHA256_MANIFEST.csv', [{'file': p.name, 'bytes': p.stat().st_size, 'sha256': engine.digest(p)} for p in sorted(output.iterdir())])
    return record

class ResearchGuards(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / 'repo'; self.root.mkdir()
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        self.output = self.root / 'analysis'; self.output.mkdir()
        self.task = {'id': 'E012_SYNTHETIC_TEST', 'kind': 'power', 'question': 'Synthetic guard test', 'novelty': 'Test only'}

    def tearDown(self): self.temp.cleanup()

    def test_zero_case_cannot_be_complete(self):
        path = self.output / 'fixture'; fixture(path, self.task)
        record = json.loads((path / 'COMPLETION.json').read_text()); record['executed_cases'] = 0
        (path / 'COMPLETION.json').write_text(json.dumps(record))
        with self.assertRaises(ValueError): daily.validate_completion(path, self.task['id'])

    def test_changed_artifact_fails_hash_gate(self):
        path = self.output / 'fixture'; fixture(path, self.task)
        (path / 'REPORT.md').write_text((path / 'REPORT.md').read_text() + 'tampered')
        with self.assertRaises(ValueError): daily.validate_completion(path, self.task['id'])

    def test_frozen_source_drift_fails(self):
        path = self.output / 'fixture'; fixture(path, self.task)
        (path / 'ENGINE_SOURCE.py').write_text('changed')
        with self.assertRaises(ValueError): daily.validate_completion(path, self.task['id'])

    def test_missing_report_section_fails(self):
        path = self.output / 'fixture'; fixture(path, self.task)
        (path / 'REPORT.md').write_text('Only maintenance; no new contribution')
        with self.assertRaises(ValueError): daily.validate_completion(path, self.task['id'])

    def test_failure_advances_to_independent_task(self):
        first = {**self.task, 'id': 'E010_TEST_FAILURE', 'kind': 'family'}
        second = {**self.task, 'id': 'E012_TEST_FALLBACK'}
        queue = self.root / 'queue.json'; engine.jsonfile(queue, {'tasks': [first, second]})
        def execute(root, output, task):
            if task['id'] == first['id']: raise ImportError('Synthetic unavailable executable dependency')
            return fixture(Path(output), task)
        result_file = self.root / 'result.json'
        with patch.object(engine, 'run', side_effect=execute), contextlib.redirect_stdout(io.StringIO()):
            code = daily.run(self.root, self.output, queue, result_file, '2026-10-12')
        result = json.loads(result_file.read_text())
        self.assertEqual(code, 0)
        self.assertEqual(result['completed_now'][0]['task_id'], second['id'])
        self.assertEqual(len(result['failed_attempts']), 1)
        self.assertTrue((Path(result['failed_attempts'][0]['preserved_attempt']) / 'FAILURE.json').exists())

    def test_completed_question_is_not_run_again(self):
        fixture(self.output / '2026-10-12' / self.task['id'], self.task)
        queue = self.root / 'queue.json'; engine.jsonfile(queue, {'tasks': [self.task]})
        with patch.object(engine, 'run') as execute, contextlib.redirect_stdout(io.StringIO()):
            code = daily.run(self.root, self.output, queue, None, '2026-10-13')
        execute.assert_not_called(); self.assertEqual(code, 3)

    def test_path_traversal_is_rejected(self):
        queue = self.root / 'queue.json'; engine.jsonfile(queue, {'tasks': [{**self.task, 'id': '../escape'}]})
        with self.assertRaises(ValueError): daily.run(self.root, self.output, queue, None, '2026-10-12')

    def test_duplicate_questions_are_rejected(self):
        queue = self.root / 'queue.json'; engine.jsonfile(queue, {'tasks': [self.task, self.task]})
        with self.assertRaises(ValueError): daily.run(self.root, self.output, queue, None, '2026-10-12')

    def test_same_experiment_with_different_id_is_rejected(self):
        queue = self.root / 'queue.json'
        engine.jsonfile(queue, {'tasks': [self.task, {**self.task, 'id': 'E012_RENAMED'}]})
        with self.assertRaises(ValueError): daily.run(self.root, self.output, queue, None, '2026-10-12')

    def test_renamed_completed_experiment_is_skipped(self):
        fixture(self.output / '2026-10-12' / self.task['id'], self.task)
        queue = self.root / 'queue.json'
        engine.jsonfile(queue, {'tasks': [{**self.task, 'id': 'E012_RENAMED', 'question': 'Cosmetic title change'}]})
        with patch.object(engine, 'run') as execute, contextlib.redirect_stdout(io.StringIO()):
            code = daily.run(self.root, self.output, queue, None, '2026-10-13')
        execute.assert_not_called(); self.assertEqual(code, 3)

    def test_tail_selection_uses_only_prior_200(self):
        history = [[0, 3, 0, 0] for _ in range(200)]
        self.assertEqual(engine.tail_choice(history, 3), 1)
        self.assertEqual(engine.tail_choice(history, 4), 1)
        with self.assertRaises(ValueError): engine.tail_choice(history + [[6] * 4], 3)
        current_and_future = [[6, 0, 6, 6] for _ in range(100)]
        self.assertEqual(engine.tail_choice((history + current_and_future)[:200], 3), 1)

    def test_overlap_weight_never_assumes_independent_duplicates(self):
        tickets = [(1, 2, 3, 4, 5, 6)] * 7
        weights = engine.overlap_weights(tickets, 1)
        self.assertTrue(all(math.isclose(w, 1 / 7) for w in weights))
        self.assertEqual(engine.ticket_vote(tickets, weights), (1, 2, 3, 4, 5, 6))

    def test_exact_binomial_normalization_and_moments(self):
        values = engine.binomial_mass(5, .2)
        self.assertAlmostEqual(sum(values), 1)
        self.assertAlmostEqual(sum(i * p for i, p in enumerate(values)), 1)
        self.assertAlmostEqual(sum((i - 1)**2 * p for i, p in enumerate(values)), .8)

    def test_existing_result_is_protected(self):
        queue = self.root / 'queue.json'; engine.jsonfile(queue, {'tasks': [self.task]})
        result = self.root / 'result.json'; result.write_text('existing')
        with self.assertRaises(FileExistsError): daily.run(self.root, self.output, queue, result, '2026-10-12')
        self.assertEqual(result.read_text(), 'existing')

if __name__ == '__main__': unittest.main()
