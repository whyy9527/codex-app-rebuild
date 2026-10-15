import importlib
import unittest

mobile = importlib.import_module('projects.bilibili-toy.tools.freeze_mobile')


class MobileEvidenceTests(unittest.TestCase):
    def test_native_endpoint_keeps_port_query_and_scheme(self):
        field = '1 text field Description: smart search field in a private window, Value: 127.0.0.1:4618/?a=1&b=2'
        self.assertEqual(mobile.observed_endpoint(field, 'http'),
                         ('http', '127.0.0.1:4618', '/', 'a=1&b=2'))
        self.assertEqual(mobile.observed_endpoint(field.replace('127.0.0.1:', 'https://127.0.0.1:'), 'http')[0], 'https')
        with self.assertRaisesRegex(ValueError, 'unavailable'):
            mobile.observed_endpoint('1 text Wrong address', 'http')

    def test_evidence_cannot_escape_private(self):
        with self.assertRaisesRegex(ValueError, 'private'):
            mobile.private_path('projects/bilibili-toy/private/../README.md')


if __name__ == '__main__':
    unittest.main()
