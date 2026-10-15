"""Collect real rendered navigation typography in matching content viewports."""
import argparse
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_evidence import URL,CONTENT

MEASURE='''() => [...document.querySelectorAll('.mainnav a')].map(e=>{const s=getComputedStyle(e),r=e.getBoundingClientRect(),range=document.createRange();range.selectNodeContents(e);const t=range.getBoundingClientRect();return {text:e.textContent.trim(),font:s.fontFamily,size:s.fontSize,weight:s.fontWeight,lineHeight:s.lineHeight,rect:[r.x,r.y,r.width,r.height],glyph:[t.width,t.height]}})'''


def collect(out):
    root=Path(__file__).resolve().parents[3];output=root/out;output.mkdir(parents=True,exist_ok=False);result={}
    with sync_playwright()as p:
        b=p.chromium.launch(executable_path=os.environ.get('REBUILD_BROWSER_EXECUTABLE','/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge'),headless=True)
        try:
            context=b.new_context(locale='zh-CN',timezone_id='Asia/Shanghai',viewport={'width':1440,'height':1000});source=context.new_page();source.goto(URL,wait_until='load');iframe=source.locator('iframe[src="'+CONTENT+'"]');iframe.wait_for();frame=iframe.element_handle().content_frame();frame.locator('.mainnav').wait_for();frame.evaluate('document.fonts.ready');result['reference']=frame.evaluate(MEASURE);size=frame.evaluate('({width:innerWidth,height:innerHeight})');result['content_viewport']=size
            page=context.new_page();page.set_viewport_size(size);page.goto('http://127.0.0.1:5173/',wait_until='load');page.locator('.mainnav').wait_for();page.evaluate('document.fonts.ready');result['candidate']=page.evaluate(MEASURE)
            for key,target in [('reference',frame),('candidate',page)]:
                try:
                    session=context.new_cdp_session(target);session.send('DOM.enable');session.send('CSS.enable');doc=session.send('DOM.getDocument');nodes=session.send('DOM.querySelectorAll',{'nodeId':doc['root']['nodeId'],'selector':'.mainnav a'});result[key+'_rendered_fonts']=[session.send('CSS.getPlatformFontsForNode',{'nodeId':n})for n in nodes['nodeIds']]
                except Exception as error:result[key+'_font_inspection_error']=str(error)
        except Exception as error:result['error']=str(error)
        finally:b.close()
    (output/'observed.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args();r=collect(a.out);print(json.dumps({'viewport':r.get('content_viewport'),'error':r.get('error'),'font_errors':[r.get('reference_font_inspection_error'),r.get('candidate_font_inspection_error')]}));raise SystemExit(1 if r.get('error')else 0)
