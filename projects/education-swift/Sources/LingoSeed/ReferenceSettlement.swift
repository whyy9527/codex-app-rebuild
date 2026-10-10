import SwiftUI
import LearningCore

/// Source-observed page sequence. Missing graphics and secondary action branches
/// remain gaps; this renderer does not substitute the old mascot or a fake course.
struct ReferenceSettlement: View {
    let page: SettlementPage
    let mistakesMade: Int
    let advance: () -> Void
    private let yellow = Color(red: 1, green: 0.78, blue: 0)
    private let orange = Color(red: 1, green: 0.58, blue: 0)
    var body: some View {
        VStack(spacing: 0) {
            Spacer(minLength: 0)
            content.frame(maxWidth: 660).frame(maxWidth: .infinity)
            Spacer(minLength: 0)
            if page.kind == "profile" {
                VStack(spacing: 16) {
                    secondary
                    Button(page.continueLabel, action: advance).buttonStyle(ReferenceButton(color: ReferenceStyle.blue))
                        .accessibilityIdentifier("settlement-continue")
                }.frame(width: 340).padding(.bottom, 110)
            } else {
                HStack {
                    if ["result", "streak", "daily_quests", "gems", "achievement"].contains(page.kind) { secondary }
                    Spacer()
                    Button(page.continueLabel, action: advance)
                        .buttonStyle(ReferenceButton(color: page.kind == "streak" ? ReferenceStyle.blue : ReferenceStyle.green))
                        .frame(width: 150).accessibilityIdentifier("settlement-continue")
                }.padding(.horizontal, 140).frame(height: 140)
                    .overlay(alignment: .top) { Rectangle().fill(ReferenceStyle.border).frame(height: 2) }
            }
        }.background(ReferenceStyle.background)
    }
    @ViewBuilder private var secondary: some View {
        if let label = page.secondaryLabel {
            // Visible source affordance only; the branch is not implemented or
            // reported as an exercised button until its source behavior is known.
            Text(label).font(ReferenceStyle.font(16, bold: true)).foregroundStyle(ReferenceStyle.disclosureInk)
                .frame(minWidth: 150, minHeight: 48)
                .overlay(RoundedRectangle(cornerRadius: 15).stroke(ReferenceStyle.border, lineWidth: 2))
        }
    }
    @ViewBuilder private var content: some View {
        switch page.kind {
        case "result":
            VStack(spacing: 12) {
                Color.clear.frame(width: 260, height: 200)
                Text(page.title).font(ReferenceStyle.font(28, bold: true)).foregroundStyle(yellow).accessibilityIdentifier("lesson-complete").accessibilityValue(page.title)
                if let body = page.body { Text(body).font(ReferenceStyle.font(18)) }
                HStack(spacing: 16) {
                    statistic("总经验", value: page.observedMistakes == nil || page.observedMistakes == mistakesMade ? String(page.experience ?? 0) : "—", color: yellow)
                    // Frozen observed result only, never an inferred scoring formula.
                    statistic(page.accuracyLabel ?? "超级棒", value: page.observedMistakes == mistakesMade && page.observedAccuracy != nil ? "\(page.observedAccuracy!)%" : mistakesMade == 0 && page.observedMistakes == nil ? "100%" : "—", color: ReferenceStyle.green)
                }
            }.padding(.bottom, 36)
        case "daily_quests":
            VStack(spacing: 28) {
                Text(page.title).font(ReferenceStyle.font(28, bold: true)).accessibilityIdentifier("settlement-title").accessibilityValue(page.title)
                Text(page.body ?? "").font(ReferenceStyle.font(20))
                ProgressView(value: 1).tint(yellow).frame(width: 360)
                Text("30 / 30").font(ReferenceStyle.font(20, bold: true))
            }
        case "score":
            VStack(spacing: 28) {
                Text("5").font(ReferenceStyle.font(72, bold: true)).foregroundStyle(ReferenceStyle.green)
                Text(page.title).font(ReferenceStyle.font(26, bold: true)).multilineTextAlignment(.center).accessibilityIdentifier("settlement-title").accessibilityValue(page.title)
                HStack(spacing: 16) {
                    Text("5").font(ReferenceStyle.font(20, bold: true))
                    ProgressView(value: 0.25).tint(ReferenceStyle.green).frame(width: 300)
                    Text("6").font(ReferenceStyle.font(20, bold: true))
                }
            }
        case "streak":
            VStack(spacing: 14) {
                ReferenceStyle.image("streak").resizable().scaledToFit().frame(width: 100, height: 120)
                Text(String(page.observedStreak ?? 0)).font(ReferenceStyle.font(96, bold: true)).foregroundStyle(orange)
                Text(page.title).font(ReferenceStyle.font(28, bold: true)).foregroundStyle(orange).accessibilityIdentifier("settlement-title").accessibilityValue(page.title)
                VStack(spacing: 12) {
                    HStack(spacing: 24) {
                        ForEach(Array(["六", "日", "一", "二", "三"].enumerated()), id: \.offset) { i, day in
                            VStack(spacing: 8) {
                                Text(day).foregroundStyle(i < 2 ? orange : ReferenceStyle.disclosureInk)
                                ZStack { Circle().fill(i < 2 ? orange : ReferenceStyle.border); if i < 2 { Text("✓").foregroundStyle(.white).font(ReferenceStyle.font(20, bold: true)) } }.frame(width: 34, height: 34)
                            }
                        }
                    }.font(ReferenceStyle.font(18)).padding(.top, 16)
                    Divider()
                    Text(page.body ?? "").font(ReferenceStyle.font(18)).foregroundStyle(ReferenceStyle.disclosureInk).multilineTextAlignment(.center).padding(.horizontal, 12).padding(.bottom, 16)
                }.frame(width: 340).overlay(RoundedRectangle(cornerRadius: 12).stroke(ReferenceStyle.border, lineWidth: 2)).padding(.top, 18)
            }
        default:
            VStack(spacing: 24) {
                if page.kind != "profile" { Color.clear.frame(width: 220, height: 210) }
                if let level = page.levelLabel { Text(level).font(ReferenceStyle.font(19)) }
                Text(page.title).font(ReferenceStyle.font(page.kind == "profile" ? 28 : 24, bold: true)).multilineTextAlignment(.center).accessibilityIdentifier("settlement-title").accessibilityValue(page.title)
                if let body = page.body { Text(body).font(ReferenceStyle.font(19)).foregroundStyle(ReferenceStyle.disclosureInk).lineSpacing(7).multilineTextAlignment(.center).frame(maxWidth: 430) }
                if page.kind == "legendary" { secondary }
            }.padding(.bottom, 70)
        }
    }
    private func statistic(_ label: String, value: String, color: Color) -> some View {
        VStack(spacing: 0) {
            Text(label).font(ReferenceStyle.font(13, bold: true)).foregroundStyle(.white).frame(height: 26).frame(maxWidth: .infinity).background(color)
            Text(value).font(ReferenceStyle.font(20, bold: true)).foregroundStyle(color).frame(height: 66).frame(maxWidth: .infinity)
        }.frame(width: 163).clipShape(RoundedRectangle(cornerRadius: 16))
            .overlay(RoundedRectangle(cornerRadius: 16).stroke(color, lineWidth: 2))
    }
}
