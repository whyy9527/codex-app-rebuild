// swift-tools-version: 6.0
import PackageDescription
import Foundation

let privacyPlist = URL(fileURLWithPath: #filePath).deletingLastPathComponent().appendingPathComponent("Support/Info.plist").path

let package = Package(
    name: "LingoSeed",
    platforms: [.macOS(.v14)],
    products: [.library(name: "LearningCore", targets: ["LearningCore"]), .executable(name: "LingoSeed", targets: ["LingoSeed"])],
    dependencies: [.package(url: "https://github.com/rive-app/rive-ios", exact: "6.24.0")],
    targets: [.target(name: "LearningCore"), .executableTarget(name: "LingoSeed", dependencies: ["LearningCore", .product(name: "RiveRuntime", package: "rive-ios")], resources: [.copy("Resources/Reference")], linkerSettings: [.unsafeFlags(["-Xlinker", "-sectcreate", "-Xlinker", "__TEXT", "-Xlinker", "__info_plist", "-Xlinker", privacyPlist])]), .executableTarget(name: "LearningCoreChecks", dependencies: ["LearningCore"], path: "Tests/LearningCoreTests")]
)
