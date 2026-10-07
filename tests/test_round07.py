import unittest
from capabilities.exploration.objective import replay_score, select_policy


class ReplayObjective(unittest.TestCase):
    def test_paper_hypervolume_and_parallel_penalty_by_hand(self):
        runs = [{'valid': True, 'calls': n, 'rounds': n, 'best_score': s}
                for n, s in [(0, 0), (1, 5), (2, 10), (3, 10), (4, 10)]]
        score = replay_score(runs, total_calls=4, best_recorded=10, penalty=.1)
        self.assertAlmostEqual(score, .625 - .08)
        runs[2]['rounds'] = 1
        self.assertGreater(replay_score(runs, total_calls=4, best_recorded=10, penalty=.1), score)
        runs[0]['valid'] = False
        self.assertIsNone(replay_score(runs, total_calls=4, best_recorded=10, penalty=.1))

    def test_incumbent_is_retained_and_all_worlds_evaluated(self):
        def incumbent(obs, ctx):
            return ['root'] if len(obs) == 1 else []
        def worse(obs, ctx):
            return []
        worlds = [[{'id': 'a', 'parent': 'root', 'score': 1},
                   {'id': 'b', 'parent': 'root', 'score': .5}],
                  [{'id': 'c', 'parent': 'root', 'score': .8},
                   {'id': 'd', 'parent': 'root', 'score': 1}]]
        result = select_policy(worlds, {'incumbent': incumbent, 'worse': worse}, incumbent='incumbent')
        self.assertEqual(result['selected'], 'incumbent')
        self.assertEqual(len(result['candidates']['incumbent']['worlds']), 2)
        self.assertEqual(len(result['candidates']['incumbent']['worlds'][0]['runs']), 5)
        with self.assertRaises(ValueError):
            select_policy(worlds, {'worse': worse}, incumbent='missing')

    def test_unsupported_policy_is_ineligible_and_ties_keep_incumbent(self):
        def one(obs, ctx):
            return ['root'] if len(obs) == 1 else []
        def unsupported(obs, ctx):
            return ['root']
        world = [[{'id': 'a', 'parent': 'root', 'score': 1},
                  {'id': 'aa', 'parent': 'a', 'score': 2}]]
        result = select_policy(world, {'one': one, 'bad': unsupported, 'same': one}, incumbent='one')
        self.assertIsNone(result['candidates']['bad']['score'])
        self.assertEqual(result['selected'], 'one')
