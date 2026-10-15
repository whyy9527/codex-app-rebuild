"""Actual candidate review/persistence facts, without expected answers."""
import argparse
from datetime import datetime,timezone
import json
import os
from pathlib import Path


def collect(url,out):
    from playwright.sync_api import sync_playwright
    root=Path(__file__).resolve().parents[3];output=root/out;output.mkdir(parents=True,exist_ok=False)
    result={'created_at':datetime.now(timezone.utc).isoformat(),'facts':{},'errors':[]}
    f=result['facts']
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path=os.environ.get('REBUILD_BROWSER_EXECUTABLE','/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge'),headless=True)
        try:
            context=b.new_context(viewport={'width':1370,'height':988},locale='zh-CN',timezone_id='Asia/Shanghai');page=context.new_page();page.set_default_timeout(20000);page.on('pageerror',lambda e:result['errors'].append(str(e)))
            def pause():
                page.locator('#play').wait_for()
                if page.locator('#play[title="暂停 (空格)"]').count():page.locator('.studio').press('Space')
            page.goto(url,wait_until='load');page.locator('#play').wait_for();f['initial_playing']=page.locator('#play').get_attribute('title');pause()
            page.locator('#next').click();page.locator('#next').click();f['before_reload']=page.locator('#stage').inner_text();f['saved_progress']=page.evaluate('JSON.parse(localStorage.getItem("vct-finals-replay-codex"))')
            page.reload(wait_until='load');pause();f['after_reload']=page.locator('#stage').inner_text()
            page.locator('.channels [data-channel="deepseek"]').click();page.locator('#next').click();f['deepseek_progress']=page.locator('#stage').inner_text()
            page.locator('.channels [data-channel="codex"]').click();f['codex_return']=page.locator('#stage').inner_text()
            page.locator('[data-day="1"]').click();page.locator('#prev').click();f['lower_player_final']=page.locator('#stage').inner_text()
            page.locator('[data-tab="schedule"]').click();f['official_rows']=page.locator('#channel-content table tbody tr').all_text_contents();f['simulated_cards']=page.locator('.simulation-card').all_text_contents();page.locator('.simulation-card').first.click();page.locator('.review-head').wait_for();f['lower_head']=page.locator('.review-head').inner_text();f['lower_maps']=page.locator('#review-content tbody tr').all_text_contents();f['lower_map_cells']=page.locator('#review-content tbody tr').evaluate_all('(rows)=>rows.map(r=>[...r.children].map(c=>c.textContent.trim()))');f['curve_values']=page.locator('.chart-value').all_text_contents();f['lower_reason']=page.locator('#review-content section').nth(1).inner_text();f['initial_map']=page.locator('#review-map').inner_text()
            page.locator('[data-review-map]').last.click();f['last_map']=page.locator('#review-map').inner_text();f['active_map']=page.locator('[data-review-map][aria-pressed="true"]').inner_text();page.screenshot(path=str(output/'lower-review.png'),full_page=True)
            page.locator('a[href*="#/match/1"]').click();page.locator('h1').filter(has_text='总决赛').wait_for();f['grand_head']=page.locator('.review-head').inner_text();f['grand_maps']=page.locator('#review-content tbody tr').all_text_contents()
            page.locator('a[href*="tab=schedule"]').click();page.locator('[data-tab="bracket"]').click();f['bracket_champion']=page.locator('.result-card h2').inner_text();f['bracket_final']=page.locator('.bracket .pick-match').nth(1).inner_text();f['model_card_champion']=page.locator('.forecast-card[href="#/?ai=codex"] .champ').inner_text()
            page.locator('#upper-winner').select_option('LOUD');page.locator('#lower-winner').select_option('G2');page.locator('[data-tab="schedule"]').click();page.locator('.simulation-card').first.click();f['alternate_head']=page.locator('.review-head').inner_text();link=page.url;f['alternate_link']=link
            fresh=b.new_context();share=fresh.new_page();share.goto(link,wait_until='load');share.locator('.review-head').wait_for();f['fresh_shared_head']=share.locator('.review-head').inner_text();fresh.close()
            page.locator('a[href*="#/match/1"]').click();page.locator('h1').filter(has_text='总决赛').wait_for();f['alternate_final_head']=page.locator('.review-head').inner_text();page.locator('a[href*="tab=schedule"]').click();f['alternate_card_champion']=page.locator('.forecast-card[href="#/?ai=codex"] .champ').inner_text();page.locator('[data-tab="bracket"]').click();f['alternate_bracket_champion']=page.locator('.result-card h2').inner_text()
            page.goto(url+'#/match/0?ai=opus',wait_until='load');page.get_by_role('heading',name='该模型等待预测',exact=True).wait_for();f['pending_review']=page.locator('#review-content').inner_text();f['pending_maps']=page.locator('[data-review-map]').count()
            page.goto(url+'#/?ai=codex&tab=players',wait_until='load');page.get_by_role('heading',name='选手数据等待官方明细',exact=True).wait_for();f['players']=page.locator('#channel-content').inner_text()
            page.locator('[data-tab="news"]').click();f['news']=page.locator('#channel-content').inner_text();f['news_card_count']=page.locator('.simulation-card').count()
            page.set_viewport_size({'width':390,'height':844});page.locator('.simulation-card').first.click();page.locator('.review-head').wait_for();f['mobile_width']=page.evaluate('({scroll:document.documentElement.scrollWidth,viewport:innerWidth})');page.screenshot(path=str(output/'mobile-review.png'),full_page=True)
            page.goto(url,wait_until='load');pause();page.locator('#replay-start').click();page.locator('.studio').press('Space');f['restarted']=page.locator('#stage').inner_text();f['restart_progress']=page.evaluate('JSON.parse(localStorage.getItem("vct-finals-replay-codex"))');context.close()
        except Exception as error:result['error']=str(error)
        finally:b.close()
    (output/'observed.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--url',default='http://127.0.0.1:5173/');parser.add_argument('--out',required=True);args=parser.parse_args();r=collect(args.url,args.out);print(json.dumps({'facts':len(r['facts']),'error':r.get('error'),'errors':r['errors']},ensure_ascii=False));raise SystemExit(1 if r.get('error')or r['errors']else 0)
