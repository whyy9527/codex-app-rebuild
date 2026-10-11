"""Semantic novelty avoids rewarding geometry/scroll/render noise; retain raw facts."""
import hashlib,json,re,importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('base_replay',Path(__file__).with_name('replay.py'));base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
choose,validate_policy,digest=base.choose,base.validate_policy,base.digest
def atoms(receipt):
 result=set()
 for line in receipt['snapshot'].splitlines():
  line=re.sub(r'^\s*-\s*','',line).strip()
  if line and line!='img':result.add(json.dumps(['ax',line],ensure_ascii=False))
 for item in receipt.get('text_runs',[]):
  if item['text'].strip():result.add(json.dumps(['text',item['text'].strip()],ensure_ascii=False))
 for item in receipt['actions']:
  identity=[item.get(k)for k in ['role','test','name']]
  for field in ['enabled','checked']:
   if field in item:result.add(json.dumps([identity,field,item[field]],ensure_ascii=False,sort_keys=True))
 return result
def load_world(directory):
 directory=Path(directory);c=json.loads((directory/'collection.json').read_text());assert c['identical_root_snapshots'];roots=[];actions=[];outcomes={}
 for branch in c['branches']:
  a=branch['action'];before=json.loads((directory/branch['before']).read_text());after=json.loads((directory/branch['after']).read_text());assert before['path']==after['path']=='/guidebook/en/12';assert a['id'] not in outcomes
  roots.append(hashlib.sha256(before['snapshot'].encode()).hexdigest());actions.append({k:a[k]for k in ['id','label']});outcomes[a['id']]=dict(atoms=sorted(atoms(after)-atoms(before)),evidence=branch['after'],receipt_sha256=hashlib.sha256((directory/branch['after']).read_bytes()).hexdigest())
 assert roots==c['root_snapshot_hashes'] and len(set(roots))==1 and len(actions)==4
 return dict(root_snapshot=before['snapshot'],actions=actions,outcomes=outcomes)
def replay(world,policy,budget=2):
 validate_policy(policy);assert budget==2
 observation=dict(actions=world['actions'],visits={},revealed=[]);found=set();trace=[]
 for step in range(budget):
  action=choose(policy,json.loads(json.dumps(observation)));outcome=world['outcomes'][action];new=set(outcome['atoms'])-found;found.update(new);observation['visits'][action]=observation['visits'].get(action,0)+1;observation['revealed'].append(dict(action=action,atoms=outcome['atoms']));trace.append(dict(step=step+1,action=action,new_atoms=len(new),outcome=outcome))
 return dict(policy_digest=digest(policy),budget=budget,score=len(found),trace=trace,interpretation='Semantic frontend fact proxy; not independent requirements or product quality')
