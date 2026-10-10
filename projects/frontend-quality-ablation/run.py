"""Real historical reconstruction task; ablate only measured frontend feedback."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def command(args, cwd, log, timeout=240):
    start = time.monotonic()
    with Path(log).open("w") as output:
        result = subprocess.run(args, cwd=cwd, stdout=output, stderr=subprocess.STDOUT, timeout=timeout)
    return {"exit_code": result.returncode, "seconds": time.monotonic() - start}


def worker(name, prompt, out, binary, registration):
    workspace = out / "empty-worker"
    workspace.mkdir(exist_ok=True)
    result = out / (name + "-result.json")
    write(out / (name + "-prompt.json"), prompt)
    args = [str(binary), "exec", "--ephemeral", "--color", "never", "--model", registration["model"],
            "-c", 'model_reasoning_effort="medium"', "--sandbox", "read-only", "--skip-git-repo-check",
            "--cd", str(workspace), "--output-schema", str(HERE / "schema.json"),
            "--output-last-message", str(result)]
    for image in registration["images"]:
        args += ["--image", str(ROOT / image)]
    args += ["-"]
    start = time.monotonic()
    process = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, start_new_session=True)
    timeout = False
    try:
        stdout, stderr = process.communicate(json.dumps(prompt, ensure_ascii=False), timeout=180)
    except subprocess.TimeoutExpired:
        timeout = True
        os.killpg(process.pid, signal.SIGTERM)
        try:
            stdout, stderr = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            stdout, stderr = process.communicate()
    (out / (name + "-stdout.txt")).write_text(stdout)
    (out / (name + "-stderr.txt")).write_text(stderr)
    header = stderr[:4000]
    fields = {}
    for key in ["model", "reasoning effort", "provider"]:
        found = re.search(r"^" + re.escape(key) + r":\s*(.+)$", header, re.M)
        fields[key] = found.group(1).strip() if found else None
    version = re.search(r"OpenAI Codex v([^\n]+)", header)
    usage = re.search(r"tokens used\s*\n\s*([\d,]+)", stdout + "\n" + stderr)
    receipt = {"exit_code": process.returncode, "timed_out": timeout, "seconds": time.monotonic() - start,
               "runtime": fields, "cli_version": version.group(1) if version else None,
               "reported_tokens": int(usage.group(1).replace(",", "")) if usage else None,
               "fee": "unknown", "input_output_cache_breakdown": "unknown"}
    write(out / (name + "-receipt.json"), receipt)
    if timeout or process.returncode or not version or "codex-cli " + version.group(1).strip() != registration["cli_version"] or fields["model"] != registration["model"] or fields["reasoning effort"] != "medium":
        raise RuntimeError("Actual model/runtime unavailable; retain failure without replacement call")
    return json.loads(result.read_text())


def apply(source, proposal):
    for edit in proposal["edits"]:
        if not edit["old"] or source.count(edit["old"]) != 1:
            raise ValueError("Edit must match exactly once; no manual model-output repair")
        source = source.replace(edit["old"], edit["new"], 1)
    return source


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = (ROOT / args.out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    registration = json.loads((HERE / "registration.json").read_text())
    binary = Path(args.codex).resolve()
    if sha(binary) != registration["cli_sha256"]:
        raise ValueError("Registered CLI binary changed")
    for file, digest in registration["files"].items():
        if sha(ROOT / file) != digest:
            raise ValueError("Registered input changed: " + file)
    checkout = out / "historical-checkout"
    subprocess.run(["git", "worktree", "add", "--detach", str(checkout), registration["baseline_commit"]], cwd=ROOT, check=True)
    target = checkout / registration["target"]
    original = target.read_text()
    common = json.loads((HERE / "input.json").read_text())
    common["source_code"] = original

    def evaluate(name, source):
        print("evaluate " + name, flush=True)
        target.write_text(source)
        folder = out / name
        folder.mkdir()
        (folder / "candidate.swift").write_text(source)
        receipt = {"source_sha256": sha(target)}
        receipt["build"] = command(["swift", "build", "--package-path", "projects/education-swift"], checkout, folder / "build.log")
        if receipt["build"]["exit_code"]:
            receipt["status"] = "build_fail"
            write(folder / "receipt.json", receipt)
            return receipt
        receipt["core"] = command(["swift", "run", "--package-path", "projects/education-swift", "LearningCoreChecks"], checkout, folder / "core.log")
        observation = folder / "native"
        receipt["native"] = command(["swift", "projects/duolingo-web/observe-frontend.swift", str(observation),
            "projects/duolingo-web/fixture-reference-en-zh-v10.json", "--seed-progress",
            "projects/duolingo-web/evidence/english-pronunciation-v2/progress-source.json", "--reference-color-scheme",
            "light", "--observe-pronunciation", "--walk-pronunciation-practice"], checkout, folder / "native.log")
        if receipt["native"]["exit_code"]:
            receipt["status"] = "native_fail"
            write(folder / "receipt.json", receipt)
            return receipt
        command(["python3", "-m", "capabilities.rebuild.frontend", "--contract", str(HERE / "contract.json"),
                 "--observed", str(observation / "observed.json"), "--out", str(folder / "frontend.json")], ROOT, folder / "frontend.log")
        command(["python3", "projects/duolingo-web/compare-english-captures.py", "--native", str(observation),
                 "--pairs", str(HERE / "pairs.json"), "--out", str(folder / "visual.json")], ROOT, folder / "visual.log")
        frontend = json.loads((folder / "frontend.json").read_text())
        receipt["counts"] = {status: sum(row["status"] == status for row in frontend["rows"]) for status in ["pass", "fail", "unavailable", "not_run"]}
        receipt["status"] = "measured" if receipt["core"]["exit_code"] == 0 else "core_fail"
        write(folder / "receipt.json", receipt)
        return receipt

    try:
        baseline = evaluate("baseline", original)
        initial = worker("initial", common, out, binary, registration)
        initial_source = apply(original, initial)
        initial_measurement = evaluate("initial", initial_source)
        revision = dict(common, prior_proposal=initial, source_code=initial_source,
                        instruction="Revise the current implementation using the same source evidence. Edits apply to current source_code, not the original. No tools or external files.")
        # Seal control before the experimental revision sees any actual native feedback.
        control = worker("control", revision, out, binary, registration)
        control_source = apply(initial_source, control)
        write(out / "control-seal.json", {"source_sha256": hashlib.sha256(control_source.encode()).hexdigest()})
        feedback = dict(revision, measured_feedback=initial_measurement)
        folder = out / "initial"
        for file in ["frontend.json", "visual.json", "build.log", "core.log", "native.log"]:
            if (folder / file).exists():
                feedback[file] = (folder / file).read_text()
        full = worker("feedback", feedback, out, binary, registration)
        full_source = apply(initial_source, full)
        write(out / "selection-seal.json", {"control_sha256": hashlib.sha256(control_source.encode()).hexdigest(),
              "feedback_sha256": hashlib.sha256(full_source.encode()).hexdigest(), "final_evaluation": "not_run"})
        control_result = evaluate("control-final", control_source)
        full_result = evaluate("feedback-final", full_source)
        write(out / "result.json", {"baseline": baseline, "initial": initial_measurement,
              "control": control_result, "feedback": full_result, "interpretation": "N=1 historical task; no RSI or generalization claim"})
        print("finished", flush=True)
    except Exception as error:
        write(out / "failure.json", {"status": "unavailable", "error": str(error)})
        raise


if __name__ == "__main__":
    main()
