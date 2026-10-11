# 听音填空：原版几何、缺词反馈与探索反例

2026-10-11。本批接续 [当前题探索与Eddy负结果](../english-current-challenge-v1/README.md)，先从已有原版 DOM/PNG 冻结前端，再修改实际 Swift。完整Goal继续，原始 RSI 论文及负消融见 [RESEARCH](../../../../docs/RESEARCH.md)；这里没有模型消融或 RSI 收益结论。

## 前端模具先暴露缺口

`freeze-isolation-presentation.py`从原版 `isolation-before.json` 和实际 `replay-from-5.json` 冻结q5角色、真正29×22播放按钮、两组选项、暂缓入口的几何/角色/enabled。v32原样保留1903条v31要求，追加9条，共1912。旧候选重评为91pass／59fail／1759not_run／3unavailable；新增9条为2pass、4fail、3unavailable，缺暂缓入口明确不可验证。没有通过自己实现生成原版事实。

源投影的新增9条全pass；整个历史投影为99pass／0fail／1799not_run／14unavailable。14项来自该历史参考缺少较新契约所需的事实，未补成通过；源自检不能替代候选验证。第一次冻结误用了仅含听力暂缓新状态的reference，KeyError后修正为原版通用练习reference，未产出虚假规格。

## 实际实现

原来的气泡整体是播放按钮，角色偏左16点、选项偏下0.5点；没有尖角、文字装饰、内容分隔线，答对后仍保留占位符。新布局只用于有实际原版token数据的通用听音填空：角色行左侧16点，角色与气泡无额外间隔，标题后32点，分隔线2点及到选项36点。真正播放控件独立为29×22，沿用真实原音播放动作；不改评分。

可选 `Question.isolationPromptTokens` 从原版 `tokens/blankRange/tts` 编译，保存空格、标点、可提示单词与缺词身份。未答时按缺词本身的字宽留白并画横线；正确反馈显示原词ice及绿色虚线。字体不是直接照CSS500：源No/ice/please宽度约22.6875/23.75/55.4219，CoreText轴400比500更接近，见 [宽度诊断](font-width-diagnostic.json)。该诊断不证明全部字体或栅格已一致。

默认通用夹具升级v3，旧v1/v2保留。v3去掉新显示字段后与v2全部数据逐项相同，50个源资源清单不变；编译器输出可复现。旧没有token数据的显式暂缓实例仍保留其布局，标题间距也按数据分支选择，避免统一增加4点造成回归。普通主课未套用该新布局。

## 原生实测与仍存在的失败

native-01：构建01后的默认练习实际走完47状态、一次错误/复习、奖励、建档稍后、返回及真正终止重启，驱动failure=null。播放按钮 `[450,270,29,22]`、两组选项 `[300,406.5,600,62]`／`[300,476.5,600,62]` 与原版精确一致；反馈实际可读文本为“No ice, please.”。

共同v32为 **94pass／56fail／1759not_run／3unavailable**。新9条5pass／1fail／3unavailable。角色仍为 `[301.1,184.75,129.8,192.5]`，原版 `[301.0861206,184.75,129.7999878,192.5]`；0.0138794点误差仍fail，没有容差或刻意修改Rive参数。暂缓入口缺失的3项仍unavailable，不能只补一个直接跳题按钮假装原版替换规则已实现。

两张整图都继续fail。未答RGB平均差由 `[3.051,2.300,3.325]` 降至 `[2.760,1.517,2.423]`，正确反馈由 `[4.025,3.019,5.796]` 降至 `[3.705,1.966,4.531]`；[完整数值](image-delta.json)。只有ICC、实测标题栏和backing scale归一，没有平移搜索、屏蔽或放宽。动画阶段未对齐、波形仍错误沿用旧题帧、正确时还露白色底块，进度、字体、暂缓入口等仍有差异；不能从数值下降宣称1:1。

发现旧实例没有token后，构建02把32点间距限定到有token的分支。最终二进制另跑decline-regression-01，真实45状态及重启无失败，共同v32为56pass／35fail／1821not_run／0unavailable；其新增9条未访问，不能累加到默认实例覆盖。最终同一二进制又在native-final完整走完默认47状态及真正重启，共同计数仍94pass／56fail／1759not_run／3unavailable；与decline-regression-01的binary SHA一致。native-01保留为前一次构建真实回执，两次构建范围分别报告。25核心／56 Python通过。220份复制件逐字节核验，重绑定PNG相对路径后重新执行得到同样计数。

## 探索没有按预定路线出现目标题

尝试从实际原版再次找听音填空时，reload被CLI的beforeunload处理打断返回，没有Result。检查实际页面确认reload已完成；未重复reload。此后完全用当前renderer单步回放，8题实际接受后到口语Hot, please.，保存未覆盖回执；实际暂缓显示麦克风已关闭，继续却插入tea with sugar翻译，不能把口语原句当替换模板。

又实际答对5题，共13题，仍没有listenIsolation。当前题模式在挑战引导页没有可见challenge，故动作前失败，现场随后单独采集并实际继续；现在原版停在挑战翻译“茶加糖”，未答。见 [逐步摘要与边界](exploration-summary.json) 和 `source-probe/`。这验证当前题续接在另一实际实例上可运行，也明确暴露引导页仍需外层流程接续；公共参考答案不构成盲探索效果证据。本批没有找到目标题，不能声称探索充分。

下一步从该真实边界继续，观察听音填空暂缓后的具体状态、补其入口与替换规则，继续波形/字体/动画时序/声学和未访导航，并完善无需人工接引导页的探索闭环。现有前端要求和负结果保留。

## 复跑

```sh
swift projects/duolingo-web/evidence/english-isolation-presentation-v1/font-width-probe.swift
python3 projects/duolingo-web/freeze-isolation-presentation.py --out-dir artifacts/isolation-freeze-new
python3 projects/duolingo-web/compile-general-practice.py
swift build --package-path projects/education-swift
swift run --package-path projects/education-swift LearningCoreChecks
python3 -m unittest discover -v
swift projects/duolingo-web/observe-frontend.swift artifacts/isolation-native-new projects/duolingo-web/fixture-reference-en-zh-v11.json --seed-progress projects/duolingo-web/evidence/english-pronunciation-v2/progress-source.json --reference-color-scheme light --observe-quests --exercise-general-practice
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-v32.json --observed projects/duolingo-web/evidence/english-isolation-presentation-v1/native-final/observed.json --out artifacts/isolation-validation-new.json
```
