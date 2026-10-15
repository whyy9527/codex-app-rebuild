"""Static preview server; network binding is explicit for isolated deployments."""
import argparse
import json
from functools import partial
from http.server import SimpleHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
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
    with ThreadingHTTPServer((args.bind, args.port), partial(Handler)) as server:
        print(f"http://{args.bind}:{args.port}/", flush=True)
        server.serve_forever()


if __name__ == "__main__":
    main()
