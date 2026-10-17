"""Independent provider workers; one atomic explicitly approved cumulative budget, no automatic HTTP retry."""
import argparse,concurrent.futures,fcntl,hashlib,json,multiprocessing,os,re,time,traceback,uuid
from datetime import datetime,timezone
from pathlib import Path
import causal_series as c
from run_api_models import PROVIDERS,request
from causal_quality import quality_flags
ROOT=c.ROOT
MODELS={'codex':c.MODEL,**{k:v['model'] for k,v in PROVIDERS.items()}}
RATES={
 'deepseek':{'input':.3,'cached':.006,'output':1.2,'currency':'USD','cny_coefficient':8,'source':'https://api-docs.deepseek.com/quick_start/pricing/'},
 'doubao':{'input':6,'cached':1.2,'output':30,'currency':'CNY','cny_coefficient':1,'source':'https://ark.volcengine.com/region%3Acn-beijing/model/detail?Id=doubao-seed-2-1-pro'},
 'mimo':{'input':3,'cached':.025,'output':6,'currency':'CNY','cny_coefficient':1,'source':'https://mimo.mi.com/models/en-US/mimo-v2.6-pro'}}
def now():return datetime.now(timezone.utc).isoformat()
def usage_fields(raw):
 u=raw if isinstance(raw,dict) else {};inp=u.get('prompt_tokens',u.get('input_tokens'));out=u.get('completion_tokens',u.get('output_tokens'));pd=u.get('prompt_tokens_details') or u.get('input_tokens_details') or {};od=u.get('completion_tokens_details') or u.get('output_tokens_details') or {}
 return {'input_tokens':inp,'output_tokens':out,'cached_input_tokens':u.get('prompt_cache_hit_tokens',pd.get('cached_tokens')),'cache_miss_input_tokens':u.get('prompt_cache_miss_tokens'),'cache_write_input_tokens':u.get('cache_creation_input_tokens'),'reasoning_tokens':od.get('reasoning_tokens',u.get('reasoning_tokens')),'total_tokens':u.get('total_tokens')}
def cost(channel,inp,out,cached=0):
 r=RATES[channel];return ((inp-cached)*r['input']+cached*r['cached']+out*r['output'])/1e6*r['cny_coefficient']
def approved_cap(root,channel=None):
 approval=json.loads((root/'approval.json').read_text());cap=approval.get('max_total_cny')
 legacy=cap in (40,50) and set(approval.get('models',[]))==set(PROVIDERS)
 postmatch=cap==25 and set(approval.get('models',[]))=={'mimo','doubao'} and approval.get('purpose')=='grand_final_postmatch_20261018' and approval.get('teams')==['LOUD','VIT']
 if approval.get('approved') is not True or type(cap) is not int or not (legacy or postmatch):raise ValueError('Explicit matching provider/budget approval required')
 if channel is not None and (channel not in approval.get('models',[]) or channel not in approval.get('active_models',list(PROVIDERS))):raise ValueError('Provider frozen by current approval; no new calls allowed')
 return cap
