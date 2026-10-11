# 研究来源与实现边界

独立访客档案已接Swift页脚导航、原版素材、引导关闭和成就404；首轮顶层路由落错旧renderer的失败已保留并修复。v57保留3846旧项增9，最终4状态93pass/10fail/94unavailable，3整图仍fail；同二进制排行榜回归87pass/15fail。头像/邀请交互与动态经验累计仍缺，下一批先补这些入口；不宣称1:1或RSI收益。[证据及复跑](../projects/duolingo-web/evidence/english-profile-native-v1/README.md)。

按历史frontier实际进入排行榜访客档案，发现独立档案、头像引导、成就404、邀请浮层及15肤色radio编辑器；修复采集器漏读aria-checked。v56保留3188旧项追加658，源649pass/9pending；候选新增全not_run，本批未实现Swift新页。下一批先接档案布局/导航与已观察交互，继续头像保存/返回和声音；无新RSI收益宣称。[证据及复跑](../projects/duolingo-web/evidence/english-profile-frontier-v1/README.md)。

原版探索确认状态底色、悬停、双徽章和段落内边距遗漏，v55保留3084旧项追加104。最终两状态87pass/15fail，整图仍失败；同一二进制5个重启状态及10个主页分支完成。保留字体猜测被否定、图片溢出和内边距差异略增的负结果；下一步优先未访问个人档案/主页分支及声音，未宣称1:1或RSI因果收益。[证据与复跑](../projects/duolingo-web/evidence/english-leaderboard-visual-v1/README.md)。

历史题目差异引导本批重访排行榜练习，真实取得16评分题、暂缓口语及17卡回顾；截图反馈再发现六个漏编译的暂缓入口。初始右列别名错误纠正产生的分数变化不计作产品改善或RSI收益。实际模型匹配预算消融未执行，原论文及负结果继续保留。[证据](../projects/duolingo-web/evidence/english-leaderboard-practice-instance-v1/README.md)。

本批由历史反馈选择排行榜状态与练习入口，实际发现角色清单漏掉的清除控件和当前选题差异，已转成可失败契约。它是探索闭环的一次实际产出，不是 RSI 因果收益；独立模型与匹配预算对照未执行。三个源音频配置零输出与原生阳性对照保留负结果，根因未知。[本批证据](../projects/duolingo-web/evidence/english-leaderboard-state-v1/README.md)。

核对日期：2026-10-10。两篇原始研究均来自仓库历史提交 `2ad5175` 的引用；本次重新检查论文页与官方仓库。

## Dream-RSI

[Dream-RSI: Recursive Self-Improvement through Evolving Worlds](https://arxiv.org/abs/2609.14858v2)，Tong Zheng 等，2026，v2 为 2026-10-06。[官方仓库](https://github.com/zhengkid/Dream-RSI)。

论文用历史发现树构造回放环境，在不重复昂贵在线发现的情况下评价和改进探索策略，再部署策略收集更多历史。它启发本项目保存真实反馈并显式区分探索策略和产品实现。

重建初期只保留有界任务循环；后续有限历史回放与真实模型策略实验见下文，仍无完整历史树模拟器与论文级策略自改进，不能称为完整 Dream-RSI 实现。App 重建中的行为证据可为未来探索策略研究提供输入，下一步需用真实探索历史验证策略调整能否改善需求发现，而不是把探索研究排除出产品工作。官方仓库核对时仍说明完整代码与复现脚本准备发布；论文已公开，发布计划表的 arXiv 条目存在滞后，不据此断言论文未发布。

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

真实分支消融02已产出模型策略、历史回放反馈和在线部署证据，补上“尚无策略生成/历史回放执行”的阶段缺口，但不是完整论文复现。一次修订后实验组仍选初始策略，离线两组同分；在线同动作却采到不同加载阶段，比较不可判定，不能证明探索或复刻质量收益。见[实测报告](../projects/exploration-ablation/REPORT.md)。下一批修采样、重新注册，产品质量对照仍待执行；不将原始前端事实数当独立需求数量。

主页旅程批次将旧内容事实计数偏好和实际未接入前端的失败反馈用于当前Codex策略选择，事前保存候选后部署四条源入口，再用候选失败修外层路由，并继续发现已完成节点的传奇/练习和错误配对原音。动作→旅程→前端结果已有实际消费者；这是当前主会话的反馈引导探索，不是独立worker、盲留出或完整论文复现。新增控件状态数不是独立功能数，暂无因果RSI收益。[策略、在线事实与限制](../projects/duolingo-web/evidence/english-home-journey-v1/exploration-feedback.json)。

完成节点／传奇／排行榜这批由上一轮缺失消费者和未建模动作反馈选择，实际新发现含独立传奇页、建档后返回差异与排行榜状态选择。冻结模具后原生负基线失败，再实施并真实验证；这是探索对实现的反馈证据，不是RSI机制消融或因果收益。152项断言不等于152项业务发现，成本token／费用未知。[原始证据](../projects/duolingo-web/evidence/english-home-branches-v1/README.md)。
