import AppKit
import CoreText
import SwiftUI

enum ReferenceStyle {
    static let choiceImages: [String: String] = {
        guard let url = Bundle.module.url(forResource: "choice-images", withExtension: "json", subdirectory: "Reference"),
              let data = try? Data(contentsOf: url), let result = try? JSONDecoder().decode([String: String].self, from: data) else { return [:] }
        return result
    }()
    static let green = Color(red: 88/255, green: 204/255, blue: 0)
    static let blue = Color(red: 28/255, green: 176/255, blue: 246/255)
    private static func adaptive(_ light: UInt32, _ dark: UInt32) -> Color {
        Color(nsColor: NSColor(name: nil) { appearance in
            let value = appearance.bestMatch(from: [.aqua, .darkAqua]) == .darkAqua ? dark : light
            return NSColor(srgbRed: Double((value >> 16) & 255) / 255, green: Double((value >> 8) & 255) / 255, blue: Double(value & 255) / 255, alpha: 1)
        })
    }
    static let border = adaptive(0xe5e5e5, 0x37464f)
    static let ink = adaptive(0x4b4b4b, 0xf1f7fb)
    static let secondaryInk = adaptive(0x777777, 0xdce6ec)
    static let disclosureInk = adaptive(0xafafaf, 0x52656d)
    static let background = adaptive(0xffffff, 0x131f24)
    static func registerFonts() {
        for name in ["font-0", "font-1"] {
            if let url = Bundle.module.url(forResource: name, withExtension: "ttf", subdirectory: "Reference") {
                CTFontManagerRegisterFontsForURL(url as CFURL, .process, nil)
            }
        }
    }
    static func font(_ size: CGFloat, bold: Bool = false) -> Font {
        let descriptor = CTFontDescriptorCreateWithAttributes([
            kCTFontNameAttribute: "DuolingoSans-Thin",
            kCTFontVariationAttribute: [NSNumber(value: 0x77676874): NSNumber(value: bold ? 700 : 500)]
        ] as CFDictionary)
        return Font(CTFontCreateWithFontDescriptor(descriptor, size, nil) as NSFont)
    }
    static func image(_ name: String) -> Image {
        guard let url = Bundle.module.url(forResource: name, withExtension: "png", subdirectory: "Reference"),
              let image = NSImage(contentsOf: url) else { return Image(systemName: "questionmark.square") }
        return Image(nsImage: image)
    }
    @MainActor static func recordWindowGeometry() {
        guard let index = CommandLine.arguments.firstIndex(of: "--render-metadata"),
              index + 1 < CommandLine.arguments.count,
              let window = NSApp.windows.first(where: { $0.contentView != nil }) else { return }
        let frame = window.frame
        let content = window.contentLayoutRect
        let value: [String: Any] = ["window_points": [frame.width, frame.height],
            "content_rect_points": [content.minX, frame.height - content.maxY, content.width, content.height],
            "backing_scale": window.backingScaleFactor]
        if let data = try? JSONSerialization.data(withJSONObject: value, options: [.sortedKeys, .prettyPrinted]) {
            try? data.write(to: URL(fileURLWithPath: CommandLine.arguments[index + 1]), options: .atomic)
        }
    }
}

struct ReferenceButton: ButtonStyle {
    var color = ReferenceStyle.green
    func makeBody(configuration: Configuration) -> some View {
        configuration.label.font(ReferenceStyle.font(15, bold: true)).tracking(0.8)
            .frame(maxWidth: .infinity).frame(height: 46)
            .foregroundStyle(.white).background(color, in: RoundedRectangle(cornerRadius: 16))
            .compositingGroup()
            .shadow(color: color == ReferenceStyle.green ? Color(red: 70/255, green: 163/255, blue: 2/255) : Color(red: 24/255, green: 153/255, blue: 214/255), radius: 0, y: configuration.isPressed ? 0 : 4)
            .offset(y: configuration.isPressed ? 4 : 0)
    }
}
