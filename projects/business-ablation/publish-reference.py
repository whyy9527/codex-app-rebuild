"""Confirm and freeze the publisher before any formal model arm starts."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--control', required=True)
    args = parser.parse_args()
    root = Path(args.control).resolve()
    sys.path.insert(0, str(root))
    from capabilities.rebuild.contracts import freeze, load, verify
    from capabilities.exploration.storage import digest, save
    from runtime.runner import input_manifest
    deadline = time.time() + 2400
    for name in ['initial', 'expanded', 'holdout']:
        output = root / ('reference-' + name + '.json')
        batch_path = root / ('batch-' + name + '.json')
        if output.exists() or batch_path.exists():
            raise ValueError('Publisher records already exist; preserve the previous preparation')
        parent = None
        if name == 'expanded':
            parent = json.loads((root / 'batch-initial.json').read_text())
            spec_path = root / 'spec-expanded.json'
            spec = json.loads(spec_path.read_text());spec['parent_digest'] = digest(parent);save(spec_path, spec)
        contract = load(root, 'spec-' + name + '.json', 'targets.json')
        receipt = verify(root, contract, 'reference', 180, deadline=min(deadline, time.time() + 1200))
        save(output, receipt)
        print(json.dumps({'batch': name, 'status': receipt['status'], 'counts': receipt['counts']}), flush=True)
        if receipt['status'] != 'pass':
            raise ValueError('Actual reference confirmation failed; do not create model arms')
        save(batch_path, freeze(contract, receipt, parent))
    old = json.loads((root / 'fixed-inputs.json').read_text())
    paths = list(old) + ['reference-' + name + '.json' for name in ['initial', 'expanded', 'holdout']] + ['batch-' + name + '.json' for name in ['initial', 'expanded', 'holdout']]
    save(root / 'fixed-inputs.json', input_manifest(root, paths))
    print('All three reference batches frozen; formal arms still require committed registration and parent input audit.', flush=True)


if __name__ == '__main__':
    main()
