import Foundation
import LearningCore

// Executable business checks for a CLT-only host without XCTest/Swift Testing.
enum CheckFailure: Error { case failed(String) }
func check(_ condition: @autoclosure () throws -> Bool, _ message: String) throws {
    if try !condition() { throw CheckFailure.failed(message) }
}
func course() throws -> Course {
    let projects = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
    return try Course.readFixture(projects.appendingPathComponent("duolingo-web/fixture-v1.json"))
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
    try Data("broken".utf8).write(to: store.url)
    var rejected = false
    do { _ = try store.load() } catch { rejected = true }
    try check(rejected, "Corrupt progress was silently accepted")
    try check(try String(contentsOf: store.url, encoding: .utf8) == "broken", "Corrupt progress was overwritten")
    print("PASS persistence and corrupt-data preservation")
}
do {
    try mistakeReview()
    try persistence()
    print("2 business checks passed; core layer only")
} catch {
    FileHandle.standardError.write(Data(("FAIL " + String(describing: error) + "\n").utf8))
    exit(1)
}
