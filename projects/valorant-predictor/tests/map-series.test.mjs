import {test} from 'node:test';
import assert from 'node:assert/strict';
import {seriesDistribution,mapSeriesDistribution,simulateMapSeries} from '../engine.mjs';
const maps = ps => ps.map((p,i)=>({map:`M${i}`,a_start_side:i%2?'DEF':'ATK',p_first:p}));
test('heterogeneous map probabilities conserve mass and agree with iid baseline when equal',()=>{
 for(const p of [0,.1,.5,.83,1]){
  const a=mapSeriesDistribution(maps([p,p,p,p,p]));
  for(const row of seriesDistribution(p))assert.ok(Math.abs((a.find(x=>String(x.score)===String(row.score))?.probability||0)-row.probability)<1e-12);
 }
 const p=maps([.2,.9,.4,.8,.1]),a=mapSeriesDistribution(p),b=mapSeriesDistribution(p.map(m=>({...m,p_first:1-m.p_first})));
 assert.ok(Math.abs(a.reduce((n,r)=>n+r.probability,0)-1)<1e-12);
 for(const row of a)assert.ok(Math.abs(row.probability-b.find(x=>String(x.score)===String([...row.score].reverse())).probability)<1e-12);
});
test('later maps use ordered probabilities and terminal scores do not play more maps',()=>{
 const p=maps([.1,.2,.3,.4,.87]);
 assert.equal(mapSeriesDistribution(p,[2,2]).find(r=>r.score[0]===3).probability,.87);
 assert.deepEqual(mapSeriesDistribution(p,[3,1]),[{score:[3,1],probability:1}]);
 const r=simulateMapSeries(['A','B'],maps([1,0,1,0,1]),42);assert.deepEqual(r.score,[3,2]);assert.equal(r.maps.length,5);
 assert.deepEqual(r,simulateMapSeries(['A','B'],maps([1,0,1,0,1]),42));
 const sweep=simulateMapSeries(['A','B'],maps([1,1,1,0,0]),42);assert.equal(sweep.maps.length,3);
});
test('missing, duplicate, nonnumeric or illegal map inputs fail closed',()=>{
 for(const p of [[],maps([.5,.5,.5,.5]),maps([.5,NaN,.5,.5,.5]),maps([.5,null,.5,.5,.5])])assert.throws(()=>mapSeriesDistribution(p));
 const p=maps([.5,.5,.5,.5,.5]);p[1].map=p[0].map;assert.throws(()=>mapSeriesDistribution(p));assert.throws(()=>mapSeriesDistribution(maps([.5,.5,.5,.5,.5]),[3,3]));
});
