from pathlib import Path
import tempfile
import unittest
from capabilities.exploration.harness import Harness
from runtime.harness_hooks import handle

class LifecycleHooks(unittest.TestCase):
    def test_hooks_only_continue_an_explicitly_started_scoped_task(self):
        with tempfile.TemporaryDirectory() as folder:
            harness=Harness(Path(folder)/'state')
            event={'cwd':folder,'session_id':'s','hook_event_name':'Stop','turn_id':'t'}
            self.assertEqual(handle(harness,event),{})
            start=handle(harness,{**event,'hook_event_name':'SessionStart'})
            self.assertIn('exploration_start',start['hookSpecificOutput']['additionalContext'])
            harness.start(workspace=folder,session_id='s',objective='fix',verifier=['python3','-m','unittest'])
            self.assertEqual(handle(harness,event)['decision'],'block')
            self.assertEqual(handle(harness,{**event,'session_id':'other'}),{})
