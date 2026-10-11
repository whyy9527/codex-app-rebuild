import SwiftUI
import RiveRuntime

/// Actual source avatar-builder asset and state-machine inputs, observed through
/// loaded public resources. These inputs compose the avatar, rather than swap photos.
@MainActor final class SourceAvatarPlayer: ObservableObject {
    let model: RiveViewModel?
    let error: String?
    private let defaultAnimation: Double
    @Published private(set) var inputSnapshot = "unavailable"
    static let initial: [String:Int] = {
        guard let url = Bundle.module.url(forResource:"avatar-initial-state",withExtension:"json",subdirectory:"Reference"),
              let bytes = try? Data(contentsOf:url),
              let values = try? JSONDecoder().decode([String:Int].self,from:bytes) else { return [:] }
        return values
    }()
    init() {
        do {
            guard let url = Bundle.module.url(forResource:"en-avatar-builder",withExtension:"riv",subdirectory:"Reference") else { throw CocoaError(.fileNoSuchFile) }
            let file = try RiveFile(data:Data(contentsOf:url),loadCdn:false)
            model = RiveViewModel(RiveModel(riveFile:file),stateMachineName:"SMAvatar",fit:.cover,alignment:.center,autoPlay:true)
            defaultAnimation = Double(model?.numberInput(named:"ENG_ONLY_Animation")?.value() ?? 0)
            error = nil
        } catch {
            model = nil
            defaultAnimation = 0
            self.error = "原版头像动画载入失败"
        }
    }
    func update(skin: Int, animations: Bool) {
        var values = Self.initial
        // Actual source IMAGE button values run from15 down to1.
        values["SkinTone"] = 15-skin
        values["ENG_ONLY_Zoom"] = 3
        for (name,value) in values { model?.setInput(name,value:Double(value)) }
        model?.setInput("ENG_ONLY_Animation",value:animations ? defaultAnimation : 0)
        inputSnapshot = measuredInputs
        if CommandLine.arguments.contains("--render-metadata") {
            // Read the runtime numbers after applying inputs; never emit pass flags.
            let line = "avatar-runtime-inputs " + inputSnapshot + "\n"
            FileHandle.standardError.write(Data(line.utf8))
        }
    }
    var measuredInputs: String {
        var values: [String:Double] = [:]
        for name in Array(Self.initial.keys)+["ENG_ONLY_Zoom","ENG_ONLY_Animation"] {
            if let value = model?.numberInput(named:name) { values[name] = Double(value.value()) }
        }
        guard let data = try? JSONSerialization.data(withJSONObject:values,options:[.sortedKeys]),
              let string = String(data:data,encoding:.utf8) else { return "unavailable" }
        return string
    }
}

struct ReferenceAvatarRenderer: View {
    let skin: Int
    let animations: Bool
    @StateObject private var player = SourceAvatarPlayer()
    var body: some View {
        Group {
            if let model = player.model { RiveViewRepresentable(viewModel:model) }
            else { Text(player.error ?? "原版头像动画不可用") }
        }
        .onAppear { player.update(skin:skin,animations:animations) }
        .onChange(of:skin) { _,_ in player.update(skin:skin,animations:animations) }
        .onChange(of:animations) { _,_ in player.update(skin:skin,animations:animations) }
        .accessibilityElement(children:.ignore)
        .accessibilityLabel(player.model == nil ? "unavailable" : "SMAvatar")
        .accessibilityValue(player.inputSnapshot)
        .accessibilityIdentifier("avatar-preview")
    }
}
