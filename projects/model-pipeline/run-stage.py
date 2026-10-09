"""One actual stage per registered model turn; completion is measured."""
import json
from pathlib import Path
from capabilities.rebuild.pipeline import Pipeline

root = Path.cwd()
pointer = root / "artifacts/host-flow/pipeline.json"
pipeline = Pipeline(root)
if pointer.exists():
    run_id = json.loads(pointer.read_text())["run_id"]
else:
    state = pipeline.start("active-spec.json", "targets.json", max_steps=30, max_seconds=5400)
    run_id = state["id"]
    pointer.parent.mkdir(parents=True, exist_ok=True)
    pointer.write_text(json.dumps({"run_id": run_id}) + "\n")
audit = "discovery-audit.json" if (root / "discovery-audit.json").exists() else None
state = pipeline.step(run_id, audit_path=audit, timeout=600)
fields = ["id", "stage", "steps", "max_steps", "deadline", "batch", "parent", "reference_receipt", "candidate_receipt", "discovered_ids", "last_error", "next_action"]
result = {key: state[key] for key in fields if key in state}
if state["stage"] in ("discover", "review", "complete") and state.get("candidate_receipt"):
    from capabilities.rebuild.contracts import coverage, load
    result["coverage"] = coverage(load(root, "active-spec.json", "targets.json"), json.loads((root / state["candidate_receipt"]).read_text()))
print(json.dumps(result))
raise SystemExit(0 if state["stage"] == "complete" else 1)
