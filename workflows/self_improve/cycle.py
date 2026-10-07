"""Online -> freeze -> replay -> select -> deploy, using executable toy policy candidates."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from capabilities.exploration.ledger import Ledger, digest
from capabilities.exploration.objective import select_policy, policy_digest
from capabilities.exploration.online import online_rollout
from runtime.toy import generate, training_evaluator, shifted_evaluator


def policy_source(root_trials, target, limit):
    return f'''def policy(observed, context):
    # Prefix-only executable portfolio; constants are part of the code fingerprint.
    root_trials, target, limit = {root_trials!r}, {target!r}, {limit!r}
    calls = len(observed) - 1
    target_calls = max(1, int(limit * (1 - .75 * context['rho']) + .999999))
    if calls >= target_calls or max(n['score'] for n in observed) >= target:
        return []
    roots = [n for n in observed if n['parent'] == 'root']
    if len(roots) < root_trials:
        return ['root']
    parents = {{n['parent'] for n in observed}}
    leaves = [n for n in observed if n['id'] != 'root' and n['id'] not in parents]
    leaves.sort(key=lambda n: (n.get('observation', {{}}).get('depth', 0), -n['score']))
    slots = min(context['width'], context['remaining_calls'], target_calls - calls)
    return [n['id'] for n in leaves[:slots]]
'''


def load_policy(path, source):
    path.write_text(source)
    spec = importlib.util.spec_from_file_location('generated_policy', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.policy


def compact_selection(selection):
    return {name: {'policy_digest': report['policy_digest'], 'score': report['score'],
                   'worlds': [{'world_digest': world['world_digest'], 'score': world['score'],
                               'runs': [{key: run[key] for key in ('rho', 'valid', 'reason', 'calls', 'rounds', 'best_score')}
                                        for run in world['runs']]} for world in report['worlds']]}
            for name, report in selection['candidates'].items()}


def run_cycles(output, *, rounds=10):
    if isinstance(rounds, bool) or not isinstance(rounds, int) or not 1 <= rounds <= 100:
        raise ValueError('rounds must be an integer in [1,100]')
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    policies = output / 'policies'
    policies.mkdir()
    root = output / 'input'
    root.mkdir()
    (root / 'candidate.json').write_text(json.dumps({'slope': 0, 'intercept': 0, 'depth': -1}))
    (root / 'solver.py').write_text('def solve(x):\n    return 0\n')
    baseline_source = policy_source(3, 2, 6)
    active_source = baseline_source
    worlds, cycles = [], []
    ledger = Ledger(output / 'records.sqlite')
    try:
        for index in range(1, rounds + 1):
            incumbent = load_policy(policies / f'cycle-{index:02}-incumbent.py', active_source)
            rollout = online_rollout(root, output / f'online-{index:02}', generate, training_evaluator,
                                     incumbent, width=2, max_calls=6, max_rounds=6)
            worlds.append(rollout['nodes'])
            sources = {'incumbent': active_source,
                       'refine_first': policy_source(1, 1, 6),
                       'two_roots': policy_source(2, 1, 6),
                       'stop_at_half': policy_source(3, .5, 6),
                       'small_budget': policy_source(1, 1, 2),
                       'one_call': policy_source(1, 2, 1)}
            candidates = {name: load_policy(policies / f'cycle-{index:02}-{name}.py', source)
                          for name, source in sources.items()}
            selection = select_policy(worlds, candidates, incumbent='incumbent', width=2,
                                      max_calls=6, max_rounds=6, penalty=.05)
            selected = selection['selected']
            next_source = sources[selected]
            record = {'id': f'cycle-{index:02}', 'parent': f'cycle-{index-1:02}' if index > 1 else None,
                      'history_worlds': len(worlds), 'online': rollout,
                      'online_policy_digest': policy_digest(incumbent),
                      'next_policy_digest': policy_digest(candidates[selected]),
                      'selected': selected, 'policy_changed': next_source != active_source,
                      'incumbent_replay_score': selection['candidates']['incumbent']['score'],
                      'selected_replay_score': selection['candidates'][selected]['score'],
                      'selection': compact_selection(selection), 'policy_sources': sources}
            ledger.append(record)
            cycles.append(record)
            active_source = next_source
        selected_policy = load_policy(policies / 'selected.py', active_source)
        baseline_policy = load_policy(policies / 'fixed.py', baseline_source)
        fixed = online_rollout(root, output / 'heldout-fixed', generate, shifted_evaluator,
                               baseline_policy, width=2, max_calls=6, max_rounds=6)
        selected = online_rollout(root, output / 'heldout-selected', generate, shifted_evaluator,
                                  selected_policy, width=2, max_calls=6, max_rounds=6)
        held_out = {name: {'calls': rollout['calls'], 'rounds': rollout['rounds'],
                          'best_score': max(n['score'] for n in rollout['nodes']),
                          'world_digest': digest(rollout['nodes'])}
                    for name, rollout in [('fixed', fixed), ('selected', selected)]}
        report = {'generation_kind': 'deterministic toy program adapter, not LLM',
                  'cycles': cycles, 'audit': ledger.verify(),
                  'total_generation_calls': sum(c['online']['calls'] for c in cycles) + fixed['calls'] + selected['calls'],
                  'model_tokens': None, 'model_cost': None, 'audiovisual': 'unavailable',
                  'held_out': held_out,
                  'limits': ['toy finite policy portfolio, not autonomous LLM policy synthesis',
                             'history reward is not a new-task quality guarantee',
                             'trusted Python adapters; not an untrusted code sandbox',
                             'generation callable must implement its own timeout',
                             'engineering round evaluators differ between rounds; no aggregate improvement score']}
        (output / 'report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
        return report
    finally:
        ledger.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    parser.add_argument('--rounds', type=int, default=10)
    args = parser.parse_args()
    report = run_cycles(args.out, rounds=args.rounds)
    print(json.dumps({'cycles': len(report['cycles']), 'generation_calls': report['total_generation_calls'],
                      'policy_changes': sum(c['policy_changed'] for c in report['cycles']),
                      'held_out': report['held_out']}))


if __name__ == '__main__':
    main()
