import json
from pathlib import Path
import tempfile
import unittest
from capabilities.exploration.development import develop_policy
from runtime.request_broker import FileWorker,NeedsResponse
from workflows.paper.audit import experiment_audit
from tests.stage3.test_01 import STOP,REFINE

class PoolReplayAudit(unittest.TestCase):
    def test_archived_selection_can_be_independently_replayed(self):
        with tempfile.TemporaryDirectory() as folder:
            broker=FileWorker(folder)
            class FixtureResponder:
                def generate(self,prompt,role):
                    try: return broker.generate(prompt,role=role)
                    except NeedsResponse as needed:
                        request=json.loads(needed.path.read_text())
                        needed.path.with_suffix('.response.json').write_text(json.dumps({'request_digest':request['request_digest'],'source':STOP,'rationale':'test double'}))
                        return broker.generate(prompt,role=role)
            world=[{'id':'a','parent':'root','score':.1},{'id':'b','parent':'a','score':1.0},{'id':'c','parent':'b','score':1.0}]
            development=develop_policy(FixtureResponder(),[world],STOP,candidate_sources=[REFINE],width=1,max_calls=2,max_rounds=2)
            development['iteration']=1
            path=next(p for p in Path(folder).glob('*.json') if not p.name.endswith('.response.json'))
            request=json.loads(path.read_text())
            request['response']=json.loads(path.with_suffix('.response.json').read_text())
            report={'requests':[request],'developments':[development],'policy_responses':1,'discovery_responses':0,'online_runs':{},'programs':{},'generation_attempts':0,'reused_discovery_responses':0}
            self.assertTrue(experiment_audit(report,replay=True)[0]['replayed'])
