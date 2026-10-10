"""Measure source/native pixel differences; does not promote diagnostics to acceptance."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageChops, ImageStat

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--native',required=True);p.add_argument('--out',required=True)
a=p.parse_args()
native=Path(a.native);source=Path('projects/duolingo-web/evidence/english-v1')
metadata=json.loads((native/'window.json').read_text())
x,y,w,h=metadata['content_rect_points'];scale=metadata['backing_scale']
assert (w,h)==(1200,732)
observations={}
for number in (1,2,3):
    for row in json.loads((source/f'replay-{number:02}.json').read_text())['observed']:
        if 'feedback' in row: observations[row['index']]=row
rows=[]
for index,row in sorted(observations.items()):
    for stage in ('before','feedback'):
        original=source/row['screenshot_'+stage]
        candidate=native/f'en-zh-q{index}-{stage}.png'
        with Image.open(original) as im: reference=im.convert('RGB')
        with Image.open(candidate) as im:
            pixels=im.size
            assert pixels==(round(metadata['window_points'][0]*scale),round(metadata['window_points'][1]*scale))
            rendered=im.crop(tuple(round(v*scale) for v in (x,y,x+w,y+h))).convert('RGB').resize((int(w),int(h)),Image.Resampling.LANCZOS)
        assert reference.size==rendered.size
        diff=ImageChops.difference(reference,rendered)
        extrema=diff.getextrema();mean=ImageStat.Stat(diff).mean
        # Any RGB difference is reported, with no invented passing tolerance.
        rows.append({'question':index,'stage':stage,'source':original.as_posix(),
                     'native':candidate.name,'source_sha256':hashlib.sha256(original.read_bytes()).hexdigest(),
                     'native_sha256':hashlib.sha256(candidate.read_bytes()).hexdigest(),
                     'mean_absolute_rgb_difference':mean,
                     'status':'identical' if all(hi==0 for lo,hi in extrema) else 'different'})
result={'kind':'same-viewport-pixel-diagnostic','native_trajectory':'first question wrong sugar, then correct, retry coffee',
        'viewport':[w,h],'normalization':'Crop native titlebar using measured content rect, downsample2x with Lanczos; reference pixels unchanged',
        'rows':rows,'candidate_acceptance':'not_proven',
        'limitations':['This is an actual pixel diagnostic, not a substitute for frontend acceptance',
                       'Animation frames and temporal sound not aligned',
                       'Font antialiasing differs across renderers; reported without tolerance or masking',
                       'Current native lacks hearts tutorial, interludes and full completion chain']}
Path(a.out).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'pairs':len(rows),'different':sum(r['status']=='different' for r in rows),'candidate_acceptance':'not_proven'}))
