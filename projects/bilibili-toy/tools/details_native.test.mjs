import assert from 'node:assert/strict';
import {seriesControls} from './details_native.mjs';
const ax=`10 button 看全部
11 button FUR 3 : 1 MVK
入围赛 胜者组第一轮 · Bo5
12 button 惊天大冷 MVK 3 : 2 C9
13 link 第 1 局 FUR 胜, Value: source.test
14 link 第 2 局 MVK 胜, Value: source.test`;
assert.deepEqual(seriesControls(ax),{first_series:'button FUR 3 : 1 MVK',games:[
 {number:1,label:'link 第 1 局 FUR 胜, Value:'},{number:2,label:'link 第 2 局 MVK 胜, Value:'}]});
assert.equal(seriesControls('1 button 小冷 FUR 1 : 3 MVK\n入围赛 胜者组第一轮 · Bo5').first_series,'button 小冷 FUR 1 : 3 MVK');
assert.deepEqual(seriesControls('1 link 第 5 局 MVK 胜 爆冷, Value: source.test').games,[{number:5,label:'link 第 5 局 MVK 胜 爆冷, Value:'}]);
assert.deepEqual(seriesControls('1 link 下一场 →, Value: example.test'),{first_series:undefined,games:[]});
console.log('Actual series and per-game navigation parsing passed');
