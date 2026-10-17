"""Check the selected model's large upper-right portrait without obscuring replay UI."""
import argparse,functools,http.server,json,threading
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--url');ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True);server=None
 if not a.url:
  server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT/'dist')));threading.Thread(target=server.serve_forever,daemon=True).start()
 url=a.url or f'http://127.0.0.1:{server.server_port}/';r={'status':'fail','checks':{},'errors':[],'http_failures':[]};c=r['checks'];layouts=[]
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',headless=True)
  try:
   page=b.new_page(viewport={'width':1440,'height':1100});page.set_default_timeout(60000);page.on('pageerror',lambda e:r['errors'].append(str(e)));page.on('response',lambda v:r['http_failures'].append({'status':v.status,'url':v.url}) if v.status>=400 else None)
   page.goto(url+'#/?ai=codex',wait_until='domcontentloaded');page.locator('#prediction-player[data-status="ready"]').wait_for();assert page.locator('#prediction-player').get_attribute('data-playing')=='true';page.locator('#causal-play').click();assets=page.evaluate('async()=>await(await fetch("data/assets.json")).json()')
   def shot(name):
    page.evaluate('''async()=>{await Promise.race([document.fonts.ready,new Promise(r=>setTimeout(r,3000))]);await Promise.all([...document.images].map(i=>Promise.race([i.decode().catch(()=>{}),new Promise(r=>setTimeout(r,5000))])))}''');page.screenshot(path=str(a.out/(name+'.png')),full_page=True,animations='disabled')
   for model in ['codex','deepseek','doubao','mimo']:
    page.locator('[data-channel="'+model+'"]').click();page.locator('#prediction-player[data-status="ready"][data-model="'+model+'"]').wait_for();figure=page.locator('.selected-character[data-selected-model="'+model+'"]');assert figure.count()==1;portrait=figure.locator('img');assert portrait.get_attribute('src')==assets['models'][model]['portrait'];portrait.evaluate('async i=>await i.decode()');assert page.locator('#prediction-player').get_attribute('data-playing')=='false'
    for width in [1440,768,390,320]:
     page.set_viewport_size({'width':width,'height':1100 if width==1440 else 844});page.locator('#causal-progress').evaluate('(e)=>{e.value=0;e.dispatchEvent(new Event("input",{bubbles:true}))}')
     geometry=figure.evaluate('''el=>{const rect=e=>{const r=e.getBoundingClientRect();return {left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height}},img=el.querySelector('img'),window=el.querySelector('.selected-character-window');return {figure:rect(el),window:rect(window),image:rect(img),natural:[img.naturalWidth,img.naturalHeight],fit:getComputedStyle(img).objectFit,overflow:getComputedStyle(window).overflow,deck:rect(document.querySelector('#home-model-selector')),controls:rect(document.querySelector('.player-controls')),screen:rect(document.querySelector('#causal-screen')),thumbnail:rect(document.querySelector('.home-model.on img'))}}''')
     assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1');assert geometry['figure']['left']>=geometry['deck']['right'] and geometry['figure']['right']<=width;assert geometry['figure']['bottom']<=geometry['controls']['top'] and geometry['figure']['bottom']<=geometry['screen']['top'];assert geometry['image']['height']>=geometry['thumbnail']['height']*2.4;assert geometry['fit']=='contain' and geometry['overflow']=='hidden'
     assert geometry['image']['top']>=geometry['window']['top']-1 and geometry['image']['bottom']<=geometry['window']['bottom']+1;assert geometry['image']['left']>=geometry['window']['left']-1 and geometry['image']['right']<=geometry['window']['right']+1
     layouts.append({'model':model,'viewport':width,**geometry})
     if width in [1440,390]:shot(model+'-bp-'+str(width))
     page.locator('#causal-map-select').select_option(index=1);page.locator('.causal-map').wait_for();assert page.locator('.causal-marker').count()==10;assert page.locator('.selected-character').count()==1;assert figure.bounding_box()['y']+figure.bounding_box()['height']<=page.locator('.causal-scoreboard').bounding_box()['y'];shot(model+'-map-'+str(width))
     for selector in ['#causal-play','[data-causal-speed="16"]']:
      button=page.locator(selector);button.scroll_into_view_if_needed();assert button.evaluate('(e)=>{const r=e.getBoundingClientRect(),n=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);return n===e||e.contains(n)}')
     page.locator('[data-causal-speed="16"]').click();assert page.locator('#prediction-player').get_attribute('data-playing')=='false';page.locator('#causal-play').click();before=float(page.locator('#prediction-player').get_attribute('data-time'));page.wait_for_timeout(100);page.locator('#causal-play').click();assert float(page.locator('#prediction-player').get_attribute('data-time'))>before;assert page.locator('#prediction-player').get_attribute('data-speed')=='16';page.evaluate('scrollTo(0,0)')
    page.locator('#causal-progress').evaluate('(e)=>{e.value=e.max;e.dispatchEvent(new Event("input",{bubbles:true}))}');page.locator('.player-finish').wait_for();assert portrait.get_attribute('src')==assets['models'][model]['portrait']
   c['four_models_use_existing_correct_portraits_in_bp_map_and_result']=True;c['upper_right_large_character_above_controls_and_map']=True;c['all_characters_contained_without_extra_crop']=True;c['four_viewports_no_overflow_and_controls_receive_clicks']=[1440,768,390,320];c['autoplay_pause_speed_and_model_switch_preserved']=True;r['layouts']=layouts;r['status']='pass' if not r['errors'] and not r['http_failures'] else 'fail'
  except Exception as e:r['failure']=str(e);page.screenshot(path=str(a.out/'failure.png'),full_page=True)
  finally:b.close()
 if server:server.shutdown()
 (a.out/'observed.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='layouts'},ensure_ascii=False));return 0 if r['status']=='pass' else 1
if __name__=='__main__':raise SystemExit(main())
