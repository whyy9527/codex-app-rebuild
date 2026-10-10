// Collect actual text from an isolated child, without encoding expected copy.
import AppKit
import ApplicationServices
import Foundation

func main() throws {
let root = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
let output = URL(fileURLWithPath: CommandLine.arguments[1], relativeTo: root).standardizedFileURL
try FileManager.default.createDirectory(at: output, withIntermediateDirectories: true)
let progress = output.appendingPathComponent("progress.json")
precondition(!FileManager.default.fileExists(atPath: progress.path), "Use a fresh output directory")
if let seedIndex = CommandLine.arguments.firstIndex(of: "--seed-progress"), seedIndex + 1 < CommandLine.arguments.count {
    try Data(contentsOf: root.appendingPathComponent(CommandLine.arguments[seedIndex + 1])).write(to: progress, options: .withoutOverwriting)
}
let childLog = output.appendingPathComponent("child.log")
FileManager.default.createFile(atPath: childLog.path, contents: nil)
let fixture = CommandLine.arguments.count > 2 ? CommandLine.arguments[2] : "projects/duolingo-web/fixture-reference-v4.json"
func launchChild() throws -> Process {
    let process = Process()
    process.executableURL = root.appendingPathComponent("projects/education-swift/.build/debug/LingoSeed")
    process.arguments = ["--fixture", root.appendingPathComponent(fixture).path, "--progress", progress.path, "--render-metadata", output.appendingPathComponent("window.json").path]
    process.standardOutput = FileHandle.nullDevice
    let log = try FileHandle(forWritingTo: childLog); try log.seekToEnd()
    process.standardError = log
    try process.run()
    return process
}
var child = try launchChild()
defer { if child.isRunning { child.terminate(); child.waitUntilExit() } }
var app = AXUIElementCreateApplication(child.processIdentifier)
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
func configureWindow() {
if let window = (attr(app, kAXWindowsAttribute) as? [AXUIElement])?.first {
    let metadata = try? Data(contentsOf: output.appendingPathComponent("window.json"))
    let value = metadata.flatMap { try? JSONSerialization.jsonObject(with: $0) as? [String: Any] }
    let frame = value?["window_points"] as? [Double]
    let rect = value?["content_rect_points"] as? [Double]
    let decoration = (frame?.last ?? 0) - (rect?.last ?? 0)
    var size = CGSize(width: 1200, height: 732 + decoration)
    AXUIElementSetAttributeValue(window, kAXSizeAttribute as CFString, AXValueCreate(.cgSize, &size)!)
}
Thread.sleep(forTimeInterval: 0.6)
AXUIElementSetAttributeValue(app, kAXFrontmostAttribute as CFString, kCFBooleanTrue)
if let window = (attr(app, kAXWindowsAttribute) as? [AXUIElement])?.first { AXUIElementPerformAction(window, kAXRaiseAction as CFString) }
Thread.sleep(forTimeInterval: 0.2)
}
configureWindow()
func capture(_ name: String) throws {
    var number: Int?
    let deadline = Date().addingTimeInterval(10)
    repeat {
        let info = CGWindowListCopyWindowInfo([.optionOnScreenOnly, .excludeDesktopElements], kCGNullWindowID) as? [[String: Any]] ?? []
        number = info.first(where: { ($0[kCGWindowOwnerPID as String] as? Int) == Int(child.processIdentifier) && ($0[kCGWindowLayer as String] as? Int) == 0 })?[kCGWindowNumber as String] as? Int
        if number == nil { Thread.sleep(forTimeInterval: 0.1) }
    } while number == nil && child.isRunning && Date() < deadline
    guard let number else { throw ProbeError(message: "No owned visible window") }
    let process = Process(); process.executableURL = URL(fileURLWithPath: "/usr/sbin/screencapture")
    process.arguments = ["-x", "-o", "-l", String(number), output.appendingPathComponent(name + ".png").path]
    try process.run(); process.waitUntilExit()
    precondition(process.terminationStatus == 0, "Owned window capture failed")
}
func observe() -> [String: Any] {
    let strings = Set(current().flatMap { node in
        [kAXValueAttribute, kAXTitleAttribute, kAXDescriptionAttribute].compactMap { attr(node, $0) as? String }.filter { !$0.isEmpty }
    })
    var elements: [String: Any] = [:]
    let metadata = (try? Data(contentsOf: output.appendingPathComponent("window.json"))).flatMap { try? JSONSerialization.jsonObject(with: $0) as? [String: Any] }
    let content = metadata?["content_rect_points"] as? [Double]
    var origin = CGPoint.zero
    if let window = (attr(app, kAXWindowsAttribute) as? [AXUIElement])?.first, let position = attr(window, kAXPositionAttribute) { AXValueGetValue(position as! AXValue, .cgPoint, &origin) }
    for node in current() {
        guard let id = attr(node, kAXIdentifierAttribute) as? String else { continue }
        var element: [String: Any] = ["role": attr(node, kAXRoleAttribute) as? String ?? "", "value": attr(node, kAXValueAttribute) as? String ?? ""]
        if let position = attr(node, kAXPositionAttribute), let size = attr(node, kAXSizeAttribute), let content {
            var point = CGPoint.zero; var dimensions = CGSize.zero
            AXValueGetValue(position as! AXValue, .cgPoint, &point); AXValueGetValue(size as! AXValue, .cgSize, &dimensions)
            element["rect"] = [point.x - origin.x - content[0], point.y - origin.y - content[1], dimensions.width, dimensions.height]
        }
        elements[id] = element
    }
    return ["accessible_text": strings.sorted(), "elements": elements]
}
var pointerActions: [[String: Any]] = []
func movePointer(to id: String) -> Bool {
    guard let node = current().first(where: { (attr($0, kAXIdentifierAttribute) as? String) == id }),
          let position = attr(node, kAXPositionAttribute), let size = attr(node, kAXSizeAttribute) else { return false }
    var point = CGPoint.zero; var dimensions = CGSize.zero
    AXValueGetValue(position as! AXValue, .cgPoint, &point); AXValueGetValue(size as! AXValue, .cgSize, &dimensions)
    let center = CGPoint(x: point.x + dimensions.width / 2, y: point.y + dimensions.height / 2)
    pointerActions.append(["control": id, "position": [point.x, point.y], "size": [dimensions.width, dimensions.height], "center": [center.x, center.y]])
    CGEvent(mouseEventSource: nil, mouseType: .mouseMoved, mouseCursorPosition: center, mouseButton: .left)?.post(tap: .cghidEventTap)
    Thread.sleep(forTimeInterval: 0.4)
    let ready = Date().addingTimeInterval(8)
    while current().isEmpty && child.isRunning && Date() < ready { Thread.sleep(forTimeInterval: 0.1) }
    pointerActions[pointerActions.count - 1]["child_running"] = child.isRunning
    pointerActions[pointerActions.count - 1]["window_count"] = (attr(app, kAXWindowsAttribute) as? [AXUIElement])?.count ?? -1
    let running = NSRunningApplication(processIdentifier: child.processIdentifier)
    pointerActions[pointerActions.count - 1]["active"] = running?.isActive
    pointerActions[pointerActions.count - 1]["hidden"] = running?.isHidden
    pointerActions[pointerActions.count - 1]["all_owned_windows"] = ((CGWindowListCopyWindowInfo(.optionAll, kCGNullWindowID) as? [[String: Any]]) ?? []).filter { ($0[kCGWindowOwnerPID as String] as? Int) == Int(child.processIdentifier) }.map { ["layer": $0[kCGWindowLayer as String] as Any, "bounds": $0[kCGWindowBounds as String] as Any, "onscreen": $0[kCGWindowIsOnscreen as String] as Any] }
    try? JSONSerialization.data(withJSONObject: pointerActions, options: [.prettyPrinted]).write(to: output.appendingPathComponent("pointer.json"))
    return true
}
var states = ["home": observe()]
try capture("home-window")
// A hover must include an outside-to-inside transition, including when the cursor
// starts over the same row left by a previous owned probe.
_ = movePointer(to: "course-entry")
let moved = movePointer(to: "nav-more")
let opened = current().contains { (attr($0, kAXIdentifierAttribute) as? String) == "more-settings" }
states["more-open"] = observe()
try capture("more-window")
let movedOut = movePointer(to: "course-entry")
let dismissed = opened && !current().contains { (attr($0, kAXIdentifierAttribute) as? String) == "more-settings" }
states["home"]?["interactions"] = ["more_hover_opened": moved && opened, "more_hover_dismissed": movedOut && dismissed]
struct ProbeError: Error { let message: String }
func waitFor(_ id: String, value: String? = nil) throws {
    let end = Date().addingTimeInterval(10)
    while Date() < end {
        if let node = current().first(where: { (attr($0, kAXIdentifierAttribute) as? String) == id }),
           value == nil || (attr(node, kAXValueAttribute) as? String) == value { return }
        Thread.sleep(forTimeInterval: 0.05)
    }
    throw ProbeError(message: "No observed control: " + id)
}
func press(_ id: String) throws {
    try waitFor(id)
    guard let node = current().first(where: { (attr($0, kAXIdentifierAttribute) as? String) == id }),
          AXUIElementPerformAction(node, kAXPressAction as CFString) == .success else { throw ProbeError(message: "Cannot press " + id) }
    Thread.sleep(forTimeInterval: 0.08)
}
func selectAppearance(_ title: String) throws {
    guard movePointer(to: "dark-mode"), let center = pointerActions.last?["center"] as? [CGFloat] else { throw ProbeError(message: "No owned appearance control") }
    let point = CGPoint(x: center[0], y: center[1])
    for kind in [CGEventType.leftMouseDown, .leftMouseUp] {
        CGEvent(mouseEventSource: nil, mouseType: kind, mouseCursorPosition: point, mouseButton: .left)?.post(tap: .cghidEventTap)
        Thread.sleep(forTimeInterval: 0.1)
    }
    let end = Date().addingTimeInterval(5)
    while Date() < end {
        let focused = attr(app, kAXFocusedUIElementAttribute).map { nodes($0 as! AXUIElement) } ?? []
        if let item = (current() + focused).first(where: { node in (attr(node, kAXRoleAttribute) as? String) == "AXMenuItem" && [kAXTitleAttribute, kAXValueAttribute, kAXDescriptionAttribute].contains { name in (attr(node, name) as? String) == title } }) {
            guard AXUIElementPerformAction(item, kAXPressAction as CFString) == .success else { throw ProbeError(message: "Cannot select appearance " + title) }
            try waitFor("dark-mode", value: title)
            return
        }
        Thread.sleep(forTimeInterval: 0.05)
    }
    throw ProbeError(message: "No actual appearance menu item " + title)
}
if opened {
    _ = movePointer(to: "nav-more")
    try press("more-settings")
    try waitFor("preferences-title")
    states["preferences"] = observe()
    try capture("preferences-window")
    try JSONSerialization.data(withJSONObject: states["preferences"]!, options: .prettyPrinted).write(to: output.appendingPathComponent("preferences-initial.json"))
    let switches = ["sound-effects", "animations", "motivational-messages", "listening-exercises"]
    for id in switches { try waitFor(id, value: "on"); try press(id); try waitFor(id, value: "off") }
    states["preferences-off"] = observe()
    try selectAppearance("On")
    states["preferences-dark"] = observe()
    try capture("preferences-dark-window")
    child.terminate(); child.waitUntilExit()
    child = try launchChild(); app = AXUIElementCreateApplication(child.processIdentifier)
    try waitFor("course-entry")
    configureWindow()
    if !current().contains(where: { (attr($0, kAXIdentifierAttribute) as? String) == "more-settings" }) { try press("nav-more") }
    try press("more-settings"); try waitFor("preferences-title")
    states["preferences-reopened"] = observe()
    var reloaded: [String: Bool] = [:]
    for id in switches {
        let value = current().first { (attr($0, kAXIdentifierAttribute) as? String) == id }.flatMap { attr($0, kAXValueAttribute) as? String }
        reloaded[id + "-off-persisted"] = value == "off"
    }
    reloaded["dark-mode-on-persisted"] = current().contains { (attr($0, kAXIdentifierAttribute) as? String) == "dark-mode" && (attr($0, kAXValueAttribute) as? String) == "On" }
    states["preferences-reopened"]?["interactions"] = reloaded
    try selectAppearance("Off")
    try selectAppearance("System Default")
    for id in switches { try press(id); try waitFor(id, value: "on") }
    try press("nav-learn")

}
var walkError: String?
if CommandLine.arguments.contains("--walk-course") {
    do {
        try press("nav-learn")
        let data = try Data(contentsOf: root.appendingPathComponent(fixture))
        let json = try JSONSerialization.jsonObject(with: data) as! [String: Any]
        let course = (json["data"] as! [String: Any])["candidate_course"] as! [String: Any]
        let lessons = course["lessons"] as! [[String: Any]]
        var capturedKinds = Set<String>()
        for (lessonIndex, definition) in lessons.enumerated() {
            let path = course["pathNodes"] as? [[String: Any]]
            let nodeIndex = path?.firstIndex { ($0["lessonIDs"] as? [String])?.contains(definition["id"] as! String) == true } ?? lessonIndex
            try press(nodeIndex == 0 ? "start-lesson" : "start-lesson-\(nodeIndex)")
            let questions = definition["questions"] as! [[String: Any]]
            for question in questions {
                try waitFor("question-title", value: question["prompt"] as? String)
                let key = question["id"] as! String
                states[key] = observe()
                if let kind = question["kind"] as? String, capturedKinds.insert(kind).inserted { try capture("question-" + kind) }
                switch question["kind"] as? String {
                case "matching":
                    for pair in question["pairs"] as! [[String: Any]] {
                        let id = pair["id"] as! String
                        try press("pair-left-" + id); try press("pair-right-" + id)
                    }
                case "word_tiles":
                    for word in question["answer_words"] as! [String] { try press("word-bank-" + word) }
                    try press("check")
                default:
                    try press("option-" + (question["answer"] as! String)); try press("check")
                }
                try waitFor("continue")
                states[key + "-feedback"] = observe()
                try press("continue")
            }
            try waitFor("lesson-complete")
            states["lesson-\(lessonIndex + 1)-complete"] = observe()
            try press("return-path")
            try waitFor("course-entry")
        }
    } catch { walkError = String(describing: error) }
}
let receipt: [String: Any] = ["kind": "owned_native_ax_observation", "states": states,
    "observed_at": ISO8601DateFormatter().string(from: Date()),
    "action": "Start isolated child, collect home, move pointer into More then out, optionally walk the observed course",
    "walk_error": walkError as Any? ?? NSNull(),
    "pointer_actions": pointerActions,
    "limitations": ["AX text and owned pointer actions; no visual/audio equivalence"]]
let data = try JSONSerialization.data(withJSONObject: receipt, options: [.prettyPrinted, .sortedKeys])
try data.write(to: output.appendingPathComponent("observed.json"), options: .withoutOverwriting)
print("Collected actual home and More text from owned child")
if child.isRunning { child.terminate(); child.waitUntilExit() }
if walkError != nil { exit(1) }

}
do { try main() } catch {
    FileHandle.standardError.write(Data(("Native observation failed: \(error)\n").utf8))
    exit(1)
}
