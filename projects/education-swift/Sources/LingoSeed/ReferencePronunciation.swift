import SwiftUI

struct ReferencePronunciation: View {
    @Bindable var model: LearningModel
    struct Phoneme: Decodable, Identifiable {
        let symbol: String
        let word: String
        let group: String
        let source_label: String
        let element: String
        let audio: String?
        var id: String { element }
    }
    private struct Catalog: Decodable { let phonemes: [Phoneme] }
    private static let phonemes: [Phoneme] = {
        guard let url = Bundle.module.url(forResource: "pronunciation", withExtension: "json", subdirectory: "Reference"),
              let data = try? Data(contentsOf: url), let catalog = try? JSONDecoder().decode(Catalog.self, from: data) else { return [] }
        return catalog.phonemes
    }()
    var body: some View {
        VStack(spacing: 0) {
            Text("一起来学英语发音！").font(ReferenceStyle.font(32, bold: true))
                .frame(maxWidth: .infinity).frame(height: 51.1953125)
            Text("磨耳朵，练就地道英语发音").font(ReferenceStyle.font(19))
                .foregroundStyle(ReferenceStyle.secondaryInk).frame(height: 26.59375).padding(.top, 10)
            Button { model.destination = "PronunciationExercise" } label: {
                Text("开始 +10 经验").font(ReferenceStyle.font(15, bold: true))
                    .foregroundStyle(.white).frame(width: 264, height: 44)
                    .background(ReferenceStyle.blue, in: RoundedRectangle(cornerRadius: 16))
                    .shadow(color: Color(red: 24/255, green: 153/255, blue: 214/255), radius: 0, y: 4)
            }.buttonStyle(.plain).accessibilityIdentifier("pronunciation-start")
                .padding(.top, 20).padding(.bottom, 33)
            section("元音")
            section("辅音")
        }.foregroundStyle(ReferenceStyle.ink)
    }
    private func section(_ title: String) -> some View {
        VStack(spacing: 0) {
            HStack(spacing: 8) {
                Rectangle().fill(ReferenceStyle.border).frame(height: 2)
                Text(title).font(ReferenceStyle.font(20, bold: true)).fixedSize()
                Rectangle().fill(ReferenceStyle.border).frame(height: 2)
            }.padding(.horizontal, 32).frame(height: 44)
            Grid(horizontalSpacing: 8, verticalSpacing: 8) {
                let phonemes = Self.phonemes.filter { $0.group == title }
                ForEach(0..<(phonemes.count / 3), id: \.self) { row in
                    GridRow { ForEach(0..<3, id: \.self) { column in
                    let phoneme = phonemes[row * 3 + column]
                    Button {
                        if let resource = phoneme.audio { model.audio.speak(phoneme.symbol, resource: resource) }
                    } label: {
                        VStack(spacing: 0) {
                            Text(phoneme.symbol).font(ReferenceStyle.font(17)).foregroundStyle(ReferenceStyle.ink)
                            Text(phoneme.word).font(ReferenceStyle.font(15)).foregroundStyle(ReferenceStyle.disclosureInk)
                            Capsule().fill(ReferenceStyle.border).frame(width: 40, height: 8).padding(.top, 4)
                        }.frame(maxWidth: .infinity).frame(height: 68)
                            .background(alignment: .top) {
                                RoundedRectangle(cornerRadius: 16).fill(ReferenceStyle.background).frame(height: 64)
                                    .shadow(color: ReferenceStyle.border, radius: 0, y: 4)
                            }
                            .overlay(alignment: .top) { RoundedRectangle(cornerRadius: 16).strokeBorder(ReferenceStyle.border, lineWidth: 2).frame(height: 64) }
                    }.buttonStyle(.plain).accessibilityLabel(phoneme.source_label).accessibilityIdentifier(phoneme.element)
                    }}
                }
            }.padding(.top, 20)
        }
    }
}
