# Codex App Rebuild

**当前状态：产品复刻未完成。** 用户实际体验指出主页、视觉还原与声音缺失，已撤回此前整体完成判断；[反思与纠正](docs/REBUILD-RETROSPECTIVE-2026-10-10.md)记录原因，[产品验收v3](projects/duolingo-web/PRODUCT-ACCEPTANCE-v3.md)固定下一阶段标准。既有12项行为与消融结果只覆盖各自范围。

把原产品的可观察行为变成可执行规格，让 Codex 在有限上下文和预算内重建 App。仓库保持私有；改名不代表开源或发布。

## 方法

观察原版 → 保存行为与证据 → 在原版验证验收 → 冻结本批规格 → 实现新版并按失败反馈迭代 → 独立验收与补充探索。

测试重新计算完成状态，文档保存决策与未知。通过现有测试不代表产品完整；未探索、不可用、失败和通过必须分开。探索新增行为后建立下一批规格，不能在实现期间降低当前验收标准。

## 当前能力

已有七个 MCP 工具、三个短 Hook、任务持久化、真实命令验收、显式多语言验收输入冻结、可配置验证时长、次数/时间/无进展停止与显式暂停。Codex 自己思考和编辑，工具不启动独立模型。已有机制检查和机制消融；原生 Stop 驱动的有界单任务模型续跑已验证，真实 App 重建收益尚未证实。

已加入共享业务场景与断言、参考确认后冻结、两端动作适配协议、行为级覆盖及增量规格检查；见 [业务规格](docs/BEHAVIOR-CONTRACT.md)和 [重建工作流](workflows/rebuild/WORKFLOW.md)。协议已有机制测试，已加入持久阶段控制及暂停任务的显式跨会话接续。Duolingo 网页与实际 SwiftUI 客户端已跑通12条共享场景（冻结 v2），包含配对、拼句、错题重练、完成恢复及退出丢弃；真实宿主多阶段模型重建及跨会话接续已完成一次可行性验证（原版/模型原生实现均12/12），见 [模型流程证据](projects/model-pipeline/README.md)；[真实业务四组消融](projects/business-ablation/REPORT.md)已完成：四组均公开12/12、可执行留出2/2，另1项未知，N=1未观察到通过率收益。[本轮逐项审计](docs/DELIVERY-AUDIT.md)连接八项证据与最终复验。最新完成情况见 [Roadmap](docs/ROADMAP.md)，机制限制见 [架构](docs/ARCHITECTURE.md)。不把规划写成已实现能力。

## 在目标项目安装迭代工具

Python 3.11+、POSIX、Codex CLI，无第三方 Python 依赖。从本仓库根运行：

```bash
python3 -m workflows.harness.install --repo . --workspace <目标项目目录>
```

安装器仅写目标项目 `.codex/`，不修改全局配置。按宿主原生机制信任项目及审查 Hook，然后重开目标项目会话。项目内的 `exploration-lab` MCP 名称、工具前缀和状态目录暂时保留兼容；仓库改名不自动迁移旧安装路径。

给 Codex 明确目标、真实验收命令及有限预算。工具协议由 [迭代工作流](workflows/harness/WORKFLOW.md)维护。验证命令是具有宿主权限的可信本地代码。

```bash
python3 -m unittest discover -v
```

## 首个业务案例：语言学习闭环 → Swift

以 Duolingo 网页版为行为观察参考，使用原创题库、素材与产品名称建立 Swift 教育软件基座。目标是课程路径、选择与拼句题、答题反馈、错题重练、课程结算及持久进度。Duolingo 规则只有在实际观察后才能标记为已确认；为了基座自定的规则必须标为产品决策。

首轮以 macOS 可运行的 SwiftUI 客户端和可测试 Swift 核心为交付，保持核心可供后续 iOS 使用；不要求首轮实现登录、订阅、排行、语音识别或完整课程库。浏览器与原生 UI 的验收通过共同业务场景适配，不能宣称同一浏览器脚本直接运行原生 UI。具体任务验收以当前运行 Goal 为准。[案例入口](projects/duolingo-web/README.md)提供实际观察、原版可行性结果及复现命令。

## 研究来源

原项目的 Dream-RSI 与 Cordis 研究是本项目的方法来源，不因聚焦 App 重建而删除。Dream-RSI 启发对探索策略和历史反馈的显式建模；Cordis 启发组件职责、依赖和生命周期管理。当前实现不是两篇论文的完整复现。原论文、历史实验与现有对应关系见 [研究来源](docs/RESEARCH.md)。

## 阅读入口

- [项目哲学](docs/PHILOSOPHY.md)：为何使用可执行业务规格。
- [代理约束](AGENTS.md)：证据、验收、实验和交付纪律。
- [架构](docs/ARCHITECTURE.md)：所有者、数据流与实际边界。
- [路线图](docs/ROADMAP.md)：分阶段完成条件。
- [本轮机制实验与原生续跑](projects/rebuild-mechanisms/REPORT.md)：固定36项检查，另有真实宿主 smoke。
- [历史机制消融](projects/ablation/REPORT.md)：只能说明机制检查结果。
