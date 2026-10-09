import Foundation
import AVFoundation

// Compile alongside LearningAudio.swift: tests the shipped generator and player,
// not a substitute. Playback transport success is not an acoustic recording.
@main struct AudioChecks {
    @MainActor static func main() async throws {
        let output = URL(fileURLWithPath: CommandLine.arguments[1])
        try FileManager.default.createDirectory(at: output, withIntermediateDirectories: true)
        var distinct = Set<Data>()
        for cue in LearningAudio.Cue.allCases {
            let data = LearningAudio.wave(cue)
            let player = try AVAudioPlayer(data: data)
            precondition(player.duration > 0.03 && player.duration < 1)
            precondition(data.count > 1000)
            precondition(String(data: data.prefix(4), encoding: .ascii) == "RIFF")
            distinct.insert(data)
            try data.write(to: output.appendingPathComponent(cue.rawValue + ".wav"))
        }
        precondition(distinct.count == LearningAudio.Cue.allCases.count)
        let audio = LearningAudio()
        precondition(audio.play(.complete))
        try await Task.sleep(for: .milliseconds(100))
        precondition(audio.isPlaying && audio.playbackTime > 0.03)
        audio.muted = true
        precondition(!audio.isPlaying && !audio.play(.correct))
        audio.muted = false
        precondition(audio.play(.correct))
        try await Task.sleep(for: .milliseconds(70))
        precondition(audio.isPlaying && audio.playbackTime > 0)
        audio.muted = true
        print("PASS four distinct decodable WAV cues; actual player time advances; mute stops/blocks; unmute resumes. Acoustic output remains unverified.")
    }
}
