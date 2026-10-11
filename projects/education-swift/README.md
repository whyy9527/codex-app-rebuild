# LingoSeed · Swift 教育基座

下一Practice已可打开原版素材建档提示并稍后返回；创建档案后实际年龄页已观察、尚未实施，候选创建按钮仍失败。最新v43共2382项，本轨迹43pass/21fail/2318not_run。[最新验证与复跑](../duolingo-web/evidence/english-path-profile-v1/README.md)。

默认v13补实际开箱前后主页、原素材及持久化记录，原生真实开箱和重启已验证；前端v41共2373项，本轨迹34pass/17fail/2322not_run，下一Practice开始/建档及排行榜遮罩仍未实施。[最新失败、探索与复跑](../duolingo-web/evidence/english-chest-v1/README.md)。

可运行的macOS SwiftUI客户端。当前默认 `fixture-reference-en-zh-v13.json` 为中文母语→英语八课115题；新增实际第八课、13卡历史回顾、结算及真实重启。前端仍133pass/17fail/2171not_run，结算图形/按钮与宝箱等未对齐，音频资源身份不等于实际输出验证。[当前验证及复跑](../duolingo-web/evidence/english-eighth-integration-v1/README.md)。

当前发音练习按三次原版轨迹编译、独立保存，完成首套后重启实际进入sip/zip。口语拒绝/关闭/暂缓及发音练习退出已接入原生验证；全错直接退出，已获得正确进度时确认，取消保留题目状态；正常录音识别只有基础接线，尚未接评分和推进，不能称正常口语完成。前端、角色及实际声音仍有差异，见[最新证据与复跑](../duolingo-web/evidence/english-practice-exit-v1/README.md)。第四/第五套及原版自适应规则继续探索；旧第七课全程结果不移用到当前构建。

原版Bea/Lucy的实际Rive全身动画已接入默认题库，官方Apple RiveRuntime锁定6.24.0。初次构建需联网下载SDK约108MB，SwiftPM自动将framework放到可执行文件旁；直接运行保留整个构建目录及资源bundle。角色变化已通过实际连续截图测量，动画时序、mouth/audio同步与其余角色仍未对齐。[当前渲染证据和失败](../duolingo-web/evidence/english-character-render-v1/README.md)。

五课、六课及组件探针保持历史版本，不再将“正常分支尚未采齐”作为默认集成已观察课程的额外门槛；未验证分支继续进入探索与验收。23项核心检查不能替代真实窗口、视觉或音频验收。

## 构建、运行与重置

从仓库根执行，macOS 14+、Swift 6 工具链：

```sh
swift build --package-path projects/education-swift --product LingoSeed
projects/education-swift/.build/debug/LingoSeed --fixture projects/duolingo-web/fixture-reference-en-zh-v13.json --progress artifacts/lingoseed-english-demo/progress.json
swift run --package-path projects/education-swift LearningCoreChecks
```

换一个尚不存在的 `--progress` 文件即可建立独立初态。普通运行默认保存到用户 Application Support 下 `LingoSeed/<fixture-name>/progress.json`，不同夹具不共享默认进度，不要将普通用户进度用作验收夹具。原生适配器始终使用临时题库/进度，关闭并清理自己启动的进程；reload 重开同一临时进度文件。

本机缺少 XCTest / Swift Testing 模块；核心检查采用非零失败的 `LearningCoreChecks` 可执行入口。23项核心检查覆盖实际英语轨迹、题间状态、空答案与错题重练、存储往返、拼句/撤回/锁定、配对、课时解锁及旧数据兼容。它们不能替代原生 UI E2E。

## 职责与扩展

- `LearningCore`：Foundation-only 课程、题型、状态机和进度存储，保留未来 iOS 复用能力；尚未验证 iOS 构建。
- `LearningModel`：用户动作、尝试状态、保存与错误提示。
- `LearningSpeech`：显式用户触发的权限/音频输入/转录基础与取消；评分和正常口语反馈尚未接入。验证注入拒绝，不开启环境录音。
- `LearningView`：SwiftUI 路径、活动、反馈与结算。
- `LearningCoreChecks`：核心业务检查。
- [参考案例](../duolingo-web/README.md)：共享规格、冻结批次和平台驱动；产品状态机不包含验收答案逻辑。

