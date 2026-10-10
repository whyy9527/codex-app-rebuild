# 原版发音练习→Swift · v1

从原版dock/deck首题续跑，观察五道听辨、五道sameDifferent、got口语暂缓、四词音频配对、错题重练、结算、匿名建档提示/稍后再说及返回发音页。原版JSON、PNG和播放事实保留，没有把它当作只有二选一的课程。

## 保留的失败

walk01在300ms切题时读到旧/新两组radio而停止，未重复提交。walk02接续，在sameDifferent时原单speaker选择器失败；随后支持原版两个speaker，walk03走到口语。walk04按URL查答案，遗漏题型/选项：同一个get音频在选单词和判断两个词是否相同中，正确选项不同。键覆盖导致24次额外答错，预算用尽，原始成本保留，不能包装成探索收益。

改为题型、选项和音频身份的复合键，并以现场负反馈更新。walk05纠正剩余题；最后继续进入结算过渡，驱动读到禁用旧radio而超时。重新读取同一页面确认已结算，没有重答或重启。源完整尝试含额外错误，不能作为候选四错路线的完整同轨迹比较。

首次原生练习无反应，是生成数据同时声明lessons与legacy questions，而启动函数静默return。Core正确拒绝数据；已修正生成器并报告加载错误，decode-failure保留。NSButton固有宽600挤坏横排，intrinsic-failure保留；改为父布局提供296×60，两项零容差矩形通过。radio-regression证明旧纵排四项几何及四项checked仍通过。

本机Python缺cairosvg，改用浏览器临时页渲染原SVG为透明PNG后关闭。一次动作/捕获共用raw文件名而EEXIST，保留原文件，用新stem重新读取同一页面。

## 实现与验证

入口建立独立Lesson，复用选择、配对、错题回顾和暂缓口语状态机；不把练习结果写入主课程完成课或生命值。定义有10道选择题、1道配对题，以及配对前的口语步骤。12个原版公开音频资源已捆绑，双speaker分别播放；未确认的口语及配对左1声音保持unavailable，不用系统TTS或其他词音频代替。

最终实际走过52个原生状态，含单选、反馈、sameDifferent、暂缓口语、配对、四道错题更正、结算/稍后再说、返回、重新开始立即退出。主进度仍为六课/生命3，与开始一致。原版新练习未答时quit直接返回，候选已去掉草拟确认弹窗；中途退出仍需观察。

v19保留1589旧项并新增49项至1638。新增练习44pass/5not_run，首题两radio零容差矩形通过；完整本次122pass/19fail/1497not_run。三组初始题/反馈整图仍different。构建、22核心业务检查、52框架检查通过；这些不证明整App 1:1。

源结束后ɑ进度0.05、ɛ进度0.041666668，生命仍3、宝石510。候选还没保存音标进度，增长公式和恢复未知。源结算含统计动画、耗时条件文案，候选只实现标题和继续。源额外错误路线与候选四错路线不同，不能直接比较结算值和进度比例。

正常口语录音/识别、两处播放身份、跳过、建档表单、结算统计、音标进度/恢复、视觉与声音等价尚未补齐。候选录音按钮目前禁用而源可用，这是实现缺漏，不是产品限制。完整Goal保持active。

## 复跑

    swift build --package-path projects/education-swift
    swift run --package-path projects/education-swift LearningCoreChecks
    swift projects/duolingo-web/observe-frontend.swift artifacts/practice-new projects/duolingo-web/fixture-reference-en-zh-v10.json --seed-progress projects/duolingo-web/evidence/english-pronunciation-v2/progress-source.json --reference-color-scheme light --observe-pronunciation --walk-pronunciation-practice
    python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-v19.json --observed artifacts/practice-new/observed.json --out artifacts/practice-new/frontend.json
    python3 projects/duolingo-web/compare-english-captures.py --native artifacts/practice-new --pairs projects/duolingo-web/evidence/english-pronunciation-practice-v1/pairs.json --out artifacts/practice-new/visual.json

前端预期fail；图像零退出只表示诊断完成，三对仍different。compile-pronunciation-practice.py从归档事实重建定义/音频；探索脚本从当前实际页面续跑，不是RSI效果实验。下一步补音标进度、正常口语及视觉差异；真实复刻质量的匹配预算消融仍未完成。
