import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from runtime.codex_worker import CodexWorker

class DurableFailure(unittest.TestCase):
    def test_missing_cli_is_persisted_as_unavailable(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'calls.jsonl'
            worker=CodexWorker(model='explicit',receipt_path=path)
            with patch('runtime.codex_worker.subprocess.Popen',side_effect=FileNotFoundError('fixture')):
                with self.assertRaises(FileNotFoundError): worker.generate('probe',role='preflight')
            receipt=json.loads(path.read_text())
            self.assertEqual(receipt['status'],'unavailable')
            self.assertEqual(receipt['error_type'],'FileNotFoundError')
            self.assertIsNone(receipt['model_cost'])
