"""Prepare or run one frozen four-model tactical case with an explicit budget.

No paid call on import or prepare. Original responses and failed attempts remain
private; only strictly validated, correctly attested plans can enter runtime data.
"""
import argparse,hashlib,json,os,re,subprocess,tempfile,fcntl
from datetime import datetime,timezone
from urllib.error import URLError
from pathlib import Path
from tactical_contract import ROOT,MODELS,LABELS,digest,strict_json,schema,prompt,validate,validate_graph,public_plan
from run_api_models import PROVIDERS,request
RATES={'deepseek':{'currency':'USD','input_per_million':.3,'output_per_million':1.2,'budget_cny_per_unit':8,'source':'https://api-docs.deepseek.com/quick_start/pricing/'},'doubao':{'currency':'CNY','input_per_million':6,'output_per_million':30,'budget_cny_per_unit':1,'source':'https://www.volcengine.com/product/doubao'},'mimo':{'currency':'CNY','input_per_million':3,'output_per_million':6,'budget_cny_per_unit':1,'source':'https://mimo.mi.com/docs/price/pay-as-you-go'}}
MAX_INPUT=24000;MAX_OUTPUT=12000;MAX_CALLS=2

def write(path,value):
 path.parent.mkdir(parents=True,exist_ok=True);temp=path.with_suffix(path.suffix+'.tmp');temp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n');temp.replace(path)
def estimate():
 rows={name:round(2*(MAX_INPUT*r['input_per_million']+MAX_OUTPUT*r['output_per_million'])/1e6*r['budget_cny_per_unit'],6) for name,r in RATES.items()}
 return {'api_upper_reservation_cny':sum(rows.values()),'per_provider_cny':rows,'max_input_tokens':MAX_INPUT,'max_output_tokens':MAX_OUTPUT,'max_calls_per_model':MAX_CALLS,'codex':'Existing ChatGPT CLI quota only; no OpenAI API request. Maximum two CLI executions.','rates':RATES,'fx_note':'USD multiplier 8 is a conservative budget reserve coefficient, not a quoted exchange rate.','approved':False}
def prepare(context,out):
 validate_graph(context);out.mkdir(parents=True,exist_ok=True);text=prompt(context)
 (out/'prompt.txt').write_text(text);write(out/'schema.json',schema(context));write(out/'context.json',context);write(out/'budget-estimate.json',estimate())
 write(out/'input-receipt.json',{'context_sha256':digest(context),'prompt_sha256':hashlib.sha256(text.encode()).hexdigest(),'model_ids':MODELS})
 return text

def approval(path):
 if path is None:raise ValueError('Explicit approval file is required before any model generation')
 value=strict_json(path.read_text())
 if value.get('approved') is not True or set(value.get('models',[]))!=set(MODELS):raise ValueError('Approval must explicitly cover these four exact models')
 if not isinstance(value.get('authorization'),str) or len(value['authorization'].strip())<8:raise ValueError('Retain the actual human authorization text')
 if not 0<value.get('max_total_cny',0)<=5 or value.get('max_calls_per_model')!=MAX_CALLS:raise ValueError('This batch is capped at CNY 5 and two calls per model')
 return value

