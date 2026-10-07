# Codex 内的探索工作流

本项目是 Codex harness 的工具。模型仍由 Codex 驱动；MCP 提供状态和实测反馈，短 Hook 提供发现与有限续跑。只为用户明确请求的迭代任务启动循环。

## 本机接入

在仓库根运行 `python3 -m workflows.harness.install --repo .`。安装器保留既有配置并备份，生成仅在本机使用的启动器；不修改认证或自动授予 Hook 信任。重启 Codex，用原生 `/hooks` 审查本项目命令后信任，保留其他 Hook 的原状态。Hook 功能需在宿主启用；本机已启用。

运行 `python3 -m workflows.harness.diagnose --workspace . --out artifacts/native-host.json` 检查实际支持的 Hook、信任及 MCP 清单。清单不能证明 Hook 已执行或模型已自动续跑。官方契约见 [Codex hooks](https://learn.chatgpt.com/docs/hooks)。本机 Codex 0.160.1 支持本项目 SessionStart、Stop、UserPromptSubmit；配置中的 Interrupt 未被该运行时列出。

## 模型操作协议

1. 先确定工作目录、用户目标及可执行的真实验收。用 `exploration_start` 显式传入 workspace、SessionStart 提供的 session_id、objective、verifier argv 和有限 max_iterations/max_failures/max_seconds。测试清单与验证命令随任务冻结；工具不会自行开始编辑。
2. 调用 `exploration_next` 预留一次尝试并写清基于反馈的假设；使用 Codex 原生工具动作，随后调用 `exploration_verify`。重复 next 不多扣预算；重复 verify 不重复执行已完成尝试。
3. 若失败，读取反馈决定下一步；不可通过删改冻结测试把失败变成通过。验收无效、执行器不可用、连续失败、时间/尝试预算耗尽或无进展时停止。用 `exploration_status` 获取真实状态。
4. Stop 仅对当前会话的 ready/working 任务请求继续；有 turn_id 才处理，重复事件去重，无实测进展会封堵重复续跑。它不自己执行模型或验证。无 active 任务时不拦截结束。
5. 用户说暂停时调用 `exploration_pause`，显式暂停提示也由 UserPromptSubmit 捕获；恢复必须来自用户，调用 `exploration_resume`，不重置预算。当前不承诺 UI Interrupt 的宿主覆盖。

验收通过仅代表约定条件通过；美学任务须有实际视听反馈，不能用测试数替代。命令是可信本地代码，拥有服务器的 OS 权限；该工具不是安全沙箱。尚无验证中进程崩溃的自动恢复。

## 复核

`python3 -m unittest discover -v` 验证实现。`python3 -m workflows.harness.audit --receipts projects/harness/receipts.json --out artifacts/harness-audit.json` 复核本阶段十组验收与准确提交。失败和替代检查均保留；新增测试跨轮不构成统一基准提升。

本阶段真实宿主调用及边界见 [报告](../../projects/harness/REPORT.md)。没有独立子模型调用，也尚未实测自动 Stop 完整续跑。
