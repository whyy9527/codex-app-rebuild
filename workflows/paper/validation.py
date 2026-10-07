"""Evaluate frozen algorithms on new packing instances, without policy selection."""
import argparse
import hashlib
import json
from pathlib import Path
from capabilities.exploration.benchmark import split_cases,case_key
from runtime.packing import evaluate_packing,packing_protocol


def validate_programs(programs,*,seeds,count=8):
    if not programs or not seeds or len(set(seeds))!=len(seeds): raise ValueError('explicit programs and unique seeds required')
    instances=[]
    used=set()
    training=set()
    for seed in seeds:
        split=split_cases(seed=seed,count=count)
        training.update(case_key(c) for c in split['training'])
        for case in split['validation']:
            identifier=case_key(case)
            if identifier in used: raise ValueError('overlapping validation problems')
            used.add(identifier)
            instances.append({'seed':seed,'case':case,'case_digest':identifier})
    if used & training: raise ValueError('cross-seed training validation overlap')
    results={}
    for name,workspace in programs.items():
        source=(Path(workspace)/'pack.py').read_bytes()
        source_digest=hashlib.sha256(source).hexdigest()
        outcomes=[evaluate_packing(workspace,cases=[instance['case']]) for instance in instances]
        if hashlib.sha256((Path(workspace)/'pack.py').read_bytes()).hexdigest()!=source_digest:
            raise ValueError('candidate changed during validation')
        results[name]={'source':source.decode(),'source_digest':source_digest,'outcomes':outcomes,
                       'failures':sum(o['status']!='pass' for o in outcomes),
                       'mean_score':sum(o['score'] for o in outcomes)/len(outcomes)}
    return {'instances':instances,'protocol_digest':packing_protocol([i['case'] for i in instances]),
            'programs':results,'selection_allowed':False,
            'scope':'algorithm validation on new generated instances; not a policy or paper benchmark effect'}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--program',action='append',required=True,help='name=workspace')
    parser.add_argument('--seed',type=int,action='append',required=True)
    parser.add_argument('--count',type=int,default=8)
    parser.add_argument('--out',required=True)
    args=parser.parse_args()
    programs={}
    for item in args.program:
        name,path=item.split('=',1)
        if name in programs: raise ValueError('duplicate program name')
        programs[name]=Path(path)
    report=validate_programs(programs,seeds=args.seed,count=args.count)
    target=Path(args.out)
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({name:{k:v[k] for k in ('mean_score','failures','source_digest')} for name,v in report['programs'].items()}))


if __name__=='__main__': main()
