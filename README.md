# Codex Exploration Lab

面向 Codex 的可审计探索工具与工作流。借鉴 Dream-RSI 的探索策略与历史回放，以及 Cordis 的组件依赖与生命周期管理。

**当前状态：设计骨架。尚无可运行探索引擎、Codex 插件、hook 或视听评审器；没有验证自动提升效果，不构成论文复现。**

## 要解决的问题

反复生成版本却没有改进时，系统应保存真实候选、反馈和成本，区分继续修复与更换方向，并在历史记录和新任务上检验探索策略。

首个应用场景是视频参考分析与包装方案探索。学习参考片与生成剪辑候选是两个阶段；观察遍数、技术检查通过和审美改进不能互相替代。

## 入口

- [架构与边界](docs/ARCHITECTURE.md)
- [分阶段实现与验收](docs/ROADMAP.md)
- [协作规则](AGENTS.md)

## 来源

- [Dream-RSI: Recursive Self-Improvement through Evolving Worlds](https://arxiv.org/abs/2609.14858)
- [Dream-RSI 官方仓库](https://github.com/zhengkid/Dream-RSI)：截至 2026-10-07，完整代码仍标注准备发布。
- [A Programming Paradigm for Spatiotemporal Composability](https://arxiv.org/abs/2608.25512)
- [Cordis](https://github.com/cordiverse/cordis)
- [DeepSeek Harness 的 Cordis 入门](https://deepseek-harness.github.io/deepseek-harness/reference/cordis-primer)

本项目独立设计，不隶属于上述项目。默认保持私有；不包含原始视频、声音、身份素材、模型权重或密钥。
