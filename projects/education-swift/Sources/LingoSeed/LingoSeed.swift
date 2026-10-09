import SwiftUI
import AppKit
import Observation
import LearningCore

@MainActor @Observable final class LearningModel {
    let course: Course
    let store: ProgressStore
    var progress: LearningProgress
    var lesson: Lesson?
    var confirmingExit = false
    var error: String?
    init(course: Course, store: ProgressStore) throws {
        self.course = course
        self.store = store
        progress = try store.load()
    }
    func advance() {
        lesson?.advance()
        if lesson?.complete == true {
            progress.completedCourses.insert(course.id)
            do { try store.save(progress) } catch { self.error = "Progress could not be saved. Please try again." }
        }
    }
}

@MainActor final class AppDelegate: NSObject, NSApplicationDelegate {
    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.regular)
        NSApp.activate(ignoringOtherApps: true)
    }
    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { true }
}

@main struct LingoSeedApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) var delegate
    @State private var model: LearningModel?
    @State private var startupError: String?
    init() {
        func argument(_ name: String) -> String? {
            guard let index = CommandLine.arguments.firstIndex(of: name), index + 1 < CommandLine.arguments.count else { return nil }
            return CommandLine.arguments[index + 1]
        }
        let fixture = URL(fileURLWithPath: argument("--fixture") ?? "projects/duolingo-web/fixture-v1.json")
        let progress = argument("--progress").map { URL(fileURLWithPath: $0) }
            ?? FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0].appendingPathComponent("LingoSeed/progress.json")
        do { _model = State(initialValue: try LearningModel(course: Course.readFixture(fixture), store: ProgressStore(url: progress))) }
        catch { _startupError = State(initialValue: "Unable to open the course or saved progress. Check the supplied files before restarting.") }
    }
    var body: some Scene {
        WindowGroup("LingoSeed") {
            if let model { LearningView(model: model) }
            else { ContentUnavailableView("Course unavailable", systemImage: "book.closed", description: Text(startupError ?? "Unknown error")) }
        }
        .defaultSize(width: 940, height: 700)
    }
}

struct LearningView: View {
    @Bindable var model: LearningModel
    private let ink = Color(red: 0.09, green: 0.22, blue: 0.25)
    private let accent = Color(red: 0.0, green: 0.43, blue: 0.40)
    var body: some View {
        VStack(alignment: .leading, spacing: 28) {
            HStack {
                Label("LingoSeed", systemImage: "leaf.fill").font(.title2.bold()).foregroundStyle(accent)
                Spacer()
                Text("A little practice. A new possibility.").foregroundStyle(.secondary)
            }
            Divider()
            if let lesson = model.lesson {
                HStack {
                    Button("Close lesson", systemImage: "xmark") { model.confirmingExit = true }.accessibilityIdentifier("quit")
                    Spacer()
                    Text("♥ \(lesson.hearts)").font(.title3.bold()).foregroundStyle(.pink)
                        .accessibilityIdentifier("hearts").accessibilityValue(String(lesson.hearts))
                }
                if model.confirmingExit {
                    VStack(alignment: .leading, spacing: 22) {
                        Text("Leave this lesson?").font(.largeTitle.bold()).accessibilityIdentifier("exit-title")
                        Text("Your finished lessons are safe. This unfinished attempt will be discarded.").foregroundStyle(.secondary)
                        Button("Keep learning") { model.confirmingExit = false }.buttonStyle(.borderedProminent).tint(accent).accessibilityIdentifier("cancel-quit")
                        Button("End session") { model.lesson = nil; model.confirmingExit = false }.accessibilityIdentifier("confirm-quit")
                    }.frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .leading)
                } else if lesson.complete {
                    VStack(alignment: .leading, spacing: 20) {
                        Image(systemName: "checkmark.seal.fill").font(.system(size: 64)).foregroundStyle(accent)
                        Text("Lesson complete").font(.largeTitle.bold()).accessibilityIdentifier("lesson-complete")
                        Text("You made time for your next step.").foregroundStyle(.secondary)
                        Button("Back to your path") { model.lesson = nil }.buttonStyle(.borderedProminent).tint(accent)
                    }.frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .leading)
                } else {
                    Text(lesson.reviewing ? "ONE MORE LOOK" : "EVERYDAY ENGLISH").font(.caption.bold()).foregroundStyle(accent)
                    Text(lesson.question.prompt).font(.system(size: 32, weight: .bold)).accessibilityIdentifier("question-title")
                    VStack(spacing: 12) {
                        ForEach(lesson.question.options) { option in
                            Button { model.lesson?.choose(option.id) } label: {
                                HStack {
                                    Image(systemName: lesson.selected == option.id ? "checkmark.circle.fill" : "circle")
                                    Text(option.text).font(.title3.weight(.medium))
                                    Spacer()
                                }.padding(18).frame(maxWidth: .infinity)
                            }
                            .buttonStyle(.bordered).tint(lesson.selected == option.id ? accent : ink)
                            .disabled(lesson.feedback != nil)
                            .accessibilityIdentifier("option-" + option.id)
                            .accessibilityValue(lesson.selected == option.id ? "selected" : "not selected")
                        }
                    }
                    Spacer(minLength: 0)
                    if let correct = lesson.feedback {
                        Text(correct ? "Correct!" : "Correct answer: \(lesson.question.options.first { $0.id == lesson.question.answer }!.text)")
                            .font(.title3.bold()).foregroundStyle(correct ? accent : .orange)
                            .accessibilityIdentifier("feedback").accessibilityValue(correct ? "correct" : "incorrect")
                        Text(lesson.question.explanation).foregroundStyle(.secondary)
                        Button("Continue") { model.advance() }.buttonStyle(.borderedProminent).tint(accent).accessibilityIdentifier("continue")
                    } else {
                        Button("Check answer") { model.lesson?.submit() }.buttonStyle(.borderedProminent).tint(accent)
                            .disabled(!lesson.canSubmit).accessibilityIdentifier("check")
                    }
                }
            } else {
                Text("Your learning path").font(.system(size: 38, weight: .bold)).accessibilityIdentifier("course-entry")
                Text("Build confidence, one small conversation at a time.").font(.title3).foregroundStyle(.secondary)
                VStack(alignment: .leading, spacing: 18) {
                    Label(model.course.title, systemImage: "sun.max.fill").font(.title.bold()).foregroundStyle(accent)
                    Text(model.progress.completedCourses.contains(model.course.id) ? "Completed · Ready to practice again" : "Lesson 1 · Greetings and gratitude")
                    Button(model.progress.completedCourses.contains(model.course.id) ? "Practice again" : "Start lesson") { model.lesson = Lesson(course: model.course) }
                        .buttonStyle(.borderedProminent).tint(accent).controlSize(.large).accessibilityIdentifier("start-lesson")
                }.padding(30).frame(maxWidth: .infinity, alignment: .leading).background(.white, in: RoundedRectangle(cornerRadius: 22))
                Spacer()
                Text("Small steps grow into everyday skills.").foregroundStyle(.secondary)
            }
            if let error = model.error { Text(error).foregroundStyle(.red) }
        }
        .padding(40).frame(minWidth: 720, minHeight: 620)
        .foregroundStyle(ink).background(Color(red: 0.96, green: 0.97, blue: 0.94))
    }
}
