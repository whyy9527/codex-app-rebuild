import Foundation

public struct Choice: Codable, Equatable, Sendable, Identifiable {
    public let id: String
    public let text: String
    public let audioResource: String?
    public let imageResource: String?
}
public struct WordPair: Codable, Equatable, Sendable, Identifiable {
    public let id: String
    public let left: String
    public let right: String
    public let audioResource: String?
}
public enum QuestionKind: String, Codable, Sendable {
    case choice, matching
    case wordTiles = "word_tiles"
}
public struct Question: Codable, Equatable, Sendable, Identifiable {
    public let id: String
    public let kind: QuestionKind
    public let prompt: String
    public let options: [Choice]
    public let answer: String
    public let words: [Choice]
    public let answerWords: [String]
    public let pairs: [WordPair]
    public let explanation: String
    public let hint: String?
    public let newWord: Bool
    public let rightOrder: [String]?
    public let audioResource: String?
    public let sourceLanguage: String?
    public let characterResource: String?
    public let sourceType: String?
    public let slowAudioResource: String?
    public let dialogueAvatars: [String]?
    public let indicator: String?
    public let example: String?
    public let exampleAudioResource: String?
    public let completionPrefix: String?
    public let completionSuffix: String?
    enum CodingKeys: String, CodingKey {
        case indicator, example, exampleAudioResource, completionPrefix, completionSuffix
        case id, kind, prompt, options, answer, words, pairs, explanation, hint, newWord, rightOrder, audioResource, sourceLanguage, characterResource, sourceType, slowAudioResource, dialogueAvatars
        case answerWords = "answer_words"
    }
    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        id = try c.decode(String.self, forKey: .id)
        kind = try c.decodeIfPresent(QuestionKind.self, forKey: .kind) ?? .choice
        prompt = try c.decode(String.self, forKey: .prompt)
        options = try c.decodeIfPresent([Choice].self, forKey: .options) ?? []
        answer = try c.decodeIfPresent(String.self, forKey: .answer) ?? ""
        words = try c.decodeIfPresent([Choice].self, forKey: .words) ?? []
        answerWords = try c.decodeIfPresent([String].self, forKey: .answerWords) ?? []
        pairs = try c.decodeIfPresent([WordPair].self, forKey: .pairs) ?? []
        explanation = try c.decode(String.self, forKey: .explanation)
        hint = try c.decodeIfPresent(String.self, forKey: .hint)
        newWord = try c.decodeIfPresent(Bool.self, forKey: .newWord) ?? false
        rightOrder = try c.decodeIfPresent([String].self, forKey: .rightOrder)
        audioResource = try c.decodeIfPresent(String.self, forKey: .audioResource)
        sourceLanguage = try c.decodeIfPresent(String.self, forKey: .sourceLanguage)
        sourceType = try c.decodeIfPresent(String.self, forKey: .sourceType)
        slowAudioResource = try c.decodeIfPresent(String.self, forKey: .slowAudioResource)
        dialogueAvatars = try c.decodeIfPresent([String].self, forKey: .dialogueAvatars)
        characterResource = try c.decodeIfPresent(String.self, forKey: .characterResource)
        indicator = try c.decodeIfPresent(String.self, forKey: .indicator)
        example = try c.decodeIfPresent(String.self, forKey: .example)
        exampleAudioResource = try c.decodeIfPresent(String.self, forKey: .exampleAudioResource)
        completionPrefix = try c.decodeIfPresent(String.self, forKey: .completionPrefix)
        completionSuffix = try c.decodeIfPresent(String.self, forKey: .completionSuffix)
    }
    public var correctText: String {
        switch kind {
        case .choice: options.first { $0.id == answer }?.text ?? ""
        case .wordTiles: answerWords.compactMap { id in words.first { $0.id == id }?.text }.joined(separator: " ")
        case .matching: "All pairs matched"
        }
    }
    var valid: Bool {
        func unique(_ ids: [String]) -> Bool { !ids.isEmpty && ids.allSatisfy { !$0.isEmpty } && Set(ids).count == ids.count }
        guard !id.isEmpty, !prompt.isEmpty else { return false }
        switch kind {
        case .choice: return unique(options.map(\.id)) && options.contains { $0.id == answer }
        case .wordTiles: return unique(words.map(\.id)) && unique(answerWords) && answerWords.allSatisfy { id in words.contains { $0.id == id } }
        case .matching: return unique(pairs.map(\.id)) && pairs.allSatisfy { !$0.left.isEmpty && !$0.right.isEmpty }
            && (rightOrder == nil || (unique(rightOrder!) && Set(rightOrder!) == Set(pairs.map(\.id))))
        }
    }
}
public struct LessonInterlude: Codable, Equatable, Sendable, Identifiable {
    public let id: String
    public let afterQuestionID: String
    public let text: String
}
public struct LessonDefinition: Codable, Equatable, Sendable, Identifiable {
    public let id: String
    public let title: String
    public let questions: [Question]
    public let interludes: [LessonInterlude]?
}
public struct CoursePathNode: Codable, Equatable, Sendable {
    public let kind: String
    public let lessonIDs: [String]
    public let lessonCount: Int?
}
public struct HomePresentation: Codable, Equatable, Sendable {
    public let sectionTitle: String
    public let firstNodeLessonCount: Int
    public let pathKinds: [String]
    public let nextSectionTitle: String
    public let flagResource: String
    public let pronunciationResource: String
}
public struct Course: Codable, Equatable, Sendable, Identifiable {
    public let id: String
    public let title: String
    public let lessons: [LessonDefinition]
    public let speechLanguage: String
    public let home: HomePresentation?
    public let interfaceLanguage: String?
    public let pathNodes: [CoursePathNode]?
    public let usesLegacyQuestions: Bool
    // Compatibility for the original single-lesson curriculum.
    public var questions: [Question] { lessons[0].questions }
    enum CodingKeys: String, CodingKey { case id, title, lessons, questions, speechLanguage, pathNodes, interfaceLanguage, home }
    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        id = try c.decode(String.self, forKey: .id)
        title = try c.decode(String.self, forKey: .title)
        home = try c.decodeIfPresent(HomePresentation.self, forKey: .home)
        interfaceLanguage = try c.decodeIfPresent(String.self, forKey: .interfaceLanguage)
        speechLanguage = try c.decodeIfPresent(String.self, forKey: .speechLanguage) ?? "en-US"
        pathNodes = try c.decodeIfPresent([CoursePathNode].self, forKey: .pathNodes)
        if let definitions = try c.decodeIfPresent([LessonDefinition].self, forKey: .lessons) {
            guard !c.contains(.questions) else { throw DecodingError.dataCorruptedError(forKey: .lessons, in: c, debugDescription: "Declare lessons or legacy questions, not both") }
            lessons = definitions
            usesLegacyQuestions = false
        } else {
            lessons = [LessonDefinition(id: "intro", title: title, questions: try c.decode([Question].self, forKey: .questions), interludes: nil)]
            usesLegacyQuestions = true
        }
    }
    public func encode(to encoder: Encoder) throws {
        var c = encoder.container(keyedBy: CodingKeys.self)
        try c.encode(id, forKey: .id); try c.encode(title, forKey: .title)
        try c.encode(speechLanguage, forKey: .speechLanguage)
        try c.encodeIfPresent(interfaceLanguage, forKey: .interfaceLanguage)
        try c.encodeIfPresent(home, forKey: .home)
        try c.encodeIfPresent(pathNodes, forKey: .pathNodes)
        if usesLegacyQuestions { try c.encode(questions, forKey: .questions) }
        else { try c.encode(lessons, forKey: .lessons) }
    }
    public static func readFixture(_ url: URL) throws -> Course {
        struct DataSection: Decodable { let candidate_course: Course }
        struct Fixture: Decodable { let data: DataSection }
        let course = try JSONDecoder().decode(Fixture.self, from: Data(contentsOf: url)).data.candidate_course
        guard !course.id.isEmpty, !course.lessons.isEmpty,
              Set(course.lessons.map(\.id)).count == course.lessons.count,
              course.lessons.allSatisfy({ lesson in
                  !lesson.id.isEmpty && !lesson.questions.isEmpty
                    && Set(lesson.questions.map(\.id)).count == lesson.questions.count
                    && lesson.questions.allSatisfy(\.valid)
              }) else { throw CocoaError(.fileReadCorruptFile) }
        return course
    }
}

