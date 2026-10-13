import importlib
import json
from pathlib import Path
import tempfile
import unittest

from capabilities.exploration.storage import digest
from runtime.dream import sha
from runtime.runner import input_manifest

viewer = importlib.import_module('projects.xiaogj-web.tools.exploration_tree')


class ExplorationTreeExport(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        (self.root / 'observed.txt').write_text('fixture evidence')
        (self.root / 'snapshot').mkdir()
        (self.root / 'snapshot/value.txt').write_text('PRIVATE-SNAPSHOT-CANARY')
        (self.root / 'policy.py').write_text('def select(view, rho): return []\n')
        history = {'states': [{'id': 'home', 'evidence': 'observed.txt', 'actions': [
            {'id': 'more', 'label': 'More', 'operations': ['hover', 'click']}]}],
            'transitions': [{'from': 'home', 'to': 'home', 'action': 'more',
                             'operation': 'hover', 'outcome': 'unavailable', 'evidence': 'observed.txt'}]}
        self.write('history.json', history)
        nodes = []
        for seq, parent in enumerate((None, 'r', 'r')):
            nodes.append({'id': 'r' if seq == 0 else 'n' + str(seq), 'parent': parent,
                          'seq': seq, 'score': 0 if seq == 0 else .5,
                          'observation': {'account': 'PRIVATE-ACCOUNT-CANARY'},
                          'generation_history': [] if seq == 0 else [
                              {'probe': 'safe-probe', 'other': 'PRIVATE-CONTEXT-CANARY'}],
                          'snapshot': 'snapshot', 'snapshot_digest': digest(input_manifest(self.root, ['snapshot']))})
        self.write('tree.json', {'schema_version': 1, 'kind': 'dream_tree', 'protocol': 'fixed',
                                'nodes': nodes, 'rounds': [], 'stop': 'round_limit',
                                'artifacts': input_manifest(self.root, ['policy.py'])})
        self.write('pool.json', {'schema_version': 1, 'kind': 'dream_pool', 'protocol': 'fixed',
                                'worlds': [{'path': 'tree.json', 'sha256': sha(self.root / 'tree.json')}],
                                'policy': {'path': 'policy.py', 'sha256': sha(self.root / 'policy.py')}})
        self.write('evaluation.json', {'selected_version': 0, 'feedback': [
            {'version': 0, 'score': .2, 'status': 'evaluated', 'private': 'PRIVATE-EVALUATION-CANARY'}]})
        self.inputs = {'exploration_history': 'history.json', 'rsi_pool': 'pool.json',
                       'rsi_evaluation': 'evaluation.json'}

    def write(self, name, value):
        (self.root / name).write_text(json.dumps(value))

    def test_whitelisted_export_keeps_real_root_branches_and_unresolved_operations(self):
        before = {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        result = viewer.collect_data(self.root, self.inputs)
        world = result['protocols'][0]['worlds'][0]
        self.assertEqual([(n['id'], n['parent']) for n in world['nodes']],
                         [('r', None), ('n1', 'r'), ('n2', 'r')])
        self.assertEqual((result['pending'], result['resolved'], result['worlds'], result['nodes']), (2, 0, 1, 3))
        self.assertEqual(result['history']['transitions'][0]['outcome'], 'unavailable')
        rendered = viewer.render(result)
        self.assertNotIn('CANARY', rendered)
        self.assertNotIn('__EXPLORATION_DATA__', rendered)
        self.assertNotIn('window.openai', rendered)
        self.assertEqual({p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()}, before)

    def test_modified_historical_world_is_rejected_before_visualization(self):
        with (self.root / 'tree.json').open('a') as stream:
            stream.write(' ')
        with self.assertRaisesRegex(ValueError, 'historical world changed'):
            viewer.collect_data(self.root, self.inputs)
