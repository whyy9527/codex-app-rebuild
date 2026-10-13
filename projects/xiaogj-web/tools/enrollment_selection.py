"""Actual readonly enrollment chooser exploration and independent reexecution.

RSI scores repeatability of newly observed probes, not visual or full acceptance.
Private discovered source results become a separate frozen E2E book only after
inspection. No worker drives the browser or creates another continuation loop.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
import uuid

PROJECT = Path(__file__).resolve().parents[1]
BRIDGE = PROJECT / 'private/enrollment-selection-bridge'


def request_ui(out, case, side='reference'):
    BRIDGE.mkdir(parents=True, exist_ok=True)
    out.mkdir(parents=True, exist_ok=False)
    key = uuid.uuid4().hex
    request = {'id': key, 'side': side, 'out': str(out),
               'cases': [{'id': case['id'], 'method': case['method']}]}
    (BRIDGE / (key + '.request.json')).write_text(json.dumps(request, ensure_ascii=False))
    reply = BRIDGE / (key + '.reply.json')
    deadline = time.monotonic() + 900
    while time.monotonic() < deadline:
        if reply.exists():
            actual = json.loads(reply.read_text())
            if 'error' in actual:
                raise RuntimeError(actual['error'])
            return actual
        time.sleep(.2)
    raise TimeoutError('Native UI request was not serviced')


def check(case, row, baseline, expected, restored):
    return {'id': case['id'], 'chooser_observed': row['result']['selected'] is not None,
            'baseline': row['baseline'] == baseline,
            'opened_options': row['result'] == expected,
            'dismiss_restores': row['afterDismiss'] == baseline,
            'restored': restored == baseline}


def passed(row):
    return all(value is True for key, value in row.items() if key != 'id')


def worker(mode):
    request = json.load(sys.stdin)
    workspace = Path(request['workspace'])
    book = json.loads((workspace / 'cases.json').read_text())
    path = workspace / 'discoveries.json'
    discoveries = json.loads(path.read_text()) if path.exists() else {}
    if mode == 'agent':
        available = [case for case in book['cases'] if case['id'] not in discoveries] or book['cases']
        case = available[0]
        actual = request_ui(workspace / ('native-' + uuid.uuid4().hex), case)
        discoveries[case['id']] = actual['rows'][0]['result']
        path.write_text(json.dumps(discoveries, ensure_ascii=False, indent=2) + '\n')
        return {'generation': {'probe': case['id'], 'hypothesis': case['hypothesis']},
                'observation': {'actual': actual}}
    checks, actuals = [], []
    for case in book['cases']:
        if case['id'] not in discoveries:
            continue
        actual = request_ui(workspace / ('native-' + uuid.uuid4().hex), case)
        checks.append(check(case, actual['rows'][0], book['baseline'], discoveries[case['id']], actual['restored']))
        actuals.append(actual)
    return {'score': sum(passed(row) for row in checks) / len(book['cases']),
            'observation': {'checks': checks, 'actual': actuals,
                            'scope': 'independent live reexecution of discovered readonly probes'}}


def main():
    if sys.argv[1] in ('agent', 'evaluator'):
        print(json.dumps(worker(sys.argv[1]), ensure_ascii=False))
        return 0
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['replay', 'compare'])
    parser.add_argument('--book', type=Path, required=True)
    parser.add_argument('--side', choices=['reference', 'candidate'])
    parser.add_argument('--observed', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    book = json.loads(args.book.read_text())
    identity = hashlib.sha256(args.book.read_bytes()).hexdigest()
    args.out.mkdir(parents=True, exist_ok=False)
    if args.operation == 'replay':
        if not args.side:
            raise ValueError('--side required')
        rows, restored = [], None
        try:
            for case in book['cases']:
                actual = request_ui(args.out / case['id'], case, args.side)
                rows.extend(actual['rows'])
                restored = actual['restored']
            result = {'side': args.side, 'contract_digest': identity, 'rows': rows, 'restored': restored}
        except Exception as error:
            (args.out / 'unavailable.json').write_text(json.dumps({'status': 'unavailable', 'reason': str(error)}))
            raise
        (args.out / 'observed.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
        print(json.dumps({'status': 'recorded', 'side': args.side}))
        return 0
    actual = json.loads(args.observed.read_text())
    if actual['contract_digest'] != identity:
        raise ValueError('Frozen source book changed')
    rows = {row['id']: row for row in actual['rows']}
    checks = [check(case, rows[case['id']], book['baseline'], case['expectedResult'], actual['restored']) for case in book['cases']]
    result = {'status': 'pass' if all(passed(row) for row in checks) else 'fail',
              'side': actual['side'], 'checks': checks,
              'completion': 'not evaluated; chooser probes do not establish full product fidelity'}
    (args.out / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result['status'] == 'pass' else 1


if __name__ == '__main__':
    raise SystemExit(main())
