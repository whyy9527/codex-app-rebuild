"""Read actual detail capture states; no actions and no comparison expectations."""
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
    for state, name in {'detail-overview': 'expanded-overview', 'detail-expanded': 'expanded-expanded',
                        'detail-returned': 'expanded-restored'}.items():
        ax_path = folder/(name+'.ax.txt')
        ax = ax_path.read_text()
        texts = [re.sub(r'^\s*\d+ text ', '', s) for s in ax.splitlines() if re.match(r'^\s*\d+ text ', s)]
        elements = {}
        for line in ax.splitlines():
            if re.match(r'^\s*\d+ (?:link|button) .*返回\s*$', line):
                elements['return'] = {'role': 'link' if ' link ' in line else 'button'}
        body = ' '.join(texts)
        image_path = folder/(name+'.png')
        with Image.open(image_path) as image:
            pixels = list(image.size)
        states[state] = {'accessible_text': texts, 'elements': elements,
                         'interactions': {'expanded-fields-visible': '基本信息' in body and '联系信息' in body},
                         'evidence': ax_path.relative_to(root).as_posix(), 'capture_pixels': pixels,
                         'capture': {'path': image_path.relative_to(root).as_posix(),
                                     'content_rect_points': [4, 80, 1462, 749], 'backing_scale': 2,
                                     'window_points': [1470, 833]}}
    with local_file(root, args.out, must_exist=False).open('x') as output:
        json.dump({'states': states}, output, ensure_ascii=False, indent=2)
        output.write('\n')


if __name__ == '__main__':
    main()
