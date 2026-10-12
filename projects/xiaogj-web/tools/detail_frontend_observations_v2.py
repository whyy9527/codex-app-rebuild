"""Read actual detail capture states; no actions and no comparison expectations."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from PIL import Image
from capabilities.rebuild.contracts import local_file


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--captures', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--review', required=True, help='Actual visual review bound to screenshot hashes; AX stability alone is insufficient')
    args = parser.parse_args()
    root = Path.cwd().resolve()
    folder = local_file(root, args.captures, must_exist=False)
    review_path = local_file(root, args.review)
    reviews = json.loads(review_path.read_text())['states']
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
        review = reviews.get(state, {})
        reviewed = (review.get('sha256') == hashlib.sha256(image_path.read_bytes()).hexdigest()
                    and review.get('unobscured') is True and review.get('same_state') is True)
        with Image.open(image_path) as image:
            pixels = list(image.size)
        states[state] = {'accessible_text': texts, 'elements': elements,
                         'interactions': {'expanded-fields-visible': '基本信息' in body and '联系信息' in body},
                         'evidence': ax_path.relative_to(root).as_posix(), 'capture_pixels': pixels,
                         'capture': {'path': image_path.relative_to(root).as_posix(),
                                     'content_rect_points': [4, 80, 1462, 749], 'backing_scale': 2,
                                     'window_points': [1470, 833], 'state_consistent': reviewed},
                         'capture_review': {'path': review_path.relative_to(root).as_posix(), 'current': reviewed}}
    with local_file(root, args.out, must_exist=False).open('x') as output:
        json.dump({'states': states}, output, ensure_ascii=False, indent=2)
        output.write('\n')


if __name__ == '__main__':
    main()
