"""Package only runtime files, excluding development evidence and credentials."""
from pathlib import Path
import shutil
import subprocess
import hashlib,json

root = Path(__file__).resolve().parents[1]
if (root / 'data/model-fiction.json').exists():
    subprocess.run(['python3', str(root / 'scripts/validate_fiction.py')], check=True)
subprocess.run(['python3', str(root / 'scripts/validate_tactical.py')], check=True)
subprocess.run(['python3', str(root / 'scripts/validate_veto.py')], check=True)
subprocess.run(['python3', str(root / 'scripts/validate_evidence.py')], check=True)
subprocess.run(['python3', str(root / 'scripts/validate_causal.py')], check=True)
out = root / 'dist'
if out.is_symlink():raise ValueError('Build destination must not be a symlink')
if out.exists():shutil.rmtree(out)
out.mkdir()
for name in ('index.html', 'style.css', 'app.js', 'engine.mjs', 'fiction.mjs', 'tactical-replay.mjs', 'tactical.css', 'veto.mjs', 'veto.css', 'forecast-v2.mjs', 'forecast-v2.css', 'prediction-player.mjs', 'prediction-player.css', 'causal-player.mjs', 'current-data.mjs'):
    shutil.copy2(root / name, out / name)
shutil.copytree(root / 'data', out / 'data', dirs_exist_ok=True)
# Producers publish validated payloads atomically, but the directory copy can span updates.
# Freeze the manifest and exactly the bytes it names as one coherent build snapshot.
causal_index=root/'data/causal/models.json'
if causal_index.exists():
    for attempt in range(10):
        index_bytes=causal_index.read_bytes();index=json.loads(index_bytes);snapshot={}
        for row in index['models'].values():
            if not row.get('file'):continue
            data=(root/row['file']).read_bytes()
            if hashlib.sha256(data).hexdigest()!=row['sha256']:break
            snapshot[row['file']]=data
        else:
            for name,data in snapshot.items():(out/name).write_bytes(data)
            (out/'data/causal/models.json').write_bytes(index_bytes)
            break
    else:raise ValueError('No coherent causal snapshot available; keep current build unpublished')
subprocess.run(['node', str(root / 'scripts/build_current.mjs'), str(out)], check=True)
if (root / 'assets').exists():
    shutil.copytree(root / 'assets', out / 'assets', dirs_exist_ok=True)
    # Current CSS uses Anton and JetBrains Mono; keep legacy sources and licenses in the repository.
    for name in ('OPPO-Sans-4.0.ttf', 'MiSans-Regular.woff2'):
        (out / 'assets/fonts' / name).unlink(missing_ok=True)
shutil.copy2(root / 'ASSET_NOTICES.md', out / 'ASSET_NOTICES.md')
shutil.copy2(root.parents[1] / 'LICENSE', out / 'LICENSE')
print('Built dist/index.html')
