"""Re-derive all declared major-page captures; original freezes before candidate."""
import argparse
import copy
import json
import re
from pathlib import Path
from .mobile_png_probe import observe
from .visual_probe import ROOT, private_path, relative


def collect(directory, side, protocol, url):
    states, records = {}, {}
    for case in protocol['cases']:
        folder=directory/case['id']
        prep=json.loads((folder/'preparation.json').read_text())
        if prep['id']!=case['id'] or prep['url']!=url:
            raise ValueError('Actual case preparation differs')
        spec=copy.deepcopy(protocol)
        spec['scene_heading']=prep['scene_heading']
        if not re.search(case['heading_pattern'],prep['scene_heading']):
            raise ValueError('Actual case heading differs')
        facts=observe(folder,side,spec,url)
        records[case['id']]=facts['records']
        raw=(folder/(spec[side]['frames'][0]+'.ax.txt')).read_text()
        if 'model' in case:
            match=re.search(r'pop up button 选择 AI 频道, Value: ([^\n]+)',raw)
            if protocol.get('channel_control')=='desktop_links':
                player=raw.split('container AI 模拟回放播放器',1)[-1]
                match=re.search(r'text AI 模拟\s+(.+?)\s+的世界',player)
            if not match:raise ValueError('Actual channel selector unavailable')
            facts['states']['business']['elements']={'model':{'value':match[1].strip()}}
            facts['states']['business']['interactions'].update(player_paused=bool(re.search(r'button\s+播放, Help:',raw)),idle_disabled=bool(re.search(r'checkbox 闲置 60 秒后自动换台, Value: (?:off|0)',raw)))
        for region,state in facts['states'].items():states[case['id']+'.'+region]=state
    return {'states':states,'records':records,'preparation':{'url':url,'protocol_scope':protocol['scope']}}


def freeze(source,protocol):
    requirements=[]
    for name,state in source['states'].items():
        case,region=name.split('.',1)
        evidence=[source['records'][case][0]['ax']]
        if state['interactions']['repeat_pixels_identical']:
            requirements.append({'id':name+'.pixels','state':name,'kind':'image_pixels','reference_image':state['capture']['path'],'pixels':state['capture']['content_rect_points'][2:],'reference_capture':state['capture'],'evidence':[state['capture']['path']]})
        else:
            requirements.append({'id':name+'.pixels','state':name,'kind':'pending','description':'Actual original region differs across repeated frames. Raw source frames retained; dynamic-state preparation/timing remains required.','evidence':[state['capture']['path']]})
        for field,value in state['interactions'].items():
            if field=='repeat_pixels_identical' and not value:continue
            requirements.append({'id':name+'.'+field,'state':name,'kind':'interaction_boolean','field':field,'expected':value,'evidence':evidence})
        for field,value in state.get('elements',{}).items():
            requirements.append({'id':name+'.'+field,'state':name,'kind':'element_value','element':field,'value':value['value'],'evidence':evidence})
        for i,text in enumerate(state['accessible_text']):
            requirements.append({'id':name+'.text.'+str(i),'state':name,'kind':'accessible_text','text':text,'evidence':evidence})
    return {'schema_version':1,'scope':protocol['scope'],'requirements':requirements}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['freeze','observe']);parser.add_argument('--captures',required=True);parser.add_argument('--out',required=True)
    parser.add_argument('--protocol',choices=['major-pages.json','major-pages-desktop.json'],default='major-pages.json')
    parser.add_argument('--candidate-url', help='Actual candidate URL recorded by the shared UI driver')
    args=parser.parse_args();protocol=json.loads((ROOT/args.protocol).read_text());original=(ROOT/'private/original-share-entry-url.txt').read_text().strip()
    from urllib.parse import urlsplit
    url=original if args.mode=='freeze' else args.candidate_url or 'https://s16.xinxiayiyan.com/?'+urlsplit(original).query
    facts=collect(private_path(args.captures),'source' if args.mode=='freeze' else 'candidate',protocol,url);out=private_path(args.out)
    if args.mode=='freeze':
        out.mkdir();contract=freeze(facts,protocol)
        for name,data in [('source',facts),('contract',contract)]:
            (out/(name+'.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2))
        print(json.dumps({'cases':len(protocol['cases']),'requirements':len(contract['requirements']),'pending':sum(x['kind']=='pending' for x in contract['requirements'])}))
    else:
        with out.open('x') as stream:json.dump(facts,stream,ensure_ascii=False,indent=2)
        print(json.dumps({'states':len(facts['states'])}))


if __name__=='__main__':main()
