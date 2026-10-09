# 首批原生实现与驱动迭代

执行日期：2026-10-10。真实 macOS SwiftUI 进程，Swift 6.3.2，当前命令行工具集；产品名 LingoSeed。没有借用 XCTest、浏览器脚本或核心测试充当原生 UI 结果。

v1 原版四条已知场景由主引擎执行通过，见 `reference-v1-01.json`；随后按当时输入成功冻结 `batch-v1.json`。冻结后才创建 Swift 产品实现。浏览器和 Swift 驱动接收相同动作，预期只在共享规格中；题面分别映射到线上西班牙语入门词汇与原创英语问候课程。

首次产品构建有两个编译问题：课程合法性校验的嵌套 `$0` 遮蔽，以及领域 `Progress` 与 Foundation 同名。前者改用显式 question 参数，后者更名 LearningProgress。第二次原始构建日志保存在 `swift-build-02.log`；后续构建实际成功。日志中工作目录和 SDK 路径已脱敏，编译器代码摘录的行尾空白已规范化。

`swift test` 实测失败，原因是本机没有 XCTest；另外实际 import Testing 也不可用。保留 `swift-tests-01.log`，核心层改用显式可执行检查，见 `swift-core-checks-01.log`。不宣称 `swift test` 通过。客户端路径页与选择题已启动并截图检查，分别见 `lingoseed-path-v1.png`、`lingoseed-question-v1.png`；主要文字与控件可见，空答案时 Check answer 呈禁用状态，尚未检查所有页面尺寸。

## 冻结后的协议失败

`candidate-v1-01.json`：空答案、正确反馈、错误反馈通过；退出取消 invalid，批次整体 fail。失败回执显示 107864 字节输出，超过执行器 65536 字节记录上限，被正确判定为截断协议；没有把截断的场景当作通过。原驱动枚举了应用窗口和完整菜单，多步重复记录造成超限。

修复假设：保留所有业务观察，只将快照范围限制为被测客户端的 AXWindows，不包含系统菜单。新驱动为 `native-adapter-v2.swift`；旧 `native-adapter.swift` 和 v1 规格、配置、回执全部保留，未修改已冻结文件，也未提高记录上限或放宽业务断言。

v1.1 使用相同四条场景与夹具，只变更原生驱动目标，并引用 v1 的实际冻结父批次。已重新执行原版并通过，建立 `batch-v1.1.json` 后原生端四项全通过（`candidate-v1.1-01.json`），最大场景回执为 11075 字节，完整性 verified。统一覆盖见 `coverage-v1.1.json`。此项属于驱动协议修复，不等于产品业务 fail→pass 或模型效果消融；完整 Goal 的相关要求仍待真实业务证据。

## 初始探索新增题型

等待原版确认期间继续第二课，已实际看到 `Write this in English` 的词块题。`mi maleta` 选择 my 后 Check 可用，点击已选 my 后 Check 再禁用；逆序 suitcase/my 提交得到 Correct solution: my suitcase，生命从 3 到 2。下一道 `mi casa` 以 my/house 顺序提交出现 Great job，生命仍为 2。

原始观察为 `word-tiles-discovery.json`、`word-tiles-selection.json`、`word-tiles-undo-wrong.json`、`word-tiles-correct.json`。题面文字在可见 DOM 中，部分字符 aria-hidden，所以同时记录可见文本；仅凭 AX 快照会遗漏题面。这些观察发生在首批候选整体通过之前，属于初始探索延伸，不计作独立补充探索收益。v1/v1.1 仍保留 word-tiles 为 unknown；后续转换为带证据的场景前不能算覆盖通过。
