"""Audit ten engineering pairs and summarize fixed validation without invented gains."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
from capabilities.exploration.ledger import verify_records
from runtime.packing import packing_protocol


def interpret_validation(report,*,baseline):
    programs=report['programs']
    if report['selection_allowed'] or baseline not in programs: raise ValueError('validation scope invalid')
    instances=report['instances']
    if not instances: raise ValueError('empty validation')
    for program in programs.values():
        if hashlib.sha256(program['source'].encode()).hexdigest()!=program['source_digest']:
            raise ValueError('program source mismatch')
        outcomes=program['outcomes']
        if len(outcomes)!=len(instances): raise ValueError('unpaired outcomes')
        for instance,outcome in zip(instances,outcomes):
            if outcome['protocol_digest']!=packing_protocol([instance['case']]): raise ValueError('case protocol mismatch')
            if outcome['status']=='pass' and outcome['source_digest']!=program['source_digest']:
                raise ValueError('executed source mismatch')
        mean=sum(o['score'] for o in outcomes)/len(outcomes)
        if not math.isclose(mean,program['mean_score'],abs_tol=1e-12): raise ValueError('mean mismatch')
    pairs={}
    base=programs[baseline]['outcomes']
    for name,program in programs.items():
        if name==baseline: continue
        differences=[a['score']-b['score'] for a,b in zip(program['outcomes'],base)]
        wins=sum(d>1e-12 for d in differences)
        losses=sum(d < -1e-12 for d in differences)
        pairs[name]={'wins':wins,'ties':len(differences)-wins-losses,'losses':losses,
                     'mean_delta':sum(differences)/len(differences),
                     'conclusion':'no_observed_gain' if not wins and not losses else 'observed_pair_differences_only'}
    return {'cases':len(instances),'seeds':sorted({i['seed'] for i in instances}),'pairs':pairs,
            'policy_effect':'not_tested','statistical_generalization':'not_established'}


def audit_rounds(records):
    verify_records(records)
    log=subprocess.check_output(['git','log','--format=%H %s'],text=True)
    commits={int(m[2]):m[1] for line in log.splitlines()
             if (m:=re.match(r'([0-9a-f]+) feat: stage3 round (\d+) ',line))}
    rounds=[]
    for index in range(1,11):
        before=next(r for r in records if r['id']==f's{index:02}-baseline')
        after=next(r for r in records if r['id']==f's{index:02}-after')
        a,b=before['evaluation'],after['evaluation']
        if a['status']!='fail' or b['status']!='pass': raise ValueError('missing fail to pass')
        if a['evaluator_digest']!=b['evaluator_digest'] or before['hypothesis']!=after['hypothesis']:
            raise ValueError('acceptance changed within pair')
        if after['parent']!=before['id']: raise ValueError('broken pair ancestry')
        mismatches=[]
        for name,expected in b['source_files'].items():
            content=subprocess.run(['git','show',f'{commits[index]}:{name}'],capture_output=True)
            if content.returncode or hashlib.sha256(content.stdout).hexdigest()!=expected: mismatches.append(name)
        rounds.append({'round':index,'commit':commits[index],'before':before['id'],'after':after['id'],
                       'fixed_acceptance':True,'source_mismatches':mismatches})
    if any(r['source_mismatches'] for r in rounds): raise ValueError('source differs from round commit')
    selected={r[k] for r in rounds for k in ('before','after')}
    return {'rounds':rounds,'additional_records':[r['id'] for r in records if r['id'] not in selected]}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--receipts',required=True)
    parser.add_argument('--validation',required=True)
    parser.add_argument('--preflight',required=True)
    parser.add_argument('--out',required=True)
    args=parser.parse_args()
    result=audit_rounds(json.loads(Path(args.receipts).read_text()))
    result['validation']=interpret_validation(json.loads(Path(args.validation).read_text()),baseline='ffd')
    result['model_preflight']=json.loads(Path(args.preflight).read_text())
    result['model_strategy_revisions_this_stage']=0
    Path(args.out).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'verified_rounds':len(result['rounds']),'validation':result['validation'],
                      'model_available':result['model_preflight']['available']}))


if __name__=='__main__': main()
