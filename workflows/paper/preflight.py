"""One bounded real CLI probe, never a catalog-based availability claim."""
import argparse
import json
from pathlib import Path
from runtime.codex_worker import CodexWorker
from runtime.policy_runtime import validate_source


def probe(worker):
    try:
        reply=worker.generate('Return source defining policy(observed, context) that returns [] and a brief rationale. Do not use tools.',role='preflight')
        receipt=reply['receipt']
        attestation=receipt.get('attestation',{})
        if receipt.get('status')!='pass' or not isinstance(attestation,dict) or not all(attestation.get(k) for k in ('model','provider','reasoning effort')):
            raise ValueError('runtime attestation required')
        validate_source(reply['source'])
        return {'available':True,'status':'pass','receipt':receipt}
    except Exception as error:
        receipt=worker.receipts[-1] if worker.receipts else None
        return {'available':False,'status':receipt['status'] if receipt and receipt['status']!='pass' else 'invalid',
                'error_type':type(error).__name__,'receipt':receipt}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--model',required=True)
    parser.add_argument('--effort',default='medium')
    parser.add_argument('--timeout',type=float,default=20)
    parser.add_argument('--out',required=True)
    args=parser.parse_args()
    worker=CodexWorker(model=args.model,effort=args.effort,timeout=args.timeout)
    result=probe(worker)
    target=Path(args.out)
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
    raise SystemExit(0 if result['available'] else 2)


if __name__=='__main__': main()
