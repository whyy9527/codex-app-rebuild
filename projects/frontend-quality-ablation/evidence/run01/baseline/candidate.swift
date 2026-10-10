import SwiftUI
import LearningCore

struct ReferencePronunciationPractice: View {
    @Bindable var model: LearningModel
    let lesson: Lesson
    private var question: Question { lesson.question }
    var body: some View {
        GeometryReader { geometry in
            VStack(spacing: 0) {
                HStack(spacing: 24) {
                    Button { model.discardAttempt() } label: { ReferenceStyle.image("practice-close-source").resizable().frame(width: 18, height: 18) }
                        .buttonStyle(.plain).accessibilityIdentifier("exit")
                    ProgressView(value: lesson.complete ? 1 : lesson.reviewing ? 0.9 : Double(lesson.position) / Double(lesson.definition.questions.count)).tint(ReferenceStyle.green).accessibilityIdentifier("lesson-progress")
                }.frame(maxWidth: 1000).padding(.top, 50)
                if let speech = lesson.deferredSpeech {
                    VStack(alignment: .leading, spacing: 40) {
                        Text(speech.title).font(ReferenceStyle.font(32, bold: true))
                        Text(speech.phrase).font(ReferenceStyle.font(22))
                        Button("点击并开始录音") {}.buttonStyle(ReferenceButton(color: ReferenceStyle.blue)).disabled(true)
                    }.frame(width: 600).padding(.top, 50)
                } else if lesson.complete {
                    VStack(spacing: 24) {
                        Text(model.settlement?.current?.title ?? "").font(ReferenceStyle.font(32, bold: true)).accessibilityIdentifier("practice-settlement-title")
                        if let body = model.settlement?.current?.body { Text(body).font(ReferenceStyle.font(19)) }
                    }.padding(.top, 80)
                } else {
                    VStack(alignment: .leading, spacing: 0) {
                        Text(question.prompt).font(ReferenceStyle.font(32, bold: true)).frame(height: 40).accessibilityIdentifier("question-prompt").accessibilityValue(question.id)
                        if question.kind == .matching {
                            HStack(spacing: 32) {
                                VStack { ForEach(question.pairs) { pair in Button(pair.left) { model.match(pair.id, left: true) }.buttonStyle(ReferenceSkipButton()).disabled(lesson.matchedPairs.contains(pair.id)).accessibilityIdentifier("pair-left-" + pair.id) } }
                                VStack { ForEach(question.pairs) { pair in Button(pair.right) { model.match(pair.id, left: false) }.buttonStyle(ReferenceSkipButton()).disabled(lesson.matchedPairs.contains(pair.id)).accessibilityIdentifier("pair-right-" + pair.id) } }
                            }.padding(.top, 40)
                        } else if question.sourceType == "sameDifferent" {
                            VStack(alignment: .leading, spacing: 0) {
                                splitSpeaker.frame(maxWidth: .infinity)
                                Text("你听到的词是？").font(ReferenceStyle.font(19, bold: true)).frame(height: 27).padding(.top, 40.25).padding(.bottom, 8)
                                ForEach(Array(question.options.enumerated()), id: \.element.id) { index, option in radio(option, index: index).padding(.bottom, 8) }
                            }.padding(.top, 27.75)
                        } else {
                            VStack(spacing: 24) {
                                speaker(0, size: 140)
                                HStack(spacing: 8) { ForEach(Array(question.options.enumerated()), id: \.element.id) { index, option in radio(option, index: index) } }
                            }.padding(.top, 105)
                        }
                    }.frame(width: 600).padding(.top, 51)
                }
                Spacer(minLength: 0)
                footer.frame(height: 140)
            }.frame(maxWidth: .infinity, maxHeight: .infinity)
                .foregroundStyle(ReferenceStyle.ink).background(ReferenceStyle.background)
        }
    }

