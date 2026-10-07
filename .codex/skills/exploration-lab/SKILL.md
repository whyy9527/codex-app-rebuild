---
name: exploration-lab
description: Run and audit codex-exploration-lab experiments, frozen-world policy replay, and evidence-backed self-iteration; use when repeated versions need verified before/after results or Dream-RSI protocol checks.
---

# Exploration Lab

Use this project to separate actual candidate execution from historical replay. Resolve the repository root and read `GOAL.md` and `docs/ARCHITECTURE.md` before choosing an adapter.

## Verified workflow

- Run commands from the repository root with `python3 -m ...`.
- Use `workflows.self_improve run` to record an explicit acceptance command. Fix the acceptance conditions before editing; use distinct IDs and `--parent` links for the next attempt.
- A recorded failure returns nonzero. Preserve it as evidence rather than changing the evaluator to make it pass.
- Run `verify` before `export`. Exports are path-redacted projections, not secret scans; inspect them before committing.
- Use `python3 -m workflows.self_improve.cycle --out artifacts/<fresh-run> --rounds 10` to test the protocol. This uses real executed toy programs and a finite policy portfolio, not LLM research.
- Use `workflows.self_improve.report` with explicit receipts, cycle report and output to check ten-round source-to-commit evidence. Its ten-round convention belongs to this experiment, not all future tasks.

## Interpretation and boundaries

Added tests across rounds do not constitute a fixed benchmark improvement. Within each pair check the evaluator digest; verify exact committed source separately. Keep engineering edit counts, online generator calls and selected policy changes distinct.

Replay only stored outcomes, expose prefixes, and reject unsupported candidates. The incumbent must participate; a better historical reward does not prove improvement on new tasks.

Missing audiovisual review remains unavailable. Do not label frame sampling as continuous viewing, reconstruct deleted outputs from summaries, or convert technical checks into aesthetic scores.

Use trusted adapters only. Generation and policy functions must control their own blocking work. Do not install global hooks, resume unrelated paused tasks or trigger paid model runs merely to demonstrate this skill.
