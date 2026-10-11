// Read visible DOM/AX in the owned source page, without hidden session/React payloads.
import {spawnSync} from 'node:child_process';
import {writeFileSync,mkdirSync,existsSync} from 'node:fs';
import {resolve,dirname,basename} from 'node:path';
function arg(name){const i=process.argv.indexOf(name);if(i<0||!process.argv[i+1])throw Error('Required '+name);return process.argv[i+1];}
const out=resolve(arg('--out'));mkdirSync(dirname(out),{recursive:true});
for(const suffix of ['.raw.txt','.json','.png'])if(existsSync(out+suffix))throw Error('Observation output already exists: '+basename(out)+suffix+'; choose a fresh stem before any source action');
const callback=async page=>{
 const facts={observed_at:new Date().toISOString(),path:new URL(page.url()).pathname,
  viewport:page.viewportSize(),snapshot:await page.locator('body').ariaSnapshot()};
 // Generic text blocks (reward titles, subtitles and hints) were missing
 // from the element selector. Read actual rendered text ranges, never hidden
 // application state, and keep their own computed typography.
 facts.text_runs=await page.locator('body').evaluate(body=>{
  const walker=document.createTreeWalker(body,NodeFilter.SHOW_TEXT),rows=[];
  for(let n=walker.nextNode();n;n=walker.nextNode()){
   const p=n.parentElement,text=n.textContent.trim();
   if(!text||!p||['SCRIPT','STYLE','NOSCRIPT'].includes(p.tagName)||!p.checkVisibility())continue;
   const range=document.createRange();range.selectNodeContents(n);const r=range.getBoundingClientRect();
   if(r.width<=0||r.height<=0||r.bottom<=0||r.right<=0||r.top>=innerHeight||r.left>=innerWidth)continue;
   const c=getComputedStyle(p);
   rows.push({text,tag:p.tagName,test:p.getAttribute('data-test'),rect:[r.x,r.y,r.width,r.height],
    css:{fontFamily:c.fontFamily,fontSize:c.fontSize,fontWeight:c.fontWeight,fontVariationSettings:c.fontVariationSettings,lineHeight:c.lineHeight,color:c.color,letterSpacing:c.letterSpacing}});
  }return rows;
 });
 facts.text_run_limitations=['DOM text ranges and computed CSS are not OCR or actual fallback font resolution; clipped animation digits may still appear.'];
 // Artwork outside buttons was absent from the old mold. Keep visible media
 // geometry and public resource identity without reading application state.
 facts.media=await page.locator('img,svg,canvas').evaluateAll(ns=>ns.filter(n=>n.checkVisibility()).map(n=>{
  const r=n.getBoundingClientRect(),css=getComputedStyle(n);
  const src=n.tagName==='IMG'?(n.currentSrc||n.src):null;
  return {tag:n.tagName,svg:n.tagName.toLowerCase()==='svg'?n.outerHTML:null,alt:n.getAttribute('alt'),test:n.getAttribute('data-test'),
   src:src&&!src.startsWith('data:')&&!src.startsWith('blob:')?src:null,
   source_kind:src?.startsWith('data:')?'inline':src?.startsWith('blob:')?'blob':src?'url':null,
   rect:[r.x,r.y,r.width,r.height],objectFit:css.objectFit,
   intrinsic:n.tagName==='IMG'?[n.naturalWidth,n.naturalHeight]:n.tagName==='CANVAS'?[n.width,n.height]:null};
 }));
 // CSS artwork (for example profile Duo) is not an img/svg/canvas node.
 facts.background_media=await page.locator('body *').evaluateAll(ns=>ns.flatMap(n=>{
  const r=n.getBoundingClientRect(),c=getComputedStyle(n),background=c.backgroundImage;
  if(!n.checkVisibility()||background==='none'||r.width<=0||r.height<=0||r.bottom<=0||r.right<=0||r.top>=innerHeight||r.left>=innerWidth)return [];
  return [{tag:n.tagName,test:n.getAttribute('data-test'),rect:[r.x,r.y,r.width,r.height],backgroundImage:background,backgroundSize:c.backgroundSize,backgroundPosition:c.backgroundPosition,backgroundRepeat:c.backgroundRepeat}];
 }));
 // Pseudo-elements can draw the actual control face without a DOM child.
 facts.pseudo_elements=await page.locator('body *').evaluateAll(ns=>ns.flatMap(n=>{
  const r=n.getBoundingClientRect();
  if(!n.checkVisibility()||r.width<=0||r.height<=0||r.bottom<=0||r.right<=0||r.top>=innerHeight||r.left>=innerWidth)return [];
  return ['::before','::after'].flatMap(p=>{const c=getComputedStyle(n,p);
   if(c.content==='none'||c.content==='normal')return [];
   return [{tag:n.tagName,test:n.getAttribute('data-test'),pseudo:p,parent_rect:[r.x,r.y,r.width,r.height],css:{content:c.content,width:c.width,height:c.height,top:c.top,left:c.left,color:c.color,backgroundColor:c.backgroundColor,backgroundImage:c.backgroundImage,borderRadius:c.borderRadius,transform:c.transform,boxShadow:c.boxShadow}}];
  });
 }));
 facts.pseudo_limitations=['Computed CSS and parent bounds only; pseudo-elements have no independently measured DOM bounding rectangle.'];
 facts.visible=await page.locator('[data-test],h1,h2,[role],button,input,label').evaluateAll(ns=>ns.filter(n=>n.checkVisibility()).map(n=>{
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
