# 方法来源与实现对应

本页记录原论文、借鉴的方法与实际实现的对应关系。日常复刻按 [Workflow](../workflows/rebuild/WORKFLOW.md)执行；历史研究记录保留在文末。

本仓库的 RSI 探索闭环由 Codex 执行：读取历史与差异，修订探索方法，实际执行探针，将发现接入 E2E，再根据结果选择下一步。论文复现范围与工作流的运行能力分别说明。

## Dream-RSI

[Dream-RSI: Recursive Self-Improvement through Evolving Worlds](https://arxiv.org/abs/2609.14858v2)，Tong Zheng 等，2026。[官方仓库](https://github.com/zhengkid/Dream-RSI)。

原研究将历史发现树构造成回放模拟器，利用已记录结果评价和改进探索策略，再部署策略收集更多历史。本项目借鉴让探索方法本身成为改进对象的思路，具体用于发现模具遗漏和改变观察方法。

| 已有实现 | 实际职责 |
| --- | --- |
| [Workflow](../workflows/rebuild/WORKFLOW.md) | Codex 根据历史、反例和候选差异修订探针，执行后消费反馈 |
| [探索前沿](../capabilities/rebuild/discovery.py) | 从真实记录列出尚未完成的状态／动作／输入方式；不自行优化策略 |
| [历史回放](../projects/exploration-ablation/replay.py) | 在已采集的单层分支上评价候选策略 |
| [策略部署](../projects/exploration-ablation/REPORT05-06.md) | 模型利用真实反馈修订策略，再实际操作原版，将发现交给模具与 Swift |

论文复现状态：多层历史树模拟器、可复用模拟器池及论文级离策略优化闭环尚未完整实现。当前默认流程由 Codex 决策并执行探索，没有自动调用历史实验脚本。

## Cordis

[A Programming Paradigm for Spatiotemporal Composability](https://arxiv.org/abs/2608.25512v1)，Yifan Shi、Wei Zhang、Tianyi Cui，2026。[实现](https://github.com/cordiverse/cordis)。

原研究以可撤销副作用和响应式依赖管理实现动态组件的空间／时间组合。它为本仓库的职责分离与资源生命周期提供设计参考：能力、宿主运行时和工作流各有所有者；[命令运行器](../runtime/runner.py)负责自己启动的进程组清理，具体职责见 [架构](ARCHITECTURE.md)。

当前借鉴停留在设计层。运行链没有导入 Cordis，也没有实现其 context、可撤销副作用或响应式依赖机制；普通模块分层和进程清理不能称为 Cordis 核心机制的复现。

## 实践与历史实验

| 记录 | 保留的事实与用途 |
| --- | --- |
| [Duolingo 经验](DUOLINGO-LESSONS.md) | 真实遗漏、策略／观察方法调整，以及模具和实现如何消费发现；直接用于改进 repo |
| [真实策略部署05／06](../projects/exploration-ablation/REPORT05-06.md) | 真实模型利用反馈改变探索动作，实际发现页面内容并进入共同契约和 Swift |
| [探索04](../projects/exploration-ablation/REPORT04.md) | 两组语义代理新增0／0；后续焦点探针揭示该指标漏掉前端要求 |
| [探索02／03](../projects/exploration-ablation/REPORT.md) | 实际策略与部署记录；起点／采样问题使比较不可判定 |
| [前端反馈质量消融](../projects/frontend-quality-ablation/REPORT.md) | 两组40／40，图像仍不同，有反馈组没有额外改善；揭示控件指标饱和和样本拟合问题 |
| [业务四组消融](../projects/business-ablation/REPORT.md) | 已有共享业务场景结果无通过率差异；保留成本、失败和限制 |
| [模型多阶段接续](../projects/model-pipeline/README.md) | 旧 Hook/Pipeline 的实际宿主执行与恢复证据，供兼容模式参考 |

这些历史结果保持原结论。当前流程先完成复刻和完整验收，消融留到完成后的优化阶段，比较机制对质量、成本和耗时的影响；顺序由 [Workflow](../workflows/rebuild/WORKFLOW.md)维护。默认复刻 Goal 依据用户体验与模具验收完成。

更早的源码与原始研究报告保存在提交 `2ad5175`：

```sh
git show 2ad5175:projects/paper-v2/REPORT.md
git show 2ad5175:projects/paper-v3/REPORT.md
git show 2ad5175:projects/self-improvement/REPORT.md
```

旧报告中的24实例无算法收益与模型预检失败继续保留。整理前的详细研究记录及批次说明可从 [历史索引](history/README.md)查找，不把旧命令冒充当前运行接口。
