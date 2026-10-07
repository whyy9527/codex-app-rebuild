import unittest
from runtime.policy_runtime import RestrictedPolicy


class PolicyBoundary(unittest.TestCase):
    def test_prefix_execution_and_timeout(self):
        policy = RestrictedPolicy('def policy(observed, context):\n return [observed[-1]["id"]]\n')
        self.assertEqual(policy([{'id': 'root'}], {}), ['root'])
        loop = RestrictedPolicy('def policy(observed, context):\n while True: pass\n', timeout=.1)
        with self.assertRaises(TimeoutError):
            loop([], {})

    def test_rejects_hidden_state_and_host_access(self):
        for source in ('import os\ndef policy(a,b): return []',
                       'def policy(a,b): return open("secret").read()',
                       'def policy(a,b): return a.__class__',
                       'x = print("effect")\ndef policy(a,b): return []'):
            with self.assertRaises(ValueError):
                RestrictedPolicy(source)
