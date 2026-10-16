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
    parser.add_argument("--suite", choices=['navigation', 'journeys', 'prediction'], default='navigation')
    parser.add_argument("--case")
    parser.add_argument("--content-top", type=int, default=80,
                        help="Measured browser-content top in the actual exported screenshot grid")
    args = parser.parse_args()
    if args.suite == 'prediction' and not args.case:
        parser.error('Prediction cases have independent prestates; select --case playin, share, or locked')
    output = (WORKSPACE / args.out).resolve()
    if not output.is_relative_to(WORKSPACE):
        parser.error("Evidence must stay in workspace")
    output.mkdir(parents=True, exist_ok=False)
    BRIDGE.mkdir(parents=True, exist_ok=True)
    source = "https://www.bilibili.com/toy/LkvCZhw12wgT2Pqx/index.html"
    url = source if args.endpoint == "source" else "http://127.0.0.1:4617/"
    suite_files = {'navigation': 'scenarios.json', 'journeys': 'journeys.json',
                   'prediction': 'prediction.json'}
    cases = json.loads((ROOT / suite_files[args.suite]).read_text())["cases"]
    if args.case:
        cases = [case for case in cases if case['id'] == args.case]
        if not cases:
            parser.error('Requested case is not in the selected suite')
    key = uuid.uuid4().hex
    request = {"id": key, "url": url, "guard": source if args.endpoint == "source" else "127.0.0.1:4617",
               "endpoint": args.endpoint, "suite": args.suite, "workspace": str(output), "cases": cases}
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
                if not 0 <= args.content_top < height:
                    raise ValueError('Measured content top is outside the exported capture')
                # This describes the exported screenshot grid, not native Retina scale.
                state["capture_pixels"] = [width, height]
                state["capture"] = {"path": state["image"], "window_points": [width, height],
                                    "backing_scale": 1, "content_rect_points": [0, args.content_top, width, height - args.content_top],
                                    "state_consistent": state.get("state_consistent")}
            (output / "observed.json").write_text(json.dumps(observed, ensure_ascii=False, indent=2))
            print(json.dumps({"endpoint": args.endpoint, "observed": str(output.relative_to(WORKSPACE) / "observed.json"),
                              "states": list(observed.get("states", {})), "error": observed.get("error")}, ensure_ascii=False))
            return 1 if "error" in observed else 0
        time.sleep(.2)
    raise TimeoutError("Native E2E request not serviced within 240 seconds")


if __name__ == "__main__":
    raise SystemExit(main())
