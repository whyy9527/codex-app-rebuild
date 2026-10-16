"""Verify the four-model revision, portrait mapping and saved/linked retired channels."""
import argparse
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = ['codex', 'deepseek', 'doubao', 'mimo']


def collect(url, out):
    out.mkdir(parents=True, exist_ok=False)
    result = {'url': url, 'facts': {}, 'errors': []}
    assets = json.loads((ROOT / 'data/assets.json').read_text())['models']
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path='/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge', headless=True)
        try:
            context = browser.new_context(viewport={'width':1370, 'height':988}, locale='zh-CN')
            context.set_default_timeout(120000)
            context.add_init_script("localStorage.setItem('vct-finals-channel', JSON.stringify('opus'));localStorage.setItem('vct-finals-reference', JSON.stringify('qwen'));")
            page = context.new_page();page.on('pageerror', lambda e:result['errors'].append(str(e)))
            page.goto(url + '#/?ai=gemini', wait_until='domcontentloaded')
            page.locator('.channels .channel').first.wait_for()
            ids = page.locator('.channels .channel').evaluate_all('(els)=>els.map(e=>e.dataset.channel)')
            assert ids == EXPECTED, ids
            assert page.locator('.channels .channel.on').get_attribute('data-channel') == 'codex'
            assert page.evaluate("JSON.parse(localStorage.getItem('vct-finals-channel'))") == 'codex'
            result['facts']['retired_saved_channel_and_link_recovered'] = True
            page.wait_for_function('()=>[...document.querySelectorAll(".portraits img")].every(i=>i.complete&&i.naturalWidth>0)')
            rows = page.locator('.portrait').evaluate_all('(els)=>els.map(e=>({channel:e.dataset.channel,src:e.querySelector("img").getAttribute("src")}))')
            assert rows == [{'channel':c,'src':assets[c]['portrait']} for c in EXPECTED], rows
            assert not any(name in page.locator('body').inner_text() for name in ('Claude','Gemini','Qwen','GLM'))
            assert page.locator('.forecast-card').count() == 4
            result['facts'].update(channel_ids=ids, portraits=rows)
            for channel in EXPECTED:
                page.locator('.channels [data-channel="'+channel+'"]').click()
                assert page.locator('.channels .channel.on').get_attribute('data-channel') == channel
                assert '等待预测' not in page.locator('#channel-content').inner_text()
            page.locator('.channels [data-channel="codex"]').click()
            if page.locator('#play[title="暂停 (空格)"]').count():page.locator('.studio').press('Space')
            page.wait_for_function('()=>[...document.querySelectorAll(".stage-scene")].every(e=>e.getAnimations().every(a=>a.playState==="finished"))')
            page.evaluate('scrollTo(0,0)');page.wait_for_function('document.fonts.status === "loaded"')
            page.screenshot(path=str(out/'desktop.png'), timeout=120000)
            page.goto(url+'#/compare', wait_until='domcontentloaded');page.locator('#champion-comparison').wait_for()
            assert page.locator('#champion-comparison thead th').count() == 6
            assert page.locator('td').filter(has_text='待预测').count() == 0
            result['facts']['comparison_four_models_and_separate_baseline'] = True
            page.goto(url+'#/pickem', wait_until='domcontentloaded');page.locator('#reference-model').wait_for()
            assert page.locator('#reference-model').input_value() == 'codex'
            assert page.locator('#reference-model option').evaluate_all('(els)=>els.map(e=>e.value)') == EXPECTED+['baseline']
            result['facts']['retired_personal_reference_recovered'] = True
            for width in [320,390]:
                page.set_viewport_size({'width':width,'height':844});page.goto(url+'#/',wait_until='domcontentloaded');page.locator('#mobile-model').wait_for()
                assert page.locator('.portrait:visible').count() == 4
                assert page.locator('#mobile-model option').evaluate_all('(els)=>els.map(e=>e.value)') == EXPECTED
                sizes=page.evaluate('({viewport:innerWidth,scroll:document.documentElement.scrollWidth})')
                assert sizes['scroll'] <= sizes['viewport'],sizes
                result['facts']['mobile_'+str(width)] = sizes
                if width == 390:
                    page.evaluate('scrollTo(0,0)');page.wait_for_function('document.fonts.status === "loaded"');page.screenshot(path=str(out/'mobile.png'),timeout=120000)
            assert not result['errors'],result['errors']
        except Exception as error:
            result['error']=str(error)
        finally:browser.close()
    (out/'observed.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    if result.get('error'):raise RuntimeError(result['error'])
    print(json.dumps({'four_models':True,'portrait_mapping':True,'retired_state_recovery':True,'mobile':True,'page_errors':result['errors']}))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--url',required=True);parser.add_argument('--out',required=True);args=parser.parse_args();collect(args.url,Path(args.out))
