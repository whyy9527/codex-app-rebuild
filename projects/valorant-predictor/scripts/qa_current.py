"""Current final batch, historical isolation and personal final vote browser regression."""
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
 url=a.url or f'http://127.0.0.1:{server.server_port}/';result={'status':'fail','checks':{},'errors':[],'http_failures':[]};c=result['checks'];order=['codex','deepseek','mimo','doubao']
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path='/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',headless=True);context=browser.new_context(viewport={'width':1440,'height':1000},permissions=['clipboard-read','clipboard-write']);page=context.new_page();page.set_default_timeout(45000);page.on('pageerror',lambda e:result['errors'].append(str(e)));page.on('response',lambda r:result['http_failures'].append({'status':r.status,'url':r.url}) if r.status>=400 else None)
  def go(route):page.goto(url+'#/'+route,wait_until='domcontentloaded');page.locator('main h1').wait_for()
  def shot(name):page.evaluate('async()=>await document.fonts.ready');page.screenshot(path=str(a.out/(name+'.png')),full_page=True,animations='disabled')
  def choose(id,model):page.locator('#'+id+' [data-model-choice="'+model+'"]').click()
  def cards(id):
   root=page.locator('#'+id);assert root.locator('[data-model-choice]').evaluate_all('els=>els.map(e=>e.dataset.modelChoice)')==order;assert root.locator('img').count()==4;assert root.locator('select').count()==0;assert root.locator('button').count()==4
  try:
   go('compare');page.locator('#current-result-comparison').wait_for();latest=page.evaluate('async()=>await(await fetch("data/gf-postmatch/results.json")).json()');manifest=page.evaluate('async()=>await(await fetch("data/gf-postmatch/models.json")).json()');old=page.evaluate('async()=>await(await fetch("data/current-results.json")).json()');pack=page.evaluate('async()=>await(await fetch("'+manifest['evidence_file']+'")).json()')
   assert page.locator('.current-meta').get_attribute('data-version')==manifest['version'];cards('compare-model')
   for model in order:
    row=page.locator('#current-result-comparison [data-current-model="'+model+'"]');m=latest['models'].get(model)
    assert row.get_attribute('data-version')==manifest['version'];choose('compare-model',model)
    if m:
     part=m['cases'][0];assert row.get_attribute('data-source')==m['source_sha256'];assert row.locator('td').nth(0).inner_text()==' : '.join(map(str,part['score']));assert row.locator('td').nth(1).inner_text()==part['winner'];assert row.locator('.current-round-count').inner_text()==str(m['round_count']);assert page.locator('#current-compare-maps .current-series-card').count()==1;assert page.locator('#current-compare-maps [data-match]').get_attribute('data-match')=='gf'
    else:assert '等待完整结果' in row.inner_text() or '已暂停' in row.inner_text();assert page.locator('#current-compare-maps .current-series-card').count()==0
   assert '597' not in page.locator('.current-compare').inner_text();c['comparison_only_current_final_batch_ready_or_pending']=True;shot('comparison-desktop')
   for model in order:
    go('channel?ai='+model);page.locator('#channel-content').wait_for();cards('home-model-selector');assert page.locator('.current-meta').count()==1;assert page.locator('.channel-event').count()==1;assert page.locator('#channel-content .channel-event').count()==1;assert page.locator('.channel-hub>.channel-event').count()==0;assert page.locator('#channel-content .channel-event [data-official-match]').count()==2;assert 'LOUD vs VIT' in page.locator('.channel-event').inner_text();assert '3 : 1' in page.locator('.channel-event').inner_text();m=latest['models'].get(model)
    if not m:assert page.locator('#channel-content .current-series-card').count()==0;continue
    part=m['cases'][0];assert page.locator('#channel-content .current-series-card').count()==1;assert page.locator('#channel-content [data-source]').get_attribute('data-source')==m['source_sha256'];page.locator('[data-tab="players"]').click();page.locator('#fiction-player-results tbody tr').first.wait_for();assert page.locator('#fiction-player-results tbody tr').count()==len(m['players']);page.locator('#fiction-player-team').select_option('VIT');assert page.locator('#fiction-player-results tbody tr').count()==5
    page.locator('[data-tab="news"]').click();page.locator('#current-report-map').wait_for();assert page.locator('.channel-event').count()==0;assert page.locator('.current-round').count()==part['maps'][0]['round_count'];page.locator('.current-round').first.locator('summary').click();assert page.locator('.current-round').first.locator('li').count()==len(part['maps'][0]['rounds'][0]['events']);page.locator('[data-tab="analysis"]').click();assert 'BP' in page.locator('#channel-content').inner_text()
   c['channel_uses_final_batch_lineups_reports_bp_and_verified_official_facts']=True;shot('channel-desktop')
   go('archive');page.locator('#archive-model').wait_for();cards('archive-model');assert 'VIT 3 : 1 100T' in page.locator('.archive-page').inner_text()
   for model in order:
    choose('archive-model',model);page.wait_for_function('(id)=>location.hash.includes("ai="+id)',arg=model);page.locator('#archive-results [data-channel="'+model+'"]').first.wait_for();assert page.locator('#archive-results .current-series-card').count()==2
    for part in old['models'][model]['cases']:
     card=page.locator('#archive-results [data-match="'+part['id']+'"]');assert card.get_attribute('data-source')==old['models'][model]['source_sha256'];assert ' : '.join(map(str,part['score'])) in card.inner_text()
    row=page.locator('#archive-leaderboard [data-current-model="'+model+'"]');assert row.locator('td').all_inner_texts()==['1','1 / 1' if model=='deepseek' else '0 / 1','1 / 1' if model=='deepseek' else '0 / 1']
   c['all_eight_original_predictions_and_original_accuracy_are_archived']=True;shot('archive-desktop')
   go('leaderboard');page.locator('#current-leaderboard').wait_for();assert page.locator('#current-leaderboard tbody tr').count()==4;assert all('待结算' in s for s in page.locator('#current-leaderboard tbody tr').all_inner_texts());assert '1 / 1' not in page.locator('#current-leaderboard').inner_text();c['current_final_accuracy_waits_for_actual_result']=True
   # A historical vote is never promoted into the new single-final scope.
   old_vote={'version':1,'source_sha256':old['evidence_sha256'],'match_ids':['old-lf','old-gf'],'upperWinner':'G2','lowerWinner':'VIT','lfWinner':'VIT','lfScore':[3,1],'champion':'G2','gfScore':[3,2],'created_at':'2026-10-16T01:00:00Z'};old_bytes=json.dumps(old_vote,separators=(',',':'));page.evaluate('(value)=>{localStorage.setItem("vct-finals-pick",value);localStorage.removeItem("vct-finals-final-pick")}',old_bytes);go('pickem');page.reload();page.locator('#reference-model').wait_for();cards('reference-model');assert page.locator('#pick-result h2').inner_text()=='?';assert page.locator('[data-pick="lf"],#lf-score').count()==0;assert page.locator('#saved-pick-record').count()==1
   for model in order:
    choose('reference-model',model);m=latest['models'].get(model)
    if m:page.locator('#autofill').click();assert page.locator('#pick-result h2').inner_text()==m['cases'][0]['winner']
    else:assert page.locator('#autofill').is_disabled()
   choose('reference-model','codex');page.locator('#reference-model [data-model-choice="codex"]').press('ArrowRight');assert page.locator('#reference-model [aria-pressed="true"]').get_attribute('data-model-choice')=='deepseek'
   for team in ['LOUD','VIT']:
    page.locator('[data-pick="gf"][data-team="'+team+'"]').click()
    for n in [0,1,2]:page.locator('[data-final-score="'+str(n)+'"]').click();assert page.locator('[data-final-score="'+str(n)+'"]').get_attribute('aria-pressed')=='true';assert '3' in page.locator('#pick-result').inner_text()
   page.locator('#save-pick').click();saved=page.evaluate('localStorage.getItem("vct-finals-final-pick")');vote=json.loads(saved);assert vote['version']==2 and vote['teams']==['LOUD','VIT'] and vote['champion']=='VIT' and vote['score']==[2,3];assert page.evaluate('localStorage.getItem("vct-finals-pick")')==old_bytes
   page.reload();page.locator('#reference-model').wait_for();assert page.locator('#pick-result h2').inner_text()=='VIT';assert page.evaluate('localStorage.getItem("vct-finals-final-pick")')==saved
   page.locator('#share-pick').click();shared=page.locator('#save-state textarea').input_value() if page.locator('#save-state textarea').count() else page.evaluate('navigator.clipboard.readText()');other=context.new_page();other.goto(shared,wait_until='domcontentloaded');other.locator('#pick-result h2').wait_for();assert other.locator('#pick-result h2').inner_text()=='VIT';assert page.evaluate('localStorage.getItem("vct-finals-final-pick")')==saved;other.close()
   page.locator('#poster-button').click();assert '10 / 18' in page.locator('#poster-content').inner_text() and '10 / 17' not in page.locator('#poster-content').inner_text()
   with page.expect_download() as download:page.locator('#download-poster').click()
   download.value.save_as(str(a.out/'personal-final-prediction.png'));page.locator('#poster').press('Escape');assert page.locator('#custom-ranking,#ranking-editor,#ranking-import,.rank-editor').count()==0;page.locator('#sim-tab').click();assert page.locator('#personal-simulation').is_visible() and page.locator('#final-vote-panel').is_hidden();cards('reference-model');page.locator('#my-tab').click();assert page.locator('#personal-simulation').is_hidden() and page.locator('#final-vote-panel').is_visible();assert page.evaluate('localStorage.getItem("vct-finals-pick")')==old_bytes;c['final_vote_save_reload_share_poster_keyboard_cards_and_old_record_preservation']=True;shot('pickem-desktop')
   for width in [1440,768,390,320]:
    page.set_viewport_size({'width':width,'height':1000 if width>700 else 844})
    for route,selector in [('?ai=codex','#prediction-player[data-status="ready"]'),('channel?ai=codex','#channel-content'),('compare','#compare-model'),('teams','#team-grid'),('team/VIT','.current-team-block'),('pickem','#reference-model'),('leaderboard','#current-leaderboard'),('method','.current-process'),('archive','#archive-model')]:
     go(route);page.locator(selector).wait_for();assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),(width,route);assert page.locator('select').evaluate_all('els=>els.every(e=>![...e.options].some(o=>["codex","deepseek","mimo","doubao"].includes(o.value)))');assert page.evaluate('localStorage.getItem("vct-finals-pick")')==old_bytes
     if width in [1440,390,320] and route in ['?ai=codex','compare','pickem','channel?ai=codex']:shot((route.split('?')[0] or 'home')+'-'+str(width))
   go('?ai=codex');page.locator('#prediction-player[data-status="ready"]').wait_for();alpha=page.locator('[data-channel="codex"] .model-portrait').evaluate('''async img=>{await img.decode();const c=document.createElement('canvas');c.width=img.naturalWidth;c.height=img.naturalHeight;const x=c.getContext('2d');x.drawImage(img,0,0);const a=(px,py)=>x.getImageData(px,py,1,1).data[3];return {src:img.getAttribute('src'),corners:[a(0,0),a(c.width-1,0),a(0,c.height-1),a(c.width-1,c.height-1)],costume:a(Math.floor(c.width*.5),Math.floor(c.height*.5)),fit:getComputedStyle(img).objectFit};}''');assert alpha['corners']==[0,0,0,0] and alpha['costume']>=250 and alpha['fit']=='contain';assets=page.evaluate('async()=>await(await fetch("data/assets.json")).json()');assert alpha['src']==assets['models']['codex']['portrait'];c['real_alpha_character_costume_preserved']=alpha
   c['all_pages_desktop_mobile_no_overflow_or_native_model_selects']=True
   assert not result['errors'] and not result['http_failures'];result['status']='pass'
  finally:
   (a.out/'observed.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));browser.close()
 if server:server.shutdown()
 print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
