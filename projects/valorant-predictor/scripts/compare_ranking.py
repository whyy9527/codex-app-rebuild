"""Independent acceptance of ranking controls and actual selected-model odds."""
import argparse
import json
import math
from pathlib import Path


def compare(f,root,reference=None):
    rows=[]
    def check(name,actual,expected):rows.append({'id':name,'status':'pass' if actual==expected else 'fail','actual':actual,'expected':expected})
    def moved(order,from_index,to_index):
        result=list(order);item=result.pop(from_index);result.insert(to_index,item);return result
    if reference is not None:
        r=reference['facts']
        check('source-ranking-arrow-button',r['keyboard_button'],moved(r['initial'],17,18))
        check('source-ranking-two-clicks',r['two_clicks'],moved(r['keyboard_button'],0,2))
        check('source-ranking-pointer-drag',r['pointer_drag'],moved(r['two_clicks'],0,1))
        check('source-ranking-save',r['saved'],r['pointer_drag'])
        check('source-ranking-reload',r['restored'],r['saved'])
    def p_map(model,a,b):
        pair=next(p for p in model['pairs'] if set(p['teams'])=={a,b});return pair['p_first'] if pair['teams'][0]==a else 1-pair['p_first']
    def percentage(p):return f'{100*p**3*(10-15*p+6*p*p):.1f}%'
    a,b=f['initial_matchup'];gpt=json.loads((root/'data/gpt-6.1-sol-forecast.json').read_text());deepseek=json.loads((root/'data/deepseek-forecast.json').read_text())
    check('gpt-reference-consumed',f['initial_odds'],[percentage(p_map(gpt,a,b)),percentage(p_map(gpt,b,a))])
    check('deepseek-reference-consumed',f['deepseek_odds'],[percentage(p_map(deepseek,a,b)),percentage(p_map(deepseek,b,a))])
    check('ranking-button',f['button_ranking'],moved(f['initial_ranking'],3,0))
    check('ranking-keyboard',f['keyboard_ranking'],moved(f['button_ranking'],0,1))
    check('ranking-two-clicks',f['click_ranking'],moved(f['keyboard_ranking'],0,2))
    check('ranking-pointer-drag',f['drag_ranking'],moved(f['click_ranking'],0,3))
    check('ranking-cancel-does-not-save',f['cancelled_saved_ranking'],None)
    check('ranking-save',f['saved_ranking'],f['imported_ranking'])
    check('custom-reference-selected',f['custom_reference'],'mine')
    order=f['saved_ranking'];p=1/(1+math.exp(-(order.index(b)-order.index(a))*.122))
    check('custom-odds-consumed',f['custom_odds'],[percentage(p),percentage(1-p)])
    check('ranking-reload',f['ranking_after_reload'],order)
    check('reference-reload',f['reference_after_reload'],'mine')
    check('deepseek-raw-provenance-link',f['deepseek_raw_link'],'data/deepseek-forecast.json')
    check('deepseek-calibration-consumed',deepseek['calibration'] in f['deepseek_process_text'],True)
    check('pending-model-no-raw-link',f['pending_raw_links'],0)
    check('pending-model-no-gpt-calibration','该模型尚未运行' in f['pending_process_text'] and gpt['calibration'] not in f['pending_process_text'],True)
    check('mobile-touch-drag',f['mobile_touch_after'],moved(f['mobile_before'],0,3))
    check('mobile-no-overflow',f['mobile_width']['scroll']<=f['mobile_width']['viewport'],True)
    return {'rows':rows,'status':'pass' if all(r['status']=='pass'for r in rows)else'fail'}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--observed',required=True);parser.add_argument('--reference');parser.add_argument('--out',required=True);args=parser.parse_args();repo=Path(__file__).resolve().parents[3];root=Path(__file__).resolve().parents[1]
    observed=json.loads((repo/args.observed).read_text());reference=json.loads((repo/args.reference).read_text())if args.reference else None;report=compare(observed['facts'],root,reference);report['page_errors']=observed['errors'];out=repo/args.out;out.mkdir(parents=True,exist_ok=False);(out/'comparison.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':report['status'],'passed':sum(r['status']=='pass'for r in report['rows']),'total':len(report['rows'])}));raise SystemExit(0 if report['status']=='pass' and not report['page_errors'] else 1)
