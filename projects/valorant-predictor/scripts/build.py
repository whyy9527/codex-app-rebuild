"""Package only runtime files, excluding development evidence and credentials."""
from pathlib import Path
import shutil
import subprocess

root = Path(__file__).resolve().parents[1]
if (root / 'data/model-fiction.json').exists():
    subprocess.run(['python3', str(root / 'scripts/validate_fiction.py')], check=True)
out = root / 'dist'
if out.is_symlink():raise ValueError('Build destination must not be a symlink')
if out.exists():shutil.rmtree(out)
out.mkdir()
for name in ('index.html', 'style.css', 'app.js', 'engine.mjs', 'fiction.mjs'):
    shutil.copy2(root / name, out / name)
shutil.copytree(root / 'data', out / 'data', dirs_exist_ok=True)
if (root / 'assets').exists():shutil.copytree(root / 'assets', out / 'assets', dirs_exist_ok=True)
shutil.copy2(root / 'ASSET_NOTICES.md', out / 'ASSET_NOTICES.md')
shutil.copy2(root.parents[1] / 'LICENSE', out / 'LICENSE')
print('Built dist/index.html')
