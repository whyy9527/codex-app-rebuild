# 三次实际发音练习编译与重启续跑

本批修复候选始终重复首套练习的问题。冻结输入来自上一批实际原版第二/第三套轨迹，新增第三套成绩单关闭→继续→建档→稍后→返回的观察。第一套 Lesson 定义逐字段未变；原版第三套最终回到 `/characters`。

## 实际实现与证据

- 编译器读取第二/第三套选择题反馈、分段播放记录、实际接受的配对和右列顺序，编译原版资源。三套各11个计分问题；第二套没有口语，第一/第三套各一个口语暂缓步骤。第二套六错、第三套五错的复习轨迹通过核心验证。
- 资源清单 v2 共35个公开原版音频，逐文件校验 SHA-256。第二套配对音频身份未采集，不按相同单词猜声音；第一套口语及配对左1仍未知。第三套 tell 口语原声和四个配对原声来自实际播放。
- 完成后在独立 pronunciation course key 保存 session ID，不更改主课程和生命值，不把有限三套样本标成整门发音课程完成。
- 原生第一套53状态：真实答题/复习、结算、返回、终止进程、重新启动、点击练习，验证控件显示 `1 sip / 2 zip`。原生第二套57状态同样完成，重启后验证 `1 tell / 2 tall`。检查实际编号文本，不只依赖三套重用的 p0 ID。
- 第一轮原生观察失败保留：检查器误要求未编号文本，实际控件带编号。修正检查器后另开新运行目录完成验证，没有把失败记为通过。

这证明已观察轨迹的候选续跑；**不证明原版自适应选题算法**。音标进度仍未更新，原版选择下一套的完整条件未知。第四套资源未编译，当前再开始将显示加载失败；这是实现缺口，不是原版限制，继续探索并修复。时长依赖的结算标题/正文目前是观察样本，尚无通用选择规则。

## 验证结果

构建与23项核心检查通过。原生第一套重跑既有完整 v22 前端契约：171 pass / 24 fail / 6 unavailable / 1501 not_run，与上一批一致。六组同状态图像全部 different。第二套执行轨迹未冒充 v22 第一套前端要求通过；第三套本批仅原生确认重启入口，完整轨迹由核心层验证，完整原生 UI 仍待执行。声音等价、正常口语识别、成绩单界面、真实前端质量消融及未知分支仍未完成，Goal active。

## 复跑

从仓库根执行，观察输出必须用新的目录：

```sh
python3 projects/duolingo-web/compile-pronunciation-practice.py
swift build --package-path projects/education-swift
swift run --package-path projects/education-swift LearningCoreChecks
swift projects/duolingo-web/observe-frontend.swift artifacts/practice-progression-fresh projects/duolingo-web/fixture-reference-en-zh-v10.json --seed-progress projects/duolingo-web/evidence/english-pronunciation-v2/progress-source.json --reference-color-scheme light --observe-pronunciation --walk-pronunciation-practice --verify-pronunciation-restart
swift projects/duolingo-web/observe-frontend.swift artifacts/practice-progression-second-fresh projects/duolingo-web/fixture-reference-en-zh-v10.json --seed-progress artifacts/practice-progression-fresh/progress.json --reference-color-scheme light --observe-pronunciation --walk-pronunciation-practice --verify-pronunciation-restart
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-v22.json --observed artifacts/practice-progression-fresh/observed.json --out artifacts/practice-progression-fresh/frontend.json
python3 projects/duolingo-web/compare-english-captures.py --native artifacts/practice-progression-fresh --pairs projects/duolingo-web/evidence/english-pronunciation-matching-v1/pairs.json --out artifacts/practice-progression-fresh/visual.json
```

前端命令因真实失败退出1；图像命令退出0仅代表比较完成，不代表复刻通过。`verification.json` 记录摘要，两个 native 目录保存实际AX、进度、重启回执与入口截图；`compilation-inputs.json` 记录来源哈希。没有录制麦克风或环境声音。
