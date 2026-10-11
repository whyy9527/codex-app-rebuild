"""Compile actual source card layouts and original artwork into native presentation data."""
import argparse
import json,hashlib
from pathlib import Path
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out-dir');args=parser.parse_args()
E=Path('projects/duolingo-web/evidence/english-sections-v1');d=json.loads((E/'layouts-before.json').read_text());manifest=[];assets={};bundle=Path('projects/education-swift/Sources/LingoSeed/Resources/Reference');cards=[]
if args.out_dir:bundle=Path(args.out_dir);bundle.mkdir(parents=True,exist_ok=False)
for i,c in enumerate(d['cards']):
    x,y,w,h=c['rect']
    def local(r):return [r[0]-x,r[1]-y,r[2],r[3]]
    def node(cls):return next(n for n in c['nodes'] if cls in (n['className'] or '').split())
    images=[]
    for n in c['nodes']:
        if n['tag']=='IMG' and n['src']:
            url=n['src'];name='en-sections-'+hashlib.sha256(url.encode()).hexdigest()[:16]
            if url not in assets:
                assets[url]=name;manifest.append(dict(name=name,url=url,kind='image',source_file=name+'.svg',render_width=max(1,round(n['rect'][2])),render_height=max(1,round(n['rect'][3]))))
            images.append(dict(resource=name,rect=local(n['rect'])))
    heading=next(n for n in c['nodes'] if n['tag']=='H1');text=node('O93KC') if i<8 else None;bubble=node('_2NZrx') if i<8 else None
    button=next((n for n in c['nodes'] if n['tag']=='BUTTON'),None);paragraph=next((n for n in c['nodes'] if n['tag']=='P'),None)
    cards.append(dict(stage=i+1,heading=heading['text'],height=h,headingRect=local(heading['rect']),background=c['css']['backgroundColor'],images=images,caption=None if text is None else dict(text=text['text'],rect=local(text['rect']),bubbleRect=local(bubble['rect']),bordered=i>0),button=None if button is None else dict(text=button['text'],rect=local(button['rect'])),paragraph=None if paragraph is None else dict(text=paragraph['text'],rect=local(paragraph['rect'])),dailyText=next((dict(text=n['text'],rect=local(n['rect'])) for n in c['nodes'] if n['tag']=='P' and n!=paragraph),None)))
    if i==0:
        svg=next(n for n in c['nodes'] if n['tag']=='svg');name='en-sections-progress-trophy';(bundle/(name+'.svg')).write_text(svg['svg']);manifest.append(dict(name=name,url='https://www.duolingo.com/sections',kind='image',source_file=name+'.svg',render_width=43,render_height=36,source='Actual original inline SVG from layouts-before.json, not downloaded page HTML'));cards[-1]['images'].append(dict(resource=name,rect=local(svg['rect'])))
entry=json.loads(Path('projects/duolingo-web/evidence/english-profile-return-v1/source/section-test-intro.json').read_text())['background_media'][0]
url=entry['backgroundImage'].split('"')[1]
manifest.append(dict(name='en-placement-entry-duo',url=url,kind='image',source_file='en-placement-entry-duo.svg',render_width=270,render_height=270))
(bundle/'sections-presentation.json').write_text(json.dumps({'cards':cards},ensure_ascii=False,indent=2)+'\n');(bundle/'sections-resource-manifest.json' if args.out_dir else Path('projects/duolingo-web/reference-assets-en-zh-sections-v1.json')).write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(len(cards),len(manifest))
