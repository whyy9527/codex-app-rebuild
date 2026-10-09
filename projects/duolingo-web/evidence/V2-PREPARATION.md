# Learning-flow batch preparation

Date: 2026-10-10. This is preparation, not a frozen or passing batch.

After `candidate-v1.1-01.json` passed its four known behaviors, independent browser exploration changed an unsubmitted wrong selection to the correct selection. The visible heart count stayed at 2 during both selections and after the final correct submission. `discovery-reselection.json` preserves all four snapshots and the actual Playwright actions. The initial shared scenarios never changed a selection before submitting. `spec-v1.2.json` adds this behavior while preserving the four prior scenarios and their assertions; word tiles remain unknown in that narrow batch. Its fresh-guest scenario checks the same rule with the independently established initial five hearts.

`spec-v2.draft.json` expands the inventory to 12 observed behaviors. It is not yet reference-confirmed or frozen, and its candidate fixture is a proposed original multi-lesson curriculum. The draft covers selection, reselection, matching, word ordering/undo/error, mistake review, completion/refresh and abandoning a later lesson. Existing word-tile and review observations predate the first candidate pass; they must not be counted as an independent discovery gain.

The v2 browser adapter owns ephemeral guest contexts and uses actual UI controls. The v3 native adapter owns its launched app PID and reads AXWindows. `build-native.py` is intended to build the current Swift source before native verification and record source/binary hashes. Syntax/type checks alone do not prove these new drivers work end to end. Product source has not yet been extended for the new types or multi-lesson fixture; freeze reference acceptance before doing that implementation.

## Raw preparation failures

- `v2-completion-probe-01.jsonl`: completed 12 observed question interactions, then failed to recognize the post-lesson path. The loading poll had a small iteration budget. This is a driver failure, not a Swift business failure.
- `v2-completion-probe-02.jsonl`: the probe request mistakenly used `action` instead of the protocol's `type`; the adapter reported unsupported action. Preserve it as an operator error.
- `v2-completion-probe-03.jsonl`: with the correct request and a longer bounded navigation wait, the actual page showed a streak-goal choice with a disabled “I can do it!” button. That branch was absent from the earlier manually observed navigation. The driver stopped; it did not invent a continuation. The next driver revision explicitly selects the observed seven-day radio and presses that button in its disposable guest context.

The same-context refresh comparison does not imply a backend reset, offline Duolingo clone or cross-device guest persistence. Unknown server rules, exhausted-heart behavior, additional question types and account/payment flows remain outside confirmed acceptance.

`reference-v1.2-01.json` preserved four passing choice behaviors (including reselection), one unknown and one invalid exit-cancel result. The invalid result was the evaluator’s `source_changed` guard: a separate prototype adapter was edited while the formal verifier was running. This was an execution-discipline mistake, not an assertion failure. Re-run with all source edits stopped; do not bypass the integrity guard or accept this receipt for freezing.

- `v2-completion-probe-04.jsonl`: an “I can do it!” button appears both before and inside the goal picker. Re-resolving that label during transition targeted the next disabled button. The following driver revision re-inspects the new UI after a bounded, recorded detached/timeout transition.
- `v2-completion-probe-05.jsonl`: successfully selected the seven-day guest streak goal and reached the optional profile page. Its visible skip button is uppercase “LATER”; the case-sensitive `Later` locator failed. The next revision matches the observed label case-insensitively. Probe 05 driver source is archived; earlier prototype revisions were not archived and their exact source digests are unavailable. These navigation probes do not count as Swift business fail→pass.

- `v2-completion-probe-06.jsonl`: reached lesson completion, returned to the path and refreshed in the same browser context. Both path observations report one completed lesson and current lesson index 1. `v2-completion-probe-06-check.json` applies the draft’s actual shared assertions and passes. This is feasibility evidence, not a reference batch receipt. The exact driver archive and request are recorded in its manifest.

`reference-v1.2-02.json` and `candidate-v1.2-01.json` both pass all five known scenarios; `batch-v1.2.json` is frozen with v1.1 as its parent. `coverage-v1.2.json` retains word tiles as unknown for that batch. No candidate product code needed changing: the discovered reselection rule was already implemented. This is verified coverage growth, not demonstrated improvement in product behavior or model efficacy. The v2 draft now binds to v1.2.
