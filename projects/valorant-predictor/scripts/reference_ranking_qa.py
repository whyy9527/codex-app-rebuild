"""Run the corresponding source ranking journey without changing remote state."""
import argparse
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_evidence import ContentSurface,URL,CONTENT


def collect(out):
    root=Path(__file__).resolve().parents[3];output=root/out;output.mkdir(parents=True,exist_ok=False);result={'facts':{}};facts=result['facts']
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=os.environ.get('REBUILD_BROWSER_EXECUTABLE','/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge'),headless=True)
        try:
            page=browser.new_page(viewport={'width':1440,'height':1000});page.set_default_timeout(20000);page.goto(URL,wait_until='load');iframe=page.locator('iframe[src="'+CONTENT+'"]');iframe.wait_for();surface=ContentSurface(iframe.element_handle().content_frame(),iframe)
            surface.locator('.mainnav a[href="#/pickem"]').press('Enter');surface.get_by_role('button',name='自定义实力排名',exact=True).press('Enter');surface.locator('.pk-rank-list').wait_for();facts['initial']=surface.locator('.pk-rank-list li>b').all_text_contents()
            team=facts['initial'][-1];surface.get_by_role('button',name=team+' 上移',exact=True).press('Enter');facts['keyboard_button']=surface.locator('.pk-rank-list li>b').all_text_contents()
            surface.locator('.pk-rank-list li>b').nth(0).click();surface.locator('.pk-rank-list li>b').nth(2).click();facts['two_clicks']=surface.locator('.pk-rank-list li>b').all_text_contents()
            # Keep both targets visible in the same column for real pointer drag.
            first=surface.locator('.pk-rank-list li').nth(0);second=surface.locator('.pk-rank-list li').nth(1);first.scroll_into_view_if_needed();grip=first.locator('.pk-rank-grip');grip.drag_to(second);facts['pointer_drag']=surface.locator('.pk-rank-list li>b').all_text_contents()
            surface.get_by_role('button',name='使用这份排名',exact=True).press('Enter');facts['saved']=surface.evaluate('JSON.parse(localStorage.getItem("s16-my-ranking"))')
            page.reload(wait_until='load');iframe=page.locator('iframe[src="'+CONTENT+'"]');iframe.wait_for();surface=ContentSurface(iframe.element_handle().content_frame(),iframe);surface.locator('.mainnav a[href="#/pickem"]').press('Enter');surface.get_by_role('button',name='调整我的实力排名',exact=True).press('Enter');surface.locator('.pk-rank-list').wait_for();facts['restored']=surface.locator('.pk-rank-list li>b').all_text_contents();iframe.screenshot(path=str(output/'source-ranking.png'))
        except Exception as error:result['error']=str(error)
        finally:browser.close()
    (output/'observed.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',required=True);args=parser.parse_args();r=collect(args.out);print(json.dumps({'facts':len(r['facts']),'error':r.get('error')},ensure_ascii=False));raise SystemExit(1 if r.get('error')else 0)
