import tempfile
from pathlib import Path
import unittest

from capabilities.rebuild.discovery import frontier


class DiscoveryFrontier(unittest.TestCase):
    def test_new_menu_actions_remain_pending_and_unavailable_is_not_completion(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'observation.txt').write_text('Real observation placeholder for mechanism test')
            history = {'states': [
                {'id': 'home', 'evidence': 'observation.txt', 'actions': [{'id': 'hover-more'}]},
                {'id': 'menu', 'evidence': 'observation.txt', 'actions': [{'id': 'settings'}, {'id': 'help'}]}],
                'transitions': [{'from': 'home', 'action': 'hover-more', 'outcome': 'observed', 'to': 'menu', 'evidence': 'observation.txt'},
                                {'from': 'menu', 'action': 'settings', 'outcome': 'unavailable', 'evidence': 'observation.txt'}]}
            result = frontier(root, history)
            self.assertEqual([row['action']['id'] for row in result['pending']], ['help', 'settings'])
            self.assertEqual(result['resolved_actions'], 1)
            history['transitions'][0]['action'] = 'invented-action'
            with self.assertRaises(ValueError):
                frontier(root, history)
