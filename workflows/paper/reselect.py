"""Re-evaluate all actual previous proposals on explicit completed experiment history."""
import argparse
import json
from pathlib import Path
from capabilities.exploration.pool import select_pool


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--experiment',required=True)
    parser.add_argument('--out',required=True)
    args=parser.parse_args()
    report=json.loads(Path(args.experiment).read_text())
    developments=report['developments']
    accepted=[d for d in developments if d['selected']=='proposal']
    if not accepted: raise ValueError('explicit incumbent source cannot be inferred; no accepted proposal')
    incumbent=accepted[-1]['source']
    settings=developments[-1]['selection']['evaluation']
    result=select_pool(report['worlds'],incumbent,[d['source'] for d in developments if d['status']=='evaluated'],
                       width=settings['width'],max_calls=settings['max_calls'],max_rounds=settings['max_rounds'],penalty=settings['penalty'])
    target=Path(args.out)
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'candidates':len(result['candidates']),'selected':result['selected'],
                      'score':result['candidates'][result['selected']]['score'],'scope':result['scope']}))


if __name__=='__main__': main()
