import json
from pathlib import Path
import tempfile
import unittest
from runtime.request_broker import FileWorker,NeedsResponse

class ResponseScope(unittest.TestCase):
    def test_independent_arms_and_explicit_reuse(self):
        with tempfile.TemporaryDirectory() as folder:
            ids=[]
            for scope in ('fixed','updated'):
                worker=FileWorker(folder,scope=scope)
                with self.assertRaises(NeedsResponse) as caught: worker.generate('same prompt',role='discovery-generation')
                path=caught.exception.path
                request=json.loads(path.read_text())
                ids.append(request['request_digest'])
                path.with_suffix('.response.json').write_text(json.dumps({'request_digest':ids[-1],'source':'def pack(a,b):\n return []\n','rationale':'fixture'}))
                self.assertFalse(worker.generate('same prompt',role='discovery-generation')['receipt']['response_reused'])
                self.assertTrue(worker.generate('same prompt',role='discovery-generation')['receipt']['response_reused'])
            self.assertNotEqual(*ids)
