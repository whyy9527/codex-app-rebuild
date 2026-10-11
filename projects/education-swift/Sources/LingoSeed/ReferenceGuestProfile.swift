import SwiftUI

/// The explicit observed guest snapshot; cumulative XP is not supplied by this presentation.
struct GuestProfileSnapshot: Decodable {
    struct Achievement: Decodable {
        let title: String
        let level: Int
        let current: Int
        let target: Int
        let description: String
        let resource: String?
    }
    let joined: String
    let streak: Int
    let experience: Int
    let achievements: [Achievement]
    static let observed: Self? = Bundle.module.url(forResource:"guest-profile-snapshot",withExtension:"json",subdirectory:"Reference")
        .flatMap { try? Data(contentsOf:$0) }.flatMap { try? JSONDecoder().decode(Self.self,from:$0) }
}

struct ReferenceGuestProfile: View {
    let achievements: () -> Void
    var body: some View {
        if let snapshot = GuestProfileSnapshot.observed {
            VStack(alignment:.leading,spacing:0) {
                ZStack(alignment:.top) {
                    RoundedRectangle(cornerRadius:16).fill(Color(red:221/255,green:244/255,blue:1))
                    ReferenceStyle.image("en-guest-avatar").resizable().frame(width:166.125,height:266).offset(y:39)
                    HStack { Spacer();ReferenceStyle.image("en-guest-edit").resizable().frame(width:18,height:18).padding(14).background(RoundedRectangle(cornerRadius:16).stroke(Color.black.opacity(0.3),lineWidth:2)).padding(16) }
                }.frame(width:480,height:224).clipShape(RoundedRectangle(cornerRadius:15))
                HStack {
                    Text(snapshot.joined).accessibilityIdentifier("guest-profile-joined").font(ReferenceStyle.font(17)).foregroundStyle(ReferenceStyle.secondaryInk)
                    Spacer()
                    ReferenceStyle.image("en-home-56c79be7b1d61ed14ae1").resizable().scaledToFit().frame(width:31,height:23.9140625)
                }.frame(height:43.9140625).padding(.top,28)
                Rectangle().fill(ReferenceStyle.border).frame(height:2).padding(.top,22)
                Text("数据统计").font(ReferenceStyle.font(24,bold:true)).foregroundStyle(Color(white:60/255)).frame(height:28).padding(.top,28)
                HStack(spacing:12) {
                    statistic("en-guest-streak",String(snapshot.streak),"连胜天数")
                    statistic("en-guest-xp",String(snapshot.experience),"总经验")
                }.padding(.top,16)
                HStack {
                    Text("成就").font(ReferenceStyle.font(24,bold:true)).foregroundStyle(Color(white:60/255))
                    Spacer()
                    ReferencePracticeControl(label:"显示全部",identifier:"guest-profile-achievements",enabled:true,action:achievements,face:AnyView(Text("显示全部").font(ReferenceStyle.font(15,bold:true)).tracking(0.8).foregroundStyle(ReferenceStyle.blue)),role:.link).frame(width:63.203125,height:18)
                }.frame(height:28).padding(.top,28)
                VStack(spacing:0) {
                    ForEach(Array(snapshot.achievements.enumerated()),id:\.offset) { index,item in
                        if index>0 { Rectangle().fill(ReferenceStyle.border).frame(height:2) }
                        HStack(spacing:30) {
                            ZStack(alignment:.bottom) {
                                if let resource=item.resource { ReferenceStyle.image(resource).resizable().frame(width:77,height:95.859375) }
                                Text("第 \(item.level) 级").font(ReferenceStyle.font(11,bold:true)).foregroundStyle(.white).padding(.bottom,12)
                            }.frame(width:77,height:95.859375)
                            VStack(alignment:.leading,spacing:16) {
                                HStack {Text(item.title).font(ReferenceStyle.font(19,bold:true));Spacer();Text("\(item.current)/\(item.target)").font(ReferenceStyle.font(17)).foregroundStyle(ReferenceStyle.disclosureInk)}
                                GeometryReader { g in
                                    Capsule().fill(ReferenceStyle.border)
                                    Capsule().fill(Color(red:1,green:204/255,blue:0)).frame(width:g.size.width*CGFloat(item.current)/CGFloat(item.target))
                                }.frame(height:14)
                                Text(item.description).font(ReferenceStyle.font(17)).foregroundStyle(ReferenceStyle.secondaryInk)
                            }
                        }.padding(20).frame(height:135.859375)
                    }
                }.overlay(RoundedRectangle(cornerRadius:16).strokeBorder(ReferenceStyle.border,lineWidth:2)).padding(.top,16)
            }.frame(width:480,alignment:.topLeading)
        }
    }
    private func statistic(_ resource:String,_ value:String,_ label:String) -> some View {
        HStack(alignment:.top,spacing:15) {
            ReferenceStyle.image(resource).resizable().scaledToFit().frame(width:21,height:29)
            VStack(alignment:.leading,spacing:4) {
                Text(value).font(ReferenceStyle.font(20,bold:true)).foregroundStyle(Color(white:60/255))
                Text(label).font(ReferenceStyle.font(16)).foregroundStyle(ReferenceStyle.disclosureInk)
            }
            Spacer(minLength:0)
        }.padding(.horizontal,26).padding(.top,14).frame(width:234,height:78,alignment:.topLeading)
            .overlay(RoundedRectangle(cornerRadius:16).strokeBorder(ReferenceStyle.border,lineWidth:2))
    }
}

struct ReferenceGuestProfileIntroduction: View {
    let later: () -> Void
    var body: some View {
        ZStack {
            Color.black.opacity(0.4)
            VStack(spacing:0) {
                ReferenceStyle.image("en-guest-intro").resizable().frame(width:336,height:160).padding(.top,40)
                Text("制作专属虚拟头像！").font(ReferenceStyle.font(24,bold:true)).padding(.top,18)
                // Avatar creation is still an uncovered native branch; do not report it as implemented.
                Text("开始").font(ReferenceStyle.font(15,bold:true)).foregroundStyle(.white).frame(width:336,height:46).background(ReferenceStyle.blue,in:RoundedRectangle(cornerRadius:16)).shadow(color:Color(red:24/255,green:153/255,blue:214/255),radius:0,y:4).padding(.top,32)
                ReferencePracticeControl(label:"下次再说",identifier:"guest-profile-later",enabled:true,action:later,face:AnyView(Text("下次再说").font(ReferenceStyle.font(15,bold:true)).foregroundStyle(ReferenceStyle.blue))).frame(width:336,height:32).padding(.top,20)
                Spacer(minLength:0)
            }.frame(width:384,height:402.5).background(.white,in:RoundedRectangle(cornerRadius:16))
        }
    }
}

struct ReferenceGuestAchievementsError: View {
    var body: some View {
        VStack(spacing:20) {
            Text("Error 404").accessibilityIdentifier("guest-profile-error").font(ReferenceStyle.font(32,bold:true))
            Text("Sorry, the page you were looking for doesn’t exist. Try going to")
            Link("duolingo.com",destination:URL(string:"https://www.duolingo.com")!).accessibilityIdentifier("guest-error-home")
            Text(", or follow us on")
            Link("Twitter",destination:URL(string:"https://twitter.com/duolingo")!).accessibilityIdentifier("guest-error-twitter")
            Text("or")
            Link("Facebook",destination:URL(string:"http://facebook.com/duolingo")!).accessibilityIdentifier("guest-error-facebook")
        }.frame(maxWidth:.infinity,maxHeight:.infinity).background(.white)
    }
}
