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
    'quick-config': 'quick-config',
    'quick-search': 'quick-search-pasted-full',
    'overview-config': 'overview-config',
    'add-card': 'add-card',
    'recent-added': 'recent-card',
    'recent-add-options': 'recent-card-draft',
    'chart-schedule': 'chart-schedule',
    'chart-attendance': 'chart-attendance',
    'background-options': 'background-options',
}
LINE = re.compile(r'^\s*\d+ (text|button|toggle button|checkbox|link|heading)(?: \(([^)]*)\))? (.*)$')


def observe(directory):
    result = {'states': {}}
    for state, filename in STATES.items():
        path = directory / (filename + '.ax.txt')
        if not path.exists():
            continue
        text, elements = [], {}
        # A recorded AX diff can establish added dialog nodes, while omitted
        # surrounding state remains unknown; do not synthesize the old tree.
        captured_lines = [re.sub(r'^[+~](?=\s)', '', line) for line in path.read_text().splitlines()]
        for line in captured_lines:
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
        if state.startswith('quick-'):
            lines = captured_lines
            start = next((i for i, line in enumerate(lines) if re.search(r'\d+ heading 已选功能', line)), None)
            end = next((i for i, line in enumerate(lines) if re.search(r'\d+ heading 全部功能', line)), None)
            if start is not None and end is not None:
                selected, previous_text = [], None
                for line in lines[start:end]:
                    leaf = re.match(r'^\s*\d+ text (.*)$', line)
                    if leaf:
                        previous_text = leaf[1].strip()
                    if re.match(r'^\s*\d+ button 移除', line) and previous_text is not None:
                        selected.append(previous_text)
                elements['selected-shortcuts'] = {'value': json.dumps(selected, ensure_ascii=False)}
            if end is not None:
                footer = next((i for i in range(end, len(lines)) if re.search(r'\d+ text 菜单范围', lines[i])), len(lines))
                fields = [line for line in lines[end:footer] if re.search(r'\d+ text field', line)]
                if fields:
                    value = re.search(r'Value: ([^,\n]+)', fields[0])
                    elements['shortcut-search'] = {'role': 'textbox', 'value': value[1] if value else ''}
                catalog = [re.sub(r'^\s*\d+ button (?:\(disabled\) )?', '', line).split(', Value:')[0].strip() for line in lines[end:footer] if re.match(r'^\s*\d+ button ', line)]
                elements['shortcut-catalog'] = {'value': json.dumps(catalog, ensure_ascii=False)}
        if state == 'recent-add-options':
            available, previous_text = [], []
            for line in captured_lines:
                leaf = re.match(r'^\s*\d+ text (.*)$', line)
                if leaf:
                    previous_text.append(leaf[1].strip())
                if re.match(r'^\s*\d+ button 添加$', line):
                    available.append(previous_text[-2:])
            elements['add-card-options'] = {'value': json.dumps(available, ensure_ascii=False)}
        if state.startswith('chart-'):
            caption = next((re.sub(r'^\s*\d+ link ', '', line).split(', Value:')[0].strip() for line in captured_lines if re.match(r'^\s*\d+ link \d+ / \d+ 近7日', line)), None)
            if caption is None:
                start = next((i for i, line in enumerate(captured_lines) if re.search(r'\d+ text 近7日数据$', line)), len(captured_lines))
                end = next((i for i in range(start + 1, len(captured_lines)) if re.search(r'\d+ image .*近7日趋势$', captured_lines[i])), len(captured_lines))
                leaves = [re.sub(r'^\s*\d+ text ', '', line).strip() for line in captured_lines[start + 1:end] if re.match(r'^\s*\d+ text ', line)]
                if leaves:
                    caption = ' '.join(leaves)
            if caption is not None:
                elements['chart-summary'] = {'value': re.sub(r'\s+', ' ', caption).strip()}
        result['states'][state] = {'accessible_text': text, 'elements': elements, 'evidence': str(path)}
        modal_capture = directory / (filename + '.png')
        if state in ('quick-config', 'overview-config', 'background-options') and modal_capture.exists():
            import hashlib
            review_path = directory / (filename + '.review.json')
            review = json.loads(review_path.read_text()) if review_path.exists() else {}
            reviewed = review.get('sha256') == hashlib.sha256(modal_capture.read_bytes()).hexdigest() and review.get('same_state') is True and review.get('unobscured') is True
            with Image.open(modal_capture) as image:
                result['states'][state]['capture_pixels'] = list(image.size)
            result['states'][state]['capture'] = {'path': str(modal_capture), 'content_rect_points': [4, 80, 1462, 749], 'backing_scale': 2, 'window_points': [1470, 833], 'state_consistent': reviewed}
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
