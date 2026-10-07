"""A deliberately trivial executable workload for protocol checks, not discovery research."""
import json
from runtime.runner import evaluate


def generate(workspace, observed, context):
    previous = json.loads((workspace / 'candidate.json').read_text())
    if context['parent'] == 'root':
        branch = sum(node.get('parent') == 'root' for node in observed)
        slope, intercept, depth = 1 + branch % 3, 0, 0
    else:
        slope, intercept, depth = 3, 1, previous['depth'] + 1
    (workspace / 'candidate.json').write_text(json.dumps({'slope': slope, 'intercept': intercept, 'depth': depth}))
    (workspace / 'solver.py').write_text(f'def solve(x):\n    return {slope} * x + {intercept}\n')


def score(workspace, target_slope=3):
    # The evaluator supplies target values independently of candidate output.
    script = ('import json, math; from solver import solve; '
              f'errors = [abs(solve(x) - ({target_slope} * x + 1)) for x in (-3,-1,0,2,4)]; '
              'error = math.fsum(errors) / len(errors); '
              'print(json.dumps({"score": 1 / (1 + error)}))')
    receipt = evaluate(workspace, ['python3', '-B', '-c', script], timeout=3)
    quality = 0
    if receipt['status'] == 'pass':
        quality = json.loads(receipt['output'])['score']
    depth = json.loads((workspace / 'candidate.json').read_text())['depth']
    return {'status': receipt['status'], 'score': quality, 'depth': depth, 'execution': receipt}


def training_evaluator(workspace):
    return score(workspace, target_slope=3)


def shifted_evaluator(workspace):
    return score(workspace, target_slope=4)
