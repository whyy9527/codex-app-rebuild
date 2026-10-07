import unittest
from capabilities.exploration.replay import Replay

WORLD = [{'id': 'a', 'parent': 'root', 'score': .2},
         {'id': 'b', 'parent': 'root', 'score': .3},
         {'id': 'aa', 'parent': 'a', 'score': .8}]


class LegalReplay(unittest.TestCase):
    def test_duplicate_unseen_nonleaf_and_overwide_rejected(self):
        replay = Replay(WORLD, width=2)
        for action in (['root', 'root'], ['aa'], ['root', 'a', 'b']):
            with self.assertRaises(ValueError):
                replay.step(action)
        self.assertEqual(len(replay.observation()), 1)
        replay.step(['root'])
        replay.step(['a'])
        with self.assertRaises(ValueError):
            replay.step(['a'])

    def test_atomic_unsupported_batch(self):
        replay = Replay(WORLD, width=2)
        replay.step(['root'])
        replay.step(['root'])
        before = replay.observation()
        self.assertEqual(replay.step(['a', 'b'])['status'], 'unsupported')
        self.assertEqual(replay.observation(), before)
        self.assertEqual(replay.rounds, 2)

    def test_parallel_batch_stop_and_view_isolation(self):
        replay = Replay(WORLD, width=2)
        replay.step(['root'])
        result = replay.step(['root', 'a'])
        self.assertEqual([n['id'] for n in result['revealed']], ['b', 'aa'])
        result['revealed'][0]['score'] = 99
        self.assertEqual(replay.observation()[2]['score'], .3)
        self.assertEqual(replay.step([])['status'], 'stopped')
        self.assertEqual(replay.rounds, 2)
