"""Read actual recent-class card facts and compare both sides without inventing data."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re


def facts(path):
    lines = [re.sub(r'^[+~](?=\s)', '', line) for line in Path(path).read_text().splitlines()]
    start = next(i for i, line in enumerate(lines) if re.search(r'\d+ text 最近30天开班$', line))
    end = next((i for i in range(start + 1, len(lines)) if re.search(r'\d+ text 拖动排序$', lines[i])), len(lines))
    body = lines[start + 1:end]
    texts = [re.sub(r'^\s*\d+ text ', '', line).strip() for line in body if re.match(r'^\s*\d+ text (?!field)', line)]
    headers, cells = [], []
    for i, line in enumerate(body):
        if not re.match(r'^\s*\d+ (?:column header|cell)(?:\s|$)', line):
            continue
        indent = len(line) - len(line.lstrip())
        value = None
        for child in body[i + 1:]:
            if len(child) - len(child.lstrip()) <= indent:
                break
            match = re.match(r'^\s*\d+ text (.*)$', child)
            if match:
                value = match[1].strip()
                break
        (headers if ' column header' in line else cells).append(value if value is not None else '')
    if not headers or len(cells) % len(headers):
        raise ValueError('Recent card table facts are incomplete')
    return {'summary': texts[0], 'headers': headers,
            'rows': [cells[i:i + len(headers)] for i in range(0, len(cells), len(headers))]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    snapshot = sub.add_parser('snapshot')
    snapshot.add_argument('--source', type=Path, required=True)
    snapshot.add_argument('--out', type=Path, required=True)
    compare = sub.add_parser('compare')
    compare.add_argument('--reference', type=Path, required=True)
    compare.add_argument('--observed', type=Path, required=True)
    compare.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'snapshot':
        data = facts(args.source)
        data['observedAt'] = datetime.fromtimestamp(args.source.stat().st_mtime, timezone.utc).isoformat().replace('+00:00', 'Z')
        with args.out.open('x') as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
        return 0
    expected, actual = facts(args.reference), facts(args.observed)
    rows = [{'id': key, 'status': 'pass' if actual[key] == value else 'fail', 'expected': value, 'actual': actual[key]} for key, value in expected.items()]
    result = {'status': 'pass' if all(row['status'] == 'pass' for row in rows) else 'fail',
              'reference_sha256': hashlib.sha256(args.reference.read_bytes()).hexdigest(),
              'observed_sha256': hashlib.sha256(args.observed.read_bytes()).hexdigest(), 'rows': rows,
              'scope': 'Actual observed card content only; does not certify layout, navigation, saving, permissions or persistence.'}
    with args.out.open('x') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'status': result['status'], 'counts': {status: sum(r['status'] == status for r in rows) for status in ['pass', 'fail']}}))
    return 0 if result['status'] == 'pass' else 1


if __name__ == '__main__':
    raise SystemExit(main())
