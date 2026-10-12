"""Read a captured blank enrollment page, independently of expected requirements."""
import argparse
import hashlib
import json
from pathlib import Path
import re

from PIL import Image
from capabilities.rebuild.contracts import local_file


def normalize_text(text):
    return re.sub(r'\s*[：:]\s*$', '', re.sub('[\ue000-\uf8ff]', '', text).strip()).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ax', required=True)
    parser.add_argument('--image', required=True)
    parser.add_argument('--review', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    root = Path.cwd().resolve()
    ax_path = local_file(root, args.ax)
    image_path = local_file(root, args.image)
    ax = ax_path.read_text()
    # Scope to the actual page, excluding shared navigation and hidden widgets.
    lines = ax.splitlines()
    start = next(i for i, line in enumerate(lines) if re.search(r'\d+ text 当前位置.*新学员报名', line))
    end = next(i for i in range(start, len(lines)) if re.search(r'\d+ (?:link|button) 报名\s*$', lines[i]))
    body = lines[start:end + 2]
    texts, elements = [], {}
    for line in body:
        match = re.match(r'^\s*\d+ text (?!field)(.*)$', line)
        if match:
            texts.append(normalize_text(match[1]))
        match = re.search(r'\d+ (radio button|checkbox) (.*), Value: ([01])$', line)
        if match:
            elements[match[2]] = {'role': 'radio' if match[1] == 'radio button' else 'checkbox', 'value': match[3]}
    for i, line in enumerate(body):
        match = re.match(r'^\s*\d+ text (?!field)(.*)$', line)
        if not match:
            continue
        label = normalize_text(match[1])
        if label not in {'姓名', '手机号', '师生信账号', '身份证号', '交费日期', '业绩归属日'}:
            continue
        field = next((line for line in body[i + 1:i + 12] if re.search(r'\d+ text field', line)), None)
        if field:
            value = re.search(r'Value: ([^,\n]+)', field)
            trailing = re.search(r'text field \(settable\) (\d{4}-\d{2}-\d{2})$', field)
            elements[label] = {'role': 'textbox', 'value': value[1] if value else trailing[1] if trailing else ''}
    review = json.loads(local_file(root, args.review).read_text())
    reviewed = (review.get('sha256') == hashlib.sha256(image_path.read_bytes()).hexdigest()
                and review.get('unobscured') is True and review.get('same_state') is True)
    with Image.open(image_path) as image:
        pixels = list(image.size)
    state = {'accessible_text': texts, 'elements': elements, 'capture_pixels': pixels,
             'evidence': ax_path.relative_to(root).as_posix(),
             'capture': {'path': image_path.relative_to(root).as_posix(),
                         'content_rect_points': [4, 80, 1462, 749], 'backing_scale': 2,
                         'window_points': [1470, 833], 'state_consistent': reviewed}}
    with local_file(root, args.out, must_exist=False).open('x') as output:
        json.dump({'states': {'enrollment-blank': state}}, output, ensure_ascii=False, indent=2)
        output.write('\n')


if __name__ == '__main__':
    main()
