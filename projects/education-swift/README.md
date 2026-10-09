# LingoSeed · Swift 教育基座（首批）

可运行的 macOS SwiftUI 客户端，使用原创 Everyday English 课程和系统符号，没有 Duolingo 素材。当前只有一个两题选择课；这不是完整 Goal 的交付。拼句、配对、多个课时的路径解锁及后续共享验收仍待实现。

## 构建与运行

从仓库根执行，macOS 14+、Swift 6 工具链：

```sh
swift build --package-path projects/education-swift
projects/education-swift/.build/debug/LingoSeed --fixture projects/duolingo-web/fixture-v1.json
swift run --package-path projects/education-swift LearningCoreChecks
```

普通运行将已完成课程保存到用户 Application Support 下 `LingoSeed/progress.json`。使用 `--progress <新文件路径>` 可在独立空进度中运行；不要把普通用户进度作为验收夹具。UI 适配器始终创建临时目录，运行后关闭自己启动的进程并清理该目录，不读取用户进度。

命令行工具集可以构建本客户端，但当前本机缺少 XCTest 和 Swift Testing 模块；保留失败日志，核心检查采用 `LearningCoreChecks` 可执行入口，错误时返回非零。它检查空答案、错题复习、完成前必须纠错、存储重开以及损坏数据不被覆盖，属于核心层，不代替原生 UI E2E。

## 职责

- `LearningCore`：可替换的 Codable 课程、题目、选择题状态机和进度存储；不依赖 SwiftUI/AppKit。
- `LingoSeed`：SwiftUI 页面、用户操作和保存完成进度；课程由显式夹具读取。
- `LearningCoreChecks`：核心业务检查。
- 原生 UI 驱动、统一场景和断言在 [参考案例](../duolingo-web/README.md)，不放进产品状态机。

题目选择、提交锁定、错误扣生命和退出取消以已观察网页行为为来源。核心目前还实现了错题队列、完成结算及本地保存，但这些尚未全部通过原版／原生共享场景验收。选择／反馈／退出取消及提交前改选五条共享场景已由原生 UI 实际执行通过，见 `candidate-v1.2-01.json`。原生界面实测截图在参考案例 evidence 中；截图只是界面检查，不证明课程或持久化的所有行为。

## 显式产品决策与限制

原创题面和课程长度不同于网页题库；两端比较相同动作语义与业务断言，不比较文字、选项顺序、奖励或品牌外观。首批五颗生命只记录错误，不阻断学习；耗尽后的原版规则尚未观察，这项是基座决策。一个课程暂时对应一个课时，完成后允许练习，不能把这当作已经实现多课时解锁。

持久化只保存已完成课程，主动退出丢弃当前未完成尝试。加载损坏的进度时显示错误，不静默重置。后续需完成跨端验收、更多题型、路径状态和完整业务实验，才能满足运行 Goal。
