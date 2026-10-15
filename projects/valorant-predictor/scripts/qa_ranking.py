"""Actual ranking controls and per-model UI consumption; raw facts only."""
import argparse
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright


def collect(out):
    root=Path(__file__).resolve().parents[3];output=root/out;output.mkdir(parents=True,exist_ok=False)
    result={'facts':{},'errors':[]};f=result['facts']
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=os.environ.get('REBUILD_BROWSER_EXECUTABLE','/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge'),headless=True)
        try:
            context=browser.new_context(viewport={'width':1370,'height':988},locale='zh-CN',timezone_id='Asia/Shanghai');page=context.new_page();page.set_default_timeout(15000)
            def page_error(error):
                result['errors'].append(str(error));result.setdefault('error_details',[]).append({'message':str(error),'stack':error.stack,'url':page.url})
            page.on('pageerror',page_error)
            page.goto('http://127.0.0.1:5173/#/pickem',wait_until='load');page.locator('#reference-model').wait_for()
            f['initial_matchup']=page.locator('#lower-final [data-pick]').evaluate_all('(buttons)=>buttons.map(b=>b.dataset.team)');f['initial_reference']=page.locator('#reference-model').input_value();f['initial_odds']=page.locator('#lower-final [data-pick] small').all_text_contents()
            page.locator('#reference-model').select_option('deepseek');f['deepseek_reference']=page.locator('#reference-model').input_value();f['deepseek_odds']=page.locator('#lower-final [data-pick] small').all_text_contents()
            page.locator('#custom-ranking').click();f['initial_ranking']=page.locator('.ranking-list li b').all_text_contents();team=f['initial_ranking'][-1]
            for _ in range(3):page.get_by_role('button',name='上移 '+team,exact=True).click()
            f['button_ranking']=page.locator('.ranking-list li b').all_text_contents()
            first=page.locator('.ranking-list li').first;first.focus();page.keyboard.press('ArrowDown');f['keyboard_ranking']=page.locator('.ranking-list li b').all_text_contents()
            page.locator('[data-ranking-row="0"] b').click();page.locator('[data-ranking-row="2"] b').click();f['click_ranking']=page.locator('.ranking-list li b').all_text_contents()
            start=page.locator('[data-ranking-grip="0"]').bounding_box();end=page.locator('[data-ranking-row="3"]').bounding_box();page.mouse.move(start['x']+start['width']/2,start['y']+start['height']/2);page.mouse.down();page.mouse.move(end['x']+end['width']/2,end['y']+end['height']/2,steps=8);page.mouse.up();f['drag_ranking']=page.locator('.ranking-list li b').all_text_contents()
            page.locator('#ranking-cancel').click();f['cancelled_saved_ranking']=page.evaluate('localStorage.getItem("vct-finals-ranking")')
            page.locator('#custom-ranking').click();page.locator('#ranking-import').select_option('codex');page.locator('#ranking-import-button').click();f['imported_ranking']=page.locator('.ranking-list li b').all_text_contents()
            page.locator('#ranking-use').click();f['saved_ranking']=page.evaluate('JSON.parse(localStorage.getItem("vct-finals-ranking"))');f['custom_reference']=page.locator('#reference-model').input_value();f['custom_odds']=page.locator('#lower-final [data-pick] small').all_text_contents()
            page.locator('#autofill').click();f['custom_champion']=page.locator('#pick-result h2').inner_text();page.reload();page.locator('#reference-model').wait_for();f['reference_after_reload']=page.locator('#reference-model').input_value();page.locator('#custom-ranking').click();f['ranking_after_reload']=page.locator('.ranking-list li b').all_text_contents();page.locator('#ranking-cancel').click()
            page.goto('http://127.0.0.1:5173/#/?ai=deepseek',wait_until='load');page.locator('[data-tab="process"]').click();f['deepseek_raw_link']=page.locator('#channel-content a.btn').get_attribute('href');f['deepseek_process_text']=page.locator('#channel-content').inner_text()
            page.goto('http://127.0.0.1:5173/#/?ai=opus',wait_until='load');page.locator('[data-tab="process"]').click();f['pending_raw_links']=page.locator('#channel-content a.btn').count();f['pending_process_text']=page.locator('#channel-content').inner_text()
            mobile=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,locale='zh-CN',timezone_id='Asia/Shanghai');m=mobile.new_page();m.goto('http://127.0.0.1:5173/#/pickem',wait_until='load');m.locator('#custom-ranking').click();m.locator('.ranking-list').scroll_into_view_if_needed()
            f['mobile_before']=m.locator('.ranking-list li b').all_text_contents();first=m.locator('[data-ranking-grip="0"]').bounding_box();last=m.locator('[data-ranking-row="3"]').bounding_box();session=mobile.new_cdp_session(m)
            x=first['x']+first['width']/2;y=first['y']+first['height']/2;target_x=last['x']+40;target_y=last['y']+last['height']/2
            session.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y}]})
            for step in range(1,9):session.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x+(target_x-x)*step/8,'y':y+(target_y-y)*step/8}]})
            session.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});f['mobile_touch_after']=m.locator('.ranking-list li b').all_text_contents();f['mobile_width']=m.evaluate('({scroll:document.documentElement.scrollWidth,viewport:innerWidth})');m.screenshot(path=str(output/'mobile-ranking.png'));mobile.close();context.close()
        except Exception as error:result['error']=str(error)
        finally:browser.close()
    (output/'observed.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',required=True);args=parser.parse_args();s=collect(args.out);print(json.dumps({'facts':len(s['facts']),'error':s.get('error'),'page_errors':s['errors']},ensure_ascii=False));raise SystemExit(1 if s.get('error') or s['errors'] else 0)
