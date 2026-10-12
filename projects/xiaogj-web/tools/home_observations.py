"""Convert saved native AX facts into the shared frontend comparator format.

This adapter does not drive the UI or infer pass flags. Both runs must execute
home-scenarios.json through CUA and save full snapshots before conversion.
"""
import argparse
import json
import re
from pathlib import Path
from PIL import Image

STATES = {
    'home': 'baseline-final',
    'todos-expanded': 'todos-expanded-full',
    'todo-config': 'todo-config-full',
    'todo-draft': 'todo-draft-full',
    'cancelled': 'cancelled-full',
}
LINE = re.compile(r'^\s*\d+ (text|button|checkbox|link|heading)(?: \(([^)]*)\))? (.*)$')


def observe(directory):
    result = {'states': {}}
    for state, filename in STATES.items():
        path = directory / (filename + '.ax.txt')
        if not path.exists():
            continue
        text, elements = [], {}
        for line in path.read_text().splitlines():
            match = LINE.match(line)
            if not match:
                continue
            role, attributes, content = match.groups()
            name = re.split(r', (?:Value|Help): ', content)[0]
            text.append(name)
            element = {'role': role, 'enabled': 'disabled' not in (attributes or '')}
            if role == 'checkbox':
                value = re.search(r', Value: ([01])(?:$|,)', content)
                if value:
                    element['checked'] = value[1] == '1'
                elements['checkbox:' + name] = element
            if role in ('button', 'link'):
                for prefix, key in [('待我审批 ', 'todo-approval'), ('近30天待补课 ', 'todo-makeup'), ('近7天生日学员 ', 'todo-birthday')]:
                    if name.startswith(prefix):
                        elements[key] = element
        result['states'][state] = {'accessible_text': text, 'elements': elements, 'evidence': str(path)}
    capture = directory / 'baseline-final.png'
    if capture.exists() and 'home' in result['states']:
        with Image.open(capture) as image:
            result['states']['home']['capture_pixels'] = list(image.size)
        # Geometry measured from the native 2x capture and original viewport.
        # A different window/scale is rejected by the image comparator.
        result['states']['home']['capture'] = {
            'path': str(capture), 'content_rect_points': [4, 80, 1462, 749],
            'backing_scale': 2, 'window_points': [1470, 833],
        }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--captures', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    with args.out.open('x') as stream:
        json.dump(observe(args.captures), stream, ensure_ascii=False, indent=2)
        stream.write('\n')


if __name__ == '__main__':
    main()
