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
        case .textEntry: throw CheckFailure.failed("Typed input is not part of this frozen historical trajectory")
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
        case .textEntry: throw CheckFailure.failed("Typed input is not part of this frozen historical trajectory")
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
        case .textEntry: throw CheckFailure.failed("Typed input is not part of this frozen historical trajectory")
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
            case .textEntry: throw CheckFailure.failed("Typed input is not part of this frozen historical trajectory")
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
        case .textEntry: throw CheckFailure.failed("Typed input is not part of this frozen historical trajectory")
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
func actualEnglishInputStates() throws {
    let source = try course(fixture: "fixture-english-input-probe.json")
    var lesson = Lesson(course: source, hearts: 4)
    try check(!lesson.canSubmit, "Empty typed input submitted")
    lesson.enterText("Te"); try check(lesson.canSubmit, "Nonempty input cannot submit")
    lesson.enterText(""); try check(!lesson.canSubmit, "Clearing typed input leaves check enabled")
    lesson.enterText("Tea"); lesson.submit()
    try check(lesson.feedback == true && lesson.hearts == 4, "Source accepted Tea rejected")
    lesson.enterText("changed"); try check(lesson.enteredText == "Tea", "Submitted input edited")
    lesson.advance(); try check(lesson.enteredText.isEmpty && !lesson.canSubmit, "Input leaked into next state")
    try check(lesson.question.completionPrefix == "I'd like " && lesson.question.completionSuffix == ".", "Source fixed sentence lost")
    lesson.enterText("tea"); lesson.submit(); lesson.advance()
    try check(lesson.complete, "Source accepted reverse input rejected")
    var progress = LearningProgress(); progress.markCompleted(source, index: 0)
    try check(!progress.completedCourses.contains(source.id), "Component probe promoted to full original course completion")
    print("PASS observed input edit/clear/lock and two source accepted values; full grader and source mistake trajectory unverified")
}
func actualEnglishAudioPairing() throws {
    let source = try course(fixture: "fixture-english-pairing-probe.json")
    var lesson = Lesson(course: source, hearts: 3)
    let a = lesson.question.pairs[0].id, b = lesson.question.pairs[1].id
    lesson.matchLeft(a); lesson.matchRight(b)
    try check(lesson.hearts == 2 && lesson.mistakesMade == 1 && lesson.incorrectMatch == [a, b], "Source audio mismatch must consume one heart and mark both controls")
    try check(lesson.feedback == nil && lesson.matchedPairs.isEmpty, "Wrong pair ended the current task")
    lesson.matchLeft(a); lesson.matchRight(a)
    try check(lesson.hearts == 2 && lesson.matchedPairs.contains(a) && lesson.incorrectMatch == nil, "Source retry failed or cost another heart")
    lesson.matchLeft(a); lesson.matchRight(a)
    try check(lesson.hearts == 2 && lesson.matchedPairs.count == 1, "Disabled matched pair accepted new input")
    for pair in lesson.question.pairs.dropFirst() { lesson.matchLeft(pair.id); lesson.matchRight(pair.id) }
    try check(lesson.feedback == true && lesson.hearts == 2, "All source audio pairs did not finish")
    let typed = try course(fixture: "fixture-english-input-probe.json").questions[1]
    try check(typed.correctText == "I'd like tea.", "Typed correction lost the source fixed sentence")
    print("PASS source audio matching wrong-heart, retry and disabled pairs; no extra pairing review observed in mixed-error source trajectory; acoustics unverified")
}
func actualEnglishTypedReview() throws {
    let source = try course(fixture: "fixture-english-hot-review-probe.json")
    var lesson = Lesson(course: source, hearts: 4)
    lesson.enterText("cold"); lesson.submit()
    try check(lesson.feedback == false && lesson.hearts == 3 && lesson.question.correctText == "hot tea", "Source cold rejection or full correction not reproduced")
    lesson.advance()
    try check(lesson.reviewing && lesson.enteredText.isEmpty && !lesson.canSubmit, "Typed error did not enter clean review")
    lesson.enterText("HOT"); lesson.submit()
    try check(lesson.feedback == true && lesson.hearts == 3, "Source accepted HOT rejected")
    lesson.advance(); try check(lesson.complete, "Corrected source typed error cannot finish")
    print("PASS source cold rejection, full hot tea correction, review and HOT acceptance; broader grader unverified")
}
func legacyCourse() throws -> Course { try course() }
func actualEnglishFifthTrajectory() throws {
    let source = try course(fixture: "fixture-reference-en-zh-v6.json")
    try check(source.lessons.map { $0.questions.count } == [15,15,15,12,15], "Captured five-course sequence changed")
    var lesson = Lesson(course: source, lessonIndex: 4, hearts: 4)
    var graded = 0, speeches = 0, introductions = 0
    while !lesson.complete {
        if let speech = lesson.deferredSpeech {
            speeches += 1
            try check(speech.phrase == "I'd like hot coffee." && lesson.question.id == "en-zh-l5-adaptive7", "Speech inserted at wrong source position")
            let position = lesson.position
            lesson.advance(); lesson.addWord(lesson.question.answerWords[0]); lesson.submit()
            try check(lesson.position == position && lesson.selectedWords.isEmpty && lesson.feedback == nil && !lesson.canSubmit, "Ungraded speech leaked into answering")
            lesson.declineSpeech(); lesson.advance()
            try check(lesson.hearts == 4 && lesson.mistakesMade == 0 && lesson.deferredSpeech == nil, "Declining speech was graded or consumed a heart")
            continue
        }
        if let interlude = lesson.interlude {
            introductions += 1
            try check(interlude.id == "en-zh-l5-review-intro" && lesson.reviewing && lesson.question.id == "en-zh-l5-q7", "Source review introduction or target wrong")
            try check(!lesson.canSubmit && lesson.enteredText.isEmpty, "Review introduction exposes stale answer")
            lesson.advance(); continue
        }
        let q = lesson.question
        switch q.kind {
        case .wordTiles: for id in q.answerWords { lesson.addWord(id) }; lesson.submit()
        case .textEntry:
            lesson.enterText(q.id == "en-zh-l5-q7" ? (lesson.reviewing ? "HOT" : "cold") : q.answer)
            lesson.submit()
        case .matching:
            if q.id == "en-zh-l5-q8" { lesson.matchLeft(q.pairs[0].id); lesson.matchRight(q.pairs[1].id) }
            for pair in q.pairs { lesson.matchLeft(pair.id); lesson.matchRight(pair.id) }
        case .choice: throw CheckFailure.failed("Unexpected fifth choice task")
        }
        try check(lesson.feedback == (q.id != "en-zh-l5-q7" || lesson.reviewing), "Captured answer outcome changed")
        graded += 1; lesson.advance()
    }
    try check(graded == 16 && speeches == 1 && introductions == 1 && lesson.hearts == 2 && lesson.mistakesMade == 2, "Full mixed-error fifth trajectory diverged")
    var flow = SettlementFlow(pages: lesson.definition.settlement!)
    var kinds = [String]()
    while let page = flow.current { kinds.append(page.kind); flow.advance() }
    try check(kinds == ["result","daily_quests","gems","profile"], "Fifth settlement ordering changed")
    var progress = LearningProgress()
    for index in source.lessons.indices { progress.markCompleted(source, index: index) }
    try check(!progress.completedCourses.contains(source.id), "Remaining three uncompiled lessons credited")
    try check(source.pathNodes?[1].lessonIDs == ["lesson-5"] && source.pathNodes?[1].lessonCount == 4, "Second-node source progress lost")
    let roundTrip = try JSONDecoder().decode(Course.self, from: JSONEncoder().encode(source))
    try check(roundTrip == source, "Speech/review metadata lost in round-trip")
    print("PASS full fifth mixed-error trajectory: 15 graded questions + ungraded speech + one typed review; settlement/home metadata; frontend pending")
}
func actualListeningDeclinePrefix() throws {
    let source = try course(fixture: "fixture-listening-decline.json")
    var lesson = Lesson(course: source, hearts: 2)
    lesson.advance()
    try check(lesson.position == 0, "Unanswered pairing advanced before decline")
    lesson.declineListening()
    let pair = lesson.question.pairs[0].id
    lesson.matchLeft(pair); lesson.matchRight(pair); lesson.submit()
    try check(lesson.listeningDeclined && lesson.feedback == nil && lesson.matchedPairs.isEmpty && lesson.hearts == 2 && lesson.mistakesMade == 0 && lesson.review.isEmpty,
              "Declined listening was scored, accepted input, or consumed a heart")
    lesson.advance()
    try check(lesson.question.id == "en-zh-decline-adaptive" && !lesson.listeningDeclined, "Inserted source translation was skipped")
    lesson.declineListening()
    try check(!lesson.listeningDeclined, "Listening decline leaked into translation")
    for id in lesson.question.answerWords { lesson.addWord(id) }
    lesson.submit(); lesson.advance()
    try check(lesson.question.id == "en-zh-decline-fill", "Original typed challenge did not follow inserted translation")
    lesson.enterText("milk"); lesson.submit()
    try check(lesson.feedback == true && lesson.hearts == 2 && lesson.review.isEmpty, "Observed milk acceptance changed")
    print("PASS source listening decline locks pairs without grading, preserves hearts, enters inserted translation then original fill; later adaptation/timer unverified")
}
func actualEnglishSixthDoubleDecline() throws {
    let source = try course(fixture: "fixture-reference-en-zh-v7.json")
    var lesson = Lesson(course: source, lessonIndex: 5, hearts: 2)
    var graded = 0, listening = 0, speech = 0, introductions = 0
    while !lesson.complete {
        if lesson.interlude != nil { introductions += 1; lesson.advance(); continue }
        if lesson.deferredSpeech != nil {
            speech += 1; lesson.declineSpeech(); lesson.advance(); continue
        }
        let q = lesson.question
        if q.listeningDecline != nil {
            listening += 1; lesson.declineListening()
            try check(lesson.feedback == nil && lesson.hearts == 2 && lesson.review.isEmpty, "Sixth listening decline was graded")
            lesson.advance(); continue
        }
        switch q.kind {
        case .wordTiles: for id in q.answerWords { lesson.addWord(id) }
        case .textEntry: lesson.enterText(q.answer)
        default: throw CheckFailure.failed("Unexpected sixth graded task")
        }
        lesson.submit()
        try check(lesson.feedback == true, "Actual sixth accepted answer rejected")
        graded += 1; try check(lesson.correctStreak == graded, "Ungraded sixth stage changed correct streak"); lesson.advance()
    }
    try check(graded == 15 && listening == 1 && speech == 1 && introductions == 1 && lesson.hearts == 2 && lesson.mistakesMade == 0 && lesson.review.isEmpty, "Sixth observed trajectory diverged")
    try check(lesson.definition.settlement?.map(\.kind) == ["result", "profile"], "Sixth incorrectly inherited fifth settlement")
    try check(source.pathNodes?[1].lessonIDs == ["lesson-5", "lesson-6"], "Sixth second-node placement lost")
    let roundTrip = try JSONDecoder().decode(Course.self, from: JSONEncoder().encode(source))
    try check(roundTrip == source, "Sixth metadata lost during round trip")
    print("PASS actual sixth double-decline: 15 graded + ungraded listening/speech, challenge entry and independent settlement; normal branch still unknown")
}

