"""Exact navigation typography comparison, independent of the browser driver."""
import argparse
import json
from pathlib import Path


def compare(observed):
    rows=[]
    reference=observed.get('reference',[]);candidate=observed.get('candidate',[])
    def check(name,a,b):rows.append({'id':name,'status':'unavailable'if a is None or b is None else'pass'if a==b else'fail','actual':a,'expected':b})
    check('six-navigation-labels',len(candidate),len(reference))
    for i,(a,b)in enumerate(zip(candidate,reference)):
        for key in ['text','size','weight','lineHeight','glyph']:check(f'nav-{i+1}-{key}',a.get(key),b.get(key))
        check(f'nav-{i+1}-control-size',a.get('rect',[])[2:],b.get('rect',[])[2:])
        fonts=observed.get('candidate_rendered_fonts',[]);ref_fonts=observed.get('reference_rendered_fonts',[])
        check(f'nav-{i+1}-actual-rendered-fonts',fonts[i]if i<len(fonts)else None,ref_fonts[i]if i<len(ref_fonts)else None)
    return {'status':'pass'if len(reference)==6 and all(r['status']=='pass'for r in rows)else'fail','rows':rows,'scope':'Six primary navigation items only. No claim about full-page visual equality.'}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--observed',required=True);p.add_argument('--out',required=True);a=p.parse_args();repo=Path(__file__).resolve().parents[3];report=compare(json.loads((repo/a.observed).read_text()));out=repo/a.out;out.mkdir(parents=True,exist_ok=False);(out/'comparison.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':report['status'],'passed':sum(r['status']=='pass'for r in report['rows']),'total':len(report['rows'])}));raise SystemExit(0 if report['status']=='pass'else 1)