class Budget:
 def __init__(self,root):self.root=root
 def mutate(self,fn):
  with (self.root/'budget.lock').open('a') as lock:
   fcntl.flock(lock,fcntl.LOCK_EX);p=self.root/'budget-ledger.json';v=json.loads(p.read_text()) if p.exists() else {'cap_cny':approved_cap(self.root),'entries':[],'pricing_checked_at':'2026-10-16','rates':RATES,'invoice_available':False}
   result=fn(v);c.write(p,v);return result
 def reserve(self,channel,stage,key,input_bound,output_cap,retry):
  cap=approved_cap(self.root,channel)
  reserved=cost(channel,input_bound,2*output_cap)
  def update(v):
   if v['cap_cny']!=cap:raise ValueError('Approval and cumulative ledger caps differ; migrate the existing ledger explicitly')
   if v.get('stopped'):raise ValueError('Budget stop: cumulative ledger paused; no new paid requests')
   if any(e['key']==key and e['channel']==channel for e in v['entries']):raise ValueError('Duplicate paid request refused')
   used=sum(e.get('budget_charge_upper_cny',e['reserved_cny']) for e in v['entries'])
   if used+reserved>cap:
    reason=f'Budget stop: charged/reserved {used:.4f} + next {reserved:.4f} exceeds CNY{cap}; additional {used+reserved-cap:.4f} required'
    v['stopped']={'at':now(),'reason':reason,'used_or_reserved_cny':used,'rejected_next_reserve_cny':reserved,'cap_cny':cap};c.write(self.root/'budget-ledger.json',v);raise ValueError(reason)
   id=uuid.uuid4().hex;v['entries'].append({'id':id,'channel':channel,'provider':channel,'model':MODELS[channel],'stage':stage,'key':key,'retry_index':retry,'started_at':now(),'input_token_byte_upper_bound':input_bound,'output_token_cap':output_cap,'reserve_output_multiplier':2,'reserved_cny':reserved,'status':'in_flight','returned_usage':None,'usage':usage_fields(None),'actual_invoice_cny':None});return id
  return self.mutate(update)
 def settle(self,id,response,elapsed,error=None):
  raw=response.get('usage') if response else None;u=usage_fields(raw)
  def update(v):
   e=next(e for e in v['entries'] if e['id']==id);known=u['input_tokens'] is not None and u['output_tokens'] is not None
   upper=cost(e['channel'],u['input_tokens'],u['output_tokens']) if known else e['reserved_cny'];cached=u['cached_input_tokens']
   estimate=cost(e['channel'],u['input_tokens'],u['output_tokens'],cached if isinstance(cached,int) else 0) if known else None
   e.update(status='response_received' if response else 'failed_unknown_usage',finished_at=now(),elapsed_seconds=elapsed,returned_usage=raw,usage=u,response_id=response.get('id') if response else None,error=error,budget_charge_upper_cny=upper,estimated_cny_from_reported_usage=estimate,estimate_assumes_uncached_when_unknown=cached is None,actual_invoice_cny=None)
   v['budget_upper_used_cny']=sum(row.get('budget_charge_upper_cny',row['reserved_cny']) for row in v['entries']);v['budget_upper_remaining_cny']=v['cap_cny']-v['budget_upper_used_cny'];return e
  return self.mutate(update)
def reconcile(root=None):
 folder=ROOT/'data/causal';rows={}
 for channel in MODELS:
  p=folder/(channel+'.json')
  if p.exists():
   raw=p.read_bytes();value=json.loads(raw);rows[channel]={'status':value['status'],'file':'data/causal/'+p.name,'sha256':hashlib.sha256(raw).hexdigest(),'champion':value.get('cases',[{}])[-1].get('state',{}).get('winner') if len(value.get('cases',[]))==2 and value['status']=='ready' else None}
  else:
   status_path=(root or ROOT/'private/causal-three-paid-20261016')/channel/'worker-status.json'
   status=json.loads(status_path.read_text()).get('status') if status_path.exists() else 'running'
   rows[channel]={'status':'blocked' if status=='blocked' else 'running','file':None}
 value={'kind':'causal_series_manifest','models':rows};temp=folder/('models.'+uuid.uuid4().hex+'.tmp');temp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n');temp.replace(folder/'models.json')
def publish_provider(out,pack,channel,publish_pair=True):
 s=json.loads((out/'state.json').read_text());ledger=json.loads((out/'ledger.json').read_text());records=[];frames=[];bp=None
 for e in ledger['entries']:
  d=out/e['directory'];p=d/'validation.json'
  if not p.exists():continue
  validation=json.loads(p.read_text())
  if validation.get('status') not in ['valid','partial']:continue
  raw=json.loads((d/'result.json').read_text());before=json.loads((d/'before.json').read_text());after=json.loads((d/'after.json').read_text());records.append({'stage':e['stage'],'before_sha256':c.digest(before),'after_sha256':c.digest(after),'raw_output_sha256':c.digest(raw),'runtime_attestation':e['runtime_attestation'],'before':before,'after':after,'decision':raw,'validation':validation,'transport_normalization':json.loads((d/'normalization.json').read_text()) if (d/'normalization.json').exists() else None})
  if before['stage']=='bp':bp=raw
  elif (d/'frames.json').exists():frames+=json.loads((d/'frames.json').read_text())
 c.write(out/'public.json',{'kind':'actual_model_batched_causal_series','channel':channel,'status':'ready' if s['stage']=='finished' else 'partial','teams':s['teams'],'evidence_sha256':pack['content_sha256'],'calls':ledger['calls'],'scope':'2026-10-18 grand final BO5' if s['teams'][0]=='LOUD' else '2026-10-17 loser final BO5','granularity':'Per-map batched sequential events; external state feedback between batches only','bp':bp,'records':records,'frames':frames,'state':s,'quality_flags':quality_flags(channel,records)})
 if publish_pair:publish_bundle(out,pack,channel)
