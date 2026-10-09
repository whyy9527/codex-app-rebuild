# 架构

## 当前运行结构

Codex 使用原生工具观察和修改；MCP 提供任务操作；短 Hook 在 SessionStart 提供协议、Stop 检查是否继续、UserPromptSubmit 捕获显式暂停。Hook 不执行长验收，不启动模型。

| 所有者 | 职责 |
| --- | --- |
| `capabilities/exploration/harness.py` | 任务状态、预算、尝试、验收冻结、暂停与会话作用域 |
| `capabilities/exploration/storage.py` | 原子 JSON 与摘要 |
| `runtime/runner.py` | 真实命令、输出、超时与进程组清理 |
| `runtime/harness_mcp.py` | 工具协议和反馈投影 |
| `runtime/harness_hooks.py` | 宿主生命周期短适配 |
| `workflows/harness/install.py` | 显式目标项目注册，保留既有配置 |
| `runtime/codex_host.py` / diagnose | 原生宿主诊断，非在线循环依赖 |

现有状态：ready → working → verifying → complete；失败返回 ready 或进入 blocked / budget_exhausted；用户可暂停并显式恢复。锁协调 MCP 和 Hook。新会话不自动激活其他会话任务。

## 待完善的重建结构

行为规格层拥有行为 ID、前置状态、动作、期望、来源证据和 unknown/observed 状态；验收记录拥有该规格版本下的 pass/fail/unavailable。运行任务引用固定规格，不能把任务历史当作产品覆盖率。

重建工作流编排观察、原版验收、批次冻结、新版实现、差异修复与补充探索。运行时只执行显式命令，不推断规则。显式接续通过用户选择旧任务并重新绑定当前会话，不取消作用域隔离。

文件冻结应覆盖显式验收输入及配置，支持 Python、TypeScript 和 Swift；测试可执行文件与数据必须声明，不能承诺自动捕获所有动态依赖。单次验收时长应显式配置并受总预算约束；零场景执行不得当成业务完成。

## Swift 教育案例边界

课程和题库是内容数据；学习引擎拥有题目队列、答题反馈、错题重练和结算；进度仓库负责保存和恢复；SwiftUI 负责展示与输入。业务核心可以独立测试，并通过场景适配器与浏览器观察的语义对应。

测试分三层：核心业务测试、原生客户端交互、视觉审查。适配器只是桥梁，不能用核心测试通过代替 UI 通过。平台构建和实际交互分别提供证据。

## 已知限制

现有冻结只覆盖 manifest 中的 Python tests 与验证命令；单次验收上限 30 秒。验证进程崩溃恢复、UI 中断完整覆盖、完整 Stop 驱动模型续跑未验证。可信验证命令具有宿主权限。

仓库重命名保留 `exploration_*` 工具、`exploration-lab` 服务名和状态目录兼容。旧目标项目安装器启动路径需显式重装后更新，不自动修改其他项目。

## 研究关系

历史策略池、回放和组件库已从运行链移除，当前不是 Dream-RSI/Cordis 复现。研究机制、历史证据与恢复位置由 [RESEARCH.md](RESEARCH.md)维护。
