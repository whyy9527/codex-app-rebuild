# Codex App Rebuild

注册年龄清除与密码显示/隐藏已按原版实际交互接入；另发现独立登录页含Apple与忘记密码，尚未实现。前端v45共2476项，最终两次20状态各116pass/31fail/2329not_run；整图仍失败，年龄图差异略增，不能称1:1。[最新证据与复跑](projects/duolingo-web/evidence/english-registration-controls-v1/README.md)。

默认v13补实际开箱前后主页、原素材及持久化记录，原生真实开箱和重启已验证；前端v41共2373项，本轨迹34pass/17fail/2322not_run，下一Practice开始/建档及排行榜遮罩仍未实施。[最新失败、探索与复跑](projects/duolingo-web/evidence/english-chest-v1/README.md)。

**当前状态：1:1 复刻未完成；当前目标按用户建议转为英语学习，默认中文母语 → 英语。** v3 的35项UI检查、12条共享业务场景和音频输出只证明各自检查的子集，没有验证原版前端需求；“产品修正已通过验收”撤回。当前差异包含课程、素材、字体、布局、菜单交互及音色，当前已加入基于实际 NSWindow 几何的采样归一化，尚未证明视觉一致。[历史回执](projects/duolingo-web/evidence/PRODUCT-V3-DELIVERY.md)保留为局部证据。

探索原产品，把用户可观察的业务与前端需求变成可独立运行的代码化模具，用历史反馈改进探索，再让 Codex 重建 App。仓库保持私有；改名不代表开源或发布。

当前默认夹具为 `fixture-reference-en-zh-v13.json`：八课115道评分题，保留前七课，补实际第八单元12题、口语暂缓、13卡回顾及后续结算和真实重启。仍未达到1:1：本轨迹前端133pass/17fail/2171not_run，结算图形、按钮及解锁宝箱等继续修复；不能把学完已编译课程标成整课程完成。[当前证据与复跑](projects/duolingo-web/evidence/english-eighth-integration-v1/README.md)。

特别任务页已从原版探索并替换英文占位内容，10文案/5几何通过；整图仍失败；独立练习入口随后接入，见下方新原生回执。[任务页、新发现与复跑](projects/duolingo-web/evidence/english-quests-v1/README.md)。

独立 `/practice` 已从实际16题轨迹编译为单独Swift课程，从任务页进入，走通口语暂缓、插入/替换、故意错误更正、结算、红心奖励及真正重启。主六课保持不变；原版资源已捆绑，采集到自有应用实际输出。共同v28仍有整图等失败，不算1:1完成；实际自适应选题及正常口语等继续探索。[原版轨迹](projects/duolingo-web/evidence/english-general-practice-v1/README.md)、[原生回执、失败与复跑](projects/duolingo-web/evidence/english-general-practice-native-v1/README.md)。

通用练习红心页已补原版图形与保留的底栏，普通听写改用Bea旁的白色分段播放和多行输入；v29原样保留旧要求并追加16项。最终完整回放通过，但共同前端仍89pass/55fail/1707not_run，整图全部有差异；错误共享布局的负结果保留。[展示修正、剩余差异和复跑](projects/duolingo-web/evidence/english-general-practice-presentation-v1/README.md)。

实际探索听力暂缓发现它会插入翻译并改变后续题单，不能沿初始API固定推进。源轨迹随后接入Swift替换状态机和真实原生回归，前端仍有失败；见[源反例](projects/duolingo-web/evidence/english-general-listening-decline-v1/README.md)及[实施验证](projects/duolingo-web/evidence/english-general-listening-decline-native-v1/README.md)。

驱动已支持读取当前实际显示题目并单步回放，用于暂缓后初始题单无法定位的插入题；实际接受后遇到未覆盖口语，保存未覆盖回执。Eddy原版Rive按源缓冲摘要导入，实际原生动画已出现，整图差异仍失败且部分略增。[当前题探索、资源及负结果](projects/duolingo-web/evidence/english-current-challenge-v1/README.md)。

默认通用夹具v3补原版听音填空token、绿色缺词反馈、气泡及分隔线，播放和两组选项几何精确通过；v32仍有整图失败和缺失的暂缓入口。[前端实测与探索反例](projects/duolingo-web/evidence/english-isolation-presentation-v1/README.md)。

