from pathlib import Path
import tempfile
import unittest
from capabilities.exploration.harness import Harness
from capabilities.exploration.storage import digest
from runtime.harness_hooks import handle

class BoundedContinuation(unittest.TestCase):
    def test_same_host_turn_can_continue_again_after_measured_progress(self):
        with tempfile.TemporaryDirectory() as folder:
            harness=Harness(Path(folder)/'state')
            task=harness.start(workspace=folder,session_id='s',objective='complete staged work',
                               verifier=['python3','-c','raise SystemExit(1)'],
                               max_iterations=3,max_failures=4)
            event={'cwd':folder,'session_id':'s','hook_event_name':'Stop','turn_id':'same-host-turn'}
            for attempt in range(2):
                harness.begin(task['id'],'make measured stage progress')
                self.assertEqual(harness.verify(task['id'])['phase'],'ready')
                self.assertEqual(handle(harness,event).get('decision'),'block')
                self.assertEqual(handle(harness,event),{})
                if attempt==0:
                    stored=harness.read(task['id'])
                    stored['hook_events']=[digest(['s','same-host-turn','Stop'])]
                    harness.write(stored)
                    self.assertEqual(handle(harness,event),{})
                self.assertEqual(harness.read(task['id'])['phase'],'ready')
            harness.begin(task['id'],'last bounded stage attempt')
            self.assertEqual(harness.verify(task['id'])['phase'],'budget_exhausted')
            self.assertEqual(handle(harness,event),{})

    def test_duplicate_stop_does_not_spawn_again_and_stagnation_stops(self):
        with tempfile.TemporaryDirectory() as folder:
            harness=Harness(Path(folder)/'state')
            task=harness.start(workspace=folder,session_id='s',objective='fix',verifier=['python3','-m','unittest'])
            event={'cwd':folder,'session_id':'s','hook_event_name':'Stop','turn_id':'one'}
            self.assertEqual(handle(harness,event)['decision'],'block')
            self.assertEqual(handle(harness,event),{})
            self.assertEqual(handle(harness,{**event,'turn_id':'two','stop_hook_active':True}),{})
            self.assertEqual(harness.read(task['id'])['phase'],'blocked')
