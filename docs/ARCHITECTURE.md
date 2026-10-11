# 架构

英语v6新增`DeferredSpeech`非评分状态与课末`reviewInterlude`，均由实际源轨迹编译；口语暂缓不能借用正确答案反馈推进。`compile-english-fifth.py`拥有第五轨迹及资源清单，`freeze-english-fifth.py`将源需求追加到共享前端v10；原生驱动实际操作五课、错误、重练与结算，同一观察分别计算全集与第五课子集，不能累计回执。录音识别和其他未实现分支继续明确记录。当前运行证据见[第五课原生验证](../projects/duolingo-web/evidence/english-fifth-native-v1/README.md)。

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

## 前端观察模具

`projects/duolingo-web/capture-visible-state.mjs`采集实际ARIA、控件状态/CSS/矩形，以及按钮外可见img/svg/canvas的资源身份、固有尺寸和布局；原始画布内容/动画与音频另行采集。CSS可见、资源存在、几何通过各自是局部证据，不推导像素或声音等价。输出在任何源动作前检查冲突，既有回执保持原样。

原生AX驱动按源场景操作自己的PID，并验证取消前后完整题目/控件状态、放弃不写完成进度、重新开始及真正终止重启。共享前端契约追加原版需求，旧断言保留；源探测与候选比较分别存档。源调用失败时继续读取同一页面，不能将等待预想弹窗超时直接判成原版不可用：先核实实际返回路径，再用正误等反例改变探索假设。具体批次状态归Roadmap，运行Goal仍拥有完成条件。

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


### 公开课程会话与实际UI交叉确认

`capture-reference-session.mjs`从显式拥有的CLI标签截取原版实际sessions响应，只保存白名单公开内容字段；`replay-reference-session.mjs`消费同一实例，保存实际词库/配对顺序、操作、反馈、题间状态和媒体调用。失步保留失败，显式续跑索引不替代现场核对。`compile-session-course.py`交叉检查源答案与UI反馈，生成独立v5夹具，保留v4。接口字段、UI事实和未知状态有不同来源，不能混成前端通过。

LearningCore的题目/选项/配对可携带可选音频资源名；LearningModel通过SwiftPM Bundle解析，LearningAudio播放原版录音。旧夹具兼容，未采齐部分仍有旧系统语音/合成音差异。播放器检查验证文件传输及静音分离，实际输出身份和时序仍待验收。前端契约包含新发现的题间页、结算状态和完成路径，产品入口继续因未覆盖项失败。


### v6 Guidebook与题间状态

Guidebook从SwiftPM中的实测结构化内容读取，使用原版语音与发音图形，原生回放在三课后进入Guidebook，与参考的课程前置状态对齐。标题几何比较采相同的文字边界，保留旧满宽块/AX文字比较失败。LessonDefinition可声明有来源的题间状态，Lesson在状态显示时阻断题目输入，继续后恢复下一题；当前只确认观察到的全对轨迹，不能视为完整鼓励策略。

用户指定后续英语学科；课程来源将改为真实中文→英语观察，已有西语夹具继续版本化保留。Guidebook内容、角色与语音属于案例数据，不能将西语字符串或旧原创英语题库当作新的课程规格。


英语首课由`compile-english-course.py`将API公开内容、UI顺序/反馈和截图转录的对话问句编译为Swift夹具。`sourceType`保留听力/对话等呈现语义，业务kind仍复用choice/word_tiles/matching；`Choice.imageResource`、`slowAudioResource`、`dialogueAvatars`及`Course.interfaceLanguage`明确资源和界面语言。音频资源依具体题目/选项关联，未知英语选项不新增合成音。`fetch-english-resources.py`下载公开原件，在隔离浏览器上下文转换SVG并登记哈希。默认课程为真实en/zh，默认进度按夹具名隔离。英语主页及完成状态链仍待连接，历史Spanish验收入口继续保留。

`observe-frontend.swift --english-first-wrong`复现源参考的首题误选sugar及最后重练，采集逐题前后AX与截图。`compare-english-captures.py`按实际窗口内容矩形去标题栏/归一化尺度，输出无遮罩、无容差的像素差异诊断；不是产品通过判据。英语共享前端契约仍将视觉/声音/交互未验证项标pending，不能凭新增布局或像素统计改为pass。


