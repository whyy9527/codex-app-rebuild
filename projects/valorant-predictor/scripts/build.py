"""Package only runtime files, excluding development evidence and credentials."""
from pathlib import Path
import shutil

root = Path(__file__).resolve().parents[1]
out = root / 'dist'
if out.is_symlink():raise ValueError('Build destination must not be a symlink')
if out.exists():shutil.rmtree(out)
out.mkdir()
for name in ('index.html', 'style.css', 'app.js', 'engine.mjs'):
    shutil.copy2(root / name, out / name)
shutil.copytree(root / 'data', out / 'data', dirs_exist_ok=True)
if (root / 'assets').exists():shutil.copytree(root / 'assets', out / 'assets', dirs_exist_ok=True)
print('Built dist/index.html')
