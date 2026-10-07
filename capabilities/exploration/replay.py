"""Frozen recorded world; policy receives only revealed observations."""
from copy import deepcopy
import math


def validate_world(nodes):
    known, used_parents = {"root"}, set()
    for node in nodes:
        identifier, parent, score = node.get("id"), node.get("parent"), node.get("score")
        if not isinstance(identifier, str) or not identifier.strip() or identifier in known:
            raise ValueError("world ids must be unique nonempty strings excluding root")
        if not isinstance(parent, str) or parent not in known:
            raise ValueError("parent must precede child")
        if parent != "root" and parent in used_parents:
            raise ValueError("nonroot branches must have a single continuation")
        if isinstance(score, bool) or not isinstance(score, (int, float)) or not math.isfinite(score) or score < 0:
            raise ValueError("score must be finite and nonnegative")
        known.add(identifier)
        used_parents.add(parent)
    return deepcopy(nodes)


class Replay:
    def __init__(self, nodes, width=1, semantics='strict'):
        if isinstance(width, bool) or not isinstance(width, int) or width < 1:
            raise ValueError("width must be a positive integer")
        self.width = width
        if semantics not in ('strict', 'paper'):
            raise ValueError('unknown replay semantics')
        self.semantics = semantics
        self._nodes = validate_world(nodes)
        self._seen = [{"id": "root", "parent": None, "score": 0.0}]
        self.rounds = 0

    def observation(self):
        return deepcopy(self._seen)

    def legal_actions(self):
        parents = {n["parent"] for n in self._seen}
        return [n["id"] for n in self._seen if n["id"] == "root" or n["id"] not in parents]

    def step(self, parents):
        if not isinstance(parents, (list, tuple)) or any(not isinstance(p, str) for p in parents):
            raise ValueError("action must be a batch of parent identifiers")
        if len(parents) > self.width or len(set(parents)) != len(parents):
            raise ValueError("duplicate or overwide batch")
        if any(parent not in self.legal_actions() for parent in parents):
            raise ValueError("action refers to unseen or nonleaf node")
        if not parents:
            return {"status": "stopped", "revealed": []}
        seen = {n["id"] for n in self._seen}
        additions = []
        for parent in parents:
            options = [n for n in self._nodes if n["parent"] == parent and n["id"] not in seen]
            if not options:
                if self.semantics == 'strict':
                    return {"status": "unsupported", "revealed": []}
                continue
            additions.append(options[0])
        self._seen.extend(deepcopy(additions))
        self.rounds += bool(parents)
        return {"status": "ok", "revealed": deepcopy(additions)}


def run_replay(nodes, policy, *, width=1, max_rounds=100, max_calls=100, rho=0, semantics='strict'):
    for value in (max_rounds, max_calls):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError('budgets must be nonnegative integers')
    if isinstance(rho, bool) or not isinstance(rho, (int, float)) or not math.isfinite(rho) or not 0 <= rho <= 1:
        raise ValueError('rho must lie in [0, 1]')
    replay = Replay(nodes, width=width, semantics=semantics)
    trajectory, calls, reason, valid = [], 0, 'complete', True
    while len(replay.observation()) - 1 < len(nodes):
        if calls >= max_calls:
            reason = 'call_budget'
            break
        if replay.rounds >= max_rounds:
            reason = 'round_budget'
            break
        context = {'width': width, 'remaining_calls': max_calls - calls,
                   'remaining_rounds': max_rounds - replay.rounds, 'rho': rho,
                   'legal_parents': replay.legal_actions()}
        try:
            action = policy(replay.observation(), deepcopy(context))
            if isinstance(action, (list, tuple)) and len(action) > max_calls - calls:
                reason, valid = 'over_budget', False
                break
            result = replay.step(action)
        except Exception as error:
            reason, valid = 'policy_error', False
            trajectory.append({'error_type': type(error).__name__})
            break
        trajectory.append({'action': list(action), **result})
        if result['status'] != 'ok':
            reason = result['status']
            valid = reason == 'stopped'
            break
        calls += len(result['revealed'])
    return {'valid': valid, 'reason': reason, 'calls': calls, 'rounds': replay.rounds,
            'best_score': max(n['score'] for n in replay.observation()) if valid else 0,
            'observed': replay.observation(), 'trajectory': trajectory, 'rho': rho}
