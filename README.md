# Codex App Rebuild

用 AI 重建复杂 App 的实践仓库。核心是持续探索原版，把发现转成能独立运行的模具，再用相同业务和前端要求验证另一种语言的实现。测试负责重建已覆盖行为的状态；探索负责寻找测试还不知道的需求。

当前案例为 Duolingo 网页版 → Swift，中文母语学习英语，随后沉淀教育软件基座。**当前尚未达到 1:1**；页面、交互、字体、动画、声音和进度恢复都属于目标，不能用核心测试通过替代。阶段进展及未完成项统一见 [Roadmap](docs/ROADMAP.md)。

## 工作方式

原版探索 → 保存状态、动作和证据 → 冻结共同业务／前端契约 → Swift 实现 → 实际 UI、像素与音频验证 → 用失败和未知调整下一轮探索。

- 模具包含原版启动／数据准备／重置边界、共同状态夹具、平台驱动、业务断言及前端要求。
- 每条要求区分 pass、fail、not_run 和 unavailable；未观察结果继续保持 unknown，不能算通过。
- 同一按钮的悬停、点击和键盘操作分别探索。已知截图前后状态变化的证据不能作为同状态图像验收；截图缩放使用独立实测数据。
- 原版内容和原素材是需求来源。未接入页面或声音是待完成工作，不自行换成原创内容或永久缩小范围。

[项目哲学](docs/PHILOSOPHY.md)解释这些选择；[架构](docs/ARCHITECTURE.md)说明所有者和数据流；[AGENTS](AGENTS.md)指导后续代理接续。用户对话及原生 Goal 管理任务，不另建 Goal 文件。

## 运行 Swift 案例

需要 macOS 与 Swift 工具链。从仓库根运行：

```sh
swift build --package-path projects/education-swift --product LingoSeed
projects/education-swift/.build/debug/LingoSeed --fixture projects/duolingo-web/fixture-reference-en-zh-v14.json --progress artifacts/lingoseed-english-demo/progress.json
swift run --package-path projects/education-swift LearningCoreChecks
```

使用尚不存在的 progress 路径建立独立初态。已探索的阶段／课程进度使用对应证据目录中的准备夹具；不能把新访客初态冒充课后状态。详细启动、进度隔离和复跑见 [Swift 基座](projects/education-swift/README.md)与 [Duolingo 案例](projects/duolingo-web/README.md)。

当前共同前端规格为 [v76](projects/duolingo-web/frontend-english-v76.json)。[主页下游证据](projects/duolingo-web/evidence/english-home-stat-branches-v1/README.md)覆盖真实目录、透明输入控件、补心持久化及Super返回链；[主页顶部交互证据](projects/duolingo-web/evidence/english-home-stats-v1/README.md)连接原版发现、输入模式、Swift 鼠标／键盘操作及严格失败；[实际声音证据](projects/duolingo-web/evidence/english-pronunciation-current-v1/README.md)区分原资源输出与尚未证明的浏览器声学等价。

## 迭代工具与验证

循环核心使用 Python 3.11+、POSIX 与 Codex CLI；图像比较等案例能力另有按需依赖。安装器只写显式目标项目，不修改全局配置：

```sh
python3 -m workflows.harness.install --repo . --workspace <目标项目目录>
python3 -m unittest discover -v
```

七个 MCP 操作、短生命周期 Hook、持久任务／阶段、真实命令验收及预算控制为代理提供执行反馈。Codex 负责判断和编辑，Hook 不启动长验收或模型。协议见 [迭代工作流](workflows/harness/WORKFLOW.md)；重建流程见 [工作流](workflows/rebuild/WORKFLOW.md)和 [业务契约](docs/BEHAVIOR-CONTRACT.md)。机制可运行不代表复刻或探索收益已经成立。

## RSI 与实验

保留 Dream-RSI 的探索策略／历史反馈研究，以及 Cordis 的组件职责／依赖／生命周期研究；原论文和已有机制对应关系见 [研究来源](docs/RESEARCH.md)。当前不是两篇论文的完整复现。

[真实探索消融04](projects/exploration-ablation/REPORT04.md)执行了真实模型生成、回放反馈与在线部署，两组语义代理新增均0，未观察到收益；后续产品探针发现该指标漏掉焦点行为。旧不可判定及负面结果保留。机制检查、探索代理分数、实际业务通过和产品视觉／声音质量分别报告，不用其中一项代替另一项。

历史复盘见 [交付审计](docs/DELIVERY-AUDIT.md)、[模型流程](projects/model-pipeline/README.md)、[业务四组消融](projects/business-ablation/REPORT.md)及 [旧 README 检查点](docs/history/README-checkpoints-2026-10-12.md)。本仓库保持私有，公开发布另行决定。
