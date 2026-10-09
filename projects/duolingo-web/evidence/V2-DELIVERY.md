# Native v2 delivery check

On 2026-10-10, the actual built LingoSeed was launched with fixture-v2 and an isolated progress file. Only the launched child PID’s AX window was driven and captured. All six images below were inspected: text readable, controls visible, no clipping at the default 940×700 window. The first completed lesson unlocks the second; selected words become locked after correct feedback. The owned process was terminated afterward. Source, binary and image SHA-256 values are in `visual-v2-manifest.json`.

- `lingoseed-v2-path.png`: initial path, second lesson locked.
- `lingoseed-v2-choice.png`: choice activity.
- `lingoseed-v2-matching.png`: pair matching.
- `lingoseed-v2-unlocked.png`: one completed lesson, next available.
- `lingoseed-v2-word-tiles.png`: word bank and answer area.
- `lingoseed-v2-word-feedback.png`: correct ordered phrase and Continue.

This is a visual inspection, separate from the12-scenario native UI verification and five executable core checks. It does not establish responsive layouts, iOS support, educational effectiveness, model efficacy or completion of the full Goal. Empty-object progress acceptance remains a discovered candidate storage defect at this checkpoint.
