# 本机交付环境预检

核验日期：2026-10-10。此处只记录交付工具能力，不记录或推导 Duolingo 产品行为。

| 项目 | 实际结果 | 可支持的结论 |
| --- | --- | --- |
| Swift | Apple Swift 6.3.2，arm64 macOS | Swift 编译器可用 |
| 当前开发目录 | CommandLineTools | 当前使用命令行工具集 |
| macOS SDK | 26.5 | `xcrun --show-sdk-version` 实际返回 |
| SwiftUI/AppKit 预检 | `swiftc -parse-as-library -typecheck -` 成功 | 原生应用入口、WindowGroup 与 Text 类型检查通过 |
| Xcode | `xcodebuild -version` 报需要完整 Xcode；标准 Applications 目录未发现 Xcode.app | 当前 Xcode/XCUITest 路径不可用，不代表 SwiftUI 无法构建 |
| 实际原生 UI 验收 | 未执行 | 需要后续可运行客户端与实际 UI 驱动证据 |

预检源代码是临时能力探针，未作为产品实现提交，也未启动应用：

```swift
import SwiftUI
import AppKit
@main struct EducationBuildProbe: App {
    var body: some Scene {
        WindowGroup { Text("Build capability probe") }
    }
}
```

后续优先检查当前环境可用的原生 UI 驱动能力；若必须使用 XCUITest，再解决完整 Xcode 的安装与开发目录。不能以本预检、核心单元测试或测试替身代替 Goal 要求的原生 UI E2E、界面和视觉检查。
