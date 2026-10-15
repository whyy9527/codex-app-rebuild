"""Reference adapter for the same main journeys in contracts/scenarios.json."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from runtime.browser import collect_step, write_json
from capabilities.rebuild.browser import observed_state
from browser_evidence import ContentSurface, URL, CONTENT


def collect(out):
    from playwright.sync_api import sync_playwright
    root=Path(__file__).resolve().parents[3];output=root/out;output.mkdir(parents=True,exist_ok=False)
    result={'schema_version':1,'created_at':datetime.now(timezone.utc).isoformat(),'url':URL,'facts':{},'states':{},'steps':[],'errors':[]}
    def fact(key,value):result['facts'][key]=value
    def capture(surface,name):
        step={'id':name,'action':{'type':'observe'},'ready':{'selector':'#main-content h1','state':'visible'},'capture':['dom','text','screenshot','accessibility']}
        record=collect_step(surface,root,output,len(result['steps']),step,{'title':'#main-content h1','nav':'.mainnav'})
        record.update(cleanup='released',receipt_path=str((output/(name+'-step.json')).relative_to(root)))
        write_json(root/record['receipt_path'],record);result['steps'].append(record);result['states'][name]=observed_state(root,record,record['receipt_path'])
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=os.environ.get('REBUILD_BROWSER_EXECUTABLE','/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge'),headless=True)
        try:
            context=browser.new_context(viewport={'width':1440,'height':1000},locale='zh-CN',timezone_id='Asia/Shanghai')
            page=context.new_page();page.set_default_timeout(25000);page.goto(URL,wait_until='load')
            iframe=page.locator('iframe[src="'+CONTENT+'"]');iframe.wait_for();surface=ContentSurface(iframe.element_handle().content_frame(),iframe)
            surface.locator('.channels .ch').first.wait_for();surface.locator('.studio2 button.play').wait_for()
            if surface.locator('button[title="暂停 (空格)"]').count():surface.locator('.studio2').press('Space')
            fact('navigation',surface.locator('.mainnav a').all_text_contents());fact('channel_count',surface.locator('.channels .ch').count())
            surface.wait_for_function('() => [...document.images].filter(i=>{const r=i.getBoundingClientRect();return r.top<innerHeight&&r.bottom>0&&r.width>0}).every(i=>i.complete&&i.naturalWidth>0)')
            surface.locator('#main-content').press('Escape')
            surface.evaluate('window.scrollTo(0,0)')
            fact('home_geometry',surface.evaluate('() => Object.fromEntries([".topbar",".home-head",".channels",".studio2"].map(s=>{const r=document.querySelector(s).getBoundingClientRect();return [s,[r.x,r.y,r.width,r.height]]}))'))
            capture(surface,'home')
            before=surface.locator('.stage-box').inner_text();surface.locator('button[aria-label="下一步"]').click();fact('player_next',{'before':before,'after':surface.locator('.stage-box').inner_text()})
            surface.get_by_role('button',name='10/18',exact=True).click();fact('player_day',surface.locator('.stage-box').inner_text())
            surface.get_by_role('button',name='4x',exact=True).click();fact('player_speed',surface.get_by_role('button',name='4x',exact=True).get_attribute('class'))
            surface.locator('.studio2').focus();before=surface.locator('.stage-box').inner_text();page.keyboard.press('ArrowRight');fact('keyboard_next',{'before':before,'after':surface.locator('.stage-box').inner_text()})
            # Sound is only a toggle/persistence observation here, not audio equality.
            mute=surface.get_by_role('button',name='静音',exact=True)
            if mute.count():mute.click()
            fact('mute_saved',surface.evaluate('localStorage.getItem("s16-sound")'))
            surface.locator('.mainnav a[href="#/pickem"]').click();surface.get_by_role('heading',name='我来预测',exact=True).wait_for()
            surface.get_by_role('button',name='按实力参考一键填完',exact=True).click();surface.locator('.pk-result').wait_for(state='visible')
            fact('saved_pick',surface.evaluate('JSON.parse(localStorage.getItem("s16-my-picks"))'))
            capture(surface,'pickem-complete')
            page.reload(wait_until='load');iframe=page.locator('iframe[src="'+CONTENT+'"]');iframe.wait_for();surface=ContentSurface(iframe.element_handle().content_frame(),iframe)
            surface.locator('.mainnav a[href="#/pickem"]').click();surface.locator('.pk-result').wait_for();fact('restored_champion',surface.locator('.pk-champ>b').inner_text())
            fact('poster_platform_dependency',surface.get_by_role('button',name='关注我解锁生成海报',exact=False).count()>0)
            for route,title in [('/compare','数据对比'),('/teams','参赛战队'),('/leaderboard','谁最准'),('/method','S16 · AI 赛制介绍')]:
                surface.locator('.mainnav a[href="#'+route+'"]').click();surface.get_by_role('heading',name=title,exact=True).wait_for();capture(surface,route.strip('/'))
                if route=='/leaderboard':fact('leaderboard',surface.locator('#main-content').inner_text())
            surface.locator('a[href="#/about"]').last.click();surface.locator('#main-content h1').wait_for();capture(surface,'about')
            fact('scope','Original full LoL tournament; candidate only final two VALORANT matches by explicit user instruction')
            context.close()
        except Exception as error:result['error']=str(error)
        finally:browser.close()
    write_json(output/'observed.json',result)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',required=True);args=parser.parse_args();result=collect(args.out)
    print(json.dumps({'facts':len(result['facts']),'error':result.get('error'),'out':args.out},ensure_ascii=False));raise SystemExit(1 if result.get('error') else 0)
