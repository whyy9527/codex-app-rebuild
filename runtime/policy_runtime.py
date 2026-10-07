"""Prefix-only restricted Python in a separate process; not an OS security sandbox."""
import ast
import json
import math
from pathlib import Path
import subprocess
import sys

SAFE_BUILTINS = {name: getattr(__builtins__, name) if not isinstance(__builtins__, dict) else __builtins__[name]
                 for name in ('len', 'min', 'max', 'sum', 'sorted', 'range', 'enumerate', 'zip', 'list',
                              'dict', 'set', 'tuple', 'int', 'float', 'str', 'bool', 'abs', 'round',
                              'all', 'any', 'reversed', 'next', 'ValueError')}
METHODS = {'get', 'items', 'keys', 'values', 'append', 'extend', 'sort', 'index', 'count',
           'add', 'discard', 'pop', 'copy', 'remove', 'setdefault', 'update'}
MATH = {'ceil', 'floor', 'sqrt', 'log', 'exp', 'isfinite', 'fabs'}


def validate_source(source):
    if not isinstance(source, str) or len(source) > 40000:
        raise ValueError('invalid policy source')
    tree = ast.parse(source)
    definitions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'policy']
    if len(definitions) != 1 or len(definitions[0].args.args) != 2:
        raise ValueError('define policy(observed, context) exactly once')
    for top in tree.body:
        if isinstance(top, ast.FunctionDef):
            if top.decorator_list or top.args.defaults or top.args.kw_defaults:
                raise ValueError('decorators and default expressions are unsupported')
        elif isinstance(top, (ast.Assign, ast.AnnAssign)):
            ast.literal_eval(top.value)
        elif not (isinstance(top, ast.Expr) and isinstance(top.value, ast.Constant) and isinstance(top.value.value, str)):
            raise ValueError('only functions and literal constants are allowed at module scope')
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.Global, ast.Nonlocal, ast.ClassDef,
                             ast.With, ast.AsyncFunctionDef, ast.AsyncWith, ast.Await)):
            raise ValueError('unsupported policy construct')
        if isinstance(node, ast.Name) and node.id.startswith('_'):
            raise ValueError('private names forbidden')
        if isinstance(node, ast.Attribute) and node.attr not in METHODS | MATH:
            raise ValueError('attribute outside restricted API')
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            defined = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
            if node.func.id not in SAFE_BUILTINS and node.func.id not in defined:
                raise ValueError('call outside restricted API: ' + node.func.id)
        if isinstance(node, ast.Call) and not isinstance(node.func, (ast.Name, ast.Attribute)):
            raise ValueError('indirect calls forbidden')
    return tree


class RestrictedPolicy:
    def __init__(self, source, timeout=1):
        validate_source(source)
        self.source, self.timeout = source, timeout

    def __call__(self, observed, context):
        try:
            result = subprocess.run([sys.executable, '-I', '-B', str(Path(__file__).resolve())],
                                    input=json.dumps({'source': self.source, 'observed': observed, 'context': context}),
                                    text=True, capture_output=True, timeout=self.timeout,
                                    env={'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8'})
        except subprocess.TimeoutExpired:
            raise TimeoutError('policy deadline exceeded') from None
        if result.returncode:
            raise ValueError('policy execution failed')
        if len(result.stdout) > 65536:
            raise ValueError('policy output exceeds limit')
        action = json.loads(result.stdout)
        if not isinstance(action, list) or any(not isinstance(item, str) for item in action):
            raise ValueError('policy must return a list of parent IDs')
        return action


def main():
    import resource
    resource.setrlimit(resource.RLIMIT_CPU, (2, 2))
    resource.setrlimit(resource.RLIMIT_FSIZE, (65536, 65536))
    value = json.load(sys.stdin)
    tree = validate_source(value['source'])
    namespace = {'__builtins__': SAFE_BUILTINS, 'math': math}
    exec(compile(tree, '<policy>', 'exec'), namespace)
    print(json.dumps(namespace['policy'](value['observed'], value['context']), allow_nan=False))


if __name__ == '__main__':
    main()
