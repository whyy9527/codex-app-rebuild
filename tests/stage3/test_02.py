import unittest
from capabilities.exploration.development import develop_policy
from tests.stage3.test_01 import STOP,REFINE

class ArchiveDevelopment(unittest.TestCase):
    def test_archive_winner_is_deployed_even_if_new_proposal_loses(self):
        class Worker:
            def generate(self,prompt,role):
                return {'source':STOP,'rationale':'explicit test fixture','receipt':{'transport':'test-double'}}
        world=[{'id':'a','parent':'root','score':.1},{'id':'b','parent':'a','score':1.0},{'id':'c','parent':'b','score':1.0}]
        result=develop_policy(Worker(),[world],STOP,candidate_sources=[REFINE],width=1,max_calls=2,max_rounds=2)
        self.assertEqual(result['selected_source'],REFINE)
        self.assertTrue(result['selected'].startswith('archive-'))
