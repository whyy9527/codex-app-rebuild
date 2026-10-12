"""Finite detail RSI workers and shared E2E comparison, backed by actual native UI receipts."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
import uuid

PROJECT = Path(__file__).resolve().parents[1]
BOOK = PROJECT / 'private/rsi-detail-seed/cases.json'
SCENARIOS = PROJECT / 'student-detail-scenarios-v3.json'
BRIDGE = PROJECT / 'private/detail-bridge'


def request_ui(out, cases, role, side='reference'):
    BRIDGE.mkdir(parents=True, exist_ok=True)
    out.mkdir(parents=True, exist_ok=True)
    key = uuid.uuid4().hex
    request = {'id': key, 'out': str(out), 'role': role, 'side': side,
               'cases': [{'id': c['id'], 'actions': c['actions'], 'entry': c['entry']} for c in cases]}
    (BRIDGE/f'{key}.request.json').write_text(json.dumps(request))
    deadline = time.monotonic()+240
    reply = BRIDGE/f'{key}.reply.json'
    while time.monotonic() < deadline:
        if reply.exists():
            actual = json.loads(reply.read_text())
            if 'error' in actual:
                raise RuntimeError(actual['error'])
            return actual
        time.sleep(.2)
    raise TimeoutError('Native detail request was not serviced')


def checks(book, actual, selected):
    observed = {row['id']: row for row in actual['rows']}
    rows = []
    for case in selected:
        row = observed[case['id']]
        tokens = row['states'][-1]['text']
        matches = all(value in tokens for value in case['expectedText'])
        passed = matches and row['baseline'] == book['baseline'] and row['restored'] == book['baseline']
        rows.append({'id': case['id'], 'status': 'pass' if passed else 'fail',
                     'missing_text': [value for value in case['expectedText'] if value not in tokens]})
    return rows


def worker(mode):
    request = json.load(sys.stdin)
    workspace = Path(request['workspace'])
    book = json.loads((workspace/'cases.json').read_text())
    path = workspace/'probes.json'
    plan = json.loads(path.read_text()) if path.exists() else []
    if mode == 'agent':
        available = [c for c in book['cases'] if c['id'] not in plan] or book['cases']
        case = available[0]
        actual = request_ui(workspace/('native-'+uuid.uuid4().hex), [case], 'discover')
        if case['id'] not in plan:
            plan.append(case['id'])
        path.write_text(json.dumps(plan))
        return {'generation': {'probe': case['id'], 'preparation': 'empty query, observed student name, readonly detail and Return'},
                'observation': {'actual': actual}}
    selected = [c for c in book['cases'] if c['id'] in plan]
    actual = request_ui(workspace/('native-'+uuid.uuid4().hex), selected, 'evaluate')
    rows = checks(book, actual, selected)
    restored = actual['restored'] == book['baseline']
    return {'score': sum(r['status'] == 'pass' for r in rows)/len(book['cases']) if restored else 0,
            'observation': {'checks': rows, 'restored': restored, 'actual': actual}}


def main():
    if sys.argv[1] in ('agent', 'evaluator'):
        print(json.dumps(worker(sys.argv[1]), ensure_ascii=False))
        return 0
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['replay', 'compare'])
    parser.add_argument('--side', choices=['reference', 'candidate'])
    parser.add_argument('--observed')
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    book = json.loads(BOOK.read_text())
    digest = hashlib.sha256(BOOK.read_bytes()+SCENARIOS.read_bytes()).hexdigest()
    try:
        if args.mode == 'replay':
            if not args.side:
                raise ValueError('--side required')
            actual = request_ui(out, book['cases'], 'e2e', args.side)
            result = {'side': args.side, 'contract_digest': digest, **actual}
            (out/'observed.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
            print(json.dumps({'status': 'recorded', 'side': args.side}))
            return 0
        actual = json.loads(Path(args.observed).read_text())
        if actual['contract_digest'] != digest:
            raise ValueError('Detail contract digest differs')
        rows = checks(book, actual, book['cases'])
        rows.append({'id': 'restored', 'status': 'pass' if actual['restored'] == book['baseline'] else 'fail'})
        result = {'status': 'pass' if all(r['status'] == 'pass' for r in rows) else 'fail',
                  'side': actual['side'], 'contract_digest': digest, 'rows': rows,
                  'completion': 'not evaluated; detail is one observed journey'}
        (out/'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
        print(json.dumps(result, ensure_ascii=False))
        return 0 if result['status'] == 'pass' else 1
    except Exception as error:
        (out/'unavailable.json').write_text(json.dumps({'status': 'unavailable', 'reason': str(error)}))
        print(str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
