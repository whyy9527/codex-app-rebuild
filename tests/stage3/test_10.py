from copy import deepcopy
import json
from pathlib import Path
import unittest
from workflows.paper.stage_report import interpret_validation

class NoInventedGain(unittest.TestCase):
    def test_real_independent_validation_reports_no_gain(self):
        report=json.loads(Path('projects/paper-v3/validation.json').read_text())
        summary=interpret_validation(report,baseline='ffd')
        self.assertEqual(summary['pairs']['hybrid']['ties'],24)
        self.assertEqual(summary['pairs']['hybrid']['conclusion'],'no_observed_gain')
        self.assertEqual(summary['policy_effect'],'not_tested')
        damaged=deepcopy(report)
        damaged['programs']['hybrid']['mean_score']=1
        with self.assertRaises(ValueError): interpret_validation(damaged,baseline='ffd')
