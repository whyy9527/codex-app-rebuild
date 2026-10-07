"""Run an explicit evaluator and retain its evidence; never assigns an aesthetic score."""
import hashlib
import math
import os
import signal
import subprocess
import tempfile
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
    if not command or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("explicit command and positive finite timeout required")
    root = Path(root).resolve()
    files = manifest(root)
    started = time.monotonic()
    exit_code, status = None, "unavailable"
    with tempfile.TemporaryFile() as stream:
        process = None
        try:
            process = subprocess.Popen(command, cwd=root, stdout=stream, stderr=stream, start_new_session=True)
            try:
                exit_code = process.wait(timeout=timeout)
                status = "pass" if exit_code == 0 else "fail"
            except subprocess.TimeoutExpired:
                status = "timeout"
        except OSError as error:
            stream.write(str(error).encode())
        finally:
            if process is not None:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()
        stream.seek(0, 2)
        output_bytes = stream.tell()
        stream.seek(0)
        output = stream.read(65536).decode(errors="replace").replace(str(root), "<workspace>")
    return {
        "command": command,
        "source_files": files,
        "source_digest": digest(files),
        "evaluator_digest": digest({"command": command, "tests": {k: v for k, v in files.items() if k.startswith("tests/")}}),
        "exit_code": exit_code,
        "status": status,
        "output": output,
        "output_bytes": output_bytes,
        "output_truncated": output_bytes > 65536,
        "output_sha256": hashlib.sha256(output.encode()).hexdigest(),
        "wall_seconds": round(time.monotonic() - started, 6),
        "model_tokens": None,
        "model_cost": None,
        "audiovisual": "unavailable",
    }
