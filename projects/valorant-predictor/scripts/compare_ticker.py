"""Common ticker workflow plus candidate-only native pointer coverage."""
import argparse
import json
from pathlib import Path


def compare(reference,candidate):
    r,f=reference['facts'],candidate['facts'];rows=[]
    def check(name,a,b):rows.append({'id':name,'actual':a,'expected':b,'status':'pass'if a==b else'fail'})
    for key in ['closed_label','closed_fixed','paused_label','paused_motion','running_motion','closed_again','reduced_motion_label']:check(key,f.get(key),r.get(key))
    check('source-has-simulated-links',bool(r.get('primary_links')),True)
    check('four-models-two-matches',len(f.get('primary_links',[])),8)
    check('candidate-default-open',f.get('default_open'),True)
    check('no-pending-model-ticker',all(any(name in x for name in ['GPT-6.1 sol','DeepSeek V4.1 Flash','MiMo V2.6 Pro','豆包']) for x in f.get('primary_links',[])),True)
    check('source-hidden-links-unfocusable',set(r.get('hidden_duplicate_tabindices',[])),{-1})
    check('candidate-hidden-links-unfocusable',set(f.get('hidden_duplicate_tabindices',[])),{-1})
    check('candidate-native-pointer-open',f.get('initial_activation'),'pointer')
    check('candidate-hover-pauses',f.get('hover_motion'),'paused')
    check('source-review-opened','AI 模拟比赛'in r.get('review_text',''),True)
    check('candidate-review-opened','AI 模拟 · 非真实赛果'in f.get('review_text',''),True)
    for name,data in [('source',r),('candidate',f)]:
        w=data.get('mobile_width',{});check(name+'-mobile-no-overflow',w.get('scroll')==w.get('viewport'),True)
    check('driver-errors',[reference.get('error'),candidate.get('error'),*reference.get('errors',[]),*candidate.get('errors',[])],[None,None])
    for row in rows:
        for key in ['actual','expected']:
            if isinstance(row[key],set):row[key]=sorted(row[key])
    return {'status':'pass'if all(x['status']=='pass'for x in rows)else'fail','rows':rows,'limitations':['Source sticky OOPIF pointer activation was not observed despite matching DOM hit tests. Keyboard defines the observed reference workflow. Source hover pause was not established; candidate native pointer/hover are verified independently.','Original aggregates full-tournament upsets; candidate aggregates the four actual model channels and only the last two series.']}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--reference',required=True);p.add_argument('--observed',required=True);p.add_argument('--out',required=True);a=p.parse_args();root=Path(__file__).resolve().parents[3];report=compare(json.loads((root/a.reference).read_text()),json.loads((root/a.observed).read_text()));out=root/a.out;out.mkdir(parents=True,exist_ok=False);(out/'comparison.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':report['status'],'passed':sum(x['status']=='pass'for x in report['rows']),'total':len(report['rows'])}));raise SystemExit(0 if report['status']=='pass'else 1)
