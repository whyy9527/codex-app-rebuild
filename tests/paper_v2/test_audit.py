from copy import deepcopy
import json
from pathlib import Path
import unittest
from workflows.paper.audit import experiment_audit


class EvidenceTamperChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads(Path('projects/paper-v2/experiment.json').read_text())

    def test_real_report_bindings(self):
        self.assertEqual(len(experiment_audit(self.report)),10)

    def test_altered_model_response_is_detected(self):
        changed=deepcopy(self.report)
        request=next(r for r in changed['requests'] if r['role']=='policy-development')
        request['response']['source']='def policy(observed, context):\n return []\n'
        with self.assertRaisesRegex(ValueError,'response source mismatch'):
            experiment_audit(changed)

    def test_altered_feedback_is_detected(self):
        changed=deepcopy(self.report)
        changed['requests'][0]['prompt']+=' altered'
        with self.assertRaisesRegex(ValueError,'binding mismatch'):
            experiment_audit(changed)

    def test_artifact_reuse_is_not_a_model_call(self):
        changed=deepcopy(self.report)
        changed['discovery_responses']=changed['generation_attempts']
        with self.assertRaisesRegex(ValueError,'counts differ'):
            experiment_audit(changed)
