"""Collect source comparison sections and candidate conditional tables/motion."""
import argparse
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_evidence import ContentSurface, URL, CONTENT

MOTION = '''async selector => {
  const el = document.querySelector(selector), start = performance.now(), samples = [];
  const style = getComputedStyle(el);
  const timing = {duration: style.animationDuration, easing: style.animationTimingFunction};
  while (performance.now() - start < 550) {
    const s = getComputedStyle(el);
    samples.push({elapsed: performance.now() - start, opacity: +s.opacity, transform: s.transform});
    await new Promise(requestAnimationFrame);
  }
  return {timing, samples};
}'''


def collect(out):
    root = Path(__file__).resolve().parents[3]
    output = root / out
    output.mkdir(parents=True, exist_ok=False)
    result = {'reference': {}, 'candidate': {}, 'errors': []}
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=os.environ.get('REBUILD_BROWSER_EXECUTABLE', '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge'), headless=True)
        try:
            context = browser.new_context(viewport={'width': 1440, 'height': 1000}, locale='zh-CN')
            source = context.new_page()
            source.goto(URL, wait_until='load')
            iframe = source.locator('iframe[src="' + CONTENT + '"]')
            iframe.wait_for()
            surface = ContentSurface(iframe.element_handle().content_frame(), iframe)
            surface.locator('.studio2 button.play').wait_for()
            if surface.locator('button[title="暂停 (空格)"]').count():
                surface.locator('.studio2').press('Space')
            surface.locator('button[aria-label="下一步"]').click()
            result['reference']['motion'] = surface.evaluate(MOTION, '.stage-box .scene')
            surface.locator('.mainnav a[href="#/compare"]').click()
            surface.get_by_role('heading', name='夺冠概率对比', exact=True).wait_for()
            surface.evaluate('document.fonts.ready')
            result['reference']['headings'] = surface.locator('h2').all_text_contents()
            result['reference']['text'] = surface.locator('#main-content').inner_text()
            result['reference']['viewport'] = surface.evaluate('({width:innerWidth,height:innerHeight})')
            surface.locator('#main-content').press('Escape')
            surface.evaluate('scrollTo(0,0)')
            surface.wait_for_function('() => [...document.images].filter(i=>{const r=i.getBoundingClientRect();return r.width>0&&r.height>0&&r.top<innerHeight&&r.bottom>0}).every(i=>i.complete&&i.naturalWidth>0)')
            surface.screenshot(path=str(output / 'reference-comparison.png'))
            page = context.new_page()
            page.on('pageerror', lambda e: result['errors'].append(str(e)))
            page.set_viewport_size(result['reference']['viewport'])
            page.goto('http://127.0.0.1:5173/', wait_until='load')
            page.locator('#play').wait_for()
            if page.locator('#play[title="暂停 (空格)"]').count():page.locator('.studio').press('Space')
            page.locator('#next').click()
            result['candidate']['motion'] = page.evaluate(MOTION, '.stage-scene')
            page.locator('.mainnav a[href="#/compare"]').click()
            page.locator('#champion-comparison').wait_for()
            page.evaluate('document.fonts.ready')
            result['candidate']['headings'] = page.locator('h2').all_text_contents()
            result['candidate']['cases'] = []
            for upper in ['LOUD', 'VIT']:
                for lower in ['G2', '100T']:
                    page.locator('#upper-winner').select_option(upper)
                    page.locator('#lower-winner').select_option(lower)
                    result['candidate']['cases'].append({'upper': upper, 'lower': lower, 'rows': page.locator('#champion-comparison tbody tr').evaluate_all('(rows)=>rows.map(r=>({team:r.querySelector("th a").textContent.trim(),values:[...r.querySelectorAll("td")].map(c=>({text:c.textContent,value:c.dataset.value??null}))}))')})
            result['candidate']['ranks'] = page.locator('#ranking-comparison tbody tr').evaluate_all('(rows)=>rows.map(r=>({team:r.querySelector("th a").textContent.trim(),values:[...r.querySelectorAll("td")].map(c=>c.textContent)}))')
            result['candidate']['dots'] = page.locator('#disagreement-chart circle title').all_text_contents()
            for model in ['codex', 'deepseek', 'baseline']:
                page.locator('#compare-model').select_option(model)
                result['candidate'][model] = {'distribution': page.locator('#distributions').inner_text(), 'reasons': page.locator('#compare-reasons').inner_text()}
            page.locator('#main-content').press('Escape')
            page.evaluate('scrollTo(0,0)')
            page.wait_for_function('getComputedStyle(document.querySelector("#toast")).opacity==="0"')
            page.wait_for_function('() => [...document.images].filter(i=>{const r=i.getBoundingClientRect();return r.width>0&&r.height>0&&r.top<innerHeight&&r.bottom>0}).every(i=>i.complete&&i.naturalWidth>0)')
            page.screenshot(path=str(output / 'candidate-comparison.png'))
            page.set_viewport_size({'width': 320, 'height': 832})
            result['candidate']['mobile_width'] = page.evaluate('({viewport:innerWidth,scroll:document.documentElement.scrollWidth})')
            page.screenshot(path=str(output / 'mobile-comparison.png'))
            context.close()
        except Exception as error:
            result['error'] = str(error)
        finally:
            browser.close()
    (output / 'observed.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser();parser.add_argument('--out', required=True);args = parser.parse_args()
    result = collect(args.out)
    print(json.dumps({'error': result.get('error'), 'page_errors': result['errors'], 'cases': len(result['candidate'].get('cases', []))}))
    raise SystemExit(1 if result.get('error') or result['errors'] else 0)
