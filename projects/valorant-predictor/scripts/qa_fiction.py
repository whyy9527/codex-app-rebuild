"""Record real browser behavior of the authorized fictional-content journeys."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]


def collect(url, output, functional_only=False):
    output.mkdir(parents=True, exist_ok=False)
    result = {'created_at': datetime.now(timezone.utc).isoformat(), 'url': url, 'functional_only':functional_only, 'cases': {}, 'boards': {}, 'pending': {}, 'mobile': {}, 'errors': []}
    ready = 'domcontentloaded' if functional_only else 'load'
    manifest = json.loads((ROOT / 'data/model-fiction.json').read_text())
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path='/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge', headless=True)
        try:
            context = browser.new_context(viewport={'width':1370, 'height':988}, locale='zh-CN')
            context.set_default_timeout(60000)
            context.grant_permissions(['clipboard-read', 'clipboard-write'])
            page = context.new_page();page.on('pageerror', lambda e: result['errors'].append(str(e)))
            for channel, filename in manifest.items():
                dataset = json.loads((ROOT / 'data' / filename).read_text())
                for key, row in dataset['cases'].items():
                    upper, lower, index = key.split('_')
                    link = url + f'#/match/{index}?ai={channel}&upper={upper}&lower={lower}'
                    page.goto(link, wait_until=ready);page.locator('.fiction-details').wait_for()
                    observed = {'headline':page.locator('.fiction-details h2').inner_text(), 'notice':page.locator('.fiction-details .fiction-notice').inner_text(), 'bp':page.locator('.bp-map b').all_text_contents(), 'unplayed':page.locator('.bp-map.unplayed').count(), 'ratings':page.locator('.fiction-ratings tbody tr').evaluate_all('(rows)=>rows.map(r=>({id:r.dataset.fictionPlayer,rating:r.children[2].textContent,comment:r.children[3].textContent}))'), 'maps':[]}
                    for i in range(len(row['input']['series']['maps'])):
                        page.locator(f'[data-review-map="{i}"]').click()
                        observed['maps'].append({'story':page.locator('.fiction-map-story p').first.inner_text(), 'title':page.locator('.fiction-map-story h3').inner_text(), 'mvp':page.locator('.fiction-map-story .muted').inner_text(), 'notice':page.locator('#review-map .fiction-notice').inner_text()})
                    result['cases'][channel + ':' + key] = observed
                page.goto(url + f'#/?ai={channel}&tab=players&upper=VIT&lower=100T', wait_until=ready);page.locator('#fiction-player-results').wait_for()
                ids = lambda:page.locator('#fiction-player-results [data-fiction-player]').get_attribute('data-fiction-player') if page.locator('#fiction-player-results [data-fiction-player]').count() == 1 else page.locator('#fiction-player-results [data-fiction-player]').evaluate_all('(rows)=>rows.map(r=>r.dataset.fictionPlayer)')
                board = {'all':page.locator('#fiction-player-results tbody tr').evaluate_all('(rows)=>rows.map(r=>({id:r.dataset.fictionPlayer,rating:r.children[3].textContent,count:r.children[4].textContent}))')}
                page.locator('#fiction-player-search').fill('zzzz-no-player');board['empty'] = page.locator('#fiction-player-results').inner_text()
                page.locator('#fiction-player-search').fill('');page.locator('#fiction-player-team').select_option('VIT');board['team'] = ids()
                page.locator('#fiction-player-team').select_option('');page.locator('#fiction-player-both').check();board['both'] = ids()
                page.locator('#fiction-player-both').uncheck();page.locator('#fiction-player-sort').select_option('name');board['names'] = page.locator('#fiction-player-results tbody th').all_text_contents()
                page.locator('#fiction-player-results .source-link').first.click();board['opened_review_notice'] = page.locator('.fiction-details .fiction-notice').inner_text()
                page.locator('#share-review').click();shared = page.evaluate('navigator.clipboard.readText()');fresh = browser.new_context();fresh.set_default_timeout(60000);other = fresh.new_page();other.goto(shared, wait_until=ready);board['shared_url'] = shared;board['shared_headline'] = other.locator('.fiction-details h2').inner_text();fresh.close()
                page.goto(url + f'#/?ai={channel}&tab=news&upper=VIT&lower=100T', wait_until=ready);board['news'] = page.locator('.fiction-news h3').all_text_contents();board['news_notice'] = page.locator('#channel-content > .fiction-notice').inner_text();result['boards'][channel] = board
                page.locator('.fiction-news').evaluate('(e)=>e.scrollIntoView({block:"start",behavior:"instant"})')
                page.wait_for_function('getComputedStyle(document.querySelector("#toast")).opacity === "0"')
                if not functional_only:page.screenshot(path=str(output / (channel + '-news.png')))
            for width in [320, 390]:
                mobile = browser.new_context(viewport={'width':width, 'height':844}, is_mobile=True, has_touch=True)
                mobile.set_default_timeout(60000)
                m = mobile.new_page();m.on('pageerror', lambda e:result['errors'].append(str(e)))
                m.goto(url + '#/match/1?ai=codex&upper=VIT&lower=100T', wait_until=ready);m.locator('.fiction-details').wait_for();m.locator('[data-review-map="4"]').click()
                result['mobile'][str(width)] = {'review':m.evaluate('({viewport:innerWidth,scroll:document.documentElement.scrollWidth})'), 'story':m.locator('.fiction-map-story p').first.inner_text()}
                m.locator('.fiction-details').evaluate('(e)=>e.scrollIntoView({block:"start",behavior:"instant"})')
                if not functional_only:m.screenshot(path=str(output / f'mobile-{width}-review.png'))
                m.goto(url + '#/?ai=codex&tab=players&upper=VIT&lower=100T', wait_until=ready);m.locator('#fiction-player-search').fill('Chronicle');result['mobile'][str(width)]['searched'] = m.locator('#fiction-player-results tbody th').all_text_contents();result['mobile'][str(width)]['board'] = m.evaluate('({viewport:innerWidth,scroll:document.documentElement.scrollWidth})');mobile.close()
            context.close()
        except Exception as e:result['error'] = str(e)
        finally:browser.close()
    (output / 'observed.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'cases':len(result['cases']), 'error':result.get('error'), 'page_errors':result['errors']}))
    return result


if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--url',default='http://127.0.0.1:5173/');parser.add_argument('--out',required=True);parser.add_argument('--functional-only',action='store_true');args=parser.parse_args();value=collect(args.url,REPO/args.out,args.functional_only);raise SystemExit(1 if value.get('error') or value['errors'] else 0)
