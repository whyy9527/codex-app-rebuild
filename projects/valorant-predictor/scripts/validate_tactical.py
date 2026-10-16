"""Fail closed on generated runtime data before packaging."""
import hashlib
from tactical_contract import ROOT,MODELS,digest,strict_json,validate_graph,validate

def main():
 root=ROOT/'data/tactical';context=strict_json((root/'context.json').read_text());validate_graph(context);index=strict_json((root/'models.json').read_text())
 if index['scenario_id']!=context['id'] or set(index['models'])!=set(MODELS):raise ValueError('Tactical model index differs from frozen case')
 for channel,model in MODELS.items():
  record=index['models'][channel]
  if record['model']!=model:raise ValueError('Unexpected runtime model in index')
  if record['status']!='ready':
   if record['file'] is not None:raise ValueError('Unready model must not expose a plan')
   continue
  path=f'data/tactical/{channel}-plan.json'
  if record['file']!=path:raise ValueError('Unexpected plan path')
  content=(ROOT/path).read_bytes();value=strict_json(content.decode());errors=validate(value['plan'],context)
  if errors:raise ValueError('; '.join(errors))
  if hashlib.sha256(content).hexdigest()!=record['sha256'] or value['context_sha256']!=digest(context) or value['raw_plan_sha256']!=digest(value['plan']):raise ValueError('Tactical provenance digest mismatch')
  if value['kind']!='model_tactical_plan' or value['channel']!=channel or value['scenario_id']!=context['id'] or value['runtime_attestation']['model']!=model:raise ValueError('Runtime tactical identity differs')
 print('Tactical graph and all published plans validated')
if __name__=='__main__':main()
