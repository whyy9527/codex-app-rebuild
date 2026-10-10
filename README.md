# Codex App Rebuild

**当前状态：1:1 复刻未完成；当前目标按用户建议转为英语学习，默认中文母语 → 英语。** v3 的35项UI检查、12条共享业务场景和音频输出只证明各自检查的子集，没有验证原版前端需求；“产品修正已通过验收”撤回。当前差异包含课程、素材、字体、布局、菜单交互及音色，当前已加入基于实际 NSWindow 几何的采样归一化，尚未证明视觉一致。[历史回执](projects/duolingo-web/evidence/PRODUCT-V3-DELIVERY.md)保留为局部证据。

探索原产品，把用户可观察的业务与前端需求变成可独立运行的代码化模具，用历史反馈改进探索，再让 Codex 重建 App。仓库保持私有；改名不代表开源或发布。

当前默认夹具为 `fixture-reference-en-zh-v10.json`：七课102道评分题，保留实际口语暂缓、听力暂缓、插入/替换题、独立输入偏好、跳过重练及结算路径。第七课15题与三页结算已原生走通，后续课程继续探索；不会把学完已编译课程标成整课程完成。

前端契约v19保留全部旧要求，共1638项。发音页及练习入口已接原生实现；实际52状态覆盖听辨、相同/不同、口语暂缓、配对、四错更正、稍后建档、返回和未答退出，新增练习44项通过、5项待验证。三组整图仍不同，正常口语、音标进度持久化、结算统计和声音等价未完成。见[最新证据与复跑](projects/duolingo-web/evidence/english-pronunciation-practice-v1/README.md)。[第七课旧构建回放](projects/duolingo-web/evidence/english-radio-feedback-v1/README.md)独立保留，未将其通过结果转移到当前构建。

Bea/Lucy、Falstaff和正确Lin的源Rive已绑定；更多角色、气泡、主页引导、radio1声音和生命刷新仍未对齐。不能用核心通过、控件几何通过或源语音文件已下载宣称1:1完成。原始RSI论文、机制实验及无收益结果见[研究来源](docs/RESEARCH.md)，新的真实探索策略消融仍待执行。

历史探针和旧版本均保留：见[Roadmap](docs/ROADMAP.md)、[反馈分支](projects/duolingo-web/evidence/english-feedback-actions-v1/README.md)、[六课连续回放](projects/duolingo-web/evidence/english-sixth-native-v1/README.md)、[第七课源观察](projects/duolingo-web/evidence/english-seventh-v1/README.md)和[跳过探针](projects/duolingo-web/evidence/english-skip-native-v1/README.md)。组件结果不相加冒充整体验收。

## 方法

观察原版 → 保存行为与证据 → 在原版验证验收 → 冻结本批规格 → 实现新版并按失败反馈迭代 → 独立验收与补充探索。

测试重新计算完成状态，文档保存决策与未知。通过现有测试不代表产品完整；未探索、不可用、失败和通过必须分开。探索新增行为后建立下一批规格，不能在实现期间降低当前验收标准。

Swift的21项核心检查覆盖实际课程轨迹、错误与暂缓、重练、输入偏好和进度。原生驱动另行操作窗口并保存控件、截图、失败及实际状态；它们不能互相替代。具体构建、启动和重置入口见[Swift基座](projects/education-swift/README.md)。

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

目标是 Duolingo 网页版到 Swift 的 1:1 复刻，之后作为教育软件基座。原版的内容、页面、素材、声音和交互都是待发现和验证的需求，不自行换成原创内容或将未知服务永久划出范围。现有 LingoSeed 是可复用的工程底座，尚不是合格的复刻交付。

原版与原生平台通过共同需求和各自驱动验收；相同动作语义不能代替相同前端结果。现有 macOS 构建和测试保留作回归。当前原生 Goal 管理本轮目标，[案例入口](projects/duolingo-web/README.md)保存观察和复跑命令。

## 研究来源

原项目的 Dream-RSI 与 Cordis 研究是本项目的方法来源，不因聚焦 App 重建而删除。Dream-RSI 启发对探索策略和历史反馈的显式建模；Cordis 启发组件职责、依赖和生命周期管理。当前实现不是两篇论文的完整复现。原论文、历史实验与现有对应关系见 [研究来源](docs/RESEARCH.md)。

## 阅读入口

- [项目哲学](docs/PHILOSOPHY.md)：为何使用可执行业务规格。
- [代理约束](AGENTS.md)：证据、验收、实验和交付纪律。
- [架构](docs/ARCHITECTURE.md)：所有者、数据流与实际边界。
- [路线图](docs/ROADMAP.md)：分阶段完成条件。
- [本轮机制实验与原生续跑](projects/rebuild-mechanisms/REPORT.md)：固定36项检查，另有真实宿主 smoke。
- [历史机制消融](projects/ablation/REPORT.md)：只能说明机制检查结果。


上一探索检查点实际完成原版英语第三课，发现重复词块及同题型动态换题；当时候选仍为前两课，v4为128通过、244未覆盖。此历史结果保留，最新候选见上文。[第三课探索与下一步](projects/duolingo-web/evidence/english-third-v1/README.md)。

上一构建默认七课同次实际回放430状态；前端1489项为985通过、69失败、435未覆盖。38对截图全部有差异，实际声音等价尚未证明；[完整回执及保留失败](projects/duolingo-web/evidence/english-seventh-native-v1/README.md)。
