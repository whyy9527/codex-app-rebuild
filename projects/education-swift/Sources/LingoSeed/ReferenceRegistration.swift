import AppKit
import SwiftUI

struct ReferenceRegistration: View {
    let close: () -> Void
    @State private var step = 0
    @State private var age = ""
    @State private var name = ""
    @State private var email = ""
    @State private var password = ""
    @State private var emailError = false
    @State private var passwordError = false
    private var invalid: Bool { emailError || passwordError }
    var body: some View {
        GeometryReader { geometry in
            ZStack(alignment: .topLeading) {
                Color.white
                Button { if step == 0 { close() } else { step -= 1; emailError = false; passwordError = false } } label: {
                    ReferenceStyle.image(step == 0 ? "en-path-profile-close" : "en-registration-back").resizable().frame(width: step == 0 ? 16 : 17, height: step == 0 ? 16 : 17)
                }.buttonStyle(.plain).frame(width: 20, height: 21.5).offset(x: 28, y: 30).accessibilityLabel(step == 0 ? "关闭" : "返回").accessibilityIdentifier("registration-back")
                if step != 1 {
                    Text("登录").font(ReferenceStyle.font(15, bold: true)).foregroundStyle(ReferenceStyle.blue)
                        .frame(width: 67.6015625, height: 46).overlay(RoundedRectangle(cornerRadius: 16).strokeBorder(ReferenceStyle.border, lineWidth: 2))
                        .offset(x: geometry.size.width - 97.6015625, y: 30)
                }
                Group {
                    if step == 0 { agePage }
                    else if step == 1 { methodsPage }
                    else { emailPage }
                }.frame(width: 375).offset(x: (geometry.size.width - 375) / 2)
            }
        }.background(.white)
    }
    private var agePage: some View {
        ZStack(alignment: .topLeading) {
            title("你的年龄是……").offset(y: 189.5)
            field("年龄", id: "path-age-input", text: $age, reservedTrailing: !age.isEmpty).offset(y: 252.5)
            (Text("告诉我们你的真实年龄，让我们为你打造一个更合适的多邻国学习体验。更多详情，请访问") + Text("隐私政策").foregroundColor(ReferenceStyle.blue) + Text("。"))
                .font(ReferenceStyle.font(16, weight: 400)).foregroundStyle(ReferenceStyle.disclosureInk)
                .frame(width: 375, height: 48, alignment: .topLeading).offset(y: 304.5)
            control("下一步", id: "path-age-next", enabled: !age.isEmpty, color: age.isEmpty ? ReferenceStyle.border : ReferenceStyle.blue) { step = 1 }
                .offset(y: age.isEmpty ? 376.5 : 372.5)
            legal.offset(y: 461.5)
        }
    }
    private var methodsPage: some View {
        ZStack(alignment: .topLeading) {
            title("选个注册方式才能继续哦！").offset(y: 70)
            ReferenceStyle.image("en-registration-duo").resizable().frame(width: 280, height: 260).offset(x: 47.5, y: 184.5)
            method("使用 GOOGLE 继续", icon: "google", id: "registration-google", enabled: false) {}.offset(y: 504)
            method("使用 Facebook 继续", icon: "facebook", id: "registration-facebook", enabled: false) {}.offset(y: 564)
            method("使用电子邮件继续", icon: "email", id: "registration-email", enabled: true) { step = 2 }.offset(y: 624)
        }
    }
    private var emailPage: some View {
        let shift: CGFloat = invalid ? 24 : 0
        return ZStack(alignment: .topLeading) {
            title("创建档案").offset(y: 153.5 - shift)
            field("姓名（选填）", id: "registration-name", text: $name).offset(y: 216.5 - shift)
            field("邮箱", id: "registration-address", text: $email).offset(y: 276.5 - shift)
            field("密码", id: "registration-password", text: $password, secure: true).offset(y: 336.5)
            if emailError { Text("邮箱地址无效").font(ReferenceStyle.font(16, weight: 400)).foregroundStyle(.red).offset(x: 28, y: 304.5) }
            if passwordError { Text("密码太短了").font(ReferenceStyle.font(16, weight: 400)).foregroundStyle(.red).offset(x: 28, y: 388.5) }
            control("创建帐户", id: "registration-submit", enabled: true, color: ReferenceStyle.blue) {
                emailError = email.isEmpty; passwordError = password.isEmpty
            }.offset(y: 408.5 + shift)
            legal.offset(y: 497.5 + shift)
        }
    }
    private func title(_ value: String) -> some View {
        Text(value).font(ReferenceStyle.font(26, bold: true)).foregroundStyle(ReferenceStyle.ink).frame(width: 375, height: 40)
    }
    private func field(_ placeholder: String, id: String, text: Binding<String>, secure: Bool = false, reservedTrailing: Bool = false) -> some View {
        ZStack(alignment: .topLeading) {
            RoundedRectangle(cornerRadius: 12).fill(Color(white: 247/255)).overlay(RoundedRectangle(cornerRadius: 12).strokeBorder(ReferenceStyle.border, lineWidth: 2))
            RegistrationTextField(text: text, placeholder: placeholder, identifier: id, secure: secure)
                .frame(width: secure || reservedTrailing ? 347 : 371, height: 44).offset(x: 2, y: 2)
        }.frame(width: 375, height: 48)
    }
    private func control(_ label: String, id: String, enabled: Bool, color: Color, action: @escaping () -> Void) -> some View {
        ReferencePracticeControl(label: label, identifier: id, enabled: enabled, action: action, face: AnyView(
            Text(label).font(ReferenceStyle.font(15, bold: true)).foregroundStyle(enabled ? .white : Color(white: 175/255))
                .frame(width: 375, height: 46).background(color, in: RoundedRectangle(cornerRadius: 16))
                .shadow(color: enabled ? Color(red: 24/255, green: 153/255, blue: 214/255) : .clear, radius: 0, y: 4).frame(height: 50, alignment: .top)))
            .frame(width: 375, height: 50)
    }
    private func method(_ label: String, icon: String, id: String, enabled: Bool, action: @escaping () -> Void) -> some View {
        ReferencePracticeControl(label: label, identifier: id, enabled: enabled, action: action, face: AnyView(
            HStack(spacing: 8) { ReferenceStyle.image("en-registration-" + icon).resizable().frame(width: 20, height: 20); Text(label.uppercased()).font(ReferenceStyle.font(17, bold: true)) }
                .foregroundStyle(ReferenceStyle.blue).frame(width: 375, height: 44)
                .background(.white, in: RoundedRectangle(cornerRadius: 16)).overlay(RoundedRectangle(cornerRadius: 16).strokeBorder(ReferenceStyle.border, lineWidth: 2))
                .shadow(color: ReferenceStyle.border, radius: 0, y: 4).frame(height: 48, alignment: .top)))
            .frame(width: 375, height: 48)
    }
    private var legal: some View {
        VStack(spacing: 20) {
            Text("登录即视为你已接受我们的服务条款与隐私政策。")
            Text("该网站受 reCAPTCHA Enterprise 保护。Google 隐私政策及服务条款也同时适用。")
        }.font(ReferenceStyle.font(14, weight: 400)).foregroundStyle(Color(white: 175/255)).multilineTextAlignment(.center).frame(width: 375)
    }
}

