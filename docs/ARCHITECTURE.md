# 架构

## 当前运行结构

Codex 使用原生工具观察和修改；MCP 提供七个任务操作；短 Hook 在 SessionStart 提供协议、Stop 检查是否继续、UserPromptSubmit 捕获显式暂停。Hook 不执行长验收，不启动模型。

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

## 重建结构与当前范围

`capabilities/rebuild/contracts.py` 已拥有行为 ID、前置状态、动作、期望与证据清单，分离 unknown/observed/decision 和 not_run/pass/fail/invalid/unavailable/timeout。它对两端动作适配器执行统一断言，检查 start/reset/scenario/reset/stop，并在输入与源码变化后拒绝旧结果。参考端通过后才能冻结；增量批次必须关联真实父批次并保留旧场景。

`workflows/rebuild/cli.py` 提供 check、verify、freeze、coverage。回执不覆盖，记录规格/源码/输入摘要、实际观察和差异。目标 layer 显式区分 browser_ui/native_ui/core/test_double；协议不是UI证据认证，当前只有测试替身证明机制。详细契约见 [业务规格](BEHAVIOR-CONTRACT.md)。

运行任务应引用固定规格，不能把任务历史当作产品覆盖率。`capabilities/rebuild/pipeline.py` 已保存 explore→specify→reference→freeze→implement→discover→reference→freeze→implement→review 的阶段证据与回执。当前 Codex 依据 next_action 工作，step 校验阶段，不生成伪观察或另起模型。Harness 拥有模型尝试，Pipeline 拥有阶段推进及额外阶段次数/时间上限；两者不复制同一状态。原生 Stop 驱动的单任务模型 fail→pass 续跑已验证（见 `projects/rebuild-mechanisms/REPORT.md`）；整个多阶段重建仍待真实任务验证。

重建工作流编排观察、原版验收、批次冻结、新版实现、差异修复与补充探索。运行时只执行显式命令，不推断规则。`exploration_adopt` 允许用户明确选择暂停任务转交新会话，不自动恢复、不重置预算；旧指针失效，忙碌目标会话和异工作目录被拒绝。正在执行的验收必须结束后才能转交；暂停期间取得的成功结果在显式恢复时正确完成，无须额外消耗尝试。

已实现 `acceptance_paths`：按显式文件/目录冻结验收及夹具，不限语言；默认包括 tests、Tests、e2e 和常见包/Playwright 配置。清单检测新增、删除和修改；拒绝越界路径。已实现 `verify_seconds`，受总截止时间约束；旧任务仍按原冻结契约验证。动态依赖必须明确声明，不能承诺自动捕获所有依赖。业务层零场景判定仍待实现；现有通用层只拒绝 unittest 的空发现。

## Swift 教育案例边界

课程和题库是内容数据；学习引擎拥有题目队列、答题反馈、错题重练和结算；进度仓库负责保存和恢复；SwiftUI 负责展示与输入。业务核心可以独立测试，并通过场景适配器与浏览器观察的语义对应。当前 `projects/education-swift` 将 LearningCore、SwiftUI 客户端和可执行核心检查分开；`projects/duolingo-web` 拥有线上浏览器与原生 AX 驱动及共享规格。首批实际结果见该案例 evidence，不能由架构分层推导完整业务已完成。

测试分三层：核心业务测试、原生客户端交互、视觉审查。适配器只是桥梁，不能用核心测试通过代替 UI 通过。平台构建和实际交互分别提供证据。

## 已知限制

默认单次验收时长 30 秒，可显式设置；验收保护只覆盖声明的输入。源码完整性检查记录常见代码文件，运行数据不自动视为源码。业务批次 deadline 阻止新的动作；到期后保留最多5秒的 stop 清理额度。验证进程崩溃恢复、UI 中断完整覆盖、多阶段模型重建未验证。可信验证命令具有宿主权限。

仓库重命名保留 `exploration_*` 工具、`exploration-lab` 服务名和状态目录兼容。旧目标项目安装器启动路径需显式重装后更新，不自动修改其他项目。

## 研究关系

历史策略池、回放和组件库已从运行链移除，当前不是 Dream-RSI/Cordis 复现。研究机制、历史证据与恢复位置由 [RESEARCH.md](RESEARCH.md)维护。
