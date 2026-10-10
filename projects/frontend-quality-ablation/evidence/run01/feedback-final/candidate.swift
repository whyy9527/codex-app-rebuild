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
                    if question.id == "p11", question.kind == .matching, !lesson.complete, lesson.deferredSpeech == nil {
                        GeometryReader { proxy in
                            let fraction = lesson.feedback == true ? 733.0 / 958.0 : 664.0 / 958.0
                            ZStack(alignment: .leading) {
                                Capsule().fill(ReferenceStyle.border)
                                Capsule().fill(ReferenceStyle.green).frame(width: proxy.size.width * fraction)
                                    .overlay(alignment: .topLeading) {
                                        Capsule().fill(Color.white.opacity(0.25)).frame(width: max(0, proxy.size.width * fraction - 8), height: 4).padding(.leading, 4).padding(.top, 2)
                                    }
                            }
                            .overlay(alignment: .topLeading) {
                                if lesson.feedback == true {
                                    Text("连对 2 题").font(ReferenceStyle.font(16, bold: true)).foregroundStyle(ReferenceStyle.green)
                                        .fixedSize().position(x: proxy.size.width * fraction / 2, y: -10)
                                }
                            }
                        }.frame(height: 16)
                            .accessibilityElement(children: .ignore)
                            .accessibilityLabel("进度")
                            .accessibilityValue(lesson.feedback == true ? "连对 2 题，76.5%" : "69.3%")
                            .accessibilityIdentifier("lesson-progress")
                    } else {
                        ProgressView(value: lesson.complete ? 1 : lesson.reviewing ? 0.9 : Double(lesson.position) / Double(lesson.definition.questions.count)).tint(ReferenceStyle.green).accessibilityIdentifier("lesson-progress")
                    }
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
                            HStack(alignment: .top, spacing: 30) {
                                VStack(spacing: 10) {
                                    ForEach(Array(question.pairs.enumerated()), id: \.element.id) { index, pair in
                                        matchingTile(pair, left: true, number: index + 1)
                                    }
                                }
                                VStack(spacing: 10) {
                                    ForEach(Array(matchingRightPairs.enumerated()), id: \.element.id) { index, pair in
                                        matchingTile(pair, left: false, number: question.pairs.count + index + 1)
                                    }
                                }
                            }.frame(width: 600).padding(.top, 88)
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
                if question.kind == .matching, !lesson.complete, lesson.deferredSpeech == nil {
                    matchingFooter.frame(height: 140)
                } else {
                    footer.frame(height: 140)
                }
            }.frame(maxWidth: .infinity, maxHeight: .infinity)
                .foregroundStyle(ReferenceStyle.ink).background(ReferenceStyle.background)
        }
    }

    private var matchingRightPairs: [WordPair] {
        guard let order = question.rightOrder else { return question.pairs }
        return order.compactMap { id in question.pairs.first { $0.id == id } }
            + question.pairs.filter { !order.contains($0.id) }
    }

    private func matchingTile(_ pair: WordPair, left: Bool, number: Int) -> some View {
        let disabled = lesson.feedback != nil || lesson.matchedPairs.contains(pair.id)
        let selected = !disabled && (left ? lesson.selectedLeft == pair.id : lesson.selectedRight == pair.id)
        let edge = selected ? ReferenceStyle.blue : ReferenceStyle.border
        let foreground = disabled ? ReferenceStyle.border : left ? ReferenceStyle.blue : ReferenceStyle.ink
        return Button { model.match(pair.id, left: left) } label: {
            ZStack(alignment: .top) {
                RoundedRectangle(cornerRadius: 12)
                    .fill(selected ? Color(red: 221/255, green: 244/255, blue: 1) : .white)
                    .overlay(RoundedRectangle(cornerRadius: 12).strokeBorder(edge, lineWidth: 2))
                    .frame(height: 56)
                    .shadow(color: edge, radius: 0, y: 2)
                ZStack {
                    if left {
                        HStack(spacing: 12) {
                            ReferenceStyle.image("en-match-speaker-source-frame")
                                .renderingMode(.template).resizable().scaledToFit().frame(width: 24, height: 24)
                            ReferenceStyle.image("en-match-waveform-source-frame")
                                .renderingMode(.template).resizable().scaledToFit().frame(width: 82, height: 24)
                        }.foregroundStyle(foreground).offset(x: 14)
                    } else {
                        Text(pair.right).font(ReferenceStyle.font(19).weight(.medium)).foregroundStyle(foreground).offset(x: 14)
                    }
                }.frame(width: 255, height: 56)
                Text(String(number)).font(ReferenceStyle.font(14, bold: true))
                    .foregroundStyle(disabled ? ReferenceStyle.border : Color(red: 175/255, green: 175/255, blue: 175/255))
                    .frame(width: 30, height: 30)
                    .overlay(RoundedRectangle(cornerRadius: 7).strokeBorder(ReferenceStyle.border, lineWidth: 2))
                    .frame(width: 255, height: 56, alignment: .leading).offset(x: 18)
            }.frame(width: 255, height: 58).contentShape(RoundedRectangle(cornerRadius: 12))
        }.buttonStyle(.plain).disabled(disabled)
            .accessibilityLabel(left ? pair.left : "\(number) \(pair.right)")
            .accessibilityIdentifier((left ? "pair-left-" : "pair-right-") + pair.id)
    }

    private var matchingFooter: some View {
        GeometryReader { proxy in
            let success = lesson.feedback == true
            let feedbackColor = success ? Color(red: 88/255, green: 167/255, blue: 0) : Color.red
            ZStack(alignment: .topLeading) {
                if let feedback = lesson.feedback {
                    Circle().fill(.white).frame(width: 80, height: 80).position(x: 180, y: 70)
                    Path { path in
                        if feedback {
                            path.move(to: CGPoint(x: 165, y: 72))
                            path.addLine(to: CGPoint(x: 176, y: 82))
                            path.addLine(to: CGPoint(x: 195, y: 63))
                        } else {
                            path.move(to: CGPoint(x: 168, y: 58))
                            path.addLine(to: CGPoint(x: 192, y: 82))
                            path.move(to: CGPoint(x: 192, y: 58))
                            path.addLine(to: CGPoint(x: 168, y: 82))
                        }
                    }.stroke(feedbackColor, style: StrokeStyle(lineWidth: 10, lineCap: .round, lineJoin: .round))
                        .accessibilityHidden(true).allowsHitTesting(false)
                    VStack(alignment: .leading, spacing: 20) {
                        Text(feedback ? (question.correctFeedback ?? "你练得一副好听力，厉害呀！") : "还不太准确，再多听几次吧！")
                            .font(ReferenceStyle.font(22, bold: true)).foregroundStyle(feedbackColor)
                            .accessibilityIdentifier("feedback")
                        ReferenceFeedbackActions(model: model, color: feedbackColor)
                    }.padding(.leading, 237).padding(.top, 30)
                    Button("继续") { model.advance() }
                        .buttonStyle(ReferenceMatchingFooterButtonStyle(primary: true))
                        .accessibilityIdentifier("continue").position(x: proxy.size.width - 215, y: 70)
                } else {
                    Button("跳过") { model.skip() }
                        .buttonStyle(ReferenceMatchingFooterButtonStyle(primary: false))
                        .accessibilityIdentifier("skip").position(x: 215, y: 72)
                    Button("检查") { model.submit() }
                        .buttonStyle(ReferenceMatchingFooterButtonStyle(primary: true))
                        .disabled(!lesson.canSubmit).accessibilityIdentifier("check")
                        .position(x: proxy.size.width - 215, y: 76)
                }
            }.frame(width: proxy.size.width, height: proxy.size.height, alignment: .topLeading)
                .background(lesson.feedback == nil ? ReferenceStyle.background : success ? Color(red: 215/255, green: 1, blue: 184/255) : Color(red: 1, green: 223/255, blue: 224/255))
                .overlay(alignment: .top) {
                    if lesson.feedback == nil { Rectangle().fill(ReferenceStyle.border).frame(height: 2) }
                }
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

private struct ReferenceMatchingFooterButtonStyle: ButtonStyle {
    let primary: Bool
    @Environment(\.isEnabled) private var enabled
    func makeBody(configuration: Configuration) -> some View {
        let muted = Color(red: 175/255, green: 175/255, blue: 175/255)
        let face = primary ? (enabled ? ReferenceStyle.green : ReferenceStyle.border) : Color.white
        let edge = primary && enabled ? Color(red: 88/255, green: 167/255, blue: 0) : ReferenceStyle.border
        configuration.label
            .font(ReferenceStyle.font(17, bold: true))
            .foregroundStyle(primary && enabled ? Color.white : muted)
            .frame(width: 150, height: 46)
            .background {
                RoundedRectangle(cornerRadius: 16).fill(face)
                    .overlay(RoundedRectangle(cornerRadius: 16).strokeBorder(primary ? Color.clear : edge, lineWidth: 2))
                    .shadow(color: edge, radius: 0, y: 4)
            }
            .offset(y: configuration.isPressed && enabled ? 2 : 0)
            .frame(width: 150, height: 50, alignment: .top)
            .contentShape(RoundedRectangle(cornerRadius: 16))
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
