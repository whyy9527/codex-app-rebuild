"""Case adapter: capture the live Toy content frame using the shared collector.

Only local storage in a fresh browser context is reset. Public CDN/version and
server responses remain remote, and all sampling drift is retained.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys

# Allow direct CLI execution while keeping the shared framework as the owner.
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from runtime.browser import collect_step, write_json
from capabilities.rebuild.browser import observed_state, evidence_problems

URL = 'https://www.bilibili.com/toy/LkvCZhw12wgT2Pqx/index.html'
CONTENT = 'https://www.bilibilitoy.com/toy/LkvCZhw12wgT2Pqx/43482999941120-v26695/index.html'
ROUTES = ['/', '/compare', '/teams', '/pickem', '/leaderboard', '/method', '/about']


class ContentSurface:
    def __init__(self, frame, element): self.frame, self.element = frame, element
    def __getattr__(self, key): return getattr(self.frame, key)
    def screenshot(self, **kwargs):
        kwargs.pop('full_page', None)
        return self.element.screenshot(**kwargs)


def capture_case(workspace, route, out, candidate=None, width=1440, height=1000):
    from playwright.sync_api import sync_playwright
    workspace, output = Path(workspace).resolve(), Path(workspace).resolve() / out
    output.mkdir(parents=True, exist_ok=False)
    executable = os.environ.get('REBUILD_BROWSER_EXECUTABLE', '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge')
    result = {'schema_version': 1, 'kind': 'browser_capture', 'created_at': datetime.now(timezone.utc).isoformat(),
              'mode': 'launch', 'steps': [], 'states': {}, 'cleanup': 'not_acquired',
              'restoration': 'Fresh isolated local context; no server-side state reset', 'route': route}
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=executable, headless=True)
        try:
            context = browser.new_context(viewport={'width': width, 'height': height}, locale='zh-CN', timezone_id='Asia/Shanghai')
            page = context.new_page()
            page.set_default_timeout(20000)
            page.goto(candidate or URL, wait_until='load')
            if candidate:
                surface = page
            else:
                iframe = page.locator('iframe[src="' + CONTENT + '"]')
                iframe.wait_for(state='visible')
                element = iframe.element_handle()
                frame = element.content_frame()
                surface = ContentSurface(frame, iframe)
            surface.locator('#main-content').wait_for(state='visible')
            if route != '/':
                surface.locator(('footer ' if candidate else '') + 'a[href="#' + route + '"]').last.click() if route == '/about' else surface.locator('.mainnav a[href="#' + route + '"]').click()
                surface.wait_for_function('r => location.hash.split("?")[0] === "#" + r', arg=route)
            surface.locator('h1').wait_for(state='visible')
            if not candidate:
                titles = {'/':'S16 AI 大模型预测大赛', '/compare':'数据对比', '/teams':'参赛战队', '/pickem':'我来预测', '/leaderboard':'谁最准', '/method':'S16 · AI 赛制介绍'}
                if route in titles:
                    surface.wait_for_function(r't => document.querySelector("h1")?.textContent.replace(/\s+/g," ").trim() === t', arg=titles[route])
            surface.wait_for_function('() => [...document.images].filter(i => {const r=i.getBoundingClientRect();return r.top < innerHeight && r.bottom > 0 && r.width > 0 && r.height > 0}).every(i => i.complete && i.naturalWidth > 0)')
            if route == '/':
                pause = surface.locator('button[title="暂停 (空格)"]')
                if pause.count(): pause.click()
            surface.locator('#main-content h1').click()
            surface.evaluate('window.scrollTo(0,0)')
            page.mouse.move(-1,-1) if candidate else page.mouse.move(width-1,height/2)
            if not candidate:
                clock = surface.locator('a.live-badge').inner_text()
                surface.wait_for_function('previous => document.querySelector("a.live-badge")?.textContent.trim() !== previous', arg=clock)
            step = {'id': route.strip('/') or 'home', 'action': {'type': 'observe'},
                    'ready': {'selector': '#main-content h1', 'state': 'visible'},
                    'capture': ['dom', 'text', 'accessibility', 'screenshot']}
            record = collect_step(surface, workspace, output, 0, step, {'title': '#main-content h1'})
            record['elapsed_seconds'] = 0
            record['receipt_path'] = (output / '0000-step.json').relative_to(workspace).as_posix()
            result['steps'].append(record)
            result['browser_version'] = browser.version
            if not candidate:
                result['frame_source'] = surface.frame.url
                result['frame_rect'] = iframe.bounding_box()
        except Exception as error:
            result['error'] = str(error)
        finally:
            browser.close()
            result['cleanup'] = 'released'
    for record in result['steps']:
        record['cleanup'] = result['cleanup']
        write_json(workspace / record['receipt_path'], record)
        result['states'][record['id']] = observed_state(workspace, record, record['receipt_path'])
    result['status'] = 'captured' if result['steps'] and not result.get('error') and all(
        not evidence_problems(workspace, r, r['requested']) for r in result['steps']) else 'incomplete'
    write_json(output / 'observed.json', result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--workspace', default=str(ROOT))
    parser.add_argument('--route', choices=ROUTES, default='/')
    parser.add_argument('--out', required=True)
    parser.add_argument('--candidate')
    args = parser.parse_args()
    result = capture_case(args.workspace, args.route, args.out, args.candidate)
    print(json.dumps({'status': result['status'], 'error': result.get('error'), 'out': args.out}, ensure_ascii=False))
    raise SystemExit(0 if result['status'] == 'captured' else 1)
