import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,mkdtempSync,writeFileSync,existsSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {spawnSync} from 'node:child_process';
import {challengeIdentity,uncoveredReplayType} from './reference-challenge-identity.mjs';
const read=name=>JSON.parse(readFileSync(new URL('evidence/english-general-practice-v1/'+name,import.meta.url)));
const source=read('session.json').session.challenges;
const row=(file,index)=>read(file).observed.find(r=>r.index===index);

test('actual audio pairs accept shuffling, but missing or duplicated visible targets fail',()=>{
 const c=source[0].content,a=row('replay.json',0).identity.actual;
 assert.equal(challengeIdentity(c,a).matches,true);
 assert.equal(challengeIdentity(c,{...a,choices:[...a.choices].reverse()}).matches,true);
 assert.equal(challengeIdentity(c,{...a,choices:a.choices.slice(1)}).matches,false);
 assert.equal(challengeIdentity(c,{...a,choices:a.choices.map(()=>a.choices[0])}).matches,false);
});
test('same isolation choices cannot hide a different sentence',()=>{
 const c=source[5].content,a=row('replay-from-5.json',5).identity.actual;
 assert.equal(challengeIdentity(c,a).matches,true);
 assert.equal(challengeIdentity({...c,tokens:[{value:'Different sentence.'}]},a).matches,false);
});
test('actual listening playback and completion context both identify the question',()=>{
 for(const i of [11,12]){
  const c=source[i].content,a=row('replay-from-11.json',i).identity.actual;
  assert.equal(challengeIdentity(c,a).matches,true);
  assert.equal(challengeIdentity(c,{...a,playedAudio:[]}).matches,false);
 }
 const c=source[12].content,a=row('replay-from-11.json',12).identity.actual;
 assert.ok(challengeIdentity(c,{...a,text:'another completion'}).reasons.includes('completion_context_changed'));
 // The actual keyboard preference remains a schema mismatch, not a silently
 // accepted empty word bank. The caller observes/toggles modes separately.
 const keyboard=row('replay-from-5.json',6).identity.actual;
 assert.equal(challengeIdentity(source[6].content,keyboard).matches,false);
 assert.equal(uncoveredReplayType('name','challenge challenge-name'),true);
});
test('a pre-existing screenshot stops both answer tools before invoking a browser',()=>{
 const dir=mkdtempSync(join(tmpdir(),'practice-collision-'));
 try{
  const prefix=join(dir,'answer'),out=join(dir,'receipt.json'),image=prefix+'-before.png';
  writeFileSync(image,'original frame');
  for(const [script,args] of [['answer-text-reference-live.mjs',['--label','input','--text','value']],['answer-reference-live.mjs',['--words','["value"]']]]){
   const result=spawnSync(process.execPath,[new URL(script,import.meta.url).pathname,'--cli',join(dir,'must-not-run'),'--session','owned','--out',out,'--screenshot-prefix',prefix,...args],{encoding:'utf8'});
   assert.equal(result.status,1);assert.match(result.stderr,/choose fresh/);
   assert.equal(readFileSync(image,'utf8'),'original frame');
   assert.equal(existsSync(out+'.intent.json'),false);assert.equal(existsSync(out+'.raw.txt'),false);
  }
 }finally{rmSync(dir,{recursive:true,force:true});}
});
