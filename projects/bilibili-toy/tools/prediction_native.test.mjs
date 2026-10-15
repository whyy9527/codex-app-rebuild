import assert from 'node:assert/strict';
import {predictionFacts, sharedPredictionFacts, finalPredictionFacts,tournamentFacts} from './prediction_native.mjs';
import {ownReportEndpoint,friendReportChecks} from './tournament_evidence.mjs';

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

const tournament=`1 heading 我来预测, Value: 1
2 button 1 入围赛
3 button (disabled) 2 第 1 轮
4 heading 入围赛, Value: 3
5 heading 第 1 轮, Value: 3
6 toggle button (disabled) KC 76% 8, Value: on
7 toggle button C9 24% 0, Value: off
8 pop up button 战队实力参考, Value: 隐藏分
9 tab (selected) 我的预测
10 text field (settable) 海报昵称, Value: 复刻验收, Placeholder: 昵称
11 button 展开 AI 模拟速报（含后续剧情）`;
const observed=tournamentFacts(tournament);
assert.equal(observed.elements.round.value,'入围赛');
assert.equal(observed.elements['round 第 1 轮'].enabled,false);
assert.equal(observed.toggles[0].enabled,false);
assert.equal(observed.elements.nickname.value,'复刻验收');
assert.throws(()=>tournamentFacts(tournament.replace('5 heading','5 container (showing 10-20 of 30 items)\n12 heading')),/incomplete/);
assert.equal(ownReportEndpoint('https://local.test/index.html?p=pickem','https://local.test/'),true);
assert.equal(ownReportEndpoint('https://other.test/index.html','https://local.test/'),false);
assert.equal(ownReportEndpoint('https://local.test/content/index.html','https://local.test/'),false);
const friendUrl='https://local.test/?p=pickem&pick=A.B.C.D.E.F.G.H_A.C.E.G_A';
const own={quarterfinalists:['A','B','C','D','E','F','G','Z'],semifinalists:['A','B','E','Z'],champion:'B'};
const friendText='冠军 A · 四强 A / C / E / G · 八强 A / B / C / D / E / F / G / H （最像 Qwen ） 与你的预测默契度 11 / 21 分';
assert.deepEqual(friendReportChecks(friendUrl,own,friendText),{score_matches:true,report_matches:true,champion:'A'});
assert.equal(friendReportChecks(friendUrl,own,friendText.replace('11 / 21','12 / 21')).score_matches,false);
assert.equal(friendReportChecks(friendUrl,own,friendText.replace('冠军 A','冠军 B')).report_matches,false);
console.log('Tournament gating, incomplete AX, static entry aliases and independent friend input checks passed');
