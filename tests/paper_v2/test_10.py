import json
import tempfile
import unittest
from pathlib import Path
from workflows.paper.experiment import Experiment
from runtime.request_broker import NeedsResponse


class EndToEndHandoff(unittest.TestCase):
    def test_experiment_waits_for_actual_code_and_resumes_without_fake_proposal(self):
        with tempfile.TemporaryDirectory() as folder:
            root, output = Path(folder)/'input', Path(folder)/'experiment'
            root.mkdir()
            (root/'pack.py').write_text('def pack(weights, capacity):\n return [[i] for i in range(len(weights))]\n')
            experiment = Experiment(root, output, iterations=2, max_calls=1)
            with self.assertRaises(NeedsResponse) as caught: experiment.step()
            request = json.loads(caught.exception.path.read_text())
            self.assertEqual(request['role'],'discovery-generation')
            response = {'request_digest':request['request_digest'],
                        'source':'def pack(weights, capacity):\n return [[i] for i in range(len(weights))]\n',
                        'rationale':'explicit test-double response'}
            caught.exception.path.with_suffix('.response.json').write_text(json.dumps(response))
            resumed = Experiment(root, output, iterations=2, max_calls=1)
            resumed.step()
            resumed.step()
            with self.assertRaises(NeedsResponse) as second: resumed.step()
            self.assertEqual(json.loads(second.exception.path.read_text())['role'],'policy-development')
            self.assertEqual(len(resumed.read()['worlds']),1)
            self.assertEqual(len(resumed.read()['developments']),0)
