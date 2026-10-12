"""Finite Dream-RSI discovery/evaluation commands backed by live CUA requests.

This worker never drives a browser itself. The current Codex session services
each request through the fixed native driver, preserving actual UI evidence.
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
    request = {"id": key, "workspace": str(workspace), "role": role, "cases": cases}
    pending = BRIDGE / f"{key}.request.json"
    reply = BRIDGE / f"{key}.reply.json"
    pending.write_text(json.dumps(request, ensure_ascii=False))
    deadline = time.monotonic() + 240
    while time.monotonic() < deadline:
        if reply.exists():
            result = json.loads(reply.read_text())
            if "error" in result:
                raise RuntimeError(result["error"])
            return result
        time.sleep(.2)
    raise TimeoutError("Live native CUA request was not serviced within 240 seconds")


def main():
    request = json.load(sys.stdin)
    workspace = Path(request["workspace"])
    book = json.loads((workspace / "cases.json").read_text())
    plan_file = workspace / "probes.json"
    plan = json.loads(plan_file.read_text()) if plan_file.exists() else []
    mode = sys.argv[1]
    if mode == "agent":
        available = [c for c in book["cases"] if c["id"] not in plan]
        if not available:
            available = book["cases"]
        case = available[0]
        observed = request_ui(workspace, [{"id": case["id"], "query": case["query"]}], "discover")
        if case["id"] not in plan:
            plan.append(case["id"])
        plan_file.write_text(json.dumps(plan))
        return {"generation": {"case": case["id"], "preparation": "reset native source list before query"},
                "observation": {"probe": case["id"], "actual": observed}}
    if mode == "evaluator":
        selected = [c for c in book["cases"] if c["id"] in plan]
        actual = request_ui(workspace, [{"id": c["id"], "query": c["query"]} for c in selected], "evaluate")
        checks = []
        for case, result in zip(selected, actual["results"], strict=True):
            checks.append({"id": case["id"], "pass": result["baseline"] == book["baseline"]
                           and result["result"] == case["expectedResult"]})
        return {"score": sum(c["pass"] for c in checks) / len(book["cases"]),
                "observation": {"checks": checks, "actual": actual, "scope": "fixed source query requirements only"}}
    raise ValueError("Unknown role")


if __name__ == "__main__":
    print(json.dumps(main(), ensure_ascii=False))