替换 fixture 的 `data.candidate_course` 可换课程。新格式含 `lessons`，每课含 questions；题型为 choice、matching、word_tiles，字段例见 fixture-v2.json。仍可读取旧单课 questions 格式。旧完成记录只给旧单课内容记分，不自动完成新课时。

## 历史 v2/v3 产品决策与边界

以下记录描述旧实现，不能作为当前 1:1 目标的范围限制。

两端比较业务动作和断言，题面、课程长度、选项顺序及视觉素材不同。生命归零暂不阻断学习；错误配对重试不扣生命。这些是原版未观察边界上的显式产品决策。完成课时和生命持久保存，主动退出丢弃未完成尝试，不保存逐题断点。没有登录、支付、排行、语音识别或完整题库。

非法 JSON、空对象、null 完成记录及负生命进度会显示 Course unavailable 并保留原文件；合法旧格式仍可打开。这五个启动界面检查已冻结并实测，见参考案例的 PROGRESS-REPAIR.md，不代表穷尽所有损坏输入。完整证据、六个实际界面与验收命令见参考案例。多阶段模型续跑已有[一次完整可行性证据](../model-pipeline/README.md)；[四组业务消融](../business-ablation/REPORT.md)已完成，均公开12/12与留出2/2、另1未知；N=1未观察到通过率收益。

历史v2工程复验：原生12/12、核心5项及Python43项通过；该记录不代表当前产品完成，见[撤回完成声明与历史审计](../../docs/DELIVERY-AUDIT.md)。

## 历史产品修正 v3（局部检查，完成声明已撤回）

默认学习主页采用白底、绿色单元横幅、课程节点、侧导航及右侧学习卡片。窄窗缩为图标侧栏，再隐藏右栏保留课程操作。练习含顶部进度/生命、中央题面及底部检查/反馈。Guidebook、导航页及返回有真实去向；账户、商店和在线排行明确未连接。

原创音效由 LearningAudio 合成：点击、正确、错误、结算，配对自动完成同样触发正确音效。单一播放器替换上一声音，指令朗读使用系统语音（不提前朗读答案）。侧栏和练习顶部有静音按钮，保存到指定进度文件旁的 `.audio.json`；恢复静音状态不会修改课程进度。已实际观察原版选项发音，选择本地选项会朗读所选文字，并提供重播；未选择时读指令，不泄露答案。采用系统英文语音，与原版录音不同。

可复现声音检查（先建立 `artifacts/product-v3`）：

```sh
mkdir -p artifacts/product-v3
swiftc -parse-as-library projects/education-swift/Sources/LingoSeed/LearningAudio.swift projects/education-swift/Checks/AudioChecks.swift -o artifacts/product-v3/audio-checks
artifacts/product-v3/audio-checks artifacts/product-v3/audio-samples
```

该检查会实际播放两次短音，验证四种音频解码、播放器时间推进、静音停止/阻断和恢复，并导出 WAV 样例。它不等于声卡输出录音或用户听觉验收。完整视觉、声音、入口及纵向流程仍按[产品验收v3](../duolingo-web/PRODUCT-ACCEPTANCE-v3.md)推进，不提前宣布完成。

本轮新增28项产品UI检查与六段真实应用系统输出录音通过；静音时执行配对的采样输出为零。检查命令、17张截图、来源与尚未对齐的拼句/导航视觉见[产品复验](../duolingo-web/evidence/PRODUCT-V3-REVIEW.md)。后续最终证据见下文。

历史产品修正检查：35项原生产品检查、22张实际截图、7段应用输出录音、冻结12项与核心5项通过，见[交付审计](../duolingo-web/evidence/PRODUCT-V3-DELIVERY.md)与[并排截图](../duolingo-web/evidence/product-v3-comparison.html)。包括自然启动三栏、五个导航页及真实课程入口、拼句发音气泡与答案横线。此前28项/6段是历史迭代，不是最终源码的回执。


## 当前 v4 修正

`ReferenceHome`、`ReferenceStyle` 负责原版主页和字体/资源呈现；`LearningCore` 仍拥有课程状态，题目答案由实际原版正向反馈确认后编入夹具。第一个路径节点含三节课，不能把每节课画成独立节点；尚未采齐的第三节课不会被伪造内容替代。`ChoiceIllustration` 按选项文本查找实际图片，不读取答案。