func actualSecondaryInputModes() throws {
    let source = try course(fixture: "fixture-reference-en-zh-secondary-v1.json")
    var lesson = Lesson(course: source, hearts: 2)
    for (index, answer) in ["Thank you.", "I'd like water and coffee, please."].enumerated() {
        try check(!lesson.canSubmit && lesson.supportsInputMode, "Observed initial action state missing")
        lesson.toggleInputMode()
        try check(lesson.usingKeyboard && !lesson.canSubmit && lesson.displayedPrompt == "用英语写出这句话", "Empty full answer must be disabled")
        lesson.enterText(answer)
        try check(lesson.canSubmit && lesson.displayedInput == answer, "Full answer not retained")
        lesson.toggleInputMode()
        try check(!lesson.canSubmit && lesson.displayedInput.isEmpty && lesson.selectedWords.isEmpty, "Alternative answer must stay independent")
        if index == 1 { try check(lesson.displayedPrompt == "输入所缺单词", "Reduced difficulty prompt missing") }
        lesson.toggleInputMode()
        try check(lesson.displayedInput == answer && lesson.canSubmit, "Reopened source answer lost")
        lesson.submit()
        try check(lesson.feedback == true && lesson.hearts == 2, "Actual accepted full answer rejected")
        lesson.toggleInputMode()
        try check(lesson.usingKeyboard, "Feedback input must remain locked")
        lesson.advance()
    }
    try check(lesson.complete && lesson.mistakesMade == 0, "Probe did not finish")
    let roundTrip = try JSONDecoder().decode(Course.self, from: JSONEncoder().encode(source))
    try check(roundTrip == source, "Input-mode metadata lost")
    print("PASS actual keyboard/harder independent buffers, source accepted full answers and feedback lock")
}

