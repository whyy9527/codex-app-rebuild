# Actual model pipeline verification

This directory owns live-host feasibility protocols and their evidence. It does not own the eventual four-arm business ablation.

Run01 used the historical choice-only Swift product and actual Codex gpt-6.1-sol / medium. It passed explore/specify stage gates, then stopped before live reference confirmation. Its first native Stop injected a continuation and the model made a second measured attempt. The old Hook key deduplicated the whole native turn, so the next Stop silently suppressed continuation despite progress. See [result](evidence/run-01/result.json), native-events.jsonl, task.json and pipeline.json. Initial verifier approval denial and all manual setup/recovery interventions are preserved. This is a failed multi-stage feasibility run.

The new regression fails before the repair. The repaired key binds session, native turn and measured checkpoint: repeated notification at one checkpoint is suppressed, a new checkpoint can continue under the same turn, no-progress/new-turn and finite-budget guards still stop. Older persisted turn-only keys remain compatible.37 mechanism checks pass, plus an explicit legacy-key check. These checks are not a corrected native-host pass; [v2 protocol](PROTOCOL-v2.md) registers that separately before execution.

Prepare an owned isolated workspace from the repository root:

```sh
python3 projects/model-pipeline/setup.py --protocol PROTOCOL-v2.md --out artifacts/host-flow/setup-v2.json
```

It copies the fixed toolkit, original UI observations, drivers and original curriculum, but takes product Sources from commit21dbe64 and excludes the finished app/build. It installs project-local Hooks/MCP and records input hashes. Native folder/Hook/tool review is still required. Do not substitute manual verifier calls for model execution. Preserve old attempts and unavailable results.

## Corrected run02 checkpoint

The actual host produced three Stop continuations under one native turn ID, confirmed all four initial online scenarios and froze the batch. A genuinely new model session explicitly adopted the same task, retaining the original deadline and4 used attempts; the old session pointer disappeared. Both the model and parent recomputed reference pass / candidate not_run behavior states from actual receipts. See [checkpoint](evidence/run-02/checkpoint-result.json) and [independent adoption verification](evidence/run-02/adoption-parent-verification.json). A parent attestation clarification and two session-scoped verifier reviews are counted as interventions.

The first native candidate batch subsequently passed4/4, then the discovery gate correctly rejected a missing audit. The model supplied the six-category audit and parent-linked expanded observed inventory, preserving the original scenarios. Expanded reference confirmation and actual Swift extension/repair remain in progress; no full-pipeline success or business effect is claimed at this checkpoint.

## Corrected run02 final result

The same registered task completed in11 attempts and11 pipeline steps across two native model sessions, retaining the original deadline. Actual expanded online reference12/12 and the model's reconstructed native candidate12/12 passed. The review recomputed current-source coverage and the two fixed legacy core checks passed. Session2 produced six native Stop continuations, then a final Stop with no continuation after measured completion. Parent edits to worker product Sources: zero. See [final result](evidence/run-02/final-result.json), expanded receipts, model-product-source.json and curated native events; the old checkpoint remains a historical in-progress snapshot.

The model recovered the long reference tool/status transport timeouts by waiting for the same attempt and reading its eventual receipt. It did not start a replacement run or reset budgets. Missing-audit failure, sandboxed core-check failure and one-off native approval remain recorded. Known observation templates were visible. This establishes the registered full-pipeline feasibility and explicit cross-session continuation, not novel autonomous discovery or a business improvement estimate. The expanded model candidate passed its first native batch; the separate main-product progress-storage fail→repair→pass evidence is not attributed to this model run. Formal business ablation remains pending under projects/business-ablation.