def reserve(out,channel,body,approved):
 schema_overhead=len(json.dumps(schema(strict_json((out/'context.json').read_text())),ensure_ascii=False).encode()) if channel=='codex' else 0
 input_bound=len(json.dumps(body,ensure_ascii=False).encode())+schema_overhead+512
 if input_bound>MAX_INPUT:raise ValueError('Conservative UTF-8 input token bound exceeds cap: '+str(input_bound))
 with (out/'ledger.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);path=out/'ledger.json';ledger=strict_json(path.read_text()) if path.exists() else {'calls':{},'reserved_cny':0,'entries':[]}
  count=ledger['calls'].get(channel,0)
  if count>=MAX_CALLS:raise ValueError('Per-model call budget exhausted')
  rate=RATES.get(channel);cost=(input_bound*rate['input_per_million']+MAX_OUTPUT*rate['output_per_million'])/1e6*rate['budget_cny_per_unit'] if rate else 0
  if ledger['reserved_cny']+cost>approved['max_total_cny']:raise ValueError('Total API budget exhausted before request')
  entry={'channel':channel,'attempt':count+1,'input_token_upper_bound':input_bound,'output_token_cap':MAX_OUTPUT,'reserved_cny':round(cost,6),'state':'reserved_before_request','created_at':datetime.now(timezone.utc).isoformat()}
  ledger['calls'][channel]=count+1;ledger['reserved_cny']+=cost;ledger['entries'].append(entry);write(path,ledger)
  return entry

def publish(channel,value):
 private=ROOT/'private';private.mkdir(exist_ok=True)
 with (private/'tactical-publish.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);path=ROOT/'data/tactical/models.json';index=strict_json(path.read_text());target=ROOT/'data/tactical'/f'{channel}-plan.json';write(target,value)
  index['models'][channel].update(status='ready',file=f'data/tactical/{channel}-plan.json',sha256=hashlib.sha256(target.read_bytes()).hexdigest(),diagnostic=None);write(path,index)

def status(channel,state,diagnostic=None):
 private=ROOT/'private';private.mkdir(exist_ok=True)
 with (private/'tactical-publish.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);path=ROOT/'data/tactical/models.json';index=strict_json(path.read_text())
  index['models'][channel].update(status=state,file=None,sha256=None,diagnostic=diagnostic);write(path,index)

def run_one(channel,context,text,out,approved):
 attempts=[];prior=None;errors=[]
 for attempt in range(1,MAX_CALLS+1):
  messages=[{'role':'user','content':text}]
  if prior is not None:messages += [{'role':'assistant','content':prior},{'role':'user','content':'原输出校验失败，不能由程序修路。错误：'+json.dumps(errors,ensure_ascii=False)+'。保留相同场景、角色与图谱，完整重新输出契约JSON；尤其留足每条边的移动时间，必要时减少移动或停留。'}]
  entry=reserve(out,channel,messages,approved);directory=out/channel/f'attempt-{entry["attempt"]}';directory.mkdir(parents=True,exist_ok=False);write(directory/'messages.json',messages)
  try:
   if channel=='codex':
    result=(directory/'last-message.json').resolve();env=os.environ.copy()
    for key in ['OPENAI_API_KEY','DEEPSEEK_API_KEY','ARK_API_KEY','MIMO_API_KEY']:env.pop(key,None)
    command=['codex','exec','--skip-git-repo-check','--ephemeral','--sandbox','read-only','--color','never','--model',MODELS[channel],'-c','model_reasoning_effort="high"','--output-schema',str((out/'schema.json').resolve()),'--output-last-message',str(result),'-']
    content='\n'.join(m['role']+':\n'+m['content'] for m in messages)
    with tempfile.TemporaryDirectory(prefix='valorant-tactical-worker-') as temp:completed=subprocess.run(command,input=content,text=True,capture_output=True,cwd=temp,env=env,timeout=600)
    (directory/'stdout.log').write_text(completed.stdout);(directory/'stderr.log').write_text(completed.stderr)
    if completed.returncode:raise RuntimeError('CLI worker failed; original logs retained, no automatic transport retry')
    match=re.search(r'OpenAI Codex[^\n]*\n-+\n(.*?)\n-+',completed.stderr,re.S)
    header=match[1] if match else ''
    fields=dict(re.findall(r'^([^:\n]+):\s*([^\n]+)',header,re.M));model=fields.get('model')
    if model!=MODELS[channel] or fields.get('reasoning effort')!='high' or fields.get('provider')!='openai' or fields.get('sandbox')!='read-only':raise RuntimeError('CLI runtime model/effort/provider/sandbox mismatch; no fallback accepted')
    original=result.read_text();attestation={'provider':'openai_chatgpt_cli','model':model,'reasoning_effort':'high','startup_header_sha256':hashlib.sha256(header.encode()).hexdigest()}
   else:
    config=PROVIDERS[channel];key=os.environ.get(config['key'])
    if not key:raise RuntimeError('Configured provider credential unavailable')
    catalog=request(config['base']+'/models',key,timeout=30);matches=[v for v in catalog.get('data',[]) if v.get('id')==MODELS[channel]]
    if len(matches)!=1 or config['display'] and matches[0].get('name')!=config['display']:raise RuntimeError('Exact model unavailable; no fallback accepted')
    write(directory/'catalog-entry.json',matches[0]);body={'model':MODELS[channel],'messages':messages,'max_tokens':MAX_OUTPUT,'thinking':{'type':'enabled'}}
    if channel!='mimo':body.update(response_format={'type':'json_object'},reasoning_effort='high')
    write(directory/'request-without-credentials.json',body);response=request(config['base']+'/chat/completions',key,body,timeout=600);write(directory/'response.json',response)
    if response.get('model')!=MODELS[channel]:raise RuntimeError('Provider runtime identity mismatch; output rejected')
    choice=response.get('choices',[{}])[0];original=choice.get('message',{}).get('content') or '';(directory/'raw-plan.txt').write_text(original)
    attestation={'provider':channel,'model':response['model'],'response_id':response.get('id'),'usage':response.get('usage'),'finish_reason':choice.get('finish_reason'),'response_sha256':digest(response)}
    if choice.get('finish_reason')!='stop':errors=['Incomplete provider output: '+str(choice.get('finish_reason'))];attempts.append({'attempt':attempt,'status':'rejected','errors':errors,'raw_sha256':hashlib.sha256(original.encode()).hexdigest()});write(directory/'validation.json',attempts[-1]);prior=original;continue
   try:raw=strict_json(original);errors=validate(raw,context)
   except (ValueError,TypeError) as e:errors=[str(e)]
   record={'attempt':attempt,'status':'valid' if not errors else 'rejected','errors':errors,'raw_sha256':hashlib.sha256(original.encode()).hexdigest()};attempts.append(record);write(directory/'validation.json',record)
   if errors:prior=original;continue
   value=public_plan(raw,context,channel,attestation,attempts,datetime.now(timezone.utc).isoformat());value['prompt_sha256']=hashlib.sha256(text.encode()).hexdigest();publish(channel,value);write(out/channel/'validated-plan.json',value);return {'channel':channel,'status':'ready','attempts':len(attempts),'model':MODELS[channel]}
  except (RuntimeError,TimeoutError,URLError,subprocess.TimeoutExpired) as e:
   write(directory/'failure.json',{'error':str(e),'classification':'transport_or_identity_failure_no_retry'});return {'channel':channel,'status':'failed','error':str(e)}
 return {'channel':channel,'status':'validation_failed','attempts':attempts}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--context',type=Path,default=ROOT/'data/tactical/context.json');p.add_argument('--execute',action='store_true');p.add_argument('--approval-file',type=Path);p.add_argument('--models',nargs='+',choices=list(MODELS),default=list(MODELS));args=p.parse_args()
 context=strict_json(args.context.read_text());text=prepare(context,args.out)
 if not args.execute:print(json.dumps({'status':'prepared_no_generation_calls','estimate':estimate(),'prompt_bytes':len(text.encode())}));raise SystemExit(0)
 allowed=approval(args.approval_file);write(args.out/'authorization.json',allowed);results=[]
 for channel in args.models:
  status(channel,'generating','真实方案生成中')
  result=run_one(channel,context,text,args.out,allowed)
  if result['status']!='ready':status(channel,result['status'],'两次输出均未通过校验' if result['status']=='validation_failed' else '真实调用失败，未生成可播放方案')
  results.append(result);write(args.out/'results.json',results);print(json.dumps(result,ensure_ascii=False),flush=True)
 if any(r['status']!='ready' for r in results):raise SystemExit(1)