英语主页配置从实际主页证据编译为`Course.home`与节点lessonCount，区分首节点总4课和当前已观察的lessonIDs，未观察课不编造ID/内容。Swift开始按钮先进入实际节点弹层；未接入第2课是已记录失败，不用首课重放冒充后续内容。原生观察器支持共同进度夹具、弹层状态/按钮enabled采样及显式参考color-scheme环境；普通用户System Default保持原义。源SVG下载处理HTTP gzip后再渲染，保留解码后原件与PNG哈希。

源第二课出现初始API末3题与实际挑战翻译不一致。参考回放现在先核对实际DOM题型，发现分歧时保留证据并停止静态动作；仍需处理同类型内容变化和运行中需求更新，不能认为一次type检查已完成探索模型。orderTapComplete通过真实UI填空顺序被确认，原生对应能力尚待接入。


第二课编译复用无导入写入副作用的`compile_questions`，`compile-english-second.py`以源UI接受反馈裁定实际题目，生成独立v2；v1原字节保持。Question新增可选indicator/example/exampleAudioResource/completionPrefix/completionSuffix，保存范例填空的固定句段及挑战标识，不改业务判题kind。词块按内在宽度换行，保持顺序；没有源语音的中文挑战提示不自动合成未知声音。资源下载支持显式manifest/out，避免覆盖冻结证据。

原生观察器现实际从首课完成主页进入第二课。after-first主页与fresh课程回放分别保存，前端组合观察逐状态登记源回执；原始状态不匹配失败保留。第二课像素诊断包含实际挑战尾部，仍不当作视觉通过。范例按钮音频身份、挑战角色动画、同类型题面动态替换仍是待观察需求。


参考回放现把API期望与独立DOM事实传给`reference-challenge-identity.mjs`，保留完整词库多重集；重复文本不去重。可读提示容器使用hint-token父容器innerText（叶textContent可能为空），否则明确降为文本存在证据。分歧在回答前保存，不能拿身份检查代替完整探索。`answer-reference-live.mjs`以现场词库和模型选择续探，正误回执先落盘，继续转移另行执行，避免过渡失败抹掉已作答证据。第三课历史已交给通用discovery消费者；未加入新策略池或声称完整RSI。


第三课编译器复用无导入写入副作用的第二课builder，输出独立v3，不改v1/v2。compile_word_bank用多重集及逐文本出现队列保留UI顺序/重复身份；核心选择按ID、判题按词序/数量，源完整替代答案规则仍未知。Progress仅在不存在未编译路径时标记course完成，避免新增观察课被旧子集credit遮盖。

原生观察器支持显式进度/起始课接续及重复词块AX检查；全程English回放从首课完成阶段保存home和对应开始弹层，保留home-initial，避免混用状态。角色API图可能为Cropped，不等同页面动画素材；实际Lottie资源需绑定具体状态后接入。


英语第四课验证了两种采集生命周期缺口：进入/重载课程可能先停在挑战邀请或复习说明，不能以challenge heading作为所有入口的就绪条件；响应捕获必须在结束/异常时移除自己的监听器。听力题身份使用当前显式播放的实际源地址和完整词库，文字题仍用可见题面；源地址相等不证明声音输出或听感。新的失败和需求保存在第四课证据，Swift尚未实现新增结算链。

### 英语结算批次与源图形发现

默认en/zh v5在四课57题基础上添加源观察的SettlementPage与独立SettlementFlow，LearningModel控制六页继续与返回主页，ReferenceSettlement负责呈现。题目判分与结算展示分开；observedStreak仅是现场快照，不承担日历算法。完成路径的源几何与两个弹窗存于证据，未接入第二节点不能重复旧内容冒充新课。前端v6保留全部v5断言并新增35项，当前341/8/205、整体fail。

回放器现在保留真实challenge canvas帧、边界与像素尺寸。原版全身角色的Canvas与接口裁切SVG/PDF不同；渲染器及动画资源绑定仍未知。此采集扩展修正素材探索遗漏，不等于已解决动画或证明RSI收益。[当前批次](../projects/duolingo-web/evidence/english-settlement-v1/README.md)。

