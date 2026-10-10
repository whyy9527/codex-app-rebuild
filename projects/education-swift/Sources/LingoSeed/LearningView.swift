import SwiftUI
import LearningCore

struct LearningView: View {
    @Bindable var model: LearningModel
    private var chinese: Bool { model.course.interfaceLanguage == "zh" }
    private func copy(_ english: String, _ zh: String) -> String { chinese ? zh : english }
    private let ink = Color(white: 0.28)
    private let accent = Color(red: 0.345, green: 0.8, blue: 0)
    private let columns = [GridItem(.adaptive(minimum: 110), spacing: 12)]
    var body: some View {
        GeometryReader { geometry in
            VStack(spacing: 0) {
                if let lesson = model.lesson {
                    lessonPage(lesson)
                } else if ["Learn", "Settings", "Guidebook"].contains(model.destination) {
                    ReferenceHome(model: model)
                } else {
                    HStack(spacing: 0) {
                        sidebar(compact: geometry.size.width < 1180)
                        Divider()
                        ScrollView {
                            destinationPage
                        }.frame(maxWidth: .infinity)
                        if geometry.size.width >= 1120 {
                            ScrollView { dashboard }.frame(width: 350).padding(.trailing, 24)
                        }
                    }
                }
                if let error = model.error {
                    HStack { Text(error).foregroundStyle(.red); Button("Retry saving") { model.save() } }.padding(8)
                }
            }
        }
        .frame(minWidth: 780, minHeight: 660)
        .foregroundStyle(ink).background(ReferenceStyle.background)
        .preferredColorScheme(model.preferences.darkMode == "On" ? .dark : model.preferences.darkMode == "Off" ? .light : nil)

    }
    private func sidebar(compact: Bool) -> some View {
        VStack(alignment: .leading, spacing: 15) {
            Text(compact ? "ls" : "lingoseed").font(.system(size: 34, weight: .heavy)).foregroundStyle(accent).padding(.bottom, 25)
            ForEach(["Learn", "Leaderboards", "Quests", "Shop", "Profile", "More"], id: \.self) { item in
                Button { model.destination = item } label: {
                    HStack(spacing: 12) {
                        Image(systemName: icon(item)).font(.system(size: 25, weight: .bold)).foregroundStyle(item == "Learn" ? accent : .orange).frame(width: 34)
                        if !compact { Text(item.uppercased()).font(.system(size: 13, weight: .bold)).tracking(0.2).fixedSize(horizontal: true, vertical: false) }
                        Spacer(minLength: 0)
                    }.padding(15).background(model.destination == item ? Color.cyan.opacity(0.12) : .clear, in: RoundedRectangle(cornerRadius: 13))
                        .overlay(RoundedRectangle(cornerRadius: 13).stroke(model.destination == item ? Color.cyan.opacity(0.45) : .clear, lineWidth: 2))
                }.buttonStyle(.plain).accessibilityLabel(item).accessibilityIdentifier("nav-" + item.lowercased())
            }
            Spacer()
            Button { model.toggleMute() } label: { Label(model.muted ? "Sound off" : "Sound on", systemImage: model.muted ? "speaker.slash.fill" : "speaker.wave.2.fill") }
                .buttonStyle(.plain).accessibilityLabel(model.muted ? "Sound off" : "Sound on").accessibilityIdentifier("sound-toggle").accessibilityValue(model.muted ? "muted" : "on").padding(15)
        }.padding(24).frame(width: compact ? 92 : 252)
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
            card("Course goal") {
                Label("Complete a lesson", systemImage: "bolt.fill").font(.headline)
                ProgressView(value: Double(min(model.progress.completedCount(model.course), 1)), total: 1).tint(.yellow)
                Button("VIEW QUESTS") { model.destination = "Quests" }.buttonStyle(.plain).foregroundStyle(.cyan).accessibilityIdentifier("view-quests")
            }
            card("Your progress stays with you") {
                Text("Your local profile works offline. Online accounts and competitive rankings are not connected.").foregroundStyle(.secondary)
                Button("VIEW PROFILE") { model.destination = "Profile" }.buttonStyle(SeedButtonStyle(fill: accent)).accessibilityIdentifier("view-profile")
            }
        }.padding(.top, 20)
    }
    private func card<Content: View>(_ title: String, @ViewBuilder content: () -> Content) -> some View {
        VStack(alignment: .leading, spacing: 23) { Text(title).font(.title3.bold()); content() }.padding(23).frame(maxWidth: .infinity, alignment: .leading)
            .overlay(RoundedRectangle(cornerRadius: 18).stroke(Color.gray.opacity(0.22), lineWidth: 2))
    }
    private var destinationPage: some View {
        VStack(alignment: .leading, spacing: 26) {
            HStack(spacing: 16) {
                Image(systemName: icon(model.destination)).font(.system(size: 36, weight: .bold)).foregroundStyle(model.destination == "Profile" ? .purple : .orange)
                Text(model.destination).font(.largeTitle.bold()).accessibilityIdentifier("destination-title").accessibilityValue(model.destination)
            }
            switch model.destination {
            case "Quests":
                card("Your course goal") {
                    Label("Complete a lesson", systemImage: "bolt.fill").font(.title3.bold()).foregroundStyle(.orange)
                    Text("\(min(model.progress.completedCount(model.course), 1)) / 1 complete in this course")
                    ProgressView(value: Double(min(model.progress.completedCount(model.course), 1)), total: 1).tint(.yellow)
                    Text("Every lesson is a step forward.").foregroundStyle(.secondary)
                    practiceButton
                }
            case "Profile":
                HStack(spacing: 24) { SeedMascot(); VStack(alignment: .leading, spacing: 8) { Text("Local learner").font(.title2.bold()); Text("Everyday practice, at your pace.").foregroundStyle(.secondary) } }
                card("Your learning") {
                    Label("\(model.progress.completedCount(model.course)) completed lessons", systemImage: "checkmark.seal.fill").font(.title3.bold()).foregroundStyle(accent)
                    Label("\(model.progress.hearts) hearts", systemImage: "heart.fill").foregroundStyle(.red)
                    Text("Progress is saved on this device. Account synchronization is not connected.").foregroundStyle(.secondary)
                }
            case "Leaderboards":
                card("Learn. Practice. Make progress.") {
                    HStack { Image(systemName: "shield.lefthalf.filled").font(.system(size: 56)).foregroundStyle(.cyan); Text("Keep learning at your own pace.").font(.title2.bold()) }
                    Text("Online competitions are not connected in this local education base.").foregroundStyle(.secondary)
                    practiceButton
                }
            case "Shop":
                card("Hearts") {
                    Label("\(model.progress.hearts) hearts", systemImage: "heart.fill").font(.title2.bold()).foregroundStyle(.red)
                    Text("Everything here is free to practice.")
                    Text("Purchases and subscriptions are not connected.").foregroundStyle(.secondary)
                }
                card("Practice is always open") { Text("Return to your course whenever you are ready."); practiceButton }
            default:
                card("Learning sounds") {
                    Label(model.muted ? "Sound off" : "Sound on", systemImage: model.muted ? "speaker.slash.fill" : "speaker.wave.2.fill").font(.title2.bold()).foregroundStyle(.cyan)
                    Text("Hear words and feedback as you learn. Your preference is saved on this device.").foregroundStyle(.secondary)
                    Button(model.muted ? "Turn sound on" : "Turn sound off") { model.toggleMute() }.buttonStyle(SeedButtonStyle(fill: accent)).accessibilityIdentifier("settings-sound")
                }
                Text("LingoSeed · original lessons and sounds, inspired by the reference learning flow.").foregroundStyle(.secondary)
            }
            Button("Back to learning") { model.destination = "Learn" }.buttonStyle(SeedButtonStyle(fill: accent)).accessibilityIdentifier("return-learn")
        }.padding(30).frame(maxWidth: 680, alignment: .leading)
    }
    private var practiceButton: some View {
        Button("START A LESSON") {
            let next = model.course.lessons.indices.first { !model.progress.isCompleted(model.course, index: $0) && model.progress.isUnlocked(model.course, index: $0) } ?? 0
            model.begin(next)
        }.buttonStyle(SeedButtonStyle(fill: accent)).accessibilityIdentifier("destination-practice")
    }
    @ViewBuilder private func lessonPage(_ lesson: Lesson) -> some View {
        if lesson.complete, let page = model.settlement?.current {
            ReferenceSettlement(page: page, allCorrect: lesson.mistakesMade == 0, advance: model.advanceSettlement)
        } else if model.entryPending, let entry = lesson.definition.entry {
            VStack(spacing: 32) {
                Spacer()
                Text(entry.title).font(ReferenceStyle.font(28, bold: true)).multilineTextAlignment(.center).frame(maxWidth: 560).accessibilityIdentifier("lesson-entry").accessibilityValue(entry.id)
                Spacer()
                HStack {
                    Button(entry.declineLabel) { model.discardAttempt() }.buttonStyle(ReferenceButton(color: .gray)).accessibilityIdentifier("lesson-entry-decline")
                    Spacer()
                    Button(entry.startLabel) { model.acceptEntry() }.buttonStyle(ReferenceButton()).accessibilityIdentifier("lesson-entry-start")
                }.padding(40)
            }
        } else {
        VStack(spacing: 0) {
            HStack(spacing: 24) {
                if !lesson.complete { Button { model.confirmingExit = true } label: { Image(systemName: "xmark").font(.title2.bold()).foregroundStyle(.gray) }.buttonStyle(.plain).accessibilityIdentifier("quit") }
                ProgressView(value: lesson.complete ? 1 : lesson.reviewing ? 0.9 : Double(lesson.position) / Double(lesson.definition.questions.count)).tint(accent).scaleEffect(y: 2).accessibilityIdentifier("lesson-progress").accessibilityValue(lesson.complete ? "complete" : lesson.reviewing ? "review" : String(lesson.position))
                Text("♥ \(lesson.hearts)").font(.title2.bold()).foregroundStyle(.red).accessibilityIdentifier("hearts").accessibilityValue(String(lesson.hearts))
                Button { model.toggleMute() } label: { Image(systemName: model.muted ? "speaker.slash.fill" : "speaker.wave.2.fill") }.buttonStyle(.plain).accessibilityLabel(model.muted ? "Sound off" : "Sound on").accessibilityIdentifier("sound-toggle").accessibilityValue(model.muted ? "muted" : "on")
            }.padding(.horizontal, 60).padding(.vertical, 35)
            Spacer(minLength: 0)
            ScrollView {
                VStack(alignment: .leading, spacing: 28) {
                    if lesson.complete { completion }
                    else if let interlude = lesson.interlude {
                        VStack(spacing: 28) {
                            ReferenceStyle.image("duo-observed-frame").resizable().scaledToFit().frame(width: 180, height: 190)
                            Text(interlude.text).font(ReferenceStyle.font(28, bold: true)).multilineTextAlignment(.center).accessibilityIdentifier("lesson-interlude").accessibilityValue(interlude.id)
                        }.frame(maxWidth: .infinity)
                    }
                    else { question(lesson) }
                }.padding(30).frame(maxWidth: 660).frame(maxWidth: .infinity)
            }
            Spacer(minLength: 0)
            if lesson.interlude != nil {
                HStack { Spacer(); Button(copy("CONTINUE", "继续")) { model.advance() }.buttonStyle(ReferenceButton()).frame(width: 150).accessibilityIdentifier("interlude-continue") }
                    .padding(.horizontal, 60).padding(.vertical, 28).frame(minHeight: 115)
                    .overlay(alignment: .top) { Rectangle().fill(ReferenceStyle.border).frame(height: 2) }
            } else if !lesson.complete { answerBar(lesson) }
        }
        .sheet(isPresented: $model.confirmingExit) { exitConfirmation }
        }
    }
    private func answerBar(_ lesson: Lesson) -> some View {
        HStack(spacing: 30) {
            if let correct = lesson.feedback {
                Image(systemName: correct ? "checkmark.circle.fill" : "xmark.circle.fill").font(.system(size: 48)).foregroundStyle(correct ? accent : .red)
                VStack(alignment: .leading, spacing: 8) {
                    Text(correct ? copy("Well done!", "好棒！") : copy("Correct answer: \(lesson.question.correctText)", "正确答案：\(lesson.question.correctText)")).font(.title2.bold())
                        .foregroundStyle(correct ? Color(red: 0.28, green: 0.62, blue: 0) : Color.red).accessibilityIdentifier("feedback").accessibilityValue(correct ? "correct" : "incorrect")
                    Text(lesson.question.explanation)
                }
                Spacer()
                Button(copy("CONTINUE", "继续")) { model.advance() }.buttonStyle(SeedButtonStyle(fill: correct ? accent : .red)).accessibilityIdentifier("continue")
            } else {
                Text(lesson.question.kind == .matching ? "Match all pairs to continue" : "Take your time. You’ve got this.").foregroundStyle(.secondary)
                Spacer()
                if lesson.question.kind != .matching { Button(copy("CHECK", "检查")) { model.submit() }.buttonStyle(SeedButtonStyle(fill: accent)).disabled(!lesson.canSubmit).accessibilityIdentifier("check") }
            }
        }.padding(.horizontal, 60).padding(.vertical, 28).frame(minHeight: 115)
            .background(lesson.feedback == nil ? Color.white : lesson.feedback == true ? Color(red: 0.843, green: 1, blue: 0.722) : Color(red: 1, green: 0.875, blue: 0.875))
            .overlay(alignment: .top) { Rectangle().fill(Color.gray.opacity(0.15)).frame(height: 2) }
    }
    private var exitConfirmation: some View {
        VStack(spacing: 22) {
            SeedMascot()
            Text("Leave this lesson?").font(.largeTitle.bold()).accessibilityIdentifier("exit-title")
            Text("Your finished lessons are safe. This unfinished attempt will be discarded.").foregroundStyle(.secondary)
            Button("Keep learning") { model.confirmingExit = false }.buttonStyle(SeedButtonStyle(fill: accent)).accessibilityIdentifier("cancel-quit")
            Button("End session") { model.discardAttempt() }.buttonStyle(SeedButtonStyle(fill: .red)).accessibilityIdentifier("confirm-quit")
        }.padding(36).frame(width: 440).multilineTextAlignment(.center)
    }
    private var completion: some View {
        VStack(alignment: .leading, spacing: 20) {
            SeedMascot()
            Text("Lesson complete").font(.largeTitle.bold()).accessibilityIdentifier("lesson-complete")
            Text("You made time for your next step.").foregroundStyle(.secondary)
            Button("Back to your path") { model.discardAttempt() }
                .buttonStyle(SeedButtonStyle(fill: accent)).accessibilityIdentifier("return-path")
        }.padding(.vertical, 32)
    }
    @ViewBuilder private func question(_ lesson: Lesson) -> some View {
        if lesson.reviewing {
            Text(copy("ONE MORE LOOK", "错题重练")).font(.caption.bold()).foregroundStyle(accent).accessibilityIdentifier("review-label")
        } else if let indicator = lesson.question.indicator {
            Text(indicator).font(ReferenceStyle.font(14, bold: true)).foregroundStyle(indicator == "挑战题" ? .red : .purple).accessibilityIdentifier("question-indicator")
        } else if lesson.question.newWord { Text(copy("NEW WORD", "新单词")).font(ReferenceStyle.font(14, bold: true)).foregroundStyle(.purple) }
        Text(lesson.question.kind == .wordTiles && lesson.question.hint == nil && lesson.question.sourceType == nil ? "Build this phrase" : lesson.question.prompt).font(ReferenceStyle.font(28, bold: true))
            .accessibilityIdentifier("question-title").accessibilityValue(lesson.question.prompt)
        switch lesson.question.kind {
        case .choice: choices(lesson)
        case .wordTiles: words(lesson)
        case .matching: matching(lesson)
        }
        if lesson.question.kind == .choice && lesson.question.sourceType != "dialogue" {
            Button { model.pronounce() } label: { Label(lesson.selected == nil ? "Read the instruction" : "Listen again", systemImage: "speaker.wave.2.fill") }.buttonStyle(.plain).foregroundStyle(.cyan).accessibilityIdentifier("pronounce")
        }
    }
    @ViewBuilder private func choices(_ lesson: Lesson) -> some View {
        if lesson.question.sourceType == "dialogue" {
            dialogue(lesson)
        } else if let hint = lesson.question.hint {
            HStack(spacing: 16) {
                if let character = lesson.question.characterResource { ReferenceStyle.image(character).resizable().scaledToFit().frame(width: 120, height: 150) }
                Text(hint).font(ReferenceStyle.font(20)).accessibilityIdentifier("question-hint")
                    .padding(16).overlay(RoundedRectangle(cornerRadius: 14).stroke(ReferenceStyle.border, lineWidth: 2))
            }
            VStack(spacing: 12) {
                ForEach(Array(lesson.question.options.enumerated()), id: \.element.id) { index, option in
                    Button { model.choose(option.id) } label: {
                        HStack(spacing: 20) { Text("\(index + 1)").font(ReferenceStyle.font(14)).frame(width: 24, height: 24).overlay(RoundedRectangle(cornerRadius: 6).stroke(ReferenceStyle.border, lineWidth: 2)); Text(option.text).font(ReferenceStyle.font(19)); Spacer() }
                    }.buttonStyle(SeedTileStyle(selected: lesson.selected == option.id))
                        .disabled(lesson.feedback != nil).accessibilityIdentifier("option-" + option.id)
                        .accessibilityLabel(option.text).accessibilityValue(lesson.selected == option.id ? "selected" : "not selected")
                }
            }
        } else { LazyVGrid(columns: [GridItem(.adaptive(minimum: 150, maximum: 220), spacing: 12)], spacing: 12) {
            ForEach(Array(lesson.question.options.enumerated()), id: \.element.id) { index, option in
                Button { model.choose(option.id) } label: {
                    VStack(spacing: 18) {
                        ChoiceIllustration(phrase: option.text, resource: option.imageResource)
                        HStack {
                            Text(option.text).font(.system(size: 17, weight: .medium)).lineLimit(1).minimumScaleFactor(0.8)
                            Spacer(minLength: 3)
                            Text("\(index + 1)").font(.caption.bold()).padding(5)
                                .overlay(RoundedRectangle(cornerRadius: 5).stroke(Color.gray.opacity(0.25), lineWidth: 1))
                        }
                    }
                }.buttonStyle(SeedChoiceStyle(selected: lesson.selected == option.id, feedback: lesson.feedback))
                    .disabled(lesson.feedback != nil).accessibilityIdentifier("option-" + option.id)
                    .accessibilityLabel(option.text).accessibilityValue(lesson.selected == option.id ? "selected" : "not selected")
            }
        } }
    }
    private func dialogue(_ lesson: Lesson) -> some View {
        VStack(spacing: 34) {
            HStack(spacing: 16) {
                if let avatar = lesson.question.dialogueAvatars?.first { ReferenceStyle.image(avatar).resizable().scaledToFit().frame(width: 64, height: 64) }
                Button { model.playQuestion() } label: {
                    HStack { Image(systemName: "speaker.wave.2.fill").foregroundStyle(ReferenceStyle.blue); Text(lesson.question.hint ?? "").foregroundStyle(ink) }
                        .font(ReferenceStyle.font(19)).padding(16).overlay(RoundedRectangle(cornerRadius: 12).stroke(ReferenceStyle.border, lineWidth: 2))
                }.buttonStyle(.plain).accessibilityIdentifier("pronounce")
                Spacer()
            }
            HStack(spacing: 20) {
                Spacer()
                Text(lesson.feedback == true ? lesson.question.correctText : "_______").font(ReferenceStyle.font(19)).padding(16)
                    .overlay(RoundedRectangle(cornerRadius: 12).stroke(ReferenceStyle.border, lineWidth: 2))
                if let avatar = lesson.question.dialogueAvatars?.last { ReferenceStyle.image(avatar).resizable().scaledToFit().frame(width: 64, height: 64) }
            }
            VStack(spacing: 12) {
                ForEach(Array(lesson.question.options.enumerated()), id: \.element.id) { index, option in
                    Button { model.choose(option.id) } label: {
                        HStack { Text("\(index + 1)").font(ReferenceStyle.font(14)).frame(width: 26, height: 26).overlay(RoundedRectangle(cornerRadius: 6).stroke(ReferenceStyle.border, lineWidth: 2)); Spacer(); Text(option.text); Spacer() }
                    }.buttonStyle(SeedTileStyle(selected: lesson.selected == option.id)).disabled(lesson.feedback != nil)
                        .accessibilityLabel(option.text).accessibilityIdentifier("option-" + option.id)
                }
            }.padding(.top, 12)
        }
    }
    private func words(_ lesson: Lesson) -> some View {
        VStack(alignment: .leading, spacing: 24) {
            if lesson.question.sourceType == "listenTap" {
                HStack(spacing: 28) {
                    Button { model.playQuestion() } label: { Image(systemName: "speaker.wave.2.fill").font(.system(size: 54)).frame(width: 110, height: 110) }
                        .buttonStyle(ReferenceButton(color: ReferenceStyle.blue)).accessibilityLabel(copy("Listen", "播放")).accessibilityIdentifier("pronounce")
                    Button { model.playQuestion(slow: true) } label: { Image(systemName: "tortoise.fill").font(.system(size: 28)).frame(width: 64, height: 64) }
                        .buttonStyle(ReferenceButton(color: ReferenceStyle.blue)).accessibilityLabel(copy("Slow", "慢速播放")).accessibilityIdentifier("pronounce-slow")
                }.frame(maxWidth: .infinity)
            } else {
                HStack(spacing: 16) {
                    Group {
                        if let character = lesson.question.characterResource { ReferenceStyle.image(character).resizable().scaledToFit() }
                        else if !chinese { SeedMascot().scaleEffect(0.7) }
                        else { Color.clear }
                    }.frame(width: 120, height: 150)
                    if let example = lesson.question.example {
                        Button { model.playExample() } label: {
                            phraseBubble(example, speaker: true)
                        }.buttonStyle(.plain).accessibilityIdentifier("pronounce-example")
                    } else if lesson.question.audioResource != nil || !chinese {
                        Button { model.pronounce() } label: {
                            phraseBubble(lesson.question.hint ?? lesson.question.prompt, speaker: true)
                        }.buttonStyle(.plain).accessibilityIdentifier("pronounce")
                    } else {
                        phraseBubble(lesson.question.hint ?? lesson.question.prompt, speaker: false)
                    }
                }
            }
            if let prefix = lesson.question.completionPrefix {
                HStack(spacing: 0) {
                    Text(prefix).accessibilityIdentifier("completion-prefix")
                    HStack(spacing: 8) {
                        ForEach(lesson.selectedWords, id: \.self) { id in
                            Button(lesson.question.words.first { $0.id == id }!.text) { model.removeWord(id) }
                                .buttonStyle(SeedTileStyle(selected: true)).disabled(lesson.feedback != nil)
                                .accessibilityIdentifier("selected-word-" + id)
                        }
                    }.frame(minWidth: 140, minHeight: 48)
                        .overlay(alignment: .bottom) { Rectangle().fill(ReferenceStyle.border).frame(height: 2) }
                    Text(lesson.question.completionSuffix ?? "").accessibilityIdentifier("completion-suffix")
                }.font(ReferenceStyle.font(20)).frame(maxWidth: .infinity, minHeight: 108, alignment: .leading)
            } else {
                WordFlowLayout(centered: false) {
                    ForEach(lesson.selectedWords, id: \.self) { id in
                        Button(lesson.question.words.first { $0.id == id }!.text) { model.removeWord(id) }
                            .buttonStyle(SeedTileStyle(selected: true)).fixedSize().disabled(lesson.feedback != nil)
                            .accessibilityIdentifier("selected-word-" + id)
                    }
                }.padding(.vertical, 12).frame(maxWidth: .infinity, minHeight: 108, alignment: .topLeading)
                    .overlay(alignment: .top) { Rectangle().fill(ReferenceStyle.border).frame(height: 2) }
                    .overlay(alignment: .bottom) { Rectangle().fill(ReferenceStyle.border).frame(height: 2) }
            }
            WordFlowLayout(centered: true) {
                ForEach(lesson.question.words) { word in
                    Button(word.text) { model.addWord(word.id) }.buttonStyle(SeedTileStyle()).fixedSize()
                        .disabled(lesson.feedback != nil || lesson.selectedWords.contains(word.id)).accessibilityIdentifier("word-bank-" + word.id)
                }
            }
            Text(chinese ? "" : "Tap a word in your phrase to put it back.").font(.callout).foregroundStyle(.secondary)
        }
    }
    private func phraseBubble(_ text: String, speaker: Bool) -> some View {
        HStack(spacing: 12) {
            if speaker { Image(systemName: "speaker.wave.2.fill").foregroundStyle(ReferenceStyle.blue) }
            Text(text).foregroundStyle(ink).multilineTextAlignment(.leading).accessibilityIdentifier("question-hint")
        }.font(ReferenceStyle.font(20)).padding(18)
            .overlay(RoundedRectangle(cornerRadius: 14).stroke(ReferenceStyle.border, lineWidth: 2))
    }
    private func matching(_ lesson: Lesson) -> some View {
        VStack(alignment: .leading, spacing: 14) {
            Text(lesson.matchingHint ?? "Choose an expression, then its meaning.").foregroundStyle(.secondary)
            HStack(alignment: .top, spacing: 20) {
                VStack(spacing: 12) {
                    ForEach(lesson.question.pairs) { pair in
                        Button(pair.left) { model.match(pair.id, left: true) }
                            .buttonStyle(SeedTileStyle(selected: lesson.selectedLeft == pair.id))
                            .disabled(lesson.feedback != nil || lesson.matchedPairs.contains(pair.id)).accessibilityIdentifier("pair-left-" + pair.id)
                    }
                }
                VStack(spacing: 12) {
                    ForEach(orderedRightPairs(lesson.question)) { pair in
                        Button(pair.right) { model.match(pair.id, left: false) }
                            .buttonStyle(SeedTileStyle(selected: lesson.selectedRight == pair.id))
                            .disabled(lesson.feedback != nil || lesson.matchedPairs.contains(pair.id)).accessibilityIdentifier("pair-right-" + pair.id)
                    }
                }
            }
        }
    }
    private func orderedRightPairs(_ question: Question) -> [WordPair] {
        question.rightOrder?.compactMap { id in question.pairs.first { $0.id == id } } ?? Array(question.pairs.reversed())
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

struct SeedTileStyle: ButtonStyle {
    var selected = false
    @Environment(\.isEnabled) private var enabled
    func makeBody(configuration: Configuration) -> some View {
        configuration.label.font(.system(size: 17, weight: .medium, design: .rounded)).lineLimit(1).minimumScaleFactor(0.8)
            .padding(.horizontal, 12).padding(.vertical, 15).frame(maxWidth: .infinity)
            .foregroundStyle(enabled ? selected ? Color(red: 0, green: 0.6, blue: 0.8) : Color(white: 0.3) : Color.gray.opacity(0.6))
            .background {
                RoundedRectangle(cornerRadius: 12).fill(enabled ? selected ? Color.cyan.opacity(0.1) : .white : Color(white: 0.95))
                    .shadow(color: Color.black.opacity(0.15), radius: 0, y: configuration.isPressed ? 0 : 3)
            }
            .overlay(RoundedRectangle(cornerRadius: 12).stroke(selected && enabled ? Color.cyan.opacity(0.5) : Color.gray.opacity(0.25), lineWidth: 2))
            .offset(y: configuration.isPressed ? 3 : 0)
    }
}

// Intrinsic word widths preserve the observed sentence order and wrap only
// when the available question width cannot hold the next tile.
private struct WordFlowLayout: Layout {
    var centered: Bool
    private func rows(_ subviews: Subviews, width: CGFloat) -> [[Int]] {
        var result: [[Int]] = [[]]; var used: CGFloat = 0
        for i in subviews.indices {
            let size = subviews[i].sizeThatFits(.unspecified)
            let gap: CGFloat = result.last!.isEmpty ? 0 : 8
            if used + gap + size.width > width && !result.last!.isEmpty { result.append([]); used = 0 }
            used += (result.last!.isEmpty ? 0 : 8) + size.width; result[result.count - 1].append(i)
        }
        return result.filter { !$0.isEmpty }
    }
    func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) -> CGSize {
        let width = proposal.width ?? 600
        let groups = rows(subviews, width: width)
        let heights = groups.map { row in row.map { subviews[$0].sizeThatFits(.unspecified).height }.max() ?? 0 }
        return CGSize(width: width, height: heights.reduce(0, +) + CGFloat(max(0, groups.count - 1)) * 8)
    }
    func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) {
        var y = bounds.minY
        for row in rows(subviews, width: bounds.width) {
            let sizes = row.map { subviews[$0].sizeThatFits(.unspecified) }
            let width = sizes.reduce(CGFloat(0)) { $0 + $1.width } + CGFloat(max(0, row.count - 1)) * 8
            var x = bounds.minX + (centered ? max(0, (bounds.width - width) / 2) : 0)
            for (i, size) in zip(row, sizes) {
                subviews[i].place(at: CGPoint(x: x, y: y), proposal: ProposedViewSize(size))
                x += size.width + 8
            }
            y += (sizes.map(\.height).max() ?? 0) + 8
        }
    }
}
