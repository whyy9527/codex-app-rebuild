"""Explicit shared native E2E bridge; current Codex must service via cua_repl."""
import argparse
import json
from pathlib import Path
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parents[1]
BRIDGE = ROOT / "private/e2e-bridge"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("endpoint", choices=["source", "candidate"])
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    output = (WORKSPACE / args.out).resolve()
    if not output.is_relative_to(WORKSPACE):
        parser.error("Evidence must stay in workspace")
    output.mkdir(parents=True, exist_ok=False)
    BRIDGE.mkdir(parents=True, exist_ok=True)
    source = "https://www.bilibili.com/toy/LkvCZhw12wgT2Pqx/index.html"
    url = source if args.endpoint == "source" else "http://127.0.0.1:4617/"
    cases = json.loads((ROOT / "scenarios.json").read_text())["cases"]
    key = uuid.uuid4().hex
    request = {"id": key, "url": url, "guard": source if args.endpoint == "source" else "127.0.0.1:4617",
               "endpoint": args.endpoint, "workspace": str(output), "cases": cases}
    (BRIDGE / f"{key}.request.json").write_text(json.dumps(request, ensure_ascii=False))
    deadline = time.monotonic() + 240
    while time.monotonic() < deadline:
        reply = BRIDGE / f"{key}.reply.json"
        if reply.exists():
            observed = json.loads(reply.read_text())
            # Evidence references remain portable; actual UI strings are untouched.
            for state in observed.get("states", {}).values():
                for field in ("image", "ax"):
                    state[field] = str(Path(state[field]).relative_to(WORKSPACE))
                from PIL import Image
                with Image.open(WORKSPACE / state["image"]) as image:
                    width, height = image.size
                # This describes the exported screenshot grid, not native Retina scale.
                state["capture_pixels"] = [width, height]
                state["capture"] = {"path": state["image"], "window_points": [width, height],
                                    "backing_scale": 1, "content_rect_points": [0, 80, width, height - 80],
                                    "state_consistent": state.get("state_consistent")}
            (output / "observed.json").write_text(json.dumps(observed, ensure_ascii=False, indent=2))
            print(json.dumps({"endpoint": args.endpoint, "observed": str(output.relative_to(WORKSPACE) / "observed.json"),
                              "states": list(observed.get("states", {})), "error": observed.get("error")}, ensure_ascii=False))
            return 1 if "error" in observed else 0
        time.sleep(.2)
    raise TimeoutError("Native E2E request not serviced within 240 seconds")


if __name__ == "__main__":
    raise SystemExit(main())
