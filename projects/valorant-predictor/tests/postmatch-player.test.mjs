import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {causalTimeline} from '../causal-player.mjs';
test('grand-final timeline preserves case identity, starts at zero and contains no loser-final frames',()=>{
 const raw=readFileSync(new URL('../data/causal/deepseek.json',import.meta.url),'utf8'),data=JSON.parse(raw),frames=causalTimeline(data,1);
 assert.equal(frames[0].start,0);assert.ok(frames.every(f=>f.caseIndex===1&&f.teams.join(',')==='LOUD,VIT'));assert.equal(frames.filter(f=>f.kind==='round_end').length,data.cases[1].frames.filter(f=>f.kind==='round_end').length);assert.equal(frames.at(-1).kind,'series_end');assert.equal(frames.at(-1).winner,'LOUD');assert.equal(JSON.stringify(data),JSON.stringify(JSON.parse(raw)));
 const archive=causalTimeline(data);assert.ok(archive.some(f=>f.caseIndex===0));assert.ok(archive.some(f=>f.caseIndex===1));
});
