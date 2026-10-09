# Candidate progress corruption repair

This is a LingoSeed data-protection rule already stated by the product, not an observed Duolingo server behavior. Review of the new migration decoder found that missing/null fields defaulted to empty progress. No defect was injected.

Before editing production code, `check-progress-ui.py`, its owned-PID AX probe, fixture-v2 and core tests were frozen by Harness. Limits:3 attempts,3 consecutive failures,1800 seconds total,240 seconds per verification. The first hypothesis predicted that empty-object/null records would show the learning path. Actual native startup confirmed two failures among five cases; invalid JSON, negative hearts and valid legacy empty progress already behaved correctly. Every input file was unchanged.

The next recorded hypothesis required a completion collection and strict decoding of present fields, while permitting missing additive fields for legacy compatibility. Only LearningProgress decoding changed. The unchanged native verifier then passed all five cases; Harness completed after two attempts without resetting budgets or acceptance. Exact evaluation output, source manifests, frozen acceptance, timing and hypotheses are preserved in progress-repair-before/after.json. Workspace paths are redacted.

This establishes one actual candidate business fail→feedback→repair→pass. The repair was performed by the main session. It is not a randomized model comparison, proof of Stop continuation or a change to shared Duolingo assertions. Shared12-scenario and old5-scenario regression results are recorded separately.