    private var splitSpeaker: some View {
        VStack(spacing: 0) {
            ForEach(0..<2) { part in
                let labels = question.practiceAudioLabels ?? []
                let label = lesson.feedback != nil && labels.indices.contains(part) ? labels[part] : ""
                ReferencePracticeAudioButton(label: label, identifier: "practice-play-" + String(part), enabled: lesson.feedback == nil,
                    action: { model.playQuestion(practicePart: part) })
                    .frame(width: 165, height: part == 0 ? 85.5 : 89.5)
            }
        }.frame(width: 165, height: 175)
            .background {
                RoundedRectangle(cornerRadius: 41.25).fill(.white)
                    .shadow(color: ReferenceStyle.border, radius: 0, y: 2)
                    .overlay(RoundedRectangle(cornerRadius: 41.25).strokeBorder(ReferenceStyle.border, lineWidth: 2))
            }
            .overlay(alignment: .top) { Rectangle().fill(ReferenceStyle.border).frame(height: 2).offset(y: 85.5).allowsHitTesting(false) }
    }

    private func speaker(_ part: Int, size: Double) -> some View {
        Button { model.playQuestion(practicePart: part) } label: {
            ReferenceStyle.image("practice-speaker-source").resizable().scaledToFit().frame(width: size * 0.67, height: size * 0.52)
                .frame(width: size, height: size).background(alignment: .top) {
                    RoundedRectangle(cornerRadius: 32).fill(ReferenceStyle.blue).frame(height: size - 4)
                        .shadow(color: Color(red: 24/255, green: 153/255, blue: 214/255), radius: 0, y: 4)
                }
        }.buttonStyle(.plain).frame(maxWidth: .infinity).accessibilityIdentifier("practice-play-" + String(part))
    }
    private func radio(_ option: Choice, index: Int) -> some View {
        ReferenceAudioRadio(label: "\(index + 1) \(option.text)", identifier: "option-" + option.id, waveform: nil,
            correct: lesson.feedback == true, selected: lesson.selected == option.id, enabled: lesson.feedback == nil,
            action: { model.choose(option.id) }, textChoice: true).frame(width: question.sourceType == "sameDifferent" ? 600 : 296, height: 60)
    }
    private var footer: some View {
        HStack {
            if let speech = lesson.deferredSpeech {
                if lesson.speechDeclined {
                    Text(speech.closedTitle).font(ReferenceStyle.font(22, bold: true)); Spacer()
                    Button("继续") { model.advance() }.buttonStyle(ReferenceCheckButton()).accessibilityIdentifier("speech-continue")
                } else {
                    Button("现在不做口语题") { model.declineSpeech() }.buttonStyle(ReferenceSkipButton()).accessibilityIdentifier("speech-decline")
                    Spacer(); Button("检查") {}.buttonStyle(ReferenceCheckButton()).disabled(true)
                }
            } else if lesson.complete {
                Spacer(); Button(model.settlement?.current?.continueLabel ?? "继续") { model.advanceSettlement() }.buttonStyle(ReferenceCheckButton()).accessibilityIdentifier("settlement-continue")
            } else if let feedback = lesson.feedback {
                VStack(alignment: .leading, spacing: 8) {
                    Text(feedback ? (question.correctFeedback ?? "你练得一副好听力，厉害呀！") : "还不太准确，再多听几次吧！").font(ReferenceStyle.font(22, bold: true)).accessibilityIdentifier("feedback")
                    if question.sourceType == "sameDifferent" { Text(question.explanation).font(ReferenceStyle.font(18)) }
                    ReferenceFeedbackActions(model: model, color: feedback ? ReferenceStyle.green : .red)
                }
                Spacer(); Button("继续") { model.advance() }.buttonStyle(ReferenceCheckButton()).accessibilityIdentifier("continue")
            } else {
                Button("跳过") { model.skip() }.buttonStyle(ReferenceSkipButton()).accessibilityIdentifier("skip")
                Spacer(); Button("检查") { model.submit() }.buttonStyle(ReferenceCheckButton()).disabled(!lesson.canSubmit).accessibilityIdentifier("check")
            }
        }.padding(.horizontal, 140).frame(maxWidth: .infinity, maxHeight: .infinity)
            .background(lesson.feedback == nil && !lesson.speechDeclined ? ReferenceStyle.background : lesson.feedback == false ? Color(red: 1, green: 223/255, blue: 224/255) : Color(red: 215/255, green: 1, blue: 184/255))
            .overlay(alignment: .top) { Rectangle().fill(ReferenceStyle.border).frame(height: 2) }
    }
}

