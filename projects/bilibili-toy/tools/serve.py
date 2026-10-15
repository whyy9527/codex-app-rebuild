"""Static preview server; network binding is explicit for isolated deployments."""
import argparse
import html
import json
import re
from functools import partial, lru_cache
from http.server import SimpleHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import time

ROOT = Path(__file__).resolve().parents[1]


@lru_cache(maxsize=1)
def share_routes(root):
    """Valid standalone share entries from the same published model/game data."""
    folder = root / 'private/site/data'
    index = folder / 'index.json'
    if not index.exists():
        return {}
    routes = {}
    for run in json.loads(index.read_text())['runs']:
        run_id = run['id']
        if not isinstance(run_id, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', run_id):
            raise ValueError('Invalid published run ID')
        base = '#/ai/' + run_id
        routes['/share/' + run_id + '/index.html'] = base
        for event in json.loads((folder / run_id / 'events.json').read_text()):
            if event.get('type') != 'game_result':
                continue
            match, game = event['match_id'], event['game_no']
            if not isinstance(match, str) or not re.fullmatch(r'[A-Za-z0-9_-]+', match) or type(game) is not int or game < 1:
                raise ValueError('Invalid published game identity')
            route = '/share/' + run_id + '/' + match + '/g' + str(game) + '.html'
            routes[route] = base + '/match/' + match + '?g=' + str(game)
    return routes


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


class Handler(SimpleHTTPRequestHandler):
    def serve_live_results(self, head_only=False):
        parsed = urlsplit(self.path)
        if parsed.path != '/content/live-results.json':
            return False
        params = parse_qs(parsed.query, keep_blank_values=True)
        minute = params.get('t', [str(int(time.time() // 60))])
        if set(params) - {'t'} or len(minute) != 1 or not re.fullmatch(r'[0-9]{1,12}', minute[0]):
            self.send_error(400)
            return True
        try:
            source = json.loads((ROOT / 'private/site/live-source.json').read_text())['url']
            upstream = urlsplit(source)
            if upstream.scheme != 'https' or not upstream.hostname or upstream.username or upstream.password or upstream.query or upstream.fragment:
                raise ValueError('Invalid fixed live-results source')
            request = Request(source + '?t=' + minute[0], headers={'Accept': 'application/json'})
            with urlopen(request, timeout=15) as response:
                data = response.read()
            json.loads(data.decode('utf-8'))
        except HTTPError as error:
            self.send_error(error.code)
            return True
        except (OSError, URLError, ValueError, KeyError):
            self.send_error(502)
            return True
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        if not head_only:
            self.wfile.write(data)
        return True

    def serve_share(self, head_only=False):
        route = urlsplit(self.path).path
        if not route.startswith('/share/'):
            return False
        entry = share_routes(ROOT).get(route)
        if entry is None:
            self.send_error(404)
            return True
        template = (ROOT / 'app/index.html').read_text()
        marker = 'data-entry-hash=""'
        if template.count(marker) != 1:
            raise ValueError('Share-entry iframe marker changed')
        data = template.replace(marker, 'data-entry-hash="' + html.escape(entry, quote=True) + '"').encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        if not head_only:
            self.wfile.write(data)
        return True

    def do_HEAD(self):
        if not self.serve_live_results(head_only=True) and not self.serve_share(head_only=True):
            super().do_HEAD()

    def do_GET(self):
        if self.serve_live_results():
            return
        if self.serve_share():
            return
        route = urlsplit(self.path).path
        if route == '/release.json':
            release = ROOT / 'release.json'
            data = release.read_bytes() if release.exists() else b'{"channel":"local"}'
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        if route.startswith('/host-api/'):
            name = route[len('/host-api'):]
            file = ROOT / 'private/site/host/responses.json'
            responses = json.loads(file.read_text()) if file.exists() else {}
            params = parse_qs(urlsplit(self.path).query)
            required = {
                '/x/toy/detail': ('id', '43482999941120'),
                '/x/toy/related/videos': ('id', '43482999941120'),
                '/x/toy/sdk/author/profile': ('id', '43482999941120'),
                '/x/toy/author/toys': ('mid', '24602611'),
                '/x/web-interface/card': ('mid', '24602611'),
                '/x/v2/reply': ('oid', '412129529')
            }
            valid = name in responses
            if name in required:
                key, value = required[name]
                valid = valid and params.get(key) == [value]
            if name == '/x/toy/plaza/category':
                valid = valid and params.get('category') == ['ALL']
            if name == '/x/v2/reply':
                valid = valid and params.get('type') == ['11'] and params.get('sort', ['2']) == ['2']
                valid = valid and params.get('pn', ['1']) == ['1'] and params.get('ps', ['20']) == ['20']
            if name in ('/x/toy/plaza/category', '/x/toy/author/toys'):
                valid = valid and params.get('pn', ['1']) == ['1']
                try:
                    valid = valid and len(params.get('ps', ['3'])) == 1
                    size = int(params.get('ps', ['3'])[0])
                    valid = valid and 1 <= size <= 16
                except ValueError:
                    valid = False
            payload = responses[name] if valid else {"code": -404, "message": "Requested input has no local snapshot"}
            if valid and name in ('/x/toy/plaza/category', '/x/toy/author/toys'):
                payload = {**payload, 'data': {**payload['data'], 'list': payload['data']['list'][:size]}}
            data = json.dumps(payload, ensure_ascii=False).encode()
            self.send_response(200 if valid else 404)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        super().do_GET()

    def list_directory(self, path):
        self.send_error(404)
        return None

    def do_POST(self):
        data = b'{"code":-403,"message":"Authenticated platform writes unavailable in local preview"}'
        self.send_response(403)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def translate_path(self, path):
        route = unquote(urlsplit(path).path)
        base = ROOT / ("private/site" if route.startswith("/content/") else "app")
        relative = route[len('/content/'):] if route.startswith("/content/") else route.lstrip("/")
        target = (base / relative).resolve()
        if target != base.resolve() and base.resolve() not in target.parents:
            return str(ROOT / "private/nonexistent")
        return str(target)

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=4617)
    parser.add_argument("--bind", default="127.0.0.1", help="Explicit container binding; default stays loopback")
    args = parser.parse_args()
    required = ['index.html', 'assets/local-index.js', 'host/pc-detail.js', 'host/responses.json']
    missing = [name for name in required if not (ROOT / 'private/site' / name).exists()]
    if missing:
        parser.error("Run the project build first; missing public-resource baseline: " + ', '.join(missing))
    # Warm once before accepting concurrent requests, keeping first-load parsing
    # out of request threads on the memory-limited preview service.
    share_routes(ROOT)
    with ThreadingHTTPServer((args.bind, args.port), partial(Handler)) as server:
        print(f"http://{args.bind}:{args.port}/", flush=True)
        server.serve_forever()


if __name__ == "__main__":
    main()
