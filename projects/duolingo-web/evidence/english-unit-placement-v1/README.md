# 单元12：真实探索 → 全轨迹前端模具 → Swift

1:1尚未完成，完整Goal继续。此次由[上一轮反馈](../english-home-scroll-v1/exploration-feedback.json)选择独立单元跳级，实际通过原版18题、四次鼓励、18张回顾卡，再走50XP／100%→英语分数仍10→解锁第2部分→建档提示→通知提示→新主页。独立测试5颗心，原版全局4颗心；原版真实进度已改变，未假装重置。

## 发现和修复

- 旧route守卫只认阶段测试，实际单元route被拒；修成观察到的结构，Node回归同时拒绝非法路径。
- 新gapFill使旧驱动停下。读取当前可见上下文、完整选项与公共题目再答，两个填空都由原版接受；检查只证明上下文存在和选项多重集，尚不证明空格位置精确一致。
- 原版退出确认没有dialog角色；实际打开并取消后，观察器增加遮罩判断。第一次过期ref失败和一次遮罩下停机都保留，后者没有作答。
- 结算DOM包含被裁剪的全部0..9，实际截图才证明50与100%；冻结时没有把全部动画数字算作可见需求。通用裁剪观察器仍待补，不能称已解决所有动态文本。
- Swift独立单元会话接18题、四鼓励、回顾、退出取消和四页结算。可选activeUnit兼容旧进度，保存解锁后的新主页；3心阶段测试与5心单元测试分开。
- 第2部分主页接真实15节点、粉色头部和Vikram烤架Lottie。入口整体位移、SVG条纹、旧主页沿用购物路径的失败保留。静态SVG转换仍有问题，角色消费实际原版Lottie；动态相位不计为一致。

## 可执行验收

v68完整保留v67的13284项，追加402项，共13686。49个新增原版状态包括全部18题前后、四鼓励、跳级入口、填空、退出确认、回顾、结算和新主页。[严格契约](../../frontend-english-v68.json)、[源参考](reference.json)及[别名](aliases.json)可复现。

[最终同一二进制50状态](native-final/observed.json)无驱动失败；[严格结果](native-final/frontend-v68.json)为205pass／93fail／13382not_run／6unavailable，49整图全部fail。结果表示全部历史契约中的本次执行，不是全产品完成率。未实现的源音效、动效与入口继续为pending。

[同二进制独立恢复主页5状态](native-home-final/observed.json)无驱动失败，[严格结果](native-home-final/frontend-v68.json)54pass／4fail／13628not_run，主页整图仍fail；mean RGB差约[3.0921,3.4831,3.7900]。与50状态结果分别报告，不能相加。[四帧角色ROI](native-home-motion.json)实际变化，不证明与原版相位／触发一致。

[最终自有应用录音](native-final/unit12-correct-and-new.wav)包含真实check动作，无麦克风或其他应用。接受答案的原语音new相关性约0.999989，残差RMS约0.000400，见[原音存在诊断](native-audio-presence.json)。源HTML媒体本题未采到反馈效果，不代表原版静音；WebAudio、全部音效、音量和时序仍未验收。

33项Swift业务核心、61项Python及21项Node通过。编译器、路径及冻结输出逐字可复现。[失败版本](native-before-container-fix/)、[动画修正前](native-before-home-animation/)与[失败资源转换](failed-asset-render/)保留。归档只重定位本地证据路径并重新计算前端比较，候选二进制与源资源摘要保留。

## 探索与RSI

[历史](history.json)80状态／44记录边，[frontier](frontier.json)2355未解决动作；18题的实际执行证据在source批次回执，未虚构成没有记录的历史边。新增库存和修正观察器不等于探索充分。

[反馈](exploration-feedback.json)把真实遗漏送回下一轮：第2部分当前课和guidebook/en/12、下一单元跳级、电台和下层入口、结算／鼓励动画及实际音效。当前Swift该单元课／指南仍复用购物实例，通知提示也未实现，必须继续探索并修复。成绩进度页原canvas角色和进度条、鼓励页原动画、其余视觉／输入／声音差异均未完成；18题全对不覆盖错误分支或自适应选题。

原论文Dream-RSI与Cordis保留在[研究来源](../../../../docs/RESEARCH.md)。历史反馈确实引出本轮新route、题型和页面；尚无本轮匹配预算的真实模型对照，不能宣称RSI带来发现收益。既有[02实验](../../../exploration-ablation/REPORT.md)仍保留不可判定结果；后续需先修复就绪观测、提交基线和注册，再执行同预算03对照及实际新分支，评价遗漏前端需求与产品质量。

## 复跑

仓库根运行，输出目录必须新建；实际UI需现有辅助功能／录屏授权。原版浏览器会话与私有profile不进仓库。原版启动、就绪及当前状态必须实际确认，不能用本地候选证明源规则。

```sh
python3 projects/duolingo-web/compile-unit-placement.py --out-dir artifacts/unit12-compile-new
python3 projects/duolingo-web/compile-unit-path.py --out-dir artifacts/unit12-path-new
python3 projects/duolingo-web/freeze-unit-placement.py --out-dir artifacts/unit12-freeze-new
python3 -m projects.duolingo-web.compile-unit-placement-frontier --out-dir artifacts/unit12-frontier-new
swift build --package-path projects/education-swift
swift run --package-path projects/education-swift LearningCoreChecks
swiftc -parse-as-library projects/duolingo-web/capture-owned-audio.swift -o artifacts/unit12-owned-audio
swift projects/duolingo-web/observe-frontend.swift artifacts/unit12-native-new projects/duolingo-web/fixture-reference-en-zh-v14.json --seed-progress projects/duolingo-web/evidence/english-unit-placement-v1/prepared-progress.json --reference-color-scheme light --exercise-home-journey projects/duolingo-web/unit-placement-native-scenarios-v1.json --audio-recorder artifacts/unit12-owned-audio
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-v68.json --observed artifacts/unit12-native-new/observed.json --out artifacts/unit12-native-new/frontend-v68.json
node --test projects/duolingo-web/*.test.mjs
python3 -m unittest discover -v
```

[49状态实际对照](comparison.html)便于审阅，不能代替严格结果。独立恢复主页使用unit-placement-home-scenarios-v1.json及unlocked-progress.json；它来自实际原生结算持久化，不是虚构源重置。
