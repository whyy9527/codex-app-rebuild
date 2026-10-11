// Collect actual text from an isolated child, without encoding expected copy.
import AppKit
import ApplicationServices
import Foundation
import CryptoKit

enum ObservationStop: Error { case afterQuestion(String) }
func main() throws {
let root = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
let output = URL(fileURLWithPath: CommandLine.arguments[1], relativeTo: root).standardizedFileURL
try FileManager.default.createDirectory(at: output, withIntermediateDirectories: true)
let progress = output.appendingPathComponent("progress.json")
precondition(!FileManager.default.fileExists(atPath: progress.path), "Use a fresh output directory")
if let seedIndex = CommandLine.arguments.firstIndex(of: "--seed-progress"), seedIndex + 1 < CommandLine.arguments.count {
    try Data(contentsOf: root.appendingPathComponent(CommandLine.arguments[seedIndex + 1])).write(to: progress, options: .withoutOverwriting)
}
let errorReview = CommandLine.arguments.contains("--exercise-error-review")
let reviewInstance = errorReview ? "error-review" : "current-review"
let childLog = output.appendingPathComponent("child.log")
FileManager.default.createFile(atPath: childLog.path, contents: nil)
let fixture = CommandLine.arguments.count > 2 ? CommandLine.arguments[2] : "projects/duolingo-web/fixture-reference-v6.json"
let candidateURL = root.appendingPathComponent("projects/education-swift/.build/debug/LingoSeed")
let candidateSHA = SHA256.hash(data: try Data(contentsOf: candidateURL)).map { String(format: "%02x", $0) }.joined()
let fixtureSHA = SHA256.hash(data: try Data(contentsOf: root.appendingPathComponent(fixture))).map { String(format: "%02x", $0) }.joined()
func launchChild() throws -> Process {
    let process = Process()
    process.executableURL = candidateURL
    process.arguments = ["--fixture", root.appendingPathComponent(fixture).path, "--progress", progress.path, "--render-metadata", output.appendingPathComponent("window.json").path]
    if let index = CommandLine.arguments.firstIndex(of: "--reference-color-scheme"), index + 1 < CommandLine.arguments.count {
        process.arguments! += ["--reference-color-scheme", CommandLine.arguments[index + 1]]
    }
    if CommandLine.arguments.contains("--exercise-general-listening-decline") {
        process.arguments! += ["--general-practice-fixture", root.appendingPathComponent("projects/duolingo-web/fixture-reference-en-zh-general-listening-decline-v1.json").path]
    }
    if CommandLine.arguments.contains("--exercise-current-review") || errorReview {
        process.arguments! += ["--general-practice-fixture", root.appendingPathComponent("projects/duolingo-web/fixture-reference-en-zh-" + reviewInstance + "-v1.json").path]
    }
    if CommandLine.arguments.contains("--exercise-speech-denied") { process.arguments! += ["--verify-speech-denied"] }
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
guard current().contains(where: { (attr($0, kAXIdentifierAttribute) as? String) == "course-entry" }) else { throw ProbeError(message: "No child home observed") }
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
        var element: [String: Any] = ["enabled": attr(node, kAXEnabledAttribute) as? Bool ?? false, "role": attr(node, kAXRoleAttribute) as? String ?? "", "value": attr(node, kAXValueAttribute) as? String ?? ""]
        // NSButton radios expose NSNumber, not text. Keep unknown values absent.
        if element["role"] as? String == "AXRadioButton",
           let value = attr(node, kAXValueAttribute) as? NSNumber,
           [0, 1].contains(value.intValue) {
            element["checked"] = value.intValue == 1
            element["numeric_value"] = value
        }
        if let position = attr(node, kAXPositionAttribute), let size = attr(node, kAXSizeAttribute), let content {
            var point = CGPoint.zero; var dimensions = CGSize.zero
            AXValueGetValue(position as! AXValue, .cgPoint, &point); AXValueGetValue(size as! AXValue, .cgSize, &dimensions)
            element["rect"] = [point.x - origin.x - content[0], point.y - origin.y - content[1], dimensions.width, dimensions.height]
        }
        elements[id] = element
    }
    return ["accessible_text": strings.sorted(), "elements": elements]
}
func bindCaptures(_ states: inout [String: [String: Any]], names: [String: String] = [:]) throws {
    if output.path.hasPrefix(root.path + "/"),
       let metadata = try JSONSerialization.jsonObject(with: Data(contentsOf: output.appendingPathComponent("window.json"))) as? [String: Any] {
        for stateName in Array(states.keys) {
            let filename = (names[stateName] ?? stateName) + ".png"
            let file = output.appendingPathComponent(filename)
            if FileManager.default.fileExists(atPath: file.path) {
                states[stateName]?["capture"] = ["path": String(file.path.dropFirst(root.path.count + 1)),
                    "content_rect_points": metadata["content_rect_points"]!, "backing_scale": metadata["backing_scale"]!,
                    "window_points": metadata["window_points"]!]
            }
        }
    }
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
func fillInput(_ value: String) throws {
    try waitFor("answer-input")
    let input = current().first { (attr($0, kAXIdentifierAttribute) as? String) == "answer-input" }!
    guard AXUIElementSetAttributeValue(input, kAXFocusedAttribute as CFString, kCFBooleanTrue) == .success else { throw ProbeError(message: "Cannot focus actual input") }
    // AX value assignment changes the field but can bypass SwiftUI's editing binding.
    // Send actual keyboard events to our isolated child instead.
    for down in [true, false] {
        let selectAll = CGEvent(keyboardEventSource: nil, virtualKey: 0, keyDown: down)!
        selectAll.flags = .maskCommand; selectAll.postToPid(child.processIdentifier)
    }
    for down in [true, false] { CGEvent(keyboardEventSource: nil, virtualKey: 51, keyDown: down)!.postToPid(child.processIdentifier) }
    if !value.isEmpty {
        let chars = Array(value.utf16)
        for down in [true, false] {
            let event = CGEvent(keyboardEventSource: nil, virtualKey: 0, keyDown: down)!
            chars.withUnsafeBufferPointer { event.keyboardSetUnicodeString(stringLength: chars.count, unicodeString: $0.baseAddress!) }
            event.postToPid(child.processIdentifier)
        }
    }
    try waitFor("answer-input", value: value)
    Thread.sleep(forTimeInterval: 0.15)
}

func captureGeneralCharacterFrames(_ key: String, _ stage: String, _ question: [String: Any]) throws {
    guard CommandLine.arguments.contains("--capture-character-frames"),
          let index = CommandLine.arguments.firstIndex(of: "--character-frame-resource"), index + 1 < CommandLine.arguments.count,
          question["characterResource"] as? String == CommandLine.arguments[index + 1],
          current().contains(where: { (attr($0, kAXIdentifierAttribute) as? String) == "question-character" }) else { return }
    for frame in 0..<12 { try capture(key + "-character-" + stage + "-\(frame)"); Thread.sleep(forTimeInterval: 0.15) }
}

var states = ["home": observe()]
try capture("home-window")
if CommandLine.arguments.contains("--observe-quests") {
    try press("nav-quests"); Thread.sleep(forTimeInterval: 0.5)
    states["quests"] = observe(); try capture("quests")
    if CommandLine.arguments.contains("--exercise-current-review") || errorReview {
        let practiceURL = root.appendingPathComponent("projects/duolingo-web/fixture-reference-en-zh-" + reviewInstance + "-v1.json")
        let data = try JSONSerialization.jsonObject(with: Data(contentsOf: practiceURL)) as! [String: Any]
        let course = (data["data"] as! [String: Any])["candidate_course"] as! [String: Any]
        let definition = (course["lessons"] as! [[String: Any]])[0]
        let questions = definition["questions"] as! [[String: Any]]
        let speech = (definition["deferredSpeech"] as! [[String: Any]])[0]
        var failure: String?
        func saveReviewState(_ key: String) throws { states[key] = observe(); try capture(key) }
        do {
            try press("quests-practice")
            for q in questions {
                let key = q["id"] as! String
                if key == speech["beforeQuestionID"] as? String {
                    try waitFor("speech-title", value: speech["id"] as? String)
                    try saveReviewState(reviewInstance+"-speech")
                    try press("speech-decline"); try waitFor("speech-closed"); try saveReviewState(reviewInstance+"-speech-declined")
                    try press("speech-continue")
                }
                try waitFor(q["kind"] as? String == "matching" ? "question-prompt" : "question-title",
                            value: q["kind"] as? String == "matching" ? key : q["prompt"] as? String)
                try saveReviewState(key)
                switch q["kind"] as? String {
                case "matching":
                    for p in q["pairs"] as! [[String: Any]] { try press("pair-left-" + (p["id"] as! String)); try press("pair-right-" + (p["id"] as! String)) }
                case "word_tiles":
                    for id in q["answer_words"] as! [String] { try press("word-bank-"+id) }
                    try press("check")
                case "text_entry": try fillInput(q["answer"] as! String); try press("check")
                default: try press("option-" + (errorReview && key == "error-review-q1" ? "1" : (q["answer"] as! String))); try press("check")
                }
                try waitFor("continue"); try saveReviewState(key+"-feedback"); try press("continue")
                if let intro = (definition["interludes"] as? [[String: Any]])?.first(where: { $0["afterQuestionID"] as? String == key }) {
                    let id = intro["id"] as! String
                    try waitFor("lesson-interlude", value: id); try saveReviewState(id); try press("interlude-continue")
                }
            }
            if errorReview {
                let intro = definition["reviewInterlude"] as! [String: Any]
                try waitFor("lesson-interlude", value: intro["id"] as? String)
                try saveReviewState("error-review-correction-intro"); try press("interlude-continue")
                let q = questions.first { $0["id"] as? String == "error-review-q1" }!
                try waitFor("question-title", value: q["prompt"] as? String)
                try saveReviewState("error-review-correction")
                try press("option-" + (q["answer"] as! String)); try press("check")
                try waitFor("continue"); try saveReviewState("error-review-correction-feedback"); try press("continue")
            }
            try waitFor("lesson-complete", value: errorReview ? "你莫不是特工？" : "完美！"); try saveReviewState(reviewInstance+"-result")
            try press("settlement-secondary"); try waitFor("result-review-title")
            try saveReviewState((errorReview ? "error" : "current")+"-practice-review-open")
            try press(errorReview ? "review-card-1" : "review-card-8"); try waitFor("result-review-answer")
            try saveReviewState(errorReview ? "error-practice-review-wrong-expanded" : "current-practice-review-speech-expanded")
            guard movePointer(to: "review-card-8") else { throw ProbeError(message: "Cannot target owned review scroll") }
            func scrollReview(_ amount: Int32, returned: Bool) throws {
                guard let event = CGEvent(scrollWheelEvent2Source: nil, units: .pixel, wheelCount: 1, wheel1: amount, wheel2: 0, wheel3: 0),
                      let point = CGEvent(source: nil)?.location,
                      NSRunningApplication(processIdentifier: child.processIdentifier)?.isActive == true else {
                    throw ProbeError(message: "No active owned review scroll target")
                }
                event.location = point; event.post(tap: .cghidEventTap)
                let deadline = Date().addingTimeInterval(8)
                while Date() < deadline {
                    let elements = observe()["elements"] as! [String: Any]
                    let rect = (elements["review-card-0"] as? [String: Any])?["rect"] as? [Double]
                    if let y = rect?[1], returned ? abs(y - 194) < 0.01 : y < 94 {
                        Thread.sleep(forTimeInterval: 0.5); return
                    }
                    Thread.sleep(forTimeInterval: 0.1)
                }
                throw ProbeError(message: "Actual review geometry did not change after scroll")
            }
            try scrollReview(-600, returned: false)
            try saveReviewState(reviewInstance+"-scrolled")
            if errorReview {
                try press("review-card-17"); try waitFor("result-review-answer")
                try saveReviewState("error-practice-review-correction-expanded")
            }
            try scrollReview(600, returned: true)
            try saveReviewState(reviewInstance+"-scroll-returned")
            if errorReview {
                for down in [true, false] {
                    CGEvent(keyboardEventSource: nil, virtualKey: 53, keyDown: down)?.postToPid(child.processIdentifier)
                }
                Thread.sleep(forTimeInterval: 0.5)
                var escaped = observe()
                let elements = escaped["elements"] as! [String: Any]
                let closed = elements["result-review-title"] == nil
                escaped["interactions"] = ["review_closed":closed]
                states["error-practice-review-escape"] = escaped
                try capture("error-practice-review-escape")
                if !closed { try press("result-review-close") }
            } else { try press("result-review-close") }
            try waitFor("lesson-complete")
            try saveReviewState(reviewInstance+"-closed")
            try press("settlement-retry"); try waitFor("question-prompt", value: reviewInstance+"-q0")
            try saveReviewState(reviewInstance+"-retried")
        } catch {
            failure = String(describing: error); states["failure-boundary"] = observe(); try? capture("failure-boundary")
        }
        try bindCaptures(&states, names: ["home":"home-window"])
        let receipt: [String: Any] = ["kind":"owned_native_ax_observation", "states":states,
            "candidate_binary_sha256":candidateSHA, "fixture_sha256":fixtureSHA,
            "general_fixture_sha256":SHA256.hash(data:try Data(contentsOf:practiceURL)).map{String(format:"%02x",$0)}.joined(),
            "observed_at":ISO8601DateFormatter().string(from:Date()), "failure":failure as Any,
            "action":errorReview ? "Actual first wrong coffee, corrected hot, distinct 18 cards, scroll, close and retry" : "Actual 16-question instance, speech decline, 17-card review, expanded speech, close and retry",
            "limitations":["Explicit observed instance; retry uses that instance, not verified adaptive selection; no acoustic equality proof"]]
        try JSONSerialization.data(withJSONObject:receipt, options:[.prettyPrinted,.sortedKeys]).write(to:output.appendingPathComponent("observed.json"))
        if let failure { throw ProbeError(message: failure) }
        return
    }
    if CommandLine.arguments.contains("--exercise-general-listening-decline") {
        let practiceURL = root.appendingPathComponent("projects/duolingo-web/fixture-reference-en-zh-general-listening-decline-v1.json")
        let fixtureData = try JSONSerialization.jsonObject(with: Data(contentsOf: practiceURL)) as! [String: Any]
        let practice = (fixtureData["data"] as! [String: Any])["candidate_course"] as! [String: Any]
        let definition = (practice["lessons"] as! [[String: Any]])[0]
        let replacements = definition["listeningDeclineReplacements"] as! [String: [String: Any]]
        var failure: String?
        let before = try Data(contentsOf: progress)
        func saveState(_ name: String) throws { states[name] = observe(); try capture(name) }
        do {
            try press("quests-practice")
            for original in definition["questions"] as! [[String: Any]] {
                var question = original
                if let replacement = replacements[original["id"] as! String] {
                    try waitFor("listening-decline")
                    try saveState("general-listening-decline-tap-before")
                    try press("listening-decline"); try waitFor("listening-declined", value: "听力题已跳过")
                    try saveState("general-listening-decline-tap-declined")
                    try press("listening-continue")
                    question = replacement
                    try waitFor("question-title", value: replacement["prompt"] as? String)
                    try saveState("general-listening-decline-after-tap")
                }
                if question["id"] as? String == "general-listening-decline-water-tea" {
                    try waitFor("speech-title", value: "general-listening-decline-speech")
                    try saveState("general-listening-decline-after-inserted")
                    try press("speech-decline"); try waitFor("speech-closed")
                    try saveState("general-listening-decline-speech-declined-with-text")
                    try press("speech-continue")
                }
                let key = question["id"] as! String
                try waitFor(question["kind"] as? String == "matching" ? "question-prompt" : "question-title", value: question["kind"] as? String == "matching" ? key : question["prompt"] as? String)
                try saveState(key)
                switch question["kind"] as? String {
                case "matching":
                    for pair in question["pairs"] as! [[String: Any]] { try press("pair-left-" + (pair["id"] as! String)); try press("pair-right-" + (pair["id"] as! String)) }
                case "word_tiles":
                    for word in question["answer_words"] as! [String] { try press("word-bank-" + word) }
                    try press("check")
                case "text_entry":
                    try fillInput(question["answer"] as! String); try press("check")
                default:
                    try press("option-" + (question["answer"] as! String)); try press("check")
                }
                try waitFor("continue")
                try saveState(key + "-feedback")
                if key == "general-listening-decline-coffee-milk" { try saveState("general-listening-decline-coffee-milk-feedback-detail") }
                try press("continue")
                if key == "general-listening-decline-goodbye" {
                    try waitFor("lesson-interlude", value: "general-listening-decline-challenge")
                    try saveState("general-listening-decline-challenge-interlude"); try press("interlude-continue")
                }
            }
            for (state, page) in zip(["general-listening-decline-result", "general-listening-decline-profile"], definition["settlement"] as! [[String: Any]]) {
                try waitFor(page["kind"] as? String == "result" ? "lesson-complete" : "settlement-title", value: page["title"] as? String)
                try saveState(state); try press("settlement-continue")
            }
            try waitFor("course-entry"); try saveState("general-listening-decline-home-return")
            try before.write(to: output.appendingPathComponent("progress-before.json"), options: .withoutOverwriting)
            try Data(contentsOf: progress).write(to: output.appendingPathComponent("progress-after.json"), options: .withoutOverwriting)
            child.terminate(); child.waitUntilExit(); child = try launchChild(); app = AXUIElementCreateApplication(child.processIdentifier)
            try waitFor("course-entry"); configureWindow(); try saveState("general-listening-decline-home-restart")
            try Data(contentsOf: progress).write(to: output.appendingPathComponent("progress-after-restart.json"), options: .withoutOverwriting)
        } catch {
            failure = String(describing: error); states["failure-boundary"] = observe(); try? capture("failure-boundary")
        }
        try bindCaptures(&states, names: ["home":"home-window"])
        let receipt: [String: Any] = ["kind":"owned_native_ax_observation", "states":states,
            "candidate_binary_sha256":candidateSHA, "fixture_sha256":fixtureSHA,
            "general_fixture_sha256":SHA256.hash(data:try Data(contentsOf:practiceURL)).map{String(format:"%02x",$0)}.joined(),
            "observed_at":ISO8601DateFormatter().string(from:Date()), "failure":failure as Any,
            "action":"Actual Quests entry, listening decline and replacement, speech decline, sixteen graded questions, result/profile/home and actual child restart",
            "limitations":["Fixed observed instance; adaptive selection and non-decline future remain unverified", "AX/PNG collection does not prove acoustic equality"]]
        try JSONSerialization.data(withJSONObject:receipt, options:[.prettyPrinted,.sortedKeys]).write(to:output.appendingPathComponent("observed.json"), options:.withoutOverwriting)
        print("Collected listening-decline native states: \(states.count); failure=\(failure ?? "none")")
        if failure != nil { exit(1) }
        return
    }
    if CommandLine.arguments.contains("--exercise-general-practice") {
        let practiceURL = root.appendingPathComponent("projects/duolingo-web/fixture-reference-en-zh-general-practice-v3.json")
        let practiceFixture = try JSONSerialization.jsonObject(with: Data(contentsOf: practiceURL)) as! [String: Any]
        let practice = (practiceFixture["data"] as! [String: Any])["candidate_course"] as! [String: Any]
        let definition = (practice["lessons"] as! [[String: Any]])[0]
        let questions = definition["questions"] as! [[String: Any]]
        let initialProgress = try Data(contentsOf: progress)
        var failure: String?
        do {
            try press("quests-practice")
            for question in questions {
                let key = question["id"] as! String
                if key == "general-practice-inserted" {
                    try waitFor("speech-title", value: "general-practice-speech")
                    states["general-practice-speech"] = observe(); try capture("general-practice-speech")
                    try press("speech-decline"); try waitFor("speech-closed")
                    states["general-practice-speech-declined"] = observe(); try capture("general-practice-speech-declined")
                    try press("speech-continue")
                }
                if key == "general-practice-q6" {
                    try waitFor("question-title", value: question["keyboardPrompt"] as? String)
                    states["general-practice-keyboard"] = observe(); try capture("general-practice-keyboard")
                    try clickOwnedControl("toggle-input-mode")
                }
                try waitFor(question["kind"] as? String == "matching" ? "question-prompt" : "question-title", value: question["kind"] as? String == "matching" ? key : question["prompt"] as? String)
                states[key] = observe(); try capture(key)
                if key == "general-practice-q0" { states["quests-practice-entry"] = states[key]; try capture("quests-practice-entry") }
                try captureGeneralCharacterFrames(key, "idle", question)
                switch question["kind"] as? String {
                case "matching":
                    let pairs = question["pairs"] as! [[String: Any]]
                    if key == "general-practice-q0", let index = CommandLine.arguments.firstIndex(of: "--general-practice-audio-recorder"), index + 1 < CommandLine.arguments.count {
                        let actions = output.appendingPathComponent("audio-actions.json")
                        try JSONSerialization.data(withJSONObject: pairs.flatMap { ["pair-left-" + ($0["id"] as! String), "pair-right-" + ($0["id"] as! String)] }).write(to: actions, options: .withoutOverwriting)
                        let recorder = Process()
                        recorder.executableURL = URL(fileURLWithPath: CommandLine.arguments[index + 1])
                        recorder.arguments = [String(child.processIdentifier), output.appendingPathComponent("general-practice.wav").path, "14", actions.path, "1.1"]
                        let log = output.appendingPathComponent("audio-recorder.log")
                        FileManager.default.createFile(atPath: log.path, contents: nil)
                        let handle = try FileHandle(forWritingTo: log)
                        recorder.standardOutput = handle; recorder.standardError = handle
                        try recorder.run(); recorder.waitUntilExit()
                        guard recorder.terminationStatus == 0 else { throw ProbeError(message: "Owned practice output recording failed; preserve log") }
                    } else {
                        for pair in pairs { try press("pair-left-" + (pair["id"] as! String)); try press("pair-right-" + (pair["id"] as! String)) }
                    }
                case "word_tiles":
                    for word in question["answer_words"] as! [String] { try press("word-bank-" + word) }
                    try press("check")
                case "text_entry":
                    try fillInput(key == "general-practice-replacement15" ? "water" : question["answer"] as! String)
                    try press("check")
                default:
                    try press("option-" + (question["answer"] as! String)); try press("check")
                }
                try waitFor("continue")
                states[key + "-feedback"] = observe(); try capture(key + "-feedback")
                try captureGeneralCharacterFrames(key, "feedback", question)
                if key == "general-practice-replacement15" {
                    try Data(contentsOf: progress).write(to: output.appendingPathComponent("progress-after-wrong.json"), options: .withoutOverwriting)
                }
                try press("continue")
                if key == "general-practice-q12" {
                    try waitFor("lesson-interlude", value: "general-practice-challenge-intro")
                    states["general-practice-challenge-intro"] = observe(); try capture("general-practice-challenge-intro")
                    try press("interlude-continue")
                }
            }
            try waitFor("lesson-interlude", value: "general-practice-review-intro")
            states["general-practice-review-intro"] = observe(); try capture("general-practice-review-intro")
            try press("interlude-continue"); try waitFor("review-label")
            states["general-practice-review"] = observe(); try capture("general-practice-review")
            try fillInput(questions.last!["answer"] as! String); try press("check"); try waitFor("continue")
            states["general-practice-review-feedback"] = observe(); try capture("general-practice-review-feedback")
            try press("continue")
            for (state, page) in zip(["general-practice-result", "general-practice-heart-reward", "general-practice-profile"], definition["settlement"] as! [[String: Any]]) {
                try waitFor(page["kind"] as? String == "result" ? "lesson-complete" : "settlement-title", value: page["title"] as? String)
                states[state] = observe(); try capture(state)
                try Data(contentsOf: progress).write(to: output.appendingPathComponent(state + "-progress.json"), options: .withoutOverwriting)
                try press("settlement-continue")
            }
            try waitFor("course-entry")
            states["general-practice-home-return"] = observe(); try capture("general-practice-home-return")
            child.terminate(); child.waitUntilExit()
            child = try launchChild(); app = AXUIElementCreateApplication(child.processIdentifier)
            try waitFor("course-entry"); configureWindow()
            states["general-practice-home-restart"] = observe(); try capture("general-practice-home-restart")
            try initialProgress.write(to: output.appendingPathComponent("progress-before.json"), options: .withoutOverwriting)
        } catch {
            failure = String(describing: error)
            states["failure-boundary"] = observe(); try? capture("failure-boundary")
        }
        try bindCaptures(&states, names: ["home":"home-window"])
        let receipt: [String: Any] = ["kind":"owned_native_ax_observation", "states":states,
            "candidate_binary_sha256":candidateSHA, "fixture_sha256":fixtureSHA,
            "general_fixture_sha256":SHA256.hash(data:try Data(contentsOf:practiceURL)).map{String(format:"%02x",$0)}.joined(),
            "observed_at":ISO8601DateFormatter().string(from:Date()), "failure":failure as Any,
            "action":"Actual Quests entry, independent practice, one wrong, correction, result/reward/profile and real child restart",
            "limitations":["Observed finite source instance; adaptive selection, complete pixels and acoustic equality remain unproven"]]
        try JSONSerialization.data(withJSONObject:receipt, options:[.prettyPrinted,.sortedKeys]).write(to:output.appendingPathComponent("observed.json"))
        if let failure { throw ProbeError(message: failure) }
        return
    }
    if CommandLine.arguments.contains("--exercise-quests-practice") {
        try press("quests-practice"); try waitFor("question-prompt", value: "general-practice-q0")
        states["quests-practice-entry"] = observe(); try capture("quests-practice-entry")
        try press("exit"); try waitFor("course-entry")
        states["quests-practice-exited"] = observe(); try capture("quests-practice-exited")
    }
    try bindCaptures(&states, names: ["home":"home-window"])
    let receipt: [String: Any] = ["kind":"owned_native_ax_observation", "states":states,
        "candidate_binary_sha256":candidateSHA, "fixture_sha256":fixtureSHA,
        "observed_at":ISO8601DateFormatter().string(from:Date()),
        "action":"Actual quests navigation and optional practice entry; no driver pass flags",
        "limitations":["Actual AX and owned captures; this entry-only run does not verify the full independent practice"]]
    try JSONSerialization.data(withJSONObject:receipt, options:[.prettyPrinted,.sortedKeys]).write(to:output.appendingPathComponent("observed.json"))
    return
}
if CommandLine.arguments.contains("--observe-pronunciation") {
    try press("nav-pronunciation")
    Thread.sleep(forTimeInterval: 0.5)
    states["en-zh-pronunciation"] = observe()
    try capture("pronunciation-window")
    if CommandLine.arguments.contains("--exercise-pronunciation-card-press") {
        guard movePointer(to: "pronunciation-sound-1"),
              NSRunningApplication(processIdentifier: child.processIdentifier)?.isActive == true,
              let center = pointerActions.last?["center"] as? [CGFloat] else {
            throw ProbeError(message: "Cannot target owned pronunciation card")
        }
        let point = CGPoint(x: center[0], y: center[1])
        guard let down = CGEvent(mouseEventSource: nil, mouseType: .leftMouseDown, mouseCursorPosition: point, mouseButton: .left),
              let up = CGEvent(mouseEventSource: nil, mouseType: .leftMouseUp, mouseCursorPosition: point, mouseButton: .left) else {
            throw ProbeError(message: "Cannot create owned card pointer events")
        }
        var held = false
        defer { if held { up.post(tap: .cghidEventTap) } }
        states["pronunciation-card-hover"] = observe(); try capture("pronunciation-card-hover")
        down.post(tap: .cghidEventTap); held = true
        Thread.sleep(forTimeInterval: 0.2)
        states["pronunciation-card-pressed"] = observe(); try capture("pronunciation-card-pressed")
        up.post(tap: .cghidEventTap); held = false
        Thread.sleep(forTimeInterval: 0.2)
        states["pronunciation-card-released"] = observe(); try capture("pronunciation-card-released")
    }
    if let index = CommandLine.arguments.firstIndex(of: "--pronunciation-audio-recorder"), index + 1 < CommandLine.arguments.count {
        let actions = output.appendingPathComponent("audio-actions.json")
        try JSONSerialization.data(withJSONObject: ["pronunciation-sound-0"]).write(to: actions)
        let recorder = Process()
        recorder.executableURL = URL(fileURLWithPath: CommandLine.arguments[index + 1])
        recorder.arguments = [String(child.processIdentifier), output.appendingPathComponent("phoneme.wav").path, "6", actions.path]
        let audioLog = output.appendingPathComponent("audio-recorder.log")
        FileManager.default.createFile(atPath: audioLog.path, contents: nil)
        let handle = try FileHandle(forWritingTo: audioLog)
        recorder.standardOutput = handle; recorder.standardError = handle
        try recorder.run(); recorder.waitUntilExit()
        precondition(recorder.terminationStatus == 0, "Owned pronunciation audio recording failed; preserve log")
    }
    if CommandLine.arguments.contains("--walk-pronunciation-practice") {
        try press("pronunciation-start"); try waitFor("question-prompt", value: "p0")
        var visits: [String: Int] = [:]
        let practiceURL = root.appendingPathComponent("projects/education-swift/Sources/LingoSeed/Resources/Reference/pronunciation-practice.json")
        let practice = try JSONSerialization.jsonObject(with: Data(contentsOf: practiceURL)) as! [String: Any]
        let definitions = practice["lessons"] as! [[String: Any]]
        let saved = try JSONSerialization.jsonObject(with: Data(contentsOf: progress)) as! [String: Any]
        let completed = ((saved["completedLessons"] as? [String: [String]])?[practice["id"] as! String]) ?? []
        guard let lessonDefinition = definitions.first(where: { !completed.contains($0["id"] as! String) }) else { throw ProbeError(message: "No compiled uncompleted practice") }
        let questions = lessonDefinition["questions"] as! [[String: Any]]
        for _ in 0..<30 {
            if current().contains(where: { (attr($0, kAXIdentifierAttribute) as? String) == "practice-settlement-title" }) { break }
            if current().contains(where: { (attr($0, kAXIdentifierAttribute) as? String) == "speech-decline" }) {
                states["pronunciation-speech-before"] = observe(); try capture("practice-speech-before")
                if CommandLine.arguments.contains("--exercise-speech-denied") {
                    try press("speech-record"); Thread.sleep(forTimeInterval: 0.3)
                    try JSONSerialization.data(withJSONObject: observe(), options: [.prettyPrinted, .sortedKeys]).write(to: output.appendingPathComponent("speech-denial-probe.json"))
                    try capture("speech-denial-probe"); try waitFor("speech-denied-title")
                    states["pronunciation-speech-denied"] = observe(); try capture("practice-speech-denied")
                    try press("speech-denied-close"); try waitFor("speech-record")
                    states["pronunciation-speech-denied-closed"] = observe(); try capture("practice-speech-denied-closed")
                }
                try press("speech-decline"); states["pronunciation-speech-declined"] = observe()
                try press("speech-continue"); continue
            }
            guard let prompt = current().first(where: { (attr($0, kAXIdentifierAttribute) as? String) == "question-prompt" }),
                  let id = attr(prompt, kAXValueAttribute) as? String,
                  let question = questions.first(where: { $0["id"] as? String == id }) else { throw ProbeError(message: "No actual practice question") }
            let repeatCount = visits[id, default: 0]; visits[id] = repeatCount + 1
            let state = "pronunciation-" + id + (repeatCount > 0 ? "-review" : "")
            var before = observe()
            let check = current().first { (attr($0, kAXIdentifierAttribute) as? String) == "check" }
            before["interactions"] = ["check_enabled": check.flatMap { attr($0, kAXEnabledAttribute) as? Bool } ?? false]
            states[state + "-before"] = before; try capture(state + "-before")
            if question["sourceType"] as? String == "sameDifferent" {
                try press("practice-play-0"); try press("practice-play-1")
            }
            if question["kind"] as? String == "matching" {
                if CommandLine.arguments.contains("--exercise-practice-quit"), repeatCount == 0 {
                    let preserved = try JSONSerialization.data(withJSONObject: observe(), options: [.sortedKeys])
                    try press("exit"); try waitFor("practice-quit-title")
                    states["pronunciation-practice-exit-confirm"] = observe(); try capture("practice-quit-confirm")
                    try press("practice-quit-cancel"); try waitFor("question-prompt", value: id)
                    let resumed = observe()
                    guard try JSONSerialization.data(withJSONObject: resumed, options: [.sortedKeys]) == preserved else { throw ProbeError(message: "Practice cancellation changed actual AX question/control state") }
                    states["pronunciation-practice-exit-cancelled"] = resumed; try capture("practice-quit-cancelled")
                }
                for pair in question["pairs"] as! [[String: Any]] {
                    let pairID = pair["id"] as! String
                    try press("pair-left-" + pairID); try press("pair-right-" + pairID)
                }
            } else {
                let options = question["options"] as! [[String: Any]]
                let answer = repeatCount > 0 ? question["answer"] as! String : options[0]["id"] as! String
                try press("option-" + answer)
                states[state + "-selected"] = observe(); try capture(state + "-selected")
                try press("check")
            }
            states[state + "-feedback"] = observe(); try capture(state + "-feedback")
            try press("continue")
        }
        states["pronunciation-settlement"] = observe(); try capture("practice-settlement")
        try press("settlement-continue"); states["pronunciation-profile"] = observe(); try capture("practice-profile")
        try press("settlement-continue"); states["pronunciation-returned"] = observe(); try capture("practice-returned")
        if CommandLine.arguments.contains("--verify-pronunciation-restart") {
            let savedAfter = try JSONSerialization.jsonObject(with: Data(contentsOf: progress)) as! [String: Any]
            let completedAfter = ((savedAfter["completedLessons"] as? [String: [String]])?[practice["id"] as! String]) ?? []
            guard completedAfter.contains(lessonDefinition["id"] as! String),
                  let next = definitions.first(where: { !completedAfter.contains($0["id"] as! String) }),
                  let nextQuestion = (next["questions"] as? [[String: Any]])?.first else { throw ProbeError(message: "Practice completion not persisted or next unavailable") }
            child.terminate(); child.waitUntilExit(); child = try launchChild(); app = AXUIElementCreateApplication(child.processIdentifier)
            try waitFor("course-entry"); configureWindow(); try press("nav-pronunciation"); try press("pronunciation-start")
            try waitFor("question-prompt", value: (nextQuestion["id"] as! String))
            let nextState = observe()
            let strings = nextState["accessible_text"] as? [String] ?? []
            // The real controls must expose the next source options, rather than merely another p0 identifier.
            for (optionIndex, option) in (nextQuestion["options"] as! [[String: Any]]).enumerated() {
                try waitFor("option-" + (option["id"] as! String))
                guard current().contains(where: { node in
                    [kAXTitleAttribute,kAXValueAttribute,kAXDescriptionAttribute].contains { name in (attr(node,name) as? String) == "\(optionIndex + 1) \(option["text"] as! String)" }
                }) else { throw ProbeError(message: "Next practice option text missing after restart") }
            }
            states["pronunciation-restarted-next"] = nextState; try capture("practice-restarted-next")
            try JSONSerialization.data(withJSONObject: ["completed":completedAfter,"next_lesson":next["id"]!,"observed_text_count":strings.count], options: [.prettyPrinted,.sortedKeys]).write(to: output.appendingPathComponent("restart.json"), options:.withoutOverwriting)
        } else { try press("pronunciation-start"); try waitFor("question-prompt", value: "p0") }
        if CommandLine.arguments.contains("--exercise-practice-quit") {
            // An option selected but not graded must still leave directly, as observed.
            guard let option = current().first(where: { (attr($0, kAXIdentifierAttribute) as? String)?.hasPrefix("option-") == true }),
                  let optionID = attr(option, kAXIdentifierAttribute) as? String else { throw ProbeError(message: "No actual fresh practice option") }
            try press(optionID)
        }
        try press("exit"); try waitFor("pronunciation-start")
        states["pronunciation-exit-returned"] = observe(); try capture("practice-exit-returned")
        if CommandLine.arguments.contains("--exercise-practice-quit") {
            let savedBefore = try Data(contentsOf: progress)
            let savedValue = try JSONSerialization.jsonObject(with: savedBefore) as! [String: Any]
            let finished = ((savedValue["completedLessons"] as? [String: [String]])?[practice["id"] as! String]) ?? []
            guard let remaining = definitions.first(where: { !finished.contains($0["id"] as! String) }),
                  let pending = remaining["questions"] as? [[String: Any]], pending.count >= 3,
                  let firstWrong = (pending[0]["options"] as? [[String: Any]])?.first(where: { $0["id"] as? String != pending[0]["answer"] as? String }),
                  let secondWrong = (pending[1]["options"] as? [[String: Any]])?.first(where: { $0["id"] as? String != pending[1]["answer"] as? String }) else { throw ProbeError(message: "Observed next practice choices unavailable") }
            try press("pronunciation-start"); try waitFor("question-prompt", value: "p0")
            try press("option-" + (firstWrong["id"] as! String)); try press("check"); try waitFor("continue"); try press("continue")
            try press("option-" + (secondWrong["id"] as! String)); try press("check"); try waitFor("continue"); try press("continue")
            try press("exit"); try waitFor("pronunciation-start")
            states["pronunciation-practice-wrong-exit-returned"] = observe(); try capture("practice-wrong-exit-returned")
            guard try Data(contentsOf: progress) == savedBefore else { throw ProbeError(message: "Wrong-only abandoned practice changed saved progress") }
            try press("pronunciation-start"); try waitFor("question-prompt", value: "p0")
            try press("option-" + (pending[0]["answer"] as! String)); try press("check"); try waitFor("continue"); try press("continue")
            try press("option-" + (secondWrong["id"] as! String)); try press("check"); try waitFor("continue"); try press("continue")
            try press("exit"); try waitFor("practice-quit-title")
            states["pronunciation-practice-abandon-confirm"] = observe(); try capture("practice-abandon-confirm")
            try press("practice-quit-confirm"); try waitFor("pronunciation-start")
            states["pronunciation-practice-abandoned"] = observe(); try capture("practice-abandoned")
            guard try Data(contentsOf: progress) == savedBefore else { throw ProbeError(message: "Abandoned practice changed saved completion or main progress") }
            try press("pronunciation-start"); try waitFor("question-prompt", value: "p0")
            states["pronunciation-practice-abandoned-restarted"] = observe(); try capture("practice-abandoned-restarted")
            try press("exit"); try waitFor("pronunciation-start")
        }
    }
    try bindCaptures(&states, names: ["home":"home-window", "en-zh-pronunciation":"pronunciation-window",
        "pronunciation-speech-before":"practice-speech-before", "pronunciation-speech-denied":"practice-speech-denied",
        "pronunciation-speech-denied-closed":"practice-speech-denied-closed"])
    let receipt: [String: Any] = ["kind": "owned_native_ax_observation", "states": states,
        "candidate_binary_sha256": candidateSHA, "fixture_sha256": fixtureSHA,
        "observed_at": ISO8601DateFormatter().string(from: Date()),
        "action": "Actual native pronunciation navigation click; collect page without supplying pass flags",
        "limitations": ["AX and owned capture; no audio or visual equivalence"]]
    try JSONSerialization.data(withJSONObject: receipt, options: [.prettyPrinted, .sortedKeys]).write(to: output.appendingPathComponent("observed.json"), options: .withoutOverwriting)
    if child.isRunning { child.terminate(); child.waitUntilExit() }
    return
}
if CommandLine.arguments.contains("--observe-home-popover") {
    try press("start-lesson"); try waitFor("start-lesson-confirm")
    var popover = observe()
    let start = current().first { (attr($0, kAXIdentifierAttribute) as? String) == "start-lesson-confirm" }
    popover["interactions"] = ["start_enabled": start.flatMap { attr($0, kAXEnabledAttribute) as? Bool } ?? false]
    states["en-zh-home-popover"] = popover; try capture("home-popover-window")
    try press("start-lesson")
}

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
func clickOwnedControl(_ id: String) throws {
    // Preserve failed AXPress attempts separately. Use one real screen click
    // for TextEditor transitions, and verify the resulting state without retry.
    try waitFor(id)
    guard child.isRunning, let node = current().first(where: { (attr($0, kAXIdentifierAttribute) as? String) == id }),
          attr(node, kAXEnabledAttribute) as? Bool == true,
          let position = attr(node, kAXPositionAttribute), let size = attr(node, kAXSizeAttribute) else { throw ProbeError(message: "No enabled owned control: " + id) }
    var point = CGPoint.zero; var dimensions = CGSize.zero
    AXValueGetValue(position as! AXValue, .cgPoint, &point); AXValueGetValue(size as! AXValue, .cgSize, &dimensions)
    let center = CGPoint(x: point.x + dimensions.width / 2, y: point.y + dimensions.height / 2)
    pointerActions.append(["control": id, "center": [center.x, center.y], "delivery": "single screen click in owned frontmost window"])
    for type in [CGEventType.leftMouseDown, .leftMouseUp] {
        CGEvent(mouseEventSource: nil, mouseType: type, mouseCursorPosition: center, mouseButton: .left)?.post(tap: .cghidEventTap)
        Thread.sleep(forTimeInterval: 0.1)
    }
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
var stoppedAtQuestion: String?
if CommandLine.arguments.contains("--walk-course") {
    do {
        try press("nav-learn")
        let data = try Data(contentsOf: root.appendingPathComponent(fixture))
        let json = try JSONSerialization.jsonObject(with: data) as! [String: Any]
        let course = (json["data"] as! [String: Any])["candidate_course"] as! [String: Any]
        let lessons = course["lessons"] as! [[String: Any]]
        var capturedKinds = Set<String>()
        let startIndex = CommandLine.arguments.firstIndex(of: "--start-lesson-index").map { Int(CommandLine.arguments[$0 + 1])! } ?? 0
        precondition(lessons.indices.contains(startIndex), "Start lesson must exist in the explicit fixture")
        for (lessonIndex, definition) in lessons.enumerated().dropFirst(startIndex) {
            let path = course["pathNodes"] as? [[String: Any]]
            let nodeIndex = path?.firstIndex { ($0["lessonIDs"] as? [String])?.contains(definition["id"] as! String) == true } ?? lessonIndex
            try press(nodeIndex == 0 ? "start-lesson" : "start-lesson-\(nodeIndex)")
            if course["interfaceLanguage"] as? String == "zh" {
                if lessonIndex == 1 {
                    var popover = observe()
                    let start = current().first { (attr($0, kAXIdentifierAttribute) as? String) == "start-lesson-confirm" }
                    popover["interactions"] = ["start_enabled": start.flatMap { attr($0, kAXEnabledAttribute) as? Bool } ?? false]
                    states["en-zh-home-popover"] = popover; try capture("after-first-popover-window")
                }
                try press("start-lesson-confirm")
            }
            if let entry = definition["entry"] as? [String: String] {
                try waitFor("lesson-entry", value: entry["id"])
                states[entry["id"]!] = observe(); try capture(entry["id"]! + "-window")
                try press("lesson-entry-start")
            }
            if let initial = definition["initialInterlude"] as? [String: String] {
                try waitFor("lesson-interlude", value: initial["id"])
                states[initial["id"]!] = observe(); try capture(initial["id"]! + "-window")
                try press("interlude-continue")
            }
            let questions = definition["questions"] as! [[String: Any]]
            let wrongFirst = CommandLine.arguments.contains("--english-first-wrong") && course["interfaceLanguage"] as? String == "zh" && lessonIndex == 0
            let fifthErrors = CommandLine.arguments.contains("--english-fifth-mixed-errors") && definition["id"] as? String == "lesson-5"
            for question in questions {
                if let speeches = definition["deferredSpeech"] as? [[String: String]], let speech = speeches.first(where: { $0["beforeQuestionID"] == question["id"] as? String }) {
                    let id = speech["id"]!
                    try waitFor("speech-title", value: id)
                    states[id] = observe(); try capture(id + "-before")
                    try press("speech-decline"); try waitFor("speech-closed")
                    states[id + "-closed"] = observe(); states[id + "-declined"] = observe(); try capture(id + "-closed")
                    if id.hasSuffix("-speech") { states[String(id.dropLast(7)) + "-declined"] = observe() }
                    try press("speech-continue")
                }
                let modeProbe = CommandLine.arguments.contains("--exercise-input-modes") && question["keyboardAnswer"] != nil
                if modeProbe {
                    if let hint = question["hint"] as? String { try waitFor("question-hint", value: hint) }
                    let full = current().first { (attr($0, kAXIdentifierAttribute) as? String) == "answer-input" }.flatMap { attr($0, kAXRoleAttribute) as? String } == "AXTextArea"
                    try waitFor("question-title", value: (full ? question["keyboardPrompt"] : question["prompt"]) as? String)
                    try waitFor("check")
                } else { try waitFor("question-title", value: question["prompt"] as? String) }
                let key = question["id"] as! String
                var initialObservation = observe()
                if modeProbe {
                    let input = current().first { (attr($0, kAXIdentifierAttribute) as? String) == "answer-input" }
                    let full = input.flatMap { attr($0, kAXRoleAttribute) as? String } == "AXTextArea"
                    let empty = input == nil ? question["kind"] as? String == "word_tiles" : input.flatMap { attr($0, kAXValueAttribute) as? String } == ""
                    let enabled = current().first { (attr($0, kAXIdentifierAttribute) as? String) == "check" }.flatMap { attr($0, kAXEnabledAttribute) as? Bool } ?? false
                    initialObservation["interactions"] = ["keyboard_mode": full, "empty_input": empty, "check_enabled": enabled]
                }
                states[key] = initialObservation
                states[key + "-initial"] = initialObservation
                if CommandLine.arguments.contains("--capture-character-frames"), current().contains(where: { (attr($0, kAXIdentifierAttribute) as? String) == "question-character" }) {
                    for frame in 0..<12 { try capture(key + "-character-idle-\(frame)"); Thread.sleep(forTimeInterval: 0.15) }
                }
                if let kind = (question["sourceType"] ?? question["kind"]) as? String, capturedKinds.insert(kind).inserted { try capture("question-" + kind) }
                if course["interfaceLanguage"] as? String == "zh" { try capture(key + "-before") }
                let skipProbe = CommandLine.arguments.contains("--exercise-source-skip") && key == "en-zh-l7-q0"
                if skipProbe {
                    let oldHearts = current().first { (attr($0, kAXIdentifierAttribute) as? String) == "hearts" }.flatMap { attr($0, kAXValueAttribute) as? String }
                    try press("skip"); try waitFor("continue")
                    let newHearts = current().first { (attr($0, kAXIdentifierAttribute) as? String) == "hearts" }.flatMap { attr($0, kAXValueAttribute) as? String }
                    var skipped = observe()
                    skipped["interactions"] = ["hearts_unchanged": oldHearts != nil && oldHearts == newHearts]
                    states[key + "-skipped"] = skipped; try capture(key + "-skipped")
                } else if CommandLine.arguments.contains("--exercise-input-modes"), let answer = question["keyboardAnswer"] as? String {
                    func enabled(_ id: String) -> Bool {
                        current().first { (attr($0, kAXIdentifierAttribute) as? String) == id }.flatMap { attr($0, kAXEnabledAttribute) as? Bool } ?? false
                    }
                    func recordMode(_ phase: String, expectedInput: String) throws {
                        var value = observe()
                        let actual = current().first { (attr($0, kAXIdentifierAttribute) as? String) == "answer-input" }.flatMap { attr($0, kAXValueAttribute) as? String }
                        let inputMatches = phase == "returned" && question["kind"] as? String == "word_tiles" ? actual == nil : actual == expectedInput
                        value["interactions"] = ["check_enabled": enabled("check"), "input_matches": inputMatches]
                        states[key + "-" + phase] = value; try capture(key + "-" + phase)
                        if question["sourceObservationPhase"] as? String == phase { states[key] = value }
                    }
                    let full = current().first { (attr($0, kAXIdentifierAttribute) as? String) == "answer-input" }.flatMap { attr($0, kAXRoleAttribute) as? String } == "AXTextArea"
                    if full {
                        try fillInput(answer)
                    } else {
                        try clickOwnedControl("toggle-input-mode"); try recordMode("empty", expectedInput: "")
                        try fillInput(answer); try recordMode("filled", expectedInput: answer)
                        try clickOwnedControl("toggle-input-mode"); try recordMode("returned", expectedInput: "")
                        try clickOwnedControl("toggle-input-mode"); try recordMode("reopened", expectedInput: answer)
                    }
                    try clickOwnedControl("check")
                } else {
                switch question["kind"] as? String {
                case "text_entry":
                    func enabled(_ id: String) -> Bool {
                        current().first { (attr($0, kAXIdentifierAttribute) as? String) == id }.flatMap { attr($0, kAXEnabledAttribute) as? Bool } ?? false
                    }
                    var interactions = ["empty_check_disabled": !enabled("check")]
                    try fillInput("Te"); interactions["nonempty_check_enabled"] = enabled("check")
                    try fillInput(""); interactions["cleared_check_disabled"] = !enabled("check")
                    if CommandLine.arguments.contains("--exercise-typed-review") {
                        let heartsBefore = current().first { (attr($0, kAXIdentifierAttribute) as? String) == "hearts" }.flatMap { attr($0, kAXValueAttribute) as? String }.flatMap(Int.init)
                        try fillInput("cold"); try press("check"); try waitFor("continue")
                        let heartsAfter = current().first { (attr($0, kAXIdentifierAttribute) as? String) == "hearts" }.flatMap { attr($0, kAXValueAttribute) as? String }.flatMap(Int.init)
                        var wrong = observe(); wrong["interactions"] = ["heart_decremented_once": heartsBefore != nil && heartsAfter == heartsBefore! - 1, "submitted_input_locked": !enabled("answer-input")]
                        states[key + "-wrong"] = wrong; try capture(key + "-wrong")
                        try press("continue"); try waitFor("review-label")
                        var review = observe()
                        review["interactions"] = ["review_input_empty": current().first { (attr($0, kAXIdentifierAttribute) as? String) == "answer-input" }.flatMap { attr($0, kAXValueAttribute) as? String } == ""]
                        states[key + "-review"] = review; try capture(key + "-review")
                        try fillInput("HOT")
                    } else { try fillInput(fifthErrors && key == "en-zh-l5-q7" ? "cold" : question["answer"] as! String) }
                    var observed = observe(); observed["interactions"] = interactions
                    states[key + "-filled"] = observed; try capture(key + "-filled")
                    try press("check"); try waitFor("continue")
                    observed = observe(); observed["interactions"] = ["submitted_input_locked": !enabled("answer-input")]
                    states[key + "-submitted"] = observed
                case "matching":
                    let pairs = question["pairs"] as! [[String: Any]]
                    func value(_ id: String) -> String? { current().first { (attr($0, kAXIdentifierAttribute) as? String) == id }.flatMap { attr($0, kAXValueAttribute) as? String } }
                    func enabled(_ id: String) -> Bool { current().first { (attr($0, kAXIdentifierAttribute) as? String) == id }.flatMap { attr($0, kAXEnabledAttribute) as? Bool } ?? false }
                    let declineLesson = CommandLine.arguments.firstIndex(of: "--decline-lesson-id").map { CommandLine.arguments[$0 + 1] }
                    if CommandLine.arguments.contains("--exercise-listening-decline"), question["listeningDecline"] != nil, declineLesson == nil || declineLesson == definition["id"] as? String {
                        let before = value("hearts")
                        try press("listening-decline"); try waitFor("listening-declined")
                        var observed = observe()
                        observed["interactions"] = ["hearts_unchanged": before != nil && value("hearts") == before,
                            "all_pairs_disabled": pairs.allSatisfy { pair in
                                let id = pair["id"] as! String
                                return !enabled("pair-left-" + id) && !enabled("pair-right-" + id)
                            }]
                        states[key + "-declined"] = observed; try capture(key + "-declined")
                        try press("listening-continue")
                        continue
                    }
                    if (CommandLine.arguments.contains("--exercise-wrong-audio-pair") || (fifthErrors && key == "en-zh-l5-q8")), question["sourceType"] as? String == "listenMatch", pairs.count > 1 {
                        let a = pairs[0]["id"] as! String, b = pairs[1]["id"] as! String
                        let before = Int(value("hearts") ?? "")
                        try press("pair-left-" + a); try press("pair-right-" + b)
                        var observed = observe()
                        observed["interactions"] = ["heart_decremented_once": before != nil && Int(value("hearts") ?? "") == before! - 1,
                            "unmatched_remains_available": enabled("pair-left-" + a) && enabled("pair-right-" + b),
                            "wrong_pair_marked_incorrect": value("pair-left-" + a) == "incorrect" && value("pair-right-" + b) == "incorrect"]
                        states[key + "-wrong"] = observed; try capture(key + "-wrong")
                    }
                    for (index, pair) in pairs.enumerated() {
                        let id = pair["id"] as! String
                        try press("pair-left-" + id); try press("pair-right-" + id)
                        if index == 0 {
                            var observed = observe(); observed["interactions"] = ["matched_pair_disabled": !enabled("pair-left-" + id) && !enabled("pair-right-" + id)]
                            states[key + "-paired-first"] = observed; try capture(key + "-paired-first")
                        }
                    }
                case "word_tiles":
                    if CommandLine.arguments.contains("--exercise-duplicate-words") {
                        let words = question["words"] as! [[String: Any]]
                        let grouped = Dictionary(grouping: words, by: { $0["text"] as! String })
                        if let duplicates = grouped.values.first(where: { $0.count > 1 }) {
                            let first = duplicates[0]["id"] as! String, second = duplicates[1]["id"] as! String
                            func enabled(_ id: String) -> Bool? {
                                current().first { (attr($0, kAXIdentifierAttribute) as? String) == id }.flatMap { attr($0, kAXEnabledAttribute) as? Bool }
                            }
                            try press("word-bank-" + first)
                            var observed = observe()
                            observed["interactions"] = ["used_occurrence_disabled": enabled("word-bank-" + first) == false,
                                "other_occurrence_available": enabled("word-bank-" + second) == true]
                            states[key + "-duplicate-first"] = observed
                            try press("word-bank-" + second); try press("selected-word-" + first)
                            observed = observe()
                            observed["interactions"] = ["removed_occurrence_available": enabled("word-bank-" + first) == true,
                                "other_occurrence_still_selected": enabled("word-bank-" + second) == false]
                            states[key + "-duplicate-undo-one"] = observed; try capture(key + "-duplicate-undo-one")
                            try press("selected-word-" + second)
                            observed = observe()
                            observed["interactions"] = ["empty_answer_disabled": enabled("check") == false,
                                "both_occurrences_available": enabled("word-bank-" + first) == true && enabled("word-bank-" + second) == true]
                            states[key + "-duplicate-empty"] = observed
                        }
                    }
                    for word in question["answer_words"] as! [String] { try press("word-bank-" + word) }
                    try press("check")
                default:
                    if wrongFirst && question["id"] as? String == "en-zh-q0" {
                        let options = question["options"] as! [[String: Any]]
                        let wrong = options.first { $0["text"] as? String == "sugar" }!["id"] as! String
                        try press("option-" + wrong)
                    } else { try press("option-" + (question["answer"] as! String)) }
                    try press("check")
                }
                }
                try waitFor("continue")
                var feedbackObservation = observe()
                if CommandLine.arguments.contains("--exercise-input-modes"), question["keyboardAnswer"] != nil {
                    let actual = current().first { (attr($0, kAXIdentifierAttribute) as? String) == "feedback" }.flatMap { attr($0, kAXValueAttribute) as? String }
                    feedbackObservation["interactions"] = ["accepted": actual == "correct"]
                }
                states[key + "-feedback"] = feedbackObservation
                if CommandLine.arguments.contains("--capture-character-frames"), current().contains(where: { (attr($0, kAXIdentifierAttribute) as? String) == "question-character" }) {
                    for frame in 0..<12 { try capture(key + "-character-feedback-\(frame)"); Thread.sleep(forTimeInterval: 0.15) }
                }
                if course["interfaceLanguage"] as? String == "zh" { try capture(key + "-feedback") }
                if CommandLine.arguments.contains("--exercise-feedback-actions") {
                    func value(_ id: String) -> String? { current().first { (attr($0, kAXIdentifierAttribute) as? String) == id }.flatMap { attr($0, kAXValueAttribute) as? String } }
                    func enabled(_ id: String) -> Bool { current().first { (attr($0, kAXIdentifierAttribute) as? String) == id }.flatMap { attr($0, kAXEnabledAttribute) as? Bool } ?? false }
                    func checked(_ id: String) -> Bool { current().first { (attr($0, kAXIdentifierAttribute) as? String) == id }.flatMap { attr($0, kAXValueAttribute) as? NSNumber }?.intValue == 1 }
                    for (action, name) in [("easy", "easy"), ("hard", "hard"), ("hard", "deselected")] {
                        try press("feedback-" + action)
                        var facts = observe(); facts["interactions"] = ["easy_selected": value("feedback-easy") == "selected", "hard_selected": value("feedback-hard") == "selected"]
                        states[key + "-" + name] = facts; try capture(key + "-" + name)
                    }
                    try press("feedback-report"); try waitFor("report-submit")
                    var facts = observe(); facts["interactions"] = ["submit_disabled": !enabled("report-submit")]
                    states[key + "-report-open"] = facts; try capture(key + "-report-open")
                    try press("report-reason-5")
                    facts = observe(); facts["interactions"] = ["other_checked": checked("report-reason-5"), "submit_enabled": enabled("report-submit")]
                    states[key + "-report-other"] = facts; try capture(key + "-report-other")
                    try press("report-reason-0")
                    facts = observe(); facts["interactions"] = ["both_checked": checked("report-reason-5") && checked("report-reason-0")]
                    states[key + "-report-two"] = facts; try capture(key + "-report-two")
                    try press("report-close")
                    facts = observe(); facts["interactions"] = ["report_closed": !current().contains { (attr($0, kAXIdentifierAttribute) as? String) == "report-submit" }]
                    states[key + "-report-closed"] = facts; try capture(key + "-report-closed")
                    try press("feedback-report"); try waitFor("report-submit")
                    facts = observe(); facts["interactions"] = ["submit_disabled": !enabled("report-submit"), "all_unchecked": (0..<6).allSatisfy { !checked("report-reason-\($0)") }]
                    states[key + "-report-reopened"] = facts; try capture(key + "-report-reopened")
                    try press("report-close")
                }
                if let i = CommandLine.arguments.firstIndex(of: "--stop-after-question-id"), i + 1 < CommandLine.arguments.count,
                   CommandLine.arguments[i + 1] == key { throw ObservationStop.afterQuestion(key) }
                if CommandLine.arguments.contains("--exercise-input-modes"), question["keyboardAnswer"] != nil {
                    try clickOwnedControl("continue")
                } else { try press("continue") }
                if let interludes = definition["interludes"] as? [[String: String]], let interlude = interludes.first(where: { $0["afterQuestionID"] == key }) {
                    try waitFor("lesson-interlude", value: interlude["id"])
                    states[interlude["id"]!] = observe(); try capture(interlude["id"]! + "-window")
                    try press("interlude-continue")
                }
            }
            if CommandLine.arguments.contains("--exercise-source-skip"), let first = questions.first, first["id"] as? String == "en-zh-l7-q0" {
                let intro = definition["reviewInterlude"] as! [String: String]
                try waitFor("lesson-interlude", value: intro["id"])
                states[intro["id"]!] = observe(); try capture(intro["id"]! + "-window")
                try press("interlude-continue"); try waitFor("review-label")
                try waitFor("question-title", value: first["prompt"] as? String)
                if let hint = first["hint"] as? String {
                    guard current().contains(where: { node in [kAXValueAttribute, kAXTitleAttribute, kAXDescriptionAttribute].contains { attr(node, $0) as? String == hint } }) else { throw ProbeError(message: "Review original hint not observed") }
                }
                states["en-zh-l7-review-q0"] = observe(); try capture("en-zh-l7-review-q0")
                var skipped = states["en-zh-l7-q0-skipped"]!
                var facts = skipped["interactions"] as! [String: Bool]
                facts["original_question_reviewed"] = current().contains { (attr($0, kAXIdentifierAttribute) as? String) == "review-label" }
                skipped["interactions"] = facts; states["en-zh-l7-q0-skipped"] = skipped
                for word in first["answer_words"] as! [String] { try press("word-bank-" + word) }
                try press("check"); try waitFor("continue")
                states["en-zh-l7-review-q0-feedback"] = observe(); try capture("en-zh-l7-review-q0-feedback")
                try press("continue")
            }
            if fifthErrors {
                let intro = definition["reviewInterlude"] as! [String: String]
                try waitFor("lesson-interlude", value: intro["id"])
                states[intro["id"]!] = observe(); try capture(intro["id"]! + "-window")
                try press("interlude-continue"); try waitFor("review-label")
                states["en-zh-l5-q7-review"] = observe(); try capture("en-zh-l5-q7-review")
                try fillInput("HOT"); try press("check"); try waitFor("continue")
                states["en-zh-l5-q7-review-feedback"] = observe(); try capture("en-zh-l5-q7-review-feedback")
                try press("continue")
            }
            if wrongFirst {
                let first = questions[0]
                try waitFor("question-title", value: first["prompt"] as? String)
                states["en-zh-review-question"] = observe(); try capture("en-zh-review-question")
                try press("option-" + (first["answer"] as! String)); try press("check"); try waitFor("continue")
                states["en-zh-review-feedback"] = observe(); try capture("en-zh-review-feedback"); try press("continue")
            }
            try waitFor("lesson-complete")
            states["lesson-\(lessonIndex + 1)-complete"] = observe()
            if course["interfaceLanguage"] as? String == "zh" { states["en-zh-l\(lessonIndex + 1)-complete"] = observe() }
            if let pages = definition["settlement"] as? [[String: Any]] {
                for (pageIndex, page) in pages.enumerated() {
                    let id = page["id"] as! String
                    try waitFor(page["kind"] as? String == "result" ? "lesson-complete" : "settlement-title", value: page["title"] as? String)
                    var observed = observe()
                    let secondary = page["secondaryLabel"] as? String
                    let actionAvailable = secondary.map { label in current().contains { node in
                        let role = attr(node, kAXRoleAttribute) as? String
                        let text = [kAXTitleAttribute, kAXValueAttribute, kAXDescriptionAttribute].compactMap { attr(node, $0) as? String }
                        return [kAXButtonRole, "AXLink"].contains(role ?? "") && text.contains(label) && (attr(node, kAXEnabledAttribute) as? Bool != false)
                    } } ?? false
                    observed["interactions"] = ["secondary_action_available": actionAvailable]
                    states[id] = observed; try capture(id + "-window")
                    try press("settlement-continue")
                    if pageIndex + 1 < pages.count { try waitFor("settlement-title", value: pages[pageIndex + 1]["title"] as? String) }
                    else { try waitFor("course-entry") }
                    observed["interactions"] = ["secondary_action_available": actionAvailable, "next_state_reached": true]
                    states[id] = observed
                }
            } else { try press("return-path") }
            try waitFor("course-entry")
            states["home-after-lesson-\(lessonIndex + 1)"] = observe()
            if course["interfaceLanguage"] as? String == "zh" { states["en-zh-l\(lessonIndex + 1)-home"] = observe() }
            try capture("home-after-lesson-\(lessonIndex + 1)-window")
            if lessonIndex == 3 && definition["settlement"] != nil {
                try press("start-lesson")
                var observed = observe()
                observed["interactions"] = ["practice_action_available": current().contains { (attr($0, kAXRoleAttribute) as? String) == kAXButtonRole && (attr($0, kAXTitleAttribute) as? String) == "练习 +5 经验" },
                    "legendary_action_available": current().contains { (attr($0, kAXRoleAttribute) as? String) == kAXButtonRole && (attr($0, kAXTitleAttribute) as? String) == "晋升传奇 +40 经验" }]
                states["en-zh-completed-popover"] = observed; try capture("en-zh-completed-popover-window")
                try press("start-lesson"); try press("start-lesson-1")
                observed = observe()
                let start = current().first { (attr($0, kAXIdentifierAttribute) as? String) == "start-lesson-confirm" }
                observed["interactions"] = ["start_enabled": start.flatMap { attr($0, kAXEnabledAttribute) as? Bool } ?? false]
                states["en-zh-next-popover"] = observed; try capture("en-zh-next-popover-window")
                try press("start-lesson-1")
            }
            if lessonIndex == 0 && course["interfaceLanguage"] as? String == "zh" {
                // The frozen English home reference follows the first lesson.
                // Keep initial facts; compare the same state from this run.
                states["home-initial"] = states["home"]
                states["home"] = observe(); try capture("after-first-home-window")
            }
        }
        // Reference Guidebook was observed after the first node's three lessons.
        try press("open-guide"); try waitFor("guide-title")
        states["guidebook"] = observe(); try capture("guidebook-window")
        try press("close-guide"); try waitFor("course-entry")
    } catch ObservationStop.afterQuestion(let id) { stoppedAtQuestion = id }
    catch {
        walkError = String(describing: error)
        states["walk-failure"] = observe()
        try? capture("walk-failure-window")
    }
}
// Read the actual rendered seventh result, not a core-state prediction or score formula.
if var skipped = states["en-zh-l7-q0-skipped"],
   let result = states["en-zh-l7-result"]?["accessible_text"] as? [String],
   result.contains("100%"), result.contains("你练习全对，无错完成本单元") {
    var facts = skipped["interactions"] as? [String: Bool] ?? [:]
    facts["settlement_mistake"] = false
    skipped["interactions"] = facts; states["en-zh-l7-q0-skipped"] = skipped
}
let receipt: [String: Any] = ["kind": "owned_native_ax_observation", "states": states,
    "candidate_binary_sha256": candidateSHA, "fixture_sha256": fixtureSHA,
    "observed_at": ISO8601DateFormatter().string(from: Date()),
    "action": "Start isolated child, collect home, move pointer into More then out, optionally walk the observed course",
    "walk_error": walkError as Any? ?? NSNull(),
    "stopped_at_question": stoppedAtQuestion as Any? ?? NSNull(),
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
