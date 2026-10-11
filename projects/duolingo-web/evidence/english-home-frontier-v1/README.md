# 改换入口、完整句翻译与成绩单取消键

2026-10-11。接续[错误卡探索](../english-error-review-v1/README.md)。完整 Goal 保持 active；本批没有新模型消融，原始 Dream-RSI/Cordis 论文及负面实验仍保留在[RESEARCH](../../../../docs/RESEARCH.md)。这条真实路线新增了覆盖，但不能据此声称探索充分或 RSI 有收益。

## 用历史改变探索路线

此前多次通用练习没有遇到 listenIsolation，本批没有再用相同重练碰运气。先在原版成绩单按 Escape，实际关闭且仍在原结算；Continue→建档稍后返回学习路径。点击 Practice 节点实际显示“完成以上全部等级才可以解锁哦！”。当前第4/4单元可打开开始入口，但开始弹建档，选择“稍后创建帐户”返回路径，再次开始仍弹提示。没有创建账户、修改账户或猜测解锁规则。

直接打开页面实际提供的 `/lesson` 地址，出现“来复习一下这个等级，完成后有惊喜哦！”与“开始挑战 +20 经验”。这是另一条实际路线，并非将路径上的建档提示当作已通过。源记录见 `source/locked-practice`、`lesson-entry`、`lesson-profile-prompt`、`repeated-profile-prompt`、`lesson-challenge-entry`。

当前题驱动新增这条已观察入口的决策，实际自动点击并答对第一题后在 speak 停下；实际暂缓 Thank you.，保存关闭反馈，继续后插入翻译，再答对3题，于新类型 completeReverseTranslation 作答前停下。新类型实际界面是一个空的多行文本框；虽然公开 displayTokens 标记了部分 isBlank，界面没有显示固定英文前缀，不能照听力填空只输入空缺词。

读取实际文本框/截图后，驱动改为在这个已观察模式输入完整 displayTokens 句子。真正接受了4道该类型，含 `tea with sugar`、`I'd like coffee with milk and sugar.` 等，再完成4道其它题到原结算。三次源回放合计12接受、1暂缓，成绩单13卡；没有错误评分或听音填空。新类型卡实际标题“完成翻译”；不是猜成普通翻译标题。仅基于公开当前答案回放，不能当盲探索实验。

## 新前端证据与明确待做

13卡全部实际布局保留，最后一张部分在视口外，不把布局存在算完整可见。第7号长答案展开：卡矩形 `[765,364,165,150]`，浮层 `[710,467,274.0703125,136]`，双方显示完整英文句。标签13粗体、41点组、20点间隔仍一致，**浮层相对卡顶为103点，不是此前短答案的78点**。源卡正文/检查图标参与行布局，确切锚点算法尚未证明，不能简单把短样本规则推广。`long-card-layout.json`、`long-tooltip-css.json`及PNG保留实测。

v36保留v35全部2208项，追加Escape关闭与结算保留2项，共2210；源事实由实际按键后DOM/AX得出。v37再原样保留2210项，追加13卡两状态的78个几何/角色/enabled、答案文字、长浮层几何及整图，共88项，总2298。源自检485pass/0fail/1799not_run/14unavailable。**这88项尚未被Swift访问或实现，全部not_run**；冻结它们是下一批必须完成的需求，不是本批候选成绩。

等级复习的课程语义、完整句输入、主课回顾入口及默认元数据还需接入；不能把当前独立17/18卡实例当默认产品已完成。听音填空回顾、正常口语、自适应与声学仍未知。[frontier](frontier.json)明确这些后续工作，未新增产品范围限制。

## Swift实际修复与失败

基线驱动在实际18卡回顾中发Escape，49状态完成，但 `review_closed=false`。第一次把 onExitCommand 放在未获得键盘响应的覆盖视图上，构建后再跑49状态仍false；不能以代码存在或驱动退出0算修复。

最终把系统取消快捷键直接绑定到实际关闭按钮（keyboardShortcut cancelAction），同样真实49状态，`review_closed=true`，保留结算、随后重新练习。v36由基线211pass/11fail/1988not_run变为212pass/10fail/1988not_run。新增2项全pass；原有三整图、两红底采样、主页4文本和任务页整图仍fail。没有放宽颜色或图像容差。基线和第一次失败按键均另有关闭按钮恢复动作，因此最后都能继续，但这不掩盖Escape失败。

同一最终二进制回归旧17卡44状态，关闭按钮/滚动/重练无驱动失败；v36为147pass/7fail/2056not_run。按最新v37重评最终18卡回执为212pass/10fail/2076not_run，新增88未访问。不同轨迹不累计通过数。这批没有重新运行默认47状态，不把上一批另一个二进制的回执冒充本次结果。

构建、27核心、56 Python、14 Node通过。Node验证真实入口、4份接受回执对应完整句、不同/非空输入状态不误用已观察模板；实际CLI的续跑是另外的源证据。v36/v37冻结均逐字节复现，归档PNG与原文件逐字节核验。源码初次按钮ref失效及嵌套button严格匹配失败发生在点击前，刷新/选择实际button后才操作；未因等待超时重复源动作。没有录音、隐式会话数据、未来题单或新模型效果结论。

## 复跑

```sh
node --test projects/duolingo-web/*.test.mjs
python3 -m unittest discover -v
python3 projects/duolingo-web/freeze-review-escape.py --out-dir artifacts/review-escape-freeze-new
python3 projects/duolingo-web/freeze-level-review.py --out-dir artifacts/level-review-freeze-new
swift build --package-path projects/education-swift
swift run --package-path projects/education-swift LearningCoreChecks
swift projects/duolingo-web/observe-frontend.swift artifacts/review-escape-native-new projects/duolingo-web/fixture-reference-en-zh-v11.json --seed-progress projects/duolingo-web/evidence/english-pronunciation-v2/progress-source.json --reference-color-scheme light --observe-quests --exercise-error-review
```

原版续跑须先确认当前状态；本批结束于 `/lesson` 的长答案成绩卡，不能直接重放早先入口或答案。可对明确选定的、实际已打开挑战运行当前题驱动，正整数步预算及 `--stop-before-type listenIsolation` 只约束这次探索动作，不限制产品目标。

```sh
python3 projects/duolingo-web/sample-frontend-colors.py --contract projects/duolingo-web/frontend-english-v37.json --observed artifacts/review-escape-native-new/observed.json --out artifacts/review-escape-native-new/observed-colors.json
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-v37.json --observed artifacts/review-escape-native-new/observed-colors.json --out artifacts/review-escape-native-new/validation.json
```

逐构建身份、计数及未知见[verification-summary](verification-summary.json)。完整Goal未收窄或完成。
