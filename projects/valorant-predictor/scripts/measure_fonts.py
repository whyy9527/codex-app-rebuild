import argparse,json,time
from pathlib import Path
from playwright.sync_api import sync_playwright
p=argparse.ArgumentParser();p.add_argument('--url',required=True);p.add_argument('--out',required=True);p.add_argument('--width',type=int,default=1440);a=p.parse_args()
out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
result={'url':a.url,'viewport':{'width':a.width,'height':1400},'cache':'new isolated context, browser cache disabled via CDP','phases':{},'errors':[]}
with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path='/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',headless=True)
 page=b.new_page(viewport=result['viewport']);page.set_default_timeout(210000)
 cdp=page.context.new_cdp_session(page);cdp.send('Network.enable');cdp.send('Network.setCacheDisabled',{'cacheDisabled':True})
 page.on('pageerror',lambda e:result['errors'].append(str(e)))
 page.add_init_script('''window.measurements={shifts:[],paints:[]};new PerformanceObserver(l=>{for(const e of l.getEntries())if(!e.hadRecentInput)window.measurements.shifts.push(e.value)}).observe({type:'layout-shift',buffered:true});new PerformanceObserver(l=>window.measurements.paints.push(...l.getEntries().map(e=>({name:e.name,startTime:e.startTime})))).observe({type:'paint',buffered:true});''')
 try:
  page.goto(a.url,wait_until='domcontentloaded')
  page.locator('#tactical-replay').wait_for()
  result['phases']['body_and_controls_ready_ms']=page.evaluate('performance.now()')
  result['phases']['font_status_at_body_ready']=page.evaluate('document.fonts.status')
  result['body_font']=page.locator('body').evaluate('e=>getComputedStyle(e).fontFamily')
  (out/'progress.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
  page.locator('.tactical-map-image').evaluate('i=>i.decode()')
  result['phases']['map_image_decoded_ms']=page.evaluate('performance.now()')
  page.wait_for_function("[...document.querySelectorAll('#tactical-replay img')].every(i=>i.complete&&i.naturalWidth>0)")
  result['phases']['map_and_all_agent_images_ready_ms']=page.evaluate('performance.now()')
  page.locator('#tactical-play').click();page.wait_for_function("document.querySelector('#tactical-replay').dataset.playing==='true'")
  result['phases']['play_control_responded_ms']=page.evaluate('performance.now()');page.locator('#tactical-play').click()
  page.wait_for_function("document.fonts.status==='loaded'")
  result['phases']['fonts_settled_ms']=page.evaluate('performance.now()')
  result['fonts']=page.evaluate("[...document.fonts].map(f=>({family:f.family,status:f.status,display:f.display}))")
  result['font_resources']=page.evaluate("performance.getEntriesByType('resource').filter(r=>r.name.includes('/fonts/')).map(r=>({url:r.name,duration_ms:r.duration,transfer_bytes:r.transferSize,encoded_bytes:r.encodedBodySize,decoded_bytes:r.decodedBodySize}))")
  result['paints']=page.evaluate('window.measurements.paints');result['cumulative_layout_shift']=page.evaluate('window.measurements.shifts.reduce((a,b)=>a+b,0)')
  result['geometry']=page.evaluate('({width:innerWidth,scroll:document.documentElement.scrollWidth})')
  result['revision']=page.evaluate("fetch('/revision.json',{cache:'no-store'}).then(r=>r.ok?r.json():null)") if a.url.startswith('https:') else None
  result['phases']['total_ms']=page.evaluate('performance.now()')
  page.locator('#tactical-replay').screenshot(path=str(out/'tactical.png'),timeout=30000)
  result['status']='pass'
 except Exception as error:result['status']='fail';result['error']=str(error)
 finally:
  (out/'observed.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');b.close()
print(json.dumps(result,ensure_ascii=False))
if result['status']!='pass':raise SystemExit(1)
