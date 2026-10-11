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
test('actual level-review entry starts only its observed exercise route',()=>{
 const capture=read('evidence/english-home-frontier-v1/source/lesson-challenge-entry.json');
 const buttons=capture.visible.filter(row=>row.tag==='BUTTON'&&row.text==='开始挑战 +20 经验');
 assert.equal(buttons.length,1);
 const facts={path:capture.path,dialog_count:0,challenge_count:0,heading_count:0,body_text:capture.snapshot,
  review_entry_count:buttons.length,review_entry_enabled:buttons[0].enabled};
 assert.deepEqual(currentFlowDecision(facts,labels),{kind:'review_entry',text:'开始挑战 +20 经验'});
 for(const override of [{path:'/learn'},{review_entry_count:2},{review_entry_enabled:false},
  {body_text:'来创建你的个人档案吧！'},{dialog_count:1}])
  assert.equal(currentFlowDecision({...facts,...override},labels).kind,'uncovered_state');
});

test('actual reverse translation uses the entire accepted sentence, not only blank tokens',()=>{
 const run=read('evidence/english-home-frontier-v1/source/lesson-after-reverse.json');
 let cases=0;
 for(let i=0;i<run.session.challenges.length;i++) {
  const c=run.session.challenges[i].content,row=run.observed[i];
  if(c.type!=='completeReverseTranslation')continue;
  assert.equal(row.rejected,false);assert.equal(row.identity.matches,true);
  const facts={textbox_count:1,textbox_enabled:true,textbox_value:'',bank_count:0};
  assert.equal(keyboardTranslationValue(c,facts),row.text_input.value);
  assert.notEqual(keyboardTranslationValue(c,facts),c.displayTokens.filter(t=>t.isBlank).map(t=>t.text).join(''));
  assert.throws(()=>keyboardTranslationValue(c,{...facts,textbox_value:'unfinished'}),/empty enabled/);
  assert.throws(()=>keyboardTranslationValue(c,{...facts,bank_count:1}),/no word bank/);
  cases++;
 }
 assert.equal(cases,4);
});
