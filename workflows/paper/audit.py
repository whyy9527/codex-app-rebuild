"""Verify paper-stage engineering evidence and summarize model response provenance."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
from capabilities.exploration.ledger import verify_records
from capabilities.exploration.ledger import digest
from capabilities.exploration.objective import select_policy
from runtime.policy_runtime import RestrictedPolicy


def engineering_audit(records):
    verify_records(records)
    log=subprocess.check_output(['git','log','--format=%H %s'],text=True)
    commits={}
    for line in log.splitlines():
        match=re.match(r'([0-9a-f]+) (?:feat|fix): paper round (\d+) ',line)
        if match: commits[int(match[2])]=match[1]
    rounds=[]
    for index in range(1,11):
        before=next(r for r in records if r['id']==f'p{index:02}-before')
        after=next(r for r in records if r['id']==f'p{index:02}-after')
        a,b=before['evaluation'],after['evaluation']
        if a['evaluator_digest']!=b['evaluator_digest'] or before['hypothesis']!=after['hypothesis']:
            raise ValueError('acceptance conditions differ within pair')
        if a['status']!='fail' or b['status']!='pass': raise ValueError('round did not verify change')
        mismatches=[]
        for name,expected in b['source_files'].items():
            actual=subprocess.run(['git','show',f'{commits[index]}:{name}'],capture_output=True)
            if actual.returncode or hashlib.sha256(actual.stdout).hexdigest()!=expected:
                mismatches.append(name)
        snapshots={}
        for name in mismatches:
            snapshot=Path(f'projects/paper-v2/round-{index:02}-worker-snapshot.py.txt')
            if name=='runtime/codex_worker.py' and snapshot.is_file():
                if hashlib.sha256(snapshot.read_bytes()).hexdigest()!=b['source_files'][name]:
                    raise ValueError('preserved snapshot does not match executed source')
                snapshots[name]=snapshot.as_posix()
        rounds.append({'round':index,'commit':commits[index],'before':a['status'],'after':b['status'],
                       'evaluator_digest':b['evaluator_digest'],'source_mismatches':mismatches,
                       'preserved_executed_snapshots':snapshots,
                       'record_ids':[before['id'],after['id']]})
    return rounds


def experiment_audit(experiment, *, replay=False):
    requests={}
    for request in experiment['requests']:
        identifier=digest({'role':request['role'],'prompt':request['prompt']})
        if identifier!=request['request_digest'] or request['response']['request_digest']!=identifier:
            raise ValueError('request response binding mismatch')
        if identifier in requests: raise ValueError('duplicate request')
        requests[identifier]=request
    revisions=[]
    previous=None
    for development in experiment['developments']:
        request=requests[development['model_receipt']['request_digest']]
        feedback=json.loads(request['prompt'][request['prompt'].index('{'):])
        if digest(feedback)!=development['feedback_digest']:
            raise ValueError('feedback provenance mismatch')
        if feedback['previous_feedback']!=previous:
            raise ValueError('feedback chain mismatch')
        source=development['source']
        if request['response']['source']!=source:
            raise ValueError('response source mismatch')
        if hashlib.sha256(source.encode()).hexdigest()!=development['model_receipt']['source_sha256']:
            raise ValueError('response source digest mismatch')
        if replay:
            settings=development['selection']['evaluation']
            result=select_policy(feedback['completed_worlds'],
                                 {'incumbent':RestrictedPolicy(feedback['current_source']),
                                  'proposal':RestrictedPolicy(source)},incumbent='incumbent',
                                 width=settings['width'],max_calls=settings['max_calls'],
                                 max_rounds=settings['max_rounds'],penalty=settings['penalty'],semantics=settings['semantics'])
            if result!=development['selection']:
                # JSON projects tuples as lists.
                if json.loads(json.dumps(result))!=development['selection']:
                    raise ValueError('replayed selection differs')
        revisions.append({'iteration':development['iteration'],'request_digest':request['request_digest'],
                          'feedback_verified':True,'source_verified':True,'replayed':replay,
                          'selected':development['selected']})
        previous=development
    policy_count=sum(r['role']=='policy-development' for r in requests.values())
    discovery_count=sum(r['role']=='discovery-generation' for r in requests.values())
    if policy_count!=experiment['policy_responses'] or discovery_count!=experiment['discovery_responses']:
        raise ValueError('response counts differ')
    if len(revisions)!=policy_count: raise ValueError('unaccounted policy response')
    for name,run in experiment['online_runs'].items():
        for node in run['nodes']:
            receipt=node['generation']
            request=requests[receipt['request_digest']]
            if hashlib.sha256(request['response']['source'].encode()).hexdigest()!=node['observation']['source_digest']:
                raise ValueError('evaluated discovery source mismatch')
            if experiment['programs'][f'{name}/{node["id"]}/pack.py']!=request['response']['source']:
                raise ValueError('program artifact mismatch')
    attempts=sum(len(run['nodes']) for run in experiment['online_runs'].values())
    if attempts!=experiment['generation_attempts'] or attempts-discovery_count!=experiment['reused_discovery_responses']:
        raise ValueError('generation attempt accounting mismatch')
    return revisions


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--receipts',required=True)
    parser.add_argument('--out',required=True)
    parser.add_argument('--experiment')
    parser.add_argument('--replay',action='store_true')
    args=parser.parse_args()
    report={'engineering_rounds':engineering_audit(json.loads(Path(args.receipts).read_text()))}
    if args.experiment:
        experiment=json.loads(Path(args.experiment).read_text())
        report['policy_revision_audit']=experiment_audit(experiment,replay=args.replay)
        report.update({key:experiment[key] for key in ('policy_responses','discovery_responses','selected_updates',
                                                      'structural_proposals','comparison','limitations')})
    Path(args.out).write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({'rounds':len(report['engineering_rounds']),
                      'mismatches':[r for r in report['engineering_rounds'] if r['source_mismatches']]}))


if __name__=='__main__': main()
