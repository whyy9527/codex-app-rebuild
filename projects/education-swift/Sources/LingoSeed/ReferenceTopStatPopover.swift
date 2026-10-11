import SwiftUI

/// Actual en/zh hover panels. Remaining streak/hearts panels and course enrollment
/// are source-observed requirements, not claimed complete by these two consumers.
struct ReferenceTopStatPopover: View {
    let kind: String
    let gems: Int
    let flagResource: String
    let selectEnglish: () -> Void
    let visitShop: () -> Void
    var body: some View {
        ZStack(alignment:.topLeading) {
            if kind == "gems" {
                face(width:384,height:152)
                ReferenceStyle.image("en-stats-0de4611fd4d7c682803e").resizable().frame(width:100,height:100).offset(x:14,y:21)
                Text("宝石").font(ReferenceStyle.font(24,bold:true)).frame(width:118,height:28,alignment:.leading).offset(x:126,y:31.75)
                Text("你有 \(gems) 颗宝石").font(ReferenceStyle.font(17)).foregroundStyle(ReferenceStyle.secondaryInk).fixedSize().offset(x:126,y:68.75)
                ReferencePracticeControl(label:"访问宝石小店",identifier:"stat-gems-shop",enabled:true,action:visitShop,face:AnyView(Text("访问宝石小店").font(ReferenceStyle.font(15,bold:true)).tracking(0.8).foregroundStyle(ReferenceStyle.blue)),role:.link,fixedFaceSize:true)
                    .frame(width:94.8046875,height:18).offset(x:126,y:100.75)
                arrow(x:261.9296875,y:-5.0703125)
            } else {
                face(width:244,height:163.3515625)
                Text("我的课程").font(ReferenceStyle.font(15,bold:true)).foregroundStyle(ReferenceStyle.disclosureInk).frame(width:90,height:20,alignment:.leading).offset(x:22,y:14)
                Rectangle().fill(ReferenceStyle.border).frame(width:240,height:2).offset(x:2,y:48)
                ReferencePracticeControl(label:"英语",identifier:"stat-course-english",enabled:true,action:selectEnglish,face:AnyView(ZStack(alignment:.topLeading) {
                    Rectangle().fill(Color(red:221/255,green:244/255,blue:1))
                    ReferenceStyle.image(flagResource).resizable().frame(width:32,height:24.6812438965).offset(x:20,y:13.0851593018)
                    Text("英语").font(ReferenceStyle.font(17,bold:true)).foregroundStyle(Color(red:24/255,green:153/255,blue:214/255)).frame(width:34,height:20).offset(x:72,y:17.671875)
                }),role:.menuItem,fixedFaceSize:true).frame(width:240,height:55.3515625).offset(x:2,y:50)
                Rectangle().fill(ReferenceStyle.border).frame(width:240,height:2).offset(x:2,y:105.3515625)
                ReferenceStyle.image("en-stats-96c4427d97cc128e7a1f").resizable().frame(width:44,height:30).offset(x:16,y:119.3515625)
                Text("添加新课程").font(ReferenceStyle.font(17,bold:true)).frame(width:85,height:20).offset(x:75,y:124.3515625)
                    .accessibilityIdentifier("stat-course-add-label")
                arrow(x:114.9296875,y:-5.0703125)
            }
        }.foregroundStyle(ReferenceStyle.ink)
        .frame(width:kind == "gems" ? 384 : 244,height:kind == "gems" ? 152 : 163.3515625,alignment:.topLeading)
    }
    private func face(width:CGFloat,height:CGFloat)->some View {
        RoundedRectangle(cornerRadius:15,style:.circular).fill(.white)
            .overlay(RoundedRectangle(cornerRadius:15,style:.circular).strokeBorder(ReferenceStyle.border,lineWidth:2)).frame(width:width,height:height)
    }
    private func arrow(x:CGFloat,y:CGFloat)->some View {
        RoundedRectangle(cornerRadius:2,style:.circular).fill(.white).overlay(RoundedRectangle(cornerRadius:2,style:.circular).strokeBorder(ReferenceStyle.border,lineWidth:2)).frame(width:14.140625,height:14.140625).rotationEffect(.degrees(45)).offset(x:x,y:y)
            .overlay(Rectangle().fill(.white).frame(width:20,height:8).offset(x:x-4,y:2))
    }
}
