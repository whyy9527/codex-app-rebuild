import AppKit
import SwiftUI

/// Source audio choices are radios, including their enabled/selected AX states.
struct ReferenceAudioRadio: NSViewRepresentable {
    let label: String
    let identifier: String
    let waveform: String?
    let selected: Bool
    let enabled: Bool
    let action: () -> Void

    final class Coordinator: NSObject {
        var action: () -> Void
        init(action: @escaping () -> Void) { self.action = action }
        @objc func choose(_ sender: NSButton) { action() }
    }
    final class Container: NSView {
        let button = Radio(frame: .zero)
    }
    final class Radio: NSButton {
        let face = PassiveHost(rootView: AnyView(EmptyView()))
        override func accessibilityRole() -> NSAccessibility.Role? { .radioButton }
        override func accessibilityValue() -> Any? { state == .on ? 1 : 0 }
        override var intrinsicContentSize: NSSize { NSSize(width: 600, height: 62) }
        // Native radio cell owns input/accessibility; the observed web face is custom.
        override func draw(_ dirtyRect: NSRect) {}
    }
    final class PassiveHost: NSHostingView<AnyView> {
        override func hitTest(_ point: NSPoint) -> NSView? { nil }
    }
    func makeCoordinator() -> Coordinator { Coordinator(action: action) }
    func makeNSView(context: Context) -> Container {
        let container = Container(frame: .zero)
        let button = container.button
        container.addSubview(button)
        button.translatesAutoresizingMaskIntoConstraints = false
        NSLayoutConstraint.activate([button.leadingAnchor.constraint(equalTo: container.leadingAnchor), button.trailingAnchor.constraint(equalTo: container.trailingAnchor), button.topAnchor.constraint(equalTo: container.topAnchor), button.bottomAnchor.constraint(equalTo: container.bottomAnchor)])
        button.setAccessibilityElement(true)
        container.setAccessibilityElement(false)
        container.setAccessibilityChildren([button])
        button.setButtonType(.radio)
        button.isBordered = false
        button.target = context.coordinator
        button.action = #selector(Coordinator.choose(_:))
        button.addSubview(button.face)
        button.face.translatesAutoresizingMaskIntoConstraints = false
        NSLayoutConstraint.activate([
            button.face.leadingAnchor.constraint(equalTo: button.leadingAnchor),
            button.face.trailingAnchor.constraint(equalTo: button.trailingAnchor),
            button.face.topAnchor.constraint(equalTo: button.topAnchor),
            button.face.bottomAnchor.constraint(equalTo: button.bottomAnchor)
        ])
        button.setAccessibilityChildren([])
        return container
    }
    func updateNSView(_ container: Container, context: Context) {
        let button = container.button
        context.coordinator.action = action
        button.title = label
        button.state = selected ? .on : .off
        button.isEnabled = enabled
        button.setAccessibilityLabel(label)
        button.setAccessibilityIdentifier(identifier)
        button.face.rootView = AnyView(face.accessibilityHidden(true))
    }
    private var face: some View {
        ZStack(alignment: .leading) {
            Text(label).font(ReferenceStyle.font(14, bold: true))
                .foregroundStyle(ReferenceStyle.disclosureInk)
                .frame(width: 28, height: 28)
                .overlay(RoundedRectangle(cornerRadius: 6).strokeBorder(ReferenceStyle.border, lineWidth: 2))
                .padding(.leading, 18)
            HStack(spacing: 16) {
                ReferenceStyle.image("en-match-speaker-source-frame").renderingMode(.template).resizable()
                    .frame(width: 24, height: 19).foregroundStyle(ReferenceStyle.blue)
                if let waveform { ReferenceStyle.image(waveform).resizable().frame(width: 152, height: 30) }
            }.frame(maxWidth: .infinity)
        }.frame(height: 58)
            .background(RoundedRectangle(cornerRadius: 12).fill(selected ? Color.cyan.opacity(0.1) : .white)
                .shadow(color: ReferenceStyle.border, radius: 0, y: 4))
            .overlay(RoundedRectangle(cornerRadius: 12).strokeBorder(selected ? ReferenceStyle.blue : ReferenceStyle.border, lineWidth: 2))
            .frame(height: 62, alignment: .top)
    }
}
