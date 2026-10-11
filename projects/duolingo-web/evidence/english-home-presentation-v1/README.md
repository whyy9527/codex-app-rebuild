# 主页伪元素与主课程原音 · 未完成

本批回到用户指出的主页/声音差异。原版实际返回`/learn`后采到完成节点、打开宝箱和525宝石；当前倒计时为3h，固定同状态比较仍使用先前实测4h参考，不把当前时钟伪造成4h。`source/current`与`source/pseudo`保存本次实测，旧参考通过版本继承保留。

## 探索发现与实施

旧采集只记普通元素，漏掉CSS伪元素。新增`pseudo_elements`记录可见父元素及真实计算样式；`parent_rect`仅为父元素边界，不伪造伪元素独立矩形。源完成节点卡面57px，主色88/204/2，高光114/214/39；原inline SVG按实际currentColor导入，路径保持原样，PNG168×138。Swift接入56×46高光和57px已完成节点卡面；排行榜图改70×58、间隔12，倒计时改17px粗体黄色。主页Duo仍是旧观察的一帧，未实现原动画。

v46实施前冻结，原样保留v45的2476项并追加3个实际截图像素，共2479。源自校验663pass/17unavailable/1799not_run；不能将其算候选通过。最终主页6状态37pass/17fail/2425not_run：高光像素通过；底色期望88/204/2实际88/204/0，倒计时点期望255/200/0实际255/196/1，整图仍失败。初版底色设2却实际为4、倒计时该点为空白的负结果保留。没有加容差或修改原断言。

## 原音与真实输出

`audio-audit.json`是修改前审计：115评分题里9题已有正确反馈原音，但主课程submit一直调用合成音。先保存`audio-binding-plan.json`再接已有资源；现在这9题可走原音，其他未知资源继续明确未补。错误/结算/点击和无原资源语音仍有合成回退，不宣称声音全部一致。

`audio-before`和`eighth-final`均在真实第八课q3点击Check时录自有应用输出；不录麦克风或其他应用。48kHz单声道解码，归一化互相关从0.025606→0.835938，拟合增益0.009413→0.995043；对齐后残差RMS为0.057432，仍明显，原因未确定。时间/增益拟合仅帮助检测原音出现，不设通过阈值、不证明时序/混音/音量一致，也不是RSI消融。参考自比较相关性1、偏移0。原始文件、摘要和触发时间在`audio-comparison.json`。

## 回归与负结果

相同最终二进制：主页6状态、八课41状态、注册20状态均无驱动失败；完整契约分别37/17/2425、133/17/2329、117/33/2329（pass/fail/not_run）。不同轨迹不合并成通过率。构建、29核心、58Python、14Node通过，详见`verification-summary.json`及原始日志。

首次录音前截图失败且无观察回执，单独标unavailable。`audio-before`虽已录到q3，33状态后滚轮实际未移动；驱动改为先确认活动自有窗口再定位滚轮目标，保留几何断言。第一次改音后15状态停在英语输入：空框实际得到附加“你”的文本，活动输入法为中文拼音；未修改产品键盘规则。驱动仅在输入期间选择已启用ASCII布局并defer恢复，每次保存`input-source.json`。完整41状态6次恢复成功；注册20状态也逐次恢复，安全密码焦点处的previous为ABC，不冒充每次均是拼音。实际输入、角色和结果断言保持不变。

## 复跑

从仓库根，使用新输出目录；原生任务顺序执行：

```sh
python3 projects/duolingo-web/freeze-home-presentation.py --out-dir artifacts/home-presentation-freeze-new
swift build --package-path projects/education-swift --product LingoSeed
swift run --package-path projects/education-swift LearningCoreChecks
swift projects/duolingo-web/observe-frontend.swift artifacts/home-presentation-native-new projects/duolingo-web/fixture-reference-en-zh-v13.json --seed-progress projects/duolingo-web/evidence/english-chest-v1/progress-seed.json --reference-color-scheme light --exercise-path-chest
python3 projects/duolingo-web/sample-frontend-colors.py --contract projects/duolingo-web/frontend-english-v46.json --observed artifacts/home-presentation-native-new/observed.json --out artifacts/home-presentation-native-new/observed-colors.json
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-v46.json --observed artifacts/home-presentation-native-new/observed-colors.json --out artifacts/home-presentation-native-new/validation.json
swiftc projects/duolingo-web/capture-owned-audio.swift -o artifacts/capture-owned-audio-home-new
```

八课录音换`english-eighth-integration-v1/progress-seed.json`，用`--observe-quests --exercise-eighth-review --eighth-feedback-audio-recorder`加录音器绝对路径。新录音与本批修改前录音的比较：

```sh
python3 projects/duolingo-web/compare-feedback-audio.py --reference projects/education-swift/Sources/LingoSeed/Resources/Reference/en-effect-086f72d3e2c92d602dfb.mp3 --before projects/duolingo-web/evidence/english-home-presentation-v1/audio-before/eighth-feedback.wav --after projects/duolingo-web/evidence/english-home-presentation-v1/eighth-final/eighth-feedback.wav --out artifacts/home-audio-comparison-new.json
```

音频分析需ffmpeg与numpy；视觉采样需Pillow。前端比较因真实差异返回1。注册回归另加`--exercise-path-profile --exercise-registration --exercise-registration-controls`。原始论文Dream-RSI、Cordis及既有无收益实验仍在[研究文档](../../../../docs/RESEARCH.md)，本批未新增RSI收益证据。[frontier](frontier.json)继续探索；完整Goal active，不另写Goal文件，不收窄1:1目标。
