# 第四课结算与完成路径：实际链已接入，1:1仍失败

2026-10-11。默认夹具en/zh v5保留四课57题，新增实际原版六页结算：挑战完成→英语分数→连胜→双倍经验→传奇邀请→创建档案→主页。仅第四课接入此链，前三课仍是历史通用结算。结算快照的20经验、100%全对、连胜2来自现场；不能据此推广奖励或跨日规则，错误准确率公式仍未知，候选显示“—”。

`final-observed.json`、`final-window.json`、`final-progress.json`、`final-result.json`及PNG来自同一次实际原生运行，从空进度完成四课，执行首课误答/重练与重复词块撤回。walk_error=null，四课完成而completedCourses为空，未给未编译的第二节点或整个课程记完成。11项核心检查通过。

共享前端v6保留v5全部519项，增加35项，共554项：341pass、8fail、205not_run，整体fail。8个失败为结算回顾/传奇/建档4项、已完成节点练习/传奇2项、第二节点开始不可用1项、下一节点几何1项。次要操作目前显示文字，不是已实现按钮，不以文本出现计行为通过。下一节点暂未接入真实题库，不能回放旧课冒充。

完成节点与下一节点的弹窗文案、解锁样式及位置来自实际原版；第一节点命中区域与源几何相同，下一节点仍有0.117/0.148点差异，不放宽断言。人物/完成英雄图、字体、动画、声学等价仍待完成。`pixels.json`比较五张已有原版结算PNG与实际候选，全部different；建档页只有源AX证据，缺该状态原版PNG，不冒充六张视觉对齐。

源奖励页过渡AX残留前一页“回顾本单元”，稳定PNG无此动作；v6冻结纠正该源事实，原因见reference-validation.json，保留run02结果。run01失败于候选AX定位，修复为真实可见标题后完整走通。不会删除失败历史。

93个公开资源的源及渲染PNG哈希已核对。PDF检查证明Junior/Lucy/Eddy的character.url仍为半身裁切图，不是全身角色解决方案。第二节点实际Canvas角色帧证据见[后续探索](../english-next-node-v1/README.md)。这轮没有进行RSI效果消融，不用新增检查数宣称探索策略收益。

从仓库根复跑（输出目录须不存在）：

```sh
python3 projects/duolingo-web/compile-english-settlement.py
python3 projects/duolingo-web/freeze-english-settlement.py
swift build --package-path projects/education-swift --product LingoSeed
swift run --package-path projects/education-swift LearningCoreChecks
swiftc projects/duolingo-web/observe-frontend.swift -o artifacts/observe-frontend
artifacts/observe-frontend artifacts/english-settlement-recheck projects/duolingo-web/fixture-reference-en-zh-v5.json --walk-course --english-first-wrong --exercise-duplicate-words --reference-color-scheme light
python3 -m capabilities.rebuild.frontend --workspace . --contract projects/duolingo-web/frontend-english-v6.json --observed artifacts/english-settlement-recheck/observed.json --out artifacts/english-settlement-recheck/result.json
```

前端命令预期失败。下一步继续源第二节点的新题型和结算次要分支，修复真实行为与角色资源绑定，随后以固定基线开展真实探索机制消融。Goal仍active。
