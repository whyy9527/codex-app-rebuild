import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {causalTimeline,routeRegion,playbackTimes} from '../causal-player.mjs';
const data=JSON.parse(readFileSync(new URL('../data/causal/codex.json',import.meta.url)));
test('player preserves actual case, map and event order without generating outcomes',()=>{
 const parts=data.cases||[data],timeline=causalTimeline(data);
 assert.equal(timeline.filter(f=>f.kind==='bp').length,parts.length*12);
 for(const [caseIndex,part] of parts.entries()){
  const frames=timeline.filter(f=>f.caseIndex===caseIndex&&f.kind!=='bp');
  assert.deepEqual(frames.map(f=>f.kind),part.frames.map(f=>f.kind));
  assert.deepEqual(frames.filter(f=>f.kind==='round_end').map(f=>[f.map,f.round_number,f.winner,f.round_score]),part.frames.filter(f=>f.kind==='round_end').map(f=>[f.map,f.round_number,f.winner,f.round_score]));
  assert.ok(frames.every(f=>JSON.stringify(f.teams)===JSON.stringify(part.teams)));
 }
 for(let i=0;i<timeline.length;i++){assert.ok(timeline[i].end>timeline[i].start);if(i)assert.equal(timeline[i].start,timeline[i-1].end);}
});
test('each actual round has one continuous six-second playback window',()=>{
 const frames=causalTimeline(data);
 for(let i=0;i<frames.length;i++)if(frames[i].kind==='round_start'){
  const end=frames.slice(i).find(f=>f.kind==='round_end');assert.ok(end);assert.ok(Math.abs(end.end-frames[i].start-6)<1e-7);
 }
});

test('movement animation visits only model-emitted real region IDs',()=>{
 for(const f of causalTimeline(data).filter(f=>f.kind==='move')){
  assert.equal(routeRegion(f,f.start),f.event.route[0]);
  assert.equal(routeRegion(f,f.end),f.event.route.at(-1));
  assert.ok(f.event.route.includes(routeRegion(f,(f.start+f.end)/2)));
 }
});

test('map result retains the last accepted round positions and alive state without mutating source',()=>{
 const original=JSON.stringify(data),timeline=causalTimeline(data);let checked=0;
 for(const [caseIndex,part] of (data.cases||[data]).entries())for(const frame of timeline.filter(f=>f.caseIndex===caseIndex&&['map_end','series_end'].includes(f.kind))){
  const last=[...part.frames].reverse().find(f=>f.kind==='round_end'&&f.map===frame.map);
  assert.deepEqual(frame.positions,last.positions);assert.deepEqual(frame.alive,last.alive);checked++;
 }
 assert.ok(checked>0);assert.equal(JSON.stringify(data),original);
});

test('16× ticks process every event and route region in order across all four complete models',()=>{
 for(const model of ['codex','deepseek','doubao','mimo']){
  const input=JSON.parse(readFileSync(new URL('../data/causal/'+model+'.json',import.meta.url))),before=JSON.stringify(input),frames=causalTimeline(input),end=frames.at(-1).end-.001;
  const visited=new Set([0]),regions=new Map();let time=0;
  while(time<end){
   const next=Math.min(end,time+.1*16),points=playbackTimes(frames,time,next);assert.equal(points.at(-1),next);
   for(const point of points){const i=frames.findIndex(f=>point<f.end),f=frames[i];visited.add(i);if(f.event?.kind==='move'){const values=regions.get(i)||[];values.push(routeRegion(f,point));regions.set(i,values);}}
   time=next;
  }
  assert.deepEqual([...visited],frames.map((_,i)=>i));
  for(const [i,values] of regions)for(const region of frames[i].event.route)assert.ok(values.includes(region),model+' move '+i+' missed '+region);
  assert.equal(frames.at(-1).winner,input.cases.at(-1).state.winner);assert.equal(JSON.stringify(input),before);
 }
});
