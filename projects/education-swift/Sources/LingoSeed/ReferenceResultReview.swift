import SwiftUI
import LearningCore

/// Source-observed result cards. Speech display is independent of grading:
/// a declined card may show the source phrase while accepted remains nil.
struct ReferenceResultReview: View {
    let entries: [ResultReviewEntry]
    let play: (String) -> Void
    let close: () -> Void
    @State private var expanded: String?
    private let ink = Color(red: 88/255, green: 167/255, blue: 0)
    private let fill = Color(red: 215/255, green: 1, blue: 184/255)
    private var rowHeights: [CGFloat] {
        stride(from: 0, to: entries.count, by: 4).map { start in
            entries[start..<min(start + 4, entries.count)].contains { $0.presentation.audioResources.count == 4 } ? 171 : 150
        }
    }
    private func top(_ index: Int) -> CGFloat { rowHeights.prefix(index / 4).reduce(0, +) + CGFloat(index / 4) * 20 }
    private var contentHeight: CGFloat { rowHeights.reduce(0, +) + CGFloat(max(0, rowHeights.count - 1)) * 20 }
    var body: some View {
        GeometryReader { geometry in
            ZStack(alignment: .top) {
                Color.black.opacity(0.4).ignoresSafeArea()
                ScrollView(.vertical) {
                    ZStack(alignment: .topLeading) {
                        RoundedRectangle(cornerRadius: 16, style: .circular).fill(.white)
                        Text("查看你的成绩单！").font(ReferenceStyle.font(32)).foregroundStyle(Color(white: 60/255))
                            .frame(width: 800, height: 38).offset(x: 30, y: 58).accessibilityIdentifier("result-review-title")
                        Text("点击下面的小方块来浏览答案吧！").font(ReferenceStyle.font(25)).foregroundStyle(Color(white: 153/255))
                            .frame(width: 800, height: 30).offset(x: 30, y: 102)
                        ForEach(Array(entries.enumerated()), id: \.element.id) { index, entry in
                            card(entry, index: index).frame(width: 165, height: rowHeights[index / 4])
                                .offset(x: 40 + CGFloat(index % 4) * 185, y: 170 + top(index))
                                .zIndex(expanded == entry.id ? 1 : 0)
                        }
                        Button(action: close) {
                            ReferenceStyle.image("en-result-review-close").resizable().frame(width: 16, height: 16)
                                .frame(width: 35, height: 35).background(.white, in: Circle())
                                .overlay(Circle().strokeBorder(ReferenceStyle.border, lineWidth: 2))
                        }.buttonStyle(.plain).frame(width: 35, height: 35)
                            .offset(x: 842.5, y: -17.5).accessibilityLabel("关闭成绩单").accessibilityIdentifier("result-review-close")
                    }.frame(width: 860, height: 170 + contentHeight + 50)
                        .padding(.top, 24).padding(.bottom, 24)
                        .frame(width: geometry.size.width)
                }.scrollIndicators(.hidden)
            }
        }
    }
    private func card(_ entry: ResultReviewEntry, index: Int) -> some View {
        ZStack(alignment: .topLeading) {
            ReferencePracticeControl(label: entry.presentation.title + (entry.presentation.prompt.isEmpty ? "" : " " + entry.presentation.prompt),
                identifier: "review-card-\(index)", enabled: true,
                action: { expanded = expanded == entry.id ? nil : entry.id }, face: AnyView(
                    ZStack(alignment: .topLeading) {
                        RoundedRectangle(cornerRadius: 10, style: .circular).fill(fill)
                        VStack(alignment: .leading, spacing: 15) {
                            Text(entry.presentation.title).font(ReferenceStyle.font(17)).frame(width: 100, alignment: .leading)
                                .fixedSize(horizontal: false, vertical: true)
                            if !entry.presentation.prompt.isEmpty {
                                Text(entry.presentation.prompt).font(ReferenceStyle.font(17, weight: 400))
                                    .frame(width: 135, alignment: .leading).fixedSize(horizontal: false, vertical: true)
                            }
                        }.foregroundStyle(ink).padding(15)
                        ReferenceStyle.image("en-result-review-check").resizable().frame(width: 12, height: 12)
                            .frame(width: 25, height: 25).background(.white, in: Circle())
                            .offset(x: 125, y: 15)
                    }))
            if !entry.presentation.audioResources.isEmpty {
                let clips = entry.presentation.audioResources
                ForEach(Array(clips.enumerated()), id: \.offset) { j, resource in
                    Button { play(resource) } label: {
                        ReferenceStyle.image("en-match-speaker-source-frame").renderingMode(.template).resizable()
                            .foregroundStyle(.white).frame(width: 21, height: 17)
                            .frame(width: 39, height: 35).background(ReferenceStyle.blue, in: RoundedRectangle(cornerRadius: 18))
                            .shadow(color: Color(red: 24/255, green: 153/255, blue: 214/255), radius: 0, y: 4)
                            .frame(height: 39, alignment: .top)
                    }.buttonStyle(.plain).accessibilityLabel("播放音频 \(j+1)")
                        .accessibilityIdentifier("review-audio-\(index)-\(j)")
                        .offset(x: clips.count == 1 ? 62.5 : 17 + CGFloat(j % 3) * 43, y: 72 + CGFloat(j / 3) * 43)
                }
            }
            if expanded == entry.id {
                VStack(alignment: .leading, spacing: 4) {
                    Text("你的答案：").foregroundStyle(Color(white: 153/255)).font(ReferenceStyle.font(14))
                    Text(entry.answer).font(ReferenceStyle.font(17, weight: 400))
                    Text("正确答案：").foregroundStyle(Color(white: 153/255)).font(ReferenceStyle.font(14)).padding(.top, 16)
                    Text(entry.presentation.correctAnswer).font(ReferenceStyle.font(17, weight: 400))
                }.foregroundStyle(Color(white: 60/255)).padding(15).frame(width: 115, alignment: .leading)
                    .background(RoundedRectangle(cornerRadius: 16).fill(.white))
                    .overlay(RoundedRectangle(cornerRadius: 16).stroke(ReferenceStyle.border, lineWidth: 2))
                    .overlay(alignment: .bottom) {
                        Path { p in p.move(to: CGPoint(x: 0, y: 0)); p.addLine(to: CGPoint(x: 7, y: 7)); p.addLine(to: CGPoint(x: 14, y: 0)) }
                            .fill(.white).frame(width: 14, height: 7).offset(y: 6)
                    }.offset(x: 25, y: -73).accessibilityIdentifier("result-review-answer")
            }
        }
    }
}
