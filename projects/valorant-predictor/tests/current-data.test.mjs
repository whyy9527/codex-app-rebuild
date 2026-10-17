import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {causalProjection,factualEvent,settleCausal,currentFixture,fixturePrediction} from '../current-data.mjs';
const read=name=>JSON.parse(readFileSync(new URL('../data/'+name,import.meta.url))),event=read('event.json'),official=read('archive/2026-10-17.json').official_snapshot_before_update;
const models=Object.fromEntries(['codex','deepseek','doubao','mimo'].map(channel=>{const bytes=readFileSync(new URL('../data/causal/'+channel+'.json',import.meta.url)),data=JSON.parse(bytes);return [channel,{data,projection:causalProjection(data,{model:data.cases[0].records[0].runtime_attestation.model,source_file:'data/causal/'+channel+'.json',source_sha256:createHash('sha256').update(bytes).digest('hex'),recorded_at:'2026-10-17T02:56:46Z',match_ids:event.matches.map(m=>m.id),finalists:event.predecessors.flatMap(m=>m.teams)})}];}));
const summary={models:Object.fromEntries(Object.entries(models).map(([id,v])=>[id,v.projection]))};
function completed(){const actual=structuredClone(official);actual.fetched_at='2026-10-17T12:00:00Z';Object.assign(actual.matches[0],{state:'completed',winner:'100T',score:[3,1]});return actual;}
test('current projection preserves all four actual pairs, scores, maps, BP and 597 rounds',()=>{
 let total=0;
 for(const {data,projection:m} of Object.values(models)){
  assert.equal(m.source_file,'data/causal/'+data.channel+'.json');
  for(const [i,p] of data.cases.entries()){
   const v=m.cases[i];assert.deepEqual(v.teams,p.teams);assert.deepEqual(v.score,p.state.series_score);assert.equal(v.winner,p.state.winner);assert.deepEqual(v.bp,p.bp);assert.deepEqual(v.maps.map(x=>[x.map,x.score,x.winner]),p.state.completed_maps.map(x=>[x.map,x.score,x.winner]));assert.equal(v.round_count,p.frames.filter(f=>f.kind==='round_end').length);assert.equal(v.maps.flatMap(x=>x.lineup).length,p.state.completed_maps.length*10);total+=v.round_count;
  }
  assert.equal(m.cases[1].teams[1],m.cases[0].winner);assert.equal(m.result_order[0],m.cases[1].winner);
 }
 assert.equal(total,597);
});
test('player statistics count only accepted model events, never synthetic ratings',()=>{
 for(const {data,projection:m} of Object.values(models)){
  const kills=data.cases.flatMap(p=>p.frames).filter(f=>f.event?.kind==='kill').length;assert.equal(m.players.reduce((n,p)=>n+p.kills,0),kills);assert.equal(m.players.reduce((n,p)=>n+p.deaths,0),kills);assert.equal(m.players.reduce((n,p)=>n+p.rounds,0),m.round_count*10);assert.ok(m.players.every(p=>p.cases.length>=1&&p.cases.length<=2&&!('rating' in p)));
 }
});
test('unstarted or future matches never settle even if a winner is injected',()=>{
 assert.ok(settleCausal(summary,official,Date.parse('2026-10-17T03:00:00Z')).every(r=>r.settled===0));const actual=completed();assert.ok(settleCausal(summary,actual,Date.parse('2026-10-17T03:00:00Z')).every(r=>r.settled===0));
});
test('verified completed loser final settles the current winner predictions only',()=>{
 const rows=settleCausal(summary,completed(),Date.parse('2026-10-17T13:00:00Z'));assert.ok(rows.every(r=>r.settled===1));assert.deepEqual(Object.fromEntries(rows.map(r=>[r.channel,r.hits])),{codex:1,deepseek:0,doubao:1,mimo:1});
});
test('late, unknown-time, invalid-score and unverified results cannot earn points',()=>{
 const time=Date.parse('2026-10-17T13:00:00Z');
 for(const stamp of ['2026-10-17T07:00:00Z','2026-10-17T07:00:01Z',null,'invalid']){const s=structuredClone(summary);Object.values(s.models).forEach(m=>m.recorded_at=stamp);assert.ok(settleCausal(s,completed(),time).every(r=>r.settled===0));}
 for(const patch of [{verified_current:false},{start_utc:null},{score:[-1,3]},{score:[3,3]},{score:[2,1]},{teams:['TBD','VIT']},{state:'inProgress'}]){const a=completed();Object.assign(a.matches[0],patch);assert.ok(settleCausal(summary,a,time).every(r=>r.settled===0));}
 const a=completed();a.fetched_at='invalid';assert.ok(settleCausal(summary,a,time).every(r=>r.settled===0));
});
test('team facts merge verified predecessor results without duplicate IDs',()=>{
 const v=factualEvent(event,official,Date.parse('2026-10-17T03:00:00Z'));assert.equal(new Set(v.history.map(m=>m.id)).size,v.history.length);for(const m of official.predecessors)assert.ok(v.history.some(x=>x.id===m.id&&x.winner===m.winner));assert.deepEqual(currentFixture(event,official),{upperWinner:'LOUD',upperLoser:'VIT',lowerWinner:'100T'});
});
test('a different grand-final opponent does not fabricate a new final or score',()=>{
 const a=completed();a.fetched_at='2026-10-18T13:00:00Z';Object.assign(a.matches[1],{state:'completed',teams:['100T','LOUD'],score:[1,3],winner:'LOUD'});const rows=settleCausal(summary,a,Date.parse('2026-10-18T14:00:00Z'));assert.ok(rows.filter(r=>r.channel!=='deepseek').every(r=>r.settled===2));assert.equal(rows.find(r=>r.channel==='deepseek').settled,1);assert.equal(summary.models.deepseek.cases[1].teams[1],'VIT');assert.deepEqual(summary.models.deepseek.cases[1].score,[3,1]);assert.equal(rows.find(r=>r.channel==='deepseek').hits,0);
});

