import unittest
from capabilities.exploration.development import develop_policy

BASE = 'def policy(observed, context):\n return []\n'
WORLD = [[{'id':'n0001','parent':'root','score':1}, {'id':'n0002','parent':'root','score':.5}]]


class Worker:
    def __init__(self, source):
        self.source, self.prompt = source, ''
    def generate(self, prompt, role):
        self.prompt = prompt
        return {'source':self.source, 'rationale':'respond to observed feedback',
                'receipt':{'role':role, 'test_double':True}}


class FeedbackRevision(unittest.TestCase):
    def test_feedback_reaches_worker_and_proposal_is_evaluated(self):
        worker = Worker('def policy(observed, context):\n if len(observed) == 1: return ["root"]\n return []\n')
        result = develop_policy(worker, WORLD, BASE, previous_feedback={'failure':'premature stop'}, width=1)
        self.assertIn('premature stop', worker.prompt)
        self.assertEqual(result['status'], 'evaluated')
        self.assertEqual(result['selected'], 'proposal')
        self.assertTrue(result['structure_changed'])
        self.assertIn('feedback_digest', result)

    def test_hardcoded_historical_ids_rejected(self):
        result = develop_policy(Worker('def policy(observed, context):\n return ["n0001"]\n'), WORLD, BASE)
        self.assertEqual(result['status'], 'rejected')
        self.assertEqual(result['selected'], 'incumbent')
