import unittest
from capabilities.exploration.replay import run_replay
from tests.test_round05 import WORLD


class ReplayBudget(unittest.TestCase):
    def test_call_and_round_budgets(self):
        def branch(observed, context):
            return ['root']
        result = run_replay(WORLD, branch, max_calls=1, max_rounds=10)
        self.assertEqual((result['calls'], result['rounds'], result['reason']), (1, 1, 'call_budget'))
        result = run_replay(WORLD, branch, max_calls=10, max_rounds=1)
        self.assertEqual((result['calls'], result['rounds'], result['reason']), (1, 1, 'round_budget'))

    def test_unsupported_and_overbudget_do_not_earn_reward(self):
        def unsupported(observed, context):
            return ['root'] if len(observed) < 3 else ['b']
        result = run_replay(WORLD, unsupported, max_calls=10)
        self.assertFalse(result['valid'])
        self.assertEqual(result['reason'], 'unsupported')
        self.assertEqual(result['calls'], 2)
        self.assertEqual(result['best_score'], 0)
        result = run_replay(WORLD, lambda obs, ctx: ['root'] if len(obs) == 1 else ['root', 'a'],
                            width=2, max_calls=2)
        self.assertEqual(result['reason'], 'over_budget')
        self.assertFalse(result['valid'])

    def test_policy_only_receives_prefix_and_public_budget(self):
        seen = []
        def policy(observed, context):
            seen.append((observed, context))
            return ['root'] if len(observed) == 1 else []
        result = run_replay(WORLD, policy, rho=.75)
        self.assertEqual(result['reason'], 'stopped')
        self.assertEqual([n['id'] for n in seen[0][0]], ['root'])
        self.assertNotIn('world', seen[0][1])
        self.assertNotIn('best_recorded_score', seen[0][1])
        self.assertEqual(seen[0][1]['rho'], .75)
        for budget in (-1, True):
            with self.assertRaises(ValueError):
                run_replay(WORLD, policy, max_calls=budget)
