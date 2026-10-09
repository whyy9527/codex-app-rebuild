"""Prepare reference publisher or isolated arms; never copy the finished product."""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from runtime.runner import input_manifest
from workflows.harness.install import install

BASELINE = '21dbe64bfea93bf7ef2633ae0152021cad24fc81'
ARMS = {'full': (True, True, True), 'no_behavior_progress': (False, True, True),
        'no_stop_feedback': (True, False, True), 'no_supplemental_discovery': (True, True, False)}


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def register(control):
    worker = control / 'worker'
    install(worker, control)
    for mode in ['mcp', 'hook']:
        path = worker / '.codex/exploration-lab' / (mode + '.sh')
        path.write_text('#!/bin/sh\nexec ' + shlex.quote(sys.executable) + ' ' + shlex.quote(str(control / 'experiment-runtime.py')) + ' ' + mode + '\n')
        path.chmod(0o700)
    (control / 'state').mkdir(exist_ok=True)
    (control / 'artifacts').mkdir(exist_ok=True)


def publisher():
    control = Path(tempfile.mkdtemp(prefix='codex-business-reference-')).resolve()
    worker = control / 'worker'
    for name in ['capabilities', 'runtime', 'workflows']:
        shutil.copytree(ROOT / name, control / name, ignore=shutil.ignore_patterns('__pycache__'))
    for name in ['controller.py', 'experiment-runtime.py', 'handoff.py', 'score.py']:
        shutil.copy2(ROOT / 'projects/business-ablation' / name, control / name)
    for name in subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', BASELINE, 'projects/education-swift'], cwd=ROOT, text=True).splitlines():
        if not (name.endswith('.swift') or '/Tests/' in name):
            continue
        dst = worker / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(subprocess.check_output(['git', 'show', BASELINE + ':' + name], cwd=ROOT))
    case = Path('projects/duolingo-web')
    for name in ['fixture-v2.json', 'native-adapter-v3.swift', 'build-native.py']:
        dst = worker / case / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / case / name, dst)
    for name in ['original-adapter-v2.mjs', 'package.json', 'package-lock.json']:
        dst = control / case / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / case / name, dst)
    shutil.copytree(ROOT / case / 'node_modules', control / case / 'node_modules')
    specifications = {}
    full = json.loads((ROOT / case / 'spec-v2.json').read_text())
    full.pop('parent_digest', None)
    initial = json.loads(json.dumps(full));initial['behaviors'] = initial['behaviors'][:4]
    initial['revision'] = 'business-initial-four'
    full['revision'] = 'business-expanded-twelve'
    hidden = json.loads((ROOT / 'projects/business-ablation/holdout-spec.json').read_text())
    for name, spec in [('initial', initial), ('expanded', full), ('holdout', hidden)]:
        spec['fixture'] = 'worker/' + spec['fixture']
        for behavior in spec['behaviors']:
            for evidence in behavior.get('evidence', []):
                dst = control / evidence
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / evidence, dst)
        specifications[name] = spec
        write(control / ('spec-' + name + '.json'), spec)
    public = json.loads(json.dumps(initial));public['fixture'] = public['fixture'].removeprefix('worker/')
    for behavior in public['behaviors']:
        for name in behavior['evidence']:
            dst = worker / 'observations' / name
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, dst)
        behavior['evidence'] = ['observations/' + name for name in behavior['evidence']]
    write(worker / 'public-spec.json', public)
    (control / 'candidate-entry.py').write_text("from pathlib import Path\nimport os,runpy\nos.chdir(Path(__file__).resolve().parent/'worker')\nrunpy.run_path('projects/duolingo-web/build-native.py',run_name='__main__')\n")
    (worker / 'verify.py').write_text("from pathlib import Path\nimport runpy,sys\np=Path(__file__).resolve().parent.parent\nsys.path.insert(0,str(p))\nrunpy.run_path(str(p/'controller.py'),run_name='__main__')\n")
    targets = json.loads((ROOT / case / 'targets-v2.json').read_text())
    targets['targets']['candidate']['command'] = ['python3', 'candidate-entry.py']
    targets['targets']['candidate']['acceptance_paths'] = ['candidate-entry.py', 'worker/projects/duolingo-web/build-native.py', 'worker/projects/duolingo-web/native-adapter-v3.swift', 'worker/projects/education-swift/Package.swift', 'worker/projects/education-swift/Tests', 'controller.py', 'experiment-runtime.py']
    write(control / 'targets.json', targets)
    (worker / 'AGENTS.md').write_text('''# Registered business reconstruction experiment
Work only in this worker directory. Edit only projects/education-swift/Sources. Do not read parent/sibling directories, the finished main repository, another model session, private scoring or reference publisher files. No Git, publishing, account changes or global config edits. Do not modify fixtures, tests, package, drivers, verify.py, public-spec.json, observations or .codex configuration. The project-local MCP verifier is the approved external evaluation boundary; running it does not authorize reading its private files.

Build an original two-lesson education app from fixture-v2, including choice, matching, ordered removable words, correct/wrong feedback, missed-question review, sequential unlocks, completed-lesson persistence and quit cancel/discard. Keep core state/content/storage separate from SwiftUI. Preserve the old fixture/core interfaces and fixed core checks. Read the native adapter for required semantic accessibility identifiers. No Duolingo brand/assets, login, payments, speech or leaderboard.

Use the installed exploration tools with the fixed verifier python3 verify.py and finite registered budgets. You may work and iterate naturally within a turn; no forced one-attempt checkpoint rule. Before each attempt record a hypothesis. Read actual failures and repair Sources. Do not claim test success yourself. Passing four visible cases does not permit omitting features in the common product brief. At the registered handoff, end while paused; the parent will start one fresh session that explicitly adopts the same task and deadline. Runtime/model attestation and private scoring are parent-owned; do not inspect UI, processes or host sessions to self-attest. Do not launch extra model workers.
''')
    write(control / 'experiment.json', dict(zip(['persist_behavior_progress', 'automatic_stop_feedback', 'supplemental_discovery'], ARMS['full'])))
    register(control)
    paths = ['capabilities', 'runtime', 'workflows', 'controller.py', 'experiment-runtime.py', 'handoff.py', 'score.py', 'candidate-entry.py', 'targets.json', 'spec-initial.json', 'spec-expanded.json', 'spec-holdout.json', 'projects', 'worker/AGENTS.md', 'worker/verify.py', 'worker/projects/duolingo-web', 'worker/projects/education-swift/Package.swift', 'worker/projects/education-swift/Tests']
    # node_modules are included as immutable reference dependencies, outside the worker.
    write(control / 'fixed-inputs.json', input_manifest(control, paths))
    return control


