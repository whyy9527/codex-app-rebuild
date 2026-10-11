# 听力暂缓替换状态机与真实原生验证

2026-10-11。依据[上一批原版冻结轨迹](../english-general-listening-decline-v1/README.md)实施，完整Goal继续active，原论文及负消融仍由[RESEARCH](../../../../docs/RESEARCH.md)拥有。本批没有新增原版导航、正常口语评分或声学相等结论，也没有模型消融调用。

## 实际改动

LessonDefinition新增可选`listeningDeclineReplacements`，由已观察实例提供替换题。暂缓不评分、不扣心、不增加连对；继续后在当前位置换成实际翻译，作答之后才推进。替换内容保留到复习，不会恢复已暂缓听力；新增核心检查分别验证实际全对路径和额外注入错误后的复习状态不变量，后者不冒充本源实例的已观察错误路径。原有配对暂缓无替换时维持其已有推进，旧课程夹具保持不变。

编译器从新源前六题、实际listenTap及后十份接受回执生成独立实例；总计16评分位置，替换原题未评分。口语暂缓后实际water and tea路径、三挑战、全对5XP/100%结算、直接建档提示均保留。结果数字来自原版PNG，未读取动画数字列表冒充成绩。七个新增原版MP3和原版黄色勾图形有资源摘要；未识别替换角色与音频仍缺，不用猜测素材补成通过。

`--general-practice-fixture`允许显式选择该观察实例，并从真实任务页入口加载。默认课程仍使用既有通用实例；这不是已实现自适应选题算法，也不证明本实例不暂缓后的未来题单。原生驱动`--exercise-general-listening-decline`操作实际控件，未直接修改Lesson状态。

## 失败驱动的前端修复

native-01完整45状态通过执行，但播放按钮被ReferenceButton拉成286点宽、黄色继续按钮宽524点，词块虽然禁用却错误变灰。source截图仍黑字，宽条明显不一致。native-02复用原版100×100／70×70播放图形与控件，黄色继续150×50，实际黄色勾、24px标题和固定底栏；保留两轮回执及不同二进制摘要。

native-02又测出词库y440而原版405，不能拿按钮尺寸通过当整页一致。最终只调整该听词组答题区为单条线、原版间隔、19点词块及暂缓后的黑字，native-03词库y405。词块宽度/AX高度仍不同；暂缓入口为[140,637,161,50]而源[140,639,160.6015625,50]，继续x910而源909.9921875，仍fail。进度长度/颜色、字体、其它题角色和动画也继续。

同一源图全页RGB平均差：暂缓前约5.75→2.16→1.87，暂缓反馈约8.58→2.46→2.15。28张新分支整图**全部fail**；未加容差、屏蔽或对齐搜索。`image-delta.json`保存各状态三轮原值，动画时刻可能影响其它状态，不能将差值当RSI收益。

第三次构建曾触发Swift复杂表达式类型检查超时；拆出独立视图并使用ViewBuilder后第四次构建通过，失败日志保留。独立进度校验一度用了历史主课程ID、之后又比较了Set编码数组的次序，分别失败；检查实际当前ID、按集合语义校验后确认主六课和红心5不变，真实终止重启保存独立练习完成。诊断修正见native-01/business-validation.json，不能把验证脚本错误说成App错误。

## 共同验收

v31原样保留v30的1885项，追加18项词库enabled、播放几何、暂缓/继续的角色/enabled/几何，共1903。源投影52pass/0fail/1851not_run，只是源自检。最终native-03完整45状态、真实重启，无驱动失败；共同契约56pass/35fail/1812not_run/0unavailable，其中本分支52项22pass/30fail（28整图加2几何）。native-01同分支18pass/34fail、native-02为22pass/30fail，没有删除断言以达标。

最终二进制默认练习回归47状态、一次错答/更正/红心奖励及真实重启执行通过；共同v31为89pass/55fail/1759not_run。两条轨迹分别报告，不叠加通过数。构建、25核心、完整56 Python通过。归档PNG字节核验，观测文件只重绑定相对capture路径，再执行共同验证得到相同结果。

下一步继续把新行为接入实例选择和通用探索循环，修复已发现整图差异，探正常口语、其余导航、计时恢复、奖励条件与音频。此批是实际反馈驱动的人工实现与自动回归，不是自主探索或RSI效果实验，完整目标未缩减。

## 复跑

```sh
python3 projects/duolingo-web/compile-general-listening-decline.py
python3 projects/duolingo-web/freeze-listening-controls.py --out-dir artifacts/listening-controls-new
swift build --package-path projects/education-swift
swift run --package-path projects/education-swift LearningCoreChecks
python3 -m unittest discover -v
swift projects/duolingo-web/observe-frontend.swift artifacts/listening-native-new \
  projects/duolingo-web/fixture-reference-en-zh-v11.json \
  --seed-progress projects/duolingo-web/evidence/english-general-listening-decline-native-v1/native-03/progress-before.json \
  --reference-color-scheme light --observe-quests --exercise-general-listening-decline
python3 -m capabilities.rebuild.frontend \
  --contract projects/duolingo-web/frontend-english-v31.json \
  --observed projects/duolingo-web/evidence/english-general-listening-decline-native-v1/native-03/observed.json \
  --out artifacts/listening-compare-new.json
```

输出目录须为新目录；最后比较因真实前端失败返回非零是预期。切换默认练习回归时移除新分支flag并传`--exercise-general-practice`，仍使用真实任务页和独立进程。