test('actual VIT 3:1 loser final awards only DeepSeek winner and exact score',()=>{
 const actual=read('official-current.json'),rows=settleCausal(summary,actual,Date.parse('2026-10-17T23:00:00Z'));
 assert.ok(rows.every(r=>r.settled===1&&r.score_settled===1));
 assert.deepEqual(Object.fromEntries(rows.map(r=>[r.channel,[r.hits,r.score_hits]])),{codex:[0,0],deepseek:[1,1],doubao:[0,0],mimo:[0,0]});
 const reversed=structuredClone(actual);reversed.matches[0].teams.reverse();reversed.matches[0].score.reverse();assert.deepEqual(settleCausal(summary,reversed,Date.parse('2026-10-17T23:00:00Z')),rows);
});
test('only pre-existing matching grand final is eligible; mismatched opponents stay missing',()=>{
 const actual=read('official-current.json').matches[1];assert.deepEqual(actual.teams,['LOUD','VIT']);
 for(const [id,m] of Object.entries(summary.models)){const prediction=fixturePrediction(m,actual);assert.equal(Boolean(prediction),id==='deepseek');if(prediction)assert.deepEqual(prediction.score,[3,1]);}
 const late=structuredClone(summary.models.deepseek);late.recorded_at=actual.start_utc;assert.equal(fixturePrediction(late,actual),null);
 const unknown=structuredClone(actual);unknown.start_utc=null;assert.equal(fixturePrediction(summary.models.deepseek,unknown),null);
});
test('archive binds original model bytes, inputs and both original series without rewriting',()=>{
 const archive=read('archive/2026-10-17.json');for(const [id,m] of Object.entries(archive.models)){
 const raw=readFileSync(new URL('../'+m.source_file,import.meta.url));assert.equal(createHash('sha256').update(raw).digest('hex'),m.source_sha256);assert.deepEqual(m.cases,models[id].data.cases.map(p=>({teams:p.teams,score:p.state.series_score,winner:p.state.winner})));
 }
 for(const field of ['evidence','event'])assert.equal(createHash('sha256').update(readFileSync(new URL('../'+archive[field+'_file'],import.meta.url))).digest('hex'),archive[field+'_sha256']);
});

test('missing or duplicated opponent identity cannot settle or appear as a matching final',()=>{
 const actual=read('official-current.json');for(const teams of [null,['VIT','VIT'],['LOUD','LOUD']]){
 const changed=structuredClone(summary);for(const model of Object.values(changed.models))for(const part of model.cases)part.teams=teams;
 assert.ok(settleCausal(changed,actual,Date.parse('2026-10-17T23:00:00Z')).every(r=>r.settled===0));assert.equal(fixturePrediction(changed.models.deepseek,actual.matches[1]),null);
 }
});
