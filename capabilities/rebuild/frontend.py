"""Compare observed frontend requirements, independently of semantic E2E.

Drivers collect facts; they do not supply pass flags. This initial comparator
checks accessible copy and capture compatibility. It does not certify visual or
audio equivalence from text checks.
"""
import argparse
import json
from pathlib import Path

from capabilities.exploration.storage import digest
from capabilities.rebuild.contracts import local_file


def compare(root, contract, observed):
    root = Path(root).resolve()
    rows = []
    for requirement in contract['requirements']:
        row = {'id': requirement['id'], 'state': requirement['state']}
        evidence = requirement.get('evidence', [])
        if not evidence:
            raise ValueError('reference evidence required')
        for name in evidence:
            local_file(root, name)
        state = observed.get('states', {}).get(requirement['state'])
        if requirement['kind'] == 'pending':
            row.update(status='not_run', reason=requirement['description'])
        elif state is None:
            row.update(status='not_run', reason='Driver has not visited this reference state')
        elif requirement['kind'] == 'accessible_text':
            expected = requirement['text']
            actual = state.get('accessible_text')
            if not isinstance(actual, list):
                row.update(status='unavailable', reason='Driver did not collect accessible text')
            else:
                found = expected.casefold() in {str(text).strip().casefold() for text in actual}
                row.update(status='pass' if found else 'fail', expected=expected)
        elif requirement['kind'] == 'capture_dimensions':
            expected = requirement['pixels']
            actual = state.get('capture_pixels')
            row.update(status='unavailable' if actual is None else 'pass' if actual == expected else 'fail',
                       expected=expected, actual=actual,
                       reason='Comparable capture dimensions only; does not prove visual equivalence')
        else:
            raise ValueError('Unsupported frontend requirement: ' + requirement['kind'])
        rows.append(row)
    if not rows or len({row['id'] for row in rows}) != len(rows):
        raise ValueError('Nonempty unique frontend requirements required')
    return {'kind': 'frontend_requirements', 'contract_digest': digest(contract),
            'observation_digest': digest(observed), 'rows': rows,
            'status': 'pass' if all(row['status'] == 'pass' for row in rows) else 'fail'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', default='.')
    parser.add_argument('--contract', required=True)
    parser.add_argument('--observed', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    root = Path(args.workspace).resolve()
    contract = json.loads(local_file(root, args.contract).read_text())
    observed = json.loads(local_file(root, args.observed).read_text())
    result = compare(root, contract, observed)
    output = root / args.out
    with output.open('x') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'status': result['status'], 'counts': {
        status: sum(row['status'] == status for row in result['rows'])
        for status in ['pass', 'fail', 'not_run', 'unavailable']}}, ensure_ascii=False))
    return 0 if result['status'] == 'pass' else 1


if __name__ == '__main__':
    raise SystemExit(main())
