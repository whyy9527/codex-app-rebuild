from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from capabilities.exploration.session import OnlineSession
from capabilities.exploration.online import copy_workspace

class CopyCrashRecovery(unittest.TestCase):
    def test_crash_during_candidate_copy_can_resume_once(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)/'input'
            root.mkdir()
            (root/'pack.py').write_text('parent')
            output=Path(folder)/'run'
            source='def policy(observed, context):\n return ["root"]\n'
            session=OnlineSession(root,output,source,max_calls=1)
            def interrupted(parent,destination):
                copy_workspace(parent,destination)
                raise RuntimeError('injected crash after copying')
            with patch('capabilities.exploration.session.copy_workspace',side_effect=interrupted):
                with self.assertRaises(RuntimeError): session.advance(lambda *a:{},lambda w:{'status':'pass','score':1})
            resumed=OnlineSession(root,output,source,max_calls=1)
            state=resumed.advance(lambda *a:{'transport':'explicit test fixture'},lambda w:{'status':'pass','score':1})
            self.assertEqual(len(state['nodes']),1)
            self.assertEqual((output/'n0001/pack.py').read_text(),'parent')
