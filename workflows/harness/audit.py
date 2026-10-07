"""Verify this harness phase's ten fixed acceptance pairs against their exact commits."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
from capabilities.exploration.ledger import verify_records


def audit(records):
    verify_records(records)
    log=subprocess.check_output(['git','log','--format=%H %s'],text=True)
    commits={int(m[2]):m[1] for line in log.splitlines() if (m:=re.match(r'([0-9a-f]+) feat: harness round (\d+) ',line))}
    rounds=[]
    for index in range(1,11):
        before_id=f'h{index:02}-before'+('-compat' if index==9 else '')
        after_id='h03-after-retry' if index==3 else f'h{index:02}-after'+('-compat' if index==9 else '')
        before=next(r for r in records if r['id']==before_id)
        after=next(r for r in records if r['id']==after_id)
        a,b=before['evaluation'],after['evaluation']
        if a['status']!='fail' or b['status']!='pass' or a['evaluator_digest']!=b['evaluator_digest'] or before['hypothesis']!=after['hypothesis']:
            raise ValueError('acceptance pair is not fixed fail to pass')
        if after['parent']!=before_id: raise ValueError('invalid pair ancestry')
        for name,expected in b['source_files'].items():
            raw=subprocess.check_output(['git','show',f'{commits[index]}:{name}'])
            if hashlib.sha256(raw).hexdigest()!=expected: raise ValueError('commit source mismatch: '+name)
        rounds.append({'round':index,'commit':commits[index],'before':before_id,'after':after_id,
                       'fixed_acceptance':True,'source_matches_commit':True})
    selected={r[k] for r in rounds for k in ('before','after')}
    return {'rounds':rounds,'other_records':[{'id':r['id'],'status':r['evaluation']['status']} for r in records if r['id'] not in selected]}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--receipts',required=True)
    parser.add_argument('--out',required=True)
    args=parser.parse_args()
    result=audit(json.loads(Path(args.receipts).read_text()))
    Path(args.out).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'verified_rounds':len(result['rounds']),'other_records':result['other_records']}))


if __name__=='__main__': main()
