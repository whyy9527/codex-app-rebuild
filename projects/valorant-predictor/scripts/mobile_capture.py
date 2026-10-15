"""Frozen mobile source discovery with explicit rendered readiness and provenance."""
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from runtime.browser import collect_step,write_json
from capabilities.rebuild.browser import observed_state,evidence_problems
from browser_evidence import ContentSurface,URL,CONTENT
PROTOCOL=json.loads((Path(__file__).resolve().parents[1]/'contracts/mobile-probes.json').read_text())


def capture_probe(workspace,probe,out):
    from playwright.sync_api import sync_playwright
    root=Path(workspace).resolve();output=root/out;output.mkdir(parents=True,exist_ok=False)
    result={'schema_version':1,'probe':probe,'created_at':datetime.now(timezone.utc).isoformat(),'actions':[],'steps':[],'states':{},'restoration':'Fresh local context; remote state not reset'}
    with sync_playwright()as p:
        browser=p.chromium.launch(executable_path=os.environ.get('REBUILD_BROWSER_EXECUTABLE','/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge'),headless=True)
        try:
            page=browser.new_page(viewport=PROTOCOL['outer_viewport'],locale='zh-CN',timezone_id='Asia/Shanghai');page.set_default_timeout(20000);page.goto(URL,wait_until='load');iframe=page.locator('iframe[src="'+CONTENT+'"]');iframe.wait_for();surface=ContentSurface(iframe.element_handle().content_frame(),iframe);surface.locator('.studio2 button.play').wait_for()
            if surface.locator('button[title="暂停 (空格)"]').count():surface.locator('.studio2').press('Space')
            if probe['kind']=='model':
                select=surface.locator('.mobile-channel select');select.select_option(label='GPT-6.1 sol');surface.wait_for_function('()=>document.querySelector(".mobile-channel select")?.selectedOptions[0]?.textContent==="GPT-6.1 sol"');surface.wait_for_function('()=>document.querySelector(".stage-box")?.innerText.includes("GPT-6.1 sol")');result['actions'].append('Select observed GPT-6.1 sol option')
                if surface.locator('button[title="暂停 (空格)"]').count():surface.locator('.studio2').press('Space')
            elif probe['kind']=='pickem':
                surface.locator('.mainnav a[href="#/pickem"]').press('Enter');surface.get_by_role('button',name='按实力参考一键填完',exact=True).press('Enter');surface.locator('.pk-result').wait_for();result['actions'].append('Open personal prediction and fill by source reference')
            elif probe['kind']=='review':
                surface.locator('a[href*="tab=schedule"]').first.press('Enter');surface.wait_for_function('()=>location.hash.includes("tab=schedule")');surface.locator('a[href*="/match/"]').first.press('Enter');surface.locator('.sh-board').wait_for();surface.locator('.game-tabs .gt').last.press('Enter');surface.wait_for_function('()=>document.querySelector(".game-tabs .gt:last-child")?.classList.contains("on")');surface.locator('.winchart').wait_for();result['actions'].append('Open observed recap, select last game and wait for rendered chart')
            surface.locator(probe['ready']).wait_for();surface.wait_for_function('()=>[...document.images].filter(i=>{const r=i.getBoundingClientRect();return r.width>0&&r.height>0&&r.top<innerHeight&&r.bottom>0}).every(i=>i.complete&&i.naturalWidth>0)')
            surface.locator('#main-content').press('Escape');surface.evaluate('scrollTo(0,0)');clock=surface.locator('a.live-badge').inner_text();surface.wait_for_function('t=>document.querySelector("a.live-badge")?.innerText!==t',arg=clock)
            result['facts']={'viewport':surface.evaluate('({width:innerWidth,height:innerHeight})'),'page_width':surface.evaluate('document.documentElement.scrollWidth'),'title':surface.locator('h1').inner_text()if surface.locator('h1').count()else None,'main_text':surface.locator('#main-content').inner_text(),'visible_controls':surface.locator('button,select,a,input').evaluate_all('(els)=>els.filter(e=>{const r=e.getBoundingClientRect();return r.width>0&&r.height>0}).map(e=>({tag:e.tagName,text:e.textContent.trim(),label:e.getAttribute("aria-label"),value:e.value,rect:[e.getBoundingClientRect().width,e.getBoundingClientRect().height]}))')}
            step={'id':probe['id'],'action':{'type':'observe'},'ready':{'selector':probe['ready'],'state':'visible'},'capture':['dom','text','accessibility','screenshot']};started=time.monotonic();record=collect_step(surface,root,output,0,step,{'main':'#main-content'});record.update(elapsed_seconds=time.monotonic()-started,cleanup='released',receipt_path=str((output/'0000-step.json').relative_to(root)));result['steps'].append(record)
        except Exception as error:result['error']=str(error)
        finally:browser.close()
    for record in result['steps']:
        write_json(root/record['receipt_path'],record);result['states'][record['id']]=observed_state(root,record,record['receipt_path'])
    result['status']='captured'if result['steps']and not result.get('error')and all(not evidence_problems(root,r,r['requested'])for r in result['steps'])else'incomplete';write_json(output/'observed.json',result);return result
