import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {currentFlowDecision,keyboardTranslationValue} from './reference-current-step.mjs';
const labels={check:'检查',continue:'继续'};
const read=path=>JSON.parse(readFileSync(new URL(path,import.meta.url)));
test('actual captured introduction can continue, result/profile cannot',()=>{
 const capture=read('evidence/english-isolation-presentation-v1/source-probe/challenge-intro.json');
 const facts={path:capture.path,dialog_count:0,challenge_count:0,heading_count:0,
  body_text:capture.snapshot,continue_count:1,continue_enabled:true};
 assert.equal(currentFlowDecision(facts,labels).kind,'interlude');
 for(const text of ['来创建你的个人档案吧！','你又获取了一颗红心！','学习完成'])
  assert.equal(currentFlowDecision({...facts,body_text:text},labels).kind,'uncovered_state');
 assert.equal(currentFlowDecision({...facts,dialog_count:1},labels).kind,'uncovered_state');
 assert.equal(currentFlowDecision({...facts,path:'/learn'},labels).kind,'uncovered_state');
});
test('old feedback and ambiguous challenge cannot be treated as a fresh question',()=>{
 const facts={path:'/practice',dialog_count:0,body_text:'正确！',heading_count:1,
  challenge_count:1,challenge_visible:true,next_text:'继续'};
 assert.equal(currentFlowDecision(facts,labels).kind,'uncovered_state');
 assert.equal(currentFlowDecision({...facts,next_text:'检查'},labels).kind,'challenge');
 assert.equal(currentFlowDecision({...facts,next_text:'检查',challenge_count:2},labels).kind,'uncovered_state');
});
test('actual keyboard challenge has a solution without fabricating a word bank',()=>{
 const c=read('evidence/english-isolation-presentation-v1/source-probe/current-challenge-after-intro.json').content;
 assert.equal(keyboardTranslationValue(c,{textbox_count:1,textbox_enabled:true,bank_count:0}),'tea with sugar');
 assert.throws(()=>keyboardTranslationValue(c,{textbox_count:0,bank_count:0}),/actual enabled text field/);
 assert.throws(()=>keyboardTranslationValue(c,{textbox_count:2,textbox_enabled:true,bank_count:0}),/actual enabled text field/);
 assert.throws(()=>keyboardTranslationValue(c,{textbox_count:1,textbox_enabled:true,bank_count:1}),/no word bank/);
 assert.equal(keyboardTranslationValue({...c,choices:['茶']},{textbox_count:1,textbox_enabled:true,bank_count:0}),null);
});
