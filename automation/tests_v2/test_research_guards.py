"""Synthetic faults for completion, novelty, fallback and causality contracts."""
import contextlib
import io
import json
import math
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import daily_research_v2 as daily
import research_engine_v2 as engine
import check_environment_v2 as environment

def fixture(output, task):
    output.mkdir(parents=True)
    (output / 'ENGINE_SOURCE.py').write_text('# Synthetic unit-test fixture; no scientific result\n')
    engine.jsonfile(output / 'FROZEN_SPEC.json', {'task': task, 'study_spec': task.get('spec'),
        'code_sha256': engine.digest(output / 'ENGINE_SOURCE.py'),
        'source_file_sha256': {'research_engine_v2.py': engine.digest(output / 'ENGINE_SOURCE.py')} if task.get('spec') else {}})
    engine.csvfile(output / 'EXACT_TAIL_POWER.csv', [{'synthetic_case': i} for i in range(24)])
    engine.jsonfile(output / 'VERIFICATION.json', {'status': 'PASS', 'exact_binomial_cases': 24})
    record = {'task_id': task['id'], 'status': 'COMPLETE', 'classification': 'NEW_STUDY',
              'validation': 'PASS', 'executed_cases': 24, 'novelty': 'SYNTHETIC UNIT-TEST ONLY',
              'protected_files_unchanged': True, 'future_predictions': 0, 'report': 'REPORT.md'}
    engine.jsonfile(output / 'COMPLETION.json', record)
    (output / 'REPORT.md').write_text('MAINTENANCE/RECHECK\nNEW STUDY\nNEW FINDING\nNEXT TEST\nSynthetic unit-test fixture only.\n')
    engine.csvfile(output / 'SHA256_MANIFEST.csv', [{'file': p.name, 'bytes': engine.portable_size(p), 'sha256': engine.digest(p)} for p in sorted(output.iterdir())])
    return record

