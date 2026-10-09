# LingoSeed · Swift 教育基座

可运行的 macOS SwiftUI 客户端，使用原创 Everyday English 两课时题库与系统符号。实现课程路径与顺序解锁、选择题、配对、拼句与撤回、反馈、错题重练、结算和持久进度。冻结 v2 的12条共享场景已在网页参考和实际原生 UI 两侧通过；这不代表整个运行 Goal 已完成。

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

非法 JSON、空对象、null 完成记录及负生命进度会显示 Course unavailable 并保留原文件；合法旧格式仍可打开。这五个启动界面检查已冻结并实测，见参考案例的 PROGRESS-REPAIR.md，不代表穷尽所有损坏输入。完整证据、六个实际界面与验收命令见参考案例。多阶段模型续跑和业务消融仍待完成。
