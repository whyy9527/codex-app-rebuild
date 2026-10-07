"""Verify and summarize ten engineering rounds against exact committed source trees."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
from capabilities.exploration.ledger import verify_records


def build_report(receipts, cycles):
    audit = verify_records(receipts)
    log = subprocess.check_output(['git', 'log', '--format=%H %s'], text=True)
    commits = {}
    for line in log.splitlines():
        match = re.match(r'([0-9a-f]+) feat: round (\d+) ', line)
        if match:
            commits[int(match[2])] = match[1]
    rounds = []
    for index in range(1, 11):
        before = next(record for record in receipts if record['id'] == f'r{index:02}-before')
        after = next(record for record in receipts if record['id'] == f'r{index:02}-after')
        a, b = before['evaluation'], after['evaluation']
        if before['hypothesis'] != after['hypothesis'] or a['evaluator_digest'] != b['evaluator_digest']:
            raise ValueError(f'round {index}: evaluator changed within pair')
        if a['status'] != 'fail' or b['status'] != 'pass' or a['source_digest'] == b['source_digest']:
            raise ValueError(f'round {index}: no verified failing-to-passing source change')
        commit = commits[index]
        for name, expected in b['source_files'].items():
            content = subprocess.check_output(['git', 'show', f'{commit}:{name}'])
            if hashlib.sha256(content).hexdigest() != expected:
                raise ValueError(f'round {index}: committed source does not match receipt: {name}')
        rounds.append({'round': index, 'commit': commit, 'hypothesis': after['hypothesis'],
                       'before': {'status': a['status'], 'source_digest': a['source_digest']},
                       'after': {'status': b['status'], 'source_digest': b['source_digest']},
                       'evaluator_digest': b['evaluator_digest'],
                       'record_ids': [before['id'], after['id']],
                       'wall_seconds': a['wall_seconds'] + b['wall_seconds']})
    return {'engineering_rounds': rounds, 'portable_audit': audit,
            'policy_cycles': len(cycles['cycles']),
            'policy_changes': sum(c['policy_changed'] for c in cycles['cycles']),
            'generation_calls': cycles['total_generation_calls'],
            'held_out': cycles['held_out'], 'model_tokens': None, 'model_cost': None,
            'interpretation': 'Ten Codex engineering edits verified by internal tools; separately ten toy policy cycles. Not ten autonomous LLM research breakthroughs.'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--receipts', required=True)
    parser.add_argument('--cycles', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    report = build_report(json.loads(Path(args.receipts).read_text()), json.loads(Path(args.cycles).read_text()))
    Path(args.out).write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({'verified_engineering_rounds': len(report['engineering_rounds']),
                      'policy_cycles': report['policy_cycles'], 'policy_changes': report['policy_changes']}))


if __name__ == '__main__':
    main()
