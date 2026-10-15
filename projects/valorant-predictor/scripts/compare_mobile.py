"""Source-grounded mobile layout/behavior checks, with explicit game scope."""
import argparse
import json
from pathlib import Path


def compare(f,r):
    rows=[]
    def check(name,a,b,source='observed'):
        rows.append({'id':name,'knowledge_source':source,'status':'unavailable'if a is None or b is None else'pass'if a==b else'fail','actual':a,'expected':b})
    check('matching-content-viewport',f.get('viewport'),r.get('viewport'))
    width=r.get('viewport',{}).get('width')
    for name in ['page_width','prediction_width','review_width']:check(name,f.get(name),r.get(name))
    check('six-navigation-labels',f.get('navigation'),r.get('navigation'))
    check('eight-model-options',f.get('model_options'),r.get('model_options'))
    a=f.get('metrics',{});b=r.get('metrics',{})
    for name in ['portraits','model_buttons']:
        check(name+'-hidden',sum(x['visible']for x in a.get(name,[])),sum(x['visible']for x in b.get(name,[])))
    for i,(actual,expected)in enumerate(zip(a.get('navigation',[]),b.get('navigation',[]))):
        for key in ['size','weight','lineHeight','padding']:check(f'nav-{i+1}-{key}',actual[key],expected[key])
        check(f'nav-{i+1}-control-size',actual['rect'][2:],expected['rect'][2:])
    for name,keys in [('title',['size','weight','lineHeight']),('model_selector',['size','weight','lineHeight','padding']),('nav_grid',['display','columns']),('tabs',['display','columns'])]:
        actual=a.get(name,[{}])[0];expected=b.get(name,[{}])[0]
        for key in keys:check(name+'-'+key,actual.get(key),expected.get(key))
    expected_tabs=[x['text']for x in b.get('tab_buttons',[])if x['text']!='瑞士轮']
    check('two-match-channel-tabs',[x['text']for x in a.get('tab_buttons',[])],expected_tabs,'decision:user-finals-only-excludes-Swiss')
    source_tabs={x['text']:x for x in b.get('tab_buttons',[])}
    for actual in a.get('tab_buttons',[]):
        expected=source_tabs.get(actual['text'],{})
        for key in ['size','weight','lineHeight','padding']:check(actual['text']+'-'+key,actual.get(key),expected.get(key))
        check(actual['text']+'-control-size',actual['rect'][2:],expected.get('rect',[])[2:])
    for name in ['side_schedule','stage']:
        actual=a.get(name,[{}])[0];expected=b.get(name,[{}])[0]
        check(name+'-visible',actual.get('visible'),expected.get('visible'))
        check(name+'-content-width',actual.get('rect',[0,0,None])[2],expected.get('rect',[0,0,None])[2])
    check('model-selector-consumed',f.get('selected_model'),r.get('selected_model'))
    check('selected-model-on-stage','GPT-6.1 sol'in f.get('selected_stage',''),True)
    check('date-jump-on-stage','18'in f.get('day_stage',''),True,'decision:user-two-dates')
    check('schedule-is-interactive',all(x['tag']=='BUTTON'for x in f.get('schedule_controls',[])),all(x['tag']=='BUTTON'for x in r.get('schedule_controls',[])))
    check('schedule-click-executed',bool(f.get('schedule_click_stage')),bool(r.get('schedule_click_stage')))
    check('completed-prediction-result',bool(f.get('prediction_result')),bool(r.get('prediction_result')))
    check('review-has-selected-map',bool(f.get('selected_review_map')),bool(r.get('selected_review_map')))
    check('review-curve-present',f.get('curve_count'),r.get('curve_count'))
    v=f.get('wide_mobile_width');check('390px-mobile-no-overflow',v['scroll']<=v['viewport']if v else None,True)
    check('390px-mobile-selector',f.get('wide_model_selector'),True)
    return {'status':'pass'if all(x['status']=='pass'for x in rows)else'fail','rows':rows,'scope':'Matching 320x832 content viewport; additional candidate 390px usability. Original social controls and game content differ; no claim of pixel identity.'}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--observed',required=True);p.add_argument('--reference',required=True);p.add_argument('--out',required=True);a=p.parse_args();repo=Path(__file__).resolve().parents[3];o=json.loads((repo/a.observed).read_text());r=json.loads((repo/a.reference).read_text());report=compare(o['facts'],r['facts']);report['driver_errors']=[o.get('error'),r.get('error'),*o.get('errors',[]),*r.get('errors',[])];out=repo/a.out;out.mkdir(parents=True,exist_ok=False);(out/'comparison.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':report['status'],'passed':sum(x['status']=='pass'for x in report['rows']),'total':len(report['rows'])}));raise SystemExit(0 if report['status']=='pass'and not any(report['driver_errors'])else 1)
