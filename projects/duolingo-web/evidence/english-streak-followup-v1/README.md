# 实际连胜探索、反馈修订与Swift消费者

由上批输入方式和缺失消费者反馈进入连胜下游；真实模型选择下滚，观察目标／俱乐部／固定标题后修订为下一月键盘操作。实际执行到11月，不把反复打开弹窗算探索充分。模型成本与05预检查失败见[05／06报告](../../../exploration-ablation/REPORT05-06.md)，无匹配对照或RSI收益声明。

原版当前访客10分／1天／155宝石／5红心，1200×732，独立实测截图scale2。下滚0→416、滚动面板480×636／内容1052，左右箭头14×14；关闭／重开与重置均使用真实UI。普通整页起点检查发现背景虚拟化切换，失败保留；06单独登记面板起点，完整背景仍参与整图验收。原始[状态和动作](source)、[归档摘要](source-archive-audit.json)、[历史](history.json)、[前沿](frontier.json)可追溯。鼠标／悬停／Enter分别记录，滚动区域来自实际scroll_regions；键盘下一月不消除其它输入方式或上月未知。

Swift接原版连胜弹窗、原SVG及实际动画一帧、日历滚动／月份箭头／关闭返回、固定标题、目标和俱乐部。首次实际截图发现年份被本地化为2,026及相邻月份缺失；修为明确字符串及真实三月布局，保留[初次](native-first)、[修年份](native-final)和[最终同二进制](native-delivery)，不把三次构建累计为独立样本。八步鼠标／滚轮／Return旅程无驱动失败，11项实际检查通过，二进制摘要匹配。[逐轨迹检查](validation.json)、[旅程](../../streak-native-scenarios-v1.json)、[绑定事实](observed-bound.json)、[归档摘要](native-archive-audit.json)。

v77保留20127旧项，新增776，共20903；本批311pass／22fail／20132not_run／438unavailable，四张整图全fail。源字体探针确认日历标题为PingFangSC-Semibold、数字为DuolingoSans-Bold；本机原TTF探针对应700轴，未因观感全局猜改字重。当前主页背景／字体绘制／亚点几何仍不等价，图片不加遮罩或容差。169状态／90条边／5062待探索记录不代表完成率。[严格逐项结果](frontend-v77.json)、[实际截图对照](comparison.html)。67Python／21Node／36Swift核心检查及构建通过；它们不能替代前端或声音。

本批新操作未作对齐音频采集，声音等价／静音未知；动画只有原版一帧，轨迹未匹配。既有真实发音输出证据不扩展为全音效通过。下一步优先未完第三课、新听音配对实例、故事／电台与课程目录，再依据整图和声音失败进行真实产品质量对照；完整Goal保持active。[失败及下一步反馈](exploration-feedback.json)。

从仓库根使用新的输出路径复跑：

```sh
PYTHONPATH=. python3 projects/duolingo-web/freeze-streak-followup.py --out-dir artifacts/streak-freeze-new
projects/duolingo-web/run-native-course.sh artifacts/streak-native-new projects/duolingo-web/fixture-reference-en-zh-v14.json --seed-progress projects/duolingo-web/evidence/english-home-stat-branches-v1/native-complete/progress.json --seed-preferences projects/duolingo-web/evidence/english-home-stats-v1/native-final/progress.json.preferences.json --exercise-home-journey projects/duolingo-web/streak-native-scenarios-v1.json
python3 projects/duolingo-web/bind-frontend-aliases.py --observed artifacts/streak-native-new/observed.json --aliases artifacts/streak-freeze-new/aliases.json --out artifacts/streak-bound-new.json
python3 -m capabilities.rebuild.frontend --contract artifacts/streak-freeze-new/contract.json --observed artifacts/streak-bound-new.json --out artifacts/streak-result-new.json
```

前端命令预期退出1，旧未运行状态不能算通过。时间跨日须使用新原版观察，不能拿固定12日截图证明其它日期；当前实现多日连胜历史尚未获源证据。冻结重建使用归档事实，不宣称在线访客可任意重置。原资源URL／SVG及3倍PNG摘要见[source资源回执](source/resources-with-arrows.json)。
