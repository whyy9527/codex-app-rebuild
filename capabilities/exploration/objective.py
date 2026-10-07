"""Paper equation (1); unsupported traces are ineligible, not fabricated rewards."""
import hashlib
import inspect
import math
from capabilities.exploration.ledger import digest
from capabilities.exploration.replay import run_replay, validate_world

RHOS = (0, .25, .5, .75, 1)


def replay_score(runs, *, total_calls, best_recorded, penalty=.05):
    if not runs or isinstance(total_calls, bool) or not isinstance(total_calls, int) or total_calls < 1:
        raise ValueError('nonempty results and positive world size required')
    if not math.isfinite(best_recorded) or best_recorded <= 0 or not math.isfinite(penalty) or penalty < 0:
        raise ValueError('positive finite reference score and nonnegative penalty required')
    if any(not run['valid'] for run in runs):
        return None
    points, ratios = [], []
    for run in runs:
        calls, rounds, score = run['calls'], run['rounds'], run['best_score']
        if (not isinstance(calls, int) or isinstance(calls, bool) or not 0 <= calls <= total_calls
                or not isinstance(rounds, int) or isinstance(rounds, bool) or not 0 <= rounds <= calls
                or not math.isfinite(score) or score < 0 or (calls == 0 and score != 0)):
            raise ValueError('invalid replay result')
        points.append((calls, min(score / best_recorded, 1)))
        ratios.append(rounds / calls if calls else 0)
    frontier = []
    best = -1
    for calls, quality in sorted(set(points), key=lambda point: (point[0], -point[1])):
        if quality > best:
            frontier.append((calls, quality))
            best = quality
    previous, volume = 0, 0
    for calls, quality in frontier:
        volume += (quality - previous) * (total_calls - calls) / total_calls
        previous = quality
    return volume - penalty * sum(ratios) / len(runs)


def policy_digest(policy):
    if isinstance(getattr(policy, 'source', None), str):
        return hashlib.sha256(policy.source.encode()).hexdigest()
    try:
        source = inspect.getsource(policy)
    except (OSError, TypeError):
        raise ValueError('policies must have inspectable source code') from None
    return hashlib.sha256(source.encode()).hexdigest()


def select_policy(worlds, candidates, *, incumbent, width=1, max_rounds=100, max_calls=100,
                  penalty=.05):
    if incumbent not in candidates or not worlds:
        raise ValueError('include incumbent and at least one world')
    worlds = [validate_world(world) for world in worlds]
    if any(not world or max(node['score'] for node in world) <= 0 for world in worlds):
        raise ValueError('worlds require at least one positive recorded score')
    reports = {}
    for name, policy in candidates.items():
        scores, evidence = [], []
        for world in worlds:
            runs = [run_replay(world, policy, width=width, max_rounds=max_rounds,
                               max_calls=max_calls, rho=rho) for rho in RHOS]
            value = replay_score(runs, total_calls=len(world),
                                 best_recorded=max(node['score'] for node in world), penalty=penalty)
            scores.append(value)
            evidence.append({'world_digest': digest(world), 'score': value, 'runs': runs})
        reports[name] = {'policy_digest': policy_digest(policy), 'worlds': evidence,
                         'score': None if None in scores else sum(scores) / len(scores)}
    if reports[incumbent]['score'] is None:
        raise ValueError('incumbent is unsupported; supply a valid baseline')
    selected = incumbent
    for name, report in reports.items():
        if report['score'] is not None and report['score'] > reports[selected]['score']:
            selected = name
    return {'selected': selected, 'incumbent': incumbent, 'candidates': reports,
            'evaluation': {'rhos': RHOS, 'penalty': penalty, 'width': width,
                           'max_rounds': max_rounds, 'max_calls': max_calls},
            'scope': 'frozen-history score only; new-task improvement unverified'}
