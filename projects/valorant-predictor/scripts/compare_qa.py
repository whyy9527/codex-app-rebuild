"""Independent comparison of recorded facts; never lets a driver self-report pass."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from capabilities.rebuild.frontend import compare as compare_frontend


def compare(root, observed, reference):
    f=observed.get('facts',{});r=reference.get('facts',{});rows=[]
    def check(name,actual,expected,source='observed'):
        rows.append({'id':name,'knowledge_source':source,'status':'unavailable' if actual is None else 'pass' if actual==expected else 'fail','actual':actual,'expected':expected})
    def changed(key):
        item=f.get(key);return None if not item else item['before']!=item['after']
    check('primary-navigation',f.get('navigation'),r.get('navigation'))
    check('eight-model-channels',f.get('channel_count'),r.get('channel_count'))
    check('visible-hero-assets-loaded',all(i['loaded'] for i in f['hero_images']) if f.get('hero_images') else None,True)
    check('player-next-step',changed('player_next'),True)
    check('player-keyboard-next',changed('keyboard_next'),True)
    check('player-day-jump',f.get('player_day'),'10 月 18 日','decision:user-two-dates')
    check('player-speed',f.get('player_speed'),r.get('player_speed'))
    check('mute-persists',f.get('mute_after_reload'),'静音' if f.get('mute_saved') is False else '取消静音')
    check('lower-winner-propagation','LOUD' in f['downstream_winner'] if 'downstream_winner'in f else None,True)
    check('dependent-final-invalidated','完成两场选择后' in f['invalidated_champion'] if 'invalidated_champion'in f else None,True)
    check('new-lower-winner-propagation','100T' in f['updated_final'] if 'updated_final'in f else None,True)
    saved=f.get('saved_pick');check('save-and-reload',f.get('restored_champion'),saved.get('champion') if saved else None)
    check('share-link',f.get('shared_link_present'),True)
    check('shared-champion',f.get('shared_champion'),saved.get('champion') if saved else None)
    check('poster-dialog',f.get('poster_visible'),True,'decision:local-poster-no-platform-follow-action')
    check('poster-download',f.get('poster_download_bytes',0)>0,True)
    check('reset-requires-new-picks',f.get('reset_save_disabled'),True)
    check('team-search',f.get('search_matches'),1)
    check('team-empty-state',f.get('search_empty'),'没有找到匹配战队')
    check('official-VIT-map-record','8–2' in f['team_detail'] if 'team_detail'in f else None,True,'observed:official-snapshot')
    check('no-premature-scoring','0 / 2 场已结算' in f['leaderboard'] if 'leaderboard'in f else None,True,'decision:user-two-dates')
    check('unrun-model-stays-pending','该模型等待预测' in f['pending_channel'] if 'pending_channel'in f else None,True,'decision:user-model-availability')
    check('available-model-independent','DeepSeek' in f['deepseek_channel'] and '等待预测' not in f['deepseek_channel'] if 'deepseek_channel'in f else None,True)
    check('model-cards-independent-of-selection','null' not in f['codex_card_with_pending_selected'] and '待预测' not in f['codex_card_with_pending_selected'] if 'codex_card_with_pending_selected'in f else None,True)
    for key in ['mobile_home_width','mobile_pick_width']:
        v=f.get(key);check(key,None if v is None else v['scroll']<=v['viewport'],True)
    check('mobile-prediction',bool(f.get('mobile_pick_champion')),True)
    check('invalid-share-feedback',f.get('invalid_share_feedback'),'分享链接无效或不适用于当前赛事数据')
    check('candidate-page-errors',observed.get('errors'),[])
    rows += [{'id':key,'knowledge_source':'unknown','status':'not_run','reason':reason} for key,reason in [
        ('full-visual-equivalence','VALORANT content/art transforms are required; detailed layout/font/whole-frame comparison remains open.'),
        ('application-audio-equivalence','Mute persistence is verified; actual application-output sound comparison has not run.'),
        ('unvisited-reference-branches','Original BP/player/story/review/custom-ranking and deeper hover/keyboard branches remain to explore.')]]
    return {'status':'incomplete' if any(row['status']!='pass' for row in rows) else 'pass','rows':rows,
            'counts':{status:sum(row['status']==status for row in rows) for status in ['pass','fail','unavailable','not_run']}}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--observed',required=True);parser.add_argument('--reference',required=True);parser.add_argument('--out',required=True);args=parser.parse_args()
    root=Path(__file__).resolve().parents[3];observed=json.loads((root/args.observed).read_text());reference=json.loads((root/args.reference).read_text());report=compare(root,observed,reference)
    out=root/args.out;out.mkdir(parents=True,exist_ok=False)
    contract=root/'projects/valorant-predictor/contracts/frontend.json'
    if contract.exists():report['frontend']=compare_frontend(root,json.loads(contract.read_text()),observed)
    (out/'comparison.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':report['status'],'counts':report['counts'],'frontend':report.get('frontend',{}).get('status')},ensure_ascii=False));raise SystemExit(0 if report['status']=='pass' else 1)
