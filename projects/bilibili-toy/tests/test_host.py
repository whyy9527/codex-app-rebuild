"""HTTP-boundary checks for the standalone preview's local public snapshots."""
import importlib.util
import json
from pathlib import Path
import tempfile
from threading import Thread
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen


class HostBoundary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        file = Path(__file__).resolve().parents[1] / 'tools/serve.py'
        spec = importlib.util.spec_from_file_location('bilibili_preview_host', file)
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)
        cls.temp = tempfile.TemporaryDirectory()
        root = Path(cls.temp.name)
        (root / 'app').mkdir()
        (root / 'release.json').write_text('{"release":"test-release","channel":"preview"}')
        (root / 'private/secret.txt').parent.mkdir(parents=True, exist_ok=True)
        (root / 'private/secret.txt').write_text('not-public')
        folder = root / 'private/site/host'
        folder.mkdir(parents=True)
        cls.snapshot = {'/x/toy/detail': {'code': 0, 'data': {'title': 'fixed reference'}},
                        '/x/toy/plaza/category': {'code': 0, 'data': {'total': 10, 'list': list(range(10))}}}
        (folder / 'responses.json').write_text(json.dumps(cls.snapshot))
        cls.module.ROOT = root
        cls.server = cls.module.ThreadingHTTPServer(('127.0.0.1', 0), cls.module.Handler)
        cls.thread = Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.thread.join()
        cls.server.server_close()
        cls.temp.cleanup()

    def get(self, path):
        with urlopen(self.url + path, timeout=3) as response:
            return json.load(response)

    def test_requested_id_is_never_substituted(self):
        self.assertEqual(self.get('/host-api/x/toy/detail?id=43482999941120')['data']['title'], 'fixed reference')
        for query in ('id=1', 'id=43482999941120&id=1', ''):
            with self.assertRaises(HTTPError) as caught:
                self.get('/host-api/x/toy/detail?' + query)
            self.assertEqual(caught.exception.code, 404)
            self.assertEqual(json.load(caught.exception)['code'], -404)

    def test_size_is_honored_and_unrecorded_pages_fail(self):
        data = self.get('/host-api/x/toy/plaza/category?category=ALL&pn=1&ps=3')['data']
        self.assertEqual(data, {'total': 10, 'list': [0, 1, 2]})
        for query in ('category=OTHER&pn=1&ps=3', 'category=ALL&pn=2&ps=3', 'category=ALL&pn=1&ps=999'):
            with self.assertRaises(HTTPError) as caught:
                self.get('/host-api/x/toy/plaza/category?' + query)
            self.assertEqual(caught.exception.code, 404)

    def test_platform_write_is_rejected_without_mutating_snapshot(self):
        request = Request(self.url + '/host-api/x/toy/like', data=b'toy_id=43482999941120&action=like', method='POST')
        with self.assertRaises(HTTPError) as caught:
            urlopen(request, timeout=3)
        self.assertEqual(caught.exception.code, 403)
        self.assertEqual(json.load(caught.exception)['code'], -403)
        self.assertEqual(self.get('/host-api/x/toy/detail?id=43482999941120'), self.snapshot['/x/toy/detail'])

    def test_release_is_public_but_private_files_and_directory_lists_are_not(self):
        self.assertEqual(self.get('/release.json')['release'], 'test-release')
        for path in ('/content/host/', '/content/%2e%2e/secret.txt', '/%2e%2e/private/secret.txt'):
            with self.assertRaises(HTTPError) as caught:
                self.get(path)
            self.assertEqual(caught.exception.code, 404)


if __name__ == '__main__':
    unittest.main()
