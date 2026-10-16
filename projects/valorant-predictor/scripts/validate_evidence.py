"""Build gate: validate evidence content identity and unchanged legacy predictions."""
import hashlib,json
from evidence_pack import ROOT,validate_pack
pack=json.loads((ROOT/'data/evidence-v2.json').read_text());validate_pack(pack)
receipts=json.loads((ROOT/'data/forecast-inputs.json').read_text())
for row in receipts['models'].values():
 if hashlib.sha256((ROOT/'data'/row['file']).read_bytes()).hexdigest()!=row['sha256'] or row['used_evidence_v2']:raise ValueError('Legacy prediction changed or incorrectly attributed to new input')
print('Evidence v2 and four unchanged legacy forecast receipts validated')

from forecast_contract import validate_proposal,parse_completion,unwrap_proposal
from tactical_contract import MODELS
from evidence_pack import digest
import subprocess
index=json.loads((ROOT/'data/forecast-v2/models.json').read_text())
for channel,row in index['models'].items():
 if row['status']!='ready':continue
 path=ROOT/row['file'];value=json.loads(path.read_text())
 if hashlib.sha256(path.read_bytes()).hexdigest()!=row['sha256'] or value['input_sha256']!=pack['content_sha256'] or value['channel']!=channel or value['method']!='single_evidence_analysis_no_persona':raise ValueError('V2 output provenance mismatch')
 validate_proposal(value['selected'],pack)
 raw,_=parse_completion((ROOT/f'data/forecast-v2/raw/{channel}-analysis.json').read_text());raw,_=unwrap_proposal(raw)
 if raw!=value['selected']:raise ValueError('Published decision differs from actual raw model answer')
 if len(value['runtime_attestations'])!=(1 if value.get('review_status')=='failed_limit_reached' else 2) or any(a['model']!=MODELS[channel] for a in value['runtime_attestations']):raise ValueError('V2 actual runtime model mismatch')
 actual=json.loads(subprocess.check_output(['node',str(ROOT/'scripts/compute_v2.mjs')],input=json.dumps(value['selected']).encode()))
 if actual!=value['computed']:raise ValueError('V2 distribution/draw mismatch')
print('V2 model manifest and every ready output validated')
