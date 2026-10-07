# Codex harness 十轮接入报告

本次目标是让 Codex 使用注册工具完成有状态、有反馈、有停止条件的迭代。六个 MCP 工具及三个原生支持的 Hook 已在本机注册，并在原生 `/hooks` 中逐项审查信任，未信任其他待审 Hook。没有新增独立子模型调用，没有恢复视频任务，也没有论文复刻率或泛化收益结论。

## 十轮源码修改

| 轮 | 行为 | 同一验收修改前后 | 提交 |
| --- | --- | --- | --- |
| 1 | 持久任务、会话作用域及冻结验收 | fail → pass | `f44dfaf` |
| 2 | 幂等预留尝试与迭代预算 | fail → pass | `aeb2a05` |
| 3 | 执行冻结验收、隔离 Python 缓存 | fail → pass | `908b5fd` |
| 4 | 六个 MCP 工具及输入契约 | fail → pass | `59a820f` |
| 5 | SessionStart 与 Stop 短 Hook | fail → pass | `8e16a9a` |
| 6 | Stop 去重、预算与无进展停止 | fail → pass | `6513fb8` |
| 7 | 中断暂停与不重置预算的恢复 | fail → pass | `1e16c63` |
| 8 | 保留用户配置的原生注册 | fail → pass | `0725549` |
| 9 | 真实宿主清单及显式暂停兼容 | fail → pass | `b5a6384` |
| 10 | 拒绝空验收 | fail → pass | `2684c9f` |

[回执](receipts.json)保存实际输出、源码摘要及固定验收摘要；[审计](audit.json)核对十组 fail→pass、父子关系和每组修改后源码到对应提交。不同轮验收不同，不构成统一基准改善。审计命令：

```bash
python3 -m workflows.harness.audit --receipts projects/harness/receipts.json --out artifacts/harness-audit.json
```

第三轮首次修改后仍失败：同秒等长 Python 改动命中旧字节码。保留 `h03-after` 失败记录；改为每次验证使用新缓存目录后 `h03-after-retry` 才通过。第九轮原清单检查过弱，增加真实宿主兼容检查，保留原始检查并以 `h09-before-compat` / `h09-after-compat` 为审计对。第十轮 Python 3.14 空 unittest 发现实际返回 5；修改前任务处于可再试失败，修改后将空验收识别为 invalid 并停止，不声称空测试曾报告成功。

最终 `h-final` 执行 `python3 -m unittest discover -v`：71 项通过，实际输出见回执。测试包括隔离配置下的真实 app-server 清单检查；协议测试替身不算真实模型实验。

## 真实 Codex 宿主自修复

[自修复记录](self-repair.json)来自真实 Codex app-server 的 `mcpServer/tool/call`，使用已注册的 exploration-lab 服务器，而非绕过宿主直接调用 Python 方法。当前主会话 Codex 根据工具反馈编辑；没有额外模型 API 调用。

任务验证命令固定为 `python3 -m unittest tests.harness.test_resume_reserved -v`。首次实际失败为 `budget_exhausted != working`：最后一次已预留、未验证的尝试被暂停后，恢复错误地把它当作预算耗尽。根据此反馈修复 `Harness.resume`，保留截止时间限制，不重置任何预算。第二次使用相同验收通过，任务 complete，耗用两次尝试。前后测试清单与验证器摘要相同；新回归测试及源码一起提交。

这验证了“当前 Codex → 已注册工具 → 实测失败 → 修改 → 同一验收通过”。它不是独立子模型实验，也不是 Hook 自动驱动的模型闭环。

## 原生注册及信任

[宿主清单](native-host.json)由 `python3 -m workflows.harness.diagnose --workspace . --out projects/harness/native-host.json` 生成：六个工具可发现，SessionStart、UserPromptSubmit、Stop 均 enabled/trusted，清单错误数为 0。原生 CLI 版本为 0.160.1。本机不列出 Interrupt；暂停语义由显式工具及 UserPromptSubmit 提供，但 UI 中断的完整覆盖未验证。

首次使用 `codex mcp add` 意外归一化了既有 node_repl 配置。已从安装前私有备份恢复原始字节，再仅追加本项目 TOML 表；对全部原有设置逐项核对相同。安装器已改为仅追加自己的表，拒绝同名异主服务器；备份及本机绝对路径不入库。未修改认证或绕过信任。

**注册和信任不等于 Hook 执行证明。** 原生信任界面已经实测；app-server 清单已验证，但本轮未取得真实会话的本项目 Hook 执行日志，SessionStart 上下文注入及 Stop 自动模型续跑仍待实际任务测量。Hook 单元测试证明处理器语义，不替代宿主端到端验证。官方契约见 [Codex hooks](https://learn.chatgpt.com/docs/hooks)。

## 运行边界与下一步

状态由 harness 单独拥有，编辑动作仍用 Codex 原生工具。尝试/失败/墙钟/Stop 事件有界，重复事件去重，无实测进展停止；恢复不重置预算。验证器和测试清单冻结，空 unittest 验收拒绝。可信本地命令仍拥有服务器 OS 权限，工具不是沙箱；无法保证任意命令代表充分验收。

当前还缺验证中进程崩溃恢复、真实 Stop 续跑、真实 UI 中断与长期任务成功率验证。下一轮应先测这些宿主行为，再测多任务人工介入率；不继续堆叠仅为凑轮数的算法或包装。媒体审美仍需真实视听评价，本次测试不能替代。

[宿主工作流](../../workflows/harness/WORKFLOW.md)是运行协议的唯一维护入口。历史论文策略实验保持独立，仍不具备完整基准复现或无人值守模型效果证据。
