"""Replay public model decisions; validate the chain, not its forecast accuracy."""
import hashlib,json
from causal_series import ROOT,MODEL,initial,apply_bp,apply_batch,digest
from causal_quality import quality_flags
MODELS={"codex":MODEL,"deepseek":"deepseek-flash","doubao":"doubao-seed-2-1-pro-260915","mimo":"mimo-v2.6-pro"}

def validate():
 manifest=ROOT/'data/causal/models.json'
 if not manifest.exists():return 0
 index=json.loads(manifest.read_text());pack=json.loads((ROOT/'data/evidence-v2.json').read_text());context=json.loads((ROOT/'data/causal/map-context.json').read_text());agents=json.loads((ROOT/'data/causal/agents.json').read_text())['agents'];count=0
 for channel,row in index['models'].items():
  if not row['file']:
   if row['status'] not in ['not_run','running','blocked']:raise ValueError('Missing model output marked complete')
   continue
  if channel not in MODELS or row['file']!='data/causal/'+channel+'.json':raise ValueError('Unapproved producer')
  path=ROOT/row['file'];raw=path.read_bytes()
  if hashlib.sha256(raw).hexdigest()!=row['sha256']:raise ValueError('Causal output hash mismatch')
  value=json.loads(raw)
  cases=value.get('cases',[value]);prior_winner=None;all_ready=len(cases)==2
  for case_index,part in enumerate(cases):
   teams=['VIT','100T'] if case_index==0 else ['LOUD',prior_winner]
   if part['teams']!=teams or (case_index and not prior_winner):raise ValueError('Grand final does not use own derived lower-final winner')
   if part.get('quality_flags',[])!=quality_flags(channel,part['records']):raise ValueError('Reviewed quality flag missing or bound to another decision chain')
   s=initial(pack,teams);frames=[]
   if part['kind'] not in ['actual_gpt_batched_causal_series','actual_model_batched_causal_series'] or part['channel']!=channel or part['evidence_sha256']!=pack['content_sha256'] or not part['calls']>=1 or (channel=='codex' and part.get('api_cny',0)!=0):raise ValueError('Causal scope or input mismatch')
   for record in part['records']:
    att=record['runtime_attestation']
    if att['model']!=MODELS[channel] or att['provider']!=('openai' if channel=='codex' else channel) or (channel=='codex' and att['reasoning_effort'] not in ['high','medium']):raise ValueError('Model runtime identity mismatch')
    if record['before']!=s or record['before_sha256']!=digest(s) or record['raw_output_sha256']!=digest(record['decision']):raise ValueError('Decision is not linked to the previous actual state')
    if s['stage']=='bp':after=apply_bp(s,record['decision'],pack)
    else:
     decision=record['decision'];validation=record.get('validation',{});partial=validation.get('status')=='partial';cap=validation.get('requested_batch_cap')
     if cap and (not isinstance(cap,int) or not 1<=len(decision['rounds']) or (not partial and len(decision['rounds'])>cap)):raise ValueError('Output exceeds declared batch window')
     if partial:
      accepted_count=validation['accepted_round_count']
      if not 0<accepted_count<len(decision['rounds']) or not validation['raw_output_unchanged']:raise ValueError('Invalid accepted prefix')
      decision={**decision,'rounds':decision['rounds'][:accepted_count]}
     after,new_frames,_=apply_batch(s,decision,context,agents,pack,allow_incomplete=partial or bool(cap));frames+=new_frames
    if after!=record['after'] or digest(after)!=record['after_sha256']:raise ValueError('Stored after-state differs from event replay')
    s=after;count+=1
   if s!=part['state'] or frames!=part['frames']:raise ValueError('Player frames diverge from validated events')
   if (part['status']=='ready')!=(s['stage']=='finished'):raise ValueError('Incomplete series marked finished')
   prior_winner=s['winner'];all_ready=all_ready and s['stage']=='finished'
   selected={a['agent'] for frame in frames if frame.get('lineup') for a in frame['lineup'].values()}
   for name in selected:
    row_agent=agents[name];path=ROOT/row_agent['image']
    if not path.exists() or not row_agent.get('sha256') or hashlib.sha256(path.read_bytes()).hexdigest()!=row_agent['sha256']:raise ValueError('Selected agent image missing or not verified')
  expected_ready=all_ready if 'cases' in value else cases[0]['status']=='ready'
  if (value['status']=='ready')!=expected_ready or row['status']!=value['status']:raise ValueError('Incomplete pair marked finished')
 for m in context['maps'].values():
  if hashlib.sha256((ROOT/m['image']).read_bytes()).hexdigest()!=m['image_sha256']:raise ValueError('Source map asset digest mismatch')
  if any(not all(0<=x<=1 for x in a['xy']) for a in m['areas'].values()):raise ValueError('Source region outside map')
 return count
if __name__=='__main__':print('Verified causal decision records:',validate())
