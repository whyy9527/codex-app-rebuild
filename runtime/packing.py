"""Fixed bin-packing feasibility and lower-bound quality; not a paper benchmark reproduction."""
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
from capabilities.exploration.ledger import digest
from runtime.policy_runtime import validate_source

CASES = [([4,4,4,3,3,3,3,3,3],10), ([6,6,4,4,5,5,3,3,2,2],10),
         ([8,7,6,5,4,3,2,2,2,1],10), ([6,6,6,4,4,4,3,3,3,3,2,2],10),
         ([5,5,5,5,4,4,4,4,3,3,3,3,2,2,2,2],10)]
HELDOUT = [([4,4,4,4,3,3,3,3,3,3,3,3],10), ([7,7,6,6,4,4,3,3,2,2,1,1],10)]


def packing_protocol(cases=CASES):
    return digest({'cases': cases, 'rule': 'all indices exactly once, capacity feasible; mean ceil(sum/capacity)/bins',
                   'evaluator_source': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})


def evaluate_packing(workspace, cases=CASES):
    source = (Path(workspace)/'pack.py').read_text()
    scores, evidence = [], []
    protocol = packing_protocol(cases)
    try:
        validate_source(source, entry='pack')
        for weights, capacity in cases:
            result = subprocess.run([sys.executable, '-I', '-B', str(Path(__file__).with_name('policy_runtime.py'))],
                                    input=json.dumps({'source': source, 'entry':'pack', 'args':[weights,capacity]}),
                                    capture_output=True, text=True, timeout=2,
                                    env={'PATH':'/usr/bin:/bin', 'LANG':'C.UTF-8'})
            if result.returncode or len(result.stdout) > 65536:
                raise ValueError('candidate execution failed')
            bins = json.loads(result.stdout)
            if not isinstance(bins, list) or not bins or any(not isinstance(b, list) or not b for b in bins):
                raise ValueError('invalid bins')
            indices = [i for b in bins for i in b]
            if any(not isinstance(i, int) or isinstance(i, bool) for i in indices) or sorted(indices) != list(range(len(weights))):
                raise ValueError('every index must appear exactly once')
            if any(sum(weights[i] for i in b) > capacity for b in bins):
                raise ValueError('capacity exceeded')
            lower = math.ceil(sum(weights)/capacity)
            scores.append(lower/len(bins))
            evidence.append({'bins':len(bins), 'lower_bound':lower, 'assignment_digest':digest(bins)})
    except (ValueError, SyntaxError, subprocess.TimeoutExpired) as error:
        return {'status':'fail', 'score':0.0, 'error':str(error), 'protocol_digest':protocol, 'cases':evidence}
    return {'status':'pass', 'score':sum(scores)/len(scores), 'cases':evidence, 'protocol_digest':protocol,
            'source_digest':hashlib.sha256(source.encode()).hexdigest()}
