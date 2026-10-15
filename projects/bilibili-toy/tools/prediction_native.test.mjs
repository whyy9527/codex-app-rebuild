import assert from 'node:assert/strict';
import {predictionFacts, sharedPredictionFacts, finalPredictionFacts} from './prediction_native.mjs';

// Two separate series can have the same side, odds and AI count, but differ in selection.
const ax = `1 heading 我来预测, Value: 1
2 button (disabled) 2 第 1 轮
3 toggle button KC 76% 8, Value: on
4 toggle button KC 76% 8, Value: off
5 button 展开 AI 模拟速报（含后续剧情）`;
const {elements} = predictionFacts(ax);
assert.equal(elements['KC 76% 8 [1]'].checked, true);
assert.equal(elements['KC 76% 8 [2]'].checked, false);
assert.equal(elements['2 第 1 轮'].enabled, false);
assert.throws(() => predictionFacts('1 heading Other'), /scope unavailable/);
const split = `1 container 好友预测战帖
  2 text 冠军 GEN （最像
  3 container Qwen
  4 text Qwen3.8 Max ）
  5 button 收起
6 container Other`;
const merged = `1 container 好友预测战帖
  2 text 冠军 GEN （最像  Qwen3.8 Max ）
  3 button 收起
4 container Other`;
assert.deepEqual(sharedPredictionFacts(split), sharedPredictionFacts(merged));
assert.equal(sharedPredictionFacts('1 container Other').interactions.shared_prediction_visible, false);
const locked = `1 text 我的冠军
2 text GEN
3 toggle button HLE 33% 0, Value: off
4 toggle button GEN 67% 8, Value: on
5 text 已锁定 ·
6 text 2026/10/15 21:15:58`;
const saved = finalPredictionFacts(locked);
assert.equal(saved.elements.champion.value, 'GEN');
assert.equal(saved.elements.selected_matches.value, '1');
assert.equal(saved.elements.match_choices.value, '2');
assert.equal(saved.interactions.prediction_locked, true);
assert.notEqual(saved.lock_signature, finalPredictionFacts(locked.replace('21:15:58', '21:16:00')).lock_signature);
assert.equal(finalPredictionFacts('1 text Other').interactions.final_result_visible, false);
console.log('Prediction duplicate controls, split text, final retention and missing scope checks passed');
