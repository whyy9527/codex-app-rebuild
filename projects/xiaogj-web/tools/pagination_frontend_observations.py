"""Read pagination AX input values and actual screenshots, without driving UI."""
import argparse
import json
from pathlib import Path
import re
from PIL import Image
from capabilities.rebuild.contracts import local_file


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--captures', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    root = Path.cwd().resolve()
    folder = local_file(root, args.captures, must_exist=False)
    states = {}
    for state, name in {'second-page': 'next-previous-step-0', 'last-page': 'last-first-step-0',
                        'returned-page': 'last-first-step-1', 'zero-page': 'zero-step-0'}.items():
        ax_path = folder/(name+'.ax.txt')
        ax = ax_path.read_text()
        line = next((s for s in ax.splitlines() if re.match(r'^\s*\d+ text field .*按回车键跳转。', s)), None)
        elements = {}
        if line is not None:
            value = re.search(r', Value: (.*?)(?:, Placeholder:|$)', line)
            elements['page-input'] = {'role': 'textbox', 'value': value[1] if value else ''}
        image_path = folder/(name+'.png')
        with Image.open(image_path) as image:
            pixels = list(image.size)
        states[state] = {'elements': elements, 'capture_pixels': pixels,
                         'evidence': ax_path.relative_to(root).as_posix(), 'capture': {
                             'path': image_path.relative_to(root).as_posix(),
                             'content_rect_points': [4, 80, 1462, 749], 'backing_scale': 2,
                             'window_points': [1470, 833]}}
    with local_file(root, args.out, must_exist=False).open('x') as output:
        json.dump({'states': states}, output, ensure_ascii=False, indent=2)
        output.write('\n')


if __name__ == '__main__':
    main()
