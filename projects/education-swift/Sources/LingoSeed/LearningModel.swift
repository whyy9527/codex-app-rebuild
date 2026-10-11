import Foundation
import Observation
import LearningCore

@MainActor @Observable final class LearningModel {
    let course: Course
    let store: ProgressStore
    var progress: LearningProgress
    var lesson: Lesson?
    enum SessionKind { case course, pronunciation, generalPractice }
    var sessionKind = SessionKind.course
    var isPronunciationPractice: Bool { sessionKind == .pronunciation }
    var isGeneralPractice: Bool { sessionKind == .generalPractice }
    var pronunciationExitNeedsConfirmation: Bool {
        guard sessionKind != .course, let lesson else { return false }
        // Source probes: all-wrong exits directly; one correct then a wrong
        // still confirms. Use earned answers, not attempts or current streak.
        if lesson.reviewing || lesson.complete { return lesson.definition.questions.count > lesson.review.count }
        return lesson.feedback == true || lesson.position > lesson.review.filter { $0 < lesson.position }.count
    }
    var confirmingExit = false
    var feedbackDifficulty: String?
    var reportingQuestion = false
    var selectedReportReasons = Set<Int>()
    func rateDifficulty(_ value: String) {
        guard lesson?.feedback != nil || lesson?.listeningDeclined == true || lesson?.speechDeclined == true else { return }
        feedbackDifficulty = feedbackDifficulty == value ? nil : value
    }
    func openQuestionReport() { selectedReportReasons = []; reportingQuestion = true }
    func closeQuestionReport() { reportingQuestion = false; selectedReportReasons = [] }
    var entryPending = false
    var settlement: SettlementFlow?
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
    let speechCapture = LearningSpeech()
    func startSpeech() { guard lesson?.deferredSpeech != nil, lesson?.speechDeclined == false else { return }; Task { await speechCapture.start() } }
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
        if (!isGeneralPractice || lesson.question.sourceType != "assist"), course.interfaceLanguage != "zh" || option.audioResource != nil {
            audio.speak(option.text, language: course.speechLanguage, resource: option.audioResource)
        }
    }
    func addWord(_ id: String) {
        guard let word = lesson?.question.words.first(where: { $0.id == id }) else { return }
        lesson?.addWord(id)
        if let resource = word.audioResource { audio.speak(word.text, language: course.speechLanguage, resource: resource) }
        else if !isGeneralPractice { audio.play(.tap) }
    }
    func toggleInputMode() { lesson?.toggleInputMode() }
    func enterText(_ text: String) { lesson?.enterText(text) }
    func removeWord(_ id: String) { lesson?.removeWord(id); if !isGeneralPractice { audio.play(.tap) } }
    func match(_ id: String, left: Bool) {
        let previous = lesson?.feedback
        let matchedBefore = lesson?.matchedPairs.count ?? 0
        let mistakesBefore = lesson?.mistakesMade ?? 0
        if left { lesson?.matchLeft(id) } else { lesson?.matchRight(id) }
        if isGeneralPractice, let lesson {
            if left, let pair = lesson.question.pairs.first(where: { $0.id == id }), let resource = pair.audioResource {
                audio.speak(pair.right, language: course.speechLanguage, resource: resource)
            }
            if lesson.matchedPairs.count > matchedBefore, let resources = lesson.question.matchedAudioResources, resources.indices.contains(matchedBefore) {
                audio.playReferenceEffect(resources[matchedBefore])
            }
            if previous == nil && lesson.feedback == true { audio.playReferenceEffect(lesson.question.correctFeedbackAudioResource) }
            if lesson.mistakesMade > mistakesBefore { audio.playReferenceEffect(lesson.question.incorrectFeedbackAudioResource) }
        } else if isPronunciationPractice {
            if left, let pair = lesson?.question.pairs.first(where: { $0.id == id }), let resource = pair.audioResource {
                audio.speak(pair.right, language: course.speechLanguage, resource: resource)
            }
            // Missing original speech is left unavailable, never replaced by a synthetic tap or voice.
        } else if (lesson?.question.sourceType == "listenMatch" ? left : !left), let pair = lesson?.question.pairs.first(where: { $0.id == id }), let resource = pair.audioResource {
            audio.speak(pair.right, language: course.speechLanguage, resource: resource)
        } else {
            audio.play(previous == nil && lesson?.feedback == true ? .correct : (lesson?.matchingHint != nil || lesson?.incorrectMatch != nil) ? .incorrect : .tap)
        }
        if sessionKind == .course, let hearts = lesson?.hearts, hearts != progress.hearts { progress.hearts = hearts; save() }
    }
    func playQuestion(slow: Bool = false, practicePart: Int = 0) {
        if let speech = lesson?.deferredSpeech {
            audio.speak(speech.phrase, language: course.speechLanguage, resource: speech.audioResource)
            return
        }
        guard let question = lesson?.question else { return }
        if let resources = question.practiceAudioResources, resources.indices.contains(practicePart) {
            audio.speak(question.prompt, resource: resources[practicePart]); return
        }
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
    func beginPronunciation() {
        guard let url = Bundle.module.url(forResource: "pronunciation-practice", withExtension: "json", subdirectory: "Reference"),
              let data = try? Data(contentsOf: url) else { error = "无法打开练习。"; return }
        let practice: Course
        do { practice = try JSONDecoder().decode(Course.self, from: data) }
        catch { self.error = "无法打开练习。"; NSLog("Practice definition decode failed: %@", String(describing: error)); return }
        let index = progress.completedCount(practice)
        guard practice.lessons.indices.contains(index) else { error = "无法加载下一次练习。"; return }
        sessionKind = .pronunciation
        lesson = Lesson(course: practice, lessonIndex: index, hearts: progress.hearts)
        settlement = nil; entryPending = false; confirmingExit = false
        feedbackDifficulty = nil; closeQuestionReport(); playQuestion()
    }
    func begin(_ index: Int) {
        sessionKind = .course
        guard progress.isUnlocked(course, index: index) else { return }
        lesson = Lesson(course: course, lessonIndex: index, hearts: progress.hearts)
        settlement = nil
        feedbackDifficulty = nil; closeQuestionReport()
        confirmingExit = false
        entryPending = course.lessons[index].entry != nil
        audio.play(.tap)
        playAutomaticPrompt()
    }
    func beginGeneralPractice() {
        let explicit = CommandLine.arguments.firstIndex(of: "--general-practice-fixture").flatMap { index in
            index + 1 < CommandLine.arguments.count ? URL(fileURLWithPath: CommandLine.arguments[index + 1]) : nil
        }
        guard let url = explicit ?? Bundle.module.url(forResource: "general-practice", withExtension: "json", subdirectory: "Reference") else { error = "无法打开练习。"; return }
        do {
            let practice = try Course.readFixture(url)
            sessionKind = .generalPractice
            lesson = Lesson(course: practice, hearts: progress.hearts)
            settlement = nil; entryPending = false; confirmingExit = false
            feedbackDifficulty = nil; closeQuestionReport(); playAutomaticPrompt()
        } catch { self.error = "无法打开练习。"; NSLog("General practice decode failed: %@", String(describing: error)) }
    }
    func acceptEntry() { entryPending = false; playAutomaticPrompt() }
    func declineSpeech() { speechCapture.cancel(); lesson?.declineSpeech() }
    func declineListening() { lesson?.declineListening() }
    private func playAutomaticPrompt() {
        guard !entryPending, lesson?.interlude == nil, lesson?.deferredSpeech == nil, let question = lesson?.question,
              ["translate", "listenTap", "dialogue", "orderTapComplete", "selectPronunciation", "sameDifferent"].contains(question.sourceType ?? "") || isGeneralPractice && ["listen", "listenComplete", "listenIsolation"].contains(question.sourceType ?? ""),
              course.interfaceLanguage != "zh" || question.audioResource != nil else { return }
        playQuestion()
    }
    func skip() {
        lesson?.skip()
        // No source evidence yet for a skip effect; do not substitute incorrect audio.
    }
    func submit() {
        guard lesson?.canSubmit == true, lesson?.feedback == nil else { return }
        lesson?.submit()
        if let lesson, isGeneralPractice || (lesson.feedback == true ? lesson.question.correctFeedbackAudioResource : lesson.question.incorrectFeedbackAudioResource) != nil {
            audio.playReferenceEffect(lesson.feedback == true ? lesson.question.correctFeedbackAudioResource : lesson.question.incorrectFeedbackAudioResource)
            if isGeneralPractice && lesson.question.sourceType == "assist", let correct = lesson.question.options.first(where: { $0.id == lesson.question.answer }), let resource = correct.audioResource {
                audio.speak(correct.text, language: course.speechLanguage, resource: resource)
            }
        } else { audio.play(lesson?.feedback == true ? .correct : .incorrect) }
        if sessionKind == .course, let hearts = lesson?.hearts, hearts != progress.hearts {
            progress.hearts = hearts
            save()
        }
    }
    func advance() {
        guard lesson?.feedback != nil || lesson?.interlude != nil || lesson?.speechDeclined == true || lesson?.listeningDeclined == true else { return }
        let previousQuestion = lesson?.question.id
        let wasInterlude = lesson?.interlude != nil
        let wasDeferred = lesson?.deferredSpeech != nil
        lesson?.advance()
        if lesson?.question.id != previousQuestion { feedbackDifficulty = nil; closeQuestionReport() }
        if let lesson, !lesson.complete, lesson.interlude == nil, (wasInterlude || wasDeferred || lesson.question.id != previousQuestion) { playAutomaticPrompt() }
        if let lesson, lesson.complete {
            if !isGeneralPractice { audio.play(.complete) }
            if let pages = lesson.definition.settlement { settlement = SettlementFlow(pages: pages) }
            if sessionKind != .course {
                // Track observed sessions separately; this finite evidence set is not the full pronunciation course.
                progress.completedLessons[lesson.course.id, default: []].insert(lesson.definition.id)
                save()
            } else { progress.markCompleted(course, index: lesson.lessonIndex); save() }
        }
    }
    func advanceSettlement() {
        if isGeneralPractice, settlement?.current?.kind == "practice_heart" {
            progress.hearts += 1; save()
        }
        settlement?.advance()
        if settlement?.current == nil { discardAttempt() }
    }
    func openPathChest() {
        if progress.openPathChest(course) { save() }
    }
    func save() {
        do { try store.save(progress); error = nil }
        catch { self.error = "Progress could not be saved. Please try again." }
    }
    func discardAttempt() { speechCapture.cancel(); if isPronunciationPractice { destination = "Pronunciation" }; if isGeneralPractice { destination = "Learn" }; sessionKind = .course; lesson = nil; confirmingExit = false; entryPending = false; settlement = nil }
}
