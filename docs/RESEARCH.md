# 研究来源与实践用途

RSI 是本仓库的探索工具：让 Codex 利用真实历史、失败与未知调整探索策略，把发现交给 E2E 模具，再据实际差异继续探索或实现。Duolingo 已提供这套流程的使用经验；不要求先开展新的消融或证明额外收益才改进仓库。

原论文、实践用途和历史实验各自保留。这里记录来源和边界，不追加课程批次。以下原引文沿用仓库此前核对记录，本次整理没有重新联网核查论文或上游发布状态。

## Dream-RSI

[Dream-RSI: Recursive Self-Improvement through Evolving Worlds](https://arxiv.org/abs/2609.14858v2)，Tong Zheng 等，2026。[官方仓库](https://github.com/zhengkid/Dream-RSI)。

原研究通过历史发现树构造回放环境，评价和改进探索策略，再部署策略收集更多历史。本项目借鉴“历史反馈→策略修订→实际探索→新历史”的关系，具体用于发现模具遗漏和改变观察方法。

当前 Codex 的反馈决策、frontier 工具与已有模型策略部署都是实际消费者；本仓库没有完整复现论文的历史树模拟器和算法。这个区别不妨碍把 RSI 用在复刻中，也不要求每次产品发现都做研究实验。

## Cordis

[A Programming Paradigm for Spatiotemporal Composability](https://arxiv.org/abs/2608.25512v1)，Yifan Shi、Wei Zhang、Tianyi Cui，2026。[实现](https://github.com/cordiverse/cordis)。

原研究讨论动态组件的空间／时间组合、依赖及生命周期。它启发本仓库区分能力、运行时与工作流职责，以及可管理资源的清理边界。它不是第二篇 RSI 算法论文，当前运行链也没有导入 Cordis。

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

这些结果不改写为正收益，也不再作为工程工作的待补前置条件。用户以后要求新的研究实验时再单独确定问题与协议；默认复刻 Goal 依据用户体验与模具验收完成。

更早的源码与原始研究报告保存在提交 `2ad5175`：

```sh
git show 2ad5175:projects/paper-v2/REPORT.md
git show 2ad5175:projects/paper-v3/REPORT.md
git show 2ad5175:projects/self-improvement/REPORT.md
```

旧报告中的24实例无算法收益与模型预检失败继续保留。整理前的详细研究记录及批次说明可从 [历史索引](history/README.md)查找，不把旧命令冒充当前运行接口。
