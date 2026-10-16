"""Evidence-driven single-analysis pipeline; prepare is free, run requires approval.

One complete evidence-based analysis -> local map arithmetic and shared seeded
draw -> explicitly fictional post-draw review. No persona or blind selection.
"""
import argparse,hashlib,json,os,re,subprocess,tempfile,fcntl
from datetime import datetime,timezone
from pathlib import Path
from evidence_pack import ROOT,digest,validate_pack
from forecast_contract import decision_prompt,schema,validate_proposal,unwrap_proposal,parse_completion
from tactical_contract import MODELS,strict_json
from run_api_models import PROVIDERS,request
from run_tactical_models import RATES,write
STAGES={'analysis':200000,'review':80000};OUTPUT_CAP=24000
REVIEW_SCHEMA={'type':'object','properties':{'headline':{'type':'string'},'series_reviews':{'type':'array','minItems':2,'maxItems':2,'items':{'type':'string'}},'limitations':{'type':'string'}},'required':['headline','series_reviews','limitations'],'additionalProperties':False}
def budget():
 rows={k:round((sum(STAGES.values())*r['input_per_million']+2*OUTPUT_CAP*r['output_per_million'])/1e6*r['budget_cny_per_unit'],6) for k,r in RATES.items()}
 return {'approved':False,'planned_calls_per_model':2,'planned_calls_total':8,'authorized_max_calls_per_model':4,'authorized_max_calls_total':16,'api_calls_planned':6,'chatgpt_cli_calls_planned':2,'per_provider_reservation_cny':rows,'api_max_reservation_cny':round(sum(rows.values()),6),'requested_additional_cap_cny':10,'input_token_upper_bounds':STAGES,'output_token_cap_per_api_call':OUTPUT_CAP,'rates':RATES,'fx_note':'USD x8 is conservative reservation coefficient, not current FX quote. No cache/discount assumed.','rate_checked_at':'2026-10-16','rate_sources':{'deepseek':RATES['deepseek']['source'],'doubao':'https://docs.volcengine.com/docs/ark/model-pricing?lang=zh','mimo':'https://mimo.mi.com/docs/zh-CN/price/pay-as-you-go'},'notes':['Additional batch only. Old 2/2 shared ledger remains unchanged.','No retry or model substitution; failed requests consume a stage allowance.','No OpenAI API, recharge, subscription, financial prediction or external model tools.']}
def prepare(pack,out):
 validate_pack(pack)
 if (out/'ledger.json').exists():raise ValueError('Cannot replace input after any stage is reserved')
 out.mkdir(parents=True,exist_ok=True);write(out/'frozen-input.json',pack);write(out/'schema.json',schema(pack));write(out/'budget.json',budget())
 (out/'analysis-prompt.txt').write_text(decision_prompt(pack))
 write(out/'input-receipt.json',{'input_sha256':pack['content_sha256'],'models':MODELS,'method':'single_evidence_analysis_no_persona','stages':list(STAGES),'approval_required':True,'no_model_calls_made':True})
 # Reject an oversized initial input now, before requesting authorization.
 if len((out/'analysis-prompt.txt').read_bytes())+len(json.dumps(schema(pack)).encode())+2048>STAGES['analysis']:raise ValueError('Prepared prompt exceeds conservative stage budget')
def approved(path,input_sha256=None):
 if path is None:raise ValueError('New explicit approval required; old tactical approval is invalid')
 a=strict_json(path.read_text())
 if a.get('batch')!='evidence-v2' or a.get('input_sha256')!=input_sha256 or a.get('approved') is not True or set(a.get('models',[]))!=set(MODELS) or a.get('max_calls_per_model')!=4 or not isinstance(a.get('authorization'),str) or len(a['authorization'].strip())<8 or not budget()['api_max_reservation_cny']<=a.get('max_total_cny',0)<=10:raise ValueError('Approval must cover this new single-analysis batch, exact models and CNY cap')
 return a
