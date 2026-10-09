# 当前项目的无监督迭代

从工具仓库根运行 `python3 -m workflows.harness.install --repo . --workspace <目标项目>`。目标项目的 `.codex/config.toml` 注册 MCP，`.codex/hooks.json` 注册三个 Hook，`.codex/exploration-lab/` 保存本机启动器和状态；不修改用户全局配置。信任项目并通过原生 `/hooks` 审查本工具后，在该项目重新打开会话。

给 Codex 一个明确目标、可执行验收和有限预算。仅启用 MCP 不会启动任务。

1. `exploration_start`：传入工作目录、当前 session_id、目标、verifier argv 及次数/失败/时间预算。可传 `acceptance_paths`（相对文件/目录列表）保护场景、配置、夹具和适配器；`verify_seconds` 控制单次验收时长，仍受总时间预算限制。省略路径时冻结默认 tests、Tests、e2e 及常见配置。冻结测试与验证命令。
2. `exploration_next`：记录本次基于反馈的假设，预留一次尝试。Codex 使用自己的工具修改。
3. `exploration_verify`：执行真实验收，返回输出和状态；通过完成，失败读取反馈后再尝试。不能改冻结测试绕过验收。
4. `exploration_status`：读取当前任务及反馈。Stop 仅对当前任务请求有限继续；重复事件和无进展受限，不运行长验证或模型。
5. `exploration_pause` / `exploration_resume`：用户暂停或需要外部输入时暂停，用户明确恢复后继续，不重置预算。UserPromptSubmit 也捕获明确暂停提示。

SessionStart 提供工具协议和当前 session_id。无任务的普通会话不启循环。工具不会替代权限审批、真人验收或美学评价。

运行 `python3 -m workflows.harness.diagnose --workspace <项目> --out artifacts/host.json` 检查原生清单。信任与清单不证明 Hook 已执行；需要实际日志和模型续跑证据。运行 `python3 -m unittest discover -v` 检查实现。

当前只注册实测宿主支持的 SessionStart、Stop、UserPromptSubmit。没有验证 UI 中断的完整覆盖或验证进程崩溃恢复。
