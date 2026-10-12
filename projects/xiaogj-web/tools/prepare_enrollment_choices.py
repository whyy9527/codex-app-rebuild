"""Extract the actually captured first chooser table; no generated catalog rows."""
import argparse
import json
from pathlib import Path
import re
from datetime import datetime, timezone
from capabilities.rebuild.contracts import local_file


def extract(path):
    ax = path.read_text()
    title_match = re.search(r'\d+ heading (选择课程|选择物品)', ax)
    if not title_match:
        raise ValueError('No observed chooser heading')
    scope = ax[title_match.start():]
    table = scope[scope.index(' table\n'):]
    total = re.search(r'共\s*(\d+)\s*条 每页', table)
    pagination = re.search(r'条 第\s*(\d+)\s*/\s*(\d+)\s*页', table)
    if not total or not pagination:
        raise ValueError('Missing actual pagination')
    blocks = re.split(r'\n\s*\d+ row \(selectable\)', table)[1:]
    headers = re.sub(r'^\s*\d+ checkbox.*', '', blocks[0], flags=re.M).strip()
    headers = [text.strip() for text in re.sub(r'[\ue000-\uf8ff]', '', headers).splitlines() if text.strip()]
    rows = []
    for block in blocks[1:]:
        if not re.search(r'\d+ checkbox', block):
            break
        cells, current = [], None
        for line in block.splitlines():
            cell = re.match(r'^\s*\d+ cell \(selectable\)(.*)$', line)
            if cell:
                current = [cell[1].strip()]
                cells.append(current)
            elif re.match(r'^\s*\d+ [a-z]', line):
                current = None
            elif current is not None:
                current.append(line.strip())
        cells = [''.join(parts) for parts in cells]
        if len(cells) != len(headers) + 1:
            raise ValueError('Captured table shape differs from actual headers')
        rows.append(cells[1:])
    if not rows:
        raise ValueError('No actual rows')
    return {'title': title_match[1], 'headers': headers, 'rows': rows,
            'total': int(total[1]), 'page': int(pagination[1]), 'totalPages': int(pagination[2]),
            'pageSize': len(rows), 'observedAt': datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
            'provenance': path.as_posix()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--courses', required=True)
    parser.add_argument('--items', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--presentation', help='Reviewed screenshot annotations, keyed by catalog kind')
    args = parser.parse_args()
    root = Path.cwd().resolve()
    result = {kind: extract(local_file(root, getattr(args, kind))) for kind in ('courses', 'items')}
    for row in result.values():
        row['provenance'] = Path(row['provenance']).relative_to(root).as_posix()
    if args.presentation:
        annotations = json.loads(local_file(root, args.presentation).read_text())
        for kind, annotation in annotations.items():
            if kind not in result or len(annotation['nameBadges']) != len(result[kind]['rows']):
                raise ValueError('Presentation annotation differs from observed rows')
            if not all(value is None or isinstance(value, str) for value in annotation['nameBadges']):
                raise ValueError('Invalid observed name badge')
            local_file(root, annotation['evidence'])
            result[kind]['presentation'] = annotation
    with local_file(root, args.out, must_exist=False).open('x') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


if __name__ == '__main__':
    main()
