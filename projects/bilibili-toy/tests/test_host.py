"""HTTP-boundary checks for the standalone preview's local public snapshots."""
import importlib.util
import io
import json
from pathlib import Path
import tempfile
from threading import Thread
import unittest
from unittest.mock import patch
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
        project = file.parents[1]
        for name in ('index.html', 'frame-entry.js', 'shell.css'):
            (root / 'app' / name).write_bytes((project / 'app' / name).read_bytes())
        data = root / 'private/site/data'
        run_id = 'gpt-6.1-sol__S16-MAIN'
        (data / run_id).mkdir(parents=True)
        (data / 'index.json').write_text(json.dumps({'runs': [{'id': run_id}]}))
        (data / run_id / 'events.json').write_text(json.dumps([
            {'type': 'game_pred', 'match_id': 'PI-UB1', 'game_no': 1},
            {'type': 'game_result', 'match_id': 'PI-UB1', 'game_no': 1},
            {'type': 'game_result', 'match_id': 'PI-UB1', 'game_no': 2}]))
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

    def test_live_relay_uses_fixed_source_and_does_not_forward_client_credentials(self):
        source = 'https://public.example/results.json'
        (self.module.ROOT / 'private/site/live-source.json').write_text(json.dumps({'url': source}))
        body = b'{"updated_utc":"2026-10-16T00:00:00Z","schema_version":2}'
        for method in ('GET', 'HEAD'):
            with patch.object(self.module, 'urlopen', return_value=io.BytesIO(body)) as upstream:
                request = Request(self.url + '/content/live-results.json?t=123', method=method,
                                  headers={'Cookie': 'private=secret', 'Authorization': 'secret'})
                with urlopen(request, timeout=3) as response:
                    self.assertEqual(response.status, 200)
                    self.assertEqual(int(response.headers['Content-Length']), len(body))
                    self.assertEqual(response.read(), body if method == 'GET' else b'')
                forwarded = upstream.call_args[0][0]
                self.assertEqual(forwarded.full_url, source + '?t=123')
                self.assertNotIn('Cookie', forwarded.headers)
                self.assertNotIn('Authorization', forwarded.headers)
        for query in ('url=https://other.example/', 't=1&t=2', 't=', 't=abc'):
            with patch.object(self.module, 'urlopen') as upstream:
                with self.assertRaises(HTTPError) as caught:
                    urlopen(self.url + '/content/live-results.json?' + query, timeout=3)
                self.assertEqual(caught.exception.code, 400)
                upstream.assert_not_called()

    def test_live_failure_is_visible_without_substituting_stale_results(self):
        (self.module.ROOT / 'private/site/live-source.json').write_text(json.dumps({'url': 'https://public.example/results.json'}))
        for error, expected in ((HTTPError('https://public.example/', 503, 'unavailable', {}, None), 503),
                                (OSError('network unavailable'), 502)):
            with patch.object(self.module, 'urlopen', side_effect=error):
                with self.assertRaises(HTTPError) as caught:
                    urlopen(self.url + '/content/live-results.json', timeout=3)
                self.assertEqual(caught.exception.code, expected)

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

    def test_known_world_and_game_share_entries_serve_the_actual_shell(self):
        prefix = '/share/gpt-6.1-sol__S16-MAIN/'
        for path, route in [('index.html', '#/ai/gpt-6.1-sol__S16-MAIN'),
                            ('PI-UB1/g2.html', '#/ai/gpt-6.1-sol__S16-MAIN/match/PI-UB1?g=2')]:
            with urlopen(self.url + prefix + path + '?p=pickem', timeout=3) as response:
                body = response.read()
                self.assertEqual(response.status, 200)
                self.assertIn(('data-entry-hash="' + route + '"').encode(), body)
                self.assertIn(b'href="/shell.css"', body)
                self.assertIn(b'src="/frame-entry.js"', body)
            with urlopen(Request(self.url + prefix + path, method='HEAD'), timeout=3) as response:
                self.assertEqual(response.status, 200)
                self.assertEqual(int(response.headers['Content-Length']), len(body))
                self.assertEqual(response.read(), b'')

    def test_unknown_share_inputs_do_not_fall_back_to_another_world_or_game(self):
        for path in ('missing/index.html', 'gpt-6.1-sol__S16-MAIN/missing/g1.html',
                     'gpt-6.1-sol__S16-MAIN/PI-UB1/g0.html', 'gpt-6.1-sol__S16-MAIN/PI-UB1/g3.html',
                     'gpt-6.1-sol__S16-MAIN/PI-UB1/g01.html', '../private/secret.txt'):
            with self.assertRaises(HTTPError) as caught:
                urlopen(self.url + '/share/' + path, timeout=3)
            self.assertEqual(caught.exception.code, 404)


if __name__ == '__main__':
    unittest.main()
