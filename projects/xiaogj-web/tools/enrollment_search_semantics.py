"""Inspect retained native AX facts against the observed search contract.

This complements, and never replaces, raw AX and strict screenshot comparison.
Missing AX text is unavailable; screenshot review remains a separate requirement.
"""
import argparse
import json
from pathlib import Path
import re


def observe(text, kind):
    heading = '选择课程' if kind == 'courses' else '选择物品'
    start = re.search(r'\d+ heading ' + heading + r',', text)
    if not start:
        raise ValueError('Actual chooser heading missing')
    dialog = text[start.start():].split(' image WindowControlShadowView', 1)[0]
    count = re.search(r'共\s*(\d+)\s*条', dialog)
    pages = re.search(r'第\s*(\d+)\s*/\s*(\d+)\s*页', dialog)
    prompt = '请输入课程名称' if kind == 'courses' else '物品名称/编码'
    field = next((line for line in dialog.splitlines() if 'text field (settable)' in line and prompt in line), '')
    value = re.search(r'Value: ([^,\n]*)', field)
    # Preserve cell Values that the historical caption-delta observer stripped.
    cells = re.findall(r'cell \(selectable\)[^\n]*Value: ([^\n]+)', dialog)
    return {'total': int(count[1]) if count else None,
            'page': int(pages[1]) if pages else None,
            'totalPages': int(pages[2]) if pages else None,
            'query': value[1] if value else None,
            'cellValues': cells,
            'rowCheckboxes': max(0, len(re.findall(r'\d+ checkbox', dialog)) - (2 if kind == 'items' else 1))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--contract', type=Path, required=True)
    parser.add_argument('--capture', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    contract = json.loads(args.contract.read_text())
    results = []
    for case in contract['cases']:
        path = args.capture / case['id'] / (case['id'] + '-searched.ax.txt')
        facts = observe(path.read_text(), case['id'].split('-')[0])
        checks = {key: 'pass' if facts[key] == case[key] else 'fail' for key in ('total', 'page', 'totalPages')}
        checks['actual_input'] = 'pass' if facts['query'] == contract['query'] else 'fail'
        checks['no_selectable_data_rows'] = 'pass' if facts['rowCheckboxes'] == 0 else 'fail'
        checks['empty_text_in_ax'] = 'pass' if case['visible_empty_message'] in facts['cellValues'] else 'unavailable'
        results.append({'id': case['id'], 'facts': facts, 'checks': checks})
    result = {'cases': results, 'completion': 'not evaluated; AX facts cannot prove screenshot fidelity or unobserved business behavior'}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x') as out:
        json.dump(result, out, ensure_ascii=False, indent=2)
        out.write('\n')
    print(json.dumps(result, ensure_ascii=False))
    return int(any(value == 'fail' for case in results for value in case['checks'].values()))


if __name__ == '__main__':
    raise SystemExit(main())
