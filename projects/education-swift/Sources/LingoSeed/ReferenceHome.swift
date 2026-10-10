import SwiftUI
import LearningCore

/// Native rendering of the observed reference home. Course/remaining states
/// continue to come from the model; this view does not supply answer outcomes.
struct ReferenceHome: View {
    @Bindable var model: LearningModel
    @State private var lessonPopoverNode: Int?
    private var chinese: Bool { model.course.interfaceLanguage == "zh" }
    private func copy(_ en: String, _ zh: String) -> String { chinese ? zh : en }
    private func navigationLabel(_ item: String) -> String {
        chinese ? ["Learn":"学习", "Pronunciation":"发音", "Leaderboards":"排行榜", "Quests":"特别任务", "Shop":"宝石小店", "Profile":"个人档案", "More":"更多"][item, default:item] : item.uppercased()
    }
    @State private var moreOpen = false
    @State private var moreHovered = false
    @State private var menuHovered = false
    private var completed: Int { model.progress.completedCount(model.course) }
    private var homeSnapshot: HomeProgressSnapshot? { model.course.home?.progressSnapshots?.first { $0.completedLessons == completed } }
    private var firstNodeCompleted: Bool { chinese && completed >= (model.course.home?.firstNodeLessonCount ?? 4) }
    private let green = ReferenceStyle.green
    private let blue = ReferenceStyle.blue
    var body: some View {
        GeometryReader { geometry in
            HStack(spacing: 0) {
                sidebar.frame(width: geometry.size.width >= 1180 ? 254 : 88)
                Rectangle().fill(ReferenceStyle.border).frame(width: 2)
                if model.destination == "Settings" { ReferenceSettings(model: model) }
                else {
                ScrollView {
                    if model.destination == "Pronunciation" { ReferencePronunciation(model: model).padding(.horizontal, 24).padding(.top, 43) }
                    else if model.destination == "Guidebook" { ReferenceGuidebook(model: model).padding(.horizontal, 24).padding(.top, 48) }
                    else { path.padding(.horizontal, 24).padding(.top, 48) }
                }
                    .frame(maxWidth: .infinity)
                if geometry.size.width >= 1120 {
                    ScrollView { dashboard.padding(.top, 32) }
                        .frame(width: 368).padding(.horizontal, 24)
                }
                }
            }
            .overlay(alignment: .topLeading) {
                if moreOpen { moreMenu.offset(x: geometry.size.width >= 1180 ? 238 : 72, y: 314).zIndex(10) }
            }
        }
        .font(ReferenceStyle.font(17)).foregroundStyle(ReferenceStyle.ink).background(ReferenceStyle.background)
    }
    private var sidebar: some View {
        VStack(alignment: .leading, spacing: 8) {
            ReferenceStyle.image("logo").resizable().scaledToFit().frame(width: 128, height: 30)
                .padding(.leading, 16).padding(.top, 32).padding(.bottom, 22)
            ForEach(chinese ? ["Learn", "Pronunciation", "Leaderboards", "Quests", "Shop", "Profile", "More"] : ["Learn", "Leaderboards", "Quests", "Shop", "Profile", "More"], id: \.self) { item in
                Button {
                    if item == "More" { moreOpen.toggle() }
                    else { model.destination = item; moreOpen = false }
                } label: {
                    HStack(spacing: 20) {
                        ReferenceStyle.image(item == "Pronunciation" ? (model.course.home?.pronunciationResource ?? "nav-test") : "nav-" + item.lowercased()).resizable().scaledToFit().frame(width: 32, height: 32)
                        ViewThatFits(in: .horizontal) {
                            Text(navigationLabel(item)).font(ReferenceStyle.font(15, bold: true)).tracking(0.7).fixedSize()
                            Color.clear.frame(width: 0, height: 1)
                        }
                        Spacer(minLength: 0)
                    }.padding(.horizontal, 16).frame(height: 52)
                        .foregroundStyle((item == model.destination || item == "Learn" && model.destination == "Guidebook") ? blue : ReferenceStyle.secondaryInk)
                        .background((item == model.destination || item == "Learn" && model.destination == "Guidebook") ? Color(red: 221/255, green: 244/255, blue: 1) : .clear, in: RoundedRectangle(cornerRadius: 12))
                        .overlay(RoundedRectangle(cornerRadius: 12).strokeBorder((item == model.destination || item == "Learn" && model.destination == "Guidebook") ? Color(red: 132/255, green: 216/255, blue: 1) : .clear, lineWidth: 2))
                        .contentShape(Rectangle())
                }.buttonStyle(.plain).accessibilityLabel(chinese ? navigationLabel(item) : item).accessibilityIdentifier("nav-" + item.lowercased())
                .onHover { inside in
                    if item == "More" { moreHovered = inside; if inside { moreOpen = true } else { dismissMenuLater() } }
                }
            }
            Spacer(minLength: 0)
        }.padding(.horizontal, 16)
    }
    private func dismissMenuLater() {
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.15) { if !moreHovered && !menuHovered { moreOpen = false } }
    }
    private var moreMenu: some View {
        VStack(alignment: .leading, spacing: 0) {
            ForEach(["Duolingo English Test", "Create a profile", "Settings", "Help", "Sign in"], id: \.self) { title in
                Button { model.destination = title; moreOpen = false } label: {
                    Text(title).font(ReferenceStyle.font(17, bold: true)).frame(maxWidth: .infinity, alignment: .leading).padding(16)
                }.buttonStyle(.plain).accessibilityIdentifier("more-" + title.lowercased().replacingOccurrences(of: " ", with: "-"))
            }
        }.frame(width: 240).background(ReferenceStyle.background, in: RoundedRectangle(cornerRadius: 16))
            .overlay(RoundedRectangle(cornerRadius: 16).stroke(ReferenceStyle.border, lineWidth: 2))
            .shadow(color: .black.opacity(0.08), radius: 8, y: 4)
            .onHover { inside in menuHovered = inside; if !inside { dismissMenuLater() } }
    }
    private var path: some View {
        VStack(spacing: 0) {
            HStack(spacing: 12) {
                VStack(alignment: .leading, spacing: 8) {
                    HStack(spacing: 8) { ReferenceStyle.image("back").resizable().frame(width: 16, height: 16); Text(model.course.home?.sectionTitle ?? "SECTION 1, UNIT 1").font(ReferenceStyle.font(16, bold: true)) }.opacity(0.8)
                    Text(model.course.title).font(ReferenceStyle.font(22, bold: true)).accessibilityIdentifier("course-entry")
                }
                Spacer(minLength: 0)
                Button { model.destination = "Guidebook" } label: {
                    HStack(spacing: 10) { ReferenceStyle.image("guidebook").resizable().frame(width: 24, height: 24); Text(copy("GUIDEBOOK", "指南")).font(ReferenceStyle.font(15, bold: true)).tracking(1) }
                        .padding(.horizontal, 14).frame(height: 48)
                        .overlay(RoundedRectangle(cornerRadius: 15).stroke(Color(red: 70/255, green: 163/255, blue: 2/255), lineWidth: 2))
                        .shadow(color: Color(red: 70/255, green: 163/255, blue: 2/255), radius: 0, y: 2)
                }.buttonStyle(.plain).accessibilityIdentifier("open-guide")
            }.padding(16).frame(height: 90).foregroundStyle(.white).background(green, in: RoundedRectangle(cornerRadius: 12))
            GeometryReader { geometry in
                let center = geometry.size.width / 2
                ReferenceStyle.image("duo-observed-frame").resizable().scaledToFit()
                    .frame(width: 243, height: 261).position(x: center + 103, y: firstNodeCompleted ? 249 : 292)
                ForEach(0..<(chinese ? 5 : 6), id: \.self) { index in
                    let xs: [CGFloat] = [0, -45, -70, -45, 0, 0]
                    let normalY: [CGFloat] = chinese ? [113.5, 204.3515625, 307.2265625, 400.1015625, 476.953125] : [94, 203, 288, 392, 476, 566]
                    let ys = firstNodeCompleted ? (model.course.home?.completedNodeCenters?.map { CGFloat($0) } ?? normalY) : normalY
                    if index == (chinese ? 2 : 3) {
                        ReferenceStyle.image("chest-locked").resizable().scaledToFit().frame(width: 80, height: 90).position(x: center + xs[index], y: ys[index])
                    } else {
                        if chinese { englishPathNode(index).position(x: center + xs[index], y: ys[index]) }
                        else { pathNode(index).position(x: center + xs[index], y: ys[index]) }
                    }
                }
            }.frame(height: firstNodeCompleted ? CGFloat(model.course.home?.completedPathHeight ?? 570) : chinese ? 570 : 640)
            if let home = model.course.home {
                HStack(spacing: 16) { Rectangle().fill(ReferenceStyle.border).frame(height: 2); Text(home.nextSectionTitle).font(ReferenceStyle.font(chinese ? 19 : 20, bold: true)).fixedSize(); Rectangle().fill(ReferenceStyle.border).frame(height: 2) }.foregroundStyle(ReferenceStyle.disclosureInk)
            }
            Text("\(completed) of \(model.course.lessons.count) lessons complete")
                .font(ReferenceStyle.font(13)).foregroundStyle(.secondary).accessibilityIdentifier("completed-count").accessibilityValue(String(completed))
        }.frame(maxWidth: 528).padding(.bottom, 40)
    }
    private func englishPathNode(_ index: Int) -> some View {
        let node = model.course.pathNodes.flatMap { $0.indices.contains(index) ? $0[index] : nil }
        let total = node?.lessonCount ?? model.course.home?.firstNodeLessonCount ?? 4
        let nodeDone = node?.lessonIDs.filter { model.progress.completedLessons[model.course.id, default: []].contains($0) }.count ?? completed
        let next = model.course.lessons.indices.first { !model.progress.isCompleted(model.course, index: $0) }
        let activeIndex = firstNodeCompleted ? 1 : 0
        let active = index == activeIndex
        let finished = firstNodeCompleted && index == 0
        return ZStack {
            if active {
                Circle().stroke(ReferenceStyle.border, lineWidth: 7).padding(3.5)
                if nodeDone > 0 { Circle().trim(from: 0, to: CGFloat(nodeDone) / CGFloat(total)).stroke(green, style: StrokeStyle(lineWidth: 7, lineCap: .round)).rotationEffect(.degrees(-90)).padding(3.5) }
            }
            Button { if active || finished { lessonPopoverNode = lessonPopoverNode == index ? nil : index } } label: {
                ReferenceStyle.image(finished ? model.course.home?.completedNodeResource ?? "star-active" : index == 4 ? "review-locked" : active ? "star-active" : "star-locked").resizable().scaledToFit().frame(width: 42, height: 34)
                    .frame(width: 70, height: 56).background(active || finished ? green : ReferenceStyle.border, in: Ellipse())
                    .compositingGroup().shadow(color: active || finished ? Color(red: 70/255, green: 163/255, blue: 2/255) : Color(white: 183/255), radius: 0, y: 8)
                    .frame(height: 65, alignment: .top).contentShape(Rectangle())
            }.buttonStyle(.plain).accessibilityLabel(active ? "Lesson \(nodeDone + 1) of \(total)" : index == 4 ? "复习该部分" : index == 3 ? "Practice" : "Lesson")
                .accessibilityIdentifier(index == 0 ? "start-lesson" : "start-lesson-\(index)")
            if active && lessonPopoverNode != index {
                Text("开始").font(ReferenceStyle.font(17, bold: true)).foregroundStyle(green).frame(width: 78, height: 42)
                    .background(ReferenceStyle.background, in: RoundedRectangle(cornerRadius: 10))
                    .overlay(RoundedRectangle(cornerRadius: 10).stroke(ReferenceStyle.border, lineWidth: 2)).offset(y: -61)
            }
            if lessonPopoverNode == index {
                VStack(alignment: .leading, spacing: 5) {
                    Text(model.course.title).font(ReferenceStyle.font(19, bold: true))
                    if finished {
                        Text("完成传奇挑战，展示你的传奇实力").font(ReferenceStyle.font(17))
                        Text("练习 +5 经验").font(ReferenceStyle.font(17, bold: true)).padding(.top, 14)
                        Text("晋升传奇 +40 经验").font(ReferenceStyle.font(17, bold: true)).padding(.top, 14)
                    } else {
                        Text("第 \(nodeDone + 1)/\(total) 单元").font(ReferenceStyle.font(17))
                        Button(next.flatMap { model.course.lessons[$0].entry } != nil ? "开始 +20 经验" : "开始 +10 经验") { if let next { lessonPopoverNode = nil; model.begin(next) } }
                            .buttonStyle(SeedButtonStyle(fill: .white, foreground: green)).frame(maxWidth: .infinity).padding(.top, 14)
                            .disabled(next == nil).accessibilityIdentifier("start-lesson-confirm")
                    }
                }.foregroundStyle(.white).padding(16).frame(width: 294).background(green, in: RoundedRectangle(cornerRadius: 15)).offset(y: 134)
            }
        }.frame(width: active ? 100 : 70, height: active ? 100 : 65).zIndex(lessonPopoverNode == index ? 2 : 0)
    }
    private func pathNode(_ index: Int) -> some View {
        let node = model.course.pathNodes?.indices.contains(index) == true ? model.course.pathNodes?[index] : nil
        let nextID = node?.lessonIDs.first { id in !model.progress.completedLessons[model.course.id, default: []].contains(id) }
        let nodeIndex = nextID.flatMap { id in model.course.lessons.firstIndex { $0.id == id } }
        let lessonIndex = node == nil ? min(index, model.course.lessons.count - 1) : nodeIndex ?? 0
        let unlocked = node == nil ? index < model.course.lessons.count && model.progress.isUnlocked(model.course, index: lessonIndex)
            : nodeIndex != nil && model.progress.isUnlocked(model.course, index: lessonIndex)
        let nodeDone = node?.lessonIDs.filter { model.progress.completedLessons[model.course.id, default: []].contains($0) }.count ?? 0
        let nodeTotal = node?.lessonIDs.count ?? 0
        return VStack(spacing: 0) {
            if index == 0 {
                Text("START").font(ReferenceStyle.font(17, bold: true)).foregroundStyle(green)
                    .frame(width: 78, height: 42).background(ReferenceStyle.background, in: RoundedRectangle(cornerRadius: 10))
                    .overlay(RoundedRectangle(cornerRadius: 10).stroke(ReferenceStyle.border, lineWidth: 2)).offset(y: -6)
            }
            Button { model.begin(lessonIndex) } label: {
                ReferenceStyle.image(index == 5 ? "review-locked" : unlocked ? "star-active" : "star-locked")
                    .resizable().scaledToFit().frame(width: 42, height: 34)
                    .frame(width: 70, height: 56).background(unlocked ? green : ReferenceStyle.border, in: Ellipse())
                    .compositingGroup()
                    .shadow(color: unlocked ? Color(red: 70/255, green: 163/255, blue: 2/255) : Color(white: 183/255), radius: 0, y: 8)
                    .padding(index == 0 ? 12 : 0)
                    .overlay { if index == 0 {
                        Circle().stroke(ReferenceStyle.border, lineWidth: 7)
                        if nodeTotal > 0 && nodeDone > 0 { Circle().trim(from: 0, to: CGFloat(nodeDone) / CGFloat(nodeTotal)).stroke(green, style: StrokeStyle(lineWidth: 7, lineCap: .round)).rotationEffect(.degrees(-90)) }
                    } }
            }.buttonStyle(.plain).disabled(!unlocked)
                .accessibilityLabel(nodeTotal > 0 ? "Lesson \(nodeDone + 1) of \(nodeTotal)" : "Lesson \(lessonIndex + 1)")
                .accessibilityIdentifier(index == 0 ? "start-lesson" : "start-lesson-\(index)")
        }.frame(width: 100, height: index == 0 ? 132 : 70)
    }
    private var dashboard: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                stat(model.course.home?.flagResource ?? "flag-spanish", chinese ? "5" : "1", color: ReferenceStyle.ink, width: 31)
                Spacer(); stat("streak", "\(homeSnapshot?.streak ?? (completed > 0 ? 1 : 0))", color: .orange, width: 23)
                Spacer(); stat("gems", "\(homeSnapshot?.gems ?? (500 + completed * 5))", color: blue, width: 22)
                Spacer(); stat("hearts", "\(model.progress.hearts)", color: .red, width: 28)
            }.padding(.horizontal, 12).padding(.bottom, 16)
            card {
                HStack {
                    Text(homeSnapshot?.leagueTitle ?? copy("Unlock Leaderboards!", "来解锁排行榜吧！")).font(ReferenceStyle.font(19, bold: true))
                    if let link = homeSnapshot?.leagueLink { Spacer(); Button(link) { model.destination = "Leaderboards" }.buttonStyle(.plain).font(ReferenceStyle.font(15, bold: true)).foregroundStyle(blue).accessibilityIdentifier("view-leaderboards") }
                }
                HStack(spacing: 20) {
                    ReferenceStyle.image(homeSnapshot?.leagueResource ?? "league-locked").resizable().scaledToFit().frame(width: 70, height: 50)
                    VStack(alignment: .leading, spacing: 8) {
                        Text(homeSnapshot?.leagueMessage ?? copy("Complete \(max(0, 3 - completed)) more lessons to start competing", "再学 \(max(0, 3 - completed)) 个单元，就能参加排行榜挑战了")).font(ReferenceStyle.font(17)).foregroundStyle(Color(white: 119/255)).lineSpacing(4)
                        if let countdown = homeSnapshot?.leagueCountdown { Text(countdown).font(ReferenceStyle.font(15)).foregroundStyle(Color(white: 175/255)) }
                    }
                }.padding(.top, 12)
            }.frame(height: 150)
            card {
                HStack { Text(copy("Daily Quests", "每日特别任务")).font(ReferenceStyle.font(19, bold: true)); Spacer(); Button(copy("VIEW ALL", "显示全部")) { model.destination = "Quests" }.buttonStyle(.plain).font(ReferenceStyle.font(15, bold: true)).foregroundStyle(blue).accessibilityIdentifier("view-quests") }
                HStack(spacing: 20) {
                    ReferenceStyle.image("quest-xp").resizable().scaledToFit().frame(width: 60, height: 60)
                    VStack(alignment: .leading, spacing: 16) {
                        Text(copy("Earn \(homeSnapshot?.questTarget ?? 10) XP", "获取 \(homeSnapshot?.questTarget ?? 10) 经验")).font(ReferenceStyle.font(17, bold: true))
                        ZStack {
                            Capsule().fill(Color(white: 229/255)).frame(height: 18)
                            if completed > 0 { Capsule().fill(Color(red: 1, green: 200/255, blue: 0)).frame(height: 18) }
                            Text("\(homeSnapshot?.questProgress ?? min(10, completed * 10)) / \(homeSnapshot?.questTarget ?? 10)").font(ReferenceStyle.font(14, bold: true)).foregroundStyle(Color(red: 204/255, green: 144/255, blue: 0))
                        }.overlay(alignment: .trailing) { ReferenceStyle.image("quest-chest").resizable().scaledToFit().frame(width: 33, height: 35).offset(x: 0) }
                    }
                }.padding(.top, 10)
            }.frame(height: 165)
            card {
                Text(copy("Create a profile to save your progress!", "创建个人档案，保存学习进度！")).font(ReferenceStyle.font(19, bold: true))
                VStack(spacing: 14) {
                    Button(copy("CREATE A PROFILE", "创建档案")) { model.destination = "Create a profile" }.buttonStyle(ReferenceButton()).accessibilityIdentifier("view-profile")
                    Button(copy("SIGN IN", "登录")) { model.destination = "Sign in" }.buttonStyle(ReferenceButton(color: blue)).accessibilityIdentifier("sign-in")
                }.padding(.top, 12)
            }.frame(height: 201)
            Text(copy("ABOUT    BLOG    STORE    EFFICACY    CAREERS\n\nINVESTORS    TERMS    PRIVACY", "关于我们    宝石小店    有效性    招聘贤才\n\n投资者    条款    隐私")).font(ReferenceStyle.font(12, bold: true)).foregroundStyle(Color(white: 175/255)).frame(maxWidth: .infinity).multilineTextAlignment(.center).padding(.top, 18)
        }
    }
    private func stat(_ image: String, _ text: String, color: Color, width: CGFloat) -> some View {
        HStack(spacing: 12) { ReferenceStyle.image(image).resizable().scaledToFit().frame(width: width, height: 28); Text(text).font(ReferenceStyle.font(15, bold: true)).foregroundStyle(color) }
    }
    private func card<Content: View>(@ViewBuilder content: () -> Content) -> some View {
        VStack(alignment: .leading, spacing: 16, content: content).padding(20).frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
            .overlay(RoundedRectangle(cornerRadius: 16).strokeBorder(ReferenceStyle.border, lineWidth: 2))
    }
}
