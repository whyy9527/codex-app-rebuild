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

    def test_identical_copy_cannot_hide_wrong_radio_role_or_enabled_state(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'reference.txt').write_text('Source feedback: radio 2 checked and disabled')
            contract = {'requirements': [
                {'id': 'role', 'state': 'feedback', 'kind': 'element_role', 'element': 'option-1', 'role': 'radio', 'evidence': ['reference.txt']},
                {'id': 'disabled', 'state': 'feedback', 'kind': 'element_boolean', 'element': 'option-1', 'field': 'enabled', 'expected': False, 'evidence': ['reference.txt']}]}
            for role in ['radio', 'AXRadioButton']:
                observed = {'states': {'feedback': {'accessible_text': ['2'], 'elements': {'option-1': {'role': role, 'enabled': False}}}}}
                self.assertEqual(compare(root, contract, observed)['status'], 'pass')
            observed['states']['feedback']['elements']['option-1'] = {'role': 'AXButton', 'enabled': True}
            self.assertEqual([x['status'] for x in compare(root, contract, observed)['rows']], ['fail', 'fail'])
            observed['states']['feedback']['elements']['option-1'] = {'role': None, 'enabled': None}
            self.assertEqual([x['status'] for x in compare(root, contract, observed)['rows']], ['unavailable', 'unavailable'])

    def test_checked_state_requires_boolean_measurement_and_detects_wrong_selection(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'reference.txt').write_text('Source radio 2 checked in accepted feedback')
            contract = {'requirements': [{'id': 'checked', 'state': 'feedback',
                'kind': 'element_boolean', 'element': 'option-1', 'field': 'checked',
                'expected': True, 'evidence': ['reference.txt']}]}
            for value, expected in [(True, 'pass'), (False, 'fail'), (1, 'unavailable'), (None, 'unavailable')]:
                observed = {'states': {'feedback': {'elements': {'option-1': {'checked': value}}}}}
                self.assertEqual(compare(root, contract, observed)['rows'][0]['status'], expected)

    def test_pixel_color_requires_rgb_measurement_and_rejects_wrong_feedback_color(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'reference.txt').write_text('Actual source correct-option background sampled from PNG')
            contract = {'requirements': [{'id': 'color', 'state': 'feedback', 'kind': 'pixel_color',
                'point': [850, 500], 'rgb': [215, 255, 184], 'evidence': ['reference.txt']}]}
            for rgb, expected in [([215, 255, 184], 'pass'), ([229, 247, 252], 'fail'),
                                  (True, 'unavailable'), ([215, True, 184], 'unavailable'), (None, 'unavailable')]:
                observed = {'states': {'feedback': {'pixel_color_space': 'sRGB', 'pixel_samples': {'850,500': rgb}}}}
                self.assertEqual(compare(root, contract, observed)['rows'][0]['status'], expected)

            observed['states']['feedback'] = {'pixel_samples': {'850,500': [215, 255, 184]}}
            self.assertEqual(compare(root, contract, observed)['rows'][0]['status'], 'unavailable')
