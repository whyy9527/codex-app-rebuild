import AppKit
import SwiftUI

/// Observed skin editor. Preview buffers are source-state images, not the full original renderer.
struct ReferenceGuestAvatar: View {
    @Binding var savedSkin: Int?
    let leave: () -> Void
    let sidebarWidth: CGFloat
    @State private var draft: Int
    @State private var touched = false
    @State private var confirming = false
    init(savedSkin: Binding<Int?>, sidebarWidth:CGFloat, leave: @escaping () -> Void) {
        _savedSkin = savedSkin; self.sidebarWidth=sidebarWidth; self.leave = leave
        _draft = State(initialValue:savedSkin.wrappedValue ?? 0)
    }
    private static let palette: [[Double]] = Bundle.module.url(forResource:"avatar-palette",withExtension:"json",subdirectory:"Reference").flatMap { try? Data(contentsOf:$0) }.flatMap { try? JSONDecoder().decode([[Double]].self,from:$0) } ?? []
    var body: some View {
        GeometryReader { g in
            ZStack(alignment:.topLeading) {
                ReferencePracticeControl(label:"",identifier:"avatar-back",enabled:true,action:{ if touched { confirming = true } else { leave() } },face:AnyView(ReferenceStyle.image("en-avatar-icon-0").resizable().frame(width:24,height:32))).frame(width:24,height:32).offset(x:24,y:24)
                Text(savedSkin == nil ? "创建虚拟头像" : "修改虚拟头像").font(ReferenceStyle.font(24,bold:true)).foregroundStyle(ReferenceStyle.disclosureInk).frame(height:32).offset(x:64,y:24)
                ZStack(alignment:.topLeading) {
                    RoundedRectangle(cornerRadius:16).fill(.white).overlay(RoundedRectangle(cornerRadius:16).strokeBorder(ReferenceStyle.border,lineWidth:2))
                    ReferenceStyle.image("en-avatar-skin-\(draft)").resizable().frame(width:372,height:352).offset(x:2,y:2).accessibilityIdentifier("avatar-preview")
                    Rectangle().fill(ReferenceStyle.border).frame(width:2,height:354).offset(x:374)
                    ForEach(0..<9) { i in
                        ReferenceStyle.image("en-avatar-icon-\(i+1)").resizable().scaledToFit().frame(width:42,height:32).frame(width:58,height:64).offset(x:392+CGFloat(i)*58,y:2)
                    }
                    Rectangle().fill(ReferenceStyle.border).frame(width:520,height:2).offset(x:376,y:64)
                    Rectangle().fill(ReferenceStyle.blue).frame(width:74,height:2).offset(x:376,y:64)
                    Text("肤色").font(ReferenceStyle.font(20,bold:true)).offset(x:408,y:87)
                    ForEach(0..<Self.palette.count,id:\.self) { i in
                        let rgb=Self.palette[i]
                        AvatarSkinRadio(identifier:"avatar-skin-\(i)",selected:draft==i,color:Color(red:rgb[0]/255,green:rgb[1]/255,blue:rgb[2]/255),action:{ draft=i;touched=true })
                            .frame(width:56,height:56).offset(x:411.1640625+CGFloat(i%6)*78.3333333333,y:130+CGFloat(i/6)*72)
                    }
                }.frame(width:896,height:356).clipShape(RoundedRectangle(cornerRadius:16)).offset(x:24,y:80)
                ReferencePracticeControl(label:"完成",identifier:"avatar-done",enabled:touched,action:{ savedSkin=draft; confirming=true },face:AnyView(Text("完成").font(ReferenceStyle.font(16,bold:true)).tracking(0.64).foregroundStyle(touched ? .white : ReferenceStyle.disclosureInk).frame(width:136,height:44).background(touched ? ReferenceStyle.blue : ReferenceStyle.border,in:RoundedRectangle(cornerRadius:12)).compositingGroup().shadow(color:touched ? Color(red:24/255,green:153/255,blue:214/255) : .clear,radius:0,y:4).frame(height:48,alignment:.top))).frame(width:136,height:48).offset(x:784,y:472)
            }.frame(width:g.size.width,height:g.size.height,alignment:.topLeading)
        }
        .overlay { GeometryReader { g in if confirming { ReferenceAvatarExit(keep:{confirming=false},discard:{draft=savedSkin ?? 0;touched=false;confirming=false;leave()}).frame(width:g.size.width+sidebarWidth,height:g.size.height).offset(x:-sidebarWidth) } } }
    }
}

