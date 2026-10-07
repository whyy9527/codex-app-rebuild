import unittest
from unittest.mock import patch, Mock
from runtime.codex_worker import CodexWorker
from capabilities.exploration.development import develop_policy
from tests.paper_v2.test_03 import Worker, WORLD, BASE


class FailedAttempts(unittest.TestCase):
    def test_malformed_source_is_a_rejected_candidate(self):
        result = develop_policy(Worker('def broken('), WORLD, BASE)
        self.assertEqual(result['status'], 'rejected')
        self.assertEqual(result['selected'], 'incumbent')
        self.assertIn('model_receipt', result)

    def test_failed_model_call_retains_cost_scope_and_diagnostic_hash(self):
        process = Mock(pid=999999999, returncode=1)
        process.communicate.return_value = ('', 'model unavailable')
        with patch('runtime.codex_worker.subprocess.Popen', return_value=process):
            worker = CodexWorker(model='explicit-model')
            with self.assertRaises(RuntimeError):
                worker.generate('prompt', role='policy-development')
        self.assertEqual(worker.receipts[0]['status'], 'fail')
        self.assertIsNone(worker.receipts[0]['model_cost'])
        self.assertIn('stderr_sha256', worker.receipts[0])
