"""Materialize the public published build as a private offline fidelity baseline.

This is published application code, not an independently authored rewrite.
Downloaded code, datasets, fonts and images stay in ignored private/site.
No cookies, signing URLs, browser profile, or third-party telemetry is copied.
"""
from concurrent.futures import ThreadPoolExecutor
import gzip
import shutil
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
BUILD = json.loads((ROOT / 'source-build.json').read_text())
ACTIVE = ROOT / 'private/site'
SITE = ROOT / 'private/prepared-builds' / BUILD['id']
BASE = BUILD['base_url']
MAIN = BUILD['main']
STYLE = BUILD['style']


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
    first = [MAIN, STYLE, BUILD["runtime"],
             BUILD["vendor_js"], BUILD["vendor_css"],
             "data/index.json", "data/aggregate.json", "data/results.json", "data/predictions.json"]
    with ThreadPoolExecutor(max_workers=8) as pool:
        records = list(pool.map(fetch, first))
    index = json.loads((SITE / "data/index.json").read_text())
    css = (SITE / STYLE).read_text() + (SITE / BUILD["vendor_css"]).read_text()
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
    # A relocated copy must link back to its own host. Keep the published bytes
    # intact and give the derived module its own local path and provenance.
    original = (SITE / MAIN).read_text()
    share_base = BUILD['share_base_identifier'] + '=`https://www.bilibili.com/toy/LkvCZhw12wgT2Pqx/`'
    if original.count(share_base) != 1:
        raise ValueError('Published share base changed; inspect before adapting')
    local_main = original.replace(share_base, BUILD['share_base_identifier'] + '=window.location.origin+`/`')
    author_mount = '(0,' + BUILD['jsx_runtime'] + '.jsx)(' + BUILD['author_component'] + ',{})'
    if local_main.count(author_mount) != 1:
        raise ValueError('Published author-bar mount changed; inspect before adapting')
    local_main = local_main.replace(author_mount, 'null')
    live_constant = BUILD['live_results_identifier'] + '=`' + BUILD['live_results_url'] + '`'
    if local_main.count(live_constant) != 1:
        raise ValueError('Published live-results constant changed; inspect before adapting')
    local_main = local_main.replace(live_constant, BUILD['live_results_identifier'] + '=window.location.origin+`/content/live-results.json`')
    (SITE / 'live-source.json').write_text(json.dumps({'url': BUILD['live_results_url']}))
    (SITE / 'source-build.json').write_text(json.dumps(BUILD, indent=2))
    (SITE / 'assets/local-index.js').write_text(local_main)
    # Local bootstrap deliberately omits host redirects, SDK, SW and analytics.
    (SITE / "index.html").write_text('''<!doctype html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<meta name="theme-color" content="#010026"><title>S16 AI 预测大赛</title>
<link rel="icon" href="site-icon.svg">
<link rel="stylesheet" href="{vendor_css}">
<link rel="stylesheet" href="{style}">
</head><body><div id="root"></div>
<script src="/content-host.js"></script>
<script type="module" src="assets/local-index.js"></script></body></html>'''.replace('{vendor_css}', BUILD['vendor_css']).replace('{style}', STYLE))
    manifest = {"source": BASE, "source_build": BUILD["id"], "scope": "published build reused as private offline baseline",
                "resources": sorted(records, key=lambda r: r["path"]), "unavailable": failures,
                "local_adaptations": [{"path": "assets/local-index.js", "source_path": MAIN,
                    "source_sha256": hashlib.sha256(original.encode()).hexdigest(),
                    "sha256": hashlib.sha256(local_main.encode()).hexdigest(),
                    "change": "Share/report/QR base uses the current origin; omit the topbar author component at the user's explicit request. Live results use a fixed same-origin read-only relay; original polling/scoring preserved. Prediction path and encoding unchanged."}]}
    (SITE / "provenance.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    if failures:
        print(json.dumps({"unavailable": failures}, ensure_ascii=False))
        return 1
    if (ACTIVE / "host").exists() and not (SITE / "host").exists():
        shutil.copytree(ACTIVE / "host", SITE / "host")
    host_result = subprocess.run(["python3", "-m", "projects.bilibili-toy.tools.prepare_host", "--site", str(SITE)],
                                 cwd=ROOT.parents[1], capture_output=True, text=True)
    if host_result.returncode:
        raise RuntimeError(host_result.stderr or host_result.stdout)
    retired = None
    if ACTIVE.exists():
        retired = ROOT / 'private/archived-sites' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        retired.parent.mkdir(parents=True, exist_ok=True)
        ACTIVE.rename(retired)
    try:
        SITE.rename(ACTIVE)
    except BaseException:
        if retired is not None: retired.rename(ACTIVE)
        raise
    (ROOT / 'private/resources.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    print(json.dumps({"source_build": BUILD['id'], "resources": len(records), "bytes": sum(r["bytes"] for r in records),
                      "unavailable": failures, "host": json.loads(host_result.stdout)}, ensure_ascii=False, indent=2))
    return bool(failures)


if __name__ == "__main__":
    raise SystemExit(main())