struct ReferenceAvatarExit: View {
    let keep: () -> Void
    let discard: () -> Void
    var body: some View {
        ZStack {
            Color.black.opacity(0.4)
            VStack(spacing:0) {
                Text("确定要退出吗？").font(ReferenceStyle.font(24,bold:true)).frame(height:32).padding(.top,32)
                Text("现在退出的话，刚完成的部分都会丢失哦").font(ReferenceStyle.font(16)).foregroundStyle(ReferenceStyle.secondaryInk).frame(height:24).padding(.top,12)
                ReferencePracticeControl(label:"继续编辑虚拟头像",identifier:"avatar-keep",enabled:true,action:keep,face:AnyView(Text("继续编辑虚拟头像").font(ReferenceStyle.font(15,bold:true)).foregroundStyle(.white).frame(width:336,height:46).background(ReferenceStyle.blue,in:RoundedRectangle(cornerRadius:16)).compositingGroup().shadow(color:Color(red:24/255,green:153/255,blue:214/255),radius:0,y:4).frame(height:50,alignment:.top))).frame(width:336,height:50).padding(.top,32)
                ReferencePracticeControl(label:"放弃编辑虚拟头像",identifier:"avatar-discard",enabled:true,action:discard,face:AnyView(Text("放弃编辑虚拟头像").font(ReferenceStyle.font(15,bold:true)).foregroundStyle(Color(red:1,green:75/255,blue:75/255)))).frame(width:336,height:32).padding(.top,16)
                Spacer(minLength:0)
            }.frame(width:384,height:258).background(.white,in:RoundedRectangle(cornerRadius:16))
        }
    }
}

private struct AvatarSkinRadio: NSViewRepresentable {
    let identifier: String
    let selected: Bool
    let color: Color
    let action: () -> Void
    final class Coordinator: NSObject {
        var action: () -> Void
        init(_ action:@escaping () -> Void) {self.action=action}
        @objc func choose(_ sender:NSButton) {action()}
    }
    final class Radio: NSButton {
        let face=ReferenceAudioRadio.PassiveHost(rootView:AnyView(EmptyView()))
        override func accessibilityRole() -> NSAccessibility.Role? {.radioButton}
        override func accessibilityValue() -> Any? {state == .on ? 1 : 0}
        override var alignmentRectInsets:NSEdgeInsets {NSEdgeInsets(top:0,left:0,bottom:0,right:0)}
        override var intrinsicContentSize:NSSize {NSSize(width:NSView.noIntrinsicMetric,height:NSView.noIntrinsicMetric)}
        override func draw(_ dirtyRect:NSRect) {}
        override func accessibilityFrame() -> NSRect {guard let window else {return super.accessibilityFrame()};return window.convertToScreen(convert(bounds,to:nil))}
    }
    final class Container:NSView {let button=Radio(frame:.zero)}
    func makeCoordinator() -> Coordinator {Coordinator(action)}
    func makeNSView(context:Context) -> Container {
        let container=Container(frame:.zero);let view=container.button;container.addSubview(view);view.translatesAutoresizingMaskIntoConstraints=false
        NSLayoutConstraint.activate([view.leadingAnchor.constraint(equalTo:container.leadingAnchor),view.trailingAnchor.constraint(equalTo:container.trailingAnchor),view.topAnchor.constraint(equalTo:container.topAnchor),view.bottomAnchor.constraint(equalTo:container.bottomAnchor)])
        container.setAccessibilityElement(false);container.setAccessibilityChildren([view])
        view.setButtonType(.radio);view.isBordered=false;view.target=context.coordinator;view.action=#selector(Coordinator.choose(_:));view.setAccessibilityElement(true);view.setAccessibilityChildren([])
        view.addSubview(view.face);view.face.translatesAutoresizingMaskIntoConstraints=false
        NSLayoutConstraint.activate([view.face.leadingAnchor.constraint(equalTo:view.leadingAnchor),view.face.trailingAnchor.constraint(equalTo:view.trailingAnchor),view.face.topAnchor.constraint(equalTo:view.topAnchor),view.face.bottomAnchor.constraint(equalTo:view.bottomAnchor)])
        return container
    }
    func sizeThatFits(_ proposal:ProposedViewSize,nsView:Container,context:Context) -> CGSize? {
        guard let width=proposal.width,let height=proposal.height,width.isFinite,height.isFinite else {return nil};return CGSize(width:width,height:height)
    }
    func updateNSView(_ container:Container,context:Context) {
        let view=container.button
        context.coordinator.action=action;view.state=selected ? .on : .off;view.setAccessibilityIdentifier(identifier);view.setAccessibilityLabel("")
        let edge=selected ? Color(red:132/255,green:216/255,blue:1) : ReferenceStyle.border
        view.face.rootView=AnyView(RoundedRectangle(cornerRadius:12).fill(selected ? Color(red:221/255,green:244/255,blue:1) : .white).overlay(RoundedRectangle(cornerRadius:12).strokeBorder(edge,lineWidth:2)).overlay(RoundedRectangle(cornerRadius:8).fill(color).frame(width:40,height:40)).compositingGroup().shadow(color:edge,radius:0,y:2).frame(height:54,alignment:.top).accessibilityHidden(true))
    }
}
