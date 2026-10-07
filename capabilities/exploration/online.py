"""Trusted local generation/evaluation adapters; no model calls are implied."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import hashlib
import math
from pathlib import Path
import shutil
import time
from capabilities.exploration.ledger import digest
from capabilities.exploration.replay import Replay, validate_world


def workspace_manifest(root):
    files = {}
    for path in sorted(Path(root).rglob('*')):
        if path.is_symlink():
            raise ValueError('workspace symlinks are unsupported')
        if path.is_file() and not any(part in {'artifacts', '__pycache__', '.git'} for part in path.relative_to(root).parts):
            files[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return files


def copy_workspace(source, target):
    files = workspace_manifest(source)
    target.mkdir(parents=True, exist_ok=False)
    for name in files:
        output = target / name
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(Path(source) / name, output)
    if workspace_manifest(target) != files:
        raise ValueError('source changed while copying workspace')
    return files


def online_rollout(root, destination, agent, evaluator, policy, *, width=1, max_calls=10,
                   max_rounds=10, rho=0):
    root, destination = Path(root).resolve(), Path(destination).resolve()
    if root == destination or root in destination.parents or destination in root.parents:
        raise ValueError('input and output trees must not overlap')
    if destination.exists():
        raise ValueError('use a fresh run directory')
    for budget in (max_calls, max_rounds):
        if isinstance(budget, bool) or not isinstance(budget, int) or budget < 0:
            raise ValueError('nonnegative integer budgets required')
    if not isinstance(rho, (int, float)) or isinstance(rho, bool) or not math.isfinite(rho) or not 0 <= rho <= 1:
        raise ValueError('rho must lie in [0,1]')
    Replay([], width=width)
    source_files = workspace_manifest(root)
    destination.mkdir(parents=True)
    copy_workspace(root, destination / 'root')
    observed = [{'id': 'root', 'parent': None, 'score': 0.0}]
    nodes, rounds, calls, trajectory = [], 0, 0, []
    started = time.monotonic()
    reason = 'round_budget'

    def attempt(identifier, parent, prefix, context):
        workspace = destination / identifier
        began = time.monotonic()
        copy_workspace(destination / parent, workspace)
        try:
            agent(workspace, deepcopy(prefix), {**deepcopy(context), "parent": parent})
            evaluation = evaluator(workspace)
            score = evaluation['score']
            if isinstance(score, bool) or not isinstance(score, (int, float)) or not math.isfinite(score) or score < 0:
                raise ValueError('evaluator returned invalid score')
            if evaluation['status'] != 'pass':
                score = 0.0
        except Exception as error:
            score = 0.0
            evaluation = {'status': 'error', 'error_type': type(error).__name__}
        return {'id': identifier, 'parent': parent, 'score': score,
                'observation': evaluation, 'workspace_digest': digest(workspace_manifest(workspace)),
                'cost': {'generation_calls': 1, 'wall_seconds': round(time.monotonic() - began, 6),
                         'model_tokens': None, 'model_cost': None}}

    with ThreadPoolExecutor(max_workers=width) as pool:
        while rounds < max_rounds:
            if calls >= max_calls:
                reason = 'call_budget'
                break
            view = Replay(nodes, width=width)
            view._seen = deepcopy(observed)
            context = {'width': width, 'remaining_calls': max_calls - calls,
                       'remaining_rounds': max_rounds - rounds, 'rho': rho,
                       'legal_parents': view.legal_actions()}
            action = policy(deepcopy(observed), deepcopy(context))
            if not isinstance(action, (list, tuple)) or any(not isinstance(p, str) for p in action):
                raise ValueError('policy must return parent identifiers')
            if (len(action) > min(width, max_calls - calls) or len(set(action)) != len(action)
                    or any(parent not in view.legal_actions() for parent in action)):
                raise ValueError('illegal online action')
            if not action:
                reason = 'stopped'
                break
            identifiers = [f'n{calls + i + 1:04}' for i in range(len(action))]
            futures = [pool.submit(attempt, identifier, parent, observed, context)
                       for identifier, parent in zip(identifiers, action)]
            additions = [future.result() for future in futures]
            validate_world(nodes + additions)
            nodes.extend(additions)
            observed.extend(deepcopy(additions))
            calls += len(additions)
            rounds += 1
            trajectory.append({'action': list(action), 'children': identifiers})
    if workspace_manifest(root) != source_files:
        raise ValueError('generation modified source input')
    return {'nodes': nodes, 'calls': calls, 'rounds': rounds, 'reason': reason,
            'trajectory': trajectory, 'input_digest': digest(source_files),
            'wall_seconds': round(time.monotonic() - started, 6),
            'generation_kind': 'caller-supplied adapter; not necessarily an LLM',
            'audiovisual': 'unavailable'}
