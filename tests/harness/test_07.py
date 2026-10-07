from pathlib import Path
import tempfile
import unittest
from capabilities.exploration.harness import Harness
from runtime.harness_hooks import handle

class UserInterrupt(unittest.TestCase):
    def test_interrupt_pauses_and_only_explicit_resume_reactivates(self):
        with tempfile.TemporaryDirectory() as folder:
            harness=Harness(Path(folder)/'state')
            task=harness.start(workspace=folder,session_id='s',objective='fix',verifier=['python3','-m','unittest'])
            event={'cwd':folder,'session_id':'s','hook_event_name':'Interrupt','turn_id':'one'}
            handle(harness,event)
            self.assertEqual(harness.read(task['id'])['phase'],'paused')
            self.assertEqual(handle(harness,{**event,'hook_event_name':'Stop'}),{})
            self.assertEqual(harness.resume(task['id'])['phase'],'ready')
