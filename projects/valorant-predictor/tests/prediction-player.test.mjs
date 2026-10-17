import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {formalPredictions,playerMarkup} from '../prediction-player.mjs';
const load=id=>JSON.parse(readFileSync(new URL(`../data/forecast-v2/${id}.json`,import.meta.url)));
test('new-chain waiting page never substitutes historical trajectories or seeded scores',()=>{
 const html=playerMarkup('<div>four model selector</div>');assert.match(html,/awaiting-new-chain/);assert.match(html,/逐步推演待生成/);assert.doesNotMatch(html,/tactical-replay|本轮模拟冠军|3 : 2/);assert.match(html,/disabled/);
});
test('existing deterministic modes remain separate from seeded results for the audit report',()=>{
 const result=load('codex'),rows=formalPredictions(result);assert.equal(rows.length,3);
 for(const row of rows){assert.equal(row.distribution.length,6);assert.ok(Math.abs(row.distribution.reduce((n,r)=>n+r.probability,0)-1)<1e-12);assert.equal(row.modes[0].probability,Math.max(...row.distribution.map(r=>r.probability)));}
 assert.deepEqual(rows.find(r=>r.key==='gf_100t').modes[0].score,[3,1]);assert.deepEqual(result.computed.sample.series[1].score,[3,2]);
 const bean=formalPredictions(load('doubao'))[0];assert.equal(bean.favorite,'100T');assert.deepEqual(bean.modes[0].score,[3,1]);
});
