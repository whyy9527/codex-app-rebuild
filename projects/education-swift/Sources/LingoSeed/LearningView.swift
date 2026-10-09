import SwiftUI
import LearningCore

struct LearningView: View {
    @Bindable var model: LearningModel
    private let ink = Color(red: 0.09, green: 0.22, blue: 0.25)
    private let accent = Color(red: 0.0, green: 0.43, blue: 0.40)
    private let columns = [GridItem(.adaptive(minimum: 130), spacing: 12)]
    var body: some View {
        VStack(alignment: .leading, spacing: 18) {
            HStack {
                Label("LingoSeed", systemImage: "leaf.fill").font(.title2.bold()).foregroundStyle(accent)
                Spacer()
                Text("A little practice. A new possibility.").foregroundStyle(.secondary)
            }
            Divider()
            ScrollView {
                VStack(alignment: .leading, spacing: 22) {
                    if let lesson = model.lesson {
                        HStack {
                            if !lesson.complete {
                                Button("Close lesson", systemImage: "xmark") { model.confirmingExit = true }.accessibilityIdentifier("quit")
                            }
                            Spacer()
                            Text("♥ \(lesson.hearts)").font(.title3.bold()).foregroundStyle(.pink)
                                .accessibilityIdentifier("hearts").accessibilityValue(String(lesson.hearts))
                        }
                        if model.confirmingExit { exitConfirmation }
                        else if lesson.complete { completion }
                        else { question(lesson) }
                    } else { path }
                }.padding(.vertical, 12).frame(maxWidth: .infinity, alignment: .leading)
            }
            if let error = model.error {
                HStack {
                    Text(error).foregroundStyle(.red)
                    Button("Retry saving") { model.save() }
                }
            }
        }
        .padding(36).frame(minWidth: 760, minHeight: 680)
        .foregroundStyle(ink).background(Color(red: 0.96, green: 0.97, blue: 0.94))
    }
    private var exitConfirmation: some View {
        VStack(alignment: .leading, spacing: 22) {
            Text("Leave this lesson?").font(.largeTitle.bold()).accessibilityIdentifier("exit-title")
            Text("Your finished lessons are safe. This unfinished attempt will be discarded.").foregroundStyle(.secondary)
            Button("Keep learning") { model.confirmingExit = false }.buttonStyle(.borderedProminent).tint(accent).accessibilityIdentifier("cancel-quit")
            Button("End session") { model.discardAttempt() }.accessibilityIdentifier("confirm-quit")
        }.padding(.vertical, 32)
    }
    private var completion: some View {
        VStack(alignment: .leading, spacing: 20) {
            Image(systemName: "checkmark.seal.fill").font(.system(size: 64)).foregroundStyle(accent)
            Text("Lesson complete").font(.largeTitle.bold()).accessibilityIdentifier("lesson-complete")
            Text("You made time for your next step.").foregroundStyle(.secondary)
            Button("Back to your path") { model.discardAttempt() }
                .buttonStyle(.borderedProminent).tint(accent).accessibilityIdentifier("return-path")
        }.padding(.vertical, 32)
    }
    private var path: some View {
        VStack(alignment: .leading, spacing: 20) {
            Text("Your learning path").font(.system(size: 38, weight: .bold)).accessibilityIdentifier("course-entry")
            Text(model.course.title).font(.title3).foregroundStyle(.secondary)
            Text("\(model.progress.completedCount(model.course)) of \(model.course.lessons.count) lessons complete")
                .accessibilityIdentifier("completed-count").accessibilityValue(String(model.progress.completedCount(model.course)))
            ForEach(model.course.lessons.indices, id: \.self) { index in
                let definition = model.course.lessons[index]
                let completed = model.progress.isCompleted(model.course, index: index)
                let unlocked = model.progress.isUnlocked(model.course, index: index)
                HStack(alignment: .top, spacing: 22) {
                    Image(systemName: completed ? "checkmark.circle.fill" : unlocked ? "circle.dotted" : "lock.circle")
                        .font(.system(size: 38)).foregroundStyle(unlocked ? accent : .gray)
                    VStack(alignment: .leading, spacing: 12) {
                        Text("LESSON \(index + 1)").font(.caption.bold()).foregroundStyle(.secondary)
                        Text(definition.title).font(.title2.bold())
                        Text("\(definition.questions.count) short activities · \(completed ? "Completed" : unlocked ? "Ready for you" : "Finish the previous lesson to unlock")")
                            .foregroundStyle(.secondary)
                        Button(completed ? "Practice again" : "Start lesson") { model.begin(index) }
                            .buttonStyle(.borderedProminent).tint(accent).controlSize(.large)
                            .disabled(!unlocked).accessibilityIdentifier(index == 0 ? "start-lesson" : "start-lesson-\(index)")
                    }
                    Spacer(minLength: 0)
                }.padding(24).frame(maxWidth: .infinity, alignment: .leading)
                    .background(.white, in: RoundedRectangle(cornerRadius: 22))
            }
            Text("Small steps grow into everyday skills.").foregroundStyle(.secondary)
        }
    }
    @ViewBuilder private func question(_ lesson: Lesson) -> some View {
        if lesson.reviewing {
            Text("ONE MORE LOOK").font(.caption.bold()).foregroundStyle(accent).accessibilityIdentifier("review-label")
        } else { Text(model.course.title.uppercased()).font(.caption.bold()).foregroundStyle(accent) }
        ProgressView(value: Double(lesson.position + 1), total: Double(lesson.definition.questions.count)).tint(accent)
            .accessibilityLabel("Lesson progress")
        Text(lesson.question.prompt).font(.system(size: 30, weight: .bold))
            .accessibilityIdentifier("question-title").accessibilityValue(lesson.question.prompt)
        switch lesson.question.kind {
        case .choice: choices(lesson)
        case .wordTiles: words(lesson)
        case .matching: matching(lesson)
        }
        if let correct = lesson.feedback {
            VStack(alignment: .leading, spacing: 14) {
                Text(correct ? "Well done!" : "Correct answer: \(lesson.question.correctText)")
                    .font(.title3.bold()).foregroundStyle(correct ? accent : .orange)
                    .accessibilityIdentifier("feedback").accessibilityValue(correct ? "correct" : "incorrect")
                Text(lesson.question.explanation).foregroundStyle(.secondary)
                Button("Continue") { model.advance() }.buttonStyle(.borderedProminent).tint(accent).controlSize(.large)
                    .accessibilityIdentifier("continue")
            }.padding(.top, 8)
        } else if lesson.question.kind != .matching {
            Button("Check answer") { model.submit() }.buttonStyle(.borderedProminent).tint(accent).controlSize(.large)
                .disabled(!lesson.canSubmit).accessibilityIdentifier("check")
        }
    }
    private func choices(_ lesson: Lesson) -> some View {
        VStack(spacing: 12) {
            ForEach(lesson.question.options) { option in
                Button { model.lesson?.choose(option.id) } label: {
                    HStack {
                        Image(systemName: lesson.selected == option.id ? "checkmark.circle.fill" : "circle")
                        Text(option.text).font(.title3.weight(.medium)); Spacer()
                    }.padding(14).frame(maxWidth: .infinity)
                }.buttonStyle(.bordered).tint(lesson.selected == option.id ? accent : ink)
                    .disabled(lesson.feedback != nil).accessibilityIdentifier("option-" + option.id)
                    .accessibilityValue(lesson.selected == option.id ? "selected" : "not selected")
            }
        }
    }
    private func words(_ lesson: Lesson) -> some View {
        VStack(alignment: .leading, spacing: 18) {
            VStack(alignment: .leading, spacing: 12) {
                Text("YOUR PHRASE").font(.caption.bold()).foregroundStyle(.secondary)
                if lesson.selectedWords.isEmpty { Text("Choose words in order.").foregroundStyle(.secondary).frame(height: 42) }
                LazyVGrid(columns: columns, alignment: .leading, spacing: 12) {
                    ForEach(lesson.selectedWords, id: \.self) { id in
                        Button(lesson.question.words.first { $0.id == id }!.text) { model.lesson?.removeWord(id) }
                            .buttonStyle(.borderedProminent).tint(accent).controlSize(.large).disabled(lesson.feedback != nil)
                            .accessibilityIdentifier("selected-word-" + id)
                    }
                }
            }.padding(20).frame(maxWidth: .infinity, alignment: .leading).background(.white, in: RoundedRectangle(cornerRadius: 18))
            LazyVGrid(columns: columns, alignment: .leading, spacing: 12) {
                ForEach(lesson.question.words) { word in
                    Button(word.text) { model.lesson?.addWord(word.id) }.buttonStyle(.bordered).controlSize(.large)
                        .disabled(lesson.feedback != nil || lesson.selectedWords.contains(word.id)).accessibilityIdentifier("word-bank-" + word.id)
                }
            }
            Text("Tap a word in your phrase to put it back.").font(.callout).foregroundStyle(.secondary)
        }
    }
    private func matching(_ lesson: Lesson) -> some View {
        VStack(alignment: .leading, spacing: 14) {
            Text(lesson.matchingHint ?? "Choose an expression, then its meaning.").foregroundStyle(.secondary)
            HStack(alignment: .top, spacing: 20) {
                VStack(spacing: 12) {
                    ForEach(lesson.question.pairs) { pair in
                        Button(pair.left) { model.lesson?.matchLeft(pair.id) }
                            .frame(maxWidth: .infinity).buttonStyle(.bordered).controlSize(.large)
                            .tint(lesson.selectedLeft == pair.id ? accent : ink)
                            .disabled(lesson.feedback != nil || lesson.matchedPairs.contains(pair.id)).accessibilityIdentifier("pair-left-" + pair.id)
                    }
                }
                VStack(spacing: 12) {
                    ForEach(lesson.question.pairs.reversed()) { pair in
                        Button(pair.right) { model.lesson?.matchRight(pair.id) }
                            .frame(maxWidth: .infinity).buttonStyle(.bordered).controlSize(.large)
                            .tint(lesson.selectedRight == pair.id ? accent : ink)
                            .disabled(lesson.feedback != nil || lesson.matchedPairs.contains(pair.id)).accessibilityIdentifier("pair-right-" + pair.id)
                    }
                }
            }
        }
    }
}
