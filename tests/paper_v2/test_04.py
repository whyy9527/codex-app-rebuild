import json
import tempfile
import unittest
from pathlib import Path
from runtime.request_broker import FileWorker, NeedsResponse


class DurableModelRequests(unittest.TestCase):
    def test_request_response_binding_and_recovery(self):
        with tempfile.TemporaryDirectory() as folder:
            worker = FileWorker(folder)
            with self.assertRaises(NeedsResponse) as caught:
                worker.generate('revise based on failures', role='policy-development')
            request = json.loads(caught.exception.path.read_text())
            response = {'request_digest': request['request_digest'], 'source': 'def policy(a,b):\n return []\n', 'rationale': 'stop'}
            caught.exception.path.with_suffix('.response.json').write_text(json.dumps(response))
            recovered = FileWorker(folder).generate('revise based on failures', role='policy-development')
            self.assertEqual(recovered['receipt']['transport'], 'interactive-codex-main-session')
            self.assertEqual(recovered['receipt']['request_digest'], request['request_digest'])
            self.assertIsNone(recovered['receipt']['runtime_model'])
            response['request_digest'] = 'wrong'
            caught.exception.path.with_suffix('.response.json').write_text(json.dumps(response))
            with self.assertRaises(ValueError):
                worker.generate('revise based on failures', role='policy-development')
