# 研究来源与实现边界

核对日期：2026-10-10。两篇原始研究均来自仓库历史提交 `2ad5175` 的引用；本次重新检查论文页与官方仓库。

## Dream-RSI

[Dream-RSI: Recursive Self-Improvement through Evolving Worlds](https://arxiv.org/abs/2609.14858v2)，Tong Zheng 等，2026，v2 为 2026-10-06。[官方仓库](https://github.com/zhengkid/Dream-RSI)。

论文用历史发现树构造回放环境，在不重复昂贵在线发现的情况下评价和改进探索策略，再部署策略收集更多历史。它启发本项目保存真实反馈并显式区分探索策略和产品实现。

当前只保留有界任务循环，没有历史树模拟器、离策略选择或策略自改进；不能称为完整 Dream-RSI 实现。App 重建中的行为证据可为未来探索策略研究提供输入，下一步需用真实探索历史验证策略调整能否改善需求发现，而不是把探索研究排除出产品工作。官方仓库核对时仍说明完整代码与复现脚本准备发布；论文已公开，发布计划表的 arXiv 条目存在滞后，不据此断言论文未发布。

## Cordis

[A Programming Paradigm for Spatiotemporal Composability](https://arxiv.org/abs/2608.25512v1)，Yifan Shi、Wei Zhang、Tianyi Cui，2026。[实现](https://github.com/cordiverse/cordis)。

论文关注动态组件的时间组合性和空间组合性，通过可逆效果与响应式依赖管理支撑组件生命周期。它是组合与生命周期研究，不应笼统叫第二篇 RSI 算法论文。对本项目的启发是职责、依赖与可管理资源的边界。

当前没有导入 Cordis，也没有保留历史小型组件库；不承诺论文的形式化保证，不能把进程清理等同于全部副作用可逆。

## 历史研究产物

历史源码和原始报告可从提交 `2ad5175` 查看：

```bash
git show 2ad5175:docs/ARCHITECTURE.md
git show 2ad5175:projects/paper-v2/REPORT.md
git show 2ad5175:projects/paper-v3/REPORT.md
git show 2ad5175:projects/self-improvement/REPORT.md
```

旧研究验证过候选记录、回放和池重选等机制。第三阶段报告在 24 个验证实例上没有观察到算法收益，独立模型预检失败；这些限制随研究来源保留，不因项目改名而省略。需要复用时先在隔离目录从旧提交恢复并核验，不将旧实验命令写成当前可运行接口。

现有 `projects/ablation/REPORT.md` 是固定机制检查的消融；新的真实业务对照已单独保存[预注册及四组报告](../projects/business-ablation/REPORT.md)，N=1未观察到通过率收益，费用仍未知。论文结果、历史机制结果与新的 App 重建结果分别报告。

本轮再次核对官方仓库，仍列 full codebase / reproduction scripts 为准备发布；不等待其开源才继续探索。[本轮探索历史](../projects/duolingo-web/evidence/exploration-v4/history.json)与待探索分支已成为实际消费者，但目前只支持未访问优先，尚无策略生成、历史树回放或在线收益证据。保持这个区别，避免把账本命名为 RSI。


第三课出现真实同类型换题和重复词块遗漏，已把失败、调整与续跑写入[实际探索历史](../projects/duolingo-web/evidence/english-third-v1/README.md)，供后续策略实验消费。当前调整由Codex依据现场选择，尚未实现Dream-RSI的历史树策略生成/离策略评估；身份回归和现场续跑不构成算法收益或真实探索消融结论。


新增[真实源App分支实验](../projects/exploration-ablation/PROTOCOL.md)：先实际采集四个具有相同根快照的英语主页分支，再用真实模型生成受限分支分配策略、历史反馈改进及封存后在线部署。现有旧账本多为单路径并有状态/动作歧义，不直接当无偏模拟器。模型运行和收益必须以正式回执为准；准备采集与机制测试不能称为RSI收益。
