"""Registered guide04 semantic replay-feedback experiment."""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import hashlib
from replay04 import load_world,replay,digest
spec=importlib.util.spec_from_file_location('worker',Path(__file__).with_name('model-worker.py'));worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--codex',required=True);p.add_argument('--registration',required=True);p.add_argument('--world',required=True);p.add_argument('--out',required=True);a=p.parse_args()
out=Path(a.out);out.mkdir(parents=True,exist_ok=False)
registration=json.loads(Path(a.registration).read_text())
for name, expected in registration['files'].items():
    if hashlib.sha256(Path(name).read_bytes()).hexdigest()!=expected:raise ValueError('Frozen source training evidence changed')
world=load_world(a.world)
if digest(world)!=registration['world_digest']:raise ValueError('Registered replay world changed')
common={'task':'Generate exploration allocation policies for a source-App frontend reconstruction task. Use only this message, no tools. Return exactly 3 distinct policy records, most promising first.',
        'interface':'Each rule adds weight when its nonempty term occurs in the currently visible action label; subtract repeat_penalty times previous visits. Max score wins, ties in displayed action order. Policy cannot see unvisited outcomes. At most16 rules; weights[-10,10]; repeat_penalty[0,20]. Two visits to the root, one branch observation per visit.',
        'objective':'Find novel source frontend facts efficiently. Deduplicated semantic AX/text/actual enabled/checked facts are a limited proxy; geometry/CSS are retained but never rewarded. Do not claim product completeness.',
        'root_snapshot':world['root_snapshot'],'available_actions':world['actions'],'transfer':'Online actions use the same operation prefixes with different guide words; online outcomes are withheld.'}
schema=Path(__file__).with_name('policy-schema.json')
initial,ir=worker.call_worker('initial',json.dumps(common,ensure_ascii=False),out/'workers',schema,a.codex,registration['cli_binary_sha256'])
initial_replays=[replay(world,p) for p in initial]
control_input=dict(common,prior_candidates=initial,instruction='Revise the three policies from visible labels and prior candidates only. No evaluator feedback is supplied. Return preferred policy first.')
control,cr=worker.call_worker('no-replay-revision',json.dumps(control_input,ensure_ascii=False),out/'workers',schema,a.codex,registration['cli_binary_sha256'])
# Seal the no-feedback choice before giving any replay result to the other arm.
control_seal={'policy':control[0],'digest':digest(control[0]),'reason':'Model preferred first candidate; no replay-feedback selection'}
(out/'control-seal.json').write_text(json.dumps(control_seal,ensure_ascii=False,indent=2)+'\n')
full_input=dict(common,prior_candidates=initial,replay_feedback=initial_replays,instruction='Use actual revealed replay feedback to revise the policies. Do not infer outcomes outside these recorded traces. Return3 revised policies.')
full,fr=worker.call_worker('replay-revision',json.dumps(full_input,ensure_ascii=False),out/'workers',schema,a.codex,registration['cli_binary_sha256'])
pool=initial+full;scored=[replay(world,p) for p in pool];best=max(range(len(pool)),key=lambda i:scored[i]['score'])
selected={'replay_feedback':pool[best],'no_replay_feedback':control[0]}
seal={'baseline_commit':registration['baseline_commit'],'registration_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
      'world_digest':digest(world),'root_snapshot_sha256':hashlib.sha256(world['root_snapshot'].encode()).hexdigest(),'selected':selected,'selected_digests':{k:digest(v) for k,v in selected.items()},
      'initial_candidates':initial,'control_candidates':control,'replay_candidates':full,'replay_scores':scored,
      'control_post_seal_replay':replay(world,control[0]),'runtime_receipts':[ir,cr,fr],
      'online_status':'not_run; policy sealed before any online heldout action','product_quality_status':'not_measured'}
(out/'selection-seal.json').write_text(json.dumps(seal,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'sealed':True,'selected_digests':seal['selected_digests'],'replay_scores':[s['score'] for s in scored],'control_post_seal_score':seal['control_post_seal_replay']['score']}))