def make_call(channel,budget_root):
 config=PROVIDERS[channel];budget=Budget(budget_root)
 def call(stage,state,sch,extra,out,pack):
  ledger_path=out/'ledger.json';ledger=json.loads(ledger_path.read_text()) if ledger_path.exists() else {'channel':channel,'calls':0,'entries':[]};key=stage+'-'+c.digest(state)[:16]
  if any(e['key']==key for e in ledger['entries']):raise ValueError('Duplicate provider state request')
  prompt='你是瓦洛兰特赛前推演员。只输出严格JSON，无工具、联网或文件操作。根据当前已形成状态推演下一阶段的双方决策和有序回合事件，不预选最终赢家或比分，不输出概率。未来首发是模拟假设。只使用冻结证据，不编造录像、伤病、心理或选手引语。schema字段必须逐字匹配，禁止多出winner/score字段。\n阶段：'+stage+'\n输入状态SHA-256（原样填入previous_state_sha256）：'+c.digest(state)+'\n输入状态：'+json.dumps(state,ensure_ascii=False,separators=(',',':'))+'\n阶段任务与资料：'+json.dumps(extra,ensure_ascii=False,separators=(',',':'))+'\n输出JSON schema：'+json.dumps(sch,ensure_ascii=False,separators=(',',':'))
  cap=6000 if stage.startswith('bp') else 32768 if channel in ['deepseek','mimo'] else 16000;body={'model':config['model'],'messages':[{'role':'user','content':prompt}],'max_tokens':cap,'thinking':{'type':'disabled'}}
  if channel in ['deepseek','mimo'] and state['stage']!='bp':body['thinking']={'type':'enabled'}
  if channel=='deepseek' and state['stage']!='bp':body['reasoning_effort']='high'
  body['response_format']={'type':'json_object'}
  bound=len(json.dumps(body,ensure_ascii=False).encode())+2048;retry=sum(e['before_sha256']==c.digest(state) for e in ledger['entries']);id=budget.reserve(channel,stage,key,bound,cap,retry)
  d=out/f'{ledger["calls"]+1:02d}-{stage}';d.mkdir(parents=True,exist_ok=False);(d/'prompt.txt').write_text(prompt);c.write(d/'before.json',state);c.write(d/'schema.json',sch);c.write(d/'request-without-credentials.json',body)
  ledger['calls']+=1;ledger['entries'].append({'key':key,'stage':stage,'before_sha256':c.digest(state),'directory':d.name,'status':'reserved','budget_id':id,'started_at':time.time()});c.write(ledger_path,ledger);start=time.monotonic();response=None
  print(channel+' request '+str(ledger['calls'])+' '+stage,flush=True)
  try:
   token=os.environ.get(config['key'])
   if not token:raise ValueError('Existing provider credential unavailable')
   response=request(config['base']+'/chat/completions',token,body,timeout=900)
  except Exception as e:
   usage=budget.settle(id,None,time.monotonic()-start,str(e));ledger['entries'][-1]['status']='failed_unknown_usage';c.write(ledger_path,ledger);c.write(d/'usage.json',usage);raise
  usage=budget.settle(id,response,time.monotonic()-start);c.write(d/'response.json',response);c.write(d/'usage.json',usage);ledger['entries'][-1]['status']='response_received';c.write(ledger_path,ledger)
  if response.get('model')!=config['model']:raise ValueError('Provider response model mismatch')
  ch=response['choices'][0];raw=ch.get('message',{}).get('content') or '';(d/'raw-output.txt').write_text(raw)
  if ch.get('finish_reason')!='stop':raise ValueError('Incomplete provider output; raw and usage retained')
  if raw.strip().startswith('```'):
   m=re.fullmatch(r'\s*```(?:json)?\s*\n(.*)\n```\s*',raw,re.S)
   if m:raw=m[1];c.write(d/'normalization.json',{'action':'remove_single_markdown_fence_only','semantic_changes':False})
  from repair_causal_transport import normalize
  value,changes=normalize(raw)
  if changes:c.write(d/'normalization.json',{'raw_completion_sha256':hashlib.sha256(raw.encode()).hexdigest(),'changes':changes,'event_values_unchanged':True})
  c.write(d/'result.json',value);att={'provider':channel,'model':response['model'],'response_id':response.get('id'),'thinking':body['thinking']['type'],'response_format':body['response_format'],'usage':usage['usage'],'response_sha256':c.digest(response)};ledger['entries'][-1].update(status='responded',runtime_attestation=att,output_sha256=c.digest(value));c.write(ledger_path,ledger);return value,d,att
 return call

