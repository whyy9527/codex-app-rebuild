"""Manual consumer projection checks. Historical Stop ablations require their frozen revision."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from capabilities.exploration.harness import Harness
from runtime import harness_mcp
from controller import check_fixed, progress, settings

BASE_SUMMARY = harness_mcp.summary
ACCEPTANCE = ['verify.py', 'AGENTS.md', 'projects/education-swift/Package.swift',
              'projects/education-swift/Tests', 'projects/duolingo-web']


def summary(state):
    value = BASE_SUMMARY(state)
    if settings()['persist_behavior_progress']:
        value['behavior_progress'] = progress()
    return value


class RegisteredHarness(Harness):
    def start(self, **kwargs):
        config = settings()
        if any(len(p.stem) == 32 for p in self.directory.glob('*.json')):
            raise ValueError('One registered task only; do not reset the budget')
        if Path(kwargs['workspace']).resolve() != ROOT / 'worker':
            raise ValueError('Only the registered worker is allowed')
        if kwargs['verifier'] != ['python3', 'verify.py']:
            raise ValueError('Use the registered verifier')
        for key, expected in [('max_iterations', 20), ('max_failures', 20), ('max_seconds', 5400), ('verify_seconds', 1200)]:
            if kwargs.get(key) != expected:
                raise ValueError('Use the registered ' + key)
        if kwargs.get('acceptance_paths') != ACCEPTANCE:
            raise ValueError('Use the registered acceptance paths in the given order')
        check_fixed()
        state = super().start(**kwargs)
        config['first_session'] = state['session_id']
        (ROOT / 'experiment.json').write_text(json.dumps(config, indent=2) + '\n')
        return state


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['mcp'])
    parser.parse_args()
    harness_mcp.summary = summary
    harness = RegisteredHarness(ROOT / 'state')
    harness_mcp.serve(harness, sys.stdin, sys.stdout)


if __name__ == '__main__':
    main()
