"""Compare measured shared page structure; game artwork/content are transformed."""
import argparse
import json
from pathlib import Path


def compare(observed):
    rows=[]
    def check(name,a,b):rows.append({'id':name,'actual':a,'expected':b,'status':'pass'if a==b else'fail'})
    source,target=observed.get('reference',{}),observed.get('candidate',{})
    check('content-viewport',target.get('viewport'),source.get('viewport'))
    a,b=target.get('home',{}),source.get('home',{})
    for name in ['header','hero','tabs','notice','stage']:
        check(name+'-rectangle',a.get(name,[{}])[0].get('rect'),b.get(name,[{}])[0].get('rect'))
    for name in ['hero','stage']:
        check(name+'-background',a.get(name,[{}])[0].get('background'),b.get(name,[{}])[0].get('background'))
    for name in ['hero_title','hero_copy','channels','tab_buttons','notice']:
        aa=a.get(name,[]);bb=b.get(name,[])
        if name=='tab_buttons':bb=[x for x in bb if x['text']!='瑞士轮']
        check(name+'-count',len(aa),len(bb))
        for i,(actual,expected)in enumerate(zip(aa,bb)):
            for key in ['size','weight','lineHeight','spacing','color']:check(f'{name}-{i}-{key}',actual[key],expected[key])
            if name=='channels':check(f'channel-{i}-rectangle',actual['rect'],expected['rect'])
            if name=='tab_buttons':check(f'tab-{i}-control-size',actual['rect'][2:],expected['rect'][2:])
    check('eight-source-portraits',len(b.get('portraits',[])),8)
    check('eight-VALORANT-portraits',len(a.get('portraits',[])),8)
    check('all-portraits-loaded',all(x['loaded']for x in a.get('portraits',[])+b.get('portraits',[])),True)
    check('sidebar-width',a.get('sidebar',[{}])[0].get('rect',[0,0,None])[2],b.get('sidebar',[{}])[0].get('rect',[0,0,None])[2])
    for page in ['compare','teams','pickem','leaderboard','method']:
        actual,expected=target.get(page,{}),source.get(page,{})
        check(page+'-title-count',len(actual.get('title',[])),len(expected.get('title',[])))
        for key in ['size','weight','lineHeight','spacing','color']:
            check(page+'-title-'+key,actual.get('title',[{}])[0].get(key),expected.get('title',[{}])[0].get(key))
        for key in ['rect','background']:
            check(page+'-band-'+key,actual.get('band',[{}])[0].get(key),expected.get('band',[{}])[0].get(key))
    check('driver-errors',[observed.get('error'),*observed.get('errors',[])],[None])
    return {'status':'pass'if all(r['status']=='pass'for r in rows)else'fail','rows':rows,'scope':'Exact shared main-page geometry, display typography, loaded portraits, channel/tab controls and backgrounds at 1370x988. VALORANT text, official character card composition, match contents and missing-model states differ; no claim of pixel identity.'}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--observed',required=True);p.add_argument('--out',required=True);a=p.parse_args();root=Path(__file__).resolve().parents[3];report=compare(json.loads((root/a.observed).read_text()));out=root/a.out;out.mkdir(parents=True,exist_ok=False);(out/'comparison.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':report['status'],'passed':sum(x['status']=='pass'for x in report['rows']),'total':len(report['rows'])}));raise SystemExit(0 if report['status']=='pass'else 1)
