"""Request actual native UI discovery and independent repeated navigation.

The main Codex session services requests through native.mjs inside cua_repl.
Snapshots preserve discovered page signatures; they do not restore remote state.
"""
import json
from pathlib import Path
import sys
import time
import uuid

BRIDGE = Path(__file__).resolve().parents[1] / "private/rsi-bridge"


def request_ui(workspace, cases, role):
    BRIDGE.mkdir(parents=True, exist_ok=True)
    key = uuid.uuid4().hex
    pending = BRIDGE / f"{key}.request.json"
    reply = BRIDGE / f"{key}.reply.json"
    pending.write_text(json.dumps({"id": key, "workspace": str(workspace),
                                   "role": role, "cases": cases}, ensure_ascii=False))
    deadline = time.monotonic() + 240
    while time.monotonic() < deadline:
        if reply.exists():
            result = json.loads(reply.read_text())
            if "error" in result:
                raise RuntimeError(result["error"])
            return result
        time.sleep(.2)
    raise TimeoutError("Native CUA request not serviced within 240 seconds")


def main():
    request = json.load(sys.stdin)
    workspace = Path(request["workspace"])
    cases = json.loads((workspace / "cases.json").read_text())["cases"]
    plan_file = workspace / "discoveries.json"
    plan = json.loads(plan_file.read_text()) if plan_file.exists() else {}
    role = sys.argv[1]
    if role == "agent":
        case = next((c for c in cases if c["id"] not in plan), cases[0])
        actual = request_ui(workspace, [case], "discover")
        plan[case["id"]] = actual["results"][0]["headings"]
        plan_file.write_text(json.dumps(plan, ensure_ascii=False))
        return {"generation": {"case": case, "preparation": "navigate source home"},
                "observation": {"discovered": list(plan), "actual": actual}}
    if role == "evaluator":
        selected = [c for c in cases if c["id"] in plan]
        actual = request_ui(workspace, selected, "evaluate")
        checks = [{"id": item["id"], "reproduced":
                   item["headings"] == plan[item["id"]]} for item in actual["results"]]
        return {"score": sum(c["reproduced"] for c in checks) / len(cases),
                "observation": {"checks": checks, "actual": actual,
                                "scope": "reproducible primary navigation only; not product completeness"}}
    raise ValueError("Unknown role")


if __name__ == "__main__":
    print(json.dumps(main(), ensure_ascii=False))
