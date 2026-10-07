"""Run an explicit evaluator and retain its evidence; never assigns an aesthetic score."""
import hashlib
import subprocess
import time
from pathlib import Path
from capabilities.exploration.ledger import digest


def manifest(root):
    root = Path(root).resolve()
    files = {}
    for directory in ("capabilities", "runtime", "workflows", "tests"):
        for path in sorted((root / directory).rglob("*.py")):
            files[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return files


def evaluate(root, command, timeout=30):
    root = Path(root).resolve()
    files = manifest(root)
    started = time.monotonic()
    result = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=timeout)
    output = (result.stdout + result.stderr).replace(str(root), "<workspace>")
    return {
        "command": command,
        "source_files": files,
        "source_digest": digest(files),
        "evaluator_digest": digest({"command": command, "tests": {k: v for k, v in files.items() if k.startswith("tests/")}}),
        "exit_code": result.returncode,
        "status": "pass" if result.returncode == 0 else "fail",
        "output": output,
        "output_sha256": hashlib.sha256(output.encode()).hexdigest(),
        "wall_seconds": round(time.monotonic() - started, 6),
        "model_tokens": None,
        "model_cost": None,
        "audiovisual": "unavailable",
    }
