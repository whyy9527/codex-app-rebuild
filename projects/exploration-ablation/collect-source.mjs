// Execute only actions observed in the source home snapshot; keep originals.
import {spawnSync} from 'node:child_process';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
const arg=n=>process.argv[process.argv.indexOf(n)+1];
const cli=arg('--cli'),session=arg('--session'),out=resolve(arg('--out'));
const actions=JSON.parse(readFileSync(arg('--actions'),'utf8'));
mkdirSync(out,{recursive:true});
function run(args,cwd=resolve('artifacts/output/playwright')){
 const r=spawnSync(cli,['-s='+session,...args],{cwd,encoding:'utf8',timeout:60000,maxBuffer:8*1024*1024});
 if(r.status!==0)throw Error('Source action unavailable: '+(r.stderr||r.stdout));
 return r.stdout;
}
function capture(stem){
 const r=spawnSync(process.execPath,['projects/duolingo-web/capture-visible-state.mjs','--cli',cli,'--session',session,'--out',out+'/'+stem],{encoding:'utf8',timeout:65000,maxBuffer:8*1024*1024});
 if(r.status!==0)throw Error('Source capture unavailable: '+(r.stderr||r.stdout));
 return JSON.parse(readFileSync(out+'/'+stem+'.json','utf8'));
}
const roots=[],branches=[];
for(const action of actions){
 const reset=run(['run-code',`async page => { await page.goto('https://www.duolingo.com/learn',{waitUntil:'domcontentloaded'}); await page.getByRole('heading',{name:'第 1 阶段，第 1 部分',exact:true}).waitFor(); await page.getByRole('button',{name:'510',exact:true}).waitFor(); await page.mouse.move(1190,730); await page.waitForTimeout(600); return {path:new URL(page.url()).pathname}; }`]);
 writeFileSync(out+'/'+action.id+'-reset.raw.txt',reset,{flag:'wx'});
 const before=capture(action.id+'-before');roots.push(before);
 const code=`async page => { const target=page.getByRole(${JSON.stringify(action.role)},{name:${JSON.stringify(action.name)},exact:true}); if(await target.count()!==1)throw Error('Observed action must identify one current control'); await target.${action.operation}(); await page.waitForTimeout(500); return {path:new URL(page.url()).pathname}; }`;
 writeFileSync(out+'/'+action.id+'-action.raw.txt',run(['run-code',code]),{flag:'wx'});
 const after=capture(action.id+'-after');
 branches.push({action,before:action.id+'-before.json',after:action.id+'-after.json',before_path:before.path,after_path:after.path});
 console.log(JSON.stringify({action:action.id,path:after.path,captured:true}));
}
const sha=s=>createHash('sha256').update(s).digest('hex');
const rootHashes=roots.map(x=>sha(x.snapshot));
const registration={kind:'actual-source-one-level-branches',root_snapshot_hashes:rootHashes,identical_root_snapshots:new Set(rootHashes).size===1,branches};
writeFileSync(out+'/collection.json',JSON.stringify(registration,null,2)+'\n',{flag:'wx'});
