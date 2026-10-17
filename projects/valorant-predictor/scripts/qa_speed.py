"""Verify real playback rates and deterministically exercise every 16x frame in a browser."""
import argparse,functools,http.server,json,threading
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
CLOCK='''(()=>{let now=0,id=0;const q=new Map();Object.defineProperty(performance,'now',{value:()=>now});window.requestAnimationFrame=fn=>{q.set(++id,fn);return id};window.cancelAnimationFrame=id=>q.delete(id);window.__clock={step(ms){now+=ms;const pending=[...q.values()];q.clear();for(const fn of pending)fn(now);},pending(){return [...q.values()].filter(fn=>fn.name==='tick').length}}})()'''
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--url');ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True);server=None
 if not a.url:
  server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT/'dist')));threading.Thread(target=server.serve_forever,daemon=True).start()
 url=a.url or f'http://127.0.0.1:{server.server_port}/';r={'status':'fail','checks':{},'errors':[],'http_failures':[]};c=r['checks']
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',headless=True)
  try:
   context=b.new_context(viewport={'width':1440,'height':1100},locale='zh-CN');page=context.new_page();page.set_default_timeout(45000)
   def watch(page):
    page.on('pageerror',lambda e:r['errors'].append(str(e)));page.on('response',lambda v:r['http_failures'].append({'status':v.status,'url':v.url}) if v.status>=400 else None)
   def ready(page,model='codex'):
    page.goto(url+'#/?ai='+model,wait_until='domcontentloaded');page.locator('#prediction-player[data-status="ready"]').wait_for();page.locator('[data-causal-speed="16"]:enabled').wait_for()
    if page.locator('#prediction-player').get_attribute('data-playing')=='true':page.locator('#causal-play').click()
    page.locator('#causal-progress').evaluate('(e)=>{e.value=0;e.dispatchEvent(new Event("input",{bubbles:true}))}')
   def shot(page,name):
    page.evaluate('async()=>{await document.fonts.ready;await Promise.all([...document.images].map(i=>i.decode().catch(()=>{})))}');page.screenshot(path=str(a.out/name),full_page=True,animations='disabled')
   watch(page);ready(page);assert page.locator('[data-causal-speed]').all_inner_texts()==['1×','2×','4×','8×','16×'];measured=[]
   for rate in [1,2,4,8,16]:
    page.locator('[data-causal-speed="'+str(rate)+'"]').click();start=page.locator('#prediction-player').get_attribute('data-time');page.wait_for_timeout(100);assert page.locator('#prediction-player').get_attribute('data-time')==start
    page.locator('#causal-play').click();before=page.evaluate('({time:+document.querySelector("#prediction-player").dataset.time,wall:performance.now()})');page.wait_for_timeout(450);after=page.evaluate('({time:+document.querySelector("#prediction-player").dataset.time,wall:performance.now()})');page.locator('#causal-play').click();actual=(after['time']-before['time'])/((after['wall']-before['wall'])/1000);assert rate*.75<actual<rate*1.25,(rate,actual);measured.append({'rate':rate,'observed_timeline_seconds_per_real_second':round(actual,3)})
   c['native_clock_actual_speed']=measured;c['paused_rate_changes_keep_exact_progress']=True
   page.locator('#causal-play').click();page.wait_for_timeout(100);before=float(page.locator('#prediction-player').get_attribute('data-time'));page.locator('[data-causal-speed="4"]').click();after=float(page.locator('#prediction-player').get_attribute('data-time'));assert after>=before and page.locator('#prediction-player').get_attribute('data-playing')=='true';page.locator('#causal-play').click();c['changing_rate_while_playing_preserves_progress_and_play_state']=True;context.close()
   context=b.new_context(viewport={'width':1440,'height':1100},locale='zh-CN');context.add_init_script(CLOCK);page=context.new_page();page.set_default_timeout(45000);watch(page);ready(page)
   page.locator('[data-causal-speed="16"]').click();page.locator('#causal-play').click();assert page.evaluate('__clock.pending()')==1
   for i in range(8):page.locator('[data-causal-speed="'+str([4,8,16][i%3])+'"]').click();assert page.evaluate('__clock.pending()')==1
   page.evaluate('__clock.step(50)');before=float(page.locator('#prediction-player').get_attribute('data-time'));page.locator('#causal-play').click();assert page.evaluate('__clock.pending()')==0;page.evaluate('__clock.step(200)');assert float(page.locator('#prediction-player').get_attribute('data-time'))==before;page.locator('[data-causal-speed="16"]').click();page.locator('#causal-play').click();assert page.evaluate('__clock.pending()')==1;page.locator('[data-channel="deepseek"]').click();page.locator('#prediction-player[data-model="deepseek"][data-status="ready"]').wait_for();assert page.evaluate('__clock.pending()')==0;assert page.locator('#prediction-player').get_attribute('data-speed')=='16';assert page.locator('#prediction-player').get_attribute('data-playing')=='false';assert float(page.locator('#prediction-player').get_attribute('data-time'))==0
   c['rate_switch_pause_resume_and_model_switch_no_duplicate_animation_loop']=True;c['model_switch_retains_rate_and_starts_new_model_paused']=True
   complete=[]
   for model in ['codex','deepseek','doubao','mimo']:
    ready(page,model);page.locator('[data-causal-speed="16"]').click();page.evaluate('''()=>{window.__frames=[];window.__observer=new MutationObserver(()=>{});__observer.observe(document.querySelector('#prediction-player'),{attributes:true,attributeOldValue:true,attributeFilter:['data-frame']});}''');page.locator('#causal-play').click()
    result=page.evaluate('''async model=>{const data=await(await fetch('data/causal/'+model+'.json')).json(),frames=(await import('./causal-player.mjs')).causalTimeline(data),root=document.querySelector('#prediction-player');let ticks=0,maxPending=0;while(root.dataset.playing==='true'&&ticks<10000){maxPending=Math.max(maxPending,__clock.pending());__clock.step(50);for(const record of __observer.takeRecords()){const i=Number(record.oldValue);if(__frames.at(-1)!==i)__frames.push(i);}ticks++;}const last=Number(root.dataset.frame);if(__frames.at(-1)!==last)__frames.push(last);__observer.disconnect();return {model,frames:frames.length,visited:__frames,expected:frames.map((_,i)=>i),ticks,maxPending,pending:__clock.pending(),time:+root.dataset.time,total:frames.at(-1).end,playing:root.dataset.playing,winner:data.cases.at(-1).state.winner,score:data.cases.at(-1).state.series_score,result:document.querySelector('.player-finish').innerText};}''',model)
    assert result['visited']==result['expected'],(model,'missing frame',next((i for i,(x,y) in enumerate(zip(result['visited'],result['expected'])) if x!=y),None));assert result['maxPending']==1 and result['pending']==0 and result['playing']=='false';assert result['winner'] in result['result'];assert ' : '.join(str(x) for x in result['score']) in result['result'];assert abs(result['time']-result['total'])<.02;result.pop('visited');result.pop('expected');complete.append(result)
   c['full_four_model_16x_browser_replay']=complete
   ready(page);page.locator('[data-causal-speed="16"]').click();page.locator('#causal-map-select').select_option(index=1);shot(page,'speed-16-desktop.png')
   for width in [320,390,768]:
    page.set_viewport_size({'width':width,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
    for rate in [4,8,16]:
     page.locator('[data-causal-speed="'+str(rate)+'"]').click();assert page.locator('[data-causal-speed="'+str(rate)+'"]').get_attribute('aria-pressed')=='true'
    bounds=page.locator('[data-causal-speed]').evaluate_all('(els)=>els.map(e=>{const r=e.getBoundingClientRect();return {left:r.left,right:r.right,width:r.width,height:r.height}})');assert all(v['left']>=0 and v['right']<=width+1 for v in bounds)
    if width<=700:assert all(v['width']>=44 and v['height']>=40 for v in bounds)
    shot(page,'speed-16-'+str(width)+'.png')
   c['all_speed_controls_visible_and_touch_sized']=[320,390,768];r['status']='pass' if not r['errors'] and not r['http_failures'] else 'fail'
  except Exception as e:r['failure']=str(e);page.screenshot(path=str(a.out/'failure.png'),full_page=True)
  finally:b.close()
 if server:server.shutdown()
 (a.out/'observed.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps(r,ensure_ascii=False));return 0 if r['status']=='pass' else 1
if __name__=='__main__':raise SystemExit(main())
