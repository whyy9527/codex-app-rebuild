"""Reproduce the preregistered dependency ablations; no model calls."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
BASELINE = 'b0b31c9024385c758c0c253d11e67d78611001e8'
OUT = Path(__file__).resolve().parent
ARMS = {
    'full': None,
    'no_behavior_progress': ('capabilities/rebuild/pipeline.py',
        "            state['events'].append(event)\n            save(self.path(run_id), state)",
        "            state['events'].append(event)\n            save(self.path(run_id), {**state, 'reference_receipt': None, 'candidate_receipt': None})"),
    'no_stop_feedback': ('runtime/harness_hooks.py',
        "    if event=='Stop' and state and state['phase'] in ('ready','working'):",
        "    if False and event=='Stop' and state and state['phase'] in ('ready','working'):"),
    'no_supplemental_discovery': ('capabilities/rebuild/pipeline.py',
        "                    state['stage'] = 'review' if state['discovery_completed'] else 'discover'",
        "                    state['stage'] = 'review'"),
}

def digest(data):
    return hashlib.sha256(data).hexdigest()

def manifest(root, prefixes):
    return {str(p.relative_to(root)): digest(p.read_bytes()) for prefix in prefixes
            for p in sorted((root / prefix).rglob('*')) if p.is_file() and '__pycache__' not in p.parts}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--historical-baseline', action='store_true', help='Explicitly replay the recorded baseline after newer remote commits.')
    args = parser.parse_args()
    remote = subprocess.check_output(['git', 'ls-remote', 'origin', 'refs/heads/main'], cwd=ROOT, text=True).split()[0]
    if remote != BASELINE:
        if not args.historical_baseline:
            raise SystemExit('Remote main differs from frozen baseline; use --historical-baseline for an explicit historical replay.')
        subprocess.run(['git', 'cat-file', '-e', remote + '^{commit}'], cwd=ROOT, check=True)
        subprocess.run(['git', 'merge-base', '--is-ancestor', BASELINE, remote], cwd=ROOT, check=True)
    archive = subprocess.check_output(['git', 'archive', BASELINE], cwd=ROOT)
    report = {'baseline': BASELINE, 'remote_verified': remote, 'python': sys.version,
              'codex_cli': subprocess.check_output(['codex', '--version'], text=True).strip(),
              'driver_sha256': digest(Path(__file__).read_bytes()), 'repetitions': 1,
              'model': None, 'tokens': None, 'cost': None, 'arms': {}}
    baseline_ids = None
    for name, mutation in ARMS.items():
        with tempfile.TemporaryDirectory(prefix='rebuild-ablation-') as directory:
            root = Path(directory)
            with tarfile.open(fileobj=io.BytesIO(archive)) as bundle:
                bundle.extractall(root, filter='data')
            tests = manifest(root, ['tests'])
            before = manifest(root, ['runtime', 'capabilities', 'workflows'])
            report.setdefault('tests', tests)
            report.setdefault('source', before)
            report.setdefault('protocol_sha256', digest((root / 'projects/rebuild-mechanisms/PROTOCOL.md').read_bytes()))
            if mutation:
                path, old, new = mutation
                target = root / path
                source = target.read_text()
                if source.count(old) != 1:
                    raise SystemExit(f'{name}: replacement does not match exactly once')
                target.write_text(source.replace(old, new))
            started = time.monotonic()
            result = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-v'], cwd=root,
                                    env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'},
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=180)
            elapsed = time.monotonic() - started
            raw = result.stdout
            clean = raw.replace(str(root.resolve()), '<workspace>').replace(str(root), '<workspace>').replace(str(ROOT), '<repository>')
            entries = [{'test': m.group(1), 'status': m.group(2)} for m in
                       re.finditer(r'^(test\S+ \([^\n]+\)) \.\.\. (ok|FAIL|ERROR|skipped[^\n]*)$', clean, re.M)]
            ids = [item['test'] for item in entries]
            if baseline_ids is None:
                baseline_ids = ids
            count = re.search(r'Ran (\d+) tests?', clean)
            valid = ids == baseline_ids and len(entries) == 36 and count is not None and int(count.group(1)) == 36
            log = OUT / f'{name}.log'
            log.write_text(clean)
            report['arms'][name] = {'valid': valid, 'elapsed_seconds': round(elapsed, 3),
                'returncode': result.returncode, 'tests': entries, 'passed': sum(e['status'] == 'ok' for e in entries),
                'raw_log_sha256': digest(raw.encode()), 'sanitized_log_sha256': digest(clean.encode()),
                'log': log.name, 'mutation': mutation, 'source_after': manifest(root, ['runtime', 'capabilities', 'workflows']),
                'frozen_tests_unchanged': tests == manifest(root, ['tests']), 'human_interventions': 0}
            (OUT / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
            print(name, valid, report['arms'][name]['passed'], result.returncode, flush=True)
    if not all(arm['valid'] and arm['frozen_tests_unchanged'] for arm in report['arms'].values()):
        raise SystemExit('Invalid arm; inspect results instead of scoring it.')

if __name__ == '__main__':
    main()
