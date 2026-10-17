"""Cross-page current-data, user-record preservation and transparent-asset browser regression."""
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
 url=a.url or f'http://127.0.0.1:{server.server_port}/';r={'status':'fail','checks':{},'errors':[],'http_failures':[],'legacy_requests':[]};c=r['checks'];selectors={'channel':'#channel-content .current-series-card','compare':'#current-result-comparison','teams':'#team-search','pickem':'#reference-model','leaderboard':'#current-leaderboard','method':'.current-process'}
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',headless=True)
  try:
   context=b.new_context(viewport={'width':1440,'height':1100},locale='zh-CN',accept_downloads=True);context.grant_permissions(['clipboard-read','clipboard-write']);page=context.new_page();page.set_default_timeout(45000)
   def watch(page):
    page.on('pageerror',lambda e:r['errors'].append(str(e)));page.on('response',lambda v:r['http_failures'].append({'status':v.status,'url':v.url}) if v.status>=400 else None)
   def block_old(route):r['legacy_requests'].append(route.request.url);route.abort()
   for pattern in ['**/data/forecast-v2/**','**/data/*-forecast.json','**/data/*-fiction.json','**/data/model-forecasts.json','**/data/model-fiction.json']:context.route(pattern,block_old)
   watch(page)
   def go(route,query=''):
    page.goto(url+'#/'+route+query,wait_until='domcontentloaded');page.locator(selectors[route]).first.wait_for()
   def clean_public_ui(page):
    assert not page.locator('.current-source').count()
    assert not page.locator('a[href]').evaluate_all("els=>els.some(a=>/data\\/(?:causal\\/(?:codex|deepseek|doubao|mimo)\\.json|forecast-v2\\/|[^/]*-fiction\\.json|tactical\\/[^/]*-plan\\.json)/.test(a.getAttribute('href')))")
    assert '原始输出' not in page.locator('main').inner_text()
   def shot(page,name):
    clean_public_ui(page)
    page.wait_for_function('!document.querySelector("#toast.show")');page.evaluate('''async()=>{await Promise.race([document.fonts.ready,new Promise(r=>setTimeout(r,3000))]);await Promise.all([...document.images].filter(i=>new URL(i.src,location.href).origin===location.origin).map(i=>Promise.race([i.decode().catch(()=>{}),new Promise(r=>setTimeout(r,5000))])))}''');page.screenshot(path=str(a.out/(name+'.png')),full_page=True,animations='disabled')
   def fits(page):assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
   go('compare');summary=page.evaluate('async()=>await(await fetch("data/current-results.json")).json()');manifest=page.evaluate('async()=>await(await fetch("data/causal/models.json")).json()');assert summary['round_count']==597
   for model,m in summary['models'].items():
    assert m['source_sha256']==manifest['models'][model]['sha256'];row=page.locator('#current-result-comparison [data-current-model="'+model+'"]');assert row.get_attribute('data-source')==m['source_sha256']
    for part in m['cases']:
     cell=row.locator('[data-match="'+part['id']+'"]');assert cell.locator('b').inner_text()==' vs '.join(part['teams']);assert cell.locator('strong').inner_text()==' : '.join(map(str,part['score']));assert part['winner'] in cell.inner_text()
   shot(page,'compare-desktop');c['four_model_two_match_comparison_matches_frozen_sources']=True
   for model,m in summary['models'].items():
    go('channel','?ai='+model)
    for part in m['cases']:
     card=page.locator('#channel-content [data-match="'+part['id']+'"]');assert card.get_attribute('data-source')==m['source_sha256'];assert ' : '.join(map(str,part['score'])) in card.inner_text();assert all(x['map'] in card.inner_text() and ':'.join(map(str,x['score'])) in card.inner_text() for x in part['maps'])
    page.locator('[data-tab="players"]').click();page.locator('#fiction-player-results tbody tr').first.wait_for();assert page.locator('#fiction-player-results tbody tr').count()==len(m['players']);assert '虚构均分' not in page.locator('#channel-content').inner_text()
    page.locator('#fiction-player-search').fill('Sayonara');assert page.locator('#fiction-player-results tbody tr').count()==1;page.locator('#fiction-player-search').fill('');page.locator('#fiction-player-team').select_option('VIT');assert page.locator('#fiction-player-results tbody tr').count()==5
    page.locator('[data-tab="news"]').click();page.locator('#current-match-select').select_option('1');page.locator('#current-report-map').wait_for();assert page.locator('.current-round').count()==m['cases'][1]['maps'][0]['round_count'];page.locator('.current-round').first.locator('summary').click();assert page.locator('.current-round').first.locator('li').count()==len(m['cases'][1]['maps'][0]['rounds'][0]['events'])
   c['channel_results_lineups_and_round_reports_use_current_outputs']=True;shot(page,'channel-report-desktop')
   go('teams');page.locator('#team-search').fill('VIT');page.locator('#team-grid a').click();page.locator('.current-team-block').wait_for();pack=page.evaluate('async()=>await(await fetch("data/evidence-v2.json")).json()');assert all(name in page.locator('main').inner_text() for name in pack['rosters']['VIT']['players']);assert page.locator('.current-team-block [data-current-model]').count()==4;shot(page,'team-vitality-desktop');c['team_facts_and_current_model_rosters_separated']=True
   go('pickem');assert page.locator('main h1').inner_text()=='你觉得谁能赢？';assert '一键' not in page.locator('#autofill').inner_text()
   for model,m in summary['models'].items():
    page.locator('#reference-model').select_option(model);page.locator('#autofill').click();assert page.locator('#pick-result h2').inner_text()==m['cases'][1]['winner'];assert page.locator('[data-pick="lf"].win').get_attribute('data-team')==m['cases'][0]['winner'];assert page.locator('#lf-score').input_value()==str(min(m['cases'][0]['score']));assert page.locator('#gf-score').input_value()==str(min(m['cases'][1]['score']))
   page.locator('#save-pick').click();saved=page.evaluate('localStorage.getItem("vct-finals-pick")');assert json.loads(saved)['source_sha256']==summary['evidence_sha256'];page.reload();page.locator('#reference-model').wait_for();assert page.evaluate('localStorage.getItem("vct-finals-pick")')==saved;page.locator('#share-pick').click();shared=page.locator('#save-state textarea').input_value() if page.locator('#save-state textarea').count() else page.evaluate('navigator.clipboard.readText()');other=context.new_page();other.goto(shared,wait_until='domcontentloaded');other.locator('#pick-result h2').wait_for();assert other.locator('#pick-result h2').inner_text()=='LOUD';other.close();shot(page,'pickem-desktop');c['model_autofill_copies_current_results_save_share_reload_preserved']=True
   page.locator('#poster-button').click();assert page.locator('#poster').is_visible();assert 'LOUD' in page.locator('#poster-content').inner_text()
   with page.expect_download() as download:page.locator('#download-poster').click()
   download.value.save_as(str(a.out/'personal-prediction.png'));page.locator('#poster').press('Escape');page.locator('#custom-ranking').click();page.locator('#ranking-import').select_option('deepseek');page.locator('#ranking-import-button').click();expected=summary['models']['deepseek']['result_order'];assert page.locator('[data-ranking-row]>b').all_inner_texts()==expected;page.locator('[data-ranking-row="0"]').press('ArrowDown');assert page.locator('[data-ranking-row]>b').all_inner_texts()==[expected[1],expected[0],*expected[2:]];page.locator('#ranking-cancel').click();assert page.evaluate('localStorage.getItem("vct-finals-pick")')==saved;page.locator('#sim-tab').click();assert page.locator('#personal-simulation .current-series-card').count()==2;page.locator('#my-tab').click();assert page.locator('#personal-simulation').is_hidden();c['poster_download_current_order_import_keyboard_and_reference_tabs_preserved']=True
   go('leaderboard');assert '已核对 1 场' in page.locator('main').inner_text();assert page.locator('#current-leaderboard [data-current-model]').count()==4
   for cell in page.locator('#current-leaderboard [data-current-model] td:first-of-type').all_inner_texts():assert cell=='1'
   assert 'Brier' not in page.locator('#current-leaderboard').inner_text();shot(page,'leaderboard-desktop');c['no_simulated_ground_truth_or_fabricated_ranking']=True
   go('method');text=page.locator('main').inner_text();assert all(t in text for t in ['597','BP','存活','下包','拆包','批内没有逐回合外部反馈']);assert 'p³' not in text;assert page.locator('.current-source').count()==0;shot(page,'method-desktop');c['method_describes_current_causal_chain']=True;c['public_raw_output_entries_removed']=True
   ticks=page.locator('.ticker-row:not([aria-hidden]) .tick');assert ticks.count()==8
   for i in range(8):
    tick=ticks.nth(i);m=summary['models'][tick.get_attribute('data-current-model')];part=next(p for p in m['cases'] if p['id']==tick.get_attribute('data-match'));assert tick.get_attribute('data-source')==m['source_sha256'];assert '–'.join(map(str,part['score'])) in tick.inner_text();assert '结果整理' in tick.inner_text();assert 'tab=prediction' in tick.get_attribute('href') and 'case='+part['id'] in tick.get_attribute('href')
   page.locator('.ticker-label').click();page.locator('.ticker-row:not([aria-hidden]) [data-current-model="deepseek"][data-match="gf"]').click();page.locator('#channel-content').wait_for();assert 'case=gf' in page.url;card=page.locator('#channel-content [data-match="gf"]');assert 'VIT' in card.inner_text();card.locator('.btn').click();page.locator('#prediction-player[data-status="ready"]').wait_for();assert float(page.locator('#prediction-player').get_attribute('data-time'))>500;assert page.locator('#causal-map-select option:checked').inner_text().startswith('总决赛');c['eight_ticker_results_time_and_bookmarks_current']=True
   # Inspect pixels from the real loaded PNG, not a CSS background workaround.
   page.goto(url+'#/?ai=codex',wait_until='domcontentloaded');page.locator('#final-pending[data-model="codex"]').wait_for()
   alpha=page.locator('[data-channel="codex"] .model-portrait').evaluate('''async img=>{await img.decode();const c=document.createElement('canvas');c.width=img.naturalWidth;c.height=img.naturalHeight;const x=c.getContext('2d');x.drawImage(img,0,0);const a=(px,py)=>x.getImageData(px,py,1,1).data[3];return {src:img.getAttribute('src'),corners:[a(0,0),a(c.width-1,0),a(0,c.height-1),a(c.width-1,c.height-1)],costume:a(Math.floor(c.width*.5),Math.floor(c.height*.5)),background:getComputedStyle(img).backgroundColor,fit:getComputedStyle(img).objectFit};}''');assert alpha['corners']==[0,0,0,0] and alpha['costume']>=250 and alpha['fit']=='contain';assert alpha['src'].endswith('gpt-dragon-transparent.png');c['real_alpha_character_costume_preserved']=alpha;shot(page,'home-gpt-desktop')
   # Preserve a valid old counterfactual record byte-for-byte across every current page.
   raw_event=json.loads((ROOT/'data/event.json').read_text());old={'version':1,'source_sha256':raw_event['source_sha256'],'match_ids':[m['id'] for m in raw_event['matches']],'upperWinner':'VIT','lowerWinner':'G2','lfWinner':'G2','lfScore':[1,3],'champion':'G2','gfScore':[1,3],'created_at':'2026-10-16T10:00:00Z'};old_text=json.dumps(old,separators=(',',':'));ranking=json.dumps(['G2','VIT','LOUD','100T'],separators=(',',':'));legacy=b.new_context(viewport={'width':390,'height':844})
   legacy.add_init_script('''(()=>{if(!sessionStorage.getItem('seeded')){localStorage.setItem('vct-finals-pick',%s);localStorage.setItem('vct-finals-ranking',%s);sessionStorage.setItem('seeded','yes')}})()'''%(json.dumps(old_text),json.dumps(ranking)));lp=legacy.new_page();watch(lp)
   for route in selectors:
    lp.goto(url+'#/'+route,wait_until='domcontentloaded');lp.locator(selectors[route]).first.wait_for();assert lp.evaluate('localStorage.getItem("vct-finals-pick")')==old_text;assert lp.evaluate('localStorage.getItem("vct-finals-ranking")')==ranking
   lp.goto(url+'#/pickem',wait_until='domcontentloaded');lp.locator('#saved-pick-notice').wait_for();assert lp.locator('#pick-result h2').inner_text()=='G2';lp.locator('#current-pick-draft').click();assert lp.locator('#pick-result h2').inner_text()=='?';assert lp.evaluate('localStorage.getItem("vct-finals-pick")')==old_text;legacy.close();c['old_counterfactual_pick_and_ranking_bytes_unchanged_on_six_pages']=True
   for width in [320,390,768]:
    page.set_viewport_size({'width':width,'height':844})
    for route in selectors:go(route);fits(page);shot(page,route+'-'+str(width))
   page.goto(url+'#/?ai=codex',wait_until='domcontentloaded');page.locator('#final-pending[data-model="codex"]').wait_for();page.set_viewport_size({'width':390,'height':844});fits(page);shot(page,'home-gpt-mobile');c['six_pages_mobile_no_overflow']=[320,390,768];c['current_pages_boot_without_legacy_payloads']=not r['legacy_requests'];assert not r['legacy_requests'];r['status']='pass' if not r['errors'] and not r['http_failures'] else 'fail'
  except Exception as e:r['failure']=str(e);page.screenshot(path=str(a.out/'failure.png'),full_page=True)
  finally:b.close()
 if server:server.shutdown()
 (a.out/'observed.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps(r,ensure_ascii=False));return 0 if r['status']=='pass' else 1
if __name__=='__main__':raise SystemExit(main())