def call(channel,stage,prompt,sch,out,a,disable_thinking=False):
 base_stage=stage.split("_retry")[0]
 if channel not in MODELS or base_stage not in STAGES:raise ValueError('Unknown stage or identity')
 config=PROVIDERS.get(channel);body={'model':MODELS[channel],'messages':[{'role':'user','content':prompt}],'max_tokens':OUTPUT_CAP,'thinking':{'type':'enabled'}}
 if disable_thinking:body['thinking']={'type':'disabled'}
 if channel not in ['codex','mimo']:body.update(response_format={'type':'json_object'},reasoning_effort='high')
 if disable_thinking:body.pop('reasoning_effort',None)
 bound=len(json.dumps(body,ensure_ascii=False).encode())+len(json.dumps(sch,ensure_ascii=False).encode())+2048
 if bound>STAGES[base_stage]:raise ValueError('Stage input byte/token bound exceeds approved reservation')
 # One atomic ledger entry per exact stage; failures never refund call counts.
 with (out/'ledger.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);p=out/'ledger.json';ledger=json.loads(p.read_text()) if p.exists() else {'batch':'evidence-v2','calls':{},'reserved_cny':0,'entries':[]}
  if any(e['channel']==channel and e['stage']==stage for e in ledger['entries']) or ledger['calls'].get(channel,0)>=4:raise ValueError('Stage already consumed; no automatic retry')
  rate=RATES.get(channel);cost=(bound*rate['input_per_million']+OUTPUT_CAP*rate['output_per_million'])/1e6*rate['budget_cny_per_unit'] if rate else 0
  if ledger['reserved_cny']+cost>a['max_total_cny']:raise ValueError('API batch budget exhausted')
  entry={'channel':channel,'model':MODELS[channel],'stage':stage,'input_token_upper_bound':bound,'output_token_cap':OUTPUT_CAP,'reserved_cny':cost,'created_at':datetime.now(timezone.utc).isoformat()};ledger['entries'].append(entry);ledger['calls'][channel]=ledger['calls'].get(channel,0)+1;ledger['reserved_cny']+=cost;write(p,ledger)
 d=out/channel/stage;d.mkdir(parents=True,exist_ok=False);write(d/'request-without-credentials.json',body);write(d/'schema.json',sch)
 if channel=='codex':
  env=os.environ.copy()
  for k in ['OPENAI_API_KEY','DEEPSEEK_API_KEY','ARK_API_KEY','MIMO_API_KEY']:env.pop(k,None)
  command=['codex','exec','--skip-git-repo-check','--ephemeral','--sandbox','read-only','--color','never','--model',MODELS[channel],'-c','model_reasoning_effort="high"','--output-schema',str((d/'schema.json').resolve()),'--output-last-message',str((d/'last-message.json').resolve()),'-']
  with tempfile.TemporaryDirectory(prefix='vct-independent-decision-') as cwd:r=subprocess.run(command,input=prompt,text=True,capture_output=True,cwd=cwd,env=env,timeout=900)
  (d/'stdout.log').write_text(r.stdout);(d/'stderr.log').write_text(r.stderr)
  if r.returncode:raise RuntimeError('CLI failed, no retry/fallback')
  match=re.search(r'OpenAI Codex[^\n]*\n-+\n(.*?)\n-+',r.stderr,re.S);header=match[1] if match else '';fields=dict(re.findall(r'^([^:\n]+):\s*([^\n]+)',header,re.M))
  if any(fields.get(k)!=v for k,v in {'model':MODELS[channel],'reasoning effort':'high','provider':'openai','sandbox':'read-only'}.items()):raise ValueError('CLI runtime identity mismatch')
  raw=(d/'last-message.json').read_text();att={'provider':'openai_chatgpt_cli','model':MODELS[channel],'reasoning_effort':'high','header_sha256':hashlib.sha256(header.encode()).hexdigest()}
 else:
  key=os.environ.get(config['key'])
  if not key:raise RuntimeError('Provider credential unavailable')
  cat=request(config['base']+'/models',key);matches=[m for m in cat.get('data',[]) if m.get('id')==MODELS[channel]]
  if len(matches)!=1 or config['display'] and matches[0].get('name')!=config['display']:raise ValueError('Exact model unavailable')
  write(d/'catalog-entry.json',matches[0]);response=request(config['base']+'/chat/completions',key,body,timeout=900);write(d/'response.json',response)
  if response.get('model')!=MODELS[channel] or response['choices'][0].get('finish_reason')!='stop':raise ValueError('Identity mismatch or incomplete output')
  raw=response['choices'][0]['message']['content'];att={'provider':channel,'model':response['model'],'usage':response.get('usage'),'response_sha256':digest(response)}
 write(d/'runtime-attestation.json',att);(d/'raw-output.txt').write_text(raw);value,transport_norm=parse_completion(raw);write(d/'transport-normalization.json',transport_norm);write(d/'parsed-output.json',value);return value,att
def run_channel(channel,pack,out,a):
 existing=out/channel/'validated-result.json'
 if existing.exists():
  value=strict_json(existing.read_text())
  if value['input_sha256']!=pack['content_sha256']:raise ValueError('Cannot reuse result from another input')
  validate_proposal(value['selected'],pack);return value
 stage='analysis_retry' if (out/channel/'analysis').exists() else 'analysis'
 selected,att=call(channel,stage,(out/'analysis-prompt.txt').read_text(),schema(pack),out,a,disable_thinking=(channel!='codex'));selected,normalizations=unwrap_proposal(selected);validate_proposal(selected,pack);trace=out/channel/stage/'transport-normalization.json';normalizations=(strict_json(trace.read_text()) if trace.exists() else [])+normalizations;attestations=[att]
 # Outcome draw occurs only after proposals and whole-plan selection are frozen.
 computed=json.loads(subprocess.check_output(['node',str(ROOT/'scripts/compute_v2.mjs')],input=json.dumps(selected).encode()))
 prompt='你是同一模型的赛后解说。以下系列赛是已冻结逐图概率由程序抽样生成的虚构情景，不是实际比赛。不改变地图、赢家、比分，不编造真实选手评分、伤病、实况或未提供技能战斗事件。按两场顺序各写一段简短模拟复盘，解释与赛前判断的关系和不确定性。不得声称走位沙盘是本次BP的实况。只输出严格JSON对象，字段headline,series_reviews(两段),limitations。输入：'+json.dumps({'selected_proposal':selected,'computed':computed},ensure_ascii=False,separators=(',',':'))
 review,att=call(channel,'review',prompt,REVIEW_SCHEMA,out,a,disable_thinking=(channel!='codex'))
 if not isinstance(review,dict) or set(review)!={'headline','series_reviews','limitations'} or not isinstance(review['series_reviews'],list) or len(review['series_reviews'])!=2 or any(not isinstance(v,str) or not v.strip() for v in [review['headline'],review['limitations'],*review['series_reviews']]):raise ValueError('Review contract mismatch')
 attestations.append(att);result={'kind':'evidence_v2_model_prediction','channel':channel,'input_sha256':pack['content_sha256'],'created_at':datetime.now(timezone.utc).isoformat(),'method':'single_evidence_analysis_no_persona','selected':selected,'computed':computed,'fictional_review':review,'runtime_attestations':attestations,'review_status':'ready','normalizations':normalizations,'legacy_outputs_unchanged':True};write(out/channel/'validated-result.json',result);write(ROOT/f'data/forecast-v2/{channel}.json',result);return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--run',action='store_true');p.add_argument('--approval-file',type=Path);args=p.parse_args()
 if args.run:
  pack=strict_json((args.out/'frozen-input.json').read_text());validate_pack(pack);a=approved(args.approval_file,pack['content_sha256'])
  from concurrent.futures import ThreadPoolExecutor,as_completed
  results={}
  with ThreadPoolExecutor(max_workers=4) as ex:
   futures={ex.submit(run_channel,channel,pack,args.out,a):channel for channel in MODELS}
   for future in as_completed(futures):
    channel=futures[future]
    try:future.result();results[channel]={'status':'ready'}
    except Exception as e:results[channel]={'status':'failed','error':str(e)}
    write(args.out/'results.json',results);print(json.dumps({'channel':channel,**results[channel]},ensure_ascii=False),flush=True)
  if any(v['status']!='ready' for v in results.values()):raise SystemExit(1)
 else:prepare(strict_json((ROOT/'data/evidence-v2.json').read_text()),args.out)
 print(json.dumps({'mode':'run' if args.run else 'prepare_only','out':str(args.out),'budget':budget()},ensure_ascii=False))
