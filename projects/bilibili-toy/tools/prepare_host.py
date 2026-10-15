"""Localize the published host UI and public read-only response snapshots.

No browser cookies or authenticated profile are imported. Unsupported requests
retain their failure instead of returning invented success.
"""
from copy import deepcopy
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "private/site"
HOST = SITE / "host"
TOY_ID = 43482999941120
API = "https://api.bilibili.com"
CDN = "https://s1.hdslb.com/bfs/seed/toy/app/pc-detail/"


def download(url):
    result = subprocess.run(["curl", "--fail", "--compressed", "--silent", "--show-error",
                             "--max-time", "30", url], capture_output=True)
    if result.returncode:
        raise OSError(result.stderr.decode(errors="replace"))
    return result.stdout


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--refresh', action='store_true')
    args = parser.parse_args()
    HOST.mkdir(parents=True, exist_ok=True)
    provenance = []
    def save(name, url):
        target = HOST / name
        target.parent.mkdir(parents=True, exist_ok=True)
        data = download(url) if args.refresh or not target.exists() else target.read_bytes()
        target.write_bytes(data)
        provenance.append({"path": "host/" + name, "source": url,
                           "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)})
        return data
    routes = {
        "/x/toy/detail": f"/x/toy/detail?id={TOY_ID}",
        "/x/toy/related/videos": f"/x/toy/related/videos?id={TOY_ID}",
        "/x/toy/plaza/category": "/x/toy/plaza/category?category=ALL&pn=1&ps=16",
        "/x/toy/author/toys": "/x/toy/author/toys?mid=24602611&pn=1&ps=9",
        "/x/toy/sdk/author/profile": f"/x/toy/sdk/author/profile?id={TOY_ID}",
        "/x/v2/reply": "/x/v2/reply?type=11&oid=412129529&sort=2&pn=1&ps=20"
    }
    responses = {}
    for route, query in routes.items():
        raw = save(route.replace("/", "_") + ".json", API + query)
        payload = json.loads(raw)
        if payload.get("code") != 0:
            raise ValueError(f"Public read unavailable for {route}: {payload.get('code')}")
        responses[route] = payload
    profile = responses["/x/toy/sdk/author/profile"]["data"]["data"]
    responses["/x/web-interface/card"] = {"code": 0, "data": {
        "card": {"name": profile["nickname"], "face": profile["avatar"],
                 "sign": profile["sign"], "fans": profile["follower"]},
        "follower": profile["follower"]}}
    responses["/x/toy/user/info"] = {"code": 0, "data": {"mid": 0, "face": ""}}
    responses["/x/web-interface/nav"] = {"code": 0, "data": {"isLogin": False, "mid": 0}}
    local = deepcopy(responses)
    images = {}
    def localize(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if isinstance(value, str) and value.startswith(("https://i", "http://i")) and ".hdslb.com/" in value:
                    url = value.replace("http://", "https://", 1)
                    if url not in images:
                        suffix = Path(url.split("?")[0]).suffix or ".webp"
                        name = "media-" + hashlib.sha256(url.encode()).hexdigest()[:16] + suffix
                        save(name, url)
                        images[url] = "/content/host/" + name
                    node[key] = images[url]
                else:
                    localize(value)
        elif isinstance(node, list):
            for value in node:
                localize(value)
    localize(local)
    (HOST / "responses.json").write_text(json.dumps(local, ensure_ascii=False, indent=2))
    original = save("pc-detail.original.js", CDN + "index.js").decode()
    needle = "Pd=new ad({middlewares:[new jd]})"
    if original.count(needle) != 1:
        raise ValueError("Published host construction changed; inspect before adapting")
    adapted = original.replace(needle, "Pd=new ad({middlewares:[]})")
    icon_template = "https://${c}/bfs/svg-next/${a}/${o}/v${s}.json"
    if adapted.count(icon_template) != 1:
        raise ValueError('Published host icon loader changed; inspect before adapting')
    adapted = adapted.replace(icon_template, "/content/host/icons/${a}/${o}/v${s}.json")
    for category, name, version in sorted(set(re.findall(r'`(BDC(?:_svg)?)/([a-z_]+)/(\d+)`', original))):
        save(f'icons/{category}/{name}/v{version}.json',
             f'https://i0.hdslb.com/bfs/svg-next/{category}/{name}/v{version}.json')
    (HOST / "pc-detail.js").write_text(adapted)
    save("comments.js", CDN + "comments.js")
    (HOST / "provenance.json").write_text(json.dumps({"resources": provenance,
        "adaptation": "Remove remote WBI signing middleware for read-only loopback snapshots; localize icon configurations; original bytes retained.",
        "derived_sha256": hashlib.sha256(adapted.encode()).hexdigest()}, ensure_ascii=False, indent=2))
    print(json.dumps({"resources": len(provenance), "routes": list(local),
                      "public_author": profile["nickname"], "follower": profile["follower"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
