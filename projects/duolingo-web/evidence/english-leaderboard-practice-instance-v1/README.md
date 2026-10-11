# 排行榜练习完整实例与遗漏控件

上一轮 v52 发现当前练习与历史默认题目不一致。本批从本任务原版排行榜重新进入，逐题读取当前 renderer 的公共内容、按实际反馈推进，不读未来题单。新首题又变成“热／茶／欢迎／你好”；因此本实例不能冒充上一实例或自适应选题算法。

实际接受16道评分题，口语在第8张卡停止未覆盖；人工点击“现在不做口语题”，观察“麦克风已关闭／将在15分钟后恢复”后继续。第二段自动跨一次已观察引导页，直到未知结算停止；实际打开17卡成绩单。公共 solutions 用来驱动作答，不是独立盲测探索评分；完整自动续跑仍未实现。

将这条实例编译为显式 Swift 练习夹具，使用原版语音及已有角色资源。原生驱动可选择 review-instance 并从排行榜进入；实际44状态完成，包括16题反馈、口语暂缓、成绩单展开／滚动／关闭及重练。默认产品仍使用历史练习，原版自适应选择尚未实现；显式实例只用于共同起点和验收。

并排检查首题截图发现编译器漏掉六道题的“现在不做听力题”。v54追加六条源标签断言，再补回控件并实测通过。暂缓展示复用此前已观察的通用练习定义；本实例的听力暂缓、插入／替换路线未执行，不能把它称为完整分支复刻。

## 结果与负证据

v53原样保留v52的2848项，增加230项；v54再追加6项，共3084项。最终实际44状态：177pass／39fail／2868not_run／0unavailable。其中新增236项为163pass／37fail／36not_run；36张新增整图全部失败，另有一项严格几何差异。两个旧任务页失败仍保留。36项声音要求处于pending，不能从 unavailable 为0 推出声音通过。

修控件前，同一v54为171pass／45fail；六个可见按钮由失败转为通过。全程没有更改图像阈值。30核心业务检查通过、构建成功；所有原生PNG尺寸都与元数据2400×1528一致。源一致性自检不是候选验收。

初始契约把右列视觉行号错误地映射到原生配对ID，造成伪几何失败。实际播放的 pair_audio_order 将翻译对应到 left_index，可据此解析打乱的右列。contract-identity-correction.json 保留原契约摘要、逐位置修正和说明；初始166pass／44fail与纠正后171pass／39fail都是同一候选，不能计为产品或RSI改善。剩余一项源几何在匹配操作中采到动画变换，与初始截图相位不同，继续保留失败并补采。

历史编译辅助函数假设四个配对有四种独立提示音；本次记录只有三种，未观察到第四个。此实例编译器单独处理这三种资源，不改源回执、不虚构第四种，也不修改旧实例编译器。实际应用声学相等仍未证明。

两次成绩单展开截图在Playwright截图阶段超时，原始失败保存在本地artifacts，不把缺图当成功。首次原生命令因缺observe-quests只执行2状态；驱动现由exercise-current-review直接触发。第二次在第4题采图找不到屏上自有窗口；后续采图先激活／抬起自有子进程，第三和第四次均完成44状态。未定位窗口消失的根因，失败回执分别保留。

历史反馈和截图审查实际发现了新题单、编译遗漏和验收映射错误。没有独立模型实验或匹配预算消融，不能声称RSI因果收益。原始论文仍在docs/RESEARCH.md；完整Goal active。下一步见frontier.json，优先整页字体／图形、排行榜选中态、听力暂缓新分支与源声学链路。

## 复跑

在仓库根使用新的输出目录。显式夹具不替换默认自适应行为；原生重练仍复用该实例。

```sh
python3 projects/duolingo-web/compile-leaderboard-review.py
python3 projects/duolingo-web/freeze-leaderboard-instance.py --out-dir artifacts/leaderboard-instance-freeze-new --with-listening-controls
swift build --package-path projects/education-swift --product LingoSeed
swift run --package-path projects/education-swift LearningCoreChecks
swift projects/duolingo-web/observe-frontend.swift artifacts/leaderboard-instance-native-new projects/duolingo-web/fixture-reference-en-zh-v14.json --seed-progress projects/duolingo-web/evidence/english-home-presentation-v1/native-final/progress-after.json --reference-color-scheme light --exercise-current-review --review-instance leaderboard-review
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-v54.json --observed artifacts/leaderboard-instance-native-new/observed.json --out artifacts/leaderboard-instance-native-new/validation.json
```

[首题、口语与成绩单实际截图对照](comparison.html)。采集时间、两段作答、媒体调用、资源摘要、共同契约、失效运行和最终回执均保存，完整计数见verification-summary.json。
