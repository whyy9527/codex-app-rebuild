import tempfile
from pathlib import Path
import unittest

from capabilities.rebuild.frontend import compare


class FrontendRequirements(unittest.TestCase):
    def test_semantic_success_does_not_hide_frontend_mismatch_or_unvisited_state(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'reference.txt').write_text('Observed reference home and menu')
            contract = {'requirements': [
                {'id': 'unit', 'state': 'home', 'kind': 'accessible_text', 'text': 'Order at a café', 'evidence': ['reference.txt']},
                {'id': 'settings', 'state': 'more-open', 'kind': 'accessible_text', 'text': 'Settings', 'evidence': ['reference.txt']},
                {'id': 'visual', 'state': 'home', 'kind': 'pending', 'description': 'Unimplemented visual comparison', 'evidence': ['reference.txt']}]}
            observed = {'semantic_status': 'pass', 'states': {'home': {'accessible_text': ['Small beginnings']}}}
            result = compare(root, contract, observed)
            self.assertEqual(result['status'], 'fail')
            self.assertEqual([row['status'] for row in result['rows']], ['fail', 'not_run', 'not_run'])
            observed['states']['home']['accessible_text'] = ['Order at a café']
            observed['states']['more-open'] = {'accessible_text': ['Settings']}
            self.assertEqual(compare(root, contract, observed)['status'], 'fail')
            contract['requirements'].pop()
            self.assertEqual(compare(root, contract, observed)['status'], 'pass')

    def test_interaction_requires_observed_boolean_and_failed_action_stays_failed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'reference.txt').write_text('Hover opens, moving out dismisses')
            contract = {'requirements': [{'id': 'hover', 'state': 'home',
                'kind': 'interaction_boolean', 'field': 'opened', 'expected': True,
                'evidence': ['reference.txt']}]}
            for actual, expected in [(None, 'unavailable'), (1, 'unavailable'), (False, 'fail'), (True, 'pass')]:
                observed = {'states': {'home': {'interactions': {'opened': actual}}}}
                self.assertEqual(compare(root, contract, observed)['rows'][0]['status'], expected)

    def test_control_geometry_rejects_displacement_and_missing_measurement(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'reference.txt').write_text('Measured content-relative switch rectangle')
            contract = {'requirements': [{'id': 'switch', 'state': 'settings',
                'kind': 'element_geometry', 'element': 'sound', 'rect': [704, 174, 56, 32],
                'tolerance_points': 1, 'evidence': ['reference.txt']}]}
            for actual, expected in [([704, 174.5, 56, 32], 'pass'), ([704, 190, 56, 32], 'fail'), (None, 'unavailable')]:
                observed = {'states': {'settings': {'elements': {'sound': {'rect': actual}}}}}
                self.assertEqual(compare(root, contract, observed)['rows'][0]['status'], expected)
