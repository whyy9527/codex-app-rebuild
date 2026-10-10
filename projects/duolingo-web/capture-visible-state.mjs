// Read visible DOM/AX in the owned source page, without hidden session/React payloads.
import {spawnSync} from 'node:child_process';
import {writeFileSync,mkdirSync} from 'node:fs';
import {resolve,dirname,basename} from 'node:path';
function arg(name){const i=process.argv.indexOf(name);if(i<0||!process.argv[i+1])throw Error('Required '+name);return process.argv[i+1];}
const out=resolve(arg('--out'));mkdirSync(dirname(out),{recursive:true});
const callback=async page=>{
 const facts={observed_at:new Date().toISOString(),path:new URL(page.url()).pathname,
  viewport:page.viewportSize(),snapshot:await page.locator('body').ariaSnapshot()};
 facts.visible=await page.locator('[data-test],h1,h2,[role="dialog"],button,input,label').evaluateAll(ns=>ns.filter(n=>n.checkVisibility()).map(n=>{
  const r=n.getBoundingClientRect(),css=getComputedStyle(n);
  return {test:n.getAttribute('data-test'),tag:n.tagName,role:n.getAttribute('role'),text:n.innerText,
   enabled:!n.disabled&&n.getAttribute('aria-disabled')!=='true',pressed:n.getAttribute('aria-pressed'),checked:n.checked??null,
   rect:[r.x,r.y,r.width,r.height],css:{fontFamily:css.fontFamily,fontSize:css.fontSize,fontWeight:css.fontWeight,lineHeight:css.lineHeight,color:css.color,backgroundColor:css.backgroundColor,borderRadius:css.borderRadius,borderWidth:css.borderWidth,borderColor:css.borderColor},
   icons:n.tagName==='BUTTON'?[...n.querySelectorAll('svg')].map(svg=>svg.outerHTML):[],
   images:n.tagName==='BUTTON'?[...n.querySelectorAll('img')].map(img=>({src:img.currentSrc||img.src,rect:img.getBoundingClientRect().toJSON()})):[],
   iconDetails:n.tagName==='BUTTON'?[...n.querySelectorAll('svg')].map(svg=>({rect:svg.getBoundingClientRect().toJSON(),color:getComputedStyle(svg).color})):[],
   ancestors:n.tagName==='BUTTON'?[n.parentElement,n.parentElement?.parentElement,n.parentElement?.parentElement?.parentElement].filter(Boolean).map(a=>({tag:a.tagName,rect:a.getBoundingClientRect().toJSON(),backgroundColor:getComputedStyle(a).backgroundColor,borderRadius:getComputedStyle(a).borderRadius,padding:getComputedStyle(a).padding,gap:getComputedStyle(a).gap})):[]};
 }));
 await page.screenshot({path:SCREENSHOT});
 return facts;
};
const r=spawnSync(arg('--cli'),['-s='+arg('--session'),'run-code',callback.toString().replace('SCREENSHOT',JSON.stringify(out+'.png'))],
 {cwd:resolve('artifacts/output/playwright'),encoding:'utf8',timeout:60000,maxBuffer:8*1024*1024});
writeFileSync(out+'.raw.txt',(r.stdout||'')+(r.stderr||''),{flag:'wx'});
if(r.status!==0||!r.stdout.includes('### Result\n'))throw Error('Observation unavailable; inspect current tab before retry');
const facts=JSON.parse(r.stdout.split('### Result\n')[1].split('\n### Ran')[0]);
facts.screenshot=basename(out)+'.png';
writeFileSync(out+'.json',JSON.stringify(facts,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({observed:true,path:facts.path,visible: facts.visible.length}));
