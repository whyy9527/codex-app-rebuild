import sqlite3
import tempfile
import unittest
from pathlib import Path
from capabilities.exploration.ledger import Ledger


class LedgerIntegrity(unittest.TestCase):
    def test_unknown_parent_rejected_without_partial_write(self):
        with tempfile.TemporaryDirectory() as folder:
            ledger = Ledger(Path(folder) / 'db')
            with self.assertRaises(ValueError):
                ledger.append({'id': 'child', 'parent': 'missing'})
            self.assertEqual(ledger.records(), [])
            ledger.close()

    def test_identifiers_and_existing_parent(self):
        with tempfile.TemporaryDirectory() as folder:
            ledger = Ledger(Path(folder) / 'db')
            for record in ({'id': '', 'parent': None}, {'id': 3, 'parent': None},
                           {'id': 'self', 'parent': 'self'}):
                with self.assertRaises(ValueError):
                    ledger.append(record)
            ledger.append({'id': 'a', 'parent': None})
            ledger.append({'id': 'b', 'parent': 'a'})
            with self.assertRaises(sqlite3.IntegrityError):
                ledger.append({'id': 'a', 'parent': None})
            self.assertEqual(len(ledger.records()), 2)
            ledger.close()
