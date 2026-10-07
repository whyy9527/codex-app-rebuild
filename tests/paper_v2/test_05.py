import tempfile
import unittest
from pathlib import Path
from runtime.packing import evaluate_packing, packing_protocol


class FixedEvaluator(unittest.TestCase):
    def test_real_program_and_invalid_output(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'pack.py'
            path.write_text('def pack(weights, capacity):\n return [[i] for i in range(len(weights))]\n')
            result = evaluate_packing(Path(folder))
            self.assertEqual(result['status'], 'pass')
            self.assertGreater(result['score'], 0)
            self.assertLess(result['score'], 1)
            path.write_text('def pack(weights, capacity):\n return [[0,0]]\n')
            bad = evaluate_packing(Path(folder))
            self.assertEqual(bad['score'], 0)
            self.assertEqual(bad['status'], 'fail')
            self.assertEqual(result['protocol_digest'], bad['protocol_digest'])
            self.assertEqual(result['protocol_digest'], packing_protocol())
