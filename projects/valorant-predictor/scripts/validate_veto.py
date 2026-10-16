from tactical_contract import ROOT,MODELS,digest,strict_json
from veto_contract import validate,inputs

def main():
 root=ROOT/'data/veto';context=strict_json((root/'context.json').read_text());index=strict_json((root/'models.json').read_text())
 if index['context_sha256']!=digest(context) or set(index['models'])!=set(MODELS):raise ValueError('Veto context or model set mismatch')
 for channel,model in MODELS.items():
  row=index['models'][channel]
  if row['model']!=model:raise ValueError('Veto model differs')
  if row['status']!='ready':
   if row['file'] is not None:raise ValueError('Unready veto exposes a file')
   continue
  if row['file']!=f'data/veto/{channel}.json':raise ValueError('Unexpected veto path')
  value=strict_json((ROOT/row['file']).read_text());errors=validate(value['plan'],context)
  if errors:raise ValueError('; '.join(errors))
  if value['kind']!='model_veto_prediction' or value['channel']!=channel or value['runtime_attestation']['model']!=model:raise ValueError('Veto runtime identity differs')
  if value['context_sha256']!=digest(context) or value['raw_plan_sha256']!=digest(value['plan']) or value['input_sha256']!=digest(value['input_cases']) or value['input_cases']!=inputs(context,channel):raise ValueError('Veto provenance or retained series binding differs')
 print('Verified actual veto outputs for four models and eight cases each')
if __name__=='__main__':main()
