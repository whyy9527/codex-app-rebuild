"""Version-isolated final playback and original archive replay, using headless Edge."""
import argparse,functools,http.server,json,threading
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*a):pass

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--url');ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True);server=None
 if not a.url:
  server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT/'dist')));threading.Thread(target=server.serve_forever,daemon=True).start()
 url=a.url or f'http://127.0.0.1:{server.server_port}/';result={'status':'fail','checks':{},'errors':[],'http_failures':[]};c=result['checks']
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path='/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',headless=True);page=browser.new_page(viewport={'width':1440,'height':1100});page.set_default_timeout(45000);page.on('pageerror',lambda e:result['errors'].append(str(e)));page.on('response',lambda r:result['http_failures'].append(r.url) if r.status>=400 else None)
  def go(route=''):page.goto(url+'#/'+route,wait_until='domcontentloaded')
  def state():return page.locator('#prediction-player').evaluate('e=>({playing:e.dataset.playing,time:+e.dataset.time,speed:+e.dataset.speed})')
  def shot(name):page.screenshot(path=str(a.out/(name+'.png')),full_page=True,animations='disabled')
  try:
   go();page.locator('#home-model-selector').wait_for();versions=page.evaluate('async()=>await(await fetch("data/gf-postmatch/models.json")).json()');assert page.locator('#home-model-selector [data-model-choice]').evaluate_all('els=>els.map(e=>e.dataset.modelChoice)')==['codex','deepseek','mimo','doubao']
   if versions['models']['deepseek']['status']=='ready':page.locator('#prediction-player[data-model="deepseek"][data-status="ready"]').wait_for()
   else:page.locator('#final-pending[data-model="deepseek"]').wait_for();assert page.locator('.selected-champion').inner_text()=='待更新'
   c['default_deepseek_uses_only_current_batch_or_truthful_pending']=True
   for model,row in versions['models'].items():
    go('?ai='+model);page.reload(wait_until='domcontentloaded')
    if row['status']!='ready':page.locator('#final-pending[data-model="'+model+'"]').wait_for();assert not page.locator('#prediction-player').count();continue
    page.locator('#prediction-player[data-status="ready"][data-model="'+model+'"]').wait_for();assert state()['speed']==4 and state()['playing']=='true';initial=state()['time'];page.wait_for_function('(initial)=>+document.querySelector("#prediction-player").dataset.time>initial',timeout=5000,arg=initial);assert page.locator('.selected-champion').inner_text()==row['winner'];assert set(page.locator('#causal-map-select option').evaluate_all('els=>els.map(e=>e.dataset.case)'))=={'1'}
    page.locator('#causal-play').click();paused=state();page.wait_for_timeout(180);assert state()==paused;choices=page.locator('#causal-map-select option').evaluate_all('els=>els.map(e=>e.value)');page.locator('#causal-map-select').select_option(choices[1]);assert page.locator('.causal-marker').count()==10
    page.locator('[data-causal-speed="16"]').click();page.locator('#causal-play').click();page.wait_for_timeout(220);page.locator('#causal-play').click();assert state()['speed']==16 and state()['playing']=='false';assert page.locator('.causal-marker').count()==10;page.locator('#causal-next').click();assert page.locator('.causal-marker').count()==10
    page.locator('.actual-sources summary').click();pack=page.evaluate('async f=>await(await fetch(f)).json()',versions['evidence_file']);assert page.locator('.actual-sources ul a').evaluate_all('els=>els.map(e=>e.href)')==[s['url'] for s in pack['sources']];shot(model+'-map-desktop');page.reload();page.locator('#prediction-player[data-status="ready"]').wait_for();assert state()['speed']==4 and state()['playing']=='true'
   c['every_ready_model_plays_own_final_maps_at_4x_16x_pause_scrub_and_reload']=True;c['pending_models_never_reuse_original_results']=True
   go('archive?replay=1&ai=deepseek&at=900');page.locator('#prediction-player[data-status="ready"]').wait_for();assert set(page.locator('#causal-map-select option').evaluate_all('els=>els.map(e=>e.dataset.case)'))=={'0','1'};assert state()['time']>=900;shot('archive-replay-desktop');go('?ai=doubao&at=900');page.locator('#prediction-player[data-status="ready"]').wait_for();assert '/archive?' in page.url and state()['time']>=900;c['historical_two_series_replay_and_old_bookmarks_preserved']=True
   for width in [320,390,768]:
    page.set_viewport_size({'width':width,'height':844});go('?ai=codex');page.locator('#prediction-player[data-status="ready"]').wait_for();page.locator('#causal-play').click();choices=page.locator('#causal-map-select option').evaluate_all('els=>els.map(e=>e.value)');page.locator('#causal-map-select').select_option(choices[1]);assert page.locator('.causal-marker').count()==10;assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1');shot('final-map-'+str(width))
   c['real_map_markers_and_controls_fit_mobile']=True;assert not result['errors'] and not result['http_failures'];result['status']='pass'
  finally:
   (a.out/'observed.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));browser.close()
 if server:server.shutdown()
 print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