public struct Lesson: Equatable, Sendable {
    public let course: Course
    public let lessonIndex: Int
    public var definition: LessonDefinition { course.lessons[lessonIndex] }
    public private(set) var position = 0
    public private(set) var selected: String?
    public private(set) var selectedWords = [String]()
    public private(set) var matchedPairs = Set<String>()
    public private(set) var selectedLeft: String?
    public private(set) var selectedRight: String?
    public private(set) var matchingHint: String?
    public private(set) var feedback: Bool?
    public private(set) var hearts: Int
    public private(set) var review = [Int]()
    public private(set) var reviewing = false
    public private(set) var complete = false
    public private(set) var interlude: LessonInterlude?
    public var question: Question { definition.questions[position] }
    public var canSubmit: Bool {
        guard feedback == nil, !complete, interlude == nil else { return false }
        switch question.kind {
        case .choice: return selected != nil
        case .wordTiles: return !selectedWords.isEmpty
        case .matching: return false
        }
    }
    public init(course: Course, lessonIndex: Int = 0, hearts: Int = 5) {
        precondition(course.lessons.indices.contains(lessonIndex) && hearts >= 0)
        self.course = course; self.lessonIndex = lessonIndex; self.hearts = hearts
    }
    public mutating func choose(_ id: String) {
        guard question.kind == .choice, feedback == nil, !complete, interlude == nil, question.options.contains(where: { $0.id == id }) else { return }
        selected = id
    }
    public mutating func addWord(_ id: String) {
        guard question.kind == .wordTiles, feedback == nil, !complete, interlude == nil,
              question.words.contains(where: { $0.id == id }), !selectedWords.contains(id) else { return }
        selectedWords.append(id)
    }
    public mutating func removeWord(_ id: String) {
        guard question.kind == .wordTiles, feedback == nil, !complete, interlude == nil else { return }
        selectedWords.removeAll { $0 == id }
    }
    public mutating func matchLeft(_ id: String) { selectPair(id, left: true) }
    public mutating func matchRight(_ id: String) { selectPair(id, left: false) }
    private mutating func selectPair(_ id: String, left: Bool) {
        guard question.kind == .matching, feedback == nil, !complete, interlude == nil,
              question.pairs.contains(where: { $0.id == id }), !matchedPairs.contains(id) else { return }
        matchingHint = nil
        if left { selectedLeft = id } else { selectedRight = id }
        if let a = selectedLeft, let b = selectedRight {
            if a == b { matchedPairs.insert(a) }
            else { matchingHint = "Try a different pair." } // Product decision: unobserved wrong-pair penalty.
            selectedLeft = nil; selectedRight = nil
            if matchedPairs.count == question.pairs.count { feedback = true }
        }
    }
    public mutating func submit() {
        guard canSubmit else { return }
        let correct = question.kind == .choice ? selected == question.answer : selectedWords == question.answerWords
        feedback = correct
        if !correct {
            hearts = max(0, hearts - 1)
            if !review.contains(position) { review.append(position) }
        }
    }
    private mutating func clearAnswer() {
        selected = nil; selectedWords = []; matchedPairs = []
        selectedLeft = nil; selectedRight = nil; matchingHint = nil; feedback = nil
    }
    public mutating func advance() {
        if interlude != nil { interlude = nil; return }
        guard feedback != nil, !complete else { return }
        let answeredID = question.id
        if reviewing {
            if feedback == true { review.removeAll { $0 == position } }
        } else if position + 1 < definition.questions.count {
            position += 1; clearAnswer()
            interlude = definition.interludes?.first { $0.afterQuestionID == answeredID }
            return
        } else { reviewing = true }
        if let next = review.first { position = next }
        else { complete = true }
        clearAnswer()
    }
}