func actualCrossQuestionPreferences() throws {
    var lesson = Lesson(course: try course(fixture: "fixture-reference-en-zh-secondary-v3.json"), hearts: 2)
    try check(!lesson.usingKeyboard, "Initial word bank must remain the source default")
    lesson.toggleInputMode(); lesson.enterText("Thank you."); lesson.submit(); lesson.advance()
    try check(!lesson.usingKeyboard && lesson.displayedPrompt == "输入所缺单词", "Tile preference must not change the initial fill difficulty")
    lesson.toggleInputMode(); lesson.enterText("I'd like water and coffee, please."); lesson.submit(); lesson.advance()
    try check(lesson.usingKeyboard && lesson.displayedInput.isEmpty && !lesson.canSubmit, "Source q6 must reopen keyboard with a fresh buffer")
    lesson.enterText("No coffee, thank you."); lesson.submit(); lesson.advance()
    try check(lesson.usingKeyboard && lesson.displayedPrompt == "用英语写出这句话" && lesson.displayedInput.isEmpty && !lesson.canSubmit, "Source q7 must independently retain full-sentence difficulty")
    lesson.enterText("With ice?"); lesson.submit()
    try check(lesson.feedback == true && lesson.hearts == 2 && lesson.mistakesMade == 0, "Observed full answer rejected after preference restoration")
    lesson.advance(); try check(lesson.complete, "Preference trajectory did not finish")
    print("PASS observed independent cross-question keyboard/full-sentence preferences and fresh buffers")
}

