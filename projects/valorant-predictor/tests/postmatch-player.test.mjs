import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {causalTimeline} from '../causal-player.mjs';
test('grand-final timeline preserves case identity, starts at zero and contains no loser-final frames',()=>{
 const raw=readFileSync(new URL('../data/causal/deepseek.json',import.meta.url),'utf8'),data=JSON.parse(raw),frames=causalTimeline(data,1);
 assert.equal(frames[0].start,0);assert.ok(frames.every(f=>f.caseIndex===1&&f.teams.join(',')==='LOUD,VIT'));assert.equal(frames.filter(f=>f.kind==='round_end').length,data.cases[1].frames.filter(f=>f.kind==='round_end').length);assert.equal(frames.at(-1).kind,'series_end');assert.equal(frames.at(-1).winner,'LOUD');assert.equal(JSON.stringify(data),JSON.stringify(JSON.parse(raw)));
 const archive=causalTimeline(data);assert.ok(archive.some(f=>f.caseIndex===0));assert.ok(archive.some(f=>f.caseIndex===1));
});

import {causalProjection} from '../current-data.mjs';
test('isolated final remains a final and cannot create a retrospective loser-final prediction',()=>{
 const original=JSON.parse(readFileSync(new URL('../data/causal/deepseek.json',import.meta.url),'utf8'));
 const data={...structuredClone(original.cases[1]),case_id:'gf',match_id:'actual-final',version_kind:'postmatch_rerun',exclude_from_original_prematch_accuracy:true,prediction_version:'unit-test-only'};
 const frames=causalTimeline(data,1);assert.ok(frames.length);assert.ok(frames.every(f=>f.caseIndex===1));assert.deepEqual(causalTimeline(data,0),[]);
 const summary=causalProjection(data,{match_ids:['old-loser-final','actual-final'],finalists:['LOUD','VIT'],recorded_at:'2026-10-17T12:00:00Z'});
 assert.equal(summary.cases.length,1);assert.equal(summary.cases[0].id,'gf');assert.equal(summary.cases[0].match_id,'actual-final');assert.equal(summary.version_kind,'postmatch_rerun');assert.equal(summary.cases[0].round_count,data.frames.filter(f=>f.kind==='round_end').length);
 assert.throws(()=>causalProjection({...data,state:{...data.state,stage:'opening'}},{match_ids:['lf','actual-final']}),/Incomplete isolated final/);
 assert.throws(()=>causalProjection({...data,teams:['LOUD','100T']},{match_ids:['lf','actual-final']}),/actual final/);
});