text_entry在Lesson中保存enteredText，输入编辑受反馈/题间边界保护，clearAnswer清除跨题残留。SwiftUI通过LearningModel绑定状态；原生驱动使用自有PID键盘事件，避免AX直接赋值绕过绑定。当前判分只对两例精确值有源证据，完整源grader待替换。独立输入probe只验证组件，默认题库不变；产品v7保留全部v6需求。[证据](../projects/duolingo-web/evidence/english-input-native-v1/README.md)。

listenMatch使用现有matching状态机及原版静态向量帧，左侧解析精确原音、右侧保留独立排序；错配记录双方状态、扣心并由LearningModel立即保存。该实际混合错误轨迹不把已修正的配对再加入课末重练。text_entry按源HOT接受加入大小写比较，完整正确句保留固定前后缀；其他grader规则未知。回放器区分同题型未支持与真实题序失步，后者仍在作答前拦截。完整第五课含插入题/口语暂缓与新结算，尚待从trajectory编入默认；source history/frontier不表示RSI效果。[证据](../projects/duolingo-web/evidence/english-pairing-native-v1/README.md)。


### 实际Rive角色渲染器

`capture-source-canvas.mjs`从当前challenge canvas导出透明绘图buffer和关联RIVE数据，compositor截图另存；公开CDN解压字节与buffer独立校验。`ReferenceCharacter`以旧角色资源身份映射实际动画资源/状态机/trigger/transform，SwiftPM精确依赖官方RiveRuntime6.24.0，LearningCore不依赖渲染SDK。当前仅Bea/Lucy配置，未映射角色仍是历史静态图，不宣称完整。

原生观察器可采集12张真实idle/feedback窗口，`compare-character-render.py`按实际content rect归一化，并单独计算角色ROI帧变化和整页像素差；变化不能代替源相位/声学等价。独立角色契约保留零容差失败，默认五课v10仍整体fail。标题按实际32px/40px修正，同时回归配对几何。此批反例驱动探索更换探针，尚无自主探索策略或收益证据。[测量与接续](../projects/duolingo-web/evidence/english-character-render-v1/README.md)。


### 观察到的听力暂缓分支

Question可选listeningDecline仅配置已观察路径。Lesson保存独立未评分暂缓状态，禁止继续配对输入，advance不将其写入错误或重练；LearningModel的集成门槛同样接受该状态。实际题序由冻结夹具保存插入翻译→原填空，不依据API下一索引推测后续替换。15分钟是源提示，尚无已验证的计时规则或默认课程完整分支。

观察器新增显式exercise-listening-decline与stop-after-question-id，回执区分局部停止与完整walk，默认不截断。通用截图比较入口可接受显式pairs manifest并保留整课进度背景不匹配限制。首次host advance失败、源AX提取错误及当前次要动作缺失均保留；同一22项契约在原版与Swift独立执行。[本批证据](../projects/duolingo-web/evidence/english-listening-decline-v1/README.md)。


### 反馈动作与独立弹窗验证

Question.feedbackReportReasons保存实际题型原因；LearningModel管理互斥可取消评价、弹窗选择及切题/关闭重置，ReferenceFeedbackActions负责源SVG图形、动作和多选弹窗。当前只冻结已观察糖题，不能用固定六项推断所有题型。提交服务、评价服务器效果未知。

源探针采集可见button/input/label的实际pressed/checked/enabled及布局；原生观察器通过AX实际点击并读取选中/禁用状态，独立生成共享契约观测。父容器必须明确accessibilityElement(children: .contain)，避免其ID覆盖子控件；失败时观察器保存现场AX和截图。卡片像素工具仅在独立测得几何严格相同时比较，不设置通过容差，整页状态背景差异另行报告。[完整范围和回执](../projects/duolingo-web/evidence/english-feedback-actions-v1/README.md)。


### 源文案采样修订与第六课原生轨迹

第六课按实际双暂缓轨迹编译为显式v7夹具，正常分支未观察，不切默认。正确连对计数仅随评分更新，暂缓不增加；主页任务来自可选进度快照。源AX序列化引号和动画父节点不等于显示文案，v12修订保留v11及逐项变化，结算数字来自实际PNG人工读取，不能冒充自动AX识别。文字、几何、像素、实际声音及资源传输分别验收；新修订仍保留全部50项视觉/音频未验证。详见[实际执行与模具反例](../projects/duolingo-web/evidence/english-sixth-native-v1/README.md)。


### 真实次要输入模式

