"""One product verdict: frozen business E2E AND observed frontend requirements.

Run from repository root. A failed frontend check cannot be hidden by semantic
success. This initial contract is deliberately incomplete and reports that fact.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from capabilities.rebuild.frontend import compare
from capabilities.exploration.storage import digest
from runtime.runner import manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    root = Path.cwd()
    output = root / args.out
    output.mkdir(parents=True, exist_ok=False)
    source = digest(manifest(root))
    business = subprocess.run([sys.executable, '-m', 'workflows.rebuild.cli', 'verify',
        '--workspace', '.', '--spec', 'projects/duolingo-web/spec-v2.json',
        '--targets', 'projects/duolingo-web/targets-v2.json', '--target', 'candidate',
        '--frozen', 'projects/duolingo-web/evidence/batch-v2.json', '--timeout', '360',
        '--max-seconds', '1800', '--out', (output / 'business.json').relative_to(root).as_posix()],
        capture_output=True, text=True, timeout=1850)
    (output / 'business.log').write_text(business.stdout + business.stderr)
    probe = subprocess.run(['swift', 'projects/duolingo-web/observe-frontend.swift', str(output / 'frontend')],
        capture_output=True, text=True, timeout=60)
    (output / 'frontend.log').write_text(probe.stdout + probe.stderr)
    frontend = {'status': 'unavailable', 'reason': 'Actual native frontend probe failed'}
    if probe.returncode == 0:
        frontend = compare(root, json.loads((root / 'projects/duolingo-web/frontend-v4.json').read_text()),
                           json.loads((output / 'frontend/observed.json').read_text()))
    (output / 'frontend.json').write_text(json.dumps(frontend, ensure_ascii=False, indent=2) + '\n')
    unchanged = source == digest(manifest(root))
    result = {'kind': 'combined_product_acceptance', 'source_digest': source,
        'source_unchanged': unchanged, 'business_exit_code': business.returncode,
        'frontend_status': frontend['status'],
        'status': 'pass' if unchanged and business.returncode == 0 and frontend['status'] == 'pass' else 'fail',
        'limitations': ['Frontend inventory expands with exploration',
                        'Current pending visual/audio requirements prevent product completion']}
    (output / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result['status'] == 'pass' else 1


if __name__ == '__main__':
    raise SystemExit(main())
