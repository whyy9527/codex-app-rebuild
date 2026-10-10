# 架构

## 当前运行结构

Codex 使用原生工具观察和修改；MCP 提供七个任务操作；短 Hook 在 SessionStart 提供协议、Stop 检查是否继续、UserPromptSubmit 捕获显式暂停。Hook 不执行长验收，不启动模型。

| 所有者 | 职责 |
| --- | --- |
| `capabilities/exploration/harness.py` | 任务状态、预算、尝试、验收冻结、暂停与会话作用域 |
| `capabilities/exploration/storage.py` | 原子 JSON 与摘要 |
| `runtime/runner.py` | 真实命令、输出、超时与进程组清理 |
| `runtime/harness_mcp.py` | 工具协议和反馈投影 |
| `runtime/harness_hooks.py` | 宿主生命周期短适配 |
| `workflows/harness/install.py` | 显式目标项目注册，保留既有配置 |
| `runtime/codex_host.py` / diagnose | 原生宿主诊断，非在线循环依赖 |

现有状态：ready → working → verifying → complete；失败返回 ready 或进入 blocked / budget_exhausted；用户可暂停并显式恢复。锁协调 MCP 和 Hook。新会话不自动激活其他会话任务。

Stop 去重绑定会话、原生 turn ID 和实际尝试/验收/阶段检查点。同一检查点的重复通知不继续，已有新进展可在同一原生 turn 内再次继续；没有进展或超出预算则停止。真实多阶段宿主试跑发现并修复了旧版按整个 turn 去重的问题，失败记录与实际复验见 `projects/model-pipeline`；修正后同一原生 turn 多次续跑及完成后停止已有实际宿主证据。

## 重建结构与当前范围

`capabilities/rebuild/contracts.py` 已拥有行为 ID、前置状态、动作、期望与证据清单，分离 unknown/observed/decision 和 not_run/pass/fail/invalid/unavailable/timeout。它对两端动作适配器执行统一断言，检查 start/reset/scenario/reset/stop，并在输入与源码变化后拒绝旧结果。参考端通过后才能冻结；增量批次必须关联真实父批次并保留旧场景。

`workflows/rebuild/cli.py` 提供 check、verify、freeze、coverage。回执不覆盖，记录规格/源码/输入摘要、实际观察和差异。目标 layer 显式区分 browser_ui/native_ui/core/test_double；协议不是 UI 证据认证。替身检查验证机制；Duolingo 案例另有真实线上浏览器和 Swift 原生 AX UI 的共享场景实测，不能由协议格式推导任意适配器都提供了真实 UI 证据。详细契约见 [业务规格](BEHAVIOR-CONTRACT.md)。

运行任务应引用固定规格，不能把任务历史当作产品覆盖率。`capabilities/rebuild/pipeline.py` 已保存 explore→specify→reference→freeze→implement→discover→reference→freeze→implement→review 的阶段证据与回执。当前 Codex 依据 next_action 工作，step 校验阶段，不生成伪观察或另起模型。Harness 拥有模型尝试，Pipeline 拥有阶段推进及额外阶段次数/时间上限；两者不复制同一状态。原生 Stop 驱动的单任务模型 fail→pass 续跑已验证（见 `projects/rebuild-mechanisms/REPORT.md`）；一次多阶段真实宿主流程已完成：初始原版4/4→冻结→新会话接续→初始原生4/4→补充观察模板及审计→扩展原版12/12→冻结→模型扩展旧 Swift→原生12/12→复核→最终停止。模板可见，不证明自主发现未知行为；四组真实业务消融已执行，均12/12及可执行留出2/2、另1未知；N=1未观察到通过率收益，见 [业务报告](../projects/business-ablation/REPORT.md)。

重建工作流编排观察、原版验收、批次冻结、新版实现、差异修复与补充探索。运行时只执行显式命令，不推断规则。`exploration_adopt` 允许用户明确选择暂停任务转交新会话，不自动恢复、不重置预算；旧指针失效，忙碌目标会话和异工作目录被拒绝。正在执行的验收必须结束后才能转交；暂停期间取得的成功结果在显式恢复时正确完成，无须额外消耗尝试。

已实现 `acceptance_paths`：按显式文件/目录冻结验收及夹具，不限语言；默认包括 tests、Tests、e2e 和常见包/Playwright 配置。清单检测新增、删除和修改；拒绝越界路径。已实现 `verify_seconds`，受总截止时间约束；旧任务仍按原冻结契约验证。动态依赖必须明确声明，不能承诺自动捕获所有依赖。业务层拒绝空行为清单；verify 和 freeze 也拒绝没有可执行已知场景的通过。通用命令层另有 unittest 空发现保护。

## Swift 教育案例边界

课程和题库是内容数据；学习引擎拥有题目队列、答题反馈、错题重练和结算；进度仓库负责保存和恢复；SwiftUI 负责展示与输入。业务核心可以独立测试，并通过场景适配器与浏览器观察的语义对应。当前 `projects/education-swift` 将 LearningCore、SwiftUI 客户端和可执行核心检查分开；`projects/duolingo-web` 拥有线上浏览器与原生 AX 驱动及共享规格。v2 已在原版和原生 UI 两侧通过12条共享场景。LearningCore 拥有 Codable 课程/课时、三题型状态机、错题队列及进度；LearningModel 处理 UI 操作与保存；LearningView 展示主页侧导航、课程路径、统计卡片与固定底部练习反馈；LearningAudio 使用 AVAudioPlayer 播放原创合成WAV、AVSpeechSynthesizer 朗读指令。LearningModel 统一选择/配对/拼句动作及声音触发，配对自动完成也走同一反馈路径。静音偏好保存于进度文件旁的 `.audio.json`，不修改旧业务进度格式；静音立即停止音效和朗读。导航占位服务明确说明未连接，不能伪造联网排行或账户。构建包装器先编译当前源码，再驱动自有 PID 的窗口，记录源码与二进制摘要。实际结果见该案例 evidence；另有实际模型从旧版 Swift 扩展到12/12的可行性记录；四组业务对照已完成且没有通过率差异，不据此宣称机制提升。

