"""One-worker paper-compatible online rollout with resumable host-model requests."""
from copy import deepcopy
import fcntl
import json
import math
from pathlib import Path
import time
from capabilities.exploration.ledger import digest
from capabilities.exploration.online import copy_workspace, workspace_manifest
from runtime.policy_runtime import RestrictedPolicy


def save(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')
    temporary.replace(path)


class OnlineSession:
    def __init__(self, source, output, policy_source, *, max_calls=4):
        self.source, self.output = Path(source).resolve(), Path(output).resolve()
        if self.source == self.output or self.source in self.output.parents or self.output in self.source.parents:
            raise ValueError('input and output must not overlap')
        if isinstance(max_calls, bool) or not isinstance(max_calls, int) or max_calls < 1:
            raise ValueError('positive call budget required')
        self.policy = RestrictedPolicy(policy_source)
        self.output.mkdir(parents=True, exist_ok=True)
        self.path = self.output/'state.json'
        self.config = {'input_digest':digest(workspace_manifest(self.source)),
                       'policy_digest':digest(policy_source), 'max_calls':max_calls, 'width':1}
        if self.path.exists():
            if self.read()['config'] != self.config:
                raise ValueError('resume configuration differs from frozen run')
        else:
            copy_workspace(self.source, self.output/'root')
            save(self.path, {'config':self.config, 'nodes':[], 'pending':None, 'done':False, 'rounds':0})

    def read(self):
        return json.loads(self.path.read_text())

    def advance(self, agent, evaluator):
        with (self.output/'lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return self._advance(agent, evaluator)

    def _advance(self, agent, evaluator):
        state = self.read()
        if state['done']:
            return state
        observed = [{'id':'root','parent':None,'score':0.0}] + deepcopy(state['nodes'])
        parents = {node['parent'] for node in observed}
        legal = [node['id'] for node in observed if node['id']=='root' or node['id'] not in parents]
        context = {'width':1, 'remaining_calls':self.config['max_calls']-len(state['nodes']),
                   'remaining_rounds':self.config['max_calls']-state['rounds'], 'rho':0, 'legal_parents':legal}
        if not context['remaining_calls']:
            state.update(done=True, reason='call_budget')
            save(self.path,state)
            return state
        if state['pending'] is None:
            action = self.policy(observed, context)
            if len(action)>1 or any(parent not in legal for parent in action):
                raise ValueError('illegal policy action')
            if not action:
                state.update(done=True, reason='stopped')
                save(self.path,state)
                return state
            identifier, parent = f'n{len(state["nodes"])+1:04}', action[0]
            copy_workspace(self.output/parent, self.output/identifier)
            state['pending'] = {'id':identifier,'parent':parent}
            save(self.path,state)
        pending = state['pending']
        work = self.output/pending['id']
        began = time.monotonic()
        try:
            generation = agent(work, observed, {**context,'parent':pending['parent']})
            evaluation = evaluator(work)
            score = evaluation['score']
            if isinstance(score,bool) or not isinstance(score,(int,float)) or not math.isfinite(score) or score<0:
                raise ValueError('invalid score')
            if evaluation['status']!='pass': score=0.0
        except Exception as error:
            generation, evaluation, score = None, {'status':'error','error_type':type(error).__name__}, 0.0
        node = {**pending,'score':score,'observation':evaluation,'generation':generation,
                'workspace_digest':digest(workspace_manifest(work)),
                'cost':{'generation_calls':1,'active_wall_seconds':round(time.monotonic()-began,6),
                        'model_tokens':None,'model_cost':None}}
        state['nodes'].append(node)
        state['rounds'] += 1
        state['pending'] = None
        save(self.path,state)
        return state
