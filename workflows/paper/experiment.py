"""Resumable paper-mechanism experiment with explicit host-model code responses."""
import argparse
import json
from pathlib import Path
from capabilities.exploration.comparison import compare_runs
from capabilities.exploration.development import develop_policy
from capabilities.exploration.export import redact
from capabilities.exploration.ledger import digest
from capabilities.exploration.online import workspace_manifest
from capabilities.exploration.session import OnlineSession, save
from runtime.discovery import ModelDiscovery
from runtime.packing import evaluate_packing, packing_protocol
from runtime.request_broker import FileWorker, NeedsResponse

SEED = '''def policy(observed, context):
    calls = len(observed) - 1
    limit = max(1, int(4 * (1 - .75 * context['rho']) + .9999))
    if calls >= limit: return []
    roots = [n for n in observed if n['parent'] == 'root']
    if len(roots) < 2: return ['root']
    parents = {n['parent'] for n in observed}
    leaves = [n for n in observed if n['id'] != 'root' and n['id'] not in parents]
    leaves.sort(key=lambda n: (-n['score'], n['id']))
    return [leaves[0]['id']]
'''


class Experiment:
    def __init__(self, source, output, *, iterations=10, max_calls=4):
        self.source, self.output = Path(source).resolve(), Path(output).resolve()
        if not self.source.is_dir() or not (self.source/'pack.py').is_file():
            raise ValueError('explicit packing input required')
        if self.source == self.output or self.source in self.output.parents or self.output in self.source.parents:
            raise ValueError('input and output must not overlap')
        if isinstance(iterations,bool) or not isinstance(iterations,int) or not 2<=iterations<=20:
            raise ValueError('iterations in [2,20] required')
        self.output.mkdir(parents=True,exist_ok=True)
        self.path = self.output/'experiment.json'
        self.worker = FileWorker(self.output/'requests')
        self.config = {'input_digest':digest(workspace_manifest(self.source)), 'iterations':iterations,
                       'max_calls':max_calls,'evaluation_protocol':packing_protocol(),
                       'model_transport':'interactive-codex-main-session','width':1,'semantics':'paper'}
        if self.path.exists():
            if self.read()['config'] != self.config: raise ValueError('experiment configuration changed')
        else:
            save(self.path,{'config':self.config,'phase':'online','online_cycle':1,'active_source':SEED,
                            'worlds':[],'developments':[],'done':False})

    def read(self): return json.loads(self.path.read_text())

    def step(self):
        state = self.read()
        if state['done']: return state
        phase = state['phase']
        if phase in ('online','control-fixed','control-updated'):
            name = f'online-{state["online_cycle"]}' if phase=='online' else phase
            source = SEED if phase=='control-fixed' else state['active_source']
            session = OnlineSession(self.source,self.output/name,source,max_calls=self.config['max_calls'])
            worker=FileWorker(self.output/'requests',scope=name)
            result = session.advance(ModelDiscovery(worker,history=state['worlds']),evaluate_packing)
            if result['done']:
                if phase=='online':
                    if not result['nodes'] or max(n['score'] for n in result['nodes'])<=0:
                        raise ValueError('online world has no positive evaluated candidate; repair required')
                    state['worlds'].append(result['nodes'])
                    state['phase']='dream'
                elif phase=='control-fixed': state['phase']='control-updated'
                else:
                    fixed = json.loads((self.output/'control-fixed/state.json').read_text())
                    state['comparison']=compare_runs(fixed,result)
                    state.update(done=True,phase='complete')
        elif phase=='dream':
            previous = state['developments'][-1] if state['developments'] else None
            worker=FileWorker(self.output/'requests',scope=f'development-{len(state["developments"])+1}')
            development = develop_policy(worker,state['worlds'],state['active_source'],
                                         previous_feedback=previous,width=1,
                                         candidate_sources=[d['source'] for d in state['developments'] if d['status']=='evaluated'],
                                         max_calls=self.config['max_calls'],max_rounds=self.config['max_calls'])
            development['iteration']=len(state['developments'])+1
            development['history_worlds']=len(state['worlds'])
            state['developments'].append(development)
            state['active_source']=development['selected_source']
            count = len(state['developments'])
            if count >= self.config['iterations']: state['phase']='control-fixed'
            elif count==(self.config['iterations']+1)//2:
                state.update(phase='online',online_cycle=2)
        else: raise ValueError('unknown phase')
        save(self.path,state)
        return state

    def report(self):
        state = self.read()
        if not state['done']: raise ValueError('experiment incomplete')
        requests=[]
        for path in sorted((self.output/'requests').glob('*.json')):
            if path.name.endswith('.response.json'): continue
            response=path.with_suffix('.response.json')
            if response.exists():
                request=json.loads(path.read_text())
                requests.append({'request_digest':request['request_digest'],'role':request['role'],
                                 'prompt':request['prompt'],
                                 **({'scope':request['scope']} if 'scope' in request else {}),
                                 'response':json.loads(response.read_text())})
        programs={}
        for path in sorted(self.output.glob('*/n*/pack.py')):
            programs[path.relative_to(self.output).as_posix()]=path.read_text()
        runs={name:json.loads((self.output/name/'state.json').read_text())
              for name in ('online-1','online-2','control-fixed','control-updated')}
        call_count=sum(len(run['nodes']) for run in runs.values())
        result=redact({'config':state['config'],'developments':state['developments'], 'worlds':state['worlds'],
                       'comparison':state['comparison'],'requests':requests,'programs':programs,'online_runs':runs,
                       'generation_attempts':call_count,
                       'reused_discovery_responses':call_count-sum(r['role']=='discovery-generation' for r in requests),
                       'policy_responses':sum(r['role']=='policy-development' for r in requests),
                       'discovery_responses':sum(r['role']=='discovery-generation' for r in requests),
                       'selected_updates':sum(d['selected']!='incumbent' for d in state['developments']),
                       'structural_proposals':sum(d['structure_changed'] is True for d in state['developments']),
                       'runtime_model':None,'model_tokens':None,'model_cost':None,
                       'limitations':['interactive main-session synthesis, not unattended CLI execution',
                                      'host model context is not isolated between experiment arms',
                                      'identical prompt bindings reuse response artifacts; generation attempts are not independent model calls',
                                      'model identity and token cost not independently attested',
                                      'packing workload is not one of the paper benchmark reproductions',
                                      'comparison uses the same training cases, not held-out tasks',
                                      'frozen-history full-pool reselection does not establish new-task gains',
                                      'one paired run is not a statistical efficiency claim']})
        save(self.output/'report.json',result)
        return result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--input',required=True)
    parser.add_argument('--out',required=True)
    parser.add_argument('--iterations',type=int,default=10)
    parser.add_argument('--max-calls',type=int,default=4)
    args=parser.parse_args()
    experiment=Experiment(args.input,args.out,iterations=args.iterations,max_calls=args.max_calls)
    try:
        while True:
            state=experiment.step()
            if state['done']:
                report=experiment.report()
                print(json.dumps({'status':'complete','policy_responses':report['policy_responses'],
                                  'discovery_responses':report['discovery_responses'],
                                  'selected_updates':report['selected_updates'],'comparison':report['comparison']}))
                break
    except NeedsResponse as waiting:
        request=json.loads(waiting.path.read_text())
        print(json.dumps({'status':'needs_model_response','request_file':waiting.path.relative_to(experiment.output).as_posix(),
                          'request_digest':request['request_digest'],'role':request['role'],
                          'phase':experiment.read()['phase'],'completed_revisions':len(experiment.read()['developments'])}))


if __name__=='__main__': main()
