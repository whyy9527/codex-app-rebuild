import tempfile
import unittest
from pathlib import Path
from capabilities.exploration.online import online_rollout


def agent(workspace, observed, context):
    path = workspace / 'value.txt'
    path.write_text(str(int(path.read_text()) + 1))


def evaluator(workspace):
    value = int((workspace / 'value.txt').read_text())
    return {'score': float(value), 'status': 'pass', 'observation': {'value': value}}


def explore(observed, context):
    if len(observed) == 1:
        return ['root']
    if len(observed) == 2:
        return ['root', observed[1]['id']]
    return []


class OnlineExecution(unittest.TestCase):
    def test_real_candidates_resume_parent_snapshots(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / 'input'
            root.mkdir()
            (root / 'value.txt').write_text('0')
            destination = Path(folder) / 'run'
            result = online_rollout(root, destination, agent, evaluator, explore, width=2, max_calls=3)
            self.assertEqual([n['score'] for n in result['nodes']], [1, 1, 2])
            self.assertEqual(result['calls'], 3)
            self.assertEqual(result['rounds'], 2)
            self.assertEqual((root / 'value.txt').read_text(), '0')
            self.assertEqual((destination / 'n0001/value.txt').read_text(), '1')
            self.assertEqual((destination / 'n0003/value.txt').read_text(), '2')
            self.assertEqual(len(result['nodes'][0]['workspace_digest']), 64)

    def test_worker_failure_is_a_zero_score_observation(self):
        def broken(workspace, observed, context):
            raise RuntimeError('generation failed')
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / 'input'
            root.mkdir()
            result = online_rollout(root, Path(folder) / 'out', broken, evaluator,
                                    lambda obs, ctx: ['root'], max_calls=1)
            self.assertEqual(result['nodes'][0]['score'], 0)
            self.assertEqual(result['nodes'][0]['observation']['status'], 'error')
            self.assertEqual(result['calls'], 1)

    def test_destination_cannot_overlap_input(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with self.assertRaises(ValueError):
                online_rollout(root, root / 'out', agent, evaluator, explore)
