"""Visual regression: current routes, channel tabs, four models and full scrolling."""
import argparse,functools,http.server,json,threading
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
MODELS=['codex','deepseek','mimo','doubao'];TABS=['schedule','bracket','players','news','analysis','process','prediction']
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*a):pass

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--url');ap.add_argument('--out',required=True,type=Path);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True);server=None
 if not a.url:
  server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT/'dist')));threading.Thread(target=server.serve_forever,daemon=True).start()
 url=a.url or f'http://127.0.0.1:{server.server_port}/';report={'status':'fail','states':[],'errors':[]}
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',headless=True)
  try:
   for width in [1440,390,430]:
    c=b.new_context(viewport={'width':width,'height':960 if width>700 else 844},reduced_motion='reduce');p=c.new_page();p.set_default_timeout(60000);p.on('pageerror',lambda e:report['errors'].append(str(e)));p.goto(url+'#/channel?ai=codex&tab=schedule',wait_until='domcontentloaded');p.locator('.channel-event').wait_for()
    if p.locator('.ticker-close').count():p.locator('.ticker-close').click()
    def settle():
     p.evaluate('async()=>{await document.fonts.ready;await Promise.all([...document.images].filter(i=>i.offsetParent!==null).map(i=>i.decode().catch(()=>{})));await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))}')
    def go(route,selector):
     p.evaluate('r=>location.hash="#/"+r',route);p.wait_for_timeout(60);p.locator(selector).first.wait_for();settle()
    def capture(name):
     settle();p.mouse.move(0,0);p.wait_for_timeout(100);assert p.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),(width,name,'overflow')
     geometry=p.locator('.model-choice').evaluate_all('els=>els.map(e=>{const r=e.getBoundingClientRect(),i=e.querySelector(".model-portrait"),ir=i.getBoundingClientRect(),h=e.querySelector("h2").getBoundingClientRect(),s=getComputedStyle(i);return {model:e.dataset.modelChoice,fit:s.objectFit,image_inside:ir.top>=r.top-1&&ir.bottom<=r.bottom+1&&ir.left>=r.left-1&&ir.right<=r.right+1,name_inside:h.top>=r.top-1&&h.bottom<=r.bottom+1,text:e.innerText}})')
     assert all(g['image_inside'] and g['name_inside'] and g['fit']=='contain' for g in geometry),(width,name,geometry)
     if name.startswith('channel-'):
      assert p.locator('.current-meta').count()==1,(name,'duplicate batch bars')
      if width<701:
       assert p.locator('.page-head').bounding_box()['height']<115
       assert p.locator('.home-tabs button').evaluate_all('els=>els.every(e=>e.getBoundingClientRect().height>=42)')
     assert p.locator('.official-score').evaluate_all('els=>els.every(e=>e.getBoundingClientRect().height<=parseFloat(getComputedStyle(e).lineHeight)+1)'),(width,name,'wrapped score')
     folder=a.out/str(width)/name;folder.mkdir(parents=True,exist_ok=True);p.evaluate('scrollTo(0,0)');p.screenshot(path=str(folder/'full.png'),full_page=True,animations='disabled',timeout=20000)
     height=p.evaluate('document.documentElement.scrollHeight');vp=p.viewport_size['height'];ys=list(range(0,max(1,height-vp+1),int(vp*.72)));ys.append(max(0,height-vp));walk=[]
     for index,y in enumerate(dict.fromkeys(ys)):
      p.evaluate('y=>scrollTo(0,y)',y);p.evaluate('()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))');p.screenshot(path=str(folder/f'scroll-{index:02d}.png'),animations='disabled',timeout=20000);walk.append(p.evaluate('scrollY'))
     horizontal=[]
     for i,table in enumerate(p.locator('.table-wrap').all()):
      if not table.is_visible() or not table.evaluate('e=>e.scrollWidth>e.clientWidth+1'):continue
      table.scroll_into_view_if_needed();table.evaluate('e=>e.scrollLeft=e.scrollWidth');p.screenshot(path=str(folder/f'horizontal-{i:02d}.png'),animations='disabled',timeout=20000);assert table.evaluate('e=>e.scrollLeft+e.clientWidth>=e.scrollWidth-1');horizontal.append(i);table.evaluate('e=>e.scrollLeft=0')
     report['states'].append({'width':width,'state':name,'model_cards':geometry,'height':height,'scroll_positions':walk,'horizontal_tables_checked':horizontal,'last_viewport_reaches_end':walk[-1]+vp>=height-1});assert walk[-1]+vp>=height-1
    for tab in TABS:
     go('channel?ai=codex&tab='+tab,'#channel-content');p.locator('[data-tab="'+tab+'"][aria-selected="true"]').wait_for()
     for model in MODELS:
      p.locator('#home-model-selector [data-model-choice="'+model+'"]').click();settle();assert p.locator('#home-model-selector [aria-pressed="true"]').get_attribute('data-model-choice')==model;capture('channel-'+tab+'-'+model)
    for model in MODELS:
     go('?ai='+model,'#prediction-player[data-status="ready"][data-model="'+model+'"]')
     if p.locator('#prediction-player').get_attribute('data-playing')=='true':p.locator('#causal-play').click()
     capture('home-'+model)
    for route,selector,picker in [('compare','#current-result-comparison','compare-model'),('archive','#archive-results','archive-model')]:
     go(route,selector)
     for model in MODELS:
      p.locator('#'+picker+' [data-model-choice="'+model+'"]').click();settle();capture(route+'-'+model)
    go('pickem','#reference-model')
    for tab in ['my-tab','sim-tab']:
     p.locator('#'+tab).click()
     for model in MODELS:
      p.locator('#reference-model [data-model-choice="'+model+'"]').click();capture('pickem-'+tab+'-'+model)
    p.locator('#my-tab').click()
    for team in ['LOUD','VIT']:
     p.locator('[data-pick="gf"][data-team="'+team+'"]').click()
     for score in [0,1,2]:
      p.locator('[data-final-score="'+str(score)+'"]').click();p.locator('#save-pick').click();p.reload();p.locator('#reference-model').wait_for();assert p.locator('#pick-result h2').inner_text()==team;assert p.locator('[data-final-score="'+str(score)+'"]').get_attribute('aria-pressed')=='true'
    p.wait_for_timeout(3300);capture('pickem-saved')
    for route,selector in [('teams','#team-grid'),('team/LOUD','.current-team-block'),('team/VIT','.current-team-block'),('team/100T','.current-team-block'),('team/G2','.current-team-block'),('leaderboard','#current-leaderboard'),('method','.current-process'),('about','.article')]:
     go(route,selector);capture(route.replace('/','-'))
    c.close()
   assert not report['errors'];report['status']='pass'
  finally:(a.out/'observed.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));b.close()
 if server:server.shutdown()
 print(json.dumps({'status':report['status'],'states':len(report['states']),'errors':report['errors']},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
