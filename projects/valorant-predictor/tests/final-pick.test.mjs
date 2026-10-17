import test from 'node:test';
import assert from 'node:assert/strict';
import {makeFinalPick,validateFinalPick} from '../final-pick.mjs';
test('final votes require the verified fixture, aligned BO5 score and new scope',()=>{
 const vote=makeFinalPick({champion:'VIT',score:[2,3]},'input-hash','2026-10-17T14:00:00Z');assert.equal(validateFinalPick(vote),true);
 for(const patch of [{version:1},{scope:'old'},{teams:['VIT','LOUD']},{match_id:'old'},{champion:'100T'},{score:[3,2]},{score:[3,3]},{score:[-1,3]},{score:[1.5,3]},{created_at:'invalid'}])assert.equal(validateFinalPick({...vote,...patch}),false);
 assert.equal(validateFinalPick({version:1,champion:'VIT',gfScore:[2,3]}),false);
});
test('making a final vote leaves a historical vote and the draft unchanged',()=>{
 const old={version:1,champion:'100T',gfScore:[1,3],lfWinner:'100T'},before=JSON.stringify(old),draft={champion:'LOUD',score:[3,0]};const vote=makeFinalPick(draft,'hash');vote.score[0]=0;assert.deepEqual(draft,{champion:'LOUD',score:[3,0]});assert.equal(JSON.stringify(old),before);
});