Question可选keyboardAnswer/keyboardPrompt承载源接受的整句；Lesson用usingKeyboard及keyboardText与已有词库/填空分别保存状态。LearningModel转发切换，SwiftUI按实际模式换提示、输入和按钮。observe-frontend的显式exercise-input-modes通过AX/键盘采集四个中间态和实际反馈，与实现前冻结契约独立比较。当前仅两题探针已配置；默认课程、跨题偏好、完整评分器和视觉/声音仍缺，不由fallback补成已验证。源reload与DOM/AX冲突说明重置/采样本身也需要可追溯证据。[本批回执](../projects/duolingo-web/evidence/english-secondary-actions-v1/README.md)。


### 多行输入与真实控件驱动

ReferenceAnswerEditor拥有NSTextView，19px/400与600×170区域，关闭系统智能引号/替换，以delegate回写独立整句缓冲。原生探针针对这类转换使用自有窗口的单次真实鼠标点击，再读取实际状态；保留AX返回失败但动作执行、PID鼠标无效及系统弯引号导致评分失败的历史，不自动重试可能已执行的动作。Falstaff绑定来自当前renderer和解压CDN核验；旧lin文件名实际是Bea，身份误配已撤回。6项输入几何通过不代表整页/声音一致。[本批实测](../projects/duolingo-web/evidence/english-input-layout-v1/README.md)。


### 同课输入偏好与完整第七课需求

Lesson将词库键盘、填空整句偏好分别保存；clearAnswer清答案缓冲，按新题支持的类型恢复对应模式，不支持切换的题不清偏好。原生驱动以当前新题提示和AXTextArea判断模式，不无条件切换。compile-input-preference-probe冻结四个实际题的跨题状态；freeze-seventh-frontend独立从完整原版回执生成39状态/419项及产品v13，组件通过不填补整课未执行。Lin绑定来自实际coffee and tea的API/PNG/renderer及CDN一致字节。源心数刷新、口语替换和额外结算继续作为显式未知/待实现状态。[本批](../projects/duolingo-web/evidence/english-seventh-v1/README.md)。


### 七课集成与控件语义

`compile-english-seventh.py`按真实源UI顺序扩展v8，而非直接照初始API顺序。`Question.reviewWordOrder`保留重练词库顺序，`Lesson.visibleWords`在重练阶段切换展示而不改变答案身份；`SettlementPage.levelLabel`保留额外成就级别。`ReferenceAudioRadio`使用原生NSButton radio承载选择/禁用语义，独立hosting视图绘制源波形帧，不把普通按钮冒充单选。

共享前端v14新增`element_role`（DOM/AX语义归一）和`element_boolean`（必须实际布尔值），在同文字情况下仍能判错控件角色和禁用状态。源ARIA快照与旧`!n.disabled`采样冲突保留，后续采集读取`aria-disabled`；旧v13不覆盖或放宽。驱动用显式`sourceObservationPhase`把切换后的空输入与对应源时点比较，初始状态另外保留；原版与候选都不由测试期望值生成事实。题库、源资源与未观察分支仍分开记录。


前端颜色事实来自实际PNG；`capture_color.py` 将嵌入ICC的macOS截图转换到参考CSS/sRGB空间，再按窗口几何采样。共同 `pixel_color` 契约要求显式sRGB与实际RGB，零容差比较采样点；不替代整图比较。旧raw RGB诊断保留为不同空间直接比较的反例。可选feedbackHint与Choice.correctImageResource表达已观察反馈阶段内容，不改变答题评分。


### 发音练习与分段播放

`compile-pronunciation-practice.py`从真实UI归档生成独立Course，`Question.practiceAudioResources`和`practiceAudioLabels`分别承载原音频身份、反馈揭示词。`LearningModel`以独立Lesson接入发音入口并复用评分/重练；当前尚未实现原版音标持久化，不能以主课程隔离代替发音恢复。`ReferencePracticeAudioButton`使用显式NSButton角色与容器，分别绘制两个分段并在反馈禁用。共同前端v20独立比较原版几何、角色和状态，`observe-frontend.swift`实际点击播放/答题并采集事实，不自行声明通过。[数据与失败](../projects/duolingo-web/evidence/english-pronunciation-split-v1/README.md)。


