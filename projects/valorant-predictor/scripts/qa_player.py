"""Headless checks against the real generated causal payload, never test trajectories."""
import argparse,functools,http.server,json,threading
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,default=Path('artifacts/valorant-causal-qa'));ap.add_argument('--url');a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 server=None
 if not a.url:
  server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT/'dist')));threading.Thread(target=server.serve_forever,daemon=True).start()
 url=a.url or 'http://127.0.0.1:'+str(server.server_port)+'/'
 r={'status':'fail','checks':{},'errors':[],'http_failures':[]}
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',headless=True)
  try:
   page=b.new_page(viewport={'width':1440,'height':1100},locale='zh-CN');page.set_default_timeout(30000);page.on('pageerror',lambda e:r['errors'].append(str(e)));page.on('response',lambda x:r['http_failures'].append({'status':x.status,'url':x.url}) if x.status>=400 else None)
   def shot(name):
    page.evaluate('async()=>{await document.fonts.ready;await Promise.all([...document.images].map(i=>i.decode().catch(()=>{})))}');page.screenshot(path=str(a.out/name),animations='disabled')
   def seek(t):page.locator('#causal-progress').evaluate('(e,t)=>{e.value=t;e.dispatchEvent(new Event("input",{bubbles:true}))}',t)
   def verify_end_state(part,frame):
    last=next(f for f in reversed(part['frames']) if f['kind']=='round_end' and f['map']==frame['map'])
    observed=page.locator('.causal-map').evaluate('(root)=>Object.fromEntries([...root.querySelectorAll("[data-causal-marker]")].map(n=>[n.dataset.causalMarker,{xy:[parseFloat(n.style.left),parseFloat(n.style.top)],dead:n.classList.contains("dead")}]))')
    assert set(observed)==set(last['positions'])
    for actor,area in last['positions'].items():
     xy=context['maps'][frame['map']]['areas'][area]['xy'];assert all(abs(observed[actor]['xy'][i]-xy[i]*100)<.01 for i in [0,1]);assert observed[actor]['dead']==(actor not in last['alive'])
   page.goto(url+'#/?ai=codex',wait_until='domcontentloaded');page.locator('#prediction-player[data-stage="bp"]').wait_for();data=page.evaluate('async()=>await(await fetch("data/causal/codex.json")).json()');frames=page.evaluate('async data=>(await import("./causal-player.mjs")).causalTimeline(data)',data);context=page.evaluate('async()=>await(await fetch("data/causal/map-context.json")).json()');r['actual_calls']=data['calls'];r['chain_status']=data['status'];r['series_score']=data['state']['series_score']
   assert page.locator('.home-model').count()==4 and page.locator('[data-tab]').count()==0 and page.locator('nav.mainnav a').count()==7;r['checks']['home_one_card_four_models_with_global_navigation']=True
   assert page.locator('[data-channel="codex"] img').get_attribute('src')=='assets/models/gpt-dragon-transparent.png';shot('bp-desktop.png')
   page.locator('#causal-play').click();page.wait_for_timeout(700);page.locator('#causal-play').click();assert float(page.locator('#prediction-player').get_attribute('data-time'))>.3;paused=page.locator('#prediction-player').get_attribute('data-time');page.wait_for_timeout(200);assert page.locator('#prediction-player').get_attribute('data-time')==paused;r['checks']['play_pause']=True
   round_checks=0;terminal_checks=0;maps=set()
   for f in frames:
    if f['kind'] not in ['lineup','round_end','map_end','series_end']:continue
    seek(f['start']+.03)
    if f['kind']=='round_end':
     assert page.locator('#causal-left-score').inner_text()==str(f['round_score'][0]);assert page.locator('#causal-right-score').inner_text()==str(f['round_score'][1]);round_checks+=1
    if f['kind']=='lineup':
     assert page.locator('.causal-marker').count()==10;assert page.locator('.causal-roster button').count()==10;assert page.locator('.causal-map>img').get_attribute('src')=='assets/causal/'+f['map'].lower()+'.png';maps.add(f['map']);shot('case'+str(f['caseIndex'])+'-map-'+f['map'].lower()+'-desktop.png')
    if f['kind']=='map_end':verify_end_state(data.get('cases',[data])[f['caseIndex']],f);terminal_checks+=1
    if f['kind']=='series_end':
     assert f['winner'] in page.locator('.player-finish').inner_text()
     for result in page.locator('.player-series-results b').all_inner_texts():assert f['teams'][0] in result and f['teams'][1] in result
     shot('case'+str(f['caseIndex'])+'-result-desktop.png')
   for chapter in [f for f in frames if f['kind']=='lineup']:
    page.locator('#causal-map-select').select_option(str(chapter['start']));assert page.locator('.causal-scoreboard>div>span').inner_text()==chapter['map'];assert page.locator('.causal-roster.L header>b').inner_text()==chapter['teams'][0];assert page.locator('.causal-roster.R header>b').inner_text()==chapter['teams'][1]
   seek(float(page.locator('#causal-progress').get_attribute('max')));assert '重播' in page.locator('#causal-play').inner_text();page.locator('#causal-play').click();page.wait_for_timeout(100);page.locator('#causal-play').click();assert float(page.locator('#prediction-player').get_attribute('data-time'))<.5;r['checks']['end_replay_resets']=True
   r['checks']['direct_map_switch']=True
   r['checks']['round_scores_from_actual_frames']=round_checks;r['checks']['actual_maps']=sorted(maps)
   movement=next((f for f in frames if f['kind']=='move' and f['end']-f['start']>.25),None)
   if movement:
    seek(movement['start']+.01);page.locator('#causal-play').click();page.wait_for_timeout(60);page.locator('#causal-play').click()
    position=page.locator('[data-causal-marker="'+movement['event']['actor']+'"]').evaluate('(e)=>[parseFloat(e.style.left),parseFloat(e.style.top)]')
    context=page.evaluate('async()=>await(await fetch("data/causal/map-context.json")).json()')
    allowed=[context['maps'][movement['map']]['areas'][id]['xy'] for id in movement['event']['route']]
    assert any(abs(position[0]-xy[0]*100)<.01 and abs(position[1]-xy[1]*100)<.01 for xy in allowed)
    assert page.locator('.causal-route-point').count()==len(movement['event']['route']);r['checks']['movement_only_visits_model_regions']=True;shot('movement-desktop.png')
   death=next((f for f in frames if f['kind']=='kill'),None)
   if death:
    seek(death['start']+.03);assert page.locator('[data-causal-marker="'+death['event']['target']+'"]').evaluate('(e)=>e.classList.contains("dead")');r['checks']['actual_kill_updates_alive_state']=True;shot('contact-desktop.png')
   manifest=page.evaluate('async()=>await(await fetch("data/causal/models.json")).json()')
   for model,row in manifest['models'].items():
    label=page.locator('[data-channel="'+model+'"] .model-overview>small').inner_text()
    if row['status']=='ready':assert '预测冠军' in label and row['champion'] in label
    elif row['status']=='partial':assert '已验算部分' in label
   r['checks']['model_completion_labels_match_manifest']=True
   for model in ['deepseek','doubao','mimo']:
    page.locator('[data-channel="'+model+'"]').click()
    row=manifest['models'][model]
    if not row.get('file'):
     page.locator('#prediction-player[data-status="not_run"]').wait_for();assert page.locator('#causal-play').is_disabled();r['checks'][model+'_pending_honest']=True;continue
    page.locator('#prediction-player[data-stage="bp"]').wait_for()
    model_data=page.evaluate('async model=>await(await fetch("data/causal/"+model+".json")).json()',model)
    model_frames=page.evaluate('async data=>(await import("./causal-player.mjs")).causalTimeline(data)',model_data)
    r['checks'][model+'_cases']=[{'teams':part['teams'],'status':part['status'],'score':part['state']['series_score'],'rounds':sum(f['kind']=='round_end' for f in part['frames'])} for part in model_data.get('cases',[model_data])]
    for f in model_frames:
     if f['kind'] not in ['round_end','map_end','series_end']:continue
     seek(f['start']+.03)
     if f['kind']=='round_end':
      assert page.locator('#causal-left-score').inner_text()==str(f['round_score'][0]);assert page.locator('#causal-right-score').inner_text()==str(f['round_score'][1]);round_checks+=1
     elif f['kind']=='map_end':
      part=model_data.get('cases',[model_data])[f['caseIndex']]
      verify_end_state(part,f);terminal_checks+=1
      for note in part.get('quality_flags',[]):
       if note['map']==f['map']:assert note['message'] in page.locator('#causal-event-copy').inner_text()
     else:
      assert f['winner'] in page.locator('.player-finish').inner_text()
      part=model_data.get('cases',[model_data])[f['caseIndex']]
      for note in part.get('quality_flags',[]):assert note['message'] in page.locator('.player-finish .causal-quality-note').inner_text();r['checks']['reviewed_quality_note_visible']=True
      for result in page.locator('.player-series-results b').all_inner_texts():assert f['teams'][0] in result and f['teams'][1] in result
      shot(model+'-case'+str(f['caseIndex'])+'-result-desktop.png')
    first=next((f for f in model_frames if f['kind']=='round_start'),None)
    if first:seek(first['start']+.03);shot(model+'-desktop.png')
   r['checks']['all_models_round_scores_verified']=round_checks;r['checks']['terminal_map_state_from_last_valid_round']=terminal_checks
   page.locator('[data-channel="codex"]').click();page.locator('#prediction-player[data-stage="bp"]').wait_for();page.set_viewport_size({'width':390,'height':844});page.mouse.move(0,0);shot('bp-mobile.png');assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1');
   if death:seek(death['start']+.03);shot('contact-mobile.png');assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
   r['checks']['mobile_no_overflow']=True
   page.locator('.player-notes>summary').click();assert '没有逐回合外部反馈' in page.locator('#causal-notes').inner_text();r['checks']['batch_boundary_disclosed']=True;r['status']='pass' if not r['errors'] and not r['http_failures'] else 'fail'
  except Exception as e:r['failure']=str(e);page.screenshot(path=str(a.out/'failure.png'))
  finally:b.close()
 if server:server.shutdown()
 (a.out/'observed.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps(r,ensure_ascii=False));return 0 if r['status']=='pass' else 1
if __name__=='__main__':raise SystemExit(main())