// The source's two halves have distinct hit rectangles, disabled states and labels.
// NSButton supplies those semantics without SwiftUI's decorative focus inset.
private struct ReferencePracticeAudioButton: NSViewRepresentable {
    let label: String
    let identifier: String
    let enabled: Bool
    let action: () -> Void
    final class Coordinator: NSObject {
        var action: () -> Void
        init(_ action: @escaping () -> Void) { self.action = action }
        @objc func play(_ sender: NSButton) { action() }
    }
    final class Button: NSButton {
        let face = ReferenceAudioRadio.PassiveHost(rootView: AnyView(EmptyView()))
        override func accessibilityRole() -> NSAccessibility.Role? { .button }
        override var intrinsicContentSize: NSSize { NSSize(width: NSView.noIntrinsicMetric, height: NSView.noIntrinsicMetric) }
        override func draw(_ dirtyRect: NSRect) {}
        override func accessibilityFrame() -> NSRect {
            guard let window else { return super.accessibilityFrame() }
            return window.convertToScreen(convert(bounds, to: nil))
        }
    }
    final class Container: NSView {
        let button = Button(frame: .zero)
    }
    func makeCoordinator() -> Coordinator { Coordinator(action) }
    func makeNSView(context: Context) -> Container {
        let container = Container(frame: .zero)
        let button = container.button
        container.addSubview(button)
        button.translatesAutoresizingMaskIntoConstraints = false
        NSLayoutConstraint.activate([
            button.leadingAnchor.constraint(equalTo: container.leadingAnchor), button.trailingAnchor.constraint(equalTo: container.trailingAnchor),
            button.topAnchor.constraint(equalTo: container.topAnchor), button.bottomAnchor.constraint(equalTo: container.bottomAnchor)
        ])
        button.setAccessibilityElement(true)
        container.setAccessibilityElement(false)
        container.setAccessibilityChildren([button])
        button.isBordered = false
        button.setButtonType(.momentaryPushIn)
        button.target = context.coordinator
        button.action = #selector(Coordinator.play(_:))
        button.addSubview(button.face)
        button.face.translatesAutoresizingMaskIntoConstraints = false
        NSLayoutConstraint.activate([
            button.face.leadingAnchor.constraint(equalTo: button.leadingAnchor), button.face.trailingAnchor.constraint(equalTo: button.trailingAnchor),
            button.face.topAnchor.constraint(equalTo: button.topAnchor), button.face.bottomAnchor.constraint(equalTo: button.bottomAnchor)
        ])
        button.setAccessibilityChildren([])
        return container
    }
    func updateNSView(_ container: Container, context: Context) {
        let button = container.button
        context.coordinator.action = action
        button.isEnabled = enabled
        button.title = label
        button.setAccessibilityLabel(label)
        button.setAccessibilityIdentifier(identifier)
        button.face.rootView = AnyView(HStack(spacing: 8) {
            ReferenceStyle.image("practice-speaker-source").renderingMode(.template).resizable().frame(width: 24, height: 19).foregroundStyle(ReferenceStyle.blue)
            Text(label.isEmpty ? " " : label).font(ReferenceStyle.font(19, bold: true)).foregroundStyle(ReferenceStyle.ink)
                .frame(width: 42, height: 27).overlay(alignment: .bottom) { Rectangle().fill(ReferenceStyle.border).frame(height: 2) }
        }.offset(y: -2).frame(maxWidth: .infinity, maxHeight: .infinity).accessibilityHidden(true))
    }
}
