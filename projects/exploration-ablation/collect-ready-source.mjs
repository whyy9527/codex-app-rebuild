// Batch03 measurement repair. Original batch02 collector remains frozen in Git.
// Markers derive from archived visible source, not from candidate implementation.
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
const readiness={
 pronunciation:{path:'/characters',markers:[{role:'link',name:'开始 +10 经验'},{role:'button',name:'ɑ hot 0'}]},
 leaderboards:{path:'/leaderboard',markers:[{text:'这周的排行榜挑战赛即将开始！'}]}
};
const roots=[],branches=[];
for(const action of actions){
 const reset=run(['run-code',`async page => { await page.goto('https://www.duolingo.com/learn',{waitUntil:'domcontentloaded'}); await page.getByRole('heading',{name:'第 1 阶段，第 1 部分',exact:true}).waitFor(); await page.getByRole('button',{name:'510',exact:true}).waitFor(); await page.mouse.move(1190,730); await page.waitForTimeout(600); return {path:new URL(page.url()).pathname}; }`]);
 writeFileSync(out+'/'+action.id+'-reset.raw.txt',reset,{flag:'wx'});
 const before=capture(action.id+'-before');roots.push(before);
 const gate=readiness[action.id];if(!gate)throw Error('No source-observed readiness markers for action');
 const code=`async page => {
  const started=Date.now(), gate=${JSON.stringify(gate)};
  const target=page.getByRole(${JSON.stringify(action.role)},{name:${JSON.stringify(action.name)},exact:true});
  if(await target.count()!==1)throw Error('Observed action must identify one current control');
  await target.${action.operation}();
  const deadline=Date.now()+15000;let previous=null,stable=0,samples=0;
  while(Date.now()<deadline){
   let ready=new URL(page.url()).pathname===gate.path;
   for(const marker of gate.markers){const loc=marker.text?page.getByText(marker.text,{exact:true}):page.getByRole(marker.role,{name:marker.name,exact:true});ready=ready&&await loc.count()===1&&await loc.isVisible();}
   const snapshot=await page.locator('body').ariaSnapshot();samples++;
   stable=ready&&snapshot===previous?stable+1:0;previous=snapshot;
   if(ready&&stable>=2)return {path:new URL(page.url()).pathname,readiness:{status:'ready',wall_ms:Date.now()-started,samples,stable_repeats:stable,markers:gate.markers}};
   await page.waitForTimeout(150);
  }
  return {path:new URL(page.url()).pathname,readiness:{status:'unavailable',reason:'source marker or semantic stabilization timeout',wall_ms:Date.now()-started,samples,markers:gate.markers}};
 }`;
 const actionResult=run(['run-code',code]);
 writeFileSync(out+'/'+action.id+'-action.raw.txt',actionResult,{flag:'wx'});
 const receipt=JSON.parse(actionResult.split('### Result\n')[1].split('\n### Ran')[0]);
 writeFileSync(out+'/'+action.id+'-readiness.json',JSON.stringify(receipt,null,2)+'\n',{flag:'wx'});
 const after=capture(action.id+'-after');
 if(receipt.readiness.status!=='ready')throw Error('Source readiness unavailable; capture preserved, no zero novelty score');
 branches.push({action,before:action.id+'-before.json',after:action.id+'-after.json',before_path:before.path,after_path:after.path});
 console.log(JSON.stringify({action:action.id,path:after.path,captured:true}));
}
const sha=s=>createHash('sha256').update(s).digest('hex');
const rootHashes=roots.map(x=>sha(x.snapshot));
const registration={kind:'actual-source-one-level-branches',root_snapshot_hashes:rootHashes,identical_root_snapshots:new Set(rootHashes).size===1,branches};
writeFileSync(out+'/collection.json',JSON.stringify(registration,null,2)+'\n',{flag:'wx'});
