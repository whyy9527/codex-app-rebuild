"""Source verification for review navigation and persisted player position."""
import argparse
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_evidence import URL,CONTENT,ContentSurface


def collect(out):
    root=Path(__file__).resolve().parents[3];output=root/out;output.mkdir(parents=True,exist_ok=False);result={'facts':{},'errors':[]};f=result['facts']
    with sync_playwright()as p:
        browser=p.chromium.launch(executable_path=os.environ.get('REBUILD_BROWSER_EXECUTABLE','/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge'),headless=True)
        try:
            page=browser.new_page(viewport={'width':1440,'height':1000},locale='zh-CN',timezone_id='Asia/Shanghai');page.set_default_timeout(20000);page.on('pageerror',lambda e:result['errors'].append(str(e)))
            def frame():
                iframe=page.locator('iframe[src="'+CONTENT+'"]');iframe.wait_for();surface=ContentSurface(iframe.element_handle().content_frame(),iframe);surface.locator('.studio2 button.play').wait_for();return surface
            def pause(s):
                if s.locator('button[title="暂停 (空格)"]').count():s.locator('.studio2').press('Space')
            page.goto(URL,wait_until='load');s=frame();f['initial_playing']=s.locator('.studio2 button.play').get_attribute('title');pause(s)
            s.get_by_role('button',name='下一步',exact=True).click();s.get_by_role('button',name='下一步',exact=True).click();f['before_reload']=s.locator('.stage-box').inner_text();f['saved_progress']=s.evaluate('Object.fromEntries(Object.entries(localStorage).filter(([k])=>k.startsWith("s16-replay-")))')
            page.reload(wait_until='load');s=frame();pause(s);f['after_reload']=s.locator('.stage-box').inner_text();f['restored_progress']=s.evaluate('Object.fromEntries(Object.entries(localStorage).filter(([k])=>k.startsWith("s16-replay-")))')
            s.locator('a[href*="tab=schedule"]').first.click();s.wait_for_function('()=>location.hash.includes("tab=schedule")');s.locator('a[href*="/match/"]').first.click();s.locator('.sh-board').wait_for();s.locator('.game-tabs .gt').first.wait_for();f['series_head']=s.locator('.sh-board').inner_text();f['initial_map']=s.locator('.game-tabs .on').inner_text();f['map_labels']=s.locator('.game-tabs .gt').all_text_contents();s.locator('.game-tabs .gt').last.click();s.wait_for_function('()=>document.querySelector(".game-tabs .gt:last-child")?.classList.contains("on")');f['last_map']=s.locator('.game-tabs .on').inner_text();f['curve_count']=s.locator('.winchart').count();f['review_controls']=s.locator('#main-content button').all_text_contents();f['review_text']=s.locator('#main-content').inner_text();s.screenshot(path=str(output/'review.png'))
        except Exception as error:result['error']=str(error)
        finally:browser.close()
    (output/'observed.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');return result


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--out',required=True);args=a.parse_args();r=collect(args.out);print(json.dumps({'facts':len(r['facts']),'error':r.get('error'),'errors':r['errors']},ensure_ascii=False));raise SystemExit(1 if r.get('error')or r['errors'] else 0)
