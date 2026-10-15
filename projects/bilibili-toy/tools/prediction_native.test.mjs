import assert from 'node:assert/strict';
import {predictionFacts} from './prediction_native.mjs';

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
console.log('Prediction duplicate controls and missing scope checks passed');
