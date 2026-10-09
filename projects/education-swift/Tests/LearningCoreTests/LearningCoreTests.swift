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
func legacyCourse() throws -> Course { try course() }
do {
    try mistakeReview()
    try persistence()
    try wordTilesAndReview()
    try matching()
    try unlocksAndLegacy()
    print("5 business checks passed; core layer only")
} catch {
    FileHandle.standardError.write(Data(("FAIL " + String(describing: error) + "\n").utf8))
    exit(1)
}
