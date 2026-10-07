"""Inspect pending host-model prompts and submit explicit source responses."""
import argparse
import json
from pathlib import Path
from runtime.codex_worker import validate_reply
from runtime.policy_runtime import validate_source


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--directory',required=True)
    parser.add_argument('--source')
    parser.add_argument('--rationale')
    parser.add_argument('--request-digest')
    args=parser.parse_args()
    paths=[path for path in Path(args.directory).glob('*.json')
           if not path.name.endswith('.response.json') and not path.with_suffix('.response.json').exists()]
    if len(paths)!=1: raise ValueError('require exactly one pending request')
    path=paths[0]
    request=json.loads(path.read_text())
    if args.source:
        if args.request_digest!=request['request_digest']: raise ValueError('explicit request binding required')
        value={'source':Path(args.source).read_text(),'rationale':args.rationale}
        validate_reply(value)
        validate_source(value['source'],entry='pack' if request['role']=='discovery-generation' else 'policy')
        value['request_digest']=request['request_digest']
        path.with_suffix('.response.json').write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')
        print(json.dumps({'submitted':request['request_digest'],'role':request['role']}))
    else:
        prompt=request['prompt']
        data=json.loads(prompt[prompt.index('{'):])
        summary={'request_digest':request['request_digest'],'role':request['role']}
        if request['role']=='discovery-generation':
            summary.update(parent_source=data['parent_source'],context=data['context'],
                           observed=[{'id':node['id'],'parent':node.get('parent'),'score':node['score'],
                                      'evaluation':node.get('observation')} for node in data['visible_prefix']],
                           completed_worlds=len(data['completed_history']),training_cases=data['training_cases'])
        else:
            replay=data['current_replay']['candidates']['incumbent']
            summary.update(current_source=data['current_source'],replay_score=replay['score'],
                           worlds=[{'world_digest':w['world_digest'],'score':w['score'],
                                    'runs':[{k:r[k] for k in ('rho','calls','rounds','best_score','reason','valid')}
                                            for r in w['runs']]} for w in replay['worlds']],
                           previous_feedback=({k:data['previous_feedback'].get(k) for k in
                                               ('iteration','status','selected','rationale','structure_changed','rejection')}
                                              if data['previous_feedback'] else None),
                           previous_proposal_score=(data['previous_feedback']['selection']['candidates'].get('proposal',{}).get('score')
                                                    if data['previous_feedback'] else None),
                           completed_worlds=len(data['completed_worlds']))
        print(json.dumps(summary,ensure_ascii=False))


if __name__=='__main__': main()
