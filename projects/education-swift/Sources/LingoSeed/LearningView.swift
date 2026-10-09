import SwiftUI
import LearningCore

struct LearningView: View {
    @Bindable var model: LearningModel
    private let ink = Color(white: 0.28)
    private let accent = Color(red: 0.345, green: 0.8, blue: 0)
    private let columns = [GridItem(.adaptive(minimum: 130), spacing: 12)]
    var body: some View {
        GeometryReader { geometry in
            VStack(spacing: 0) {
                if let lesson = model.lesson {
                    lessonPage(lesson)
                } else {
                    HStack(spacing: 0) {
                        sidebar(compact: geometry.size.width < 1180)
                        Divider()
                        ScrollView {
                            if model.destination == "Learn" { path }
                            else { destinationPage }
                        }.frame(maxWidth: .infinity)
                        if geometry.size.width >= 980 {
                            ScrollView { dashboard }.frame(width: 280).padding(.trailing, 20)
                        }
                    }
                }
                if let error = model.error {
                    HStack { Text(error).foregroundStyle(.red); Button("Retry saving") { model.save() } }.padding(8)
                }
            }
        }
        .frame(minWidth: 780, minHeight: 660)
        .fontDesign(.rounded).foregroundStyle(ink).background(.white)
        .sheet(isPresented: $model.showingGuide) {
            VStack(alignment: .leading, spacing: 24) {
                Text("Unit guidebook").font(.largeTitle.bold())
                Text(model.course.title).font(.title2.bold())
                Text("Practice greetings, match expressions with their meaning, and build short phrases. Mistakes return at the end so you can try again.")
                ForEach(model.course.lessons.indices, id: \.self) { i in Text("\(i + 1). \(model.course.lessons[i].title)").font(.headline) }
                Button("Back to learning") { model.showingGuide = false }.buttonStyle(SeedButtonStyle(fill: accent))
            }.padding(40).frame(width: 500)
        }
    }
    private func sidebar(compact: Bool) -> some View {
        VStack(alignment: .leading, spacing: 15) {
            Text(compact ? "ls" : "lingoseed").font(.system(size: 34, weight: .heavy)).foregroundStyle(accent).padding(.bottom, 25)
            ForEach(["Learn", "Leaderboards", "Quests", "Shop", "Profile", "More"], id: \.self) { item in
                Button { model.destination = item } label: {
                    HStack(spacing: 18) {
                        Image(systemName: icon(item)).font(.system(size: 25, weight: .bold)).foregroundStyle(item == "Learn" ? accent : .orange).frame(width: 34)
                        if !compact { Text(item.uppercased()).font(.system(size: 15, weight: .heavy)).tracking(0.5).lineLimit(1).minimumScaleFactor(0.8) }
                        Spacer(minLength: 0)
                    }.padding(15).background(model.destination == item ? Color.cyan.opacity(0.12) : .clear, in: RoundedRectangle(cornerRadius: 13))
                        .overlay(RoundedRectangle(cornerRadius: 13).stroke(model.destination == item ? Color.cyan.opacity(0.45) : .clear, lineWidth: 2))
                }.buttonStyle(.plain).accessibilityIdentifier("nav-" + item.lowercased())
            }
            Spacer()
            Button { model.toggleMute() } label: { Label(model.muted ? "Sound off" : "Sound on", systemImage: model.muted ? "speaker.slash.fill" : "speaker.wave.2.fill") }
                .buttonStyle(.plain).accessibilityIdentifier("sound-toggle").accessibilityValue(model.muted ? "muted" : "on").padding(15)
        }.padding(24).frame(width: compact ? 92 : 226)
    }
    private func icon(_ name: String) -> String {
        switch name { case "Learn": "house.fill"; case "Leaderboards": "shield.fill"; case "Quests": "shippingbox.fill"; case "Shop": "storefront.fill"; case "Profile": "person.crop.circle.fill"; default: "ellipsis.circle.fill" }
    }
    private var dashboard: some View {
        VStack(alignment: .leading, spacing: 22) {
            HStack { Label("EN", systemImage: "globe"); Spacer(); Label("\(model.progress.completedCount(model.course) * 10)", systemImage: "bolt.fill").foregroundStyle(.orange); Spacer(); Label("\(model.progress.hearts)", systemImage: "heart.fill").foregroundStyle(.red) }.font(.headline).padding(.vertical, 20)
            card("Your learning milestones") {
                Label("\(model.progress.completedCount(model.course)) lessons complete", systemImage: "shield.lefthalf.filled").font(.title3.bold())
                Text("Learn at your own pace. Every completed lesson is saved on this device.").foregroundStyle(.secondary)
            }
            card("Daily practice") {
                Label("Complete a lesson", systemImage: "bolt.fill").font(.headline)
                ProgressView(value: Double(min(model.progress.completedCount(model.course), 1)), total: 1).tint(.yellow)
                Button("VIEW QUESTS") { model.destination = "Quests" }.buttonStyle(.plain).foregroundStyle(.cyan)
            }
            card("Your progress stays with you") {
                Text("Your local profile works offline. Online accounts and competitive rankings are not connected.").foregroundStyle(.secondary)
                Button("VIEW PROFILE") { model.destination = "Profile" }.buttonStyle(SeedButtonStyle(fill: accent))
            }
        }.padding(.top, 20)
    }
    private func card<Content: View>(_ title: String, @ViewBuilder content: () -> Content) -> some View {
        VStack(alignment: .leading, spacing: 23) { Text(title).font(.title3.bold()); content() }.padding(23).frame(maxWidth: .infinity, alignment: .leading)
            .overlay(RoundedRectangle(cornerRadius: 18).stroke(Color.gray.opacity(0.22), lineWidth: 2))
    }
    private var destinationPage: some View {
        VStack(alignment: .leading, spacing: 26) {
            Text(model.destination).font(.largeTitle.bold())
            switch model.destination {
            case "Quests": Text("Practice a lesson").font(.title2.bold()); Text("\(min(model.progress.completedCount(model.course), 1)) / 1 complete in this course")
            case "Profile": Text("Local learner").font(.title2.bold()); Text("\(model.progress.completedCount(model.course)) completed lessons · \(model.progress.hearts) hearts"); Text("Progress is saved on this device. Account synchronization is not connected.")
            case "Leaderboards": Text("Keep learning at your own pace.").font(.title2.bold()); Text("Online competitions are not connected in this local education base.")
            case "Shop": Text("Everything here is free to practice.").font(.title2.bold()); Text("Purchases and subscriptions are not connected.")
            default: Button(model.muted ? "Turn sound on" : "Turn sound off") { model.toggleMute() }.buttonStyle(SeedButtonStyle(fill: accent)); Text("LingoSeed · original lessons and sounds, inspired by the reference learning flow.")
            }
            Button("Back to learning") { model.destination = "Learn" }.buttonStyle(SeedButtonStyle(fill: accent))
        }.padding(40).frame(maxWidth: 680, alignment: .leading)
    }
    private func lessonPage(_ lesson: Lesson) -> some View {
        VStack(spacing: 0) {
            HStack(spacing: 24) {
                if !lesson.complete { Button { model.confirmingExit = true } label: { Image(systemName: "xmark").font(.title2.bold()).foregroundStyle(.gray) }.buttonStyle(.plain).accessibilityIdentifier("quit") }
                ProgressView(value: Double(lesson.position + 1), total: Double(lesson.definition.questions.count)).tint(accent).scaleEffect(y: 2)
                Text("♥ \(lesson.hearts)").font(.title2.bold()).foregroundStyle(.red).accessibilityIdentifier("hearts").accessibilityValue(String(lesson.hearts))
                Button { model.toggleMute() } label: { Image(systemName: model.muted ? "speaker.slash.fill" : "speaker.wave.2.fill") }.buttonStyle(.plain).accessibilityIdentifier("sound-toggle").accessibilityValue(model.muted ? "muted" : "on")
            }.padding(.horizontal, 60).padding(.vertical, 35)
            Spacer(minLength: 0)
            ScrollView {
                VStack(alignment: .leading, spacing: 28) {
                    if model.confirmingExit { exitConfirmation }
                    else if lesson.complete { completion }
                    else { question(lesson) }
                }.padding(30).frame(maxWidth: 660).frame(maxWidth: .infinity)
            }
            Spacer(minLength: 0)
            if !lesson.complete && !model.confirmingExit { answerBar(lesson) }
        }
    }
    private func answerBar(_ lesson: Lesson) -> some View {
        HStack(spacing: 30) {
            if let correct = lesson.feedback {
                VStack(alignment: .leading, spacing: 8) {
                    Text(correct ? "Well done!" : "Correct answer: \(lesson.question.correctText)").font(.title2.bold())
                        .foregroundStyle(correct ? Color.green : Color.red).accessibilityIdentifier("feedback").accessibilityValue(correct ? "correct" : "incorrect")
                    Text(lesson.question.explanation)
                }
                Spacer()
                Button("CONTINUE") { model.advance() }.buttonStyle(SeedButtonStyle(fill: correct ? accent : .red)).accessibilityIdentifier("continue")
            } else {
                Text(lesson.question.kind == .matching ? "Match all pairs to continue" : "Take your time. You’ve got this.").foregroundStyle(.secondary)
                Spacer()
                if lesson.question.kind != .matching { Button("CHECK") { model.submit() }.buttonStyle(SeedButtonStyle(fill: accent)).disabled(!lesson.canSubmit).accessibilityIdentifier("check") }
            }
        }.padding(.horizontal, 60).padding(.vertical, 28).frame(minHeight: 115)
            .background(lesson.feedback == nil ? Color.white : lesson.feedback == true ? Color.green.opacity(0.13) : Color.red.opacity(0.1))
            .overlay(alignment: .top) { Rectangle().fill(Color.gray.opacity(0.15)).frame(height: 2) }
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
        VStack(spacing: 28) {
            HStack(alignment: .center) {
                VStack(alignment: .leading, spacing: 9) {
                    Text("SECTION 1, UNIT 1").font(.headline).opacity(0.8)
                    Text(model.course.title).font(.system(size: 26, weight: .heavy)).accessibilityIdentifier("course-entry")
                }
                Spacer(minLength: 10)
                Button { model.showingGuide = true } label: { Label("GUIDEBOOK", systemImage: "text.book.closed.fill").font(.headline) }.buttonStyle(SeedButtonStyle(fill: accent))
            }.padding(23).foregroundStyle(.white).background(accent, in: RoundedRectangle(cornerRadius: 17))
            Text("\(model.progress.completedCount(model.course)) of \(model.course.lessons.count) lessons complete").font(.caption.bold()).foregroundStyle(.secondary)
                .accessibilityIdentifier("completed-count").accessibilityValue(String(model.progress.completedCount(model.course)))
            ForEach(model.course.lessons.indices, id: \.self) { index in
                let completed = model.progress.isCompleted(model.course, index: index)
                let unlocked = model.progress.isUnlocked(model.course, index: index)
                VStack(spacing: 14) {
                    if unlocked && !completed { Text("START").font(.headline.bold()).foregroundStyle(accent).padding(12).background(.white, in: RoundedRectangle(cornerRadius: 12)).overlay(RoundedRectangle(cornerRadius: 12).stroke(Color.gray.opacity(0.2), lineWidth: 2)) }
                    Button { model.begin(index) } label: {
                        Image(systemName: completed ? "checkmark" : unlocked ? "star.fill" : "lock.fill").font(.system(size: 32, weight: .heavy)).foregroundStyle(unlocked ? .white : .gray)
                            .frame(width: 83, height: 74).background(unlocked ? accent : Color(white: 0.9), in: Ellipse())
                            .shadow(color: unlocked ? Color(red: 0.28, green: 0.62, blue: 0) : Color(white: 0.72), radius: 0, y: 8)
                            .padding(9).overlay(Ellipse().stroke(unlocked && !completed ? accent.opacity(0.3) : .clear, lineWidth: 5))
                    }.buttonStyle(.plain).disabled(!unlocked).accessibilityLabel(completed ? "Practice again: " + model.course.lessons[index].title : "Start lesson: " + model.course.lessons[index].title)
                        .accessibilityIdentifier(index == 0 ? "start-lesson" : "start-lesson-\(index)")
                    Text(model.course.lessons[index].title).font(.headline).foregroundStyle(unlocked ? ink : .gray)
                }.offset(x: index % 2 == 0 ? 25 : -60).padding(.vertical, 12)
            }
            Image(systemName: "leaf.circle.fill").font(.system(size: 85)).foregroundStyle(accent).offset(x: 100)
            Text("More lessons will grow here.").foregroundStyle(.secondary).padding(.bottom, 40)
        }.padding(30).frame(maxWidth: 720).frame(maxWidth: .infinity)
    }
    @ViewBuilder private func question(_ lesson: Lesson) -> some View {
        if lesson.reviewing {
            Text("ONE MORE LOOK").font(.caption.bold()).foregroundStyle(accent).accessibilityIdentifier("review-label")
        } else { Text(model.course.title.uppercased()).font(.caption.bold()).foregroundStyle(accent) }
        Text(lesson.question.prompt).font(.system(size: 30, weight: .bold))
            .accessibilityIdentifier("question-title").accessibilityValue(lesson.question.prompt)
        switch lesson.question.kind {
        case .choice: choices(lesson)
        case .wordTiles: words(lesson)
        case .matching: matching(lesson)
        }
        if lesson.question.kind != .matching {
            Button { model.pronounce() } label: { Label("Read the instruction", systemImage: "speaker.wave.2.fill") }.buttonStyle(.plain).foregroundStyle(.cyan).accessibilityIdentifier("pronounce")
        }
    }
    private func choices(_ lesson: Lesson) -> some View {
        VStack(spacing: 12) {
            ForEach(lesson.question.options) { option in
                Button { model.choose(option.id) } label: {
                    HStack {
                        Image(systemName: lesson.selected == option.id ? "checkmark.circle.fill" : "circle")
                        Text(option.text).font(.title3.weight(.medium)); Spacer()
                    }.padding(14).frame(maxWidth: .infinity)
                }.buttonStyle(SeedButtonStyle(fill: lesson.selected == option.id ? Color.cyan.opacity(0.12) : .white, foreground: ink))
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
                        Button(lesson.question.words.first { $0.id == id }!.text) { model.removeWord(id) }
                            .buttonStyle(.borderedProminent).tint(accent).controlSize(.large).disabled(lesson.feedback != nil)
                            .accessibilityIdentifier("selected-word-" + id)
                    }
                }
            }.padding(20).frame(maxWidth: .infinity, alignment: .leading).background(.white, in: RoundedRectangle(cornerRadius: 18))
            LazyVGrid(columns: columns, alignment: .leading, spacing: 12) {
                ForEach(lesson.question.words) { word in
                    Button(word.text) { model.addWord(word.id) }.buttonStyle(.bordered).controlSize(.large)
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
                        Button(pair.left) { model.match(pair.id, left: true) }
                            .frame(maxWidth: .infinity).buttonStyle(.bordered).controlSize(.large)
                            .tint(lesson.selectedLeft == pair.id ? accent : ink)
                            .disabled(lesson.feedback != nil || lesson.matchedPairs.contains(pair.id)).accessibilityIdentifier("pair-left-" + pair.id)
                    }
                }
                VStack(spacing: 12) {
                    ForEach(lesson.question.pairs.reversed()) { pair in
                        Button(pair.right) { model.match(pair.id, left: false) }
                            .frame(maxWidth: .infinity).buttonStyle(.bordered).controlSize(.large)
                            .tint(lesson.selectedRight == pair.id ? accent : ink)
                            .disabled(lesson.feedback != nil || lesson.matchedPairs.contains(pair.id)).accessibilityIdentifier("pair-right-" + pair.id)
                    }
                }
            }
        }
    }
}

struct SeedButtonStyle: ButtonStyle {
    var fill: Color
    var foreground: Color = .white
    @Environment(\.isEnabled) private var enabled
    func makeBody(configuration: Configuration) -> some View {
        configuration.label.font(.system(size: 16, weight: .bold, design: .rounded)).padding(.horizontal, 24).padding(.vertical, 16)
            .frame(minWidth: 110).foregroundStyle(enabled ? foreground : Color.gray)
            .background {
                RoundedRectangle(cornerRadius: 13).fill(enabled ? fill : Color(white: 0.9))
                    .shadow(color: Color.black.opacity(0.18), radius: 0, y: configuration.isPressed ? 0 : 4)
            }
            .overlay(RoundedRectangle(cornerRadius: 13).stroke(Color.black.opacity(0.12), lineWidth: 2))
            .offset(y: configuration.isPressed ? 4 : 0)
    }
}
