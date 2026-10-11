# 单元12：指南、当前课程、声音与下一课补漏

这批由上一轮“当前课／指南仍复用购物课”的反馈继续实际探索，未缩减完整复刻目标。原版为中文母语→英语、访客、第2阶段第2部分；准备状态英语分10、505宝石、4生命。独立跳级测试的5生命不能用于普通课程。实际浏览器会话仍保留，原版进度没有重置。

## 实际发现与实现

原版 `/guidebook/en/12` 有五句独立内容、25个词语焦点和五段点击播放的原语音。当前第1/6课实际完成17道判分题、1次口语暂缓、2个鼓励页，回顾18卡，完美结算15XP／100%，档案提示后返回第2/6课主页。Swift已接独立指南／课程／口语暂缓／回顾／结算／主页保存与重启恢复，不再复用购物实例。原版完美结算画面已用实际原SVG画帧接入；动画及相位仍不等价。

播放探针实际记录HTMLMediaElement调用：六个答对窗口捕获同一原音效，volume0.35；完成音效volume0.5。缺失窗口保留unknown，不能据此补写每题的声音。Swift支持资源对应播放增益；三次真实UI动作的自有应用输出已录音，只采自有PID，不采麦克风。[测量](native-final/audio-resource-measurements.json)相关系数约0.99999／0.99996／0.99991，拟合增益约1／0.35／0.5。这证明资源在对应动作中实际播放，不证明与原版声学输出相等。

继续原版补漏发现：课后延迟出现“在这里学习英语字母！”遮罩，电台、学习、提示文字点击被拦截，Escape也未消除；实际点击灰色背景(1100,650)后提示消失。再返回主页点击电台，实际出现“公寓参观／完成以上全部等级才可以解锁哦！／未解锁”。第2/6课实际首题是图片选择“客厅”，不是第1课重复。新首题已判分通过并停在下一题，未完成第2课；Swift目前仍会重复第1课，属于已发现缺口。

这些发现进入[历史与frontier](frontier.json)及[下一轮反馈](exploration-feedback.json)，95状态、54条有回执的边、2741待探索动作。未知后继不填成已探索。原论文Dream-RSI和Cordis继续保留在[研究来源](../../../../docs/RESEARCH.md)。本轮利用历史遗漏选择新分支，但没有新的匹配预算模型因果对照，不宣称RSI收益；既有02不可判定、03测量复查中止的负面记录见[原报告](../../../exploration-ablation/REPORT.md)。后续真实模型对照应新注册04，不能把已见页面重命名为未见留出。

## 前端模具与结果

[v69](../../frontend-english-v69.json)完整保留v68，追加45个原版状态，共14717项。[v70](../../frontend-english-v70.json)再追加延迟遮罩、电台锁定、下一课弹层及首题前后5状态，共15255项。新题目回放采集器已在真实第2课验证：答前6控件／11文字范围、反馈8控件／14文字范围，包含rect、CSS、enabled、命中测试及裁剪祖先，和整图共同保留。以后不能只记录题目标题就声称前端已验证；本批旧17题没有这些补采字段，不能倒填。

最终同一二进制实际跑46原生状态，0旅程执行失败，包括完整课程和真实重启。[严格结果](native-final/frontend-v70.json)：258pass／178fail／14272not_run／547unavailable，45个已运行整图全fail。not_run包含历史未运行要求及新发现未实现状态，不能作为完成率；unavailable含尚未映射的控件和采集缺口，不能当通过或全归为产品缺失。源指南逐字DOM、字体、图形、控件几何、鼓励／结算动效、延迟遮罩和下一课仍有差异。

[并排对照](comparison.html)只供审阅，不替代严格比较。两个已知平台别名错误已修正，用[显式绑定器](../../bind-frontend-aliases.py)将原生实际测得事实绑定到契约ID；保留原回执与绑定摘要，不生成位置或通过标志。[早期驱动失败](driver-failures.json)保留：录音器未编译、向视口外元素滚动无效、回顾关闭ID错误。最终修正后重跑全链路，未删除断言。

原版初期指南打开失败和错误命名的 `unit12-guide-top` 实际是带通知的主页，不能用作指南参考。正式指南仅 `unit12-guide-ready-top/bottom`。源文本归档移除本机路径及日志末尾空行，[审计](source-archive-audit.json)保留原始与归档哈希；原始字节不冒充归档。原生截图转运仅修改文件位置，字节哈希、二进制摘要及测量值保留。

## 复跑

从仓库根运行，输出目录／回执使用新路径；原版操作需先确认当前真实路径与正文。不要重置当前访客进度来冒充同状态。

```sh
python3 projects/duolingo-web/compile-unit12-guide.py --out-dir artifacts/unit12-guide-recompile
python3 projects/duolingo-web/compile-unit12-lesson.py --out-dir artifacts/unit12-content-recompile
python3 projects/duolingo-web/freeze-unit12-content.py --out-dir artifacts/unit12-content-refreeze
python3 projects/duolingo-web/freeze-unit12-next-lesson.py --out-dir artifacts/unit12-next-refreeze
python3 -m projects.duolingo-web.compile-unit12-content-frontier --out-dir artifacts/unit12-content-frontier-new
swift build --package-path projects/education-swift
swift run --package-path projects/education-swift LearningCoreChecks
swiftc -parse-as-library projects/duolingo-web/capture-owned-audio.swift -o artifacts/unit12-owned-audio-new
swift projects/duolingo-web/observe-frontend.swift artifacts/unit12-content-native-new projects/duolingo-web/fixture-reference-en-zh-v14.json --seed-progress projects/duolingo-web/evidence/english-unit12-content-v1/prepared-progress.json --reference-color-scheme light --exercise-home-journey projects/duolingo-web/unit12-content-native-scenarios-v1.json --audio-recorder artifacts/unit12-owned-audio-new
python3 projects/duolingo-web/bind-frontend-aliases.py --observed artifacts/unit12-content-native-new/observed.json --aliases projects/duolingo-web/evidence/english-unit12-content-v1/aliases.json --out artifacts/unit12-content-native-new/observed-bound.json
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-v70.json --observed artifacts/unit12-content-native-new/observed-bound.json --out artifacts/unit12-content-native-new/frontend-v70.json
python3 projects/duolingo-web/measure-unit12-owned-audio.py --native artifacts/unit12-content-native-new --out artifacts/unit12-content-native-new/audio-resource-measurements.json
```

当前34核心业务检查、61Python检查、21Node检查通过；源编译器和契约冻结可逐字复现。核心检查不验证UI、声音或整图。完整Goal active，1:1未完成；下一批优先实现已发现的遮罩／电台与第2课，继续指南词语、错误／口语分支和真正匹配预算的探索机制对照。
