"""Actual fixed simulation ticker: reveal, pause, hover, close and motion preference."""
import argparse
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_evidence import ContentSurface, URL, CONTENT


def collect(mode,out):
    root=Path(__file__).resolve().parents[3];output=root/out;output.mkdir(parents=True,exist_ok=False);result={'mode':mode,'facts':{},'errors':[]};f=result['facts']
    with sync_playwright()as p:
        b=p.chromium.launch(executable_path=os.environ.get('REBUILD_BROWSER_EXECUTABLE','/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge'),headless=True)
        try:
            context=b.new_context(viewport={'width':1440,'height':1000},locale='zh-CN')
            def prepare(context):
                page=context.new_page();page.set_default_timeout(25000);page.on('pageerror',lambda e:result['errors'].append(str(e)));page.goto(URL if mode=='reference'else'http://127.0.0.1:5173/',wait_until='load')
                if mode=='reference':
                    iframe=page.locator('iframe[src="'+CONTENT+'"]');iframe.wait_for();s=ContentSurface(iframe.element_handle().content_frame(),iframe);studio='.studio2'
                else:s=page;studio='.studio'
                s.locator(studio+' button.play').wait_for()
                if s.locator('button[title="暂停 (空格)"]').count():s.locator(studio).press('Space')
                return page,s
            page,s=prepare(context)
            def pointer(control,click=False):
                # Native locator auto-scroll misplaces this sticky OOPIF control.
                # Use its observed viewport rectangle, with the measured iframe scale.
                rect=control.evaluate('(e)=>{const r=e.getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height}}')
                box=s.element.bounding_box()if mode=='reference'else{'x':0,'y':0,'width':page.viewport_size['width'],'height':page.viewport_size['height']}
                viewport=s.evaluate('({width:innerWidth,height:innerHeight})')
                x=box['x']+(rect['x']+rect['w']/2)*box['width']/viewport['width'];y=box['y']+(rect['y']+rect['h']/2)*box['height']/viewport['height']
                if not(0<=x<page.viewport_size['width']and 0<=y<page.viewport_size['height']):raise ValueError('Observed control center is outside the visible browser')
                f.setdefault('pointer_actions',[]).append({'x':x,'y':y,'click':click,'control':control.inner_text()[:80]})
                page.mouse.click(x,y)if click else page.mouse.move(x,y)
            closed=s.get_by_role('button',name='展开 AI 模拟速报（含后续剧情）',exact=True);closed.wait_for();f['closed_label']=closed.inner_text();f['closed_fixed']=s.locator('.ticker').evaluate('(e)=>({position:getComputedStyle(e).position,bottom:getComputedStyle(e).bottom,height:e.getBoundingClientRect().height})')
            if mode=='candidate':closed.click()
            else:closed.press('Enter')
            f['initial_activation']='pointer'if mode=='candidate'else'keyboard'
            s.locator('.ticker-track').wait_for();f['opened_text']=s.locator('.ticker').inner_text();f['primary_links']=s.locator('.ticker-row:not([aria-hidden]) a').all_text_contents();f['hidden_duplicate_tabindices']=s.locator('.ticker-row[aria-hidden] a').evaluate_all('(els)=>els.map(e=>e.tabIndex)')
            s.get_by_role('button',name='暂停速报',exact=True).press('Enter');f['paused_label']=s.get_by_role('button',name='滚动速报',exact=True).inner_text();f['paused_motion']=s.locator('.ticker-move').evaluate('(e)=>({name:getComputedStyle(e).animationName,state:getComputedStyle(e).animationPlayState,transform:getComputedStyle(e).transform})');s.screenshot(path=str(output/'paused.png'))
            s.get_by_role('button',name='滚动速报',exact=True).press('Enter');s.locator('#main-content').press('Escape');page.mouse.move(-1,-1);f['running_motion']=s.locator('.ticker-move').evaluate('(e)=>({name:getComputedStyle(e).animationName,state:getComputedStyle(e).animationPlayState,duration:getComputedStyle(e).animationDuration})')
            pointer(s.locator('.ticker-track'));f['hover_motion']=s.locator('.ticker-move').evaluate('(e)=>getComputedStyle(e).animationPlayState')
            s.get_by_role('button',name='收起模拟速报',exact=True).press('Enter');f['closed_again']=closed.count()
            closed.press('Enter');s.locator('.ticker-row:not([aria-hidden]) a').first.press('Enter');s.locator('.sh-board'if mode=='reference'else'.review-head').wait_for();f['review_text']=s.locator('#main-content').inner_text();context.close()
            reduced=b.new_context(viewport={'width':390,'height':844},reduced_motion='reduce');page,s=prepare(reduced);s.get_by_role('button',name='展开 AI 模拟速报（含后续剧情）',exact=True).press('Enter');f['reduced_motion_label']=s.get_by_role('button',name='滚动速报',exact=True).inner_text();f['mobile_width']=s.evaluate('({viewport:innerWidth,scroll:document.documentElement.scrollWidth})');s.screenshot(path=str(output/'mobile.png'));reduced.close()
        except Exception as error:
            result['error']=str(error)
            try:
                result['failure_ticker_dom']=s.locator('.ticker').evaluate('(e)=>e.outerHTML')
                s.screenshot(path=str(output/'failure.png'))
            except Exception as failure:result['failure_capture_error']=str(failure)
        finally:b.close()
    (output/'observed.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['reference','candidate'],required=True);p.add_argument('--out',required=True);a=p.parse_args();r=collect(a.mode,a.out);print(json.dumps({'mode':a.mode,'facts':len(r['facts']),'error':r.get('error'),'errors':r['errors']}));raise SystemExit(1 if r.get('error')or r['errors']else 0)
