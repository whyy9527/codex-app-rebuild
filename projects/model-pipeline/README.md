# Actual model pipeline verification

This directory owns live-host feasibility protocols and their evidence. It does not own the eventual four-arm business ablation.

Run01 used the historical choice-only Swift product and actual Codex gpt-6.1-sol / medium. It passed explore/specify stage gates, then stopped before live reference confirmation. Its first native Stop injected a continuation and the model made a second measured attempt. The old Hook key deduplicated the whole native turn, so the next Stop silently suppressed continuation despite progress. See [result](evidence/run-01/result.json), native-events.jsonl, task.json and pipeline.json. Initial verifier approval denial and all manual setup/recovery interventions are preserved. This is a failed multi-stage feasibility run.

The new regression fails before the repair. The repaired key binds session, native turn and measured checkpoint: repeated notification at one checkpoint is suppressed, a new checkpoint can continue under the same turn, no-progress/new-turn and finite-budget guards still stop. Older persisted turn-only keys remain compatible.37 mechanism checks pass, plus an explicit legacy-key check. These checks are not a corrected native-host pass; [v2 protocol](PROTOCOL-v2.md) registers that separately before execution.

Prepare an owned isolated workspace from the repository root:

```sh
python3 projects/model-pipeline/setup.py --protocol PROTOCOL-v2.md --out artifacts/host-flow/setup-v2.json
```

It copies the fixed toolkit, original UI observations, drivers and original curriculum, but takes product Sources from commit21dbe64 and excludes the finished app/build. It installs project-local Hooks/MCP and records input hashes. Native folder/Hook/tool review is still required. Do not substitute manual verifier calls for model execution. Preserve old attempts and unavailable results.
