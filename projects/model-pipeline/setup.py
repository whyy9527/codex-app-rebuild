"""Prepare a curated owned workspace, excluding the finished Swift app."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from workflows.harness.install import install

PRODUCT_BASELINE = "21dbe64bfea93bf7ef2633ae0152021cad24fc81"


def prepare():
    workspace = Path(tempfile.mkdtemp(prefix="codex-rebuild-host-flow-"))
    for name in ["capabilities", "runtime", "workflows"]:
        shutil.copytree(ROOT / name, workspace / name, ignore=shutil.ignore_patterns("__pycache__"))
    files = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", PRODUCT_BASELINE, "projects/education-swift"], cwd=ROOT, text=True).splitlines()
    for name in files:
        target = workspace / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(subprocess.check_output(["git", "show", PRODUCT_BASELINE + ":" + name], cwd=ROOT))
    case = Path("projects/duolingo-web")
    for name in ["original-adapter-v2.mjs", "native-adapter-v3.swift", "build-native.py", "fixture-v1.json", "fixture-v2.json", "package.json", "package-lock.json"]:
        target = workspace / case / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / case / name, target)
    shutil.copytree(ROOT / case / "node_modules", workspace / case / "node_modules")
    first = json.loads((ROOT / case / "spec-v1.2.json").read_text())
    first["behaviors"] = first["behaviors"][:4]
    first.pop("parent_digest", None)
    first["revision"] = "host-flow-initial-four"
    expanded = json.loads((ROOT / case / "spec-v2.json").read_text())
    expanded.pop("parent_digest", None)
    for specification in [first, expanded]:
        for behavior in specification["behaviors"]:
            for name in behavior.get("evidence", []):
                target = workspace / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / name, target)
    (workspace / "active-spec.json").write_text(json.dumps(first, indent=2) + "\n")
    (workspace / "expanded-template.json").write_text(json.dumps(expanded, indent=2) + "\n")
    shutil.copy2(ROOT / case / "targets-v2.json", workspace / "targets.json")
    shutil.copy2(ROOT / "projects/model-pipeline/run-stage.py", workspace / "run-stage.py")
    shutil.copy2(ROOT / "projects/model-pipeline/PROTOCOL.md", workspace / "PROTOCOL.md")
    (workspace / "AGENTS.md").write_text("""# Registered actual-host feasibility run
Work only in this explicit temporary workspace. Do not read the finished product or another repository. No Git, publishing, login, payment or account changes. Use the installed project exploration MCP and native Hooks. Do not bypass sandbox, trust or approval checks.

Product Sources may be edited. Toolkit, run-stage.py, targets.json, drivers, fixture-v1/v2, expanded-template.json, original evidence, Package.swift and existing Tests are fixed inputs. active-spec.json may change only at discover to form a parent-linked expanded batch that preserves all prior behaviors and assertions. Do not change acceptance to fit the product. An unavailable UI is not a pass.

The existing app starts as a choice-only product. The expanded original curriculum has multiple lessons, matching and word tiles. Use original names/content from the fixtures. Maintain state/UI separation; do not put adapter answers into the UI. Read the actual driver to learn required semantic accessibility identifiers. Preserve failures and use them to repair product Sources.

The fixed verifier advances exactly one real Pipeline stage and only returns0 at complete. Its intermediate exit1 means unfinished; inspect actual stage/candidate receipts for business failures. One attempt per model turn, then checkpoint, allows native Stop behavior to be observed. No manual continuation prompt is expected except the registered explicit two-session handoff. Stop on exhausted budget or unavailable capability.
""")
    registration = install(workspace, workspace)
    tracked = [p for p in workspace.rglob("*") if p.is_file() and "node_modules" not in p.parts and ".codex" not in p.parts]
    manifest = {p.relative_to(workspace).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(tracked)}
    (workspace / "input-manifest.json").write_text(json.dumps({"product_baseline": PRODUCT_BASELINE, "files": manifest}, indent=2) + "\n")
    return {"workspace": str(workspace), "registration": registration, "input_files": len(manifest)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    result = prepare()
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"workspace": result["workspace"], "input_files": result["input_files"]}))
