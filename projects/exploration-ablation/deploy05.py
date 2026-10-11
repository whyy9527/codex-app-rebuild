"""Real frontend-feedback policy generation, sealing and bounded UI deployment."""
import argparse,hashlib,json,re,subprocess,sys,importlib.util
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from replay import choose,digest
P=Path('projects/exploration-ablation')
spec=importlib.util.spec_from_file_location('model_worker',P/'model-worker.py');worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker);call_worker=worker.call_worker
p=argparse.ArgumentParser();p.add_argument('--phase',choices=['initial','revise','deploy'],required=True);p.add_argument('--step',type=int,choices=[1,2]);p.add_argument('--out',required=True);p.add_argument('--root',required=True);p.add_argument('--codex-binary');p.add_argument('--cli');p.add_argument('--session');p.add_argument('--registration',default=str(P/'registration05.json'));a=p.parse_args()
out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
def read(p):return json.loads(Path(p).read_text())
def write(p,d):
 with Path(p).open('x') as f:f.write(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
r=read(a.registration);actions=read(P/'actions05.json');root=read(a.root)
def root_identity(s):
 return {'path':s['path'],'stats':[(x['name'],x['rect']) for x in s['actions'] if x['role']=='button' and x['rect'][1]==24 and x['name'].isdigit()],'panel':next(x for x in s['scroll_regions'] if x['rect']==[360,48,480,636])}
assert hashlib.sha256(root['snapshot'].encode()).hexdigest()==r['root_snapshot_sha256']
if 'root_identity_digest' in r:assert digest(root_identity(root))==r['root_identity_digest']
if a.phase in ['initial','revise']:
 step=1 if a.phase=='initial' else 2;assert not (out/f'seal{step}.json').exists();assert not (out/f'worker{step}').exists(), 'One model attempt per phase; preserve any running/failed worker'
 prior=[read(n) for n in r['past_feedback']]
 context={'past_product_feedback':prior,'source_root':{'path':root['path'],'snapshot':root['snapshot'],'scroll_regions':root['scroll_regions'],'focus':root['focus']},'actions':actions,'past_native_result':{'revision':'v76','counts':{'pass':481,'fail':65,'not_run':18954,'unavailable':627},'whole_images':'7 fail; streak consumer missing'},'limitations':['Unexecuted results unknown','One group, not causal evaluation','Do not use files, web, tools or hidden application state']}
 visits={}
 if step==2:
  seal=read(out/'seal1.json');result=read(out/'step1-result.json');before=read(out/'step1-before.json');after=read(out/'step1-after.json');visits[seal['action']['id']]=1
  context['actual_step1_feedback']={'selected_policy':seal['policy'],'action':seal['action'],'result':result,'before':{'snapshot':before['snapshot'],'focus':before['focus'],'scroll_regions':before['scroll_regions']},'after':{'snapshot':after['snapshot'],'focus':after['focus'],'scroll_regions':after['scroll_regions'],'text_runs':after['text_runs']}}
 prompt='Return exactly three distinct bounded policies in the given schema. Parent deploys first returned policy. Improve exploration of missing frontend requirements using only provided past feedback and source-visible action labels. Rules are literal substrings of labels; weights -10..10, at most16 rules, term1..80 characters, repeat_penalty0..20. Do not claim unseen outcomes or RSI benefits. Do not call any tools or inspect files.\n'+json.dumps(context,ensure_ascii=False)
 policies,receipt=call_worker('initial05' if step==1 else 'revision05',prompt,out/f'worker{step}',P/'policy-schema.json',a.codex_binary,r['cli_binary_sha256'])
 stderr=(out/f'worker{step}'/('initial05-stderr.txt' if step==1 else 'revision05-stderr.txt')).read_text()
 if re.search(r'^(exec|tool)\s*$',stderr,re.M):raise RuntimeError('Unexpected worker tool execution; preserve and stop')
 observation={'actions':[{'id':x['id'],'label':x['label']} for x in actions],'visits':visits,'revealed':[]}
 policy=policies[0];action=next(x for x in actions if x['id']==choose(policy,observation))
 write(out/f'seal{step}.json',{'step':step,'policy':policy,'policy_digest':digest(policy),'action':action,'action_digest':digest(action),'registration_digest':digest(r),'worker_receipt':receipt,'selection':'First returned policy; no unseen reward selection','visits':visits})
 print(json.dumps({'sealed_step':step,'action':action['id'],'tokens':receipt['reported_tokens_used']}));sys.exit(0)
step=a.step;assert step in [1,2];seal=read(out/f'seal{step}.json');assert seal['registration_digest']==digest(r) and seal['policy_digest']==digest(seal['policy']) and seal['action_digest']==digest(seal['action']);assert not (out/f'step{step}-result.json').exists()
def ui(name,code):
 dest=out/(name+'.raw.txt');assert not dest.exists()
 x=subprocess.run([a.cli,'-s='+a.session,'run-code',code],cwd='artifacts/output/playwright',capture_output=True,text=True,timeout=60000)
 dest.write_text(x.stdout+x.stderr)
 if x.returncode or '### Error' in x.stdout or '### Result\n' not in x.stdout:raise RuntimeError('Actual source action unavailable; keep receipt, no replacement')
 return json.loads(x.stdout.split('### Result\n',1)[1].split('\n### Ran',1)[0])
def capture(name):
 x=subprocess.run(['node','projects/duolingo-web/capture-visible-state.mjs','--out',str(out/name),'--cli',a.cli,'--session',a.session,'--preserve-hover'],capture_output=True,text=True,timeout=60000)
 (out/(name+'-collector.log')).write_text(x.stdout+x.stderr)
 if x.returncode:raise RuntimeError('Source capture unavailable')
 s=read(out/(name+'.json'));assert s['capture_state_consistent'];return s
ui(f'step{step}-reset',"async page=>{await page.mouse.move(600,610);await page.mouse.wheel(0,-1200);await page.waitForTimeout(300);const c=await page.locator('[data-test=close-button]').boundingBox();if(c.y<0)throw Error('Close still outside viewport');await page.mouse.click(c.x+c.width/2,c.y+c.height/2);const b=await page.getByRole('button',{name:'1',exact:true}).boundingBox();await page.mouse.move(b.x+b.width/2,b.y+b.height/2);await page.getByText('查看更多',{exact:true}).waitFor();const d=await page.getByRole('button',{name:'查看更多',exact:true}).boundingBox();await page.mouse.click(d.x+d.width/2,d.y+d.height/2);await page.getByText('连胜日历',{exact:true}).waitFor();await page.mouse.move(600,100);return {snapshot:await page.locator('body').ariaSnapshot()};}")
before=capture(f'step{step}-before');assert before['path']=='/learn'
if 'root_identity_digest' in r:assert digest(root_identity(before))==r['root_identity_digest']
else:assert hashlib.sha256(before['snapshot'].encode()).hexdigest()==r['root_snapshot_sha256']
assert any(s['scrollTop']==0 and s['rect']==[360,48,480,636] for s in before['scroll_regions'])
action=seal['action']
if action['operation']=='wheel':code="async page=>{await page.mouse.move(600,610);await page.mouse.wheel(0,700);await page.waitForTimeout(500);return {snapshot:await page.locator('body').ariaSnapshot()};}"
else:
 operation="await b.click();" if action['operation']=='click' else "await b.focus();await page.keyboard.press('Enter');"
 code="async page=>{const b=page.getByRole('button',{name:'',exact:true}).nth(INDEX);const r=await b.boundingBox();if(JSON.stringify([r.x,r.y,r.width,r.height])!==JSON.stringify(RECT))throw Error('Visible control geometry changed');OPERATION await page.waitForTimeout(500);return {snapshot:await page.locator('body').ariaSnapshot()};}".replace('INDEX',str(action['index'])).replace('RECT',json.dumps(action['rect'])).replace('OPERATION',operation)
ui(f'step{step}-action',code);after=capture(f'step{step}-after')
write(out/f'step{step}-result.json',{'step':step,'action':action,'policy_digest':seal['policy_digest'],'root_snapshot_sha256':r['root_snapshot_sha256'],'before_scroll':before['scroll_regions'],'after_scroll':after['scroll_regions'],'before_focus':before['focus'],'after_focus':after['focus'],'new_rendered_text':sorted({x['text'] for x in after['text_runs']}-{x['text'] for x in before['text_runs']}),'before_semantic_state_consistent':before['capture_state_consistent'],'after_semantic_state_consistent':after['capture_state_consistent'],'interpretation':'Actual observations only; no discovery score, independent requirement count or RSI/product gain claimed'})
print(json.dumps({'deployed_step':step,'action':action['id']}))
