"""Fetch exact public source assets, render SVGs in an isolated browser context."""
import argparse
import concurrent.futures
import hashlib
import gzip
import json
from pathlib import Path
import subprocess
from urllib.request import urlopen

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--cli', required=True); p.add_argument('--session', required=True)
p.add_argument('--manifest', default='projects/duolingo-web/reference-assets-en-zh-v1.json')
p.add_argument('--out', default='projects/duolingo-web/evidence/english-v1/resources.json')
a = p.parse_args()
base = Path('projects/duolingo-web')
out = Path('projects/education-swift/Sources/LingoSeed/Resources/Reference')
rows = json.loads(Path(a.manifest).read_text())
def fetch(row):
    path = out/row['source_file']
    if not path.exists():
        with urlopen(row['url'], timeout=30) as response:
            data = response.read()
            encoding = response.headers.get('Content-Encoding', '').lower()
            if encoding == 'gzip' or data.startswith(b'\x1f\x8b'):
                row['wire_sha256'] = hashlib.sha256(data).hexdigest()
                row['content_encoding'] = 'gzip'
                data = gzip.decompress(data)
        if row['kind'] != 'speech': assert b'<svg' in data[:2000]
        path.write_bytes(data)
    row['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
    return row
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
    rows = list(pool.map(fetch, rows))
images = [{'name': r['name'], 'svg': (out/r['source_file']).read_text(),
           'target': str((out/(r['name']+'.png')).resolve())} for r in rows if r['kind'] != 'speech']
# Own tab is used only to reach its browser; asset rendering does not share
# reference cookies, navigation or state.
code = '''async page => {
 const context=await page.context().browser().newContext({viewport:{width:180,height:180},deviceScaleFactor:3});
 try {const render=await context.newPage();
 for(const image of IMAGES){await render.setContent('<html><body style="margin:0;background:transparent"><img style="width:180px;height:180px;object-fit:contain" src="data:image/svg+xml;base64,'+Buffer.from(image.svg).toString('base64')+'"></body></html>');
 await render.locator('img').evaluate(n=>n.decode()); await render.screenshot({path:image.target,omitBackground:true});}
 return {rendered:IMAGES.length,scale:3};
 }finally{await context.close()}
}'''.replace('IMAGES', json.dumps(images))
r = subprocess.run([a.cli,'-s='+a.session,'run-code',code],cwd='artifacts/output/playwright',text=True,capture_output=True,timeout=90)
if r.returncode or '### Result\n' not in r.stdout: raise RuntimeError('Asset rendering failed; inspect browser before retry')
for row in rows:
    if row['kind'] != 'speech':
        row['rendered_file'] = row['name']+'.png'
        row['rendered_sha256'] = hashlib.sha256((out/row['rendered_file']).read_bytes()).hexdigest()
receipt = Path(a.out)
receipt.parent.mkdir(parents=True, exist_ok=True)
receipt.write_text(json.dumps({'resources':rows,'render':'Original SVG, transparent180x180at3x in isolated context; native geometry still to verify'},indent=2)+'\n')
print(json.dumps({'downloaded':len(rows),'rendered':len(images),'hashes_recorded':True}))
