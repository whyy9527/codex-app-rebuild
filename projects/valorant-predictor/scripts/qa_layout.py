"""Collect matching main-page typography/layout and fully rendered screenshots."""
import argparse
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_evidence import ContentSurface, URL, CONTENT

MEASURE = '''selectors => Object.fromEntries(Object.entries(selectors).map(([key,selector])=>[key,[...document.querySelectorAll(selector)].map(e=>{
 const r=e.getBoundingClientRect(),s=getComputedStyle(e);
 return {rect:[r.x,r.y,r.width,r.height],size:s.fontSize,weight:s.fontWeight,lineHeight:s.lineHeight,spacing:s.letterSpacing,color:s.color,background:s.backgroundImage,text:e.innerText,loaded:e.tagName==='IMG'?e.complete&&e.naturalWidth>0:null};
})]))'''


def collect(out):
    root=Path(__file__).resolve().parents[3];output=root/out;output.mkdir(parents=True,exist_ok=False)
    result={'reference':{},'candidate':{},'errors':[]}
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=os.environ.get('REBUILD_BROWSER_EXECUTABLE','/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge'),headless=True)
        try:
            context=browser.new_context(viewport={'width':1440,'height':1000},locale='zh-CN',timezone_id='Asia/Shanghai')
            for mode in ['reference','candidate']:
                page=context.new_page();page.set_default_timeout(25000);page.on('pageerror',lambda e:result['errors'].append(str(e)))
                if mode=='candidate':page.set_viewport_size(result['reference']['viewport'])
                page.goto(URL if mode=='reference' else 'http://127.0.0.1:5173/',wait_until='load')
                if mode=='reference':
                    iframe=page.locator('iframe[src="'+CONTENT+'"]');iframe.wait_for();surface=ContentSurface(iframe.element_handle().content_frame(),iframe)
                    surface.locator('.channels .ch').nth(1).click();studio='.studio2'
                    surface.wait_for_function('document.querySelector(".stage-box")?.innerText.includes("GPT-6.1 sol")')
                else:surface=page;studio='.studio'
                surface.locator(studio+' button.play').wait_for()
                if surface.locator('button[title="暂停 (空格)"]').count():surface.locator(studio).press('Space')
                result[mode]['viewport']=surface.evaluate('({width:innerWidth,height:innerHeight})')
                def capture(name,selectors):
                    surface.evaluate('document.fonts.ready')
                    surface.wait_for_function('() => [...document.images].filter(i=>{const r=i.getBoundingClientRect();return r.width>0&&r.height>0&&r.top<innerHeight&&r.bottom>0}).every(i=>i.complete&&i.naturalWidth>0)')
                    surface.wait_for_function('() => [...document.querySelectorAll(".stage-scene,.stage-box .scene")].every(e=>e.getAnimations().every(a=>a.playState==="finished"))')
                    surface.locator('#main-content').press('Escape');surface.evaluate('scrollTo(0,0)')
                    result[mode][name]=surface.evaluate(MEASURE,selectors)
                    surface.screenshot(path=str(output/(mode+'-'+name+'.png')))
                capture('home',{'header':'.topbar','hero':'.home-head'if mode=='reference'else'.hero','hero_title':'.home-head h1'if mode=='reference'else'.hero h1','hero_copy':'.home-head-in p'if mode=='reference'else'.hero-top p','channels':'.channels .ch'if mode=='reference'else'.channels .channel','portraits':'.lineup img'if mode=='reference'else'.portraits img','studio':studio,'stage':'.stage-box','sidebar':'.today'if mode=='reference'else'.schedule','tabs':'.studio-tabs'if mode=='reference'else'.tabs','tab_buttons':'.studio-tabs>a'if mode=='reference'else'.tabs button','notice':'.studio-section>.source-pill'if mode=='reference'else'#channel-content>.notice'})
                for route in ['compare','teams','pickem','leaderboard','method']:
                    surface.locator('.mainnav a[href="#/'+route+'"]').click();surface.locator('#main-content h1').wait_for()
                    capture(route,{'title':'.band h1 .cn'if mode=='reference'else'.page-title-cn','band':'.band'if mode=='reference'else'.page-head','nav':'.mainnav a','main':'#main-content'})
                page.close()
            context.close()
        except Exception as error:result['error']=str(error)
        finally:browser.close()
    (output/'observed.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args();r=collect(a.out);print(json.dumps({'error':r.get('error'),'page_errors':r['errors'],'pages':{k:len(r[k])for k in ['reference','candidate']}}));raise SystemExit(1 if r.get('error')or r['errors']else 0)
