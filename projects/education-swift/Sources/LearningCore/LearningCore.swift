import Foundation

public struct Choice: Codable, Equatable, Sendable, Identifiable {
    public let id: String
    public let text: String
}
public struct Question: Codable, Equatable, Sendable, Identifiable {
    public let id: String
    public let prompt: String
    public let options: [Choice]
    public let answer: String
    public let explanation: String
}
public struct Course: Codable, Equatable, Sendable, Identifiable {
    public let id: String
    public let title: String
    public let questions: [Question]
    public static func readFixture(_ url: URL) throws -> Course {
        struct DataSection: Decodable { let candidate_course: Course }
        struct Fixture: Decodable { let data: DataSection }
        let course = try JSONDecoder().decode(Fixture.self, from: Data(contentsOf: url)).data.candidate_course
        guard !course.questions.isEmpty, Set(course.questions.map(\.id)).count == course.questions.count,
              course.questions.allSatisfy({ question in
                  !question.options.isEmpty && Set(question.options.map(\.id)).count == question.options.count
                      && question.options.contains(where: { $0.id == question.answer })
              }) else {
            throw CocoaError(.fileReadCorruptFile)
        }
        return course
    }
}

public struct Lesson: Equatable, Sendable {
    public let course: Course
    public private(set) var position = 0
    public private(set) var selected: String?
    public private(set) var feedback: Bool?
    public private(set) var hearts = 5
    public private(set) var review = [Int]()
    public private(set) var reviewing = false
    public private(set) var complete = false
    public var question: Question { course.questions[position] }
    public var canSubmit: Bool { selected != nil && feedback == nil && !complete }

    public init(course: Course) { self.course = course }
    public mutating func choose(_ id: String) {
        guard feedback == nil, !complete, question.options.contains(where: { $0.id == id }) else { return }
        selected = id
    }
    public mutating func submit() {
        guard canSubmit else { return }
        let correct = selected == question.answer
        feedback = correct
        if !correct {
            hearts = max(0, hearts - 1)
            if !review.contains(position) { review.append(position) }
        }
    }
    public mutating func advance() {
        guard feedback != nil, !complete else { return }
        if reviewing {
            if feedback == true { review.removeAll { $0 == position } }
        } else if position + 1 < course.questions.count {
            position += 1
            selected = nil
            feedback = nil
            return
        } else { reviewing = true }
        if let next = review.first { position = next }
        else { complete = true }
        selected = nil
        feedback = nil
    }
}

public struct LearningProgress: Codable, Equatable, Sendable {
    public var completedCourses: Set<String> = []
    public init() {}
}
public struct ProgressStore: Sendable {
    public let url: URL
    public init(url: URL) { self.url = url }
    public func load() throws -> LearningProgress {
        guard FileManager.default.fileExists(atPath: url.path) else { return LearningProgress() }
        return try JSONDecoder().decode(LearningProgress.self, from: Data(contentsOf: url))
    }
    public func save(_ progress: LearningProgress) throws {
        try FileManager.default.createDirectory(at: url.deletingLastPathComponent(), withIntermediateDirectories: true)
        try JSONEncoder().encode(progress).write(to: url, options: .atomic)
    }
}