public struct LearningProgress: Codable, Equatable, Sendable {
    public var completedCourses: Set<String> = []
    public var completedLessons: [String: Set<String>] = [:]
    public var hearts = 5
    public init() {}
    enum CodingKeys: String, CodingKey { case completedCourses, completedLessons, hearts }
    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        guard c.contains(.completedCourses) || c.contains(.completedLessons) else {
            throw DecodingError.dataCorruptedError(forKey: .completedCourses, in: c, debugDescription: "Stored progress must contain a completion collection")
        }
        completedCourses = c.contains(.completedCourses) ? try c.decode(Set<String>.self, forKey: .completedCourses) : []
        completedLessons = c.contains(.completedLessons) ? try c.decode([String: Set<String>].self, forKey: .completedLessons) : [:]
        hearts = c.contains(.hearts) ? try c.decode(Int.self, forKey: .hearts) : 5
        guard hearts >= 0 else { throw DecodingError.dataCorruptedError(forKey: .hearts, in: c, debugDescription: "Hearts cannot be negative") }
    }
    public func isCompleted(_ course: Course, index: Int) -> Bool {
        guard course.lessons.indices.contains(index) else { return false }
        return completedLessons[course.id, default: []].contains(course.lessons[index].id)
            || course.usesLegacyQuestions && completedCourses.contains(course.id)
    }
    public func completedCount(_ course: Course) -> Int {
        course.lessons.indices.prefix { isCompleted(course, index: $0) }.count
    }
    public func isUnlocked(_ course: Course, index: Int) -> Bool {
        course.lessons.indices.contains(index) && (0..<index).allSatisfy { isCompleted(course, index: $0) }
    }
    @discardableResult public mutating func markCompleted(_ course: Course, index: Int) -> Bool {
        guard isUnlocked(course, index: index) else { return false }
        completedLessons[course.id, default: []].insert(course.lessons[index].id)
        if completedCount(course) == course.lessons.count { completedCourses.insert(course.id) }
        return true
    }
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
