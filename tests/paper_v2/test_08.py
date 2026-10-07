import tempfile
import unittest
from pathlib import Path
from capabilities.exploration.session import OnlineSession
from runtime.request_broker import NeedsResponse


class ResumableOnline(unittest.TestCase):
    def test_wait_resume_preserves_parent_and_completed_attempts(self):
        with tempfile.TemporaryDirectory() as folder:
            source, output = Path(folder)/'input', Path(folder)/'run'
            source.mkdir()
            (source/'value.txt').write_text('0')
            ready, calls = [], []
            def agent(work, observed, context):
                calls.append(1)
                if not ready: raise NeedsResponse(Path(folder)/'request.json')
                (work/'value.txt').write_text('1')
                return {'transport':'test-double'}
            def evaluator(work):
                return {'status':'pass','score':float((work/'value.txt').read_text())}
            policy = 'def policy(observed, context):\n return ["root"]\n'
            session = OnlineSession(source, output, policy, max_calls=1)
            with self.assertRaises(NeedsResponse): session.advance(agent, evaluator)
            ready.append(True)
            resumed = OnlineSession(source, output, policy, max_calls=1)
            resumed.advance(agent, evaluator)
            state = resumed.advance(agent, evaluator)
            self.assertTrue(state['done'])
            self.assertEqual(len(state['nodes']), 1)
            self.assertEqual(len(calls), 2)
            self.assertEqual((source/'value.txt').read_text(), '0')
            with self.assertRaises(ValueError):
                OnlineSession(source, output, 'def policy(a,b):\n return []\n', max_calls=1)
