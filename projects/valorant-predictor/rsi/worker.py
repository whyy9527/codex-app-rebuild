"""Fixed discovery and independent live browser evaluation for Toy navigation."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from browser_evidence import capture_case, ROUTES


def main():
    request = json.load(sys.stdin)
    workspace = Path(request['workspace'])
    if sys.argv[1] == 'agent':
        visited = json.loads((workspace / 'visited.json').read_text()) if (workspace / 'visited.json').exists() else []
        remaining = [r for r in ROUTES if r not in visited]
        route = remaining[0] if remaining else ROUTES[-1]
        (workspace / 'probe.json').write_text(json.dumps({'route': route}))
        return {'generation': {'route': route, 'restoration': 'fresh isolated browser context'},
                'observation': {'planned_route': route, 'remaining': remaining}}
    probe = json.loads((workspace / 'probe.json').read_text())
    route = probe['route']
    out = 'capture-' + str(len(list(workspace.glob('capture-*'))))
    result = capture_case(workspace, route, out)
    state = result['states'].get(route.strip('/') or 'home', {})
    text = '\n'.join(state.get('accessible_text', []))
    # This score measures confirmed distinct navigation surfaces, not appearance,
    # semantic completeness, or app quality. Screenshot drift remains in receipts.
    loaded = len(text) > 300 and bool(result['steps']) and result['steps'][0].get('ready', {}).get('status') == 'observed'
    visited = json.loads((workspace / 'visited.json').read_text()) if (workspace / 'visited.json').exists() else []
    if loaded and route not in visited: visited.append(route)
    (workspace / 'visited.json').write_text(json.dumps(visited))
    return {'score': len(visited) / len(ROUTES), 'observation': {'visited': visited,
            'capture': out + '/observed.json', 'capture_status': result['status'],
            'loaded': loaded, 'text_characters': len(text), 'remaining': [r for r in ROUTES if r not in visited],
            'error': result.get('error')}}


if __name__ == '__main__': print(json.dumps(main(), ensure_ascii=False))
