# 从剩余像素差异探索实际字体与卡片按下反馈

上一批改了字号后，æ cat区域仍约1.846平均RGB差异。继续扩大同一种CSS采样并不能解释字形偏粗；本批改用浏览器实际platform font和CoreText实际解析，随后实测按住/释放及伪元素。它是失败反馈改变探针的真实记录，不是自主探索或RSI收益证明。

## 源观察与实现

2026-10-11，原版/characters、1200×732、真实匿名六课状态。source/source-fonts.json记录可见卡片的字体CSS、字体集及公开资源URL。platform-fonts.json显示：音标19px、词例15px，CSS weight500，但真正PostScript字体为DuolingoSans-Thin_wght1900000；font-probe.txt在同一源TTF上实测该后缀对应轴400，旧Swift500解析成wght1F40000。字体不是只比较字号和CSS weight即可等价。

fallback-fonts.json进一步验证中文副标题是PingFangSC-Medium，标题/分组为Semibold；所以没有把全局default500直接改成400。仅卡片英文/音标显式400，加上原版0.8px字距。蓝色开始链接实际16px/700、字距0.64px，也按此修正。

实际hover、mouse-down、mouse-up的DOM、截图和动作收据在source。按住æ cat时源按钮y从291.7890625变293.7890625，外框仍68高；释放恢复。pseudo-actual.json显示卡面阴影从2px变none，源背景/边框不变。候选原为64点卡面+4点阴影且无按下反馈，现66点面+2点阴影、按住下移2点并去阴影；不改变页面布局或模仿主课程的4点按压。当前cat点击前后仍0进度、路径characters，不推断通用音标增长规则。

SDK接口确认RoundedRectangle默认continuous；CSS border-radius的角是四分之一椭圆，等半径时为圆，依据[W3C CSS背景边框规范](https://www.w3.org/TR/css-backgrounds-3/#corner-shaping)。本页开始按钮/卡片显式circular；未批量猜测其它页面样式。中间continuous构建与最后circular构建分别保留。

## 可执行模具与结果

共同element_geometry可选relative_to_state：比较器从两个实际矩形相减，再独立与期望位移比较；driver pass不能代替矩形。未访问原点not_run，缺/坏矩形unavailable，不补零。v26原样保留1725旧要求，仅追加4项；source/geometry-observed.json从真实源控件矩形投影，geometry-reference.json四项通过。

最终实际64原生状态、Swift构建/23核心通过；完整Python56测试通过，包括零移动却driver pass仍fail、2点真实移动才pass、坏值/缺原点不计通过。新两项按住/释放位移通过，新两项绝对几何仍因分数坐标失败；整套194pass/37fail/1498not_run/0unavailable，8项整图仍全部fail。旧要求的状态结果保持不变，不能拿新增两项通过声称1:1已完成。

image-metrics.json按相同冻结零进度源、ICC→sRGB、实测标题栏/2x归一化比较：æ cat区域[442,291,598,360]约1.846→0.767→0.734；整页[3.480,3.085,3.642]→[3.180,2.842,3.427]。这是组合修正和后续圆角修正的诊断，不单独归因于字重、不是通过阈值。区域不替代整图，当前在线非零增长页不拿来伪造零进度验收。

## 失败与边界

CSS stylesheet跨来源fetch均unavailable，保留font-faces.json；实际字体来自成功的公开DOM平台字体查询，不把fetch失败写成成功。fontTools未安装，随后用真实CoreText字体描述及轴查询。初版pseudo脚本语法错误保留。首轮native未发送mouse-down即失败：center实际存CGFloat数组，错误cast成Double；failed-pointer-type保留窗口/指针/日志，修复后完整重跑。native-final实际持有鼠标期间读AX并截图，异常时释放，目标为独立owned前台子窗口。

没有环境麦克风/其他应用录音；释放按钮实际触发捆绑音标文件，但本批未做声学等价。正常口语评分/推进、音标增长/恢复、其它页面与完整课程仍有缺口。原始RSI论文及负面消融不变，完整Goal保持active。

## 复跑

归档保留原始observed.json；portable仅将capture.path指向字节相同的入库PNG，receipt.json逐一核验摘要。新输出路径，预期前端命令退出1并报告194/37/1498/0；需Pillow：

```sh
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-v26.json --observed projects/duolingo-web/evidence/english-pronunciation-typography-v1/native-final/observed-portable.json --out artifacts/typography-replay.json
```

从当前源码重新实际运行，macOS需已有AX和截图权限：

```sh
swift build --package-path projects/education-swift --product LingoSeed
swift run --package-path projects/education-swift LearningCoreChecks
swift projects/duolingo-web/observe-frontend.swift artifacts/output/playwright/typography-fresh projects/duolingo-web/fixture-reference-en-zh-v10.json --seed-progress projects/duolingo-web/evidence/english-pronunciation-v2/progress-source.json --reference-color-scheme light --observe-pronunciation --exercise-pronunciation-card-press --walk-pronunciation-practice --exercise-speech-denied --verify-pronunciation-restart --exercise-practice-quit
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-v26.json --observed artifacts/output/playwright/typography-fresh/observed.json --out artifacts/output/playwright/typography-fresh/frontend.json
```

[图片对照](comparison.html)。next：其它未访问导航与主课分支、实际音标增长，以及现有图像/声音失败继续；不将卡片局部改进作为整App交付。