测试分别报告核心业务、原生客户端交互、视觉相似性、音频和入口覆盖；AudioChecks 验证实际生成器/播放器的解码、时间推进、静音和恢复，仅证明播放传输，不证明声卡输出可闻。适配器只是桥梁，不能用核心测试通过代替 UI 通过。平台构建和实际交互分别提供证据。

## 已知限制

默认单次验收时长 30 秒，可显式设置；验收保护只覆盖声明的输入。源码完整性检查记录常见代码文件，运行数据不自动视为源码。业务批次 deadline 阻止新的动作；到期后保留最多5秒的 stop 清理额度。验证进程崩溃恢复和 UI 中断完整覆盖仍未验证；多阶段模型重建仅有一次修正后的可行性证据。可信验证命令具有宿主权限。

仓库重命名保留 `exploration_*` 工具、`exploration-lab` 服务名和状态目录兼容。旧目标项目安装器启动路径需显式重装后更新，不自动修改其他项目。

## 研究关系

历史策略池、回放和组件库已从运行链移除，当前不是 Dream-RSI/Cordis 复现。研究机制、历史证据与恢复位置由 [RESEARCH.md](RESEARCH.md)维护。

产品检查另用自有子进程AX驱动，隔离进度，不改变冻结v2断言。音频输出检查使用ScreenCaptureKit的自有PID过滤、关闭麦克风，录音开始后驱动真实控件并记录时间戳；非零输出和静音零输出分别判断。数字输出证据与物理扬声器听感分开。ChoiceIllustration只按选项文本呈现原创插画，SeedMascot只负责展示，不读取正确答案。详见[产品复验](../projects/duolingo-web/evidence/PRODUCT-V3-REVIEW.md)。

最终产品修正增加导航卡片与真实课程入口、拼句角色/发音提示与答案横线；没有改变Foundation学习状态或持久化格式。UI35项、核心5项、冻结原生12项与7段系统输出录音分别验证，实际参考对照见[产品交付](../projects/duolingo-web/evidence/PRODUCT-V3-DELIVERY.md)。此前AudioChecks的“只证明传输”仍指该单项检查；新ScreenCaptureKit回执另证明应用数字音频输出。

## 当前架构缺口：探索和前端模具

现有 Pipeline 的 discover 只要求六类证据和至少一个新行为，之后 review 能结束该业务批次。这是阶段编排，不是探索充分性判断，也不是产品完成。现有共享断言主要检查状态字段，未检查题库、文案、图形、字体、布局和音色；独立 UI35 项亦明确未证明原版视觉一致。历史 v3 完成声明因此撤回。

修正方向是让真实探索历史保存状态→动作→结果→新增需求及未访问分支，利用反馈调整行动选择；需求模具同时拥有业务与前端断言。浏览器/Swift 驱动只采集实际结果，共同断言判定差异。保留原始截图并显式处理窗口装饰和像素比例，同状态同内容同视口才比较视觉；无法对齐的历史截图是不可比较，不能算通过。研究来源和历史负结果继续由 RESEARCH.md 维护。


### 当前 v4 数据与前端链

原版逐题观察（含失败）→ `compile-observed-course.py` → 西语夹具 → `LearningCore`/SwiftUI → 自有子进程 AX 采集 → 共享前端契约。当前包括两节实测课24题；第三节与后续课题仍进入探索。`Course.pathNodes` 单独描述节点包含的课时，避免把课程层级误当成页面节点。

`ReferenceStyle` 从 SwiftPM Bundle 加载实际资源并注册字体；主页与题图使用源自原版 DOM/CSS 的图形，资源摘要由产品入口独立冻结。`measure-visual.py` 按真实窗口 contentLayoutRect 和 backingScale 去除窗口装饰、归一化 Retina 采样，不对齐产品内容、不掩盖差异，输出诊断而非视觉通过。文字、悬停、视觉和音频分别判定。144项题目文案通过仍不能解除视觉和声音失败。

`discovery` 目前只从实际历史产生未访问优先队列；新增的未知短语→反馈→参考确认记录为后续策略实验提供真实样本，还没有执行策略自改进或证明 RSI 收益。研究关系继续见 RESEARCH.md。


### 偏好与参考驱动

`LearningPreferences`独立于学习进度保存；原有全局静音与参考Sound effects分离，避免关闭音效同时错误阻断语音。`ReferenceSettings`呈现实际偏好控件；原生AX驱动操作、关闭并重开自有进程，再读取实际值。共享比较器支持内容坐标中的控件矩形，不把四个矩形通过提升为整页视觉通过。

原版驱动`observe-reference-preferences.mjs`从显式拥有的Playwright CLI会话读取相同控件，记录对应保存确认和刷新结果。Motivational messages使用另一条偏好接口；请求200与最终UI状态仍有反例。`verify-product.py`同时比较最新原版事实和候选，并冻结代码、资源、夹具、前端契约及其引用证据的摘要；原版契约自身失败不能被候选通过遮盖。

参考词汇由实际正向反馈提取，跨课驱动保留运行时知识快照、未知题面和反馈；当前词汇记忆复用不等于探索策略RSI。后续应直接观察原版课程数据结构与交互类型，减少将逐词解题当作产品探索。
