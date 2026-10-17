"""Export a versioned snapshot of authorized final workers after replaying every decision."""
import argparse,datetime,hashlib,json
from pathlib import Path
import causal_series as c
from causal_quality import quality_flags
from evidence_pack import validate_pack
from paid_causal import approved_cap
from validate_causal import MODELS

def verify(value,pack,channel):
 if value.get('case_id')!='gf' or value.get('version_kind')!='postmatch_rerun' or value.get('exclude_from_original_prematch_accuracy') is not True or value.get('match_id')!='115576361461208331':raise ValueError('Wrong final version')
 if value['channel']!=channel or value['evidence_sha256']!=pack['content_sha256'] or value['teams']!=['LOUD','VIT']:raise ValueError('Wrong model/input/teams')
 if value['quality_flags']!=quality_flags(channel,value['records']):raise ValueError('Quality notes differ')
 context=json.loads((c.ROOT/'data/causal/map-context.json').read_text());agents=json.loads((c.ROOT/'data/causal/agents.json').read_text())['agents'];s=c.initial(pack,['LOUD','VIT']);frames=[]
 for record in value['records']:
  att=record['runtime_attestation']
  if att['model']!=MODELS[channel] or att['provider']!=('openai' if channel=='codex' else channel):raise ValueError('Runtime identity mismatch')
  if channel=='codex' and att['reasoning_effort']!=('high' if s['stage']=='bp' else 'medium'):raise ValueError('Actual GPT effort differs')
  if record['before']!=s or record['before_sha256']!=c.digest(s) or record['raw_output_sha256']!=c.digest(record['decision']):raise ValueError('Broken prior state chain')
  if s['stage']=='bp':after=c.apply_bp(s,record['decision'],pack)
  else:
   d=record['decision'];v=record['validation'];cap=v.get('requested_batch_cap');partial=v.get('status')=='partial'
   if cap!=(6 if channel=='codex' else 3) or not d['rounds'] or (not partial and len(d['rounds'])>cap):raise ValueError('Invalid batch cap')
   if partial:
    n=v['accepted_round_count']
    if not 0<n<len(d['rounds']) or n>cap or not v['raw_output_unchanged']:raise ValueError('Invalid accepted prefix')
    d={**d,'rounds':d['rounds'][:n]}
   after,new_frames,_=c.apply_batch(s,d,context,agents,pack,allow_incomplete=True);frames+=new_frames
  if after!=record['after'] or c.digest(after)!=record['after_sha256']:raise ValueError('After-state differs')
  s=after
 if s!=value['state'] or frames!=value['frames'] or s['stage']!='finished' or value['status']!='ready' or max(s['series_score'])!=3:raise ValueError('Incomplete or divergent final')
 return len(value['records'])

def export(root):
 root=root.resolve();approved_cap(root);a=json.loads((root/'approval.json').read_text());pack=json.loads((root/'evidence.json').read_text());validate_pack(pack)
 if a['evidence_sha256']!=pack['content_sha256']:raise ValueError('Approval input differs')
 base=c.ROOT/'data/gf-postmatch';version=base/root.name;version.mkdir(parents=True,exist_ok=True)
 evidence=version/'evidence.json';evidence.write_bytes((root/'evidence.json').read_bytes());rows={}
 for channel in ['codex','mimo','doubao']:
  out=root/channel;status=json.loads((out/'worker-status.json').read_text());row={'status':status['status'],'file':None}
  if status['status']=='finished':
   raw=(out/'public.json').read_bytes();v=json.loads(raw);verify(v,pack,channel)
   if v['prediction_version']!=root.name or v['information_cutoff']!=pack['frozen_at']:raise ValueError('Wrong version cutoff')
   destination=version/(channel+'.json');destination.write_bytes(raw);row.update(status='ready',file=str(destination.relative_to(c.ROOT)),sha256=hashlib.sha256(raw).hexdigest(),recorded_at=status['finished_at'],winner=v['state']['winner'],score=v['state']['series_score'])
  elif status['status']=='blocked':row['reason']='请求被服务商拒绝（HTTP 402，具体原因未保留）' if '402' in status.get('error','') else '本轮因运行错误停止，未发布不完整结果'
  rows[channel]=row
 index={'kind':'isolated_postmatch_final_manifest','version_kind':'postmatch_rerun','version':root.name,'information_cutoff':pack['frozen_at'],'evidence_sha256':pack['content_sha256'],'evidence_file':str(evidence.relative_to(c.ROOT)),'match_id':'115576361461208331','teams':['LOUD','VIT'],'snapshot_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exclude_from_original_prematch_accuracy':True,'models':rows}
 c.write(base/'models.json',index);print(json.dumps({k:v['status'] for k,v in rows.items()}))
def validate_snapshot():
 index=json.loads((c.ROOT/'data/gf-postmatch/models.json').read_text());pack=json.loads((c.ROOT/index['evidence_file']).read_text());validate_pack(pack)
 if set(index['models'])!={'codex','mimo','doubao'} or index['kind']!='isolated_postmatch_final_manifest' or index['information_cutoff']!=pack['frozen_at'] or index['evidence_sha256']!=pack['content_sha256'] or index['teams']!=['LOUD','VIT'] or index['exclude_from_original_prematch_accuracy'] is not True:raise ValueError('Wrong published final input')
 for channel,row in index['models'].items():
  if channel not in ['codex','mimo','doubao']:raise ValueError('Unapproved final provider')
  if row['status']!='ready':
   if row.get('file') or row['status'] not in ['running','blocked']:raise ValueError('Incomplete result published')
   continue
  raw=(c.ROOT/row['file']).read_bytes()
  if hashlib.sha256(raw).hexdigest()!=row['sha256']:raise ValueError('Published final digest mismatch')
  value=json.loads(raw)
  if value['prediction_version']!=index['version'] or value['information_cutoff']!=index['information_cutoff']:raise ValueError('Published final version mismatch')
  verify(value,pack,channel)
 print('Verified isolated final snapshot')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path);p.add_argument('--validate',action='store_true');a=p.parse_args();validate_snapshot() if a.validate else export(a.root)
