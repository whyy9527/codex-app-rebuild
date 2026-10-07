import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from workflows.self_improve.cycle import run_cycles


class IntegratedCycle(unittest.TestCase):
    def test_two_real_cycles_expand_world_pool_and_redeploy_source(self):
        with tempfile.TemporaryDirectory() as folder:
            result = run_cycles(Path(folder) / 'run', rounds=2)
            self.assertEqual(len(result['cycles']), 2)
            self.assertEqual(result['cycles'][1]['history_worlds'], 2)
            self.assertEqual(result['cycles'][0]['next_policy_digest'], result['cycles'][1]['online_policy_digest'])
            self.assertGreater(result['total_generation_calls'], 0)
            self.assertEqual(result['generation_kind'], 'deterministic toy program adapter, not LLM')
            for cycle in result['cycles']:
                self.assertGreaterEqual(cycle['selected_replay_score'], cycle['incumbent_replay_score'])
                self.assertTrue(cycle['policy_sources'])
            self.assertIsNone(result['model_tokens'])
            self.assertIn('fixed', result['held_out'])
            self.assertIn('selected', result['held_out'])
            self.assertTrue((Path(folder) / 'run/report.json').exists())

    def test_cli_preserves_evaluator_failure_exit_status(self):
        with tempfile.TemporaryDirectory() as folder:
            result = subprocess.run(['python3', '-m', 'workflows.self_improve', '--db',
                                     str(Path(folder) / 'db'), 'run', '--id', 'bad', '--round', '0',
                                     '--phase', 'baseline', '--hypothesis', 'failure is nonzero',
                                     '--', 'python3', '-c', 'raise SystemExit(7)'], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(json.loads(result.stdout)['status'], 'fail')
