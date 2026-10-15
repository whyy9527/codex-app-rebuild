"""PID-filtered browser output capture, with real in-recording UI triggers.

Requires an already permitted ScreenCaptureKit collector. Never records mic or
other apps. An unavailable permission/API is retained as an error, not silence.
"""
import argparse
import json
import os
from pathlib import Path
import select
import subprocess
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parent))
from browser_evidence import ContentSurface, URL, CONTENT


def collect(mode, out, collector, collector_flags=(), inspect_processes=False, warmup_audio=False, cue='pick', audible_only=False):
    from playwright.sync_api import sync_playwright
    root=Path(__file__).resolve().parents[3];output=root/out;output.mkdir(parents=True,exist_ok=False)
    executable=os.environ.get('REBUILD_BROWSER_EXECUTABLE','/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge')
    profile=output/'owned-profile'
    process=subprocess.Popen([executable,'--user-data-dir='+str(profile),'--remote-debugging-port=0','--no-first-run','--no-default-browser-check','about:blank'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    result={'mode':mode,'cue':cue,'owned_pid':process.pid,'microphone':False,'actions':[],'captures':[],'collector_flags':list(collector_flags),'web_audio_events':[]}
    audio_process=None
    try:
        active=profile/'DevToolsActivePort';deadline=time.monotonic()+20
        while not active.exists():
            if time.monotonic()>deadline:raise TimeoutError('Owned browser CDP did not become ready')
            time.sleep(.1)
        endpoint='http://127.0.0.1:'+active.read_text().splitlines()[0]
        with sync_playwright() as p:
            browser=p.chromium.connect_over_cdp(endpoint);context=browser.contexts[0];page=context.new_page();page.set_default_timeout(20000)
            page.on('dialog', lambda dialog: dialog.accept() if dialog.type == 'confirm' and '清空这份预测' in dialog.message else dialog.dismiss())
            page.goto(URL if mode=='reference' else 'http://127.0.0.1:5173/',wait_until='load')
            if mode=='reference':
                iframe=page.locator('iframe[src="'+CONTENT+'"]');iframe.wait_for();surface=ContentSurface(iframe.element_handle().content_frame(),iframe)
                surface.locator('.studio2 button.play').wait_for()
                if surface.locator('button[title="暂停 (空格)"]').count():surface.locator('.studio2').press('Space')
                if surface.get_by_role('button',name='开启音效',exact=True).count():surface.get_by_role('button',name='开启音效',exact=True).click()
            else:
                surface=page;surface.locator('#play').wait_for()
                if surface.locator('#play[title="暂停 (空格)"]').count():surface.locator('.studio').press('Space')
                if surface.get_by_role('button',name='取消静音',exact=True).count():surface.get_by_role('button',name='取消静音',exact=True).click()
            audio_session=context.new_cdp_session(surface.frame if mode=='reference'else page)
            contexts=set()
            def audio_event(event):
                result['web_audio_events'].append(event)
                if event.get('context',{}).get('contextId'):contexts.add(event['context']['contextId'])
            audio_session.on('WebAudio.contextCreated',audio_event)
            audio_session.on('WebAudio.contextChanged',audio_event)
            audio_session.send('WebAudio.enable')
            def inspect_owned():
                if not inspect_processes:return None
                pairs=[tuple(map(int,line.split()))for line in subprocess.check_output(['ps','-axo','pid=,ppid='],text=True).splitlines()]
                owned={process.pid}
                while True:
                    children={pid for pid,parent in pairs if parent in owned}
                    if children<=owned:break
                    owned|=children
                result['owned_pid_tree']=sorted(owned)
                return json.loads(subprocess.check_output([str(root/'artifacts/inspect-owned-audio'),*map(str,sorted(owned))],text=True))
            def pick_screen(kind=cue):
                surface.locator('.mainnav a[href="#/pickem"]').click()
                if mode=='reference':
                    reveal=surface.get_by_role('button',name='揭晓对阵',exact=True)
                    if reveal.count():reveal.click()
                    if kind != 'pick':
                        fill=surface.get_by_role('button',name='按实力参考一键填完',exact=True)
                        if kind == 'autofill':return fill
                        fill.click();time.sleep(2)
                        return surface.get_by_role('button',name='锁定我的预测',exact=True)
                    surface.locator('.pk-team').first.wait_for();teams=surface.locator('.pk-match').first.locator('.pk-team');index=max(range(teams.count()),key=lambda i:float(teams.nth(i).locator('.mono').inner_text().strip('%')));return surface.locator('.pk-match').first.locator('.pk-team').nth(index)
                if kind != 'pick':
                    if kind == 'autofill':return surface.locator('#autofill')
                    surface.locator('#autofill').click();time.sleep(2)
                    return surface.locator('#save-pick')
                surface.locator('[data-pick="lf"]').first.wait_for();return surface.locator('[data-pick="lf"]').first
            if warmup_audio:
                pick=pick_screen('pick')
                result['preparation_actions']=[{'control':pick.inner_text(),'action':'Real click before capture to register the owned browser audio process'}];pick.click()
            pick=pick_screen()
            time.sleep(1)
            for phase in ['audible'] if audible_only else ['audible','muted','restored']:
                if phase!='audible':
                    surface.locator('.mainnav a[href="#/"]').click()
                    if mode=='reference':surface.locator('.studio2 button.play').wait_for()
                    else:surface.locator('#mute').wait_for()
                    surface.get_by_role('button',name='静音' if phase=='muted' else ('开启音效' if mode=='reference' else '取消静音'),exact=True).click()
                    if mode=='reference' and cue!='pick':
                        surface.locator('.mainnav a[href="#/pickem"]').click()
                        surface.get_by_role('button',name='重新预测',exact=True).click()
                    pick=pick_screen();time.sleep(1)
                wav=output/(phase+'.wav')
                audio_process=subprocess.Popen([str(root/collector),str(process.pid),str(wav),'5',*collector_flags],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
                started=time.monotonic();ready=False
                while time.monotonic()-started<15:
                    readable,_,_=select.select([audio_process.stdout],[],[],.2)
                    if readable:
                        line=audio_process.stdout.readline()
                        if line.startswith('READY '):ready=True;break
                    if audio_process.poll() is not None:break
                if not ready:
                    stdout,stderr=audio_process.communicate(timeout=10);raise RuntimeError('Audio collector unavailable: '+stderr[-700:])
                origin=time.monotonic();phase_actions=[]
                for i in range(3 if cue=='pick' else 1):
                    time.sleep(.6 if i==0 else 1)
                    label=pick.inner_text();pick.click();phase_actions.append({'control':label,'elapsed_seconds_after_capture_ready':time.monotonic()-origin,'realtime_contexts':[audio_session.send('WebAudio.getRealtimeData',{'contextId':c})for c in contexts],'core_audio':inspect_owned()})
                stdout,stderr=audio_process.communicate(timeout=15)
                if audio_process.returncode:raise RuntimeError('Audio capture failed: '+stderr[-700:])
                receipt=json.loads(wav.with_suffix('.wav.json').read_text());receipt['real_browser_actions']=phase_actions
                wav.with_suffix('.wav.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
                result['captures'].append({'phase':phase,'receipt':str(wav.with_suffix('.wav.json').relative_to(root))});result['actions'].extend(phase_actions)
            page.screenshot(path=str(output/'owned-browser.png'))
            browser.close()
    except Exception as error:result['error']=str(error)
    finally:
        for child in (audio_process,process):
            if child and child.poll() is None:
                try:
                    child.terminate()
                    try:child.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        child.kill();child.wait(timeout=10)
                        result.setdefault('cleanup_notes',[]).append('Owned child required kill after termination timeout')
                except Exception as error:result.setdefault('cleanup_errors',[]).append(str(error))
        (output/'observed.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=['reference','candidate'],required=True);parser.add_argument('--out',required=True);parser.add_argument('--collector',default='artifacts/capture-owned-audio');parser.add_argument('--include-self-audio',action='store_true');parser.add_argument('--window-filter',action='store_true');parser.add_argument('--inspect-processes',action='store_true');parser.add_argument('--warmup-audio',action='store_true');parser.add_argument('--cue',choices=['pick','autofill','save'],default='pick');parser.add_argument('--audible-only',action='store_true');args=parser.parse_args()
    result=collect(args.mode,args.out,args.collector,(['--include-self-audio']if args.include_self_audio else[])+(['--filter=window']if args.window_filter else[]),args.inspect_processes,args.warmup_audio,args.cue,args.audible_only);print(json.dumps({'mode':args.mode,'captures':len(result['captures']),'error':result.get('error')},ensure_ascii=False));raise SystemExit(1 if result.get('error')else 0)
