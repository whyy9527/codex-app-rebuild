"""Parent-only final scoring after both model sessions; never feed scores back."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--control', required=True)
    parser.add_argument('--task', required=True)
    args = parser.parse_args()
    root = Path(args.control).resolve();sys.path.insert(0, str(root))
    from capabilities.exploration.harness import Harness
    from capabilities.exploration.storage import save
    from capabilities.rebuild.contracts import load, verify
    from controller import check_fixed
    h = Harness(root / 'state');task = h.read(args.task)
    history = len(task.get('ownership_history', []))
    early_terminal = history == 0 and task['phase'] in ['blocked', 'budget_exhausted']
    if task.get('verification_in_flight') or (history != 1 and not early_terminal):
        raise ValueError('Two sessions or a terminal first-session failure, and no live verifier, required')
    hooks = [json.loads(line) for line in (root / 'state/hook-events.jsonl').read_text().splitlines()]
    stops = [e for e in hooks if e['event'] == 'Stop' and e['session_id'] == task['session_id']]
    if not stops or stops[-1]['decision'] is not None:
        raise ValueError('Actual session2 final non-continuing Stop required')
    check_fixed()
    if (root / 'artifacts/final-seal.json').exists():
        raise ValueError('Scoring opportunity already consumed; preserve prior results')
    if task['phase'] in ['ready', 'working']:
        h.pause(task['id'], 'Registered final Stop; Sources sealed for private evaluation')
    files = sorted((root / 'worker/projects/education-swift/Sources').rglob('*.swift'))
    snapshot = {str(p.relative_to(root / 'worker')): {'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'content': p.read_text()} for p in files}
    save(root / 'artifacts/final-seal.json', {'sealed_at': time.time(), 'task': task, 'stop_event': stops[-1], 'sources': snapshot})
    for name in ['expanded', 'holdout']:
        contract = load(root, 'spec-' + name + '.json', 'targets.json')
        batch = json.loads((root / ('batch-' + name + '.json')).read_text())
        receipt = verify(root, contract, 'candidate', 300, batch, deadline=time.time() + 1200)
        current = {str(p.relative_to(root / 'worker')): hashlib.sha256(p.read_bytes()).hexdigest() for p in (root / 'worker/projects/education-swift/Sources').rglob('*.swift')}
        if current != {k: v['sha256'] for k, v in snapshot.items()}:
            receipt.update(status='invalid', integrity='changed_after_seal')
        save(root / ('artifacts/final-' + name + '.json'), receipt)
        check_fixed()
        print(json.dumps({'batch': name, 'status': receipt['status'], 'counts': receipt['counts']}), flush=True)


if __name__ == '__main__':
    main()