def clone(master, arm):
    expected = json.loads((master / 'fixed-inputs.json').read_text())
    if input_manifest(master, list(expected)) != expected:
        raise ValueError('Publisher immutable inputs changed')
    for name in ['initial', 'expanded', 'holdout']:
        if not (master / ('batch-' + name + '.json')).is_file():
            raise ValueError('Reference-confirmed frozen batch required: ' + name)
    dst = Path(tempfile.mkdtemp(prefix='codex-business-' + arm + '-')).resolve()
    shutil.copytree(master, dst, dirs_exist_ok=True, ignore=shutil.ignore_patterns('__pycache__', '.build'))
    write(dst / 'experiment.json', dict(zip(['persist_behavior_progress', 'automatic_stop_feedback', 'supplemental_discovery'], ARMS[arm])))
    register(dst)
    return dst


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--publisher', action='store_true')
    parser.add_argument('--master')
    parser.add_argument('--arm', choices=ARMS)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    control = publisher() if args.publisher else clone(Path(args.master).resolve(), args.arm)
    files = {str(p.relative_to(control)): hashlib.sha256(p.read_bytes()).hexdigest() for p in control.rglob('*') if p.is_file() and 'node_modules' not in p.parts and '.codex' not in p.parts}
    write(Path(args.out), {'control': str(control), 'worker': str(control / 'worker'), 'product_baseline': BASELINE, 'arm': args.arm, 'files': files})
    print(json.dumps({'control': str(control), 'worker': str(control / 'worker'), 'files': len(files)}))
