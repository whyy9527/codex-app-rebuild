"""Experiment boundary checks; not model/Swift efficacy evidence."""
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from capabilities.exploration.harness import Harness

PROJECT = Path(__file__).resolve().parents[2] / 'projects/business-ablation'


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, PROJECT / filename)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


controller = module('business_controller_test', 'controller.py')
runtime = module('business_runtime_test', 'experiment-runtime.py')


class Controls(unittest.TestCase):
    def test_no_progress_removes_only_projection(self):
        state = {'id': 't', 'objective': 'repair', 'phase': 'ready', 'iterations': 2, 'max_iterations': 20,
                 'verifier': ['python3', 'verify.py'], 'last_error': 'fail', 'acceptance_files': {},
                 'attempts': [{'evaluation': {'status': 'fail', 'exit_code': 1, 'output': 'current actionable failure'}}]}
        with patch.object(runtime, 'settings', return_value={'persist_behavior_progress': True}), patch.object(runtime, 'progress', return_value={'past': 'receipt'}):
            full = runtime.summary(state)
        with patch.object(runtime, 'settings', return_value={'persist_behavior_progress': False}), patch.object(runtime, 'progress', side_effect=AssertionError('must not read history')):
            stripped = runtime.summary(state)
        self.assertEqual(full.pop('behavior_progress'), {'past': 'receipt'})
        self.assertEqual(full, stripped)
        self.assertIn('current actionable failure', stripped['feedback']['output'])

    def test_no_stop_keeps_session_start_but_never_consumes_continuation(self):
        with tempfile.TemporaryDirectory() as directory:
            h = Harness(Path(directory) / 'state')
            state = h.start(workspace=directory, session_id='s', objective='test', verifier=['python3', '-c', 'raise SystemExit(1)'])
            payload = {'hook_event_name': 'Stop', 'cwd': directory, 'session_id': 's', 'turn_id': 't'}
            with patch.object(runtime, 'settings', return_value={'automatic_stop_feedback': False}):
                self.assertEqual(runtime.hook(h, payload), {})
                self.assertEqual(h.read(state['id'])['hook_events'], [])
                start = runtime.hook(h, dict(payload, hook_event_name='SessionStart'))
                self.assertIn('additionalContext', start['hookSpecificOutput'])
            with patch.object(runtime, 'settings', return_value={'automatic_stop_feedback': True}):
                self.assertEqual(runtime.hook(h, payload)['decision'], 'block')

    def test_registered_task_cannot_reset_budget_or_change_verifier(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(runtime, 'ROOT', Path(directory).resolve()), patch.object(runtime, 'settings', return_value={}), patch.object(runtime, 'check_fixed'):
            root = Path(directory).resolve();worker = root / 'worker';worker.mkdir()
            h = runtime.RegisteredHarness(root / 'state')
            args = dict(workspace=str(worker), session_id='s', objective='repair', verifier=['python3', 'verify.py'], max_iterations=20, max_failures=20, max_seconds=5400, verify_seconds=1200, acceptance_paths=runtime.ACCEPTANCE)
            with self.assertRaisesRegex(ValueError, 'registered verifier'):
                h.start(**dict(args, verifier=['python3', 'anything.py']))
            state = h.start(**args)
            h.pause(state['id'], 'unit boundary')
            with self.assertRaisesRegex(ValueError, 'do not reset'):
                h.start(**dict(args, session_id='new'))

    def test_external_frozen_input_tampering_rejected(self):
        from runtime.runner import input_manifest
        with tempfile.TemporaryDirectory() as directory, patch.object(controller, 'ROOT', Path(directory)):
            root = Path(directory)
            (root / 'spec.json').write_text('{"expected":true}')
            (root / 'fixed-inputs.json').write_text(json.dumps(input_manifest(root, ['spec.json'])))
            controller.check_fixed()
            (root / 'spec.json').write_text('{"expected":false}')
            with self.assertRaisesRegex(ValueError, 'changed'):
                controller.check_fixed()

    def run_initial_pass(self, discovery, already_handed_off):
        with tempfile.TemporaryDirectory() as directory, patch.object(controller, 'ROOT', Path(directory)):
            root = Path(directory);(root / 'state').mkdir();(root / 'worker/projects/education-swift/Sources').mkdir(parents=True)
            (root / 'worker/projects/education-swift/Sources/core.swift').write_text('// baseline')
            (root / 'state'/('a'*32+'.json')).write_text(json.dumps({'id': 'a'*32, 'phase': 'verifying', 'iterations': 1, 'deadline': 1e12}))
            (root / 'batch-initial.json').write_text('{}')
            (root / 'experiment-state.json').write_text(json.dumps({'phase': 'initial', 'receipts': [], 'handoff_done': already_handed_off, 'initial_confirmed': False}))
            receipt = {'status': 'pass', 'revision': 'business-initial-four', 'counts': {'pass': 4}, 'integrity': 'verified', 'behaviors': []}
            with patch.object(controller, 'check_fixed'), patch.object(controller, 'settings', return_value={'supplemental_discovery': discovery}), patch.object(controller, 'load', return_value={}), patch.object(controller, 'verify', return_value=receipt), patch.object(controller, 'reveal') as reveal, patch.object(controller, 'Harness') as h, redirect_stdout(io.StringIO()):
                exit_code = controller.run()
                state = json.loads((root / 'experiment-state.json').read_text())
                return exit_code, state['phase'], h.return_value.pause.call_count, reveal.call_count

    def test_handoff_happens_once_and_early_stop_does_not_skip_discovery(self):
        self.assertEqual(self.run_initial_pass(True, False), (1, 'expanded', 1, 1))
        self.assertEqual(self.run_initial_pass(True, True), (1, 'expanded', 0, 1))
        self.assertEqual(self.run_initial_pass(False, False), (1, 'initial', 1, 0))
        self.assertEqual(self.run_initial_pass(False, True), (0, 'complete', 0, 0))


if __name__ == '__main__':
    unittest.main()
