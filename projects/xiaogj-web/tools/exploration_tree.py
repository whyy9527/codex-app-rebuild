"""Render the ended case's recorded exploration; never run probes or change Goal."""
import argparse
from datetime import datetime
import json
from pathlib import Path
import webbrowser

from capabilities.rebuild.contracts import local_file
from capabilities.rebuild.discovery import frontier
from runtime.dream import load_pool
from workflows.rebuild.project import load_project

PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT.parents[1]
LABELS = {
    'rsi': '学员查询 · Safari', 'pagination_rsi': '学员分页',
    'query_rsi': '学员查询 · 可见状态', 'detail_rsi': '学员详情',
    'tabs_rsi': '学费／课消／积分', 'enrollment_grade_rsi': '报名 · 年级',
    'enrollment_chooser_rsi': '报名 · 课程／物品目录',
    'enrollment_search_rsi': '报名 · 查询与空结果',
    'enrollment_selection_rsi': '报名 · 勾选与清空',
    'enrollment_confirm_rsi': '报名 · 确定入表',
    'enrollment_amounts_rsi': '报名 · 数量与优惠金额',
}


def collect_data(root, inputs):
    """Validate immutable pools, then copy only visualization metadata."""
    root = Path(root).resolve()
    history = json.loads(local_file(root, inputs['exploration_history']).read_text())
    pending = frontier(root, history)
    protocols = []
    for key, path in inputs.items():
        if 'rsi' not in key or not key.endswith('_pool') or 'selected' in key:
            continue
        prefix = key.removesuffix('_pool').removesuffix('_collected')
        evaluation_path = inputs[prefix + '_evaluation']
        evaluation = json.loads(local_file(root, evaluation_path).read_text())
        pool, trees, _ = load_pool(root, path)
        worlds = []
        for entry, tree in zip(pool['worlds'], trees):
            nodes = []
            for node in tree['nodes']:
                history_item = node['generation_history'][-1] if node['generation_history'] else {}
                probe = history_item.get('probe') or history_item.get('id') if isinstance(history_item, dict) else None
                nodes.append({field: node[field] for field in ('id', 'parent', 'seq', 'score')} | {
                    'probe': probe if isinstance(probe, str) else '准备状态' if node['parent'] is None else '观察分支'})
            worlds.append({'phase': '再部署' if 'redeploy' in entry['path'] else '初始采集',
                           'source': entry['path'], 'nodes': nodes,
                           'rounds': len(tree['rounds']), 'stop': tree['stop']})
        protocols.append({'id': key, 'label': LABELS.get(prefix, prefix), 'pool': path,
                          'evaluation': evaluation_path, 'selected': evaluation['selected_version'],
                          'scores': [{field: row[field] for field in ('version', 'score', 'status')}
                                     for row in evaluation['feedback']], 'worlds': worlds})
    return {'history': history, 'protocols': protocols,
            'pending': len(pending['pending']), 'resolved': pending['resolved_actions'],
            'worlds': sum(len(p['worlds']) for p in protocols),
            'nodes': sum(len(w['nodes']) for p in protocols for w in p['worlds'])}


def render(data):
    fragment = Path(__file__).with_name('exploration-tree.html').read_text()
    payload = json.dumps(data, ensure_ascii=False, allow_nan=False).replace('</', '<\\/')
    fragment = fragment.replace('__EXPLORATION_DATA__', payload)
    # Standalone shell is original project code; no Codex widget runtime required.
    return '''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>校管家探索树</title>
<style>
:root{color-scheme:light dark;--background:#fff;--foreground:#17202b;--muted-foreground:#66717e;--popover:#fff;--popover-foreground:#17202b;--border:#c4cbd3;--viz-series-1:#2787d7;--viz-series-2:#d86d22}
@media(prefers-color-scheme:dark){:root{--background:#171b22;--foreground:#e8ecf2;--muted-foreground:#a5afbb;--popover:#252c36;--popover-foreground:#e8ecf2;--border:#536071;--viz-series-1:#70b4f3;--viz-series-2:#ffb16f}}
body{margin:20px;font:14px system-ui;background:var(--background);color:var(--foreground)}
h2{font-weight:500;margin:0 0 12px}.text-small{font-size:12px}.text-muted{color:var(--muted-foreground)}
.tabular-nums{font-variant-numeric:tabular-nums}.viz-row{display:flex;align-items:center;flex-wrap:wrap;gap:12px}
.btn{font:inherit;color:var(--foreground);background:var(--background);border:1px solid var(--border);border-radius:6px;padding:7px 12px;cursor:pointer}
#xiaogj-echarts-tree #xe-chart{height:max(560px,calc(100vh - 185px))}
</style></head><body>''' + fragment + '</body></html>\n'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', help='仓库内 private/ 下的新 HTML 路径')
    parser.add_argument('--open', action='store_true', help='生成后打开浏览器')
    args = parser.parse_args(argv)
    root, project = load_project(ROOT, 'projects/xiaogj-web/rebuild.json')
    name = args.out or ('projects/xiaogj-web/private/visualizations/exploration-tree-'
                        + datetime.now().strftime('%Y%m%d-%H%M%S-%f') + '.html')
    output = local_file(root, name, must_exist=False)
    if 'private' not in Path(name).parts or output.suffix != '.html':
        raise ValueError('generated case evidence must stay in private/ as HTML')
    if output.exists():
        raise FileExistsError('use a new output path')
    data = collect_data(root, project['inputs'])
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x') as stream:
        stream.write(render(data))
    print(json.dumps({'output': name, 'worlds': data['worlds'], 'nodes': data['nodes'],
                      'completion': 'not evaluated; visualization of recorded history only'}, ensure_ascii=False))
    if args.open:
        webbrowser.open(output.as_uri())
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