private struct RegistrationTextField: NSViewRepresentable {
    @Binding var text: String
    let placeholder: String
    let identifier: String
    let secure: Bool
    final class Coordinator: NSObject, NSTextFieldDelegate {
        var parent: RegistrationTextField
        init(_ parent: RegistrationTextField) { self.parent = parent }
        func controlTextDidChange(_ notification: Notification) {
            guard let field = notification.object as? NSTextField else { return }
            parent.text = field.stringValue
        }
    }
    func makeCoordinator() -> Coordinator { Coordinator(self) }
    func makeNSView(context: Context) -> NSTextField {
        let field: NSTextField = secure ? NSSecureTextField() : NSTextField()
        field.isBordered = false; field.drawsBackground = false; field.focusRingType = .none
        field.setContentHuggingPriority(.defaultLow, for: .vertical)
        field.setContentCompressionResistancePriority(.defaultLow, for: .vertical)
        field.font = ReferenceStyle.nativeFont(19, weight: 400)
        field.placeholderString = placeholder; field.delegate = context.coordinator
        field.setAccessibilityLabel(placeholder); field.setAccessibilityIdentifier(identifier)
        return field
    }
    func updateNSView(_ field: NSTextField, context: Context) {
        context.coordinator.parent = self
        // The field editor owns in-flight keystrokes; a SwiftUI layout update must not overwrite them.
        if field.currentEditor() == nil && field.stringValue != text { field.stringValue = text }
    }
}
