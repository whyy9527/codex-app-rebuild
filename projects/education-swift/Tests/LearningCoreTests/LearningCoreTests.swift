import Foundation
import LearningCore

// Executable business checks for a CLT-only host without XCTest/Swift Testing.
enum CheckFailure: Error { case failed(String) }
func check(_ condition: @autoclosure () throws -> Bool, _ message: String) throws {
    if try !condition() { throw CheckFailure.failed(message) }
}
func course(fixture: String = "fixture-v1.json") throws -> Course {
    let projects = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
    return try Course.readFixture(projects.appendingPathComponent("duolingo-web/" + fixture))
}
func mistakeReview() throws {
    let course = try course()
    var lesson = Lesson(course: course)
    lesson.submit()
    try check(lesson.feedback == nil, "Empty answer was submitted")
    lesson.choose(course.questions[0].options.first { $0.id != course.questions[0].answer }!.id)
    lesson.submit()
    try check(lesson.hearts == 4, "Wrong answer must consume one heart")
    lesson.advance()
    lesson.choose(lesson.question.answer); lesson.submit(); lesson.advance()
    try check(!lesson.complete && lesson.reviewing, "Mistakes must be reviewed before completion")
    try check(lesson.question.id == course.questions[0].id, "Review must revisit missed question")
    lesson.choose(lesson.question.answer); lesson.submit(); lesson.advance()
    try check(lesson.complete, "Corrected mistake must allow completion")
    print("PASS mistake review and empty-answer boundary")
}
func persistence() throws {
    let directory = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
    defer { try? FileManager.default.removeItem(at: directory) }
    let store = ProgressStore(url: directory.appendingPathComponent("progress.json"))
    var progress = try store.load()
    progress.completedCourses.insert("original-course")
    try store.save(progress)
    try check(try ProgressStore(url: store.url).load() == progress, "Completed progress lost on reopening")
    for content in ["broken", "{}", "{\"completedCourses\":null}", "{\"completedCourses\":[],\"hearts\":-1}"] {
        try Data(content.utf8).write(to: store.url)
        var rejected = false
        do { _ = try store.load() } catch { rejected = true }
        try check(rejected, "Corrupt progress was silently accepted: " + content)
        try check(try String(contentsOf: store.url, encoding: .utf8) == content, "Corrupt progress was overwritten")
    }
    print("PASS persistence and corrupt-data preservation")
}
func wordTilesAndReview() throws {
    let course = try course(fixture: "fixture-v2.json")
    var lesson = Lesson(course: course, lessonIndex: 1)
    lesson.choose(lesson.question.answer); lesson.submit(); lesson.advance()
    let missed = lesson.question.id
    let words = lesson.question.answerWords
    lesson.addWord(words[0])
    try check(lesson.canSubmit, "A partial phrase must be submittable")
    lesson.removeWord(words[0])
    try check(!lesson.canSubmit && lesson.selectedWords.isEmpty, "Undo must restore the empty-answer boundary")
    for word in words.reversed() { lesson.addWord(word) }
    lesson.submit()
    try check(lesson.feedback == false && lesson.hearts == 4, "Reversed phrase must consume one heart")
    lesson.removeWord(words[0])
    try check(lesson.selectedWords.count == 2, "Submitted words must remain locked")
    lesson.advance()
    for word in lesson.question.answerWords { lesson.addWord(word) }
    lesson.submit(); lesson.advance()
    try check(lesson.reviewing && lesson.question.id == missed && lesson.selectedWords.isEmpty, "Review must restore the missed phrase without its old selection")
    for word in lesson.question.answerWords { lesson.addWord(word) }
    lesson.submit(); lesson.advance()
    try check(lesson.complete, "Corrected phrase must permit completion")
    print("PASS word order, undo, locking and mistake review")
}
func matching() throws {
    let course = try course(fixture: "fixture-v2.json")
    var lesson = Lesson(course: course)
    for _ in 0..<2 { lesson.choose(lesson.question.answer); lesson.submit(); lesson.advance() }
    let pairs = lesson.question.pairs
    lesson.matchLeft(pairs[0].id); lesson.matchRight(pairs[1].id)
    try check(lesson.matchedPairs.isEmpty && lesson.hearts == 5 && lesson.matchingHint != nil, "Wrong-pair retry decision was not preserved")
    for pair in pairs.dropLast() { lesson.matchLeft(pair.id); lesson.matchRight(pair.id) }
    try check(lesson.feedback == nil && !lesson.complete, "Matching finished before the last pair")
    lesson.matchLeft(pairs.last!.id); lesson.matchRight(pairs.last!.id)
    try check(lesson.feedback == true && lesson.matchedPairs.count == pairs.count, "All pairs must produce positive feedback")
    lesson.advance()
    try check(lesson.complete, "A completed matching activity must finish this lesson")
    print("PASS matching completion and explicit wrong-pair retry decision")
}
func unlocksAndLegacy() throws {
    let course = try course(fixture: "fixture-v2.json")
    var progress = LearningProgress()
    try check(!progress.isUnlocked(course, index: 1), "Later lesson started before its prerequisite")
    try check(!progress.markCompleted(course, index: 1), "Locked lesson was credited")
    try check(progress.markCompleted(course, index: 0), "First lesson could not be recorded")
    try check(progress.completedCount(course) == 1 && progress.isUnlocked(course, index: 1), "Completion did not unlock the next lesson")
    progress.hearts = 4
    let directory = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
    defer { try? FileManager.default.removeItem(at: directory) }
    let store = ProgressStore(url: directory.appendingPathComponent("progress.json"))
    try store.save(progress)
    let reopened = try store.load()
    try check(reopened == progress && reopened.completedCount(course) == 1 && reopened.hearts == 4, "Lesson and heart progress did not survive reopening")
    let legacy = try JSONDecoder().decode(LearningProgress.self, from: Data("{\"completedCourses\":[\"everyday-english\"]}".utf8))
    try check(legacy.completedCount(try legacyCourse()) == 1, "Old single-lesson progress was lost")
    try check(legacy.completedCount(course) == 0, "Old course credit silently completed new lesson content")
    print("PASS prerequisite unlock, progress reopening and legacy-content boundary")
}
func observedInterludes() throws {
    let source = try course(fixture: "fixture-reference-v6.json")
    var lesson = Lesson(course: source, lessonIndex: 2)
    var seen = [String]()
    while !lesson.complete {
        if let interlude = lesson.interlude {
            seen.append(interlude.text)
            let questionID = lesson.question.id
            lesson.choose(lesson.question.answer); lesson.submit()
            try check(lesson.selected == nil && lesson.feedback == nil && !lesson.canSubmit, "Interlude allowed answering the hidden next question")
            lesson.advance()
            try check(lesson.interlude == nil && lesson.question.id == questionID, "Dismissing interlude skipped the next question")
            continue
        }
        switch lesson.question.kind {
        case .choice: lesson.choose(lesson.question.answer); lesson.submit()
        case .wordTiles:
            for id in lesson.question.answerWords { lesson.addWord(id) }; lesson.submit()
        case .matching:
            for pair in lesson.question.pairs { lesson.matchLeft(pair.id); lesson.matchRight(pair.id) }
        }
        try check(lesson.feedback == true, "Observed source answer failed")
        lesson.advance()
    }
    try check(seen == ["Cool! 5 in a row!", "Nice! Practice always pays off."], "Observed interludes missing or repeated")
    print("PASS observed interludes block hidden input and resume without losing a question; other trajectories unverified")
}
func actualEnglishTrajectory() throws {
    let source = try course(fixture: "fixture-reference-en-zh-v1.json")
    try check(source.speechLanguage == "en" && source.interfaceLanguage == "zh", "Real course language metadata lost")
    try check(source.questions.count == 15, "Actual English question count changed")
    let listening = source.questions.filter { $0.sourceType == "listenTap" }
    let dialogues = source.questions.filter { $0.sourceType == "dialogue" }
    try check(listening.count == 2 && listening.allSatisfy { $0.audioResource != nil && $0.slowAudioResource != nil }, "Observed listening clips missing")
    try check(dialogues.count == 2 && dialogues.allSatisfy { $0.dialogueAvatars?.count == 2 && $0.hint != nil && $0.audioResource != nil }, "Dialogue presentation data missing")
    try check(source.questions[0].options.allSatisfy { $0.imageResource != nil }, "Per-option source artwork lost")
    var lesson = Lesson(course: source)
    let first = lesson.question.id
    lesson.choose(lesson.question.options.first { $0.text == "sugar" }!.id); lesson.submit()
    try check(lesson.hearts == 4 && lesson.feedback == false, "Observed first mistake must consume one heart")
    lesson.advance()
    var accepted = 0
    while !lesson.reviewing && !lesson.complete {
        switch lesson.question.kind {
        case .choice: lesson.choose(lesson.question.answer); lesson.submit()
        case .wordTiles:
            for id in lesson.question.answerWords { lesson.addWord(id) }; lesson.submit()
        case .matching:
            for pair in lesson.question.pairs { lesson.matchLeft(pair.id); lesson.matchRight(pair.id) }
        }
        try check(lesson.feedback == true, "Observed English answer rejected")
        accepted += 1; lesson.advance()
    }
    try check(accepted == 14 && lesson.reviewing && lesson.question.id == first && !lesson.complete, "Actual mistake review trajectory lost")
    lesson.choose(lesson.question.answer); lesson.submit(); lesson.advance()
    try check(lesson.complete && lesson.hearts == 4, "Correct retry must complete without restoring lost heart")
    let roundTrip = try JSONDecoder().decode(Course.self, from: JSONEncoder().encode(source))
    try check(roundTrip == source, "English presentation metadata failed Codable round-trip")
    print("PASS actual en/zh 15-question wrong-first/review trajectory and presentation metadata; frontend equivalence pending")
}
func actualEnglishSecondTrajectory() throws {
    let source = try course(fixture: "fixture-reference-en-zh-v2.json")
    try check(source.lessons.count == 2 && source.pathNodes?.first?.lessonIDs == ["lesson-1", "lesson-2"], "Second lesson lost its first-node membership")
    let questions = source.lessons[1].questions
    try check(questions.count == 15 && questions.suffix(3).allSatisfy { $0.sourceType == "translate" && $0.indicator == "挑战题" }, "Actual adaptive tail replaced by unvisited API tail")
    let fill = questions[4]
    try check(fill.sourceType == "orderTapComplete" && fill.example == "Tea with sugar." && fill.completionPrefix == "Coffee " && fill.completionSuffix == ".", "Observed fill-in context missing")
    var progress = LearningProgress()
    try check(!progress.isUnlocked(source, index: 1), "Second lesson unlocked before first completion")
    progress.markCompleted(source, index: 0)
    try check(progress.isUnlocked(source, index: 1), "First completion did not unlock actual second lesson")
    var lesson = Lesson(course: source, lessonIndex: 1, hearts: 4)
    var seen = [String](); var count = 0
    while !lesson.complete {
        if let interlude = lesson.interlude { seen.append(interlude.text); lesson.advance(); continue }
        switch lesson.question.kind {
        case .choice: lesson.choose(lesson.question.answer); lesson.submit()
        case .wordTiles:
            if lesson.question.sourceType == "orderTapComplete" {
                let first = lesson.question.answerWords[0]
                lesson.addWord(first); lesson.removeWord(first)
                try check(lesson.selectedWords.isEmpty && !lesson.canSubmit, "Fill undo lost empty-answer boundary")
            }
            for id in lesson.question.answerWords { lesson.addWord(id) }; lesson.submit()
        case .matching: throw CheckFailure.failed("Unvisited API matching question entered actual second trajectory")
        }
        try check(lesson.feedback == true, "Source accepted second-lesson answer rejected")
        count += 1; lesson.advance()
    }
    try check(count == 15 && lesson.hearts == 4 && seen == ["你的辛勤付出得到了回报！", "你是最棒的！", "哎哟不错哦！要不要玩点刺激的？"], "Second trajectory or interludes lost")
    let roundTrip = try JSONDecoder().decode(Course.self, from: JSONEncoder().encode(source))
    try check(roundTrip == source, "Second-lesson presentation lost during round-trip")
    print("PASS actual second lesson, fill undo, adaptive tail, three interludes and first-node unlock; frontend equivalence pending")
}
func actualEnglishThirdTrajectory() throws {
    let source = try course(fixture: "fixture-reference-en-zh-v3.json")
    try check(source.lessons.count == 3 && source.pathNodes?.first?.lessonIDs == ["lesson-1", "lesson-2", "lesson-3"], "Actual third lesson not connected to first node")
    var progress = LearningProgress()
    progress.markCompleted(source, index: 0)
    try check(!progress.isUnlocked(source, index: 2), "Third lesson unlocked without second completion")
    progress.markCompleted(source, index: 1)
    try check(progress.isUnlocked(source, index: 2), "Third lesson unavailable after first two completions")
    var lesson = Lesson(course: source, lessonIndex: 2, hearts: 4)
    var count = 0; var interludes = [String]()
    while !lesson.complete {
        if let interlude = lesson.interlude { interludes.append(interlude.text); lesson.advance(); continue }
        if lesson.question.id == "en-zh-l3-q9" {
            let duplicates = lesson.question.words.filter { $0.text == "不要" }.map(\.id)
            try check(duplicates.count == 2 && Set(duplicates).count == 2, "Repeated visible words collapsed")
            lesson.addWord(duplicates[0]); lesson.addWord(duplicates[0])
            try check(lesson.selectedWords.count == 1, "A tile occurrence was reused")
            lesson.addWord(duplicates[1]); lesson.removeWord(duplicates[0])
            try check(lesson.selectedWords == [duplicates[1]], "Undo removed both equal-text tiles")
            lesson.removeWord(duplicates[1])
            try check(!lesson.canSubmit, "Removing both repeated tiles left a submittable answer")
            var missing = lesson
            for id in lesson.question.answerWords where id != duplicates[1] { missing.addWord(id) }
            missing.submit()
            try check(missing.feedback == false, "Missing a repeated word was accepted")
            for id in lesson.question.answerWords {
                lesson.addWord(id == duplicates[0] ? duplicates[1] : id == duplicates[1] ? duplicates[0] : id)
            }
            lesson.submit()
        } else {
            switch lesson.question.kind {
            case .choice: lesson.choose(lesson.question.answer); lesson.submit()
            case .wordTiles: for id in lesson.question.answerWords { lesson.addWord(id) }; lesson.submit()
            case .matching: throw CheckFailure.failed("Unobserved matching tail entered third actual trajectory")
            }
        }
        try check(lesson.feedback == true, "Source accepted third-lesson word sequence rejected")
        count += 1; lesson.advance()
    }
    try check(count == 15 && lesson.hearts == 4 && interludes.count == 3, "Third accepted trajectory or interludes lost")
    progress.completedCourses.insert(source.id) // Old partial-fixture credit must be repaired.
    progress.markCompleted(source, index: 2)
    try check(progress.completedCount(source) == 3 && !progress.completedCourses.contains(source.id), "Observed three-lesson subset incorrectly credited the whole uncompiled path")
    try check(source.lessons[2].questions.suffix(3).allSatisfy { $0.indicator == "挑战题" && $0.sourceLanguage == "zh" }, "Static API tail substituted for actual hard questions")
    let roundTrip = try JSONDecoder().decode(Course.self, from: JSONEncoder().encode(source))
    try check(roundTrip == source, "Third-course occurrence identities lost during round-trip")
    print("PASS actual third lesson, duplicate-tile independence/undo/multiplicity/equivalent sequence, three interludes and unlock; full source grader unverified")
}
func actualEnglishFourthTrajectory() throws {
    let source = try course(fixture: "fixture-reference-en-zh-v4.json")
    try check(source.lessons.map { $0.questions.count } == [15,15,15,12], "Fourth source length replaced with assumed 15 questions")
    try check(source.lessons[3].entry?.startLabel == "开始挑战 +20 经验", "Observed challenge entry lost")
    var progress = LearningProgress()
    for index in 0..<3 { progress.markCompleted(source, index: index) }
    try check(progress.isUnlocked(source, index: 3), "Fourth unavailable after actual first three")
    var lesson = Lesson(course: source, lessonIndex: 3, hearts: 4)
    try check(lesson.interlude?.id == "en-zh-l4-review-intro" && !lesson.canSubmit, "Initial review intro skipped")
    lesson.choose(lesson.question.answer)
    try check(lesson.selected == nil, "Hidden question accepted input during introduction")
    var count = 0; var interludes = [String]()
    while !lesson.complete {
        if let interlude = lesson.interlude { interludes.append(interlude.id); lesson.advance(); continue }
        switch lesson.question.kind {
        case .choice: lesson.choose(lesson.question.answer)
        case .wordTiles: for id in lesson.question.answerWords { lesson.addWord(id) }
        case .matching: throw CheckFailure.failed("Fourth actual trajectory has no matching task")
        }
        lesson.submit(); try check(lesson.feedback == true, "Actual accepted fourth answer rejected")
        count += 1; lesson.advance()
    }
    try check(count == 12 && lesson.hearts == 4 && interludes == ["en-zh-l4-review-intro", "en-zh-l4-hard-intro"], "Fourth trajectory or introduction ordering changed")
    progress.markCompleted(source, index: 3)
    try check(!progress.completedCourses.contains(source.id), "Uncompiled next path falsely credited")
    let afterThird = source.home?.progressSnapshots?.first { $0.completedLessons == 3 }
    try check(afterThird?.gems == 505 && afterThird?.leagueTitle == "青铜等级", "Observed home snapshot lost")
    let roundTrip = try JSONDecoder().decode(Course.self, from: JSONEncoder().encode(source))
    try check(roundTrip == source, "Fourth presentation round-trip failed")
    print("PASS actual fourth 12-question trajectory, initial input boundary, hard interlude, home snapshot and partial path credit; frontend pending")
}
func actualEnglishSettlement() throws {
    let source = try course(fixture: "fixture-reference-en-zh-v5.json")
    let pages = source.lessons[3].settlement!
    var flow = SettlementFlow(pages: pages)
    var ids = [String]()
    while let page = flow.current { ids.append(page.id); flow.advance() }
    try check(ids == ["en-zh-l4-complete", "en-zh-l4-score", "en-zh-l4-streak", "en-zh-l4-xp-boost", "en-zh-l4-legendary", "en-zh-l4-profile"], "Observed settlement ordering changed")
    flow.advance(); try check(flow.current == nil && flow.position == 6, "Finished settlement restarted")
    let roundTrip = try JSONDecoder().decode(Course.self, from: JSONEncoder().encode(source))
    try check(roundTrip == source, "Settlement metadata lost in round-trip")
    var lesson = Lesson(course: source, hearts: 4)
    lesson.choose(lesson.question.options.first { $0.id != lesson.question.answer }!.id); lesson.submit()
    try check(lesson.mistakesMade == 1, "Incorrect attempt lost, potentially rendering false 100 percent")
    print("PASS source six-stage settlement sequence, terminal behavior, metadata and incorrect-attempt accounting; frontend/secondary branches pending")
}
func legacyCourse() throws -> Course { try course() }
do {
    try mistakeReview()
    try persistence()
    try wordTilesAndReview()
    try matching()
    try unlocksAndLegacy()
    try observedInterludes()
    try actualEnglishTrajectory()
    try actualEnglishSecondTrajectory()
    try actualEnglishThirdTrajectory()
    try actualEnglishFourthTrajectory()
    try actualEnglishSettlement()
    print("11 business checks passed; core layer only")
} catch {
    FileHandle.standardError.write(Data(("FAIL " + String(describing: error) + "\n").utf8))
    exit(1)
}
