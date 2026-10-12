"""Compare actual captured homepage period content against fixed original captures."""
import argparse
import hashlib
import json
from pathlib import Path
import re


def facts(path, section):
    lines = Path(path).read_text().splitlines()
    first, last = ('数据概览', '近7日数据') if section == 'metrics' else ('学员动态', '人数概况')
    start = next(i for i, line in enumerate(lines) if re.search(r'\d+ text ' + first + r'$', line))
    end = next(i for i in range(start + 1, len(lines)) if re.search(r'\d+ text ' + last + r'$', lines[i]))
    body = lines[start + 1:end]
    if section == 'metrics':
        content = [re.sub(r'^\s*\d+ link ', '', line).split(', Value:')[0].strip() for line in body if re.match(r'^\s*\d+ link ', line)]
        if not content:
            raise ValueError('Metric content missing')
        return [re.sub(r'\s+', ' ', caption).strip() for caption in content]
    content = [re.sub(r'^\s*\d+ button ', '', line).split(', Value:')[0].strip() for line in body if re.match(r'^\s*\d+ button \d', line)]
    if not content:
        raise ValueError('Student counts missing')
    return content


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference', type=Path, required=True)
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument('--captures', type=Path)
    inputs.add_argument('--receipt', type=Path, help='Actual shared-driver actions.json; captures are adjacent')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    capture_root = args.captures
    if args.receipt:
        receipt = json.loads(args.receipt.read_text())
        if receipt.get('side') != 'candidate':
            raise ValueError('Expected candidate action receipt')
        capture_root = args.receipt.parent
    rows = []
    scenarios = json.loads((Path(__file__).resolve().parents[1] / 'home-periods-scenarios.json').read_text())
    for case in scenarios['cases']:
        name, source, section = case['id'], case['reference'], case['kind']
        reference, observed = args.reference / source, capture_root / (name + '.ax.txt')
        row = {'id': name, 'reference': str(reference), 'observed': str(observed)}
        if hashlib.sha256(reference.read_bytes()).hexdigest() != case['reference_sha256']:
            row.update(status='unavailable', reason='Frozen original capture changed; requires a sourced contract revision')
        elif not observed.exists():
            row.update(status='not_run', reason='Candidate state not captured')
        else:
            try:
                expected, actual = facts(reference, section), facts(observed, section)
                row.update(status='pass' if expected == actual else 'fail', expected=expected, actual=actual,
                           reference_sha256=hashlib.sha256(reference.read_bytes()).hexdigest(),
                           observed_sha256=hashlib.sha256(observed.read_bytes()).hexdigest())
            except (ValueError, StopIteration) as error:
                row.update(status='unavailable', reason='Actual section facts missing: ' + type(error).__name__)
        rows.append(row)
        rows.append({'id': name + '.frontend', 'status': 'not_run', 'reason': 'This run has no paired reviewed period screenshots; content pass cannot certify frontend parity.'})
    result = {'rows': rows, 'status': 'pass' if all(r['status'] == 'pass' for r in rows) else 'fail',
              'scope': 'Observed period content only; navigation, other inputs, live data refresh and persistence remain unverified.'}
    with args.out.open('x') as output:
        json.dump(result, output, ensure_ascii=False, indent=2)
        output.write('\n')
    print(json.dumps({'status': result['status'], 'counts': {s: sum(r['status'] == s for r in rows) for s in ['pass', 'fail', 'not_run', 'unavailable']}}))
    return 0 if result['status'] == 'pass' else 1


if __name__ == '__main__':
    raise SystemExit(main())
