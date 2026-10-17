"""Verify the factual final, historical archive and unchanged model evidence in a headless browser."""
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
 url=a.url or f'http://127.0.0.1:{server.server_port}/';r={'status':'fail','checks':{},'errors':[],'http_failures':[]};c=r['checks']
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',headless=True)
  try:
   context=browser.new_context(viewport={'width':1440,'height':1100},locale='zh-CN');page=context.new_page();page.set_default_timeout(45000);page.on('pageerror',lambda e:r['errors'].append(str(e)));page.on('response',lambda v:r['http_failures'].append({'status':v.status,'url':v.url}) if v.status>=400 else None)
   def go(route=''):page.goto(url+'#/'+route,wait_until='domcontentloaded')
   def ready():page.locator('#prediction-player[data-status="ready"][data-model="deepseek"]').wait_for()
   def state():return page.locator('#prediction-player').evaluate('e=>({playing:e.dataset.playing,time:+e.dataset.time,speed:+e.dataset.speed})')
   def fits():assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
   def shot(name):
    page.evaluate('''async()=>{await Promise.race([document.fonts.ready,new Promise(r=>setTimeout(r,3000))]);await Promise.all([...document.images].map(i=>Promise.race([i.decode().catch(()=>{}),new Promise(r=>setTimeout(r,5000))])))}''');page.screenshot(path=str(a.out/(name+'.png')),full_page=True,animations='disabled')
   go();ready();initial=state();assert initial['playing']=='true' and initial['speed']==4;page.wait_for_timeout(250);assert state()['time']>initial['time'];assert page.locator('main h1').inner_text().split()==['LOUD','VS','VIT'];assert '10 月 18 日 14:00' in page.locator('.event-scope').inner_text();assert all(x=='1' for x in page.locator('#causal-map-select option').evaluate_all('els=>els.map(e=>e.dataset.case)'));assert page.locator('#causal-map-select option').count()>1;c['default_home_plays_only_existing_deepseek_grand_final_at_4x']=True
   order=page.locator('#home-model-selector a').evaluate_all('els=>els.map(e=>e.dataset.channel)');assert order==['codex','deepseek','mimo','doubao'];assert page.locator('.selected-champion').inner_text()=='LOUD';assert float(page.locator('.selected-champion').evaluate('e=>parseFloat(getComputedStyle(e).fontSize)'))>=30;c['oral_script_order_and_larger_champion']=order
   page.locator('#causal-play').click();paused=state();page.wait_for_timeout(180);assert state()==paused;page.locator('[data-causal-speed="8"]').click();assert state()['speed']==8 and state()['playing']=='false';page.reload(wait_until='domcontentloaded');ready();assert state()['speed']==4 and state()['playing']=='true';page.locator('#causal-play').click();shot('final-home-desktop');c['manual_pause_and_refresh_default_4x_preserved']=True
   options=page.locator('#causal-map-select option').evaluate_all('els=>els.map(e=>e.value)');page.locator('#causal-map-select').select_option(options[1]);assert page.locator('.causal-marker').count()==10;page.locator('#causal-next').click();page.locator('#causal-play').click();page.wait_for_timeout(220);page.locator('#causal-play').click();assert page.locator('.causal-marker').count()==10;shot('final-map-desktop');c['map_switch_lineups_next_and_play_pause']=True
   for model in ['codex','mimo','doubao']:
    page.locator('#home-model-selector [data-channel="'+model+'"]').click();page.locator('#final-pending[data-model="'+model+'"]').wait_for();assert not page.locator('#prediction-player').count();assert page.locator('.selected-champion').inner_text()=='待更新';assert '不替换队名' in page.locator('#final-pending').inner_text();assert page.locator('.final-pending a.btn').get_attribute('href')=='#/archive?ai='+model
   c['three_mismatched_finals_explicitly_pending_without_relabeling']=True;shot('pending-model-desktop')
   page.locator('#home-model-selector [data-channel="deepseek"]').click();ready();assert state()['playing']=='false';page.locator('.actual-sources summary').click();pack=page.evaluate('async()=>await(await fetch("data/evidence-v2.json")).json()');sources=page.locator('.actual-sources ul a').evaluate_all('els=>els.map(a=>a.href)');assert sources==[s['url'] for s in pack['sources']];assert '不代表模型另行实时浏览' in page.locator('.actual-sources').inner_text();c['displayed_input_sources_match_frozen_evidence_exactly']=len(sources)
   page.locator('.final-reference a[href="#/archive"]').click();page.locator('#archive-model').wait_for();assert 'VIT 3 : 1 100T' in page.locator('.archive-page').inner_text();summary=page.evaluate('async()=>await(await fetch("data/current-results.json")).json()');archive=page.evaluate('async()=>await(await fetch("data/archive/2026-10-17.json")).json()')
   for model in order:
    page.locator('#archive-model').select_option(model);page.locator('#archive-model').wait_for();m=summary['models'][model];assert page.locator('#archive-results .current-series-card').count()==2
    for part in m['cases']:
     card=page.locator('#archive-results [data-match="'+part['id']+'"]');assert card.get_attribute('data-source')==archive['models'][model]['source_sha256'];assert ' : '.join(map(str,part['score'])) in card.inner_text();assert all(t in card.inner_text() for t in part['teams'])
   assert archive['actual_result']['maps']==[{'map':'Split','score':[5,13]},{'map':'Summit','score':[13,10]},{'map':'Lotus','score':[13,11]},{'map':'Ascent','score':[13,9]}];c['all_eight_original_series_remain_archived_with_hash_bindings']=True;shot('archive-desktop');page.locator('#archive-results [data-match="gf"] .btn').click();page.locator('#prediction-player[data-status="ready"]').wait_for();assert set(page.locator('#causal-map-select option').evaluate_all('els=>els.map(e=>e.dataset.case)'))=={'0','1'};assert '总决赛' in page.locator('#causal-map-select option:checked').inner_text();c['archive_bookmark_opens_original_two_series_replay']=True;go('?ai=doubao&at=900');page.locator('#prediction-player[data-status="ready"]').wait_for();assert '/archive?' in page.url and float(page.locator('#prediction-player').get_attribute('data-time'))>=900;c['old_home_bookmarks_redirect_to_original_archive']=True
   go('leaderboard');page.locator('#current-leaderboard').wait_for();assert page.locator('#current-leaderboard [data-current-model]').evaluate_all('els=>els.map(e=>e.dataset.currentModel)')==order
   for model in order:
    values=page.locator('#current-leaderboard [data-current-model="'+model+'"] td').all_inner_texts();assert values[0]=='1';assert values[1]==('1 / 1' if model=='deepseek' else '0 / 1');assert values[2]==('1 / 1' if model=='deepseek' else '0 / 1')
   c['only_deepseek_hits_actual_winner_and_exact_score']=True;shot('settlement-desktop')
   for width in [320,390,768]:
    page.set_viewport_size({'width':width,'height':844})
    for route,selector in [('', '#prediction-player[data-status="ready"]'),('archive','#archive-model'),('leaderboard','#current-leaderboard'),('?ai=codex','#final-pending')]:
     go(route);page.locator(selector).wait_for();fits();assert page.locator('.creator-platforms a').count()==3;assert '主页未解析' not in page.locator('footer').inner_text();assert not page.locator('.current-source').count()
    if width==390:
     go();ready();page.locator('#causal-play').click() if state()['playing']=='true' else None;shot('final-home-mobile');go('archive');page.locator('#archive-model').wait_for();shot('archive-mobile')
   c['home_pending_archive_and_settlement_responsive_at_320_390_768']=True;assert not r['errors'] and not r['http_failures'];r['status']='pass'
  except Exception as e:
   import traceback
   r['failure']=traceback.format_exc();page.screenshot(path=str(a.out/'failure.png'),full_page=True)
  finally:browser.close()
 if server:server.shutdown()
 (a.out/'observed.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps(r,ensure_ascii=False));return 0 if r['status']=='pass' else 1
if __name__=='__main__':raise SystemExit(main())
