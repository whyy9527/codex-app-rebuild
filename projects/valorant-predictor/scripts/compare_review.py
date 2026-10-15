"""Independent acceptance using recorded source/candidate facts and model data."""
import argparse
import itertools
import json
from pathlib import Path
import re


def compare(f,r,root):
    rows=[]
    def check(name,actual,expected,source='observed'):
        rows.append({'id':name,'knowledge_source':source,'status':'unavailable'if actual is None else'pass'if actual==expected else'fail','actual':actual,'expected':expected})
    check('source-default-autoplay',r.get('initial_playing'),'暂停 (空格)')
    check('default-autoplay',f.get('initial_playing'),r.get('initial_playing'))
    check('source-restores-progress',r.get('restored_progress'),r.get('saved_progress'))
    check('source-review-map-switch',r.get('initial_map')!=r.get('last_map'),True)
    check('source-review-curve',bool(r.get('curve_count')),True)
    check('player-reload-position',f.get('after_reload'),f.get('before_reload'))
    check('player-channel-position',f.get('codex_return'),f.get('before_reload'))
    check('player-index-persisted',f.get('saved_progress',{}).get('index'),2)
    check('two-official-series',len(f.get('official_rows',[])),2,'decision:user-two-matches')
    check('official-rows-stay-pending',all('TBD' in row and '待开赛'in row for row in f.get('official_rows',[])),True,'observed:official-snapshot')
    check('two-simulated-series',len(f.get('simulated_cards',[])),2,'decision:user-two-matches')
    check('lower-review-labelled-simulation','AI 模拟 · 非真实赛果'in f.get('lower_head',''),True)
    score=re.search(r'\n([0-3]) : ([0-3])\n',f.get('lower_head',''));score=tuple(map(int,score.groups()))if score else None
    check('lower-score-stops-at-three',bool(score and max(score)==3 and min(score)<3),True)
    check('review-map-count',len(f.get('lower_maps',[])),sum(score)if score else None)
    check('player-review-share-result',f'{score[0]} : {score[1]}'in f.get('lower_player_final','')if score else None,True)
    check('review-map-switch',f.get('initial_map')!=f.get('last_map'),True)
    model=json.loads((root/'data/gpt-6.1-sol-forecast.json').read_text());pair=next(p for p in model['pairs']if set(p['teams'])=={'LOUD','100T'});p=pair['p_first']if pair['teams'][0]=='LOUD'else 1-pair['p_first']
    # Enumerate all remaining win/loss paths independently of the app's recursive formula.
    def chance(a,b):
        total=0
        for seq in itertools.product([0,1],repeat=5-a-b):
            x,y=a,b;prob=1
            for winner in seq:
                if x==3 or y==3:break
                if winner==0:x+=1;prob*=p
                else:y+=1;prob*=1-p
            # Count a terminal path once, irrespective of its unused suffix.
            if x==3:total+=prob/(2**(len(seq)-(x-a+y-b)))
        return f'{100*total:.1f}%'
    cells=f.get('lower_map_cells',[]);scores=[(0,0)]+[tuple(map(int,c[2].split(':')))for c in cells]
    check('conditional-curve-values',f.get('curve_values'),[chance(*s)for s in scores],'decision:constant-map-probability-adaptation')
    check('actual-model-reason',pair['reason']in f.get('lower_reason',''),True,'observed:model-output')
    lower=re.search(r'\n([A-Z0-9]+) 晋级总决赛',f.get('lower_head',''));champ=re.search(r'\n([A-Z0-9]+) 夺得模拟冠军',f.get('grand_head',''))
    lower=lower.group(1)if lower else None;champ=champ.group(1)if champ else None
    check('final-contains-lower-winner',lower in f.get('grand_head','')if lower else None,True)
    check('bracket-final-same-as-recap',lower in f.get('bracket_final','')if lower else None,True)
    check('bracket-champion-same-as-recap',f.get('bracket_champion'),champ)
    # Ignore only outer whitespace between the decorative logo and team identifier.
    check('model-card-champion-same-as-recap',f.get('model_card_champion','').strip(),champ)
    alternate=re.search(r'\n([A-Z0-9]+) 夺得模拟冠军',f.get('alternate_final_head',''));alternate=alternate.group(1)if alternate else None
    check('alternate-card-champion-same-as-recap',f.get('alternate_card_champion','').strip(),alternate)
    check('alternate-bracket-champion-same-as-recap',f.get('alternate_bracket_champion'),alternate)
    check('shared-scenario-in-fresh-context',f.get('fresh_shared_head'),f.get('alternate_head'))
    check('shared-scenario-encoded','upper=LOUD&lower=G2'in f.get('alternate_link',''),True)
    check('unrun-model-no-recap-maps',f.get('pending_maps'),0,'decision:user-available-models-only')
    check('unrun-model-labelled-pending','该模型等待预测'in f.get('pending_review',''),True)
    check('unknown-player-data-explicit','暂无可核实的选手榜'in f.get('players',''),True,'decision:no-invented-official-stats')
    check('two-labelled-reports',f.get('news_card_count'),2)
    check('report-labelled-simulation','非真实新闻'in f.get('news',''),True)
    v=f.get('mobile_width');check('mobile-review-no-overflow',v['scroll']<=v['viewport']if v else None,True)
    check('replay-restarts-at-zero',f.get('restart_progress',{}).get('index'),0)
    return {'rows':rows,'status':'pass'if all(x['status']=='pass'for x in rows)else'fail'}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--observed',required=True);p.add_argument('--reference',required=True);p.add_argument('--out',required=True);a=p.parse_args();repo=Path(__file__).resolve().parents[3];root=Path(__file__).resolve().parents[1];o=json.loads((repo/a.observed).read_text());r=json.loads((repo/a.reference).read_text());report=compare(o['facts'],r['facts'],root);report['driver_errors']=[o.get('error'),r.get('error'),*o.get('errors',[]),*r.get('errors',[])];out=repo/a.out;out.mkdir(parents=True,exist_ok=False);(out/'comparison.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':report['status'],'passed':sum(x['status']=='pass'for x in report['rows']),'total':len(report['rows'])}));raise SystemExit(0 if report['status']=='pass'and not any(report['driver_errors'])else 1)
