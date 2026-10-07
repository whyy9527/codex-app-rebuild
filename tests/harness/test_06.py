from pathlib import Path
import tempfile
import unittest
from capabilities.exploration.harness import Harness
from runtime.harness_hooks import handle

class BoundedContinuation(unittest.TestCase):
    def test_duplicate_stop_does_not_spawn_again_and_stagnation_stops(self):
        with tempfile.TemporaryDirectory() as folder:
            harness=Harness(Path(folder)/'state')
            task=harness.start(workspace=folder,session_id='s',objective='fix',verifier=['python3','-m','unittest'])
            event={'cwd':folder,'session_id':'s','hook_event_name':'Stop','turn_id':'one'}
            self.assertEqual(handle(harness,event)['decision'],'block')
            self.assertEqual(handle(harness,event),{})
            self.assertEqual(handle(harness,{**event,'turn_id':'two','stop_hook_active':True}),{})
            self.assertEqual(harness.read(task['id'])['phase'],'blocked')
