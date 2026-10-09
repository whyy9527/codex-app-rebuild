"""Parent-only single transfer after session1's actual non-continuing Stop."""
import argparse
import json
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--control', required=True)
    parser.add_argument('--task', required=True)
    parser.add_argument('--session', required=True)
    args = parser.parse_args()
    root = Path(args.control).resolve();sys.path.insert(0, str(root))
    from capabilities.exploration.harness import Harness
    from capabilities.exploration.storage import save
    h = Harness(root / 'state');before = h.read(args.task)
    if before['session_id'] != args.session or before.get('ownership_history') or before.get('verification_in_flight'):
        raise ValueError('Wrong owner, transfer already used, or verification still running')
    if before['phase'] in ['blocked', 'budget_exhausted', 'complete']:
        raise ValueError('Terminal arm must not be restarted')
    hooks = [json.loads(line) for line in (root / 'state/hook-events.jsonl').read_text().splitlines()]
    stops = [e for e in hooks if e['event'] == 'Stop' and e['session_id'] == args.session]
    if not stops or stops[-1]['decision'] is not None:
        raise ValueError('Actual non-continuing session1 Stop required')
    state_path = root / 'experiment-state.json'
    state = json.loads(state_path.read_text()) if state_path.exists() else {'phase': 'initial', 'receipts': [], 'handoff_done': False, 'initial_confirmed': False}
    if state['handoff_done']:
        raise ValueError('Single registered transfer already consumed')
    paused = h.pause(args.task, 'Registered single session transfer after actual Stop')
    state['handoff_done'] = True;save(state_path, state)
    record = {'task_id': args.task, 'from_session': args.session, 'before': {k: before[k] for k in ['phase', 'iterations', 'deadline', 'max_iterations']},
              'paused': {k: paused[k] for k in ['phase', 'iterations', 'deadline', 'max_iterations']}, 'stop_event': stops[-1]}
    save(root / 'artifacts/parent-handoff.json', record)
    print(json.dumps(record))


if __name__ == '__main__':
    main()
