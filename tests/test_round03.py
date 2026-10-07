import sys
import tempfile
import time
import unittest
from pathlib import Path
from runtime.runner import evaluate


class BoundedExecution(unittest.TestCase):
    def test_timeout_is_evidence_not_an_exception(self):
        result = evaluate('.', [sys.executable, '-c', 'import time; time.sleep(5)'], timeout=.05)
        self.assertEqual(result['status'], 'timeout')
        self.assertLess(result['wall_seconds'], 2)
        self.assertIsNone(result['exit_code'])

    def test_timeout_cleans_descendant_processes(self):
        with tempfile.TemporaryDirectory() as folder:
            marker = Path(folder) / 'leaked'
            child = f"import time; from pathlib import Path; time.sleep(.35); Path({str(marker)!r}).touch()"
            parent = f"import subprocess, sys, time; subprocess.Popen([sys.executable, '-c', {child!r}]); time.sleep(5)"
            evaluate('.', [sys.executable, '-c', parent], timeout=.1)
            time.sleep(.45)
            self.assertFalse(marker.exists())

    def test_unavailable_and_invalid_budget(self):
        self.assertEqual(evaluate('.', ['nonexistent-exploration-evaluator'])['status'], 'unavailable')
        for timeout in (0, -1, float('nan')):
            with self.assertRaises(ValueError):
                evaluate('.', [sys.executable, '-c', 'pass'], timeout=timeout)
