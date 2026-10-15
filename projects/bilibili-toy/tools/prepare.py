"""Materialize the public published build as a private offline fidelity baseline.

This is published application code, not an independently authored rewrite.
Downloaded code, datasets, fonts and images stay in ignored private/site.
No cookies, signing URLs, browser profile, or third-party telemetry is copied.
"""
from concurrent.futures import ThreadPoolExecutor
import gzip
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "private/site"
BASE = "https://www.bilibilitoy.com/toy/LkvCZhw12wgT2Pqx/43482999941120-v26695/"
MAIN = "assets/index-c1ZjPqQS.js"
STYLE = "assets/index-2AhI0v6_.css"


def fetch(name, source=None):
    if name.startswith("/") or ".." in Path(name).parts or ":" in name:
        raise ValueError(f"Unsafe public resource path: {name}")
    target = SITE / name
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        data = target.read_bytes()
    else:
        time.sleep(.15)
        result = subprocess.run(["curl", "--fail", "--compressed", "--silent", "--show-error",
                                 "--max-time", "45", source or BASE + name], capture_output=True)
        if result.returncode:
            raise OSError(result.stderr.decode(errors="replace").strip())
        data = result.stdout
        if data[:2] == b"\x1f\x8b":
            data = gzip.decompress(data)
        target.write_bytes(data)
    return {"path": name, "source": source or BASE + name, "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest()}


def main():
    first = [MAIN, STYLE, "assets/rolldown-runtime-CbXtAM7H.js",
             "assets/vendor-DqwCY14m.js", "assets/vendor-BsAqU1mh.css",
             "data/index.json", "data/aggregate.json", "data/results.json"]
    with ThreadPoolExecutor(max_workers=8) as pool:
        records = list(pool.map(fetch, first))
    index = json.loads((SITE / "data/index.json").read_text())
    css = (SITE / STYLE).read_text() + (SITE / "assets/vendor-BsAqU1mh.css").read_text()
    names = {"zhangdamiao.png", "site-icon.svg", "licenses/ASSET_LICENSES.md"}
    for match in re.findall(r"url\(([^)]+)\)", css):
        name = match.strip('\"\' ')
        if not name.startswith("data:"):
            names.add("assets/" + name.removeprefix("./"))
    for run in index["runs"]:
        names.update(f"data/{run['id']}/{kind}.json" for kind in ("run", "events"))
    for key in ("claude", "gpt", "gemini", "deepseek", "qwen", "glm", "doubao", "mimo"):
        names.update(f"avatars/{key}_{kind}.webp" for kind in ("head", "half"))
        names.add(f"logos/models/{'opus' if key == 'claude' else key}.svg")
    for team in index["teams"]:
        names.add(f"logos/teams/{team}.png")
    for region in {team["region"] for team in index["teams"].values()}:
        names.add(f"logos/leagues/{region}.png")
    names.update(f"champions/{champ}.png" for champ in set(index["champions_id"].values()))
    failures = []
    def attempt(name):
        try:
            return fetch(name)
        except OSError as error:
            failures.append({"path": name, "error": str(error)})
            return None
    with ThreadPoolExecutor(max_workers=2) as pool:
        records += [r for r in pool.map(attempt, sorted(names)) if r is not None]
    records.append(fetch("host-cover.png", "https://i0.hdslb.com/bfs/static/toy/app/LkvCZhw12wgT2Pqx/icon_25819_upload"))
    # Local bootstrap deliberately omits host redirects, SDK, SW and analytics.
    (SITE / "index.html").write_text('''<!doctype html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<meta name="theme-color" content="#010026"><title>S16 AI 预测大赛</title>
<link rel="icon" href="site-icon.svg">
<link rel="stylesheet" href="assets/vendor-BsAqU1mh.css">
<link rel="stylesheet" href="assets/index-2AhI0v6_.css">
</head><body><div id="root"></div>
<script type="module" src="assets/index-c1ZjPqQS.js"></script></body></html>''')
    manifest = {"source": BASE, "scope": "published build reused as private offline baseline",
                "resources": sorted(records, key=lambda r: r["path"]), "unavailable": failures}
    (ROOT / "private/resources.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    print(json.dumps({"resources": len(records), "bytes": sum(r["bytes"] for r in records),
                      "unavailable": failures}, ensure_ascii=False, indent=2))
    return bool(failures)


if __name__ == "__main__":
    raise SystemExit(main())