func actualSkipReview() throws {
    let c = try course(fixture: "fixture-reference-en-zh-skip-v1.json")
    var lesson = Lesson(course: c, hearts: 2)
    try check(!lesson.canSubmit, "Empty source question unexpectedly submittable")
    lesson.skip(); lesson.skip()
    try check(lesson.skipped && lesson.feedback == false && lesson.review == [0], "Skip must queue original question once")
    try check(lesson.hearts == 2 && lesson.mistakesMade == 0, "Skip was incorrectly graded as a mistake")
    try check(lesson.question.skipCorrectText == "茶和咖啡", "Source correction lost Chinese spacing")
    lesson.advance()
    try check(lesson.reviewing && !lesson.complete && lesson.interlude != nil && !lesson.skipped, "Skip bypassed review intro")
    lesson.advance()
    for word in lesson.question.answerWords { lesson.addWord(word) }
    lesson.submit()
    try check(lesson.feedback == true, "Source review answer rejected")
    lesson.advance()
    try check(lesson.complete && lesson.hearts == 2 && lesson.mistakesMade == 0 && lesson.review.isEmpty, "Skip review altered hearts/errors or remained incomplete")
    print("PASS observed empty skip, no heart/error penalty, original-question review and correction")
}

func actualSeventhTrajectory() throws {
    let c = try course(fixture: "fixture-reference-en-zh-v8.json")
    var lesson = Lesson(course: c, lessonIndex: 6, hearts: 2)
    let original = lesson.question.id
    lesson.skip(); lesson.advance()
    for index in 1..<15 {
        try check(lesson.position == index, "Seventh actual order changed")
        if lesson.deferredSpeech != nil { lesson.declineSpeech(); lesson.advance() }
        if [1,4].contains(index) { lesson.toggleInputMode() }
        if [6,7,8,14].contains(index) { try check(lesson.usingKeyboard, "Source independent preference lost") }
        if lesson.usingKeyboard { lesson.enterText(lesson.question.keyboardAnswer!); lesson.submit() }
        else {
            switch lesson.question.kind {
            case .matching: for p in lesson.question.pairs { lesson.matchLeft(p.id); lesson.matchRight(p.id) }
            case .choice: lesson.choose(lesson.question.answer); lesson.submit()
            case .textEntry: lesson.enterText(lesson.question.answer); lesson.submit()
            case .wordTiles: for w in lesson.question.answerWords { lesson.addWord(w) }; lesson.submit()
            }
        }
        try check(lesson.feedback == true && lesson.hearts == 2 && lesson.mistakesMade == 0, "Seventh source accepted answer failed")
        lesson.advance()
    }
    try check(lesson.reviewing && lesson.interlude != nil && lesson.question.id == original, "Seventh skipped q0 not queued at actual end")
    lesson.advance()
    try check(lesson.visibleWords.map(\.text) == ["和","茶","咖啡","谢谢你"], "Review bank must follow observed reshuffle")
    for w in lesson.question.answerWords { lesson.addWord(w) }; lesson.submit()
    try check(lesson.correctStreak == 15, "Actual fifteen-correct streak lost")
    lesson.advance()
    try check(lesson.complete && lesson.mistakesMade == 0, "Seventh actual review did not complete")
    try check(lesson.definition.settlement?.map(\.kind) == ["result","achievement","profile"], "Source seventh settlement order lost")
    print("PASS full observed seventh skip/normal listening/radio2/preferences/speech decline/insertion/review/settlement; heart refresh and unknown radio1 audio unverified")
}

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
    try actualEnglishInputStates()
    try actualEnglishAudioPairing()
    try actualEnglishTypedReview()
    try actualEnglishFifthTrajectory()
    try actualListeningDeclinePrefix()
    try actualEnglishSixthDoubleDecline()
    try actualSecondaryInputModes()
    try actualCrossQuestionPreferences()
    try actualSkipReview()
    try actualSeventhTrajectory()
    print("21 business checks passed; core layer only")
} catch {
    FileHandle.standardError.write(Data(("FAIL " + String(describing: error) + "\n").utf8))
    exit(1)
}
