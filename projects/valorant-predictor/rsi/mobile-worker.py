"""Frozen mobile discovery planner/evaluator. Scores capture coverage, not parity."""
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from mobile_capture import capture_probe,PROTOCOL
PROBES=PROTOCOL['probes']


def main():
    request=json.load(sys.stdin);work=Path(request['workspace']);visited=json.loads((work/'visited.json').read_text())
    if sys.argv[1]=='agent':
        probe=next((p for p in PROBES if p['id']not in visited),PROBES[-1]);(work/'probe.json').write_text(json.dumps(probe));return {'generation':{'probe':probe['id']},'observation':{'planned_probe':probe,'remaining':[p['id']for p in PROBES if p['id']not in visited]}}
    probe=json.loads((work/'probe.json').read_text());out='mobile-'+str(len(list(work.glob('mobile-*'))));result=capture_probe(work,probe,out)
    observed=result['status']=='captured'and result['facts'].get('viewport')==PROTOCOL['expected_content_viewport']
    if observed and probe['id']not in visited:visited.append(probe['id'])
    (work/'visited.json').write_text(json.dumps(visited));return {'score':len(visited)/len(PROBES),'observation':{'visited':visited,'remaining':[p['id']for p in PROBES if p['id']not in visited],'capture':out+'/observed.json','capture_status':result['status'],'error':result.get('error'),'content_viewport':result.get('facts',{}).get('viewport')}}


if __name__=='__main__':print(json.dumps(main(),ensure_ascii=False))
