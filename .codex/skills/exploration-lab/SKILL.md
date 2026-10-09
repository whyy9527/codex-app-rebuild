---
name: exploration-lab
description: Use exploration-lab MCP and project hooks for bounded Codex iteration with measured verification, persistent progress and explicit pause.
---

# Exploration Lab

Use when the user requests repeated repair or unattended iteration in an explicit project. Read [the workflow](../../../workflows/harness/WORKFLOW.md); it owns the protocol. Codex performs the reasoning and edits; the tool manages measured feedback and bounded state.

Preserve actual failed results. Registration and trust do not prove Hook execution or automatic model continuation. Do not change acceptance merely to make verification pass, bypass native Hook trust, resume another session's task without explicit paused-task adoption, or start a separate paid model to demonstrate the tool.

Fast same-size Python edits can read stale timestamp bytecode. Harness.verify uses a fresh PYTHONPYCACHEPREFIX per evaluation and disables writes; -B alone does not prevent cache reads.

Native codex mcp add was observed rewriting unrelated server settings. Use the project installer, which owns only its table and Hook entries, backs up files and checks existing settings. Do not restore backups over later user changes indiscriminately.

For a mechanism ablation, commit and push first, freeze the checks, remove one mechanism at a time in isolated copies and report the fixed-check score. Keep model effectiveness claims separate.

## Native CLI appears stalled before verification

Use this recovery only for a CLI/PTY owned by the current task. If tool output stops, inspect its actual Harness state first: a reserved attempt with verification_in_flight unset is different from a running verifier. Silence alone does not establish a crashed host or failed business case.

In native CLI0.162.0-alpha.17.2, an 80×24 PTY stopped painting while awaiting MCP verifier permission. Empty polls, Ctrl-L and WINCH alone did not reveal it; resizing the same owned PTY to100×40 and sending WINCH exposed the pending permission screen. The original session-scoped approval then continued the original attempt successfully. This is a verified UI recovery, not a proven internal cause or universal size requirement.

Resolve the already-known CLI PID's terminal with ps -p <owned-cli-pid> -o tty=. On macOS, after confirming that terminal belongs to this worker, use stty -f /dev/<owned-tty> cols 100 rows 40 and kill -WINCH <owned-cli-pid>, then read the newly rendered screen. Act on the visible permission request under existing authorization; do not send blind Enter, trust unrelated Hooks, permanently allow tools or remove sandboxing.

Preserve task/session IDs, deadline, attempts and actual failures. Do not restart a model/verifier merely to fix painting, patch a live rollout, or count this as automatic model repair. In experiments, record the UI diagnostic intervention and include its wait in wall time; a recovered host does not justify attributing the delay to the ablated mechanism.
