"""Freeze source-observed replay text and controls without publishing source prose."""
import argparse
import hashlib
import json
from pathlib import Path
import re

WORKSPACE = Path(__file__).resolve().parents[3]


def scoped_player_text(ax):
    lines = ax.splitlines()
    start = next(i for i, line in enumerate(lines) if 'container AI 模拟回放播放器' in line)
    indent = len(lines[start]) - len(lines[start].lstrip())
    text = []
    for line in lines[start + 1:]:
        if len(line) - len(line.lstrip()) <= indent:
            break
        match = re.match(r'^\s*\d+ (?:heading|text|button|link) (.*?)(?:, Value:|, Help:|$)', line)
        if match:
            text.append(match[1].strip())
    return list(dict.fromkeys(text))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--reference', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    reference = (WORKSPACE / args.reference).resolve()
    output = (WORKSPACE / args.out).resolve()
    if not reference.is_relative_to(WORKSPACE) or not output.is_relative_to(WORKSPACE):
        parser.error('Reference and output must be in the worktree')
    if 'private' not in output.relative_to(WORKSPACE).parts:
        parser.error('Expanded source-text contracts belong in ignored private evidence')
    raw = reference.read_bytes()
    observed = json.loads(raw)
    requirements = []
    for name, state in observed['states'].items():
        ax_path = state['ax']
        ax_file = (WORKSPACE / ax_path).resolve()
        if not ax_file.is_relative_to(WORKSPACE):
            raise ValueError('Source AX evidence outside worktree')
        if name.startswith('player-'):
            texts = scoped_player_text(ax_file.read_text())
        elif name.startswith('host-'):
            texts = ['展开详情', '进入作者空间', '添加到桌面'] if name == 'host-collapsed' else ['S16AI预测大赛', '相关内容', 'UP更多Toy', '热门Toy']
        else:
            raise ValueError('This source protocol does not own state ' + name)
        for i, text in enumerate(texts):
            requirements.append({'id': f'{name}.text.{i}', 'state': name, 'kind': 'accessible_text',
                                 'text': text, 'evidence': [ax_path]})
        if name.startswith('player-'):
            for key, value in state['elements'].items():
                if 'checked' in value:
                    requirements.append({'id': name + '.checked.' + key, 'state': name,
                        'kind': 'element_boolean', 'element': key, 'field': 'checked',
                        'expected': value['checked'], 'evidence': [ax_path]})
                if 'value' in value:
                    requirements.append({'id': name + '.value.' + key, 'state': name,
                        'kind': 'element_value', 'element': key, 'value': value['value'], 'evidence': [ax_path]})
        capture = state['capture']
        requirements.append({'id': name + '.pixels', 'state': name, 'kind': 'image_pixels',
            'reference_image': state['image'], 'pixels': capture['content_rect_points'][2:],
            'reference_capture': {k: capture[k] for k in ('content_rect_points', 'backing_scale', 'window_points')},
            'evidence': [state['image']]})
    contract = {'schema_version': 1, 'source_observation_sha256': hashlib.sha256(raw).hexdigest(),
        'scope': 'Source replay text/control facts and strict measured images. Limited to visited states; live clocks, platform counts, media and unvisited journeys remain separate.',
        'requirements': requirements}
    with output.open('x') as stream:
        json.dump(contract, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'contract': str(output.relative_to(WORKSPACE)), 'requirements': len(requirements)}))


if __name__ == '__main__':
    main()
