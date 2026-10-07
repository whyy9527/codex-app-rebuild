import json
import sys
import tempfile
import unittest
from pathlib import Path
from capabilities.exploration.ledger import Ledger
from runtime.runner import evaluate


class EvidenceIntegrity(unittest.TestCase):
    def test_modified_receipt_and_deleted_prefix_detected(self):
        with tempfile.TemporaryDirectory() as folder:
            ledger = Ledger(Path(folder) / 'db')
            ledger.append({'id': 'a', 'parent': None, 'value': 1})
            ledger.append({'id': 'b', 'parent': 'a', 'value': 2})
            self.assertEqual(ledger.verify()['records'], 2)
            changed = ledger.records()[0]
            changed['value'] = 9
            ledger.db.execute('UPDATE records SET payload = ? WHERE id = ?', (json.dumps(changed), 'a'))
            ledger.db.commit()
            with self.assertRaises(ValueError):
                ledger.verify()
            ledger.close()

    def test_mutating_evaluator_cannot_report_pass(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'capabilities').mkdir()
            (root / 'capabilities/subject.py').write_text('before = True\n')
            result = evaluate(root, [sys.executable, '-c', "from pathlib import Path; Path('capabilities/subject.py').write_text('after = True\\n')"])
            self.assertEqual(result['status'], 'invalid')
            self.assertEqual(result['integrity'], 'source_changed')
            self.assertTrue((root / result['snapshot'] / 'capabilities/subject.py').exists())
            self.assertEqual((root / result['snapshot'] / 'capabilities/subject.py').read_text(), 'before = True\n')
