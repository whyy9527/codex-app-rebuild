import math
import unittest
from capabilities.exploration.replay import Replay


class WorldValidation(unittest.TestCase):
    def test_rejects_ambiguous_or_noncausal_worlds(self):
        bad = [
            [{'id': 'a', 'parent': 'root', 'score': math.nan}],
            [{'id': 'a', 'parent': 'root', 'score': math.inf}],
            [{'id': 'a', 'parent': 'root', 'score': True}],
            [{'id': 'a', 'parent': 'root', 'score': -1}],
            [{'id': 'a', 'parent': 'missing', 'score': 1}],
            [{'id': 'root', 'parent': 'root', 'score': 1}],
            [{'id': 'a', 'parent': 'root', 'score': 1}, {'id': 'a', 'parent': 'root', 'score': 2}],
            [{'id': 'a', 'parent': 'root', 'score': 1}, {'id': 'b', 'parent': 'a', 'score': 1},
             {'id': 'c', 'parent': 'a', 'score': 2}],
        ]
        for world in bad:
            with self.subTest(world=world), self.assertRaises(ValueError):
                Replay(world)

    def test_root_can_open_multiple_chronological_branches(self):
        replay = Replay([{'id': 'a', 'parent': 'root', 'score': 0},
                         {'id': 'b', 'parent': 'root', 'score': 1}])
        self.assertEqual(replay.step(['root'])['revealed'][0]['id'], 'a')
        self.assertEqual(replay.step(['root'])['revealed'][0]['id'], 'b')
