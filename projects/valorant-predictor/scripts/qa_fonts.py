from pathlib import Path
import json,argparse
from playwright.sync_api import sync_playwright
p=argparse.ArgumentParser();p.add_argument('--url',required=True);p.add_argument('--out',required=True);a=p.parse_args();out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
r={'url':a.url,'checks':[],'page_errors':[],'normal_font_requests':[]}
def check(value,name):
 if not value:raise AssertionError(name)
 r['checks'].append(name)
with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path='/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',headless=True)
 try:
  ctx=b.new_context(viewport={'width':1440,'height':1400});page=ctx.new_page();page.set_default_timeout(60000)
  page.on('pageerror',lambda e:r['page_errors'].append(str(e)))
  page.on('request',lambda q:r['normal_font_requests'].append(q.url) if '/fonts/' in q.url else None)
  page.goto(a.url,wait_until='domcontentloaded');page.locator('#tactical-replay').wait_for();page.wait_for_function("[...document.querySelectorAll('#tactical-replay img')].every(i=>i.complete&&i.naturalWidth)")
  page.wait_for_function("document.fonts.status==='loaded'")
  check(not any('OPPO' in url or 'MiSans' in url for url in r['normal_font_requests']),'no OPPO or MiSans download on a fresh visit')
  check(all('swap'==x for x in page.evaluate('[...document.fonts].map(f=>f.display)')),'remaining small custom fonts retain nonblocking swap display')
  page.evaluate('new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
  page.locator('#tactical-replay').screenshot(path=str(out/'desktop.png'))
  session=ctx.new_cdp_session(page);session.send('DOM.enable');session.send('CSS.enable');doc=session.send('DOM.getDocument');node=session.send('DOM.querySelector',{'nodeId':doc['root']['nodeId'],'selector':'.tactical-disclosure'});r['rendered_chinese_fonts']=session.send('CSS.getPlatformFontsForNode',{'nodeId':node['nodeId']})['fonts']
  check(any(f['glyphCount']>0 and not f['isCustomFont'] for f in r['rendered_chinese_fonts']),'Chinese paragraph is rendered by installed system glyphs')
  for width in [320,390,768,1440]:
   page.set_viewport_size({'width':width,'height':1700 if width<700 else 1400})
   check(page.evaluate('document.documentElement.scrollWidth<=innerWidth'),f'no document overflow at {width}px')
   check(page.locator('[data-marker]').count()==10,f'ten tactical agents retained at {width}px')
   page.locator('#tactical-play').click();check(page.locator('#tactical-replay').get_attribute('data-playing')=='true',f'play control works at {width}px');page.locator('#tactical-play').click()
   if width==390:
    page.evaluate('new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
    page.locator('#tactical-replay').screenshot(path=str(out/'mobile.png'))
  ctx.close()
  # Fault injection is behavioral only, not substituted visual evidence.
  ctx=b.new_context(viewport={'width':390,'height':844});page=ctx.new_page();page.set_default_timeout(60000)
  session=ctx.new_cdp_session(page);session.send('Network.enable');session.send('Network.setBlockedURLs',{'urls':['*assets/fonts/*']})
  page.goto(a.url,wait_until='domcontentloaded');page.locator('#tactical-replay').wait_for();page.locator('.tactical-map-image').evaluate('i=>i.decode()')
  check(page.locator('.tactical-disclosure').is_visible(),'Chinese body remains visible when all web fonts are unavailable')
  page.locator('#tactical-play').click();check(page.locator('#tactical-replay').get_attribute('data-playing')=='true','map controls respond when all web fonts are unavailable')
  check(page.evaluate('document.documentElement.scrollWidth<=innerWidth'),'font failure has no mobile horizontal overflow')
  ctx.close();check(not r['page_errors'],'no normal-mode JavaScript errors');r['status']='pass'
 except Exception as e:r['status']='fail';r['error']=str(e)
 finally:b.close();(out/'observed.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(r,ensure_ascii=False))
if r['status']!='pass':raise SystemExit(1)
