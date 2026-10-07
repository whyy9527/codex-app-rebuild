"""LLM code generation from explicit parent workspace, visible prefix and completed history."""
import hashlib
from pathlib import Path
from capabilities.exploration.ledger import canonical, digest
from runtime.policy_runtime import validate_source
from runtime.packing import CASES, packing_protocol

INSTRUCTIONS = ('Improve Python pack(weights, capacity) for bin packing. Return bins of original item indices, '
                'every index exactly once, each bin sum <= capacity. Evaluator rewards mean lower-bound/bins. '
                'Generate executable code, not a preset. Use only functions and literal module constants, no imports, '
                'classes, decorators, default arguments, private names, file access or tools. Available builtins: '
                'len,min,max,sum,sorted,range,enumerate,zip,list,dict,set,tuple,int,float,str,bool,abs,round,all,any,next. '
                'Basic dict/list/set methods and math.ceil/floor/sqrt/log/isfinite are available. '
                'Each case must finish within two seconds. Discuss actual previous failures when present. ')


class ModelDiscovery:
    def __init__(self, worker, *, history=None):
        self.worker, self.history = worker, history or []

    def __call__(self, workspace, observed, context):
        parent_source = (workspace/'pack.py').read_text()
        data = {'parent_source':parent_source, 'visible_prefix':observed, 'context':context,
                'completed_history':self.history, 'training_cases':CASES,
                'evaluation_protocol':packing_protocol()}
        reply = self.worker.generate(INSTRUCTIONS + canonical(data), role='discovery-generation')
        validate_source(reply['source'], entry='pack')
        (workspace/'pack.py').write_text(reply['source'])
        return {**reply['receipt'], 'rationale':reply['rationale'],
                'generator_protocol':digest({'instructions':INSTRUCTIONS,'evaluator':packing_protocol()}),
                'parent_source_digest':hashlib.sha256(parent_source.encode()).hexdigest()}