原版两节课24题在真实原生 AX 驱动中走完，144项题面/选项/词库/配对文案通过。文案通过不证明选项几何、反馈或声音一致。实际字体与图形已经纳入 SwiftPM 资源；Duo 目前只是原版一个动画帧，动画仍缺。系统西语朗读已接入，原版语音和反馈音效身份/时序尚未对齐，旧合成音不能被算作 1:1。

从仓库根复验：

```sh
python3 projects/duolingo-web/compile-observed-course.py
python3 projects/duolingo-web/verify-product.py --out artifacts/product-new
```

统一入口会因未完成的前端需求返回失败，这是当前实际状态。具体回执与未探索分支见[探索记录](../duolingo-web/evidence/exploration-v4/README.md)。


### Preferences修正

设置页使用原版布局、字体、四个开关和三项外观选择。`LearningPreferences`保存非全局静音的偏好，`LearningAudio.effectsEnabled`单独控制音效，原来的全局静音继续控制所有输出。`ReferenceSettings`通过实际AX动作验证四个开关关闭后重启恢复、Dark mode=On重启恢复，以及四个开关的内容坐标几何。

这些检查不代表课程效果已实现：Animations、Motivational messages、Listening exercises目前只保存偏好。原版相同契约还暴露了保存200后刷新恢复旧值的反例，统一产品入口会一并报告。当前完整证据和未知见[偏好与探索记录](../duolingo-web/evidence/exploration-v4/README.md)。


### 当前v5：第三课与原版语音

默认夹具改为`fixture-reference-v5.json`，由原版前三课37题组成。第三课源答案、实际呈现顺序和逐题正向反馈已经交叉确认，31个源语音文件按具体题目/选项关联；旧课的语音缺口仍在。关闭Sound effects不阻断这些语音，全局静音仍停止并阻断播放，实际播放器推进已检查，原版音色/时序输出尚未比较。

Swift仍缺原版题间鼓励、评分/连续学习/Legendary/注册提示及完成节点状态。它们已进入新版前端契约，不会因37题文案通过被算作完成。重新编译固定v5使用`python3 projects/duolingo-web/compile-session-course.py`；[本批证据与运行方式](../duolingo-web/evidence/exploration-v5/README.md)保留失败及人工续点。


### v6与英语方向

历史西语夹具`fixture-reference-v6.json`：原版角色、两处题间状态和完整实测Guidebook内容已加入。`ReferenceGuidebook`替换通用介绍弹窗，逐句播放六个源语音文件。6项核心检查、37题实际原生回放通过；Guidebook还有1.03125点的图标y差、完整视觉/声音和其它行为缺口，不能视为1:1。

用户建议英语学科后，当前目标转为中文母语学习英语。默认候选尚未切换，正在采真实英语课；旧原创英语夹具只保留历史兼容，不是原版英语复刻。详见[v6证据和运行命令](../duolingo-web/evidence/exploration-v6/README.md)。


### 真实英语首课接入

默认启动已读取`fixture-reference-en-zh-v1.json`，不是旧原创英语题库。15题由实际API公开内容及UI确认的顺序/反馈编译；首题答案在实际错题重练中接受。明确资源关联替代词语全局猜测，保留normal/slow听力源剪辑及双人对话头像/问句。34个公共源资源（21音频、13SVG及对应PNG）有URL和SHA256清单；资源传输、播放调用不代表实际声音输出一致。

```sh
python3 projects/duolingo-web/compile-english-course.py
swift build --package-path projects/education-swift
swift run --package-path projects/education-swift LearningCoreChecks
projects/education-swift/.build/debug/LingoSeed --fixture projects/duolingo-web/fixture-reference-en-zh-v1.json --progress artifacts/my-english-preview/progress.json
```

7项核心检查通过，原生UI全对/首题答错两条轨迹均执行到结算；标题15通过，59待覆盖；28对源/原生归一化截图均有差异。普通默认启动也单独验证英语标题。原生仍缺原版红心教学、鼓励和完整完成链；英语主页及Guidebook尚未迁移，当前Guidebook还是历史西语。不可称1:1或声学验收完成。[证据与复跑](../duolingo-web/evidence/english-native-v1/README.md)。


### 英语主页v2

