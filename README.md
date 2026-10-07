# Codex Exploration Lab

帮助当前 Codex 完成有界的无监督迭代：保存任务进度，执行真实验收，根据失败反馈继续，到达预算或用户暂停时停止。

```text
用户目标 → Codex 修改 → MCP 验收 → 反馈 → 下一次修改
                       ↑
                项目 Hook 检查是否继续
```

唯一运行链：Codex + 六个 MCP 工具 + 三个短 Hook + 一个任务状态核心。没有独立模型服务、策略池、论文回放或演示任务。

## 在目标项目启用

从本工具仓库根执行：

```bash
python3 -m workflows.harness.install --repo . --workspace <目标项目目录>
```

只在目标项目的 `.codex/` 写入 MCP 配置、Hook、启动器和状态。重启该项目的 Codex 会话，按原生机制信任项目及审查本工具 Hook。工具源码继续位于安装时指定的仓库，不需要复制到每个项目。

然后告诉 Codex：

> 使用 exploration-lab 无监督迭代，目标是……；验收命令是……；最多尝试 10 次、30 分钟，失败后根据实测反馈调整。

MCP 提供操作，任务指令启动迭代；Stop Hook 用于在 Codex 提前结束时请求继续。仅启用 MCP 不会自行开始任务。[工作流](workflows/harness/WORKFLOW.md)包含工具调用协议。

## 验证与限制

Python 3.11+、POSIX、Codex CLI；无第三方 Python 依赖。运行 `python3 -m unittest discover -v`。项目级发现与隔离由真实 app-server 测试；注册、信任、Hook 执行和完整模型续跑分别报告。

验收命令是可信本地代码，具有宿主权限。通过只代表约定验收通过；本工具无法自行判断美学质量。验证进程崩溃恢复及完整自动 Stop 模型续跑仍待验证。

仓库保持私有。本轮删除的研究代码和历史实验可从 Git 提交 `2ad5175` 找回，不再成为当前运行依赖。[架构](docs/ARCHITECTURE.md)说明保留机制。
