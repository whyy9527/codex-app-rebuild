# LingoSeed · Swift 教育基座

可运行的 macOS SwiftUI 客户端，使用原创 Everyday English 两课时题库与系统符号。实现课程路径与顺序解锁、选择题、配对、拼句与撤回、反馈、错题重练、结算和持久进度。冻结 v2 的12条共享场景已在网页参考和实际原生 UI 两侧通过；本轮产品修正的逐项证据见文末，行为测试本身仍不代表全部产品要求。

## 构建、运行与重置

从仓库根执行，macOS 14+、Swift 6 工具链：

```sh
swift build --package-path projects/education-swift --product LingoSeed
projects/education-swift/.build/debug/LingoSeed --fixture projects/duolingo-web/fixture-v2.json --progress artifacts/lingoseed-demo/progress.json
swift run --package-path projects/education-swift LearningCoreChecks
```

换一个尚不存在的 `--progress` 文件即可建立独立初态。普通运行默认保存到用户 Application Support 下 `LingoSeed/progress.json`，不要将普通用户进度用作验收夹具。原生适配器始终使用临时题库/进度，关闭并清理自己启动的进程；reload 重开同一临时进度文件。

本机缺少 XCTest / Swift Testing 模块；核心检查采用非零失败的 `LearningCoreChecks` 可执行入口。五项检查覆盖空答案与错题重练、存储往返、拼句/撤回/锁定、配对、课时解锁及旧数据兼容。它们不能替代原生 UI E2E。

## 职责与扩展

- `LearningCore`：Foundation-only 课程、题型、状态机和进度存储，保留未来 iOS 复用能力；尚未验证 iOS 构建。
- `LearningModel`：用户动作、尝试状态、保存与错误提示。
- `LearningView`：SwiftUI 路径、活动、反馈与结算。
- `LearningCoreChecks`：核心业务检查。
- [参考案例](../duolingo-web/README.md)：共享规格、冻结批次和平台驱动；产品状态机不包含验收答案逻辑。

替换 fixture 的 `data.candidate_course` 可换课程。新格式含 `lessons`，每课含 questions；题型为 choice、matching、word_tiles，字段例见 fixture-v2.json。仍可读取旧单课 questions 格式。旧完成记录只给旧单课内容记分，不自动完成新课时。

## 产品决策与边界

两端比较业务动作和断言，题面、课程长度、选项顺序及视觉素材不同。生命归零暂不阻断学习；错误配对重试不扣生命。这些是原版未观察边界上的显式产品决策。完成课时和生命持久保存，主动退出丢弃未完成尝试，不保存逐题断点。没有登录、支付、排行、语音识别或完整题库。

非法 JSON、空对象、null 完成记录及负生命进度会显示 Course unavailable 并保留原文件；合法旧格式仍可打开。这五个启动界面检查已冻结并实测，见参考案例的 PROGRESS-REPAIR.md，不代表穷尽所有损坏输入。完整证据、六个实际界面与验收命令见参考案例。多阶段模型续跑已有[一次完整可行性证据](../model-pipeline/README.md)；[四组业务消融](../business-ablation/REPORT.md)已完成，均公开12/12与留出2/2、另1未知；N=1未观察到通过率收益。

历史v2工程复验：原生12/12、核心5项及Python43项通过；该记录不代表当前产品完成，见[撤回完成声明与历史审计](../../docs/DELIVERY-AUDIT.md)。

## 产品修正 v3

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

最终产品修正验收：35项原生产品检查、22张实际截图、7段应用输出录音、冻结12项与核心5项通过，见[交付审计](../duolingo-web/evidence/PRODUCT-V3-DELIVERY.md)与[并排截图](../duolingo-web/evidence/product-v3-comparison.html)。包括自然启动三栏、五个导航页及真实课程入口、拼句发音气泡与答案横线。此前28项/6段是历史迭代，不是最终源码的回执。
