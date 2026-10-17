import test from 'node:test';
import assert from 'node:assert/strict';
import {MAP_NAMES,mapDisplay,finalCountdown,FINAL_START_UTC} from '../display.mjs';
test('Chinese map names cover the actual pool without translating technical references',()=>{
 assert.equal(Object.keys(MAP_NAMES).length,7);
 assert.equal(mapDisplay('Ascent · LOTUS / 固定Haven场景 Split.'),'亚海悬城 · 莲华古城 / 固定隐世修所场景 霓虹町.');
 for(const technical of ['assets/Ascent.webp','https://x.test/Split','map:Lotus:1','foo_Summit','Abyss.json'])assert.equal(mapDisplay(technical),technical);
});
test('final countdown uses the absolute final start and clamps after the deadline',()=>{
 const start=Date.parse(FINAL_START_UTC);
 assert.equal(finalCountdown(start-90061000),'距离决赛开赛 1天 1时1分1秒');
 assert.equal(finalCountdown(start-1),'距离决赛开赛 0时0分1秒');
 assert.equal(finalCountdown(start),'已到开赛时间');
 assert.equal(finalCountdown(start+100000),'已到开赛时间');
});
