# 架构

目标只有一个：帮助当前 Codex 完成更可靠的有界无监督迭代。

| 组件 | 职责 |
| --- | --- |
| `runtime/harness_mcp.py` | 六个工具的参数和协议适配 |
| `runtime/harness_hooks.py` | SessionStart 提示、Stop 续跑条件、UserPromptSubmit 暂停 |
| `capabilities/exploration/harness.py` | 唯一任务状态、会话作用域、预算、冻结验收及状态迁移 |
| `capabilities/exploration/storage.py` | 原子 JSON 写入与摘要辅助函数 |
| `runtime/runner.py` | 真实命令、输出、源码完整性及超时清理 |
| `workflows/harness/install.py` | 在目标项目 `.codex/` 注册并保留已有配置 |
| `runtime/codex_host.py`、`workflows/harness/diagnose.py` | 原生宿主集成验证；线上循环不依赖诊断客户端 |

MCP 与 Hook 共用 Harness 状态。Codex 负责思考、编辑和选择下一步；工具不启动另一个模型。状态为 ready → working → verifying → complete；失败可返回 ready 或进入 blocked/budget_exhausted；用户可暂停并显式恢复。文件锁协调 Hook 和 MCP 写入。

项目配置仅对受信任项目生效；Hook 另需原生审查。一个工具仓库可为多个项目安装，每个项目拥有独立配置和状态。工作目录和会话 ID 绑定当前任务；新会话不会自动继承其他会话的 active 任务。

已移除策略池、回放、独立模型适配器、装箱与线性函数演示、组件容器、SQLite 实验账本和历史实验工作流。旧账本的摘要与旧会话模块的原子保存函数提取到 storage；其余无活跃调用者。源码副本快照、媒体标签和未知模型费用字段也已删除，保留实际反馈所需摘要。

限制：冻结测试只覆盖当前 manifest 的 Python tests 文件和验证命令，不能保证任意项目的验收充分性。可信验证具有 OS 权限；验证中进程崩溃恢复、UI 中断覆盖和完整自动模型续跑尚未验证。
