# 架构

本仓库运行在当前 Codex 中。原生 Goal 管理目标和持续执行，Codex 依据 workflow 决策与编辑，RSI 利用历史和反例改进探索，E2E 模具比较原版与候选。

## 当前所有者

| 所有者 | 输入与职责 | 输出 |
| --- | --- | --- |
| 原生 Goal | 用户目标、完成条件、停止／恢复 | 持续执行及最终完成判定 |
| `workflows/rebuild/WORKFLOW.md` | 选择探索或修复、消费反馈、验收与交付的方法 | 当前 Codex 的行动流程 |
| 案例 `rebuild.json` | 案例目标、原版／平台、现有输入路径和命令 argv | 项目入口；不记录运行生命周期 |
| `workflows/rebuild/project.py` | 读取显式项目，使用 `GOAL.template.md` | `create_goal` 参数、证据索引、现有命令调用；不安装 Hook 或启动模型 |
| `capabilities/rebuild/discovery.py` | 实际状态／动作／输入方式／结果历史 | 已记录的待探索动作；策略选择仍由 Codex 完成 |
| `capabilities/rebuild/contracts.py` | 共同夹具、场景、断言、两端适配器 | 参考确认、冻结批次、行为比较和覆盖 |
| `frontend.py` / `images.py` / `coverage.py` | 前端契约、实际观测、实测截图与动作库存 | 文字／几何／图像差异和未建模动作 |
| 案例观察器与驱动 | 真实浏览器或候选 UI 操作 | 状态、资源、截图、音频和动作回执 |
| `runtime/runner.py` | 显式命令与输入 | 命令输出、超时与进程组清理 |

项目清单是新增的连接点，引用已有能力而不复制断言。主文档不维护案例当前版本；由清单指向契约、夹具、历史与命令。运行结果继续落各次独立 artifacts／证据路径，`status` 只读汇总，历史结果明确标为历史，不据此完成 Goal。

## 原生 Goal 路径

用户选择原版、目标平台和要求 → Codex 读取 workflow 与项目配置 → `project goal` 生成原生 `create_goal` 参数 → 当前 Codex 在授权后调用原生工具。

每轮读取目标、真实历史与实际差异，选择一个能推动用户体验收敛的工作：补原版观察、修观察器、扩充模具或修候选。取得证据后再次比较并选择下一步。RSI 的消费者是这一决策过程及后续实际探针，不是独立强制阶段，也不要求先证明额外收益。

新发现进入共同场景和前端契约，两端实际操作后统一判定。业务、视觉、交互、动效和声音同时参与每轮验收；已有测试通过之后仍可回到探索。默认 workflow 不以固定阶段次数、六类检查或至少一个新增行为作为充分性判定。

`project run` 只按 argv 调用清单中的现有命令，使用显式 workspace，拒绝覆盖指定输出；不经 shell，不吞掉验收失败退出码。Duolingo 的 replay 命令连接既有先构建后驱动脚本，compare 连接原严格比较器。它们是封存课程的复跑入口，不是新的原版观察或整站验收。

## E2E 模具边界

业务层由 `contracts.py` 拥有共同动作与 expect，适配器只收到动作和前置状态，返回实际观察。参考确认后冻结，候选使用同批次；新增需求保留父版本。前端层由 `frontend.py` 独立读取状态事实，`images.py` 从实际 PNG 和窗口采样元数据计算比较。平台驱动不能自报通过。

语义、几何、像素和实际音频分别是不同测量；最终以共同用户需求组织交付。当前通用比较器已支持文字、角色、布尔值、矩形、采样颜色和严格整图；动画与声音还依赖案例工具，需求级汇总尚待实现。详细协议见 [BEHAVIOR-CONTRACT](BEHAVIOR-CONTRACT.md)。

## 兼容运行链

旧 `capabilities/exploration/harness.py`、MCP 与短 Hook 管理有界命令尝试／暂停／预算；旧 `capabilities/rebuild/pipeline.py` 管理固定业务批次的阶段与回执。它们保留已有测试和历史宿主证据，供明确需要该模式的环境使用。

原生 Goal 模式不调用安装器或 `exploration_start`，不同时由 Stop Hook 续跑同一任务。旧 Pipeline 的 complete 仅表示其有界业务批次完成，不能作为完整复刻 Goal 的 verifier。当前整理没有改写旧状态机或声称已经完成全部迁移；兼容用法见 [Harness](../workflows/harness/WORKFLOW.md)。

## 案例实现

Duolingo 观察器／契约在 `projects/duolingo-web`；Swift 的 `LearningCore` 拥有学习状态与持久化，`LearningModel` 连接操作和音频，SwiftUI 与原版 Rive／Lottie 资源负责呈现，原生 AX 驱动采集实际自有应用。

线上原版不能完全注入共同夹具或重置服务端，需保留实例、准备路径及限制。API 提供内容不等于 UI 开放对应操作；资源存在不等于已被产品消费。实例数据、平台映射与独立验证事实应保持来源可追溯。

案例尚未 1:1，试验已结束。源码中既有未验证交互修改不属于本次仓库整理的交付；边界见 [案例状态](../projects/duolingo-web/STATUS.md)。批次技术细节与旧文档见 [历史索引](history/README.md)，经验见 [复盘](DUOLINGO-LESSONS.md)。
