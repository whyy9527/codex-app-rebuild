"""Actual deep source discovery/evaluation; frozen probes are evidence-derived."""
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from deep_capture import capture_probe
PROBES=json.loads((Path(__file__).resolve().parents[1]/'contracts/deep-probes.json').read_text())['probes']


def main():
    request=json.load(sys.stdin);work=Path(request['workspace']);visited=json.loads((work/'visited.json').read_text())
    if sys.argv[1]=='agent':
        probe=next((p for p in PROBES if p['id']not in visited),PROBES[-1]);(work/'probe.json').write_text(json.dumps(probe))
        return {'generation':{'probe':probe['id']},'observation':{'planned_probe':probe,'known_remaining':[p['id']for p in PROBES if p['id']not in visited]}}
    probe=json.loads((work/'probe.json').read_text());out='deep-'+str(len(list(work.glob('deep-*'))));result=capture_probe(work,probe,out)
    state=result['states'].get(probe['id'],{});text='\n'.join(state.get('accessible_text',[]));observed=bool(result['steps']) and len(text)>700 and not result.get('error')
    if observed and probe['id']not in visited:visited.append(probe['id'])
    (work/'visited.json').write_text(json.dumps(visited));return {'score':len(visited)/len(PROBES),'observation':{'visited':visited,'remaining':[p['id']for p in PROBES if p['id']not in visited],'capture':out+'/observed.json','capture_status':result['status'],'error':result.get('error'),'text_characters':len(text),'controls':result.get('controls',[]),'links':result.get('links',[])}}


if __name__=='__main__':print(json.dumps(main(),ensure_ascii=False))
