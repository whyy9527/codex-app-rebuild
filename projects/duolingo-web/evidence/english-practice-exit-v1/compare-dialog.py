"""Compare the observed dialog region; surrounding question content is different."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from PIL import Image, ImageChops, ImageStat
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from capture_color import srgb_image

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--native', required=True)
p.add_argument('--out', required=True)
a = p.parse_args()
source = Path(__file__).parent / 'source/positive-then-wrong-confirm.png'
native = Path(a.native)
candidate = native / 'practice-abandon-confirm.png'
meta = json.loads((native / 'window.json').read_text())
x, y, w, h = meta['content_rect_points']
scale = meta['backing_scale']
assert (w, h) == (1200, 732)
# Integer enclosure of the full observed [408,172.75,384,386.5] dialog.
# No interior mask, shifted alignment search, or acceptance tolerance.
region = (408, 172, 792, 560)
with Image.open(source) as im:
    reference = srgb_image(im)
with Image.open(candidate) as im:
    assert im.size == tuple(round(v * scale) for v in meta['window_points'])
    rendered = srgb_image(im).crop(tuple(round(v * scale) for v in (x, y, x+w, y+h)))
    rendered = rendered.resize((int(w), int(h)), Image.Resampling.LANCZOS)
assert reference.size == rendered.size
comparison = ImageChops.difference(reference.crop(region), rendered.crop(region))
result = {
    'kind': 'original-dialog-region-diagnostic',
    'region_css_integer_enclosure': region,
    'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
    'native_sha256': hashlib.sha256(candidate.read_bytes()).hexdigest(),
    'normalization': 'ICC to sRGB, measured native titlebar crop, 2x downsample; integer enclosure of complete dialog; no mask or tolerance',
    'mean_absolute_rgb_difference': ImageStat.Stat(comparison).mean,
    'status': 'identical' if all(hi == 0 for lo, hi in comparison.getextrema()) else 'different',
    'candidate_acceptance': 'not_proven',
    'limitations': ['Both after correct then wrong; underlying questions and practice instance differ. This is a dialog-only comparison, not full-state equivalence.', 'Native/font rendering differences remain reported without tolerance.'],
}
Path(a.out).write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(result))
