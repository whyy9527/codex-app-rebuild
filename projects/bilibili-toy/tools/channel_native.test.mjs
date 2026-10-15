import assert from 'node:assert/strict';
import {channelFacts} from './channel_native.mjs';
const raw=`0 standard window Example
\t1 scroll area
\t\t2 HTML content
\t\t\t3 link 跳到主要内容, Value: example.test
\t\t\t4 container Example · AI 区新人 UP · 资深 LOL 观众
\t\t\t\t5 button + 关注
\t\t\t6 text 模型 · EXAMPLE
\t\t\t7 slider (settable, float) 比赛日, Value: 18
\t\t\t8 table (showing 0-1 of 100 items)
\t\t\t\t9 row (selectable) 选手
战队, Value: 选手
战队
\t\t\t\t\t10 cell (selectable) Player
\t\t\t11 link Value: …, 长标题
第二行
\t\t\t12 link 距真实开赛 01:02:03, Value: example.test
\t\t13 scroll bar (settable, float) 0`;
const facts=channelFacts(raw);
assert.deepEqual(facts.elements,{world:{value:'EXAMPLE'},match_day:{value:'18'}});
assert.deepEqual(facts.partial_ranges,[{role:'table',table_ordinal:0,start:0,end:1,total:100}]);
assert.deepEqual(facts.tables,[{ordinal:0,observed_rows:1,truncated:true}]);
assert(facts.accessible_text.includes('选手战队'));
assert(facts.accessible_text.includes('长标题第二行'));
assert(!facts.accessible_text.some(x=>x.includes('关注')||x.includes('01:02:03')));
const complete=channelFacts(raw.replace('table (showing 0-1 of 100 items)','table'));
assert.deepEqual(complete.tables,[{ordinal:0,observed_rows:1,truncated:false}]);
assert.deepEqual(complete.partial_ranges,[]);
const desktopPlayer=raw.replace('6 text 模型 · EXAMPLE',`6 container AI 模拟回放播放器
\t\t\t\t14 text AI 模拟 Example Model  的世界 入围赛 赛前
\t\t\t\t15 button 播放, Help: Play
\t\t\t\t16 checkbox 闲置 60 秒后自动换台, Value: 0`);
assert.equal(channelFacts(desktopPlayer).elements.world.value,'Example Model');
assert.deepEqual(channelFacts(desktopPlayer).interactions,{player_paused:true,idle_enabled:false});
console.log('Channel multiline labels, desktop world and partial-table checks passed');
