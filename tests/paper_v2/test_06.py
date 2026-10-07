import unittest
from capabilities.exploration.replay import run_replay
from capabilities.exploration.objective import replay_score


class PaperTransitions(unittest.TestCase):
    def test_empty_continuations_count_rounds_without_fabricating_calls(self):
        world = [{'id':'a','parent':'root','score':.2}, {'id':'aa','parent':'a','score':1}]
        result = run_replay(world, lambda obs, ctx: ['root'], max_rounds=3, semantics='paper')
        self.assertTrue(result['valid'])
        self.assertEqual((result['rounds'], result['calls']), (3,1))
        self.assertEqual(result['best_score'], .2)
        self.assertIsNotNone(replay_score([result], total_calls=2, best_recorded=1))

    def test_mixed_batch_reveals_only_available_recorded_children(self):
        world = [{'id':'a','parent':'root','score':.2}, {'id':'b','parent':'root','score':.3},
                 {'id':'aa','parent':'a','score':1}]
        def policy(obs, ctx):
            if len(obs) < 3: return ['root']
            return ['a','b']
        result = run_replay(world, policy, width=2, semantics='paper')
        self.assertTrue(result['valid'])
        self.assertEqual(result['calls'], 3)
        self.assertEqual(result['best_score'], 1)