class ResearchGuards(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent)
        self.root = Path(self.temp.name) / 'repo'; self.root.mkdir()
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        engine.csvfile(self.root/'lotto_data.csv',[{'round':1,'date':'2002-12-07','no1':1,'no2':2,'no3':3,'no4':4,'no5':5,'no6':6,'bonus':7}])
        self.output = self.root / 'analysis'; self.output.mkdir()
        self.task = {'id': 'E012_SYNTHETIC_TEST', 'kind': 'power', 'question': 'Synthetic guard test', 'novelty': 'Test only'}

    def tearDown(self): self.temp.cleanup()

    def registered_task(self, task_id, study_class='empirical', novelty='test-setting'):
        return {'id':task_id,'kind':'synthetic','question':'Synthetic study','novelty':'Synthetic only',
            'spec':{'study_id':task_id,'kind':'synthetic','research_question':'Synthetic study','data_cutoff':1245,
                'target_rounds':[601,1245],'training_cutoff_rule':'target_round - 1',
                'primary_metric':'mean_hits','secondary_metrics':['rate_ge_2'],'comparator':'synthetic control',
                'baseline':'fixed fixture','multiplicity_correction':'none for fixture','block_stability':'not applicable',
                'tie_break':'lower number','random_seed':7,'expected_output_files':['EXACT_TAIL_POWER.csv'],
                'expected_record_counts':{'EXACT_TAIL_POWER.csv':24},'novelty_signature':novelty,'study_class':study_class}}

    def test_zero_case_cannot_be_complete(self):
        path = self.output / 'fixture'; fixture(path, self.task)
        record = json.loads((path / 'COMPLETION.json').read_text()); record['executed_cases'] = 0
        (path / 'COMPLETION.json').write_text(json.dumps(record))
        with self.assertRaises(ValueError): daily.validate_completion(path, self.task['id'])

    def test_future_prediction_cannot_be_complete(self):
        path=self.output/'fixture'; fixture(path,self.task)
        record=json.loads((path/'COMPLETION.json').read_text()); record['future_predictions']=1
        (path/'COMPLETION.json').write_text(json.dumps(record))
        with self.assertRaises(ValueError): daily.validate_completion(path,self.task['id'])

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
        third = self.registered_task('E013_SECOND_FALLBACK', novelty='third')
        queue = self.root / 'queue.json'; engine.jsonfile(queue, {'tasks': [first, second, third]})
        def execute(root, output, task):
            if task['id'] == first['id']: raise ImportError('Synthetic unavailable executable dependency')
            return fixture(Path(output), task)
        result_file = self.root / 'result.json'
        with patch.object(engine, 'run', side_effect=execute), contextlib.redirect_stdout(io.StringIO()):
            code = daily.run(self.root, self.output, queue, result_file, '2026-10-12')
        result = json.loads(result_file.read_text())
        self.assertEqual(code, 0)
        self.assertEqual(result['completed_now'][0]['task_id'], second['id'])
        self.assertEqual(len(result['completed_now']),2)
        self.assertEqual(len(result['failed_attempts']), 1)
        self.assertTrue((Path(result['failed_attempts'][0]['preserved_attempt']) / 'FAILURE.json').exists())

    def test_one_success_is_not_full_complete(self):
        task=self.registered_task('E013_ONE_SUCCESS')
        queue=self.root/'queue.json'; engine.jsonfile(queue,{'tasks':[task]})
        with patch.object(engine,'run',side_effect=lambda root,out,task:fixture(Path(out),task)), contextlib.redirect_stdout(io.StringIO()):
            code=daily.run(self.root,self.output,queue,None,'2026-10-12',min_successful_studies=2,max_successful_studies=3)
        self.assertEqual(code,3)
        self.assertEqual(len(list((self.output/'2026-10-12').glob('E013_ONE_SUCCESS/COMPLETION.json'))),1)

    def test_two_successes_reach_full_complete(self):
        tasks=[self.registered_task('E013_FIRST',novelty='first'),self.registered_task('E014_SECOND',novelty='second')]
        queue=self.root/'queue.json'; engine.jsonfile(queue,{'tasks':tasks}); result_file=self.root/'result.json'
        with patch.object(engine,'run',side_effect=lambda root,out,task:fixture(Path(out),task)), contextlib.redirect_stdout(io.StringIO()):
            code=daily.run(self.root,self.output,queue,result_file,'2026-10-12')
        result=json.loads(result_file.read_text())
        self.assertEqual(code,0); self.assertEqual(result['status'],'FULL_COMPLETE')
        self.assertEqual(len(result['completed_now']),2)

    def test_theory_only_does_not_satisfy_empirical_gate(self):
        tasks=[self.registered_task('E013_THEORY1','theory','theory1'),self.registered_task('E014_THEORY2','theory','theory2')]
        queue=self.root/'queue.json'; engine.jsonfile(queue,{'tasks':tasks}); result_file=self.root/'result.json'
        with patch.object(engine,'run',side_effect=lambda root,out,task:fixture(Path(out),task)), contextlib.redirect_stdout(io.StringIO()):
            code=daily.run(self.root,self.output,queue,result_file,'2026-10-12')
        result=json.loads(result_file.read_text())
        self.assertEqual(code,3); self.assertEqual(result['status'],'PARTIAL')

    def test_daily_cap_counts_validated_same_day_studies(self):
        existing=self.registered_task('E013_TODAY_EXISTING',novelty='existing')
        fixture(self.output/'2026-10-12'/existing['id'],existing)
        next_task=self.registered_task('E014_TODAY_NEW',novelty='next')
        third=self.registered_task('E015_OVER_CAP',novelty='third')
        queue=self.root/'queue.json'; engine.jsonfile(queue,{'tasks':[existing,next_task,third]}); result_file=self.root/'result.json'
        executed=[]
        def execute(root,out,task):
            executed.append(task['id']); return fixture(Path(out),task)
        with patch.object(engine,'run',side_effect=execute),contextlib.redirect_stdout(io.StringIO()):
            code=daily.run(self.root,self.output,queue,result_file,'2026-10-12',min_successful_studies=2,max_successful_studies=2)
        result=json.loads(result_file.read_text())
        self.assertEqual(code,0); self.assertEqual(executed,[next_task['id']])
        self.assertEqual(result['successful_studies_today'],2)

    def test_new_study_signature_ignores_cosmetic_id_and_random_seed(self):
        first=self.registered_task('E013_STUDY',novelty='same-core')
        renamed=self.registered_task('E014_RENAMED',novelty='same-core')
        renamed['spec']['study_id']='E014_RENAMED'; renamed['spec']['random_seed']=999
        self.assertEqual(engine.experiment_signature(first),engine.experiment_signature(renamed))

    def test_e013_completion_is_discovered(self):
        task=self.registered_task('E013_FOUND')
        fixture(self.output/'2026-10-12'/task['id'],task)
        self.assertIn(task['id'],daily.completed_tasks(self.root,None))

    def test_frozen_spec_mismatch_is_rejected(self):
        task=self.registered_task('E013_SPEC'); path=self.output/'fixture'; fixture(path,task)
        frozen=json.loads((path/'FROZEN_SPEC.json').read_text()); frozen['study_spec']['kind']='wrong'
        (path/'FROZEN_SPEC.json').write_text(json.dumps(frozen))
        with self.assertRaises(ValueError): daily.validate_completion(path,task['id'])

    def test_publication_paths_include_all_new_directories_and_report(self):
        first=self.output/'2026-10-12'/'E013_A'; second=self.output/'2026-10-12'/'E014_B'
        first.mkdir(parents=True); second.mkdir(parents=True)
        (first/'COMPLETION.json').write_text('{}'); (second/'COMPLETION.json').write_text('{}')
        report=self.output/'2026-10-12'/'DAILY_MASTER_REPORT_test.md'; report.write_text('report')
        attempt=self.output/'2026-10-12'/'.attempts'/'E015-failed'; attempt.mkdir(parents=True); (attempt/'FAILURE.json').write_text('{}')
        result={'completed_now':[{'path':str(first)},{'path':str(second)}],'daily_master_report':str(report)}
        paths=daily.publication_paths(self.root,result)
        self.assertIn(str(first.relative_to(self.root)),paths); self.assertIn(str(second.relative_to(self.root)),paths)
        self.assertIn(str(report.relative_to(self.root)),paths)
        self.assertIn(str(attempt.relative_to(self.root)),paths)

    def test_completed_question_is_not_run_again(self):
        fixture(self.output / '2026-10-12' / self.task['id'], self.task)
        queue = self.root / 'queue.json'; engine.jsonfile(queue, {'tasks': [self.task]}); result_file=self.root/'result.json'
        with patch.object(engine, 'run') as execute, contextlib.redirect_stdout(io.StringIO()):
            code = daily.run(self.root, self.output, queue, result_file, '2026-10-13')
        execute.assert_not_called(); self.assertEqual(code, 3)
        self.assertEqual(json.loads(result_file.read_text())['status'],'INSUFFICIENT_RESEARCH_QUEUE')

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

    def test_dependency_failure_does_not_claim_empirical_readiness(self):
        wrong = types.SimpleNamespace(__version__='unavailable')
        captured = io.StringIO()
        with patch.dict(sys.modules, {'numpy': wrong}), contextlib.redirect_stdout(captured):
            self.assertEqual(environment.main(self.root, allow_theory_fallback=True), 0)
            with self.assertRaises(SystemExit): environment.main(self.root)
            with self.assertRaises(RuntimeError): engine.comparison_tests({}, [])
        result = json.loads(captured.getvalue())
        self.assertEqual(result['environment'], 'EMPIRICAL_BLOCKED')
        self.assertFalse(result['new_study_claimed'])

    def test_existing_result_is_protected(self):
        queue = self.root / 'queue.json'; engine.jsonfile(queue, {'tasks': [self.task]})
        result = self.root / 'result.json'; result.write_text('existing')
        with self.assertRaises(FileExistsError): daily.run(self.root, self.output, queue, result, '2026-10-12')
        self.assertEqual(result.read_text(), 'existing')

    def test_missing_empirical_source_allows_only_theory_recovery(self):
        available = types.SimpleNamespace(__version__='2.3.5')
        captured = io.StringIO()
        with patch.dict(sys.modules, {'numpy': available}), contextlib.redirect_stdout(captured):
            self.assertEqual(environment.main(self.root, allow_theory_fallback=True), 0)
            with self.assertRaises(SystemExit): environment.main(self.root)
        result = json.loads(captured.getvalue())
        self.assertEqual(result['environment'], 'EMPIRICAL_BLOCKED')
        self.assertTrue(result['independent_theory_possible'])
        self.assertFalse(result['new_study_claimed'])

if __name__ == '__main__': unittest.main()
