import Foundation
import Observation
import LearningCore

@MainActor @Observable final class LearningModel {
    let course: Course
    let store: ProgressStore
    var progress: LearningProgress
    var lesson: Lesson?
    var confirmingExit = false
    var error: String?
    var destination = "Learn"
    var showingGuide = false
    let audio = LearningAudio()
    var muted = false
    private var audioPreferencesURL: URL { store.url.appendingPathExtension("audio.json") }
    func toggleMute() {
        muted.toggle(); audio.muted = muted
        do {
            try FileManager.default.createDirectory(at: audioPreferencesURL.deletingLastPathComponent(), withIntermediateDirectories: true)
            try JSONEncoder().encode(muted).write(to: audioPreferencesURL, options: .atomic)
        } catch { self.error = "Sound preference could not be saved." }
    }
    func choose(_ id: String) {
        guard let lesson, lesson.feedback == nil, let option = lesson.question.options.first(where: { $0.id == id }) else { return }
        self.lesson?.choose(id)
        audio.speak(option.text)
    }
    func addWord(_ id: String) { lesson?.addWord(id); audio.play(.tap) }
    func removeWord(_ id: String) { lesson?.removeWord(id); audio.play(.tap) }
    func match(_ id: String, left: Bool) {
        let previous = lesson?.feedback
        if left { lesson?.matchLeft(id) } else { lesson?.matchRight(id) }
        audio.play(previous == nil && lesson?.feedback == true ? .correct : lesson?.matchingHint != nil ? .incorrect : .tap)
    }
    func pronounce() {
        guard let lesson else { return }
        let phrase = lesson.question.options.first { $0.id == lesson.selected }?.text ?? lesson.question.prompt
        audio.speak(phrase)
    }
    init(course: Course, store: ProgressStore) throws {
        self.course = course; self.store = store; progress = try store.load()
        if let data = try? Data(contentsOf: audioPreferencesURL), let saved = try? JSONDecoder().decode(Bool.self, from: data) { muted = saved; audio.muted = saved }
    }
    func begin(_ index: Int) {
        guard progress.isUnlocked(course, index: index) else { return }
        lesson = Lesson(course: course, lessonIndex: index, hearts: progress.hearts)
        confirmingExit = false
        audio.play(.tap)
    }
    func submit() {
        guard lesson?.canSubmit == true, lesson?.feedback == nil else { return }
        lesson?.submit()
        audio.play(lesson?.feedback == true ? .correct : .incorrect)
        if let hearts = lesson?.hearts, hearts != progress.hearts {
            progress.hearts = hearts
            save()
        }
    }
    func advance() {
        guard lesson?.feedback != nil else { return }
        lesson?.advance()
        if let lesson, lesson.complete {
            audio.play(.complete)
            progress.markCompleted(course, index: lesson.lessonIndex)
            save()
        }
    }
    func save() {
        do { try store.save(progress); error = nil }
        catch { self.error = "Progress could not be saved. Please try again." }
    }
    func discardAttempt() { lesson = nil; confirmingExit = false }
}
