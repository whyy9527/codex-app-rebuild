import assert from 'node:assert/strict';
import {predictionOptionsFacts} from './prediction_options_evidence.mjs';
import {swissChecks} from './tournament_evidence.mjs';

const prefix=`1 heading 我来预测, Value: 1
2 tab (selected) 模拟一届
3 pop up button (disabled) 战队实力参考, Value: 我的实力排名
4 button 暂停
5 button 直接看结果
6 button (expanded) 调整我的实力排名, Secondary Actions: Collapse
7 pop up button 导入来源, Value: 隐藏分
8 button (disabled) T1 上移
9 button T1 下移
10 button (disabled) T19 下移
11 button 使用这份排名
12 button 取消`;
const ranking=Array.from({length:19},(_,i)=>`${20+i} text ${i+1} T${i+1} LCK`).join('\n');
const suffix='50 button 展开 AI 模拟速报（含后续剧情）\n51 menu\n52 (selected) 隐藏分\n53 Claude Opus 5.5';
const parsed=predictionOptionsFacts(prefix+'\n'+ranking+'\n'+suffix);
assert.equal(parsed.ranks.length,19);
assert.equal(parsed.elements['战队实力参考 enabled'].enabled,false);
assert.equal(parsed.elements['control 暂停'].enabled,true);
assert.equal(parsed.elements['T1 上移'].enabled,false);
assert.equal(parsed.elements.menu.value,'隐藏分 | Claude Opus 5.5');
assert.throws(()=>predictionOptionsFacts(prefix+'\n'+ranking.split('\n').slice(1).join('\n')+'\n'+suffix),/Incomplete custom ranking/);

const facts=(pairs,winners)=>({toggles:pairs.flatMap(([a,b],i)=>[a,b].map(team=>({label:team+' 50% 0',checked:team===winners[i],enabled:false})))});
const states={};
const rounds=[
  ['AB','CD','EF','GH','IJ','KL','MN','OP'],
  ['AC','EG','IK','MO','BD','FH','JL','NP'],
  ['AE','IM','CG','KO','BF','JN','DH','LP'],
  ['EM','CK','BJ','GO','FN','DL'],
  ['MK','JG','FD']
];
for(const [i,strings] of rounds.entries()){
  const pairs=strings.map(x=>x.split('')),completed={facts:facts(pairs,pairs.map(x=>x[0]))};
  states['r'+(i+1)+'-draw']=states['r'+(i+1)+'-complete']=completed;
}
states['pi-draw']={facts:facts([['F','Q'],['R','S']],[])};
states['pi-complete']={facts:facts([['F','Q'],['R','S'],['F','R'],['Q','S'],['R','Q'],['F','R']],['F','R','F','Q','R','F'])};
const ko=facts([['A','M'],['E','C'],['I','J'],['B','F'],['A','E'],['I','B'],['A','I']],['A','E','I','B','A','I','A']);
// A completed simulation exposes QF, SF and final together. Qualifier comparison
// must use its first four pairs, rather than treating later rounds as new entrants.
states['ko-draw']=states['ko-final-complete']={facts:ko};
assert.ok(Object.values(swissChecks(states)).every(Boolean));
const invalid=structuredClone(states);invalid['ko-draw'].facts.toggles[1].label='N 50% 0';
assert.equal(swissChecks(invalid).knockout_uses_qualified_teams,false);
console.log('Ranking completeness, menu/disabled states and completed-simulation qualifier checks passed');
