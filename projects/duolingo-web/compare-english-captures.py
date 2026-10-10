"""Measure source/native pixel differences; does not promote diagnostics to acceptance."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageChops, ImageStat

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--native',required=True);p.add_argument('--out',required=True)
p.add_argument('--home-reference',help='Compare this actual home PNG with native home-window.png')
lessons=p.add_mutually_exclusive_group()
lessons.add_argument('--second-lesson', action='store_true', help='Compare actual second-lesson normal and adaptive question captures')
lessons.add_argument('--third-lesson', action='store_true', help='Compare actual third-lesson normal and adaptive question captures')
a=p.parse_args()
native=Path(a.native);source=Path('projects/duolingo-web/evidence/english-v1')
metadata=json.loads((native/'window.json').read_text())
x,y,w,h=metadata['content_rect_points'];scale=metadata['backing_scale']
assert (w,h)==(1200,732)
if a.second_lesson: source=Path('projects/duolingo-web/evidence/english-second-v1')
if a.third_lesson: source=Path('projects/duolingo-web/evidence/english-third-v1')
observations={}
for number in ((1,2) if a.second_lesson or a.third_lesson else (1,2,3)):
    for row in json.loads((source/f'replay-{number:02}.json').read_text())['observed']:
        if 'feedback' in row: observations[row['index']]=row
rows=[]
pairs=[]
if a.home_reference:
    pairs.append((None, 'home', Path(a.home_reference), native/'home-window.png'))
else:
    for index,row in sorted(observations.items()):
        for stage in ('before','feedback'):
            prefix = 'en-zh-l3-q' if a.third_lesson else 'en-zh-l2-q' if a.second_lesson else 'en-zh-q'
            pairs.append((index,stage,source/Path(row['screenshot_'+stage]).name,native/f'{prefix}{index}-{stage}.png'))
    if a.second_lesson:
        for index,stem in [(12,'english-second-adaptive'),(13,'english-second-adaptive-2'),(14,'english-second-adaptive-3')]:
            for stage in ('before','feedback'):
                pairs.append((index,stage,source/('reference-english-second-02-question-12-before.png' if index == 12 and stage == 'before' else 'reference-'+stem+'-'+stage+'.png'),native/f'en-zh-l2-q{index}-{stage}.png'))
    if a.third_lesson:
        for index in (12,13,14):
            for stage in ('before','feedback'):
                pairs.append((index,stage,source/f'reference-english-third-adaptive-{index}-{stage}.png',native/f'en-zh-l3-q{index}-{stage}.png'))
for index,stage,original,candidate in pairs:
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
result={'kind':'same-viewport-pixel-diagnostic','native_trajectory':'home after first lesson, hearts4' if a.home_reference else 'third lesson all accepted, starting hearts4' if a.third_lesson else 'second lesson all accepted, starting hearts4' if a.second_lesson else 'first question wrong sugar, then correct, retry coffee',
        'viewport':[w,h],'normalization':'Crop native titlebar using measured content rect, downsample2x with Lanczos; reference pixels unchanged',
        'rows':rows,'candidate_acceptance':'not_proven',
        'limitations':['This is an actual pixel diagnostic, not a substitute for frontend acceptance',
                       'Animation frames and temporal sound not aligned',
                       'Font antialiasing differs across renderers; reported without tolerance or masking',
                       'Hearts tutorial, source interlude visuals and full completion chain remain incomplete']}
Path(a.out).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'pairs':len(rows),'different':sum(r['status']=='different' for r in rows),'candidate_acceptance':'not_proven'}))
