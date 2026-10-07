import tempfile
import unittest
from pathlib import Path
from runtime.components import Context
from runtime.runner import evaluate


class FinalReview(unittest.TestCase):
    def test_dependent_start_failure_rolls_back_new_provider(self):
        context, cleaned = Context(), []
        def broken(scope):
            raise RuntimeError('dependent startup failed')
        def provider(scope):
            scope.on_close(lambda: cleaned.append('provider'))
            return 'resource'
        context.mount('dependent', broken, requires=('provider',))
        with self.assertRaises(RuntimeError):
            context.mount('provider', provider)
        self.assertEqual(context.active(), [])
        self.assertEqual(cleaned, ['provider'])
        context.close()

    def test_nonexistent_workspace_is_not_created(self):
        with tempfile.TemporaryDirectory() as folder:
            missing = Path(folder) / 'missing'
            with self.assertRaises(ValueError):
                evaluate(missing, ['python3', '-c', 'pass'])
            self.assertFalse(missing.exists())

    def test_portable_projection_keeps_raw_records_unchanged(self):
        from capabilities.exploration.ledger import Ledger, digest, verify_records
        from capabilities.exploration.export import portable_records
        with tempfile.TemporaryDirectory() as folder:
            ledger = Ledger(Path(folder) / 'db')
            ledger.append({'id': 'a', 'parent': None, 'message': '/opt/vendor/python/lib/module.py'})
            raw = ledger.records()
            projection = portable_records(raw)
            self.assertEqual(projection[0]['message'], '<local-path>')
            self.assertEqual(projection[0]['export_provenance']['raw_record_digest'], digest(raw[0]))
            self.assertEqual(ledger.records(), raw)
            self.assertEqual(verify_records(projection)['records'], 1)
            ledger.close()
