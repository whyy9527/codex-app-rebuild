"""Common mobile journeys/metrics; source/candidate adapters only collect facts."""
import argparse
from datetime import datetime,timezone
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_evidence import ContentSurface,URL,CONTENT

METRICS='''selectors=>Object.fromEntries(Object.entries(selectors).map(([key,selector])=>{const els=[...document.querySelectorAll(selector)];return [key,els.map(e=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e);return {text:e.innerText?.trim(),visible:r.width>0&&r.height>0,rect:[r.x,r.y,r.width,r.height],size:s.fontSize,weight:s.fontWeight,lineHeight:s.lineHeight,display:s.display,columns:s.gridTemplateColumns,padding:s.padding}})]}))'''


def collect(mode,out):
    root=Path(__file__).resolve().parents[3];output=root/out;output.mkdir(parents=True,exist_ok=False);result={'created_at':datetime.now(timezone.utc).isoformat(),'mode':mode,'facts':{},'errors':[]};f=result['facts']
    with sync_playwright()as p:
        browser=p.chromium.launch(executable_path=os.environ.get('REBUILD_BROWSER_EXECUTABLE','/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge'),headless=True)
        try:
            context=browser.new_context(viewport={'width':390,'height':844}if mode=='reference'else{'width':320,'height':832},locale='zh-CN',timezone_id='Asia/Shanghai');page=context.new_page();page.set_default_timeout(20000);page.on('pageerror',lambda e:result['errors'].append(str(e)));page.goto(URL if mode=='reference'else'http://127.0.0.1:5173/',wait_until='load')
            if mode=='reference':
                iframe=page.locator('iframe[src="'+CONTENT+'"]');iframe.wait_for();surface=ContentSurface(iframe.element_handle().content_frame(),iframe);studio='.studio2';selector='.mobile-channel select';stage='.stage-box'
            else:surface=page;studio='.studio';selector='#mobile-model';stage='.stage-box'
            surface.locator(selector).wait_for();surface.locator(studio+' button.play').wait_for()
            if surface.locator('button[title="暂停 (空格)"]').count():surface.locator(studio).press('Space')
            surface.evaluate('document.fonts.ready');surface.locator('#main-content').press('Escape');surface.evaluate('scrollTo(0,0)')
            f['viewport']=surface.evaluate('({width:innerWidth,height:innerHeight})');f['page_width']=surface.evaluate('document.documentElement.scrollWidth');f['navigation']=surface.locator('.mainnav a').all_text_contents();f['model_options']=surface.locator(selector+' option').all_text_contents()
            f['metrics']=surface.evaluate(METRICS,{'title':'.home-head h1'if mode=='reference'else'.hero h1','navigation':'.mainnav a','nav_grid':'.mainnav','model_selector':selector,'portraits':'.lineup'if mode=='reference'else'.portraits','model_buttons':'.channels .ch'if mode=='reference'else'.channels .channel','tabs':'.studio-tabs'if mode=='reference'else'.tabs','tab_buttons':'.studio-tabs>a'if mode=='reference'else'.tabs button','side_schedule':'.today'if mode=='reference'else'.schedule','stage':stage})
            surface.screenshot(path=str(output/'home.png'));surface.locator(selector).select_option(label='GPT-6.1 sol');surface.wait_for_function('s=>document.querySelector(s)?.innerText.includes("GPT-6.1 sol")',arg=stage)
            if surface.locator('button[title="暂停 (空格)"]').count():surface.locator(studio).press('Space')
            f['selected_model']=surface.locator(selector+' option:checked').inner_text();f['selected_stage']=surface.locator(stage).inner_text();surface.screenshot(path=str(output/'model.png'))
            surface.get_by_role('button',name='10/18',exact=True).click();f['day_stage']=surface.locator(stage).inner_text();f['schedule_controls']=surface.locator('.today-row'if mode=='reference'else'.schedule-row').evaluate_all('(els)=>els.map(e=>({tag:e.tagName,text:e.innerText,title:e.title}))')
            if surface.locator('.today-row'if mode=='reference'else'.schedule-row').count():
                surface.locator('.today-row'if mode=='reference'else'.schedule-row').first.click();f['schedule_click_stage']=surface.locator(stage).inner_text()
            surface.locator('.mainnav a[href="#/pickem"]').click();surface.get_by_role('button',name='按实力参考一键填完',exact=True).click()if mode=='reference'else surface.locator('#autofill').click()
            result_selector='.pk-result'if mode=='reference'else'#pick-result';surface.locator(result_selector).wait_for();f['prediction_result']=surface.locator(result_selector).inner_text();f['prediction_width']=surface.evaluate('document.documentElement.scrollWidth');surface.screenshot(path=str(output/'pickem.png'))
            if mode=='reference':
                surface.locator('.mainnav a[href="#/"]').click();surface.locator('a[href*="tab=schedule"]').first.click();surface.locator('a[href*="/match/"]').first.click();surface.locator('.sh-board').wait_for();surface.locator('.game-tabs .gt').last.click();surface.wait_for_function('()=>document.querySelector(".game-tabs .gt:last-child")?.classList.contains("on")');surface.locator('.winchart').wait_for();f['selected_review_map']=surface.locator('.game-tabs .on').inner_text();f['curve_count']=surface.locator('.winchart').count()
            else:
                surface.locator('.mainnav a[href="#/"]').click();surface.locator('[data-tab="schedule"]').click();surface.locator('.simulation-card').first.click();surface.locator('.review-head').wait_for();surface.locator('[data-review-map]').last.click();f['selected_review_map']=surface.locator('[data-review-map][aria-pressed="true"]').inner_text();f['curve_count']=surface.locator('.series-chart').count()
            f['review_width']=surface.evaluate('document.documentElement.scrollWidth');surface.screenshot(path=str(output/'review.png'))
            if mode=='candidate':
                page.set_viewport_size({'width':390,'height':844});page.goto('http://127.0.0.1:5173/',wait_until='load');page.locator('#mobile-model').wait_for();f['wide_mobile_width']=page.evaluate('({scroll:document.documentElement.scrollWidth,viewport:innerWidth})');f['wide_model_selector']=page.locator('#mobile-model').is_visible();page.screenshot(path=str(output/'wide-home.png'))
            context.close()
        except Exception as error:result['error']=str(error)
        finally:browser.close()
    (output/'observed.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['reference','candidate'],required=True);p.add_argument('--out',required=True);a=p.parse_args();r=collect(a.mode,a.out);print(json.dumps({'mode':a.mode,'facts':len(r['facts']),'error':r.get('error'),'errors':r['errors']},ensure_ascii=False));raise SystemExit(1 if r.get('error')or r['errors']else 0)
