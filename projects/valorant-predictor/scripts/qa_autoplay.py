"""Exercise initial autoplay, deliberate pauses, mount races and every real model frame."""
import argparse,functools,http.server,json,threading
from pathlib import Path
from playwright.sync_api import sync_playwright
from qa_speed import CLOCK
ROOT=Path(__file__).resolve().parents[1]
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
AUDIO='''(()=>{window.__autoAudio={contexts:0,mediaPlays:0};for(const name of ['AudioContext','webkitAudioContext'])if(window[name]){const Original=window[name];window[name]=new Proxy(Original,{construct(target,args){__autoAudio.contexts++;return Reflect.construct(target,args)}})}const original=HTMLMediaElement.prototype.play;HTMLMediaElement.prototype.play=function(...args){__autoAudio.mediaPlays++;return original.apply(this,args)}})()'''
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--url');ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True);server=None
 if not a.url:
  server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT/'dist')));threading.Thread(target=server.serve_forever,daemon=True).start()
 url=a.url or f'http://127.0.0.1:{server.server_port}/';r={'status':'fail','checks':{},'errors':[],'http_failures':[]};c=r['checks']
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',headless=True)
  try:
   def watch(page):
    page.set_default_timeout(60000);page.on('pageerror',lambda e:r['errors'].append(str(e)));page.on('response',lambda v:r['http_failures'].append({'status':v.status,'url':v.url}) if v.status>=400 else None)
   def ready(page,model='codex'):page.locator('#prediction-player[data-status="ready"][data-model="'+model+'"]').wait_for();page.locator('[data-causal-speed="16"]:enabled').wait_for()
   def state(page):return page.locator('#prediction-player').evaluate('(e)=>({playing:e.dataset.playing,time:+e.dataset.time,speed:e.dataset.speed,model:e.dataset.model})')
   ctx=b.new_context(viewport={'width':1440,'height':1100});ctx.add_init_script(AUDIO);page=ctx.new_page();watch(page);page.goto(url+'#/?ai=codex',wait_until='domcontentloaded');ready(page);first=state(page);assert first['playing']=='true';page.wait_for_timeout(350);assert state(page)['time']>first['time'];assert page.evaluate('__autoAudio')=={'contexts':0,'mediaPlays':0};c['first_load_autoplays_without_audio']=True
   page.reload(wait_until='domcontentloaded');ready(page);assert state(page)['playing']=='true';page.wait_for_timeout(200);assert state(page)['time']>0;assert page.evaluate('__autoAudio')=={'contexts':0,'mediaPlays':0};c['refresh_autoplays_without_audio']=True
   page.locator('#causal-play').click();paused=state(page);page.wait_for_timeout(250);assert state(page)==paused and paused['playing']=='false';page.locator('[data-causal-speed="16"]').click();page.wait_for_timeout(150);assert state(page)['time']==paused['time'] and state(page)['playing']=='false';c['manual_pause_and_paused_speed_change_stay_paused']=True
   page.locator('[data-channel="codex"]').click();ready(page);assert state(page)['playing']=='false';page.locator('[data-channel="deepseek"]').click();ready(page,'deepseek');assert state(page)['playing']=='false' and state(page)['speed']=='16';page.locator('[data-channel="codex"]').click();ready(page);assert state(page)['playing']=='false';page.locator('.mainnav a[href="#/compare"]').click();page.locator('#current-result-comparison').wait_for();page.locator('.mainnav a[href="#/"]').click();ready(page);assert state(page)['playing']=='false';c['same_model_rerender_model_switch_and_return_home_do_not_restart']=True
   page.locator('#causal-play').click();page.wait_for_timeout(120);before=state(page);page.locator('[data-causal-speed="4"]').click();after=state(page);assert after['playing']=='true' and after['time']>=before['time'];page.wait_for_timeout(120);assert state(page)['time']>after['time'];page.locator('#causal-play').click();page.screenshot(path=str(a.out/'autoplay-controls-desktop.png'),full_page=True);c['manual_resume_and_running_speed_change_preserve_playback']=True;ctx.close()
   ctx=b.new_context(viewport={'width':390,'height':844});ctx.add_init_script(AUDIO);page=ctx.new_page();watch(page);page.goto(url+'#/?ai=mimo',wait_until='domcontentloaded');ready(page,'mimo');assert state(page)['playing']=='true';assert page.evaluate('__autoAudio')=={'contexts':0,'mediaPlays':0};page.locator('#causal-play').click();paused=state(page);page.wait_for_timeout(150);assert state(page)==paused;assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1');page.screenshot(path=str(a.out/'autoplay-controls-mobile.png'),full_page=True);c['mobile_selected_model_autoplay_and_pause']=True;ctx.close()
   ctx=b.new_context();ctx.add_init_script(CLOCK);page=ctx.new_page();watch(page);page.goto(url+'#/?ai=codex',wait_until='domcontentloaded');ready(page);assert state(page)['playing']=='true' and page.evaluate('__clock.pending()')==1;complete=[]
   for model in ['codex','deepseek','doubao','mimo']:
    if model!='codex':
     page.locator('[data-channel="'+model+'"]').click();ready(page,model);assert state(page)['playing']=='false' and page.evaluate('__clock.pending()')==0
    page.locator('[data-causal-speed="16"]').click();page.evaluate('''()=>{window.__frames=[];window.__observer=new MutationObserver(()=>{});__observer.observe(document.querySelector('#prediction-player'),{attributes:true,attributeOldValue:true,attributeFilter:['data-frame']});}''')
    if state(page)['playing']=='false':page.locator('#causal-play').click()
    result=page.evaluate('''async model=>{const data=await(await fetch('data/causal/'+model+'.json')).json(),frames=(await import('./causal-player.mjs')).causalTimeline(data),root=document.querySelector('#prediction-player');let ticks=0,maxPending=0;while(root.dataset.playing==='true'&&ticks<10000){maxPending=Math.max(maxPending,__clock.pending());__clock.step(50);for(const record of __observer.takeRecords()){const i=Number(record.oldValue);if(__frames.at(-1)!==i)__frames.push(i);}ticks++;}const last=Number(root.dataset.frame);if(__frames.at(-1)!==last)__frames.push(last);__observer.disconnect();return {model,frames:frames.length,visited:__frames,expected:frames.map((_,i)=>i),maxPending,pending:__clock.pending(),playing:root.dataset.playing,winner:data.cases.at(-1).state.winner,score:data.cases.at(-1).state.series_score,result:document.querySelector('.player-finish').innerText};}''',model)
    assert result['visited']==result['expected'] and result['maxPending']==1 and result['pending']==0 and result['playing']=='false';assert result['winner'] in result['result'] and ' : '.join(map(str,result['score'])) in result['result'];result.pop('visited');result.pop('expected');complete.append(result)
   c['initial_autoplay_and_manual_model_replays_visit_every_frame_once_in_order']=complete;ctx.close()
   ctx=b.new_context();ctx.add_init_script(CLOCK);held=[];ctx.route('**/data/causal/codex.json',lambda route:held.append(route));page=ctx.new_page();watch(page);page.goto(url+'#/?ai=codex',wait_until='domcontentloaded');page.locator('#prediction-player[data-model="codex"]').wait_for()
   for _ in range(600):
    if held:break
    page.wait_for_timeout(100)
   assert held,'Expected the first raw model request to remain in flight';page.locator('[data-channel="deepseek"]').click();ready(page,'deepseek');assert state(page)['playing']=='true' and page.evaluate('__clock.pending()')==1
   for route in held:route.continue_()
   page.wait_for_timeout(200);page.evaluate('__clock.step(100)');page.evaluate('__clock.step(100)');assert state(page)['model']=='deepseek' and state(page)['playing']=='true' and page.evaluate('__clock.pending()')==1;page.locator('#causal-play').click();assert page.evaluate('__clock.pending()')==0;c['stale_async_model_mount_cannot_steal_player_or_create_second_loop']=True;ctx.close()
   r['status']='pass' if not r['errors'] and not r['http_failures'] else 'fail'
  except Exception as e:r['failure']=str(e);page.screenshot(path=str(a.out/'failure.png'),full_page=True)
  finally:b.close()
 if server:server.shutdown()
 (a.out/'observed.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps(r,ensure_ascii=False));return 0 if r['status']=='pass' else 1
if __name__=='__main__':raise SystemExit(main())