def publish_bundle(out,pack,channel):
 lf=ROOT/'private/gpt-causal-bo5-20261016' if channel=='codex' else out.parent/channel
 if out.name=='grand-final':lf=out.parent
 cases=[]
 for folder in [lf,lf/'grand-final']:
  if (folder/'public.json').exists():cases.append(json.loads((folder/'public.json').read_text()))
 if not cases:return
 value={**cases[0],'cases':cases,'status':'ready' if len(cases)==2 and all(v['status']=='ready' for v in cases) else 'partial','calls':sum(v['calls'] for v in cases),'scope':'Loser final, then grand final using own derived finalist'}
 c.write(ROOT/f'data/causal/{channel}.json',value);reconcile()

def bp_task(teams,final=False):
 return {'task':('总决赛BO5：LOUD为胜者组冠军，连续禁用两图并优先选择A/B身份；A/B/A/B选四图，第五图剩余；选边权B/A/B/A/B。对手是本模型刚完成的败者决赛赢家。' if final else '败者组决赛BO5，VIT优先选择A/B；双方各禁一图，A/B/A/B选四图；选边B/A/B/A/B。')+'teams='+str(teams)+'。first_team_start_side始终指teams[0]。只输出BP，无赢家或比分。'}

def complete_bp(channel,root,out,s,pack,final,task_override=None):
 while s['stage']=='bp':
  extra=dict(task_override) if task_override else bp_task(s['teams'],final);extra['frozen_evidence']=pack
  ledger=json.loads((out/'ledger.json').read_text()) if (out/'ledger.json').exists() else {'entries':[]}
  matching=[e for e in ledger['entries'] if e['before_sha256']==c.digest(s)]
  if matching:
   d=out/matching[-1]['directory'];previous=d/'validation.json'
   if not (d/'response.json').exists() and matching[-1]['status']=='reserved':raise ValueError('BP request still unfinished; do not duplicate')
   extra['previous_validation_error']=json.loads(previous.read_text()).get('error') if previous.exists() else 'Previous response was incomplete or malformed; produce concise exact BP JSON without scores.'
  stage='bp' if not matching else 'bp-retry'+str(len(matching))
  try:raw,d,att=c.call(stage,s,c.bp_schema(pack),extra,out,pack)
  except (ValueError,KeyError) as error:
   ledger_path=out/'ledger.json'
   if not ledger_path.exists():raise
   entries=json.loads(ledger_path.read_text()).get('entries',[])
   if not entries:raise
   current=entries[-1]
   if current['key']!=stage+'-'+c.digest(s)[:16]:raise
   d=out/current['directory'];response=d/'response.json'
   if not response.exists():raise
   actual=json.loads(response.read_text())
   if actual.get('model')!=MODELS[channel]:raise
   c.write(d/'validation.json',{'status':'invalid','error':str(error)});print(channel+' BP response rejected: '+str(error),flush=True);continue
  try:after=c.apply_bp(s,raw,pack)
  except ValueError as error:
   c.write(d/'validation.json',{'status':'invalid','error':str(error)});print(channel+' BP rejected: '+str(error),flush=True);continue
  c.write(d/'after.json',after);c.write(d/'validation.json',{'status':'valid','after_sha256':c.digest(after)});c.write(out/'state.json',after);s=after
 return s

