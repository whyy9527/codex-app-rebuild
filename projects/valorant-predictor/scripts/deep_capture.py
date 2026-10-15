"""Frozen deep-branch discovery adapter, with real live frame actions and evidence."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from runtime.browser import collect_step, write_json
from capabilities.rebuild.browser import observed_state, evidence_problems
from browser_evidence import ContentSurface, URL, CONTENT


def capture_probe(workspace, probe, out):
    from playwright.sync_api import sync_playwright
    root=Path(workspace).resolve();output=root/out;output.mkdir(parents=True,exist_ok=False)
    result={'schema_version':1,'created_at':datetime.now(timezone.utc).isoformat(),'probe':probe,
            'restoration':'Fresh local context; no server-side reset','steps':[],'states':{},'actions':[]}
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=os.environ.get('REBUILD_BROWSER_EXECUTABLE','/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge'),headless=True)
        try:
            page=browser.new_page(viewport={'width':1440,'height':1000},locale='zh-CN',timezone_id='Asia/Shanghai');page.set_default_timeout(20000)
            page.goto(URL,wait_until='load');iframe=page.locator('iframe[src="'+CONTENT+'"]');iframe.wait_for();surface=ContentSurface(iframe.element_handle().content_frame(),iframe)
            surface.locator('.studio2 button.play').wait_for()
            if surface.locator('button[title="暂停 (空格)"]').count():surface.locator('.studio2').press('Space')
            if probe['kind']=='pickem_ranking':
                surface.locator('.mainnav a[href="#/pickem"]').press('Enter');surface.get_by_role('button',name='自定义实力排名',exact=True).wait_for();surface.get_by_role('button',name='自定义实力排名',exact=True).press('Enter')
                surface.locator('.pk-rank-list').wait_for();result['actions'].append('Open custom ranking via real button Enter')
            else:
                selector='a[href*="tab='+probe['tab']+'"]'
                surface.locator(selector).first.press('Enter');surface.wait_for_function('t=>new URLSearchParams(location.hash.split("?")[1]).get("tab")===t',arg=probe['tab'])
                result['actions'].append('Activate '+probe['tab']+' channel tab via Enter')
                # A real tab link's selected CSS and nonempty content are observed,
                # while async arrival and sampling instability remain in receipts.
                surface.wait_for_function('()=>document.querySelector("#main-content")?.innerText.length>700')
                if probe['kind']=='schedule_review':
                    links=surface.locator('a[href*="/match/"]')
                    links.first.wait_for();href=links.first.get_attribute('href');links.first.press('Enter');surface.wait_for_function('h=>location.hash===h',arg=href)
                    result['actions'].append('Open observed match link '+href)
            surface.locator('#main-content').press('Escape');surface.evaluate('window.scrollTo(0,0)')
            clock=surface.locator('a.live-badge').inner_text();surface.wait_for_function('previous=>document.querySelector("a.live-badge")?.textContent.trim()!==previous',arg=clock)
            step={'id':probe['id'],'action':{'type':'observe'},'ready':{'selector':'#main-content','state':'visible'},'capture':['dom','text','accessibility','screenshot']}
            started=time.monotonic();record=collect_step(surface,root,output,0,step,{'main':'#main-content'})
            record.update(elapsed_seconds=time.monotonic()-started,receipt_path=str((output/'0000-step.json').relative_to(root)),cleanup='released')
            result['steps'].append(record);result['links']=surface.locator('#main-content a').evaluate_all('(a)=>a.map(e=>({text:e.textContent.trim(),href:e.getAttribute("href")}))')
            result['controls']=surface.locator('#main-content button, #main-content input, #main-content select').evaluate_all('(a)=>a.map(e=>({tag:e.tagName,text:e.textContent.trim(),label:e.getAttribute("aria-label"),title:e.getAttribute("title"),value:e.value,disabled:e.disabled}))')
        except Exception as error:result['error']=str(error)
        finally:browser.close()
    for record in result['steps']:
        write_json(root/record['receipt_path'],record);result['states'][record['id']]=observed_state(root,record,record['receipt_path'])
    result['status']='captured' if result['steps'] and not result.get('error') and all(not evidence_problems(root,r,r['requested'])for r in result['steps']) else 'incomplete'
    write_json(output/'observed.json',result);return result
