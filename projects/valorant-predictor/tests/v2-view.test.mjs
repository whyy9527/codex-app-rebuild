import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {v2Markup} from '../forecast-v2.mjs';
const load=name=>JSON.parse(readFileSync(new URL('../data/'+name,import.meta.url)));
const pack=load('evidence-v2.json');
test('real v2 output renders five maps, seven factors and provenance for all three cases',()=>{
 const result=load('forecast-v2/codex.json');
 for(const key of ['lf','gf_vit','gf_100t']){
  const html=v2Markup(result,pack,key,'codex');
  assert.equal((html.match(/class="v2-map"/g)||[]).length,5);
  assert.equal((html.match(/<article><h4>/g)||[]).length,7);
  assert.ok(html.includes(result.input_sha256));assert.ok(html.includes('不是实际'));
  assert.ok(html.includes('data/forecast-v2/codex.json'));
 }
 const sum=Object.values(result.computed.champion_probabilities).reduce((n,p)=>n+p,0);assert.ok(Math.abs(sum-1)<1e-12);
});
test('missing result and missing model review are explicit, never filled with invented output',()=>{
 assert.match(v2Markup(null,pack),/尚未完成/);
 const result=load('forecast-v2/deepseek.json'),html=v2Markup(result,pack,'lf','deepseek');
 assert.equal(result.fictional_review,null);assert.match(html,/文字复盘未完成/);assert.match(html,/不补写或冒充/);
});

test('DeepSeek direction contradictions are explicit while original numeric probabilities remain unchanged',()=>{
 const result=load('forecast-v2/deepseek.json');assert.equal(result.fact_consistency_findings.length,9);
 const map=result.selected.cases.lf.maps.find(m=>m.map==='Ascent');assert.equal(map.p_first,.55);assert.match(map.reason,/p偏100T/);
 const html=v2Markup(result,pack,'lf','deepseek');assert.match(html,/理由方向与数值矛盾/);assert.match(html,/不能据此声称其判断前后一致/);
});