def run_case(channel,root,out,teams,final=False):
 out.mkdir(parents=True,exist_ok=True)
 pack=json.loads((ROOT/'data/evidence-v2.json').read_text())
 with (out/'run.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  state=out/'state.json';s=json.loads(state.read_text()) if state.exists() else c.initial(pack,teams)
  if not state.exists():c.write(state,s)
  if s['teams']!=teams:raise ValueError('Finalist differs from own derived winner')
  c.call=make_call(channel,root) if channel!='codex' else GPT_CALL
  c.publish=lambda dest,pack:publish_provider(dest,pack,channel)
  if channel=='codex':c.write(out/'approval.json',{'approved':True,'model':c.MODEL,'api_budget_cny':0,'no_artificial_call_limit':True,'authorization_source':'User canceled artificial count caps and requested both final-two-match chains; ChatGPT quota only'})
  if s['stage']=='bp':s=complete_bp(channel,root,out,s,pack,final)
  c.run_remaining(out,pack,max_rounds=int(os.environ.get('VALORANT_CAUSAL_ROUND_WINDOW','3')) if channel!='codex' else 6)
  return json.loads(state.read_text())
GPT_CALL=c.call

def worker(channel,root):
 out=(ROOT/'private/gpt-causal-bo5-20261016') if channel=='codex' else root/channel
 out.mkdir(parents=True,exist_ok=True)
 try:
  c.write(out/'worker-status.json',{'status':'running','pid':os.getpid(),'at':now()})
  lf=run_case(channel,root,out,['VIT','100T'])
  if lf['stage']!='finished':raise ValueError('Lower final unfinished')
  print(channel+' LF COMPLETE '+str(lf['series_score'])+' winner '+lf['winner'],flush=True)
  gf=run_case(channel,root,out/'grand-final',['LOUD',lf['winner']],True)
  c.write(out/'worker-status.json',{'status':'finished','at':now()})
  print(channel+' BOTH COMPLETE '+str(gf['series_score'])+' winner '+gf['winner'],flush=True)
 except Exception as e:
  c.write(out/'worker-status.json',{'status':'blocked','error':str(e),'at':now()});traceback.print_exc();print(channel+' BLOCKED: '+str(e),flush=True)
 finally:reconcile(root)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--prepare-only',action='store_true');ap.add_argument('--channels',nargs='+',default=list(PROVIDERS));a=ap.parse_args();root=a.out.resolve();root.mkdir(parents=True,exist_ok=True)
 if a.prepare_only:
  c.write(root/'prepared.json',{'models':MODELS,'cap_cny':json.loads((root/'budget-ledger.json').read_text())['cap_cny'] if (root/'budget-ledger.json').exists() else 40,'rates':RATES,'rate_units':'per 1M tokens','currency_note':'USD coefficient8 is a conservative budget conversion, not FX quote','no_model_calls':True});print('Prepared; no generation requests');return
 with (root/('supervisor-'+ '-'.join(sorted(a.channels))+'.lock')).open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  approved_cap(root)
  ctx=multiprocessing.get_context('spawn');workers=[ctx.Process(target=worker,args=(channel,root),name='causal-'+channel) for channel in a.channels]
  for p in workers:p.start()
  while any(p.is_alive() for p in workers):
   reconcile(root)
   for p in workers:p.join(timeout=.1)
   time.sleep(5)
  reconcile(root);print('Paid workers ended. Inspect each worker-status and budget ledger.',flush=True)
if __name__=='__main__':main()
