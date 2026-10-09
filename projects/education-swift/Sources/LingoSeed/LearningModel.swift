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
    init(course: Course, store: ProgressStore) throws {
        self.course = course; self.store = store; progress = try store.load()
    }
    func begin(_ index: Int) {
        guard progress.isUnlocked(course, index: index) else { return }
        lesson = Lesson(course: course, lessonIndex: index, hearts: progress.hearts)
        confirmingExit = false
    }
    func submit() {
        lesson?.submit()
        if let hearts = lesson?.hearts, hearts != progress.hearts {
            progress.hearts = hearts
            save()
        }
    }
    func advance() {
        lesson?.advance()
        if let lesson, lesson.complete {
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
