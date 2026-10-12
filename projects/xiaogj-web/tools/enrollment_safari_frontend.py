"""Extract facts from the reviewed Safari blank enrollment pair, without driving UI."""
import argparse
import json
from pathlib import Path
import re
from PIL import Image
from capabilities.rebuild.contracts import local_file


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', default='.')
    parser.add_argument('--capture', required=True, help='AX and PNG common prefix')
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    root = Path(args.workspace).resolve()
    ax_path = local_file(root, args.capture + '.ax.txt')
    image_path = local_file(root, args.capture + '.png')
    ax = ax_path.read_text()
    texts = []
    for line in ax.splitlines():
        match = re.match(r'^\s*\d+ (?:text|link|button|cell)(?: \([^)]*\))? (.*)$', line)
        if match:
            texts.append(re.split(r', (?:Value|Help): ', match[1])[0])
    with Image.open(image_path) as image:
        pixels = list(image.size)
    if pixels not in ([2648, 1666], [1324, 833]):
        raise ValueError('This reviewed Safari geometry requires a new capture protocol for other sizes')
    scale = pixels[0] / 1324
    facts = {'states': {'enrollment-safari-blank': {
        'accessible_text': texts, 'capture_pixels': pixels,
        'capture': {'path': image_path.relative_to(root).as_posix(),
                    'content_rect_points': [0, 90, 1324, 743],
                    'backing_scale': scale, 'window_points': [1324, 833]},
        'evidence': ax_path.relative_to(root).as_posix()}}}
    with local_file(root, args.out, must_exist=False).open('x') as stream:
        json.dump(facts, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


if __name__ == '__main__':
    main()
