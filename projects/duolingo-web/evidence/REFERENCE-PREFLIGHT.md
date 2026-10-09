# 原版可行性检查

执行日期：2026-10-10。真实线上 Duolingo、英文界面、English → Spanish、新访客。执行入口、依赖和重置边界见 [案例说明](../README.md)。这些记录的种类是 `reference_feasibility`，不能作为主流程冻结凭据，也不代表 Swift 已通过。

四条场景从新的访客浏览器分别执行，均实测启动 → 重置 → 场景 → 再次重置 → 停止。所有生命周期命令实际成功，断言差异为空，验收输入摘要完整。四条可行性探针并发执行；它们不是模型实验组，不用于比较耗时收益。

| 场景 | 结果 | 整次墙钟秒 | 原始记录 |
| --- | --- | --- | --- |
| 空答案 | pass | 44.4 | [choice-empty](preflight-choice-empty-02.json) |
| 正确选择与反馈 | pass | 50.5 | [choice-correct](preflight-choice-correct-02.json) |
| 错误选择、纠正与扣生命 | pass | 47.9 | [choice-wrong](preflight-choice-wrong-02.json) |
| 退出确认后取消，保留反馈 | pass | 46.5 | [exit-cancel](preflight-exit-cancel-02.json) |

原版选项顺序在不同访客中实际变化。驱动按当前题目映射词义并选择唯一可见选项，不固定选项位置；预期结果只由 `spec.draft.json` 提供，驱动不接收预期。已观察的课程/结算/配对/错题重练尚未纳入这四条可行性场景，不能因上述结果而记为验收通过。

首条错误场景还单独执行过一次：[第一次记录](preflight-choice-wrong-01.json)，43.0 秒。随后发现并修正了包装器的退出码处理：Python `finally` 中如果清理失败，旧包装器可能已经确定了之前的返回码；当前包装器在清理和完整性检查后才决定返回码。首轮源码保存在 [历史包装器](probe-reference-recorded-01.txt)，其 SHA-256 与首轮回执相符。表中四条均由修正后的同一版本实际执行。此修正没有改变业务断言。

浏览器安装前的失败见 [reference-probe-01.jsonl](reference-probe-01.jsonl)，缺少浏览器可执行文件，状态 unavailable。安装固定版本 Playwright Chromium 后，初态探针 [reference-probe-02.jsonl](reference-probe-02.jsonl) 成功建立首次课题面。接入失败、探索脚本误答、产品错误反馈和验收失败分别保留，不互相混称。

仍需完整的 reference/candidate 目标配置、主引擎参考回执和批次冻结，随后才开始这一批的 Swift 产品实现。当前没有正式业务消融或模型效果结论。
