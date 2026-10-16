"""Strict scrolled-table PNG/content observations from native element anchors."""
import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlsplit
from PIL import Image, ImageChops
from capabilities.rebuild.images import srgb_image
from .visual_probe import ROOT, relative, private_path, ax_facts, inspector_provenance, validate_lossless_image
from .major_pages_probe import validate_source_build, validate_ticker
from .live_cycle_probe import match_details


def observe(directory, side, protocol, url):
    states,records={},{}
    models=[x['name'] for x in json.loads((ROOT/'private/site/data/index.json').read_text())['runs']]
    for case in protocol['cases']:
        folder=directory/case['id'];prep=json.loads((folder/'preparation.json').read_text());spec=protocol[side]
        if (prep['id'],prep['url'],prep['selector'])!=(case['id'],url,case['selector']):raise ValueError('Actual native anchor preparation differs')
        before=(folder/'anchor.before.ax.txt').read_text();menu=(folder/'anchor.menu.ax.txt').read_text();after=(folder/'anchor.after.ax.txt').read_text()
        for ax in (before,after):
            if 'standard window Web Inspector — '+urlsplit(url).hostname not in ax or 'Value: '+case['selector'] not in ax or not any('row (selected' in line and re.search(case['node_pattern'],line) for line in ax.splitlines()):raise ValueError('Actual selected original table anchor differs')
        if not re.search(r'^\s*\d+ Scroll into View,',menu,re.M):raise ValueError('Actual native scroll action unavailable')
        validate_ticker((folder/spec['ticker_evidence']).read_text(),side,protocol,url)
        header=(folder/spec['header_evidence']).read_text()
        if 'standard window Web Inspector — '+urlsplit(url).hostname not in header or not re.search(r'--header-height:[^0-9]*'+str(spec['header_css'])+r'px',header):raise ValueError('Actual header measurement unavailable')
        if side=='source':
            for proof in protocol['source_node_deletions']:
                a,b=[(folder/proof[name]).read_text() for name in ('before','after')]
                if not re.search(proof['node_pattern'],a) or re.search(proof['node_pattern'],b):raise ValueError('Original requested removals not observed')
        crops=[];first_content=None;first_scroll=None;items=[]
        for stem in spec['frames']:
            a,b,image=[folder/(stem+suffix) for suffix in ('.ax.txt','.after.ax.txt','.png')]
            raw,last=a.read_text(),b.read_text()
            metas=[ax_facts(ax,url,spec,protocol,prep['windowUuid']) for ax in (raw,last)]
            if any(x['at_scroll_origin'] for x in metas):raise ValueError('Actual table was not scrolled into view')
            scroll=[re.findall(r'scroll bar \(settable, float\) ([0-9.]+)',ax) for ax in (raw,last)]
            if scroll[0]!=scroll[1] or first_scroll is not None and scroll[0]!=first_scroll:raise ValueError('Actual anchored scroll drifted')
            first_scroll=scroll[0]
            content=[match_details(ax,url,prep['windowUuid'],models) for ax in (raw,last)]
            if content[0]!=content[1] or first_content is not None and content[0]!=first_content:raise ValueError('Actual completed-series contents changed')
            first_content=content[0]
            if side=='source':
                build=json.loads((ROOT.parents[1]/protocol['source_build_config']).read_text())['id']
                for ax in (raw,last):validate_source_build(ax,build)
            provenance=inspector_provenance(folder,stem,url)
            if not re.search(r'text '+str(spec['width_css'])+r'\s+×\s+'+str(protocol['height_css'])+r'$',provenance[0].read_text(),re.M):raise ValueError('Actual body CSS box differs')
            with Image.open(image) as im:
                validate_lossless_image(im,spec['viewport_pixels'][2:]);rgb=srgb_image(im);x,y,w,h=protocol['regions']['business'][side];crops.append(rgb.crop((x,y,x+w,y+h)))
            files=[a,b,image,folder/'preparation.json',folder/'anchor.before.ax.txt',folder/'anchor.menu.ax.txt',folder/'anchor.after.ax.txt',*provenance]
            items.append({'image':relative(image),'ax':relative(a),'after_ax':relative(b),'sha256':{relative(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}})
        stable=all(ImageChops.difference(crops[0],x).getbbox() is None for x in crops[1:])
        states[case['id']]={'capture':{'path':items[0]['image'],'content_rect_points':protocol['regions']['business'][side],'backing_scale':1,'window_points':spec['viewport_pixels'][2:],'state_consistent':True},'elements':first_content['elements'],'interactions':{'anchor_observed':True,'nonzero_stable_scroll':True,'completed_series_content_stable':True,'repeat_pixels_identical':stable}}
        records[case['id']]=items
    return {'states':states,'records':records}


def freeze(facts,protocol):
    requirements=[]
    for name,state in facts['states'].items():
        evidence=[facts['records'][name][0]['ax']];image=state['capture']['path']
        if state['interactions']['repeat_pixels_identical']:
            requirements.append({'id':name+'.pixels','state':name,'kind':'image_pixels','reference_image':image,'pixels':state['capture']['content_rect_points'][2:],'reference_capture':state['capture'],'evidence':[image]})
        else:requirements.append({'id':name+'.pixels','state':name,'kind':'pending','description':'Actual original visible business pixels differ across repeated frames; raw captures retained.','evidence':[image]})
        for field,value in state['interactions'].items():
            if field=='repeat_pixels_identical' and not value:continue
            requirements.append({'id':name+'.'+field,'state':name,'kind':'interaction_boolean','field':field,'expected':value,'evidence':evidence})
        for field,value in state['elements'].items():requirements.append({'id':name+'.'+field,'state':name,'kind':'element_value','element':field,'value':value['value'],'evidence':evidence})
    return {'schema_version':1,'scope':protocol['scope'],'requirements':requirements}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['freeze','observe']);p.add_argument('--captures',required=True);p.add_argument('--out',required=True);p.add_argument('--case',action='append');a=p.parse_args()
    protocol=json.loads((ROOT/'series-tables-desktop.json').read_text())
    if a.case:
        if not set(a.case)<={x['id'] for x in protocol['cases']}:raise ValueError('Unknown declared table case')
        protocol['cases']=[x for x in protocol['cases'] if x['id'] in a.case]
    original=(ROOT/'private/original-share-entry-url.txt').read_text().strip();url=original if a.mode=='freeze' else 'https://s16.xinxiayiyan.com/?'+urlsplit(original).query
    facts=observe(private_path(a.captures),'source' if a.mode=='freeze' else 'candidate',protocol,url);out=private_path(a.out)
    if a.mode=='freeze':
        out.mkdir()
        for name,data in [('source',facts),('contract',freeze(facts,protocol))]:(out/(name+'.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2))
    else:
        with out.open('x') as f:json.dump(facts,f,ensure_ascii=False,indent=2)
    print(json.dumps({'states':len(facts['states'])}))


if __name__=='__main__':main()
