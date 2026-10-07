import unittest
from capabilities.exploration.pool import select_pool

STOP='def policy(observed, context):\n return ["root"] if len(observed)==1 else []\n'
REFINE='def policy(observed, context):\n return [observed[-1]["id"]]\n'

class CompletePool(unittest.TestCase):
    def test_old_rejected_source_can_win_after_new_world(self):
        world=[{'id':'a','parent':'root','score':.1},{'id':'b','parent':'a','score':1.0},{'id':'c','parent':'b','score':1.0}]
        result=select_pool([world],STOP,[REFINE,REFINE],max_calls=2,max_rounds=2)
        self.assertEqual(result['selected_source'],REFINE)
        self.assertEqual(len(result['candidates']),2)
        self.assertEqual(result['scope'],'frozen-history score only; new-task improvement unverified')
