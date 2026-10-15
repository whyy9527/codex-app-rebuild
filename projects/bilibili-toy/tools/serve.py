"""Loopback-only static server for the local shell and private published baseline."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


class Handler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        route = unquote(urlsplit(path).path)
        base = ROOT / ("private/site" if route.startswith("/content/") else "app")
        relative = route.removeprefix("/content/") if route.startswith("/content/") else route.lstrip("/")
        target = (base / relative).resolve()
        if not target.is_relative_to(base.resolve()):
            return str(ROOT / "private/nonexistent")
        return str(target)

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=4617)
    args = parser.parse_args()
    if not (ROOT / "private/site/index.html").exists():
        parser.error("Run tools/prepare.py first to obtain the private public-resource baseline")
    with ThreadingHTTPServer(("127.0.0.1", args.port), partial(Handler)) as server:
        print(f"http://127.0.0.1:{args.port}/", flush=True)
        server.serve_forever()


if __name__ == "__main__":
    main()