主页补入中文侧栏/卡片、发音与英语旗帜源素材、五节点顺序、首节点四课进度环及开始弹层。按首课完成且红心4的共同夹具，v2.1主页/弹层26项通过、1项失败、75项未执行；第2课开始仍失败，原版实际第2课已观察但尚未编译。首轮资源gzip、色彩环境、AX标签及点击范围失败均保留。使用`--reference-color-scheme light`匹配本次原版浏览器环境，普通用户默认外观保持System Default。源资源现36个（21音频、15SVG/PNG）。见[主页实测](../duolingo-web/evidence/english-home-v2/README.md)和[第二课实际尾部变化](../duolingo-web/evidence/english-second-v1/README.md)。


### 英语第二课接入（当前默认）

默认夹具现为`fixture-reference-en-zh-v2.json`，两课各15题；v1保留历史回归。第二课按实际UI尾部编译，包含范例填空、三道挑战及三处鼓励，首节点第2课可启动。8项核心及原生两课回放完成；前端匹配状态128通过、105未覆盖，第二课30对截图全有差异，整体仍失败。见[实际回执与命令](../duolingo-web/evidence/english-second-native-v1/README.md)。上述v1主页开始失败是保留的历史结果。


### 当前默认：英语第三课

默认`fixture-reference-en-zh-v3.json`为三课各15道实际题，支持重复词块独立选择/撤回。9项核心及原生完整三课回放通过；前端221通过、151未覆盖整体fail，第三课30对截图均有差异。完成三课不再错误标记未编译路径全部完成。旧v1/v2与先前失败保留。[实测、限制与命令](../duolingo-web/evidence/english-third-native-v1/README.md)。


### 真实英语第四课与公开语音交付

默认v4接入12题挑战、独立入口及开场/难题说明；四课原生从空进度走完，核心10项通过，统一前端303pass/8fail/208not_run，产品仍fail。主页三课后宝石505及青铜卡片已修正，70条公共源语音随默认应用资源纳入Git；结算链、下一节点、视觉及实际声音等价仍未完成。详见[本批验证与复跑](../duolingo-web/evidence/english-fourth-native-v1/README.md)。

新增text_entry可编辑/清空/提交后锁定，两个源确认输入值和正常/慢速语音已实际原生验证。独立输入probe不替换默认四课；完整判分和第二节点其余题型未完成。[证据与命令](../duolingo-web/evidence/english-input-native-v1/README.md)。

听音配对已按源事实改为左侧播放、错配扣心并保存、重试与双侧锁定；自由输入补齐完整正确句与HOT重练接受。14项核心通过，配对组件14/0/4、重练组件7/0/3，均未整体通过。[实测](../duolingo-web/evidence/english-pairing-native-v1/README.md)。原版第五课已走完，默认仍四课，整课及口语暂缓/结算接入继续。

反馈动作新增互斥可取消评价、多选报错及关闭重置；当前源证据只冻结糖题，其他题型选项和提交服务未完成。31项两端25通过/6未验证，像素仍不同。完整失败与复跑见[反馈动作批次](../duolingo-web/evidence/english-feedback-actions-v1/README.md)。

第六课已编入显式`fixture-reference-en-zh-v7.json`并在原生走完已观察双暂缓路径，默认仍v6，正常分支未采齐。新增连对计数、输入区域/标签、口语暂缓动作、第二节点进度和实际30经验任务。17项核心通过；309项独立第六课228通过/31失败/50未验证，25对像素仍不同。[证据及复跑](../duolingo-web/evidence/english-sixth-native-v1/README.md)。


发音卡片按实际原版修正为19px音标、15px单词和68点点击区域；共同v25直接读取PNG比较，8幅整图仍失败。正常口语评分/推进、音标增长和完整前端/声音继续，不能称1:1完成。[本批证据与可复跑图像验收](../duolingo-web/evidence/english-pronunciation-cards-v1/README.md)。


当前发音卡片使用实测Latin字体轴400与0.8px字距，保留中文实际回退字重；按住下移2点并去掉2点阴影，释放恢复。共同v26独立比较真实状态位移，绝对几何及8图仍失败。[本批64状态验证与图片](../duolingo-web/evidence/english-pronunciation-typography-v1/README.md)。


中文特别任务页已替换英文占位页，保留原版Duo/徽章/锁/时钟素材及六课14小时快照。10文案/5几何通过，整图与独立Practice题目仍失败；v11仅扩展快照，不变更七课内容。[真实导航及复跑](../duolingo-web/evidence/english-quests-v1/README.md)。
