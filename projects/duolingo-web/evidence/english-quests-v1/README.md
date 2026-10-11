# 原版特别任务页：新导航探索、Swift替换占位页

2026-10-11从真实中文→英语匿名六课状态的发音页点击特别任务，进入/quests。冻结1200×732的ready.json/png、文字布局、面板、可见媒体和真实月挑战按钮样式。原候选是英文通用Quests占位内容，不是原版任务页。当前已用原版横幅、经验任务、锁定区、月挑战卡片和原始图形替换。

## 探索得到的新需求

源页面横幅“就是你了！”和每日任务30/30，更多特别任务锁定；右侧显示“每月挑战稍后揭秘！”及“去学个单元”。原Duo横幅、月挑战徽章和锁SVG从实际可见img公共URL取得，时钟为实际inline SVG；按原尺寸2x在临时Chromium页透明渲染并关闭，assets.json保留URL、尺寸、字节摘要。已有经验/宝箱素材与源URL相同，复用原件，不用系统图形替代。

“去学个单元”实际去/practice，首题为四个音频按钮及茶/你好/欢迎/热四项文字配对；没有作答，退出实际回/learn。practice-entry刚跳转时snapshot为空，practice-ready才是已加载题；两者保留，不能把空白当完成。该练习不是已有主课程，也不是发音练习，当前未编译完整序列；候选按钮进入仍未实现的Practice目的页，选择配对标题实际失败。没有用主课程或跳回主页伪装此入口。exploration-frontier.json把这条具体分支、每日重置、月挑战解锁和其它导航保留为后续工作。

当前14小时来自真实源观察，仅编入六课状态的questCountdown快照。compile-quests-page.py读取源DOM与进度seed，核对30/30与六课状态后生成v11；v10保持不变，v11仅增加这一个可选字段，七课102题不变。另用新输出完整重编译，文件字节相同。没有由快照猜每日计时、重置或新任务解锁阈值。当前默认切v11；显式指定原v10或原progress路径仍可运行。

## 实现、失败和验收

LearningView将中文Quests接入ReferenceHome；ReferenceQuests拥有中栏，ReferenceQuestMonthly拥有右栏，既有状态栏复用。首页右侧“显示全部”和侧导航共用同一路由。中文以外历史路由保留；新副本不是西语页面的替代。真实源 footer 是13px/700、第一排5个链接/第二排2个，按观察的href生成Link；本批未实际点击外部链接，不声称外部内容复刻。

原生观察器按真实导航读取AX/截图，不返回pass标记；源可见几何独立投影后，新增可执行17项在原版通过，完整练习1项pending。v27原样保留1729旧要求，追加18。首个原生构建10文案和4区域几何通过，但月挑战图片溢出影响父VStack宽度，按钮x+10、AX点击高48。限制HStack布局提议为源内容宽度，并明确50点contentShape后重跑，五项零容差几何全部通过，不修改源断言。

新18项最终15pass/2fail/1not_run：整图、独立练习标题仍fail；完整v27回执34pass/6fail/1707not_run/0unavailable。四个额外失败属于历史home要求与当前六课状态不匹配，不能据此声称本批覆盖全App。源同状态整页平均RGB差异由原通用页[23.238,24.650,26.109]降到[1.367,1.542,1.354]，仍不同；不掩码、不搜索偏移、不放宽容差。

最终实际四状态（主页、任务页、Practice入口、退出回主页），导航前后进度文件内容不变，主六课/生命3。另新夹具下实际五状态发音导航/按住/释放回归，共同全规格80pass/22fail/1645not_run，旧发音绝对分数几何及整图仍fail；不与任务页累计成覆盖率。Swift构建/23核心、完整56 Python测试通过。原始RSI论文、已执行负面消融不变，本批不构成RSI或自主探索收益证明。

捕获stem最初与导航action raw重名，预检在采样前拒绝、旧文件保留，使用新ready stem。编译器初版误以为fixture未包装，KeyError发生在写输出前；已改为data.candidate_course。首次原生按钮几何失败、原始观察与PNG保留，没有覆盖。没有环境声音录制。

## 复跑

仓库根，新输出文件（不覆盖已有证据）。下面归档回放无需运行原生，Pillow用于图像比较，预期退出1、34/6/1707/0：

```sh
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-v27.json --observed projects/duolingo-web/evidence/english-quests-v1/native-final/observed-portable.json --out artifacts/quests-replay.json
python3 projects/duolingo-web/compile-quests-page.py --out artifacts/quests-fixture-recompiled.json
```

实际原生运行需已有macOS AX/截图权限：

```sh
swift build --package-path projects/education-swift --product LingoSeed
swift run --package-path projects/education-swift LearningCoreChecks
swift projects/duolingo-web/observe-frontend.swift artifacts/output/playwright/quests-fresh projects/duolingo-web/fixture-reference-en-zh-v11.json --seed-progress projects/duolingo-web/evidence/english-pronunciation-v2/progress-source.json --reference-color-scheme light --observe-quests --exercise-quests-practice
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-v27.json --observed artifacts/output/playwright/quests-fresh/observed.json --out artifacts/output/playwright/quests-fresh/frontend.json
```

原始observed.json未改；portable只把capture.path重绑定到字节一致的入库PNG，receipt逐文件校验。完整全规格最终结果与18项子集分开保存，不删除旧要求。原生可执行退出0仅说明观察完成，前端仍fail。完整Goal保持active；下一步优先走完真实/practice并编译独立练习，而非停在页面结构通过。

[原版、旧版与新版截图](comparison.html)。
