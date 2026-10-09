"""Ablate consumer projections/Stop only; preserve the same Harness semantics."""
import argparse
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from capabilities.exploration.harness import Harness
from runtime import harness_hooks, harness_mcp
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


def hook(harness, payload):
    if payload.get('hook_event_name') == 'Stop' and not settings()['automatic_stop_feedback']:
        return {}
    return harness_hooks.handle(harness, payload)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['mcp', 'hook'])
    args = parser.parse_args()
    harness_mcp.summary = summary
    harness_hooks.summary = summary
    harness = RegisteredHarness(ROOT / 'state')
    if args.mode == 'mcp':
        harness_mcp.serve(harness, sys.stdin, sys.stdout)
    else:
        try:
            raw = sys.stdin.read(65537)
            if len(raw) > 65536:
                raise ValueError('Hook input too large')
            payload = json.loads(raw)
            result = hook(harness, payload)
            with (ROOT / 'state/hook-events.jsonl').open('a') as stream:
                stream.write(json.dumps({'event': payload.get('hook_event_name'), 'session_id': payload.get('session_id'),
                                         'turn_id': payload.get('turn_id'), 'decision': result.get('decision'),
                                         'output_fields': sorted(result), 'time': time.time()}) + '\n')
        except Exception:
            result = {}
        print(json.dumps(result))


if __name__ == '__main__':
    main()
