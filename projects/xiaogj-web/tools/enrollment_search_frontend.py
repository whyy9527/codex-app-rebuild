"""Read the paired native chooser search captures; no UI driving or verdicts."""
import argparse
import json
from pathlib import Path
from PIL import Image
from capabilities.rebuild.contracts import local_file


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture-root', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    root = Path.cwd().resolve()
    states = {}
    for kind in ('courses', 'items'):
        prefix = args.capture_root + '/' + kind + '-no-match/' + kind + '-no-match-searched'
        image_path = local_file(root, prefix + '.png')
        ax_path = local_file(root, prefix + '.ax.txt')
        ax = ax_path.read_text()
        title = '选择课程' if kind == 'courses' else '选择物品'
        if 'heading ' + title not in ax:
            raise ValueError('Expected actual chooser heading')
        with Image.open(image_path) as image:
            pixels = list(image.size)
        if pixels not in ([1324, 833], [2648, 1666]):
            raise ValueError('Unreviewed native capture geometry')
        states['enrollment-search-' + kind] = {
            'capture_pixels': pixels,
            'capture': {'path': image_path.relative_to(root).as_posix(),
                        'content_rect_points': [0, 90, 1324, 743],
                        'backing_scale': pixels[0] / 1324,
                        'window_points': [1324, 833]},
            'evidence': ax_path.relative_to(root).as_posix()}
    with local_file(root, args.out, must_exist=False).open('x') as stream:
        json.dump({'states': states}, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


if __name__ == '__main__':
    main()
