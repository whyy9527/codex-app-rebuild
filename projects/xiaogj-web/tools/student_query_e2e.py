"""Shared query mold: request live native actions or compare their actual facts.

Replay awaits the current Codex cua_repl driver, not a nested browser or agent.
Private queries, expected IDs and native captures stay in ignored local paths.
"""
import argparse
import json
from pathlib import Path
import time
import uuid

from capabilities.exploration.storage import digest
from capabilities.rebuild.contracts import local_file


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('replay', 'compare'))
    parser.add_argument('--workspace', default='.')
    parser.add_argument('--side', choices=('reference', 'candidate'), default='candidate')
    parser.add_argument('--observed')
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    root = Path(args.workspace).resolve()
    base = 'projects/xiaogj-web/'
    book = json.loads(local_file(root, base+'private/rsi-seed/cases.json').read_text())
    contract = json.loads(local_file(root, base+'student-query-scenarios.json').read_text())
    out = local_file(root, args.out, must_exist=False)
    out.mkdir(parents=True, exist_ok=False)
    identity = digest({'contract': contract, 'book': book})
    if args.operation == 'replay':
        bridge = root / base / 'private/e2e-bridge'
        bridge.mkdir(parents=True, exist_ok=True)
        actual = {'rows': []}
        for case in book['cases']:
            key = uuid.uuid4().hex
            captures = out / case['id']
            captures.mkdir()
            request = {'id': key, 'side': args.side, 'out': str(captures),
                       'cases': [{'id': case['id'], 'query': case['query']}]}
            (bridge / (key+'.request.json')).write_text(json.dumps(request, ensure_ascii=False))
            reply = bridge / (key+'.reply.json')
            deadline = time.monotonic()+240
            while not reply.exists() and time.monotonic()<deadline:
                time.sleep(.2)
            response = json.loads(reply.read_text()) if reply.exists() else {'error': 'Native UI replay unavailable: timeout'}
            if 'error' in response:
                actual['error'] = response['error']
                break
            actual['rows'].extend(response['rows'])
            actual['restored'] = response['restored']
        result = {'side': args.side, 'contract_digest': identity, 'actual': actual}
        (out/'observed.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
        print(json.dumps({'observed': args.out+'/observed.json', 'status': 'unavailable' if 'error' in actual else 'recorded'}))
        return 2 if 'error' in actual else 0
    observed = json.loads(local_file(root, args.observed).read_text())
    if observed.get('contract_digest') != identity:
        raise ValueError('Shared contract or private fixture changed; do not compare stale captures')
    actual = observed['actual']
    rows = []
    for case in book['cases']:
        found = next((r for r in actual.get('rows', []) if r['id']==case['id']), None)
        checks = {'baseline': found is not None and found['baseline']==book['baseline'],
                  'query-result': found is not None and found['result']==case['expectedResult'],
                  'reset-clears-input': found is not None and found['inputCleared'] is True,
                  'reset-retains-results': found is not None and found['afterReset']==case['expectedResult']}
        rows.extend({'id':case['id']+'/'+key,'status': 'pass' if value else ('unavailable' if found is None else 'fail')}
                    for key,value in checks.items())
    rows.append({'id':'restored-baseline','status': 'unavailable' if 'restored' not in actual
                 else ('pass' if actual['restored']==book['baseline'] else 'fail')})
    status = ('unavailable' if 'error' in actual else
              ('pass' if all(r['status']=='pass' for r in rows) else 'fail'))
    result = {'status':status,'side':observed['side'],'contract_digest':identity,'rows':rows,
              'scope':contract['scope'],'completion':'not evaluated; query mold is only part of the full rebuild'}
    (out/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if status=='pass' else (2 if status=='unavailable' else 1)


if __name__ == '__main__':
    raise SystemExit(main())
