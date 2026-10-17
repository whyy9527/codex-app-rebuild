"""Headless navigation, map-art and retained interaction regression; no model calls."""
import argparse,functools,http.server,json,threading,hashlib
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--url');ap.add_argument('--out',type=Path,required=True);args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True)
 server=None
 if not args.url:
  server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT/'dist')));threading.Thread(target=server.serve_forever,daemon=True).start()
 url=args.url or f'http://127.0.0.1:{server.server_port}/';r={'status':'fail','checks':{},'errors':[],'http_failures':[]};checks=r['checks']
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',headless=True)
  try:
   context=b.new_context(viewport={'width':1440,'height':1100},locale='zh-CN',accept_downloads=True);context.grant_permissions(['clipboard-read','clipboard-write']);page=context.new_page();page.set_default_timeout(45000);page.on('pageerror',lambda e:r['errors'].append(str(e)));page.on('response',lambda v:r['http_failures'].append({'status':v.status,'url':v.url}) if v.status>=400 else None)
   def shot(name):
    page.evaluate('async()=>{await document.fonts.ready;await Promise.all([...document.images].map(i=>i.decode().catch(()=>{})))}');page.screenshot(path=str(args.out/(name+'.png')),full_page=True,animations='disabled')
   def fits():assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
   def home(model='codex'):
    page.goto(url+'#/?ai='+model,wait_until='domcontentloaded');page.locator('.bp-map-card').first.wait_for()
   home();assert page.locator('.mainnav a').count()==7 and page.locator('[data-tab]').count()==0;shot('after-bp-desktop')
   # Verify locally cached artwork against provenance and the already-used minimap UUID.
   art=page.evaluate('async()=>await(await fetch("data/causal/map-art.json")).json()');maps=page.evaluate('async()=>await(await fetch("data/causal/map-context.json")).json()');assert set(art['maps'])==set(maps['maps'])
   for name,row in art['maps'].items():
    assert row['uuid']==maps['maps'][name]['uuid'] and row['source_image'].endswith('/'+row['uuid']+'/splash.png')
    observed=page.evaluate('async file=>{let r=await fetch(file);return [...new Uint8Array(await crypto.subtle.digest("SHA-256",await r.arrayBuffer()))].map(v=>v.toString(16).padStart(2,"0")).join("")}',row['image']);assert observed==row['sha256']
   checks['seven_map_images_match_existing_uuid_and_digest']=True
   n=0
   for model in ['codex','deepseek','doubao','mimo']:
    home(model);data=page.evaluate('async model=>await(await fetch("data/causal/"+model+".json")).json()',model);frames=page.evaluate('async data=>(await import("./causal-player.mjs")).causalTimeline(data)',data)
    for f in [x for x in frames if x['kind']=='bp']:
     page.locator('#causal-progress').evaluate('(e,t)=>{e.value=t;e.dispatchEvent(new Event("input",{bubbles:true}))}',f['start']+.03)
     assert page.locator('.bp-map-card').count()==7 and page.locator('.bp-sequence button').count()==12
     assert page.locator('.bp-feature h3').inner_text()==f['step']['map'];assert page.locator('.bp-feature>img').get_attribute('src')==art['maps'][f['step']['map']]['image']
     assert page.locator('.bp-turn').inner_text().endswith(f['step']['team'] or '自动确定')
     assert page.locator('.bp-map-card.banned').count()==sum(s['kind']=='ban' for s in f['steps'])
     assert page.locator('.bp-map-card.picked').count()==sum(s['kind'] in ['pick','decider'] for s in f['steps'])
     assert page.locator('.bp-map-card.current').get_attribute('data-map')==f['step']['map']
     assert page.locator('.bp-sequence [aria-current="step"] small').inner_text()==str(f['index']+1).zfill(2)
     n+=1
    page.locator('.bp-sequence button').nth(2).click();assert '3 / 12' in page.locator('.bp-turn').inner_text();assert page.locator('#prediction-player').get_attribute('data-playing')=='false'
    page.locator('.bp-map-card[data-map="'+data['cases'][1]['bp']['bans'][0]+'"]').click();assert page.locator('.bp-feature h3').inner_text()==data['cases'][1]['bp']['bans'][0]
   checks['actual_bp_steps_and_states']=n;checks['picture_and_step_click_seek_actual_output']=True
   home();page.locator('.bp-sequence button').nth(2).click();shot('after-pick-desktop');page.locator('.bp-sequence button').nth(3).click();shot('after-side-desktop')
   # Retained interactive pages are reached through the actual restored navigation.
   page.locator('.mainnav a[href="#/pickem"]').click();page.locator('#reference-model').wait_for();page.locator('#reference-model').select_option('deepseek');assert page.locator('#reference-model').input_value()=='deepseek';page.locator('#custom-ranking').click();before=page.locator('.ranking-list li b').all_inner_texts();page.get_by_role('button',name='上移 '+before[-1],exact=True).click();assert page.locator('.ranking-list li b').all_inner_texts()!=before;page.locator('#ranking-use').click();page.locator('#autofill').click();page.locator('#save-pick').click();assert page.evaluate('!!localStorage.getItem("vct-finals-pick")');page.reload();page.locator('#pick-result h2').wait_for();checks['pick_reference_ranking_save_and_reload']=True;shot('pickem-desktop')
   page.locator('#share-pick').click();shared=page.locator('#save-state textarea').input_value() if page.locator('#save-state textarea').count() else page.evaluate('navigator.clipboard.readText()');assert '#/pickem?share=' in shared
   other=context.new_page();other.goto(shared,wait_until='domcontentloaded');other.locator('#pick-result h2').wait_for();other.close();page.locator('#poster-button').click();assert page.locator('#poster').is_visible()
   with page.expect_download() as d:page.locator('#download-poster').click()
   d.value.save_as(str(args.out/'prediction-poster.png'));assert (args.out/'prediction-poster.png').stat().st_size>1000;page.locator('#close-poster').click();checks['share_link_and_poster_download']=True
   page.locator('.mainnav a[href="#/teams"]').click();page.locator('#team-search').fill('VIT');assert page.locator('#team-grid a').count()==1;page.locator('#team-grid a').click();assert 'VIT' in page.locator('main').inner_text();checks['team_search_and_detail']=True
   for route in ['compare','leaderboard','method']:
    page.locator('.mainnav a[href="#/'+route+'"]').click();page.locator('main h1').wait_for();assert page.locator('.mainnav a[aria-current="page"]').get_attribute('href')=='#/'+route;assert '页面不存在' not in page.locator('main').inner_text()
   checks['comparison_ranking_method_routes']=True
   page.locator('.mainnav a[href="#/channel"]').click();page.locator('[data-tab="schedule"]').wait_for();assert page.locator('[data-tab]').count()==7
   for tab in ['schedule','bracket','players','news','analysis','process','prediction']:
    page.locator('[data-tab="'+tab+'"]').click();page.locator('[data-tab="'+tab+'"][aria-selected="true"]').wait_for();assert page.locator('#channel-content').inner_text().strip()
   page.locator('[data-tab="players"]').click();page.locator('#fiction-player-search').fill('no-player-zzzzz');assert page.locator('#fiction-player-results tbody tr').count()==0;page.locator('#fiction-player-search').fill('');page.locator('#fiction-player-team').select_option('VIT');assert page.locator('#fiction-player-results tbody tr').count()>0;checks['seven_channel_tabs_and_player_filters']=True;shot('channel-desktop')
   for width in [320,390,768]:
    page.set_viewport_size({'width':width,'height':844});home();fits();assert page.locator('.mainnav a').count()==7
    for rect in page.locator('.mainnav a').evaluate_all('(els)=>els.map(e=>{let r=e.getBoundingClientRect();return {left:r.left,right:r.right,width:r.width,height:r.height}})'):assert rect['left']>=0 and rect['right']<=width+1 and rect['height']>=30
    assert page.locator('.bp-map-card img').evaluate_all('(els)=>els.every(e=>e.complete&&e.naturalWidth>0&&getComputedStyle(e).objectFit==="cover")')
    page.locator('.bp-sequence button').nth(3).click();fits();shot('after-side-'+str(width));page.locator('.mainnav a[href="#/channel"]').click();page.locator('[data-tab="players"]').click();page.locator('#fiction-player-search').wait_for();fits();shot('channel-'+str(width));page.locator('.mainnav a[href="#/pickem"]').click();page.locator('#custom-ranking').click();page.locator('#ranking-cancel').click();fits()
   checks['mobile_navigation_all_visible_bp_images_proportional_no_overflow']=[320,390,768]
   page.set_viewport_size({'width':390,'height':844});home();page.locator('.bp-sequence button').nth(2).click();shot('after-pick-mobile')
   page.emulate_media(reduced_motion='reduce');assert page.locator('.event-intro').evaluate('(e)=>getComputedStyle(e,"::before").animationName')=='none';checks['reduced_motion_respected']=True
   r['status']='pass' if not r['errors'] and not r['http_failures'] else 'fail'
  except Exception as e:r['failure']=str(e);page.screenshot(path=str(args.out/'failure.png'),full_page=True)
  finally:b.close()
 if server:server.shutdown()
 (args.out/'observed.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps(r,ensure_ascii=False));return 0 if r['status']=='pass' else 1
if __name__=='__main__':raise SystemExit(main())
