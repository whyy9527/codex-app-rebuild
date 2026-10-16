"""Collect actual candidate browser facts for independent requirement comparison."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from runtime.browser import collect_step, write_json
from capabilities.rebuild.browser import observed_state


def collect(url, out, timeout_ms=20000, browser_args=None):
    from playwright.sync_api import sync_playwright
    root=Path(__file__).resolve().parents[3]
    output=root/out;output.mkdir(parents=True,exist_ok=False)
    result={'schema_version':1,'created_at':datetime.now(timezone.utc).isoformat(),'url':url,'browser_args':browser_args or [],'facts':{},'states':{},'steps':[], 'errors':[]}
    def fact(name,value):result['facts'][name]=value
    def screenshot(page,name):
        path=output/(name+'.png');page.screenshot(path=str(path),full_page=False);return str(path.relative_to(root))
    def capture(page,name):
        page.wait_for_function('() => [...document.querySelectorAll(".stage-scene")].every(e=>e.getAnimations().every(a=>a.playState==="finished"))')
        page.wait_for_function('getComputedStyle(document.querySelector("#toast")).opacity==="0"')
        step={'id':name,'action':{'type':'observe'},'ready':{'selector':'h1','state':'visible'},'capture':['dom','text','screenshot','accessibility']}
        record=collect_step(page,root,output,len(result['steps']),step,{'title':'#main-content h1'})
        record.update(cleanup='released',receipt_path=str((output/(name+'-step.json')).relative_to(root)))
        write_json(root/record['receipt_path'],record);result['steps'].append(record);result['states'][name]=observed_state(root,record,record['receipt_path'])
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=os.environ.get('REBUILD_BROWSER_EXECUTABLE','/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge'),headless=True,args=browser_args or [])
        try:
            context=browser.new_context(viewport={'width':1370,'height':988},locale='zh-CN',timezone_id='Asia/Shanghai',accept_downloads=True)
            context.set_default_timeout(timeout_ms);context.set_default_navigation_timeout(timeout_ms)
            page=context.new_page()
            page.on('pageerror',lambda e:result['errors'].append(str(e)))
            page.goto(url,wait_until='load');page.locator('.channels').wait_for(state='visible')
            page.wait_for_function('() => [...document.querySelectorAll(".portraits img")].every(i=>i.complete&&i.naturalWidth>0)')
            page.locator('.channels [data-channel="deepseek"]').click()
            fact('deepseek_channel',page.locator('#channel-content').inner_text())
            fact('channel_ids',page.locator('.channels [data-channel]').evaluate_all('(els)=>els.map(e=>e.dataset.channel)'))
            fact('portrait_sources',page.locator('.portrait').evaluate_all('(els)=>els.map(e=>({channel:e.dataset.channel,src:e.querySelector("img").getAttribute("src")}))'))
            for channel in ['doubao','mimo']:
                page.locator('.channels [data-channel="'+channel+'"]').click()
                fact(channel+'_channel',page.locator('#channel-content').inner_text())
            fact('codex_card_with_other_selected',page.locator('.forecast-card[href="#/?ai=codex"]').inner_text())
            page.locator('.channels [data-channel="codex"]').click()
            if page.locator('#play[title="暂停 (空格)"]').count():page.locator('.studio').press('Space')
            fact('navigation',page.locator('.mainnav a').all_text_contents())
            fact('channel_count',page.locator('.channels .channel').count())
            fact('hero_images',page.locator('.portraits img').evaluate_all('(images)=>images.map(i=>({src:i.currentSrc,loaded:i.complete&&i.naturalWidth>0}))'))
            page.locator('#main-content').press('Escape')
            page.mouse.move(-1,-1)
            page.evaluate('window.scrollTo(0,0)')
            fact('home_geometry',page.evaluate('() => Object.fromEntries([".topbar",".hero",".channels",".studio"].map(s=>{const r=document.querySelector(s).getBoundingClientRect();return [s,[r.x,r.y,r.width,r.height]]}))'))
            capture(page,'home')
            initial=page.locator('#stage').inner_text();page.locator('#next').click();fact('player_next',{'before':initial,'after':page.locator('#stage').inner_text()})
            page.locator('[data-day="1"]').click();fact('player_day',page.locator('#stage-date').inner_text())
            page.locator('[data-speed="4"]').click();fact('player_speed',page.locator('[data-speed="4"]').get_attribute('class'))
            page.locator('.studio').focus();before=page.locator('#stage').inner_text();page.keyboard.press('ArrowRight');fact('keyboard_next',{'before':before,'after':page.locator('#stage').inner_text()})
            page.locator('#mute').click();fact('mute_saved',page.evaluate('JSON.parse(localStorage.getItem("vct-finals-muted"))'))
            page.reload();page.locator('#mute').wait_for();fact('mute_after_reload',page.locator('#mute').inner_text())
            page.locator('.mainnav a[href="#/pickem"]').click();page.locator('#lower-final').wait_for()
            page.locator('[data-pick="lf"][data-team="LOUD"]').click();page.locator('[data-pick="gf"][data-team="LOUD"]').wait_for();fact('downstream_winner',page.locator('#grand-final').inner_text())
            page.locator('[data-pick="gf"][data-team="LOUD"]').click();page.locator('[data-pick="lf"][data-team="100T"]').click();fact('invalidated_champion',page.locator('#pick-result').inner_text());fact('updated_final',page.locator('#grand-final').inner_text())
            page.locator('#autofill').click();page.locator('#save-pick').click();saved=page.evaluate('JSON.parse(localStorage.getItem("vct-finals-pick"))');fact('saved_pick',saved)
            capture(page,'pickem-complete')
            page.reload();page.locator('#pick-result h2').wait_for();fact('restored_champion',page.locator('#pick-result h2').inner_text())
            page.locator('#share-pick').click()
            link=page.evaluate('navigator.clipboard.readText()') if False else None
            # UI fallback is observable on headless systems without clipboard grant.
            if page.locator('#save-state textarea').count():link=page.locator('#save-state textarea').input_value()
            if not link:
                context.grant_permissions(['clipboard-read','clipboard-write'])
                page.locator('#share-pick').click();link=page.evaluate('navigator.clipboard.readText()')
            fact('shared_link_present',bool(link and '#/pickem?share=' in link))
            shared=context.new_page();shared.goto(link,wait_until='load');shared.locator('#pick-result h2').wait_for();fact('shared_champion',shared.locator('#pick-result h2').inner_text());shared.close()
            page.locator('#poster-button').click();fact('poster_visible',page.locator('#poster').is_visible())
            with page.expect_download() as download:page.locator('#download-poster').click()
            download.value.save_as(str(output/'prediction-poster.png'));fact('poster_download_bytes',(output/'prediction-poster.png').stat().st_size)
            page.locator('#close-poster').click()
            page.locator('#reset').click();fact('reset_save_disabled',page.locator('#save-pick').is_disabled())
            page.locator('.mainnav a[href="#/compare"]').click();page.locator('#distributions').wait_for();fact('compare_pending_cells',page.locator('td').filter(has_text='待预测').count());capture(page,'compare')
            page.locator('.mainnav a[href="#/teams"]').click();page.locator('#team-search').fill('VIT');fact('search_matches',page.locator('#team-grid a').count());page.locator('#team-grid a').click();fact('team_detail',page.locator('main').inner_text());capture(page,'team-detail')
            page.locator('a[href="#/teams"]').last.click();page.locator('#team-search').fill('zzzzzzz');fact('search_empty',page.locator('#team-grid').inner_text())
            page.locator('.mainnav a[href="#/leaderboard"]').click();page.get_by_role('heading',name='等待真实赛果',exact=True).wait_for();fact('leaderboard',page.locator('main').inner_text());capture(page,'leaderboard')
            page.locator('.mainnav a[href="#/method"]').click();page.locator('h1').filter(has_text='AI 赛制介绍').wait_for();capture(page,'method')
            page.locator('footer a[href="#/about"]').first.click();page.locator('h1').filter(has_text='内容、数据与素材说明').wait_for();capture(page,'about')
            mobile=browser.new_context(viewport={'width':390,'height':844},locale='zh-CN',timezone_id='Asia/Shanghai',is_mobile=True,has_touch=True)
            mobile.set_default_timeout(timeout_ms);mobile.set_default_navigation_timeout(timeout_ms)
            m=mobile.new_page();m.goto(url,wait_until='load');m.locator('.channels').wait_for();m.locator("#mobile-model").wait_for();fact('mobile_home_width',m.evaluate('({scroll:document.documentElement.scrollWidth,viewport:innerWidth})'));screenshot(m,'mobile-home')
            m.locator('.mainnav a[href="#/pickem"]').click();m.locator('#autofill').click();m.locator('#save-pick').click();fact('mobile_pick_width',m.evaluate('({scroll:document.documentElement.scrollWidth,viewport:innerWidth})'));fact('mobile_pick_champion',m.locator('#pick-result h2').inner_text());screenshot(m,'mobile-pickem')
            m.goto(url+'#/pickem?share=invalid',wait_until='load');m.locator('#lower-final').wait_for();fact('invalid_share_feedback',m.locator('#toast').inner_text())
            mobile.close();context.close()
        except Exception as error:result['error']=str(error)
        finally:browser.close()
    write_json(output/'observed.json',result)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--url',default='http://127.0.0.1:5173/');parser.add_argument('--out',required=True);parser.add_argument('--timeout-ms',type=int,default=20000);parser.add_argument('--browser-arg',action='append',default=[]);args=parser.parse_args()
    result=collect(args.url,args.out,args.timeout_ms,args.browser_arg);print(json.dumps({'facts':len(result['facts']),'error':result.get('error'),'page_errors':result['errors'],'out':args.out},ensure_ascii=False));raise SystemExit(1 if result.get('error') or result['errors'] else 0)
