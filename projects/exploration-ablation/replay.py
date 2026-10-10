"""Replay real one-level source branches without exposing unseen outcomes to policy."""
import hashlib
import json
import re
from pathlib import Path


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def atoms(receipt):
    result = set()
    for line in receipt['snapshot'].splitlines():
        line = re.sub(r'^\s*-\s*', '', line).strip()
        if line and line != 'img':
            result.add(json.dumps(['ax', line], ensure_ascii=False))
    for item in receipt['visible']:
        # Read the recorded facts; never infer scores or unexecuted effects.
        identity = [item.get(k) for k in ['tag', 'role', 'test', 'text']]
        for field in ['enabled', 'checked', 'rect', 'css']:
            if field in item:
                result.add(json.dumps([identity, field, item[field]], ensure_ascii=False, sort_keys=True))
    return result


def validate_policy(policy):
    if not isinstance(policy.get('rules'), list) or len(policy['rules']) > 16:
        raise ValueError('At most 16 visible-label rules')
    for row in policy['rules']:
        if not isinstance(row['term'], str) or not 1 <= len(row['term']) <= 80 or type(row['weight']) not in (int, float) or not -10 <= row['weight'] <= 10:
            raise ValueError('Invalid bounded label rule')
    if type(policy['repeat_penalty']) not in (int, float) or not 0 <= policy['repeat_penalty'] <= 20:
        raise ValueError('Invalid repeat penalty')


def choose(policy, observation):
    validate_policy(policy)
    def score(action):
        label = action['label'].casefold()
        return sum(r['weight'] for r in policy['rules'] if r['term'].casefold() in label) - policy['repeat_penalty'] * observation['visits'].get(action['id'], 0)
    return max(observation['actions'], key=score)['id']


def load_world(directory):
    directory = Path(directory)
    collection = json.loads((directory / 'collection.json').read_text())
    if not collection['identical_root_snapshots']:
        raise ValueError('Source root snapshots differ; do not pretend a matched replay world')
    actions, outcomes, roots = [], {}, []
    for branch in collection['branches']:
        action = branch['action']
        if action['id'] in outcomes:
            raise ValueError('Ambiguous state/action successor')
        before = json.loads((directory / branch['before']).read_text())
        after = json.loads((directory / branch['after']).read_text())
        roots.append(hashlib.sha256(before['snapshot'].encode()).hexdigest())
        if before['path'] != '/learn':
            raise ValueError('Expected observed home root')
        actions.append({'id': action['id'], 'label': action['label']})
        outcomes[action['id']] = {'atoms': sorted(atoms(after) - atoms(before)), 'evidence': branch['after'],
                                  'receipt_sha256': hashlib.sha256((directory / branch['after']).read_bytes()).hexdigest()}
    if len(actions) < 2 or len(set(roots)) != 1 or roots != collection['root_snapshot_hashes']:
        raise ValueError('Recomputed source roots do not match registered branch world')
    return {'root_snapshot': before['snapshot'], 'actions': actions, 'outcomes': outcomes}


def replay(world, policy, budget=2):
    if type(budget) is not int or not 1 <= budget <= 100:
        raise ValueError('Explicit finite action budget required')
    observation = {'actions': world['actions'], 'visits': {}, 'revealed': []}
    discovered, trace = set(), []
    for step in range(budget):
        # The policy receives only action labels, prior visits and past revelations.
        action = choose(policy, json.loads(json.dumps(observation)))
        if action not in world['outcomes']:
            raise ValueError('Unknown outcome cannot be fabricated')
        outcome = world['outcomes'][action]
        newly = set(outcome['atoms']) - discovered
        discovered.update(newly)
        observation['visits'][action] = observation['visits'].get(action, 0) + 1
        observation['revealed'].append({'action': action, 'atoms': outcome['atoms']})
        trace.append({'step': step + 1, 'action': action, 'new_atoms': len(newly), 'outcome': outcome})
    return {'policy_digest': digest(policy), 'budget': budget, 'score': len(discovered), 'trace': trace,
            'interpretation': 'Recorded frontend fact novelty proxy only; not requirement sufficiency, online gains or visual equivalence'}
