# Codex Exploration Lab

面向 Codex 的可审计探索工具。借鉴 Dream-RSI 的历史回放与探索策略选择，以及 Cordis 的组件依赖与生命周期管理。

**当前状态：可运行的 Python 标准库原型。** 已完成十轮工程修改，并实际运行十次「在线执行 → 冻结历史 → 策略比较 → 部署」闭环。没有付费模型接入、完整论文复现、Codex 插件安装或实际视听评审能力。

## 运行

需要 Python 3.11+、Git 和 POSIX 系统；已在 macOS / Python 3.14.3 验证。无需安装第三方 Python 包。从仓库根执行：

```bash
python3 -m unittest discover -v
python3 -m workflows.self_improve.cycle --out artifacts/my-policy-run --rounds 10
```

输出目录必须不存在。演示会实际生成并执行简单线性函数代码，回放已记录结果，写出策略代码和报告。生成器是确定性小程序，不是 LLM。

记录自己项目的实际验收命令：

```bash
python3 -m workflows.self_improve --root . --db artifacts/my-experiment.sqlite run \
  --id candidate-001 --round 1 --phase baseline \
  --hypothesis 'Verify the explicit acceptance command' \
  -- python3 -m unittest discover -v
python3 -m workflows.self_improve --db artifacts/my-experiment.sqlite verify
python3 -m workflows.self_improve --db artifacts/my-experiment.sqlite export \
  --out artifacts/my-receipts.json
```

失败、超时、执行器不可用或源码变化会产生非通过记录，CLI 返回非零。原始记录与源码快照保存在本地；导出投影会遮盖常见本地绝对路径并保留原记录摘要。导出并非秘密检测器，提交前仍需检查内容。

## 能力

- SQLite 持久化、父子关系验证、追加记录和完整性核验。
- 显式验收命令、进程组超时清理、源码快照与变化检测。
- 从父工作目录生成隔离候选，记录实际评价、调用次数和耗时。
- 冻结回放、前缀观察、root/leaf 动作、原子批次、预算及超出支持范围处理。
- 论文公式 (1) 的质量／调用成本目标、五个预算偏好、全部历史上的策略比较与原策略保留。
- 组件依赖启动、停用、恢复、逆序清理和启动失败回滚。
- 项目内 [Codex 使用 skill](.codex/skills/exploration-lab/SKILL.md)。

这些是可信本地 Python 适配器，**不是不可信代码沙箱**。命令评估器有超时；在线生成与策略函数须自行保证终止。未计量 token 与模型费用均为 null，不等于零。

## 已验证结果

十轮源码修改均保留了同一轮内不变的验收条件，修改前失败、修改后通过，源码哈希与对应 Git 提交匹配。不同轮验收规则不同，因此不计算整体质量提升百分比。

十次确定性策略闭环实际选择过一次新策略，后九次保持不变。总计 32 次生成器调用，包含最终的两次对照运行。在另一个目标参数的简单任务上，固定策略与选中策略最佳得分均为 1/3，调用数分别为 6 和 2。这是单个小任务的协议验证，不能外推到模型科研能力、视频质量或一般任务效率。

- [十轮复核报告](projects/self-improvement/REPORT.md)
- [机器可读汇总](projects/self-improvement/summary.json)
- [原型边界与论文差异](docs/ARCHITECTURE.md)
- [当前路线](docs/ROADMAP.md)
- [任务完成条件](GOAL.md)

## 来源

- [Dream-RSI 论文](https://arxiv.org/abs/2609.14858)与[官方仓库](https://github.com/zhengkid/Dream-RSI)：截至 2026-10-07，完整代码仍标注准备发布。
- [Cordis 论文](https://arxiv.org/abs/2608.25512)、[实现](https://github.com/cordiverse/cordis)及 [DSH 官方说明](https://deepseek-harness.github.io/deepseek-harness/reference/cordis-primer)。

本项目独立设计，默认保持私有，不包含用户媒体、模型权重或凭证。
