---
name: exploration-lab
description: Use codex-exploration-lab MCP tools and hooks for bounded Codex iteration; audit fixed acceptance feedback, native host registration, or historical Dream-RSI experiments.
---

# Exploration Lab

Use this project to separate actual candidate execution from historical replay. Resolve the repository root and read `GOAL.md` and `docs/ARCHITECTURE.md` before choosing an adapter.

## Codex harness workflow

For registered-tool iteration, read [the canonical harness workflow](../../../workflows/harness/WORKFLOW.md). Follow its explicit session scope, frozen verifier, bounded attempts and user pause behavior. Historical paper adapters below remain separate.

Native inventory and trust are separate from execution: verify with `workflows.harness.diagnose`, then require actual hook output or host-driven continuation evidence before claiming automation. Do not bypass native trust or count a protocol fixture as a model run. Current host does not list Interrupt; do not infer support from documentation or configuration alone.

Verified failure mechanisms:

- Fast same-size Python source edits can hit stale timestamp-based bytecode and give false feedback. `Harness.verify` uses a fresh `PYTHONPYCACHEPREFIX` and disables writes for each evaluation. Keep the original failed receipt; never modify acceptance to conceal a cache problem. A generic `-B` alone does not prevent reading existing caches.
- Native `codex mcp add` can normalize unrelated existing server definitions. The project installer appends only its owned table, rejects a name collision, backs up originals, and checks pre-existing semantic settings. Use that owner rather than rewriting the whole user config; never restore backups indiscriminately over subsequent user edits.

## Verified workflow

- Run commands from the repository root with `python3 -m ...`.
- Use `workflows.self_improve run` to record an explicit acceptance command. Fix the acceptance conditions before editing; use distinct IDs and `--parent` links for the next attempt.
- A recorded failure returns nonzero. Preserve it as evidence rather than changing the evaluator to make it pass.
- Run `verify` before `export`. Exports are path-redacted projections, not secret scans; inspect them before committing.
- Use `python3 -m workflows.self_improve.cycle --out artifacts/<fresh-run> --rounds 10` to test the protocol. This uses real executed toy programs and a finite policy portfolio, not LLM research.
- Use `workflows.self_improve.report` with explicit receipts, cycle report and output to check ten-round source-to-commit evidence. Its ten-round convention belongs to this experiment, not all future tasks.

## Actual model handoff and paper-stage audit

Use this path when CLI model availability fails or when auditing feedback-driven source synthesis. A model catalog entry is not proof of account access: perform a bounded real request, keep its failure, and never replace it with a test double counted as a model result. `CodexWorker` requires an explicit model; the interactive broker is a different transport with no independent identity/token attestation.

Run `python3 -m workflows.paper.experiment --input <explicit-input> --out artifacts/<run> --iterations 10 --max-calls 4`. When it requests code, inspect `python3 -m workflows.paper.requests --directory artifacts/<run>/requests`; read the actual feedback before generating source. Submit with `--source <source-file> --request-digest <pending-digest> --rationale '<reason>'`, then repeat the experiment command. Do not manufacture model replies, prewrite all iterations before feedback, or treat unchanged optimal code as an improvement.

Audit the exported experiment with `python3 -m workflows.paper.audit --receipts <receipts> --experiment <experiment-report> --replay --out artifacts/<audit>.json`. This checks feedback chains, response source and executed artifacts, and reruns policy selection. Identical request bindings reuse responses: distinguish unique response count, generation attempts, evaluated candidates and selected policy updates. A cached shared response is not an independent model call or statistical control.

If source-to-commit audit differs, preserve the executed snapshot and state the mismatch; never rewrite a receipt to fit the commit. The current driver reselects the complete policy pool and audit reconstructs it from feedback. See `projects/paper-v3/REPORT.md` for verified commands and limitations. Frozen-history reselection is not new-task validation; ties or unexercised branches do not establish new capability.

For availability use `workflows.paper.preflight --model <explicit-model> --out <result>`; failure stays unavailable for experimentation. For independent algorithm validation use `workflows.paper.validation` with explicit program workspaces and seeds. Keep a tied validation set instead of replacing it until improvement appears. Request scopes separate experiment arms; response-use counters do not attest independent host context or concurrent billing. Workspace preparation recovery was tested, but model-return-to-state-commit recovery is still incomplete.

## Interpretation and boundaries

Added tests across rounds do not constitute a fixed benchmark improvement. Within each pair check the evaluator digest; verify exact committed source separately. Keep engineering edit counts, online generator calls and selected policy changes distinct.

Replay only stored outcomes, expose prefixes, and reject unsupported candidates. The incumbent must participate; a better historical reward does not prove improvement on new tasks.

Missing audiovisual review remains unavailable. Do not label frame sampling as continuous viewing, reconstruct deleted outputs from summaries, or convert technical checks into aesthetic scores.

Use trusted adapters only. Generation and policy functions must control their own blocking work. Register global hooks only within the user-authorized integration scope and follow native review. Do not resume unrelated paused tasks or trigger paid model runs merely to demonstrate this skill.
