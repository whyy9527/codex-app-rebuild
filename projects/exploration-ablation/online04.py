"""Deploy sealed policies with fixed interleaved source observations, no retries."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time
from replay04 import choose,atoms,digest
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--seal',required=True);p.add_argument('--cli',required=True);p.add_argument('--session',required=True);p.add_argument('--out',required=True);a=p.parse_args()
seal=json.loads(Path(a.seal).read_text());selected=seal['selected']
for arm,policy in selected.items():
 if digest(policy)!=seal['selected_digests'][arm]:raise ValueError('Sealed policy changed')
actions=json.loads(Path(__file__).with_name('actions04-online.json').read_text())
out=Path(a.out);out.mkdir(parents=True,exist_ok=False)
manifest={'selection_seal_sha256':hashlib.sha256(Path(a.seal).read_bytes()).hexdigest(),'selected_digests':seal['selected_digests'],
          'online_driver_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'source_driver_sha256':hashlib.sha256(Path(__file__).with_name('collect-guide04.mjs').read_bytes()).hexdigest(),
          'evaluator_sha256':hashlib.sha256(Path(__file__).with_name('replay04.py').read_bytes()).hexdigest(),'actions':actions,'order':['replay_feedback','no_replay_feedback','no_replay_feedback','replay_feedback']}
(out/'before-online-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
observations={k:{'actions':[{'id':x['id'],'label':x['label']} for x in actions],'visits':{},'revealed':[]} for k in selected}
found={k:set() for k in selected};traces=[];root_hash=seal['root_snapshot_sha256']
for step,arm in enumerate(manifest['order'],1):
 observation=observations[arm];action_id=choose(selected[arm],observation);action=next(x for x in actions if x['id']==action_id)
 action_file=out/f'{step:02}-{arm}-action.json';action_file.write_text(json.dumps([action],ensure_ascii=False,indent=2)+'\n')
 target=out/f'{step:02}-{arm}';start=time.monotonic()
 command=['node',str(Path(__file__).with_name('collect-guide04.mjs')),'--cli',a.cli,'--session',a.session,'--actions',str(action_file),'--out',str(target)]
 result=subprocess.run(command,text=True,capture_output=True)
 (out/f'{step:02}-collector.log').write_text(result.stdout+result.stderr)
 if result.returncode:raise RuntimeError('Source action unavailable; preserve prior traces, no replacement')
 before=json.loads((target/(action_id+'-before.json')).read_text());after=json.loads((target/(action_id+'-after.json')).read_text())
 current_hash=hashlib.sha256(before['snapshot'].encode()).hexdigest()
 if root_hash is None:root_hash=current_hash
 if root_hash!=current_hash:raise ValueError('Online source roots differ; stop causal scoring')
 actual=atoms(after)-atoms(before);new=actual-found[arm];found[arm].update(new)
 observation['visits'][action_id]=observation['visits'].get(action_id,0)+1;observation['revealed'].append({'action':action_id,'atoms':sorted(actual)})
 traces.append({'step':step,'arm':arm,'action':action,'new_atoms':len(new),'total_atoms':len(found[arm]),'wall_seconds':time.monotonic()-start,'root_snapshot_sha256':current_hash,'before':str(target.relative_to(out)/(action_id+'-before.json')),'after':str(target.relative_to(out)/(action_id+'-after.json')),'revealed_atoms':sorted(actual)})
 (out/'progress.json').write_text(json.dumps({'traces':traces},ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'step':step,'arm':arm,'action':action_id,'new_atoms':len(new)}),flush=True)
report={'status':'observed','selected_digests':seal['selected_digests'],'counts':{k:len(v) for k,v in found.items()},'traces':traces,'matched_root_snapshot_sha256':root_hash,'product_quality':'not_measured','limitations':['One source guest context; identical visible roots do not prove identical hidden server/cache state','Semantic frontend-fact novelty proxy excludes geometry/CSS; not independent requirement count','One-level allocation, one sample, no model-driven answer generation','No product implementation A/B or actual visual/audio gain claim']}
(out/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
