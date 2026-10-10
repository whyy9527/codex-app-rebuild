// Collect actual text from an isolated child, without encoding expected copy.
import AppKit
import ApplicationServices
import Foundation

let root = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
let output = URL(fileURLWithPath: CommandLine.arguments[1], relativeTo: root).standardizedFileURL
try FileManager.default.createDirectory(at: output, withIntermediateDirectories: true)
let progress = output.appendingPathComponent("progress.json")
precondition(!FileManager.default.fileExists(atPath: progress.path), "Use a fresh output directory")
let child = Process()
child.executableURL = root.appendingPathComponent("projects/education-swift/.build/debug/LingoSeed")
child.arguments = ["--fixture", root.appendingPathComponent("projects/duolingo-web/fixture-v2.json").path, "--progress", progress.path]
child.standardOutput = FileHandle.nullDevice
child.standardError = FileHandle.nullDevice
try child.run()
defer { if child.isRunning { child.terminate() } }
let app = AXUIElementCreateApplication(child.processIdentifier)
func attr(_ element: AXUIElement, _ name: String) -> AnyObject? {
    var result: CFTypeRef?
    guard AXUIElementCopyAttributeValue(element, name as CFString, &result) == .success else { return nil }
    return result
}
func nodes(_ element: AXUIElement, _ depth: Int = 0) -> [AXUIElement] {
    guard depth < 24 else { return [] }
    return [element] + ((attr(element, kAXChildrenAttribute) as? [AXUIElement]) ?? []).flatMap { nodes($0, depth + 1) }
}
func current() -> [AXUIElement] {
    ((attr(app, kAXWindowsAttribute) as? [AXUIElement]) ?? []).flatMap { nodes($0) }
}
let deadline = Date().addingTimeInterval(12)
while Date() < deadline && !current().contains(where: { (attr($0, kAXIdentifierAttribute) as? String) == "course-entry" }) {
    Thread.sleep(forTimeInterval: 0.1)
}
precondition(current().contains(where: { (attr($0, kAXIdentifierAttribute) as? String) == "course-entry" }), "No child home observed")
func observe() -> [String: Any] {
    let strings = Set(current().flatMap { node in
        [kAXValueAttribute, kAXTitleAttribute, kAXDescriptionAttribute].compactMap { attr(node, $0) as? String }.filter { !$0.isEmpty }
    })
    return ["accessible_text": strings.sorted()]
}
var states = ["home": observe()]
if let more = current().first(where: { (attr($0, kAXIdentifierAttribute) as? String) == "nav-more" }) {
    let result = AXUIElementPerformAction(more, kAXPressAction as CFString)
    if result == .success {
        Thread.sleep(forTimeInterval: 0.5)
        // Reference expectation: submenu. Candidate currently opens a page.
        states["more-open"] = observe()
    }
}
let receipt: [String: Any] = ["kind": "owned_native_ax_observation", "states": states,
    "observed_at": ISO8601DateFormatter().string(from: Date()),
    "action": "Start isolated child, collect home, press More, collect result",
    "limitations": ["AX text only; no visual/audio equivalence", "More press is not reference hover"]]
let data = try JSONSerialization.data(withJSONObject: receipt, options: [.prettyPrinted, .sortedKeys])
try data.write(to: output.appendingPathComponent("observed.json"), options: .withoutOverwriting)
print("Collected actual home and More text from owned child")
