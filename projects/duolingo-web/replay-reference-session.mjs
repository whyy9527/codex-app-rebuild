// Replay a captured public reference session and retain actual UI ordering and interludes.
// Run after capture-reference-session.mjs on the same owned tab. Resume explicitly by index.
import {spawnSync} from 'node:child_process';
import {writeFileSync,mkdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
function arg(name,fallback){const i=process.argv.indexOf(name);return i<0?fallback:process.argv[i+1];}
for(const name of ['--cli','--session','--out'])if(!arg(name))throw Error('Required: --cli PATH --session NAME --out PATH [--start-index N]');
const start=Number(arg('--start-index','0'));
if(!Number.isInteger(start)||start<0)throw Error('Invalid start index');
const output=resolve(arg('--out'));mkdirSync(dirname(output),{recursive:true});
const callback = async page => {
 const session=await page.evaluate(()=>window.__referenceSession);
 const observed=[],interludes=[];let failure=null;
 async function exactVisible(locator,text){
   const labels=await locator.allTextContents();
   const indices=labels.flatMap((label,i)=>label.trim().replace(/^\d\s*|\s*\d$/g,'').trim()===text?[i]:[]);
   if(indices.length!==1)throw new Error('Reference option not unique: '+text+' labels='+JSON.stringify(labels));
   await locator.nth(indices[0]).click();
 }
 for(const record of session.challenges.filter(row=>row.index>=START_INDEX)){
  const c=record.content,row={index:record.index,type:c.type,actions:[]};observed.push(row);
  try{
   for(let transition=0;transition<6;transition++){
    await page.waitForFunction(()=>{const n=document.querySelectorAll('[data-test="challenge-header"]').length,b=document.querySelector('[data-test="player-next"]');return b&&((n===1&&b.textContent.trim()==='Check')||(n===0&&b.textContent.trim()==='Continue'));});
    if(await page.getByRole('heading',{level:1}).count()===1)break;
    interludes.push({before_index:record.index,snapshot:await page.locator('body').ariaSnapshot()});
    await page.getByRole('button',{name:'Continue',exact:true}).click();
   }
   await page.getByRole('heading',{level:1}).waitFor();
   row.before=await page.locator('body').ariaSnapshot();
   row.heading=await page.getByRole('heading',{level:1}).textContent();
   row.screenshot_before=SCREENSHOT_PREFIX+'-question-'+record.index+'-before.png';
   await page.screenshot({path:row.screenshot_before});
   const mediaStart=await page.evaluate(()=>window.__referenceMedia.length);
   if(['select','assist'].includes(c.type)){
    const choice=c.choices[c.correctIndex],text=typeof choice==='string'?choice:choice.phrase;
    await exactVisible(page.getByRole('radio'),text);row.actions.push({select:text});
    await page.getByRole('button',{name:'Check',exact:true}).click();
   }else if(c.type==='translate'){
    const bank=page.locator('[data-test="word-bank"]');row.word_bank=await bank.getByRole('button').allTextContents();
    for(const index of c.correctIndices){const choice=c.choices[index],text=typeof choice==='string'?choice:choice.text;
     await bank.getByRole('button',{name:text,exact:true}).click();row.actions.push({word:text});}
    await page.getByRole('button',{name:'Check',exact:true}).click();
   }else if(c.type==='match'){
    row.button_order=await page.getByRole('button').allTextContents();
    for(const pair of c.pairs){for(const text of [pair.fromToken,pair.learningToken]){await exactVisible(page.getByRole('button'),text);row.actions.push({match:text});}}
   }else throw new Error('Uncovered type: '+c.type);
   await page.getByRole('button',{name:'Continue',exact:true}).waitFor();
   row.feedback=await page.locator('body').ariaSnapshot();
   row.media=await page.evaluate(start=>window.__referenceMedia.slice(start),mediaStart);
   if(row.feedback.includes('Correct solution'))throw new Error('Source answer rejected');
   row.screenshot_feedback=SCREENSHOT_PREFIX+'-question-'+record.index+'-feedback.png';
   await page.screenshot({path:row.screenshot_feedback});
   await page.getByRole('button',{name:'Continue',exact:true}).click();
  }catch(error){failure=String(error);break;}
 }
 return {session,observed,interludes,failure,final:await page.locator('body').ariaSnapshot(),limitations:['One actual generated lesson instance; media invocations are not acoustic output evidence.']};
};
const code=callback.toString().replace('START_INDEX',String(start)).replaceAll('SCREENSHOT_PREFIX',JSON.stringify(arg('--screenshot-prefix','reference-session')));
const result=spawnSync(arg('--cli'),['-s='+arg('--session'),'run-code',code],{cwd:resolve('artifacts/output/playwright'),encoding:'utf8',timeout:300000,maxBuffer:16*1024*1024});
const raw=(result.stdout||'')+(result.stderr||'');writeFileSync(output+'.raw.txt',raw,{flag:'wx'});
if(result.status!==0||!raw.includes('### Result\n'))throw Error('Unavailable replay; raw output retained, inspect current tab before resuming');
const facts=JSON.parse(raw.split('### Result\n')[1].split('\n### Ran')[0]);
writeFileSync(output,JSON.stringify({...facts,observed_at:new Date().toISOString()},null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({observed:facts.observed.length,interludes:facts.interludes.length,failure:facts.failure}));
if(facts.failure)process.exitCode=1;