发音分段与配对共用`ReferencePracticeControl`的原生按钮/AX容器；各自绘制面独立，`Question.rightOrder`决定右列而不改变匹配身份。共同v21比较八个真实原版矩形及标签顺序。第二次原版路线/音标恢复已另存探索frontier，尚未进入课程选择或持久化模型；不以首套定义证明后续练习支持。源驱动对切换后仍禁用的旧radio先等真实可操作状态或非选择题/结算，目前只验证已有终态，后续继续验实际切换。


源练习驱动现在默认建立answer_memory：键包含真实题型、选项标签和原音频身份，结果只从实际反馈更新，续跑显式传入并记录first_probe/prior_feedback；第三次五道重练均实际接受。就绪等待防止disabled旧radio被再次操作；既有slide和已观察成绩单入口共同识别终态，未知题型仍保存现场。源口语/权限及成绩单需求进入v22下一批，原生尚缺对应实现；权限denied探针只改变当前来源并恢复原prompt，不采集环境麦克风。


### 共同前端契约的实际图像要求

`image_pixels`由`capabilities/rebuild/images.py`独立读取参考与候选PNG；原生观察器只绑定真实文件和实测窗口元数据。按ICC转sRGB、实测标题栏裁切及backing scale下采样，零像素差才pass，无掩码/平移搜索/容差。`capture_color.py`兼容导出同一provider，案例独立比较与共同契约不复制算法。Pillow仅图像要求需要，缺少时unavailable，其它能力仍可运行。归档只重定位capture.path到字节一致PNG，原始观察不覆盖。v25将一个旧pending实际执行并追加七幅源图，声音/动画时序与未访问状态仍单独验收。[当前失败与复跑](../projects/duolingo-web/evidence/english-pronunciation-cards-v1/README.md)。


### 字体实际解析与相对几何

发音页的CSS500不能直接映射variable font轴500：实际浏览器使用轴400，而同一页面中文回退为PingFang Medium。卡片局部显式400及源字距，未改变公共default或其它页面。ButtonStyle拥有源66点卡面/2点阴影与按住2点移动，驱动实际持有mouse-down期间采样，异常释放。共同element_geometry可选relative_to_state，比较器从两次真实矩形计算差值；缺原点not_run、坏矩形unavailable，无driver通过标记。绝对几何和图像仍单独验收，位移通过不替代它们。[来源、失败、实际构建](../projects/duolingo-web/evidence/english-pronunciation-typography-v1/README.md)。


### 特别任务页与快照边界

中文Quests路由进入ReferenceHome，ReferenceQuests为中栏、ReferenceQuestMonthly为右栏；状态栏复用，footer使用源链接。HomeProgressSnapshot新增可选questCountdown，compile-quests-page从源DOM及原六课seed生成v11，旧v10不改、课程不改。导航观察与发音共用bindCaptures绑定真实PNG/元数据，不供pass。此批首次发现独立/practice，首题及退出已观察，候选标题失败。源码/实际原生/全规格与子集结果各自保存，不累计不同轨迹覆盖。[该批真实失败](../projects/duolingo-web/evidence/english-quests-v1/README.md)。

### 独立练习的实际轨迹

capture-reference-session显式选择/lesson或/practice，保留白名单公共内容。reference-challenge-identity在作答前校验完整选项/实际媒体/填空上下文；replay按实际DOM类型识别插入/替换，未支持题型另记coverage。键盘态不被当空词库接受。freeze-general-practice从有反馈的真实回执生成前端规格及按实际顺序排列的trace，不将API预告列表当状态机。原版GLOBAL_PRACTICE已出现口语暂缓插入、挑战题替换、错题复习及红心奖励，需要独立于主课解锁/扣生命；该源采集批次尚未接入Swift。后续实现见下一段。源自校验与旧候选重评估分别报告。[证据、模具和下一实施批次](../projects/duolingo-web/evidence/english-general-practice-v1/README.md)。


### 独立练习的Swift消费者

`compile-general-practice.py`读取实际评分回执与动态替换，生成单独的Course夹具及原版媒体清单。Lesson沿用题型、独立输入偏好、暂缓和重练；每课程的mistakeHeartCost默认1，实际通用练习设0。LearningModel用sessionKind区分主课、发音和通用练习，任务入口加载单独课程，完成记录不解锁主课，实际奖励页继续才写入一颗心。当前只重放已观测实例，自适应题目生成及奖励上限并未实现。

