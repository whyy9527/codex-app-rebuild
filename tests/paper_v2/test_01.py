import unittest
from runtime.codex_worker import parse_attestation, validate_reply


class WorkerContract(unittest.TestCase):
    def test_runtime_attestation_and_schema(self):
        banner = 'OpenAI Codex v0.160.1\n--------\nmodel: gpt-6.1-sol\nprovider: openai\nreasoning effort: medium\n--------\n'
        self.assertEqual(parse_attestation(banner, 'gpt-6.1-sol', 'medium')['model'], 'gpt-6.1-sol')
        with self.assertRaises(ValueError):
            parse_attestation(banner, 'different', 'medium')
        self.assertEqual(validate_reply({'source': 'def policy(observed, context):\n return []\n', 'rationale': 'stop'})['rationale'], 'stop')
        for value in ({'source': '', 'rationale': 'x'}, {'source': 'code', 'rationale': 1}):
            with self.assertRaises(ValueError):
                validate_reply(value)
