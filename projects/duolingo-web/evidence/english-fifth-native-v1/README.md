# 完整第五轨迹接入默认 Swift

2026-10-11。英语v6默认五课72题（15/15/15/12/15），另含一次未评分口语暂缓。依据[实际原版轨迹](../english-next-node-v1/trajectory.json)，不按API索引虚构口语后的页面，三道插入翻译题来自实际UI。原始RSI论文及历史无收益实验仍在[研究来源](../../../../docs/RESEARCH.md)；本批没有探索策略消融或收益结论。

## 规则与缺口

`DeferredSpeech`独立于评分题，位于q5之后、adaptive7之前。“现在不做口语题”显示“麦克风已关闭 / 将在 15 分钟后恢复”，继续后进入实际插入题；不扣心、不记对、不改变评分题位置。15分钟只是源观察文案，未模拟未经观察的计时规则。播放按钮关联原版句子音频；录音与识别未接入，点击录音会报告缺失。

实际混合错误路径：输入cold被拒绝，配对错选再扣一心；配对原地修复，课末只重练hot tea，清空输入并接受HOT。保留源重练介绍。随后是“你莫不是特工？”、每日任务30/30、5宝石、建档提示、主页。13XP/94%只用于这条两次错误的已观察结果，其他错误次数显示未知，不推断通用公式。主页510宝石和16小时也是源快照。第二节点4节只接入第一节，仍不记完整课程完成。

111项源资源全部存在，新增16项（15个公开MP3、1个源SVG及其PNG）。`new-resources.json`记录本次下载哈希，`verification.json`记录整个清单文件哈希；资源一致不证明实际输出、听感或动画一致。

## 同一次运行与失败

15项核心检查通过，包括口语阻断隐藏答题、未评分暂缓、混合错误、重练介绍与HOT、结算顺序及未编译课程不记完成。

`seeded-*`为从完成前四课、4红心开始的第五课实际运行，walk_error=null；当时契约145项，91pass/4fail/50not_run，30对PNG全部different。它早于配对反馈文案修正，保留原回执。

`run01-*`从空进度连续走五课，结束2红心，walk_error=null。共享v10下433pass/12fail/307not_run。逐张核对原版PNG发现第一次配对反馈应为“真厉害！”，旧实现默认文案错误。源PNG提供正向反馈证据，先前转换失败造成的AX丢失仍保留，不补造AX观察。

修正并重新从空进度走完五课后，`final-*`记录214个实际状态、两次错题重练（首课及第五课）、口语暂缓及结算。walk_error=null，最终2红心、五课completedLessons、completedCourses为空。共享v10共752项：**434pass / 11fail / 307not_run，整体fail**；同次观察里的第五课146项为**92pass / 4fail / 50not_run**。这些是全集与子集，不能相加。

11项失败是第四课4个结算次要动作、完成节点练习/传奇2个动作、第二节点1项几何、第五课4个结算次要动作。没有删断言或放宽几何。30对第五课同视口PNG全部different。角色/结算英雄区、字体、动画、布局和实际声音仍不一致或未验证；当前结算英雄区为空，不能把文案和顺序通过当作视觉完成。

此前四课与组件回执保持历史身份。本批没有运行旧西语12场景综合入口；`verify-product.py`仍是历史西语入口，不称当前英语完整产品验收。

## 复跑

从仓库根执行，原生输出目录须不存在；源证据和资源随Git交付：

```sh
python3 projects/duolingo-web/compile-english-fifth.py
python3 projects/duolingo-web/freeze-english-fifth.py
swift build --package-path projects/education-swift --product LingoSeed
swift run --package-path projects/education-swift LearningCoreChecks
swiftc projects/duolingo-web/observe-frontend.swift -o artifacts/observe-frontend
artifacts/observe-frontend artifacts/english-five-recheck projects/duolingo-web/fixture-reference-en-zh-v6.json --walk-course --english-first-wrong --english-fifth-mixed-errors --exercise-duplicate-words --reference-color-scheme light
python3 -m capabilities.rebuild.frontend --workspace . --contract projects/duolingo-web/frontend-english-v10.json --observed artifacts/english-five-recheck/observed.json --out artifacts/english-five-recheck/result.json
python3 projects/duolingo-web/compare-english-captures.py --native artifacts/english-five-recheck --fifth-lesson --out artifacts/english-five-recheck/pixels.json
```

前端命令预期失败。像素比较按实际NSWindow内容矩形裁标题栏，将Retina采样降至原版1200×732；不修改原版、不遮罩、不放宽通过阈值。动画时刻与声学输出仍未对齐。两个编译脚本可字节一致地重生成fixture、资源清单与契约。

单独复跑第五课可加`--start-lesson-index 4 --seed-progress projects/duolingo-web/evidence/english-fifth-native-v1/initial-progress.json`，同时保留`--english-fifth-mixed-errors`；它只证明该阶段，不替代完整五课。

## 继续位置

原版停在第二节点第2/4单元入口，下一课尚未开始。继续探索其余三课、录音识别及未访问动作，补齐视觉/实际声音和完整前端模具，再以固定起点与资源开展真实探索策略消融。Goal保持active，五课不是范围上限。
