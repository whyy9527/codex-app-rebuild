"""Trusted experiment boundary; visible feedback and private scoring stay separate."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import time

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from capabilities.rebuild.contracts import coverage, load, verify
from capabilities.exploration.harness import Harness
from capabilities.exploration.storage import save
from runtime.runner import input_manifest


def read(path):
    return json.loads(Path(path).read_text())


def settings():
    return read(ROOT / 'experiment.json')


def check_fixed():
    expected = read(ROOT / 'fixed-inputs.json')
    if input_manifest(ROOT, list(expected)) != expected:
        raise ValueError('Registered external acceptance or toolkit changed')


def progress():
    state = read(ROOT / 'experiment-state.json') if (ROOT / 'experiment-state.json').exists() else {}
    phase = state.get('phase', 'initial')
    current_spec = 'spec-expanded.json' if phase != 'initial' and settings()['supplemental_discovery'] else 'spec-initial.json'
    result = {'phase': phase, 'batches': []}
    latest = {}
    for name in state.get('receipts', []):
        receipt = read(ROOT / name)
        latest[receipt['revision']] = (name, receipt)
    current_receipt = None
    for name, receipt in latest.values():
        spec = 'spec-initial.json' if receipt['revision'] == 'business-initial-four' else 'spec-expanded.json'
        contract = load(ROOT, spec, 'targets.json')
        result['batches'].append({'receipt': name, 'revision': receipt['revision'],
                                 'historical_counts': receipt['counts'],
                                 'current': coverage(contract, receipt)})
        if spec == current_spec:
            current_receipt = receipt
    result['current_inventory'] = coverage(load(ROOT, current_spec, 'targets.json'), current_receipt)
    return result


def reveal():
    worker = ROOT / 'worker'
    public = read(ROOT / 'spec-expanded.json')
    public['fixture'] = public['fixture'].removeprefix('worker/')
    for behavior in public['behaviors']:
        for name in behavior.get('evidence', []):
            dst = worker / 'observations' / name
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, dst)
        behavior['evidence'] = ['observations/' + name for name in behavior.get('evidence', [])]
    save(worker / 'public-spec.json', public)


def visible_result(receipt, phase):
    diagnostics = []
    sources = [e['receipt'] for e in receipt.get('lifecycle', []) if e['receipt']['status'] != 'pass']
    sources += [b['receipt'] for b in receipt['behaviors'] if b['status'] != 'pass' and 'receipt' in b]
    for raw in sources[:2]:
        output = raw.get('output', '')
        try:
            payload = json.loads(next(line.removeprefix('APP_REBUILD_RESULT ') for line in output.splitlines() if line.startswith('APP_REBUILD_RESULT ')))
            message = str(payload.get('reason', '')) + '\n' + str(payload.get('build_log', ''))
        except (ValueError, StopIteration):
            message = output
        diagnostics.append({'status': raw['status'], 'message': message[:1800]})
    return {'phase': phase, 'revision': receipt['revision'], 'counts': receipt['counts'],
            'integrity': receipt['integrity'], 'diagnostics': diagnostics,
            'differences': [{'id': b['id'], 'status': b['status'], 'differences': b.get('differences', []),
                             'reason': b.get('reason')} for b in receipt['behaviors'] if b['status'] != 'pass'],
            'next_action': 'Read the current public specification and repair product Sources; preserve frozen inputs.'}


def run():
    check_fixed()
    config = settings()
    harness = Harness(ROOT / 'state')
    tasks = [read(p) for p in (ROOT / 'state').glob('*.json') if len(p.stem) == 32]
    live = [t for t in tasks if t['phase'] == 'verifying']
    if len(live) != 1:
        raise ValueError('Exactly one registered verification must be in flight')
    task = live[0]
    state_path = ROOT / 'experiment-state.json'
    state = read(state_path) if state_path.exists() else {'phase': 'initial', 'receipts': [], 'handoff_done': False, 'initial_confirmed': False}
    number = task['iterations']
    (ROOT / 'artifacts').mkdir(exist_ok=True)
    if (ROOT / f'artifacts/attempt-{number:02d}-source.json').exists():
        raise ValueError('Refusing to replace prior source snapshot')
    snapshot = {str(p.relative_to(ROOT / 'worker')): {'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'content': p.read_text()}
                for p in sorted((ROOT / 'worker/projects/education-swift/Sources').rglob('*.swift'))}
    save(ROOT / f'artifacts/attempt-{number:02d}-source.json', snapshot)
    phase = state['phase']
    spec = 'spec-initial.json' if phase == 'initial' else 'spec-expanded.json'
    batch = 'batch-initial.json' if phase == 'initial' else 'batch-expanded.json'
    contract = load(ROOT, spec, 'targets.json')
    receipt = verify(ROOT, contract, 'candidate', 300, read(ROOT / batch), deadline=min(task['deadline'], time.time() + 1100))
    name = f'artifacts/attempt-{number:02d}-candidate.json'
    if (ROOT / name).exists():
        raise ValueError('Refusing to replace prior receipt')
    save(ROOT / name, receipt)
    state['receipts'].append(name)
    handoff_now = False
    if receipt['status'] == 'pass' and phase == 'initial' and not state['initial_confirmed']:
        state['initial_confirmed'] = True
        state['phase'] = 'expanded' if config['supplemental_discovery'] else 'initial'
        if config['supplemental_discovery']:
            reveal()
        if not state['handoff_done']:
            handoff_now = True
            harness.pause(task['id'], 'Registered single post-initial-batch session handoff')
        elif not config['supplemental_discovery']:
            state['phase'] = 'complete'
    elif receipt['status'] == 'pass':
        state['phase'] = 'complete'
    save(state_path, state)
    check_fixed()
    result = visible_result(receipt, state['phase'])
    if state['phase'] == 'complete':
        result['next_action'] = 'Measured visible acceptance completed. End the turn; private evaluation is parent-owned.'
    elif handoff_now:
        result['next_action'] = 'Registered handoff boundary reached; end this session while paused. New session adopts the same task and deadline.'
    print(json.dumps(result))
    return 0 if state['phase'] == 'complete' else 1


if __name__ == '__main__':
    try:
        raise SystemExit(run())
    except (ValueError, OSError, KeyError) as error:
        print(json.dumps({'status': 'invalid', 'reason': str(error).replace(str(ROOT), '<control>')}))
        raise SystemExit(2)
