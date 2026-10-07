import tempfile
import unittest
from pathlib import Path
from runtime.discovery import ModelDiscovery
from capabilities.exploration.comparison import compare_runs


class ControlledDiscovery(unittest.TestCase):
    def test_parent_code_history_and_fixed_protocol_reach_generator(self):
        class Worker:
            def generate(self, prompt, role):
                self.prompt = prompt
                return {'source':'def pack(a,b):\n return [[i] for i in range(len(a))]\n',
                        'rationale':'test response', 'receipt':{'transport':'test-double'}}
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root/'pack.py').write_text('def pack(weights, capacity):\n return []\n')
            worker = Worker()
            adapter = ModelDiscovery(worker, history=[{'recorded_failure':'overflow'}])
            receipt = adapter(root, [{'id':'root','score':0}], {'parent':'root'})
            self.assertIn('overflow', worker.prompt)
            self.assertIn('return []', worker.prompt)
            self.assertIn('generator_protocol', receipt)

    def test_mismatched_evaluator_rejected_and_unknown_model_is_partial(self):
        def run(protocol):
            return {'config':{'input_digest':'same','max_calls':4,'width':1}, 'nodes':[
                {'score':.8,'observation':{'protocol_digest':protocol},
                 'generation':{'generator_protocol':'same','transport':'interactive-codex-main-session'}}]}
        result = compare_runs(run('fixed'), run('fixed'))
        self.assertEqual(result['control_status'], 'partial_model_unattested')
        with self.assertRaises(ValueError): compare_runs(run('fixed'), run('changed'))
