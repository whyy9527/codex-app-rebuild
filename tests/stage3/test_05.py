import unittest
from workflows.paper.preflight import probe

class AvailabilityGate(unittest.TestCase):
    def test_unattested_reply_is_not_an_available_model(self):
        class Unattested:
            receipts=[]
            def generate(self,prompt,role):
                return {'source':'def policy(observed, context):\n return []\n','receipt':{'status':'pass'}}
        result=probe(Unattested())
        self.assertFalse(result['available'])
        self.assertEqual(result['status'],'invalid')
