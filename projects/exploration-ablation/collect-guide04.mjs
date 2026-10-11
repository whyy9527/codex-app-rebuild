// Registered batch04: actual source actions, semantic readiness, no forced clicks.
import {spawnSync} from 'node:child_process';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
const arg=n=>process.argv[process.argv.indexOf(n)+1];
const cli=arg('--cli'),session=arg('--session'),out=resolve(arg('--out'));
const actions=JSON.parse(readFileSync(arg('--actions'),'utf8'));
mkdirSync(out,{recursive:true});
function run(code,name){
 const r=spawnSync(cli,['-s='+session,'run-code',code],{cwd:resolve('artifacts/output/playwright'),encoding:'utf8',timeout:45000,maxBuffer:8*1024*1024});
 writeFileSync(out+'/'+name+'.raw.txt',r.stdout+r.stderr,{flag:'wx'});
 if(r.status!==0 || !r.stdout.includes('### Result\n') || r.stdout.includes('### Error'))throw Error('Source unavailable; preserve actual receipt');
 return JSON.parse(r.stdout.split('### Result\n')[1].split('\n### Ran')[0]);
}
function cap(name){
 const r=spawnSync(process.execPath,['projects/duolingo-web/capture-visible-state.mjs','--cli',cli,'--session',session,'--out',out+'/'+name],{encoding:'utf8',timeout:65000,maxBuffer:8*1024*1024});
 if(r.status!==0)throw Error('Source capture unavailable');
 return JSON.parse(readFileSync(out+'/'+name+'.json','utf8'));
}
const stable=`const deadline=Date.now()+15000;let previous=null,stable=0,samples=0;
 while(Date.now()<deadline){const snapshot=await page.locator('body').ariaSnapshot();samples++;stable=snapshot===previous?stable+1:0;previous=snapshot;
 if(new URL(page.url()).pathname==='/guidebook/en/12' && await page.locator('[data-test="hint-token"]').count()===25 && stable>=2)return {status:'ready',samples,stable_repeats:stable,wall_ms:Date.now()-started};
 await page.waitForTimeout(150);}return {status:'unavailable',samples,reason:'guide path/token inventory or semantic stability timeout'};`;
const branches=[],roots=[];
for(const a of actions){
 const beforeReady=run(`async page=>{const started=Date.now();await page.goto('https://www.duolingo.com/guidebook/en/12',{waitUntil:'domcontentloaded'});await page.getByText('嗨，欢迎来到我的公寓！',{exact:true}).waitFor();await page.mouse.move(1190,730);await page.evaluate(()=>window.scrollTo(0,0));${stable}}`,a.id+'-reset');
 if(beforeReady.status!=='ready')throw Error('Guide root unavailable');
 const before=cap(a.id+'-before');roots.push(createHash('sha256').update(before.snapshot).digest('hex'));
 const receipt=run(`async page=>{const started=Date.now(),a=${JSON.stringify(a)},target=page.locator('[data-test="hint-token"]').nth(a.index);if((await target.getAttribute('aria-label'))!==a.text)throw Error('Observed token identity mismatch');if(a.operation==='Enter'){await target.focus();await target.press('Enter');}else if(a.operation==='click'){await target.click();}else if(a.operation==='hover'){await target.hover();}else throw Error('Unregistered operation');${stable}}`,a.id+'-action');
 const after=cap(a.id+'-after');writeFileSync(out+'/'+a.id+'-readiness.json',JSON.stringify({before:beforeReady,after:receipt},null,2)+'\n',{flag:'wx'});
 if(receipt.status!=='ready')throw Error('Action unavailable; not zero novelty');
 branches.push({action:a,before:a.id+'-before.json',after:a.id+'-after.json',before_path:before.path,after_path:after.path});
 console.log(JSON.stringify({action:a.id,observed:true,path:after.path}));
}
writeFileSync(out+'/collection.json',JSON.stringify({kind:'actual-guide-token-branches',root_snapshot_hashes:roots,identical_root_snapshots:new Set(roots).size===1,branches},null,2)+'\n',{flag:'wx'});
