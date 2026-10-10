---
name: macos-owned-app-audio-output
description: Verify macOS application sound and mute through ScreenCaptureKit output recordings with timed UI actions. Use when player logs or generated WAV files do not prove that the actual owned app emits audio.
---
# Verify owned application audio output

## Failure mechanism

AVAudioPlayer construction, generated WAV bytes and advancing playback time prove separate stages, not application system output. A silent recording is also weak evidence if the clicks happened before capture began. Preserve those transport checks, then record real triggers inside a PID-filtered capture.

## Procedure

Use an isolated app instance and progress file. Record its PID; inspect or terminate only that owned instance. Screen Recording and Accessibility permissions must already be available or obtained through the normal authorized flow.

The repository's tested collector is [capture-owned-audio.swift](../../../projects/duolingo-web/capture-owned-audio.swift). Its optional fourth argument is a JSON array of AX identifiers. Compile and invoke from the repository root:

```sh
swiftc -parse-as-library projects/duolingo-web/capture-owned-audio.swift -o artifacts/capture-owned-audio
artifacts/capture-owned-audio OWNED_PID artifacts/output.wav 7 artifacts/actions.json
```

Adapt the real app's AX identifiers and duration; do not copy the education fixture's answers into a different product. The [product audio suite](../../../projects/duolingo-web/product-audio-checks.py) demonstrates isolated launch, failure reporting and cleanup.

Essential mechanics:

- Find the exact `SCRunningApplication.processID`, use `SCContentFilter(display:including:[app],exceptingWindows:[])`, set `capturesAudio = true` and `captureMicrophone = false`. Add only `.audio` stream output; no screen frames are saved.
- Begin capture before any UI trigger. Drive the owned PID's enabled AX controls and record elapsed action timestamps inside the recording interval. Reject missing controls or incomplete action counts.
- Copy samples with `CMSampleBufferCopyPCMDataIntoAudioBufferList` into an allocated `AVAudioPCMBuffer`; write through `AVAudioFile`. Flush the serial sample queue after `stopCapture` before reading totals/closing the file.
- Require sampled frames and nonzero signal for audible scenarios. For mute, trigger actual sounds while muted and require sampled silence, then unmute and require output again. Do not treat no samples as silence.
- Keep the original WAV and source provenance. For convenient playback, `afconvert -f WAVE -d LEI16 input.wav replay.wav` converts a float WAV to PCM16; it does not create additional audio evidence.

## Verification and limits

Verified on an actual SwiftUI client: choice and instruction speech, correct/incorrect/completion cues, automatic matching feedback, mute during real matching clicks, and restored output. The collector records digital application output; it does not prove physical speaker volume or subjective sound quality. Use a host SDK supporting the collector's ScreenCaptureKit properties; permission/API failure remains unavailable, not pass.

## Avoid false evidence

Never record another app or microphone as a substitute. Do not bypass permission failures, use an unrelated tone generator to prove the product UI, accept silence without in-window triggers, or weaken behavior assertions to make capture succeed. Run UI suites sequentially to avoid focus competition; preserve user progress and failed receipts.
