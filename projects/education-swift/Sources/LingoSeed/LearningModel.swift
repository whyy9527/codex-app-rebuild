import Foundation
import Observation
import LearningCore

@MainActor @Observable final class LearningModel {
    let course: Course
    let store: ProgressStore
    var progress: LearningProgress
    var lesson: Lesson?
    var confirmingExit = false
    var entryPending = false
    var error: String?
    var destination = "Learn"
    var preferences = LearningPreferences()
    private var preferencesURL: URL { store.url.appendingPathExtension("preferences.json") }
    func savePreferences() {
        audio.effectsEnabled = preferences.soundEffects
        do {
            try FileManager.default.createDirectory(at: preferencesURL.deletingLastPathComponent(), withIntermediateDirectories: true)
            try JSONEncoder().encode(preferences).write(to: preferencesURL, options: .atomic)
        } catch { self.error = "Preferences could not be saved." }
    }
    let audio = LearningAudio(resourceURL: { Bundle.module.url(forResource: $0, withExtension: nil, subdirectory: "Reference") })
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
        if course.interfaceLanguage != "zh" || option.audioResource != nil {
            audio.speak(option.text, language: course.speechLanguage, resource: option.audioResource)
        }
    }
    func addWord(_ id: String) {
        guard let word = lesson?.question.words.first(where: { $0.id == id }) else { return }
        lesson?.addWord(id)
        if let resource = word.audioResource { audio.speak(word.text, language: course.speechLanguage, resource: resource) }
        else { audio.play(.tap) }
    }
    func removeWord(_ id: String) { lesson?.removeWord(id); audio.play(.tap) }
    func match(_ id: String, left: Bool) {
        let previous = lesson?.feedback
        if left { lesson?.matchLeft(id) } else { lesson?.matchRight(id) }
        if !left, let pair = lesson?.question.pairs.first(where: { $0.id == id }), let resource = pair.audioResource {
            audio.speak(pair.right, language: course.speechLanguage, resource: resource)
        } else {
            audio.play(previous == nil && lesson?.feedback == true ? .correct : lesson?.matchingHint != nil ? .incorrect : .tap)
        }
    }
    func playQuestion(slow: Bool = false) {
        guard let question = lesson?.question else { return }
        audio.speak(question.hint ?? question.prompt, language: question.sourceLanguage ?? course.speechLanguage, resource: slow ? question.slowAudioResource : question.audioResource)
    }
    func playExample() {
        guard let question = lesson?.question, let example = question.example, let resource = question.exampleAudioResource else { return }
        audio.speak(example, language: course.speechLanguage, resource: resource)
    }
    func pronounce() {
        guard let lesson else { return }
        let option = lesson.question.options.first { $0.id == lesson.selected }
        let selected = option?.text
        let phrase = selected ?? lesson.question.hint ?? lesson.question.prompt
        audio.speak(phrase, language: selected != nil ? course.speechLanguage : (lesson.question.sourceLanguage ?? (lesson.question.kind == .wordTiles ? course.speechLanguage : "en-US")), resource: option?.audioResource ?? lesson.question.audioResource)
    }
    init(course: Course, store: ProgressStore) throws {
        self.course = course; self.store = store; progress = try store.load()
        if let data = try? Data(contentsOf: preferencesURL), let saved = try? JSONDecoder().decode(LearningPreferences.self, from: data) { preferences = saved }
        audio.effectsEnabled = preferences.soundEffects
        if let data = try? Data(contentsOf: audioPreferencesURL), let saved = try? JSONDecoder().decode(Bool.self, from: data) { muted = saved; audio.muted = saved }
    }
    func begin(_ index: Int) {
        guard progress.isUnlocked(course, index: index) else { return }
        lesson = Lesson(course: course, lessonIndex: index, hearts: progress.hearts)
        confirmingExit = false
        entryPending = course.lessons[index].entry != nil
        audio.play(.tap)
        playAutomaticPrompt()
    }
    func acceptEntry() { entryPending = false; playAutomaticPrompt() }
    private func playAutomaticPrompt() {
        guard !entryPending, lesson?.interlude == nil, let question = lesson?.question, ["translate", "listenTap", "dialogue", "orderTapComplete"].contains(question.sourceType ?? ""),
              course.interfaceLanguage != "zh" || question.audioResource != nil else { return }
        playQuestion()
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
        guard lesson?.feedback != nil || lesson?.interlude != nil else { return }
        let previousQuestion = lesson?.question.id
        let wasInterlude = lesson?.interlude != nil
        lesson?.advance()
        if let lesson, !lesson.complete, lesson.interlude == nil, (wasInterlude || lesson.question.id != previousQuestion) { playAutomaticPrompt() }
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
    func discardAttempt() { lesson = nil; confirmingExit = false; entryPending = false }
}