题目可带已观察的配对/反馈MP3，LearningAudio的原版效果播放器允许配对完成音与最终反馈并发；缺失原音不添加通用练习的合成点击。复用ReferencePronunciationPractice的头部和配对区，其余题型由共享题型渲染；这只是代码复用，不表示视觉一致。原生驱动实际点击/键入同一状态ID并采样PNG，失败时存实际边界。AXPress返回成功但键盘模式未切换的失败保留，单独重跑使用实际屏幕点击。自有应用输出采集仅筛选子进程、关闭麦克风，回执记录动作时序，不能从非零波形推出声学相等。[完整证据与边界](../projects/duolingo-web/evidence/english-general-practice-native-v1/README.md)。


### 奖励媒体与普通听写布局

通用练习夹具v2给SettlementPage增加可选heartResources，直接编译实际奖励页五个IMG URL；旧夹具v1保留，主课程v11不改。共同前端v29在v28上追加五个图形及三个footer控件的几何/角色/enabled/文案要求。布局实现与验收不合并：回顾仍未实现动作，静态文本的role会明确失败。普通listen根据原版固定画面使用已有Bea Rive、白色分段播放及多行输入，listenTap保留独立蓝色播放布局；相同音频字段不决定相同UI。各轮整图比较与错误合并的负结果保留在[展示修正证据](../projects/duolingo-web/evidence/english-general-practice-presentation-v1/README.md)。


实际探索边界由`replay-reference-session.mjs --stop-before-type`表达；stopped与answered分开，观察到待探题不等于已评分。原版初始sessions字段只提供背景，暂缓后的插入与变题由独立可见页面/提交回执形成实际trace。`freeze-general-listening-decline.py`把这条已执行分支追加到v30，旧断言保留。文字Range/CSS与inlineSVG属于采集事实，不能替代PNG或实际字体解析；源投影自校验、旧候选重评、真实新原生执行分别保存。当前Swift仅支持listenMatch暂缓，listenTap插入与后续变题仍待接入，详见[冻结证据](../projects/duolingo-web/evidence/english-general-listening-decline-v1/README.md)。


LessonDefinition的可选listeningDeclineReplacements由实例提供已观察替换；Lesson在当前位置保留替换用于复习，暂缓本身不评分。原有无替换配对路径保持推进。显式general-practice-fixture选择与主课程分离，默认资源不变，非自适应选题实现；原生驱动从真实任务页进入。v31追加enabled/角色/几何，图像断言保留，源投影与候选执行分别报告。[实现与证据](../projects/duolingo-web/evidence/english-general-listening-decline-native-v1/README.md)。

### 当前渲染题与资源身份

`public-reference-challenge`拥有公共字段投影，session捕获和当前题捕获共享；`rendered-reference-challenge`只从唯一可见challenge的renderer取题目、核对DOM类型，不用初始序列或challengeState回退。`--current-only`把当时内容交给既有身份校验和真实UI作答，保留单步接受、未覆盖、主动边界三种不同结果，不改写初始session。公共答案不作为盲探索效果证据。

`import-current-character.py`连接当前公共角色与实际renderer绑定：下载公开Rive并核对实测缓冲SHA后才进入Swift资源映射。资源身份、原生可见运动、同状态几何、像素和时序分别验证，不能互相代替。原生可选按指定resource采样实际自有窗口，q5动作期12帧，不注入Lesson状态。当前Eddy绑定已生效但全图差异没有改善。[实际源、新驱动与负结果](../projects/duolingo-web/evidence/english-current-challenge-v1/README.md)。

`Question.isolationPromptTokens`为可选显示数据，从源token和blankRange编译，保留空格/标点/缺词/可提示词身份，不改变答案或评分。通用夹具v3带该数据；`ReferenceIsolationPhrase`按真实词宽留白，正确反馈显示绿色原词，播放控件仅覆盖原版29×22区域。只有带数据的通用题使用新行/气泡/分隔线布局，旧夹具保持旧路径。v32追加9条源几何和语义，整图与暂缓缺失继续明确失败/不可验证；当前题模式在无challenge引导页仍不能自动续接。[验证与局限](../projects/duolingo-web/evidence/english-isolation-presentation-v1/README.md)。
