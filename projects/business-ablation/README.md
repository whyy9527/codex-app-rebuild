# 真实业务消融

旧 Stop Hook 已退役。本页与 evidence 保留历史结果；完整实验复跑须检出报告记录的 Git 版本，当前入口仅保留手动验证边界检查，不再注册或运行 Hook。

四组真实模型实验已执行并封存，最终均为公开12/12、留出2/2，另1项未知保留。本次没有观察到验收通过率收益；每组N=1，不证明统计、泛化或效率提升。[完整报告](REPORT.md)解释失败、输入公平性、实际宿主证据、介入、时间、token与限制。

四个对照是完整流程、去持久化行为进度、去Stop自动续跑、去补充观察。每组相同历史Swift基线、完整两课时需求、原始题库、原生驱动和初始四项验收。三组可获得额外八项已观察规格；去补充组不获得它们。它仍收到完整需求，允许独立实现所需功能。原版线上观察、共享语义断言、原生AX执行与核心检查分别报告。

- [预注册协议](PROTOCOL.md)和[留出观察计划](HOLDOUT-PLAN.md)：固定模型、预算、一次交接及评分规则。
- [注册与原版冻结](evidence/registration-01/registration.json)：原版4/4、12/12、留出2/2与1未知；四组启动前输入摘要。
- [统一结果](evidence/summary-01.json)：四组封存后各一次评分、回归/遗漏、用量与源码摘要。
- [完整组](evidence/full-01/final-result.json)、[去进度](evidence/no_behavior_progress-01/final-result.json)、[去Stop](evidence/no_stop_feedback-01/final-result.json)、[去补充](evidence/no_supplemental_discovery-01/final-result.json)：每组含最终回执、Source封存、每次失败、原生事件与显式接续记录。
- [43项最终检查](evidence/final-checks-01/python-result.json)：机制/控制检查，不能代替业务模型效果。

原版计划三条留出路径，两条确认、一条错误反馈退出不可用；始终报告2个可执行场景和1个未知，不把未知计通过。旧基线实际Course unavailable，保留原始回执；不把启动失败当业务断言失败。历史机制消融和独立多阶段试跑均未算作正式完整组。

复现新一轮需先注册新协议和盲留出，以下仅为准备入口，从仓库根运行：

    python3 projects/business-ablation/setup.py --publisher --out artifacts/business-ablation/publisher-new.json
    python3 projects/business-ablation/publish-reference.py --control <publisher-directory>

原版需要可访问Duolingo、Playwright Chromium；候选需要macOS、Swift和AX权限。确认冻结并提交输入后，使用setup.py的--master、--arm、--out从同一publisher建立隔离副本。父端用固定prompt-session1.txt启动原生CLI并核验模型，handoff.py在实际Stop后登记唯一交接，第二新会话用prompt-session2.txt显式adopt/resume。score.py只在最终Stop和Source封存后运行，不能给模型反馈再修复。控制器不启动模型，Hook不运行长验收。

本次CLI固定0.162.0-alpha.17.2 / gpt-6.1-sol / medium，workspace-write / on-request；未来环境变化需重新核验和注册，不把旧记录当新执行。每组两会话共享原20次/5400秒预算；全部中间回执不可覆盖。模型可写范围仅产品Source及指定任务指针，父端另存证明。流程审计不等于OS强制隐藏文件。
