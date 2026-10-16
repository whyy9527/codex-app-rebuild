"""Use the one remaining call per model from the already approved shared ledger."""
import argparse,os,json,re,subprocess,tempfile,hashlib
from pathlib import Path
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor,as_completed
from urllib.error import URLError
from tactical_contract import ROOT,MODELS,digest,strict_json
from veto_contract import schema,inputs,prompt,validate
from run_api_models import PROVIDERS,request
from run_tactical_models import reserve,approval,write,MAX_OUTPUT

def run(channel,context,out,approved):
 rows=inputs(context,channel);text=prompt(context,rows);sch=schema(context);messages=[{'role':'user','content':text}]
 # Additional schema is included in the reservation bound for the CLI adapter.
 bounded=messages+[{'role':'user','content':json.dumps(sch,ensure_ascii=False)}] if channel=='codex' else messages
 entry=reserve(out,channel,bounded,approved);directory=out/channel/f'attempt-{entry["attempt"]}';directory.mkdir(exist_ok=False);write(directory/'messages.json',messages);write(directory/'schema.json',sch);write(directory/'veto-input.json',{'context':context,'cases':rows});(directory/'prompt.txt').write_text(text)
 try:
  if channel=='codex':
   result=(directory/'last-message.json').resolve();env=os.environ.copy()
   for key in ['OPENAI_API_KEY','DEEPSEEK_API_KEY','ARK_API_KEY','MIMO_API_KEY']:env.pop(key,None)
   args=['codex','exec','--skip-git-repo-check','--ephemeral','--sandbox','read-only','--color','never','--model',MODELS[channel],'-c','model_reasoning_effort="high"','--output-schema',str((directory/'schema.json').resolve()),'--output-last-message',str(result),'-']
   with tempfile.TemporaryDirectory(prefix='valorant-veto-worker-') as temp:completed=subprocess.run(args,input=text,text=True,capture_output=True,cwd=temp,env=env,timeout=600)
   (directory/'stdout.log').write_text(completed.stdout);(directory/'stderr.log').write_text(completed.stderr)
   if completed.returncode:raise RuntimeError('CLI generation failed; no calls remain')
   match=re.search(r'OpenAI Codex[^\n]*\n-+\n(.*?)\n-+',completed.stderr,re.S);header=match[1] if match else '';fields=dict(re.findall(r'^([^:\n]+):\s*([^\n]+)',header,re.M))
   if fields.get('model')!=MODELS[channel] or fields.get('reasoning effort')!='high' or fields.get('provider')!='openai' or fields.get('sandbox')!='read-only':raise RuntimeError('CLI runtime identity mismatch')
   original=result.read_text();attestation={'provider':'openai_chatgpt_cli','model':fields['model'],'reasoning_effort':'high','startup_header_sha256':hashlib.sha256(header.encode()).hexdigest()}
  else:
   config=PROVIDERS[channel];key=os.environ.get(config['key'])
   if not key:raise RuntimeError('Provider credential unavailable')
   catalog=request(config['base']+'/models',key,timeout=30);matches=[r for r in catalog.get('data',[]) if r.get('id')==MODELS[channel]]
   if len(matches)!=1 or config['display'] and matches[0].get('name')!=config['display']:raise RuntimeError('Exact model unavailable')
   write(directory/'catalog-entry.json',matches[0]);body={'model':MODELS[channel],'messages':messages,'max_tokens':MAX_OUTPUT,'thinking':{'type':'enabled'}}
   if channel!='mimo':body.update(response_format={'type':'json_object'},reasoning_effort='high')
   write(directory/'request-without-credentials.json',body);response=request(config['base']+'/chat/completions',key,body,timeout=600);write(directory/'response.json',response)
   if response.get('model')!=MODELS[channel]:raise RuntimeError('Provider identity mismatch')
   choice=response.get('choices',[{}])[0];original=choice.get('message',{}).get('content') or '';(directory/'raw-plan.txt').write_text(original);attestation={'provider':channel,'model':response['model'],'response_id':response.get('id'),'usage':response.get('usage'),'finish_reason':choice.get('finish_reason'),'response_sha256':digest(response)}
   if choice.get('finish_reason')!='stop':raise RuntimeError('Incomplete generation; no calls remain')
  raw=strict_json(original);errors=validate(raw,context);write(directory/'validation.json',{'task':'map_veto','status':'valid' if not errors else 'rejected','errors':errors,'raw_sha256':hashlib.sha256(original.encode()).hexdigest()})
  if errors:raise RuntimeError('; '.join(errors))
  value={'kind':'model_veto_prediction','channel':channel,'context_sha256':digest(context),'input_cases':rows,'input_sha256':digest(rows),'raw_plan_sha256':digest(raw),'runtime_attestation':attestation,'created_at':datetime.now(timezone.utc).isoformat(),'plan':raw};write(ROOT/f'data/veto/{channel}.json',value);write(directory/'validated-veto.json',value);return {'channel':channel,'status':'ready','file':f'data/veto/{channel}.json','model':MODELS[channel]}
 except (ValueError,TypeError,RuntimeError,TimeoutError,URLError,subprocess.TimeoutExpired) as e:
  write(directory/'failure.json',{'task':'map_veto','error':str(e),'no_calls_remain':True});return {'channel':channel,'status':'failed','model':MODELS[channel],'error':str(e),'file':None}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--ledger-out',type=Path,required=True);p.add_argument('--approval-file',type=Path,required=True);a=p.parse_args();approved=approval(a.approval_file);context=strict_json((ROOT/'data/veto/context.json').read_text());results={};index={'context_sha256':digest(context),'models':{k:{'model':m,'status':'generating','file':None} for k,m in MODELS.items()}};write(ROOT/'data/veto/models.json',index)
 with ThreadPoolExecutor(max_workers=4) as pool:
  futures={pool.submit(run,ch,context,a.ledger_out,approved):ch for ch in MODELS}
  for future in as_completed(futures):
   channel=futures[future]
   try:result=future.result()
   except Exception as e:result={'channel':channel,'status':'failed','model':MODELS[channel],'error':str(e),'file':None}
   results[channel]=result;index['models'][channel]=result;write(ROOT/'data/veto/models.json',index);write(a.ledger_out/'veto-results.json',results);print(json.dumps(result,ensure_ascii=False),flush=True)
 if any(r['status']!='ready' for r in results.values()):raise SystemExit(1)
