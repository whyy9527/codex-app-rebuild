// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "LingoSeed",
    platforms: [.macOS(.v14)],
    products: [.library(name: "LearningCore", targets: ["LearningCore"]), .executable(name: "LingoSeed", targets: ["LingoSeed"])],
    targets: [.target(name: "LearningCore"), .executableTarget(name: "LingoSeed", dependencies: ["LearningCore"], resources: [.copy("Resources/Reference")]), .executableTarget(name: "LearningCoreChecks", dependencies: ["LearningCore"], path: "Tests/LearningCoreTests")]
)
