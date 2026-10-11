import SwiftUI

/// Observed guest bronze page. Ranking membership and remote status persistence remain unverified.
struct ReferenceLeaderboard: View {
    @Binding var selectedStatus: Int?
    let practice: () -> Void
    var body: some View {
        ZStack(alignment:.topLeading) {
            HStack(alignment:.center,spacing:28) {
                ReferenceStyle.image("en-leaderboard-bronze").resizable().frame(width:80,height:91)
                ForEach(0..<9) { _ in ReferenceStyle.image("en-leaderboard-locked").resizable().frame(width:52,height:58) }
            }.offset(x:200)
            Text("青铜等级").font(ReferenceStyle.font(25,bold:true)).frame(width:480,height:30).offset(y:110)
            Text("只要一息尚存，就要坚持到底。来学个单元，挑战本周排行榜！").font(ReferenceStyle.font(19)).foregroundStyle(ReferenceStyle.secondaryInk).multilineTextAlignment(.center).fixedSize(horizontal:false,vertical:true).frame(width:480,height:43).offset(y:153.5)
            ReferencePracticeControl(label:"去学个单元",identifier:"leaderboard-practice",enabled:true,action:practice,face:AnyView(Text("去学个单元").font(ReferenceStyle.font(15,bold:true)).tracking(0.8).foregroundStyle(ReferenceStyle.blue).frame(width:256,height:44).background { RoundedRectangle(cornerRadius:16).fill(.white).overlay(RoundedRectangle(cornerRadius:16).strokeBorder(ReferenceStyle.border,lineWidth:2)).shadow(color:ReferenceStyle.border,radius:0,y:2) }.frame(height:48,alignment:.top)),role:.link)
                .frame(width:256,height:48).offset(x:112,y:215)
            ZStack(alignment:.topLeading) {
                ReferenceStyle.image("en-leaderboard-ghost-rank").resizable().frame(width:16,height:464).offset(x:28)
                ReferenceStyle.image("en-leaderboard-ghost-users").resizable().frame(width:208,height:480).offset(x:68)
                ReferenceStyle.image("en-leaderboard-ghost-xp").resizable().frame(width:48,height:462).offset(x:408)
            }.frame(width:480,height:290,alignment:.topLeading).clipped().mask(LinearGradient(colors:[.white,.white,.clear],startPoint:.top,endPoint:.bottom)).offset(y:311)
            HStack(spacing:20) {
                Text("-").frame(width:24)
                ReferenceLeaderboardAvatar(selectedStatus:$selectedStatus,size:48)
                Spacer();Text("0 经验").font(ReferenceStyle.font(17)).padding(.trailing,34)
            }.font(ReferenceStyle.font(17,bold:true)).foregroundStyle(ReferenceStyle.disclosureInk).padding(.leading,38).frame(width:480,height:72).background(Color(white:247/255),in:RoundedRectangle(cornerRadius:16)).offset(y:612)
        }.frame(width:480,height:684,alignment:.topLeading).clipped()
    }
}
struct ReferenceLeaderboardStatus: View {
    @Binding var selectedStatus: Int?
    var body: some View {
        ZStack(alignment:.topLeading) {
            RoundedRectangle(cornerRadius:16).strokeBorder(ReferenceStyle.border,lineWidth:2)
            Text("设置状态").font(ReferenceStyle.font(19,bold:true)).offset(x:22,y:24.5)
            ReferenceLeaderboardAvatar(selectedStatus:$selectedStatus,size:80).offset(x:146,y:75)
            ReferenceStyle.image("en-leaderboard-smile").resizable().frame(width:36,height:36).padding(4).background(.white,in:Circle()).overlay(Circle().strokeBorder(ReferenceStyle.border,lineWidth:2)).offset(x:212,y:63)
            if let selectedStatus { ReferenceStyle.image("en-leaderboard-status-\(selectedStatus)").resizable().frame(width:40,height:40).offset(x:214,y:67).accessibilityIdentifier("leaderboard-selected-status") }
            ForEach(0..<12) { index in
                ReferencePracticeControl(label:"",identifier:"leaderboard-status-\(index)",enabled:true,action:{ selectedStatus=index },face:AnyView(
                    ReferenceStyle.image("en-leaderboard-status-\(index)").resizable().scaledToFit().frame(width:index==5 ? 32 : 44,height:index==5 ? 25 : 42).frame(width:48,height:44).background(.white,in:RoundedRectangle(cornerRadius:16)).overlay(RoundedRectangle(cornerRadius:16).strokeBorder(ReferenceStyle.border,lineWidth:2)).shadow(color:ReferenceStyle.border,radius:0,y:2).frame(width:48,height:48,alignment:.top)))
                    .frame(width:48,height:48).offset(x:22+CGFloat(index%6)*56,y:187+CGFloat(index/6)*58)
            }
        }.frame(width:368,height:315)
    }
}
struct ReferenceLeaderboardAvatar: View {
    @Binding var selectedStatus: Int?
    let size: CGFloat
    var body: some View {
        ZStack {
            Circle().stroke(ReferenceStyle.disclosureInk,style:StrokeStyle(lineWidth:2,dash:[3,2]))
            Text("U").font(ReferenceStyle.font(size*0.46,bold:true)).foregroundStyle(ReferenceStyle.disclosureInk)
        }.frame(width:size,height:size).overlay(alignment:.bottomTrailing) { Circle().fill(ReferenceStyle.green).frame(width:size*0.2,height:size*0.2).overlay(Circle().stroke(.white,lineWidth:2)) }
    }
}
