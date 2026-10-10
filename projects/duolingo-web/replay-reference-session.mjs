// Replay a captured public reference session and retain actual UI ordering and interludes.
// Run after capture-reference-session.mjs on the same owned tab. Resume explicitly by index.
import {spawnSync} from 'node:child_process';
import {writeFileSync,mkdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {challengeIdentity} from './reference-challenge-identity.mjs';
function arg(name,fallback){const i=process.argv.indexOf(name);return i<0?fallback:process.argv[i+1];}
for(const name of ['--cli','--session','--out'])if(!arg(name))throw Error('Required: --cli PATH --session NAME --out PATH [--start-index N]');
const uiLanguage=arg('--ui-language','en');
if(!['en','zh'].includes(uiLanguage))throw Error('Unsupported UI language: '+uiLanguage);
const labels=uiLanguage==='zh'?{check:'检查',continue:'继续'}:{check:'Check',continue:'Continue'};
const start=Number(arg('--start-index','0'));
if(!Number.isInteger(start)||start<0)throw Error('Invalid start index');
const output=resolve(arg('--out'));mkdirSync(dirname(output),{recursive:true});
const callback = async page => {
 const labels=UI_LABELS;
 const identity=CHALLENGE_IDENTITY;
 const session=await page.evaluate(()=>window.__referenceSession);
 const observed=[],interludes=[];let failure=null;
 async function exactVisible(locator,text){
   const labels=await locator.allTextContents();
   const indices=labels.flatMap((label,i)=>label.trim().replace(/^\d\s*|\s*\d$/g,'').trim()===text?[i]:[]);
   if(indices.length!==1)throw new Error('Reference option not unique: '+text+' labels='+JSON.stringify(labels));
   await locator.nth(indices[0]).click();
 }
 async function clickWord(bank,text){
   const matches=bank.getByRole('button',{name:text,exact:true});
   for(let i=0;i<await matches.count();i++){
    const button=matches.nth(i);
    if(await button.isVisible() && await button.isEnabled()) { await button.click(); return i; }
   }
   throw new Error('No available occurrence of word: '+text);
 }
 for(const record of session.challenges.filter(row=>row.index>=START_INDEX)){
  const c=record.content,row={index:record.index,type:c.type,actions:[]};observed.push(row);
  try{
   for(let transition=0;transition<6;transition++){
    await page.waitForFunction(labels=>{const n=document.querySelectorAll('[data-test="challenge-header"]').length,b=document.querySelector('[data-test="player-next"]');return b&&((n===1&&document.querySelectorAll('[data-test~="challenge"]').length===1&&b.textContent.trim()===labels.check)||(n===0&&b.textContent.trim()===labels.continue));},labels);
    if(await page.getByRole('heading',{level:1}).count()===1)break;
    interludes.push({before_index:record.index,snapshot:await page.locator('body').ariaSnapshot()});
    await page.getByRole('button',{name:labels.continue,exact:true}).click();
   }
   await page.getByRole('heading',{level:1}).waitFor();
   row.before=await page.locator('body').ariaSnapshot();
   row.heading=await page.getByRole('heading',{level:1}).textContent();
   row.dom_type=await page.locator('[data-test~="challenge"]').getAttribute('data-test');
   row.images=await page.locator('[data-test~="challenge"] img').evaluateAll(ns=>ns.map(n=>({alt:n.alt,src:n.currentSrc||n.src})));
   row.media_before=await page.evaluate(()=>window.__referenceMedia.slice());
   row.screenshot_before=SCREENSHOT_PREFIX+'-question-'+record.index+'-before.png';
   await page.screenshot({path:row.screenshot_before});
   const mediaStart=await page.evaluate(()=>window.__referenceMedia.length);
   const challenge=page.locator('[data-test~="challenge"]');
   const radioTexts=await challenge.getByRole('radio').allTextContents();
   const bank=challenge.locator('[data-test="word-bank"]');
   const bankTexts=await bank.getByRole('button').allTextContents();
   const buttons=await challenge.getByRole('button').allTextContents();
   const visibleChoices=radioTexts.length ? radioTexts.map(t=>t.trim().replace(/^\d\s*|\s*\d$/g,'').trim()) : bankTexts.length ? bankTexts : buttons.filter(t=>t.trim()&&! [labels.check,labels.continue,'跳过','Skip','使用键盘','Use keyboard'].includes(t.trim()));
   const prompts=await challenge.locator('[data-test=hint-token]').evaluateAll(ns=>[...new Set(ns.map(n=>n.parentElement.innerText.trim()).filter(Boolean))]);
   if(!prompts.length && c.type==='select'){const quoted=row.heading.match(/[“「](.+?)[”」]/);if(quoted)prompts.push(quoted[1]);}
   const playedAudio=[];
   if(c.type==='listenTap'){
    // Observed normal-speaker SVG, independently inspected on the real source.
    const speaker=challenge.getByRole('button').filter({has:page.locator('svg[viewBox="0 0 94 73"]')});
    const playbackStart=await page.evaluate(()=>window.__referenceMedia.length);
    await speaker.click();
    await page.waitForFunction(start=>window.__referenceMedia.slice(start).some(m=>m.src.startsWith('https://d1vq87e9lcf771.cloudfront.net/')),playbackStart);
    row.identity_playback=await page.evaluate(start=>window.__referenceMedia.slice(start),playbackStart);
    playedAudio.push(...new Set(row.identity_playback.map(m=>m.src).filter(Boolean)));
   }
   row.identity=identity(c,{type:row.dom_type,text:await challenge.innerText(),choices:visibleChoices,prompts,playedAudio});
   row.dom_fields=await challenge.locator('[data-test]').evaluateAll(ns=>ns.map(n=>({test:n.getAttribute('data-test'),text:n.textContent})));
   if(!row.identity.matches){row.divergence={kind:row.identity.reasons.includes('type_changed')?'type_changed':'same_type_content_changed',next_action:'Read current prompt and complete choice set; do not reuse captured answer. Record new observed branch before resuming.'};throw new Error('Reference UI diverged: '+row.identity.reasons.join(', '));}
   if(['select','assist','dialogue'].includes(c.type)){
    const choice=c.choices[c.correctIndex],text=typeof choice==='string'?choice:choice.phrase;
    await exactVisible(page.getByRole('radio'),text);row.actions.push({select:text});
    await page.getByRole('button',{name:labels.check,exact:true}).click();
   }else if(['translate','listenTap'].includes(c.type)){
    const bank=page.locator('[data-test="word-bank"]');row.word_bank=await bank.getByRole('button').allTextContents();
    for(const index of c.correctIndices){const choice=c.choices[index],text=typeof choice==='string'?choice:choice.text;
     const occurrence=await clickWord(bank,text);row.actions.push({word:text,occurrence});}
    await page.getByRole('button',{name:labels.check,exact:true}).click();
   }else if(c.type==='orderTapComplete'){
    const blanks=c.displayTokens.filter(token=>token.isBlank).map(token=>token.text);
    row.word_bank=[];
    for(const choice of c.choices){const button=page.getByRole('button',{name:choice.text,exact:true});await button.waitFor();row.word_bank.push(await button.textContent());}
    for(const text of blanks){await page.getByRole('button',{name:text,exact:true}).click();row.actions.push({word:text});}
    await page.getByRole('button',{name:labels.check,exact:true}).click();
   }else if(c.type==='match'){

    row.button_order=await page.getByRole('button').allTextContents();
    for(const pair of c.pairs){for(const text of [pair.fromToken,pair.learningToken]){await exactVisible(page.getByRole('button'),text);row.actions.push({match:text});}}
   }else throw new Error('Uncovered type: '+c.type);
   await page.getByRole('button',{name:labels.continue,exact:true}).waitFor();
   row.feedback=await page.locator('body').ariaSnapshot();
   row.media=await page.evaluate(start=>window.__referenceMedia.slice(start),mediaStart);
   row.screenshot_feedback=SCREENSHOT_PREFIX+'-question-'+record.index+'-feedback.png';
   await page.screenshot({path:row.screenshot_feedback});
   if(await page.locator('[data-test~="blame-incorrect"]').count())throw new Error('Source answer rejected');
   await page.getByRole('button',{name:labels.continue,exact:true}).click();
  }catch(error){failure=String(error);break;}
 }
 return {session,observed,interludes,failure,final:await page.locator('body').ariaSnapshot(),limitations:['One actual generated lesson instance; media invocations are not acoustic output evidence.']};
};
const code=callback.toString().replace('CHALLENGE_IDENTITY',challengeIdentity.toString()).replace('UI_LABELS',JSON.stringify(labels)).replace('START_INDEX',String(start)).replaceAll('SCREENSHOT_PREFIX',JSON.stringify(arg('--screenshot-prefix','reference-session')));
const result=spawnSync(arg('--cli'),['-s='+arg('--session'),'run-code',code],{cwd:resolve('artifacts/output/playwright'),encoding:'utf8',timeout:300000,maxBuffer:16*1024*1024});
const raw=(result.stdout||'')+(result.stderr||'');writeFileSync(output+'.raw.txt',raw,{flag:'wx'});
if(result.status!==0||!raw.includes('### Result\n'))throw Error('Unavailable replay; raw output retained, inspect current tab before resuming');
const facts=JSON.parse(raw.split('### Result\n')[1].split('\n### Ran')[0]);
writeFileSync(output,JSON.stringify({...facts,observed_at:new Date().toISOString()},null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({observed:facts.observed.length,interludes:facts.interludes.length,failure:facts.failure}));
if(facts.failure)process.exitCode=1;