当前题驱动新增显式多步预算，真实重练实例接受16题，并自动接续一次已观察引导页；口语仍需人工交接，未证明完整无监督或探索充分。实际成绩单发现17张卡（含暂缓口语），采集器补DIV角色；v33保留1912旧项新增111，候选新增全未运行。[续跑、成绩单漏采与下一实施批次](projects/duolingo-web/evidence/english-current-walk-v1/README.md)。

该17卡实例已编译共同夹具并接入Swift真实成绩历史、回顾展开/关闭/滚动，实际44状态完成；v34本批115项113pass/2整图fail。原生滚轮曾未移动仍退出0，现按实际几何验证387点位移；负结果保留。默认练习47状态及真正重启回归无驱动失败，但默认回顾仍待源规则与元数据，不能把显式实例当全产品完成。[实际原生回执、差异与复跑](projects/duolingo-web/evidence/english-result-review-native-v1/README.md)。

实际错误探索又确认成绩单保留首答coffee与改答hot两张卡；v35追加181项前端契约，Swift修红卡及浮层，48原生状态完成。新增176pass/5fail，三整图差异下降但仍fail，两红底采样经色彩转换仍差1级。旧17卡44状态回归完成，默认回顾及其它未知仍未补齐；完整Goal active。[原版证据、负结果与复跑](projects/duolingo-web/evidence/english-error-review-v1/README.md)。

按历史换入口后，等级复习实际发现完整句翻译新类型，驱动修正后12题接受并采到13卡及长浮层；仍没找到听音填空。Swift已实测修复Escape关闭，第一次无效方案保留。v37追加的13卡/长浮层88项尚未实现，不能用旧实例替代默认产品。[新路线、失败与下一步](projects/duolingo-web/evidence/english-home-frontier-v1/README.md)。

共同前端契约已接入真实PNG比较，缺图不可计为通过；发音卡片进一步按浏览器实际字体、字距、卡面和按下反馈修正，整图仍失败。[当前证据与复跑](projects/duolingo-web/evidence/english-pronunciation-typography-v1/README.md)。

前端契约保留旧要求并持续追加源观察；最新口语权限及发音退出分支已接入实际原生验证。反例探测区分全错直接退出与已获得正确进度后的确认，取消保持题目状态。几何、整图和声音仍有失败/未覆盖，正常录音评分与推进未完成。[最新证据、探索反例与复跑](projects/duolingo-web/evidence/english-practice-exit-v1/README.md)，逐批结果由[Roadmap](docs/ROADMAP.md)维护；不累计旧构建回执填当前未执行项。

Bea/Lucy、Falstaff和正确Lin的源Rive已绑定；更多角色、气泡、主页引导、radio1声音和生命刷新仍未对齐。不能用核心通过、控件几何通过或源语音文件已下载宣称1:1完成。原始RSI论文、机制实验及无收益结果见[研究来源](docs/RESEARCH.md)，已执行的[真实探索消融](projects/exploration-ablation/REPORT.md)和[前端质量消融](projects/frontend-quality-ablation/REPORT.md)保留不可归因和无额外收益结果，尚未证明RSI探索收益。

历史探针和旧版本均保留：见[Roadmap](docs/ROADMAP.md)、[反馈分支](projects/duolingo-web/evidence/english-feedback-actions-v1/README.md)、[六课连续回放](projects/duolingo-web/evidence/english-sixth-native-v1/README.md)、[第七课源观察](projects/duolingo-web/evidence/english-seventh-v1/README.md)和[跳过探针](projects/duolingo-web/evidence/english-skip-native-v1/README.md)。组件结果不相加冒充整体验收。

## 方法

观察原版 → 保存行为与证据 → 在原版验证验收 → 冻结本批规格 → 实现新版并按失败反馈迭代 → 独立验收与补充探索。

测试重新计算完成状态，文档保存决策与未知。通过现有测试不代表产品完整；未探索、不可用、失败和通过必须分开。探索新增行为后建立下一批规格，不能在实现期间降低当前验收标准。

Swift的27项核心检查覆盖实际课程轨迹、错误与暂缓、重练、输入偏好和进度。原生驱动另行操作窗口并保存控件、截图、失败及实际状态；它们不能互相替代。具体构建、启动和重置入口见[Swift基座](projects/education-swift/README.md)。

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


听力暂缓替换已接入Swift核心，并用显式观察实例从任务页走完45状态和真实重启；默认练习47状态回归也执行通过。v31保留旧要求增18项控件检查，最终新分支22pass/30fail，28整图全fail；仍未完成1:1或自适应实例选择。[实现、负结果与复跑](projects/duolingo-web/evidence/english-general-listening-decline-native-v1/README.md)。
