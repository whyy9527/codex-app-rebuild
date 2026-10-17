"""Evidence-bound batched BO5. Model owns decisions/events, code derives state.
GPT uses quota approval; paid_causal orchestrates independent providers under a shared budget.
"""
import argparse,fcntl,hashlib,json,os,re,subprocess,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MODEL='gpt-6.1-sol'
IDS=[f'{s}{i}' for s in ['L','R'] for i in range(1,6)]
TEAM=['VIT','100T']
from causal_json import decode_json
def digest(v):return hashlib.sha256(json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);t=p.with_suffix('.tmp');t.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n');t.replace(p)
def strict(props):return {'type':'object','additionalProperties':False,'required':list(props),'properties':props}
def arr(item,n=None,maxn=None):
 r={'type':'array','items':item}
 if n is not None:r['minItems']=n
 if maxn is not None:r['maxItems']=maxn
 return r
def text():return {'type':'string'}
def choice(values):return {'type':'string','enum':list(values)}
def bp_schema(pack):
 return strict({'previous_state_sha256':text(),'priority_role':choice(['A','B']),'bans':arr(choice(pool(pack)),2,2),'maps':arr(strict({'map':choice(pool(pack)),'first_team_start_side':choice(['ATK','DEF']),'reason':text(),'evidence_refs':arr(choice([f['id'] for f in pack['facts']]),1)}),5,5),'reason':text()})
def pool(pack):return next(f['value']['pool'] for f in pack['facts'] if f['id']=='official:rules')
def initial(pack,teams=None):return {'kind':'causal_batched_bo5_state','evidence_sha256':pack['content_sha256'],'teams':teams or TEAM,'stage':'bp','map_index':0,'series_score':[0,0],'round_score':[0,0],'round_number':1,'loss_streak':[0,0],'last_buy':['pistol','pistol'],'maps':[],'bans':[],'lineup':None,'winner':None,'history':[]}
def apply_bp(before,value,pack):
 if set(value)!={'previous_state_sha256','priority_role','bans','maps','reason'}:raise ValueError('Unexpected BP fields, including supplied score/winner')
 if value['previous_state_sha256']!=digest(before):raise ValueError('BP prior state mismatch')
 if len(value['bans'])!=2 or len(value['maps'])!=5 or sorted(value['bans']+[m['map'] for m in value['maps']])!=sorted(pool(pack)):raise ValueError('Invalid seven-map BP')
 if value['priority_role'] not in ['A','B']:raise ValueError('Invalid A/B identity')
 ids={f['id'] for f in pack['facts']}
 for m in value['maps']:
  if set(m)!={'map','first_team_start_side','reason','evidence_refs'}:raise ValueError('Unexpected map decision fields')
  if m['first_team_start_side'] not in ['ATK','DEF'] or not m['evidence_refs'] or not set(m['evidence_refs'])<=ids:raise ValueError('Invalid side/evidence')
 s=json.loads(json.dumps(before));s.update(stage='opening',maps=value['maps'],bans=value['bans'],priority_role=value['priority_role'],bp_reason=value['reason']);return s

def call(stage,state,sch,extra,out,pack):
 approval=json.loads((out/'approval.json').read_text())
 if approval.get('approved') is not True or approval.get('model')!=MODEL or approval.get('api_budget_cny')!=0:raise ValueError('Explicit GPT quota approval required')
 ledger_path=out/'ledger.json';ledger=json.loads(ledger_path.read_text()) if ledger_path.exists() else {'batch':'gpt-causal-bo5','calls':0,'api_cny':0,'entries':[]}
 effort='high' if stage=='bp' else 'medium'
 key=stage+'-'+digest(state)[:16]
 if any(e['key']==key for e in ledger['entries']):raise ValueError('Stage already reserved; refusing duplicate request')
 if not approval.get('no_artificial_call_limit') and ledger['calls']>=approval.get('max_calls',0):raise ValueError('Approved request cap reached')
 d=out/f'{ledger["calls"]+1:02d}-{stage}';d.mkdir(parents=True,exist_ok=False)
 base='''你是GPT-6.1 sol瓦洛兰特赛前推演员。只输出严格JSON；禁止工具、文件、联网或调用其他模型。不是写已知比分的复盘，不要先决定赢家或最终比分。根据当前真实输入状态逐步做双方决策与有序模拟事件；前一事件发生后才推下一事件。模拟事件是你的预测，不是官方赛况。只使用本次冻结证据，未来首发/阵容是你的显式假设，不编伤病/训练赛/看过录像。不得生成概率或预定最终比分。脚本将根据事件得出回合、地图和系列赛结果。既有旧概率、旧抽样、旧Ascent方案不作为输入。证据质量与小样本须体现在具体判断，理由短，避免套话。\n'''
 prompt=base+'阶段：'+stage+'\n本步输入状态（必须绑定摘要'+digest(state)+'）：'+json.dumps(state,ensure_ascii=False,separators=(',',':'))+'\n阶段资料与任务：'+json.dumps(extra,ensure_ascii=False,separators=(',',':'))
 (d/'prompt.txt').write_text(prompt);write(d/'before.json',state);write(d/'schema.json',sch)
 ledger['calls']+=1;ledger['entries'].append({'key':key,'stage':stage,'before_sha256':digest(state),'status':'reserved','directory':d.name,'prompt_bytes':len(prompt.encode()),'expected_reasoning_effort':effort,'started_at':time.time()});write(ledger_path,ledger)
 env=os.environ.copy()
 for k in ['OPENAI_API_KEY','DEEPSEEK_API_KEY','ARK_API_KEY','MIMO_API_KEY']:env.pop(k,None)
 result_path=d/'result.json'
 cmd=['codex','exec','--skip-git-repo-check','--ephemeral','--sandbox','read-only','--color','never','--model',MODEL,'-c',f'model_reasoning_effort="{effort}"','--output-schema',str((d/'schema.json').resolve()),'--output-last-message',str(result_path.resolve()),'-']
 print(f'GPT request {ledger["calls"]}: {stage}; prompt {len(prompt.encode())} bytes',flush=True)
 with tempfile.TemporaryDirectory(prefix='valorant-causal-worker-') as work:
  with (d/'stdout.log').open('w') as stdout,(d/'stderr.log').open('w') as stderr:
   try:r=subprocess.run(cmd,input=prompt,text=True,stdout=stdout,stderr=stderr,cwd=work,env=env,timeout=900)
   except subprocess.TimeoutExpired:
    ledger['entries'][-1]['status']='timeout';write(ledger_path,ledger);write(d/'validation.json',{'status':'timeout','error':'900-second client timeout; output not accepted','request_consumed':True});raise
 stderr_text=(d/'stderr.log').read_text()
 match=re.search(r'OpenAI Codex[^\n]*\n-+\n(.*?)\n-+',stderr_text,re.S)
 header=match.group(1) if match else '';fields={k.strip():v.strip() for k,v in re.findall(r'^([^:\n]+):\s*(.*)$',header,re.M)}
 if r.returncode or fields.get('provider')!='openai' or fields.get('model')!=MODEL or fields.get('reasoning effort')!=effort or fields.get('sandbox')!='read-only':
  ledger['entries'][-1]['status']='runtime_failed';write(ledger_path,ledger);raise ValueError('Worker failed or startup identity mismatch')
 value=decode_json(result_path.read_text());att={'provider':fields.get('provider'),'model':fields['model'],'reasoning_effort':fields['reasoning effort'],'startup_header_sha256':hashlib.sha256(header.encode()).hexdigest()}
 ledger['entries'][-1].update(status='responded',runtime_attestation=att,output_sha256=digest(value));write(ledger_path,ledger);return value,d,att

def round_schema(areas):
 event=strict({'at_s':{'type':'number','minimum':0,'maximum':160},'kind':choice(['move','kill','plant','defuse']),'actor':choice(IDS),'target':{'type':['string','null'],'enum':IDS+[None]},'area':choice(areas),'route':arr(choice(areas),0,8)})
 return strict({'number':{'type':'integer','minimum':1,'maximum':50},'buy_left':choice(['pistol','eco','force','half','full']),'buy_right':choice(['pistol','eco','force','half','full']),'start_areas':strict({id:choice(areas) for id in IDS}),'events':arr(event,1,12),'resolution':choice(['elimination','timeout','exploded','defused']),'turning_point':text()})
def batch_schema(state,context,agents,pack,max_rounds=None):
 name=state['maps'][state['map_index']]['map'];areas=list(context['maps'][name]['areas']);props={'previous_state_sha256':text(),'map':choice([name])}
 if state['stage']=='opening':
  props['lineup']=strict({id:strict({'player':choice(pack['rosters'][state['teams'][0 if id[0]=='L' else 1]]['players']),'agent':choice(agents)}) for id in IDS})
  props['opening_plan']=strict({'left':text(),'right':text()})
 else:props['adjustment']=strict({'left':text(),'right':text()})
 cap=12 if state['stage']=='opening' else max(2,25-state['round_number'])
 if max_rounds:cap=min(cap,max_rounds)
 props['rounds']=arr(round_schema(areas),1 if max_rounds else 12 if state['stage']=='opening' else 1,cap)
 return strict(props)
def map_packet(state,pack,context,agents,max_rounds=None):
 name=state['maps'][state['map_index']]['map']
 selected=[f for f in pack['facts'] if f['type']=='map_result' and f['value'].get('map')==name and set(f['value'].get('teams',[]))&set(state['teams'])]
 series=[f for f in pack['facts'] if f['type']=='completed_series' and set(f['value'].get('teams',[]))&set(state['teams'])]
 task='''本阶段使用真实地图语义区域，不用棋盘格、不输出凭空路线坐标。上下文中的区域名来自游戏资源目录，route用已存在area ID序列表示你假设的通路；不宣称已验证视线/碰撞。每回合只写改变局面的关键区域移动和交锋，最多12个关键事件，务必给下包/拆包留位置；不要为每个角色重复写无关移动。事件按时间先后逐个推演，每个回合结束后再推下一回合，不要朝任何预先选定的比分收束。每个回合先给十人的初始控图区域（不是声称真实出生坐标），每个动作actor必须存活；kill的target是对手且当时存活。kill.area是受害者所在接触区域；plant/defuse需活人到该Site（用事件area），plant只能进攻方，defuse只能防守方且需此前plant。move.route首项是该人当前区域，末项为事件area。kill/plant/defuse.route应为空。事件时间非降序，表示回合内秒，未模拟完整枪械/技能物理。每回合最后给resolution，胜者由脚本根据事件得出：elimination要求某方全灭，已下包后进攻方死光还不能判守方胜；timeout只可未下包（守方胜）；exploded必须已下包（攻方胜）；defused必须有有效defuse事件（守方胜）。不输出赢家或最终比分字段。
每图先13分且领先2分才结束，系列赛先赢三图。前12回合沿BP第一队起始边；13-24换边，13回合双边经济重新pistol；加时25开始假设第一队先攻，之后逐轮换边，双方full（这是显式模拟假设）。经济只预测pistol/eco/force/half/full档位与loss_streak，不编造信用点或宣称完整经济引擎。旧枪械/资源点/50%射击棋盘不参与。本图阵容使用last-observed名单作模拟首发，双方每队五特工不能重复，特工限定目录。每回合turning_point仅1句短中文事件因果，不写真实选手引语。'''
 cap=12 if state['stage']=='opening' else max(2,25-state['round_number'])
 if max_rounds:cap=min(cap,max_rounds)
 if state['stage']=='opening':task+='\n这是本图第一次请求：先给双方同时选出的阵容与开局想法，再按本批窗口顺序推演事件，不输出预定赢家。'
 else:task+='\n读取脚本已验算的比分、经济档位、连败与回合历史，调整双方策略，再按本批窗口继续。'
 task+=f"\n本批窗口：从第{state['round_number']}回合开始，最多{cap}回合；地图达到结束立即停止，未结束则完成本批窗口后交回脚本验算。不得输出窗口之后的回合。"
 task+='\n每个kill仅改变受害者位置及存活，不移动射手，射手仍在上一个位置；后续move.route必须从射手真实当前位置开始。不要让死者继续动作。move.route至少两个区域ID；若只是原地不动，省略该move事件，不要输出只有一项的route。elimination只有一队五人确实全部死亡才成立，双方仍有人存活不能判全灭。defuse事件表示已经完成拆包，不是尝试拆包，出现后只能resolution=defused；若拆包者被击杀且未拆完，则不要输出defuse事件。每次输出前内部核对存活名单与事件因果，不要用旁白替代缺失事件。'
 schedule=[{'round':n,'attacking_team':state['teams'][attacker(state,n)],'plant_actor_ids':[i for i in IDS if actor_side(i)==attacker(state,n)],'defuse_actor_ids':[i for i in IDS if actor_side(i)!=attacker(state,n)],'required_buy':'pistol' if n in [1,13] else 'full' if n>=25 else None} for n in range(state['round_number'],state['round_number']+cap)]
 return {'round_schedule':schedule,'task':task,'map_context':context['maps'][name],'agent_catalog':list(agents),'frozen_evidence_sha256':pack['content_sha256'],'evidence':{'rosters':{t:pack['rosters'][t] for t in state['teams']},'series':series,'this_map_facts':selected,'map_summary':{t:pack['team_summaries'][t]['by_map'].get(name,{'played':0}) for t in state['teams']},'gaps':pack['gaps']}}
def actor_side(id):return 0 if id[0]=='L' else 1
def attacker(state,number):
 initial=0 if state['maps'][state['map_index']]['first_team_start_side']=='ATK' else 1
 return initial if number<=12 else 1-initial if number<=24 else 0 if number%2 else 1
def apply_batch(before,value,context,agents,pack,allow_incomplete=False):
 expected={'previous_state_sha256','map','rounds'}|({'lineup','opening_plan'} if before['stage']=='opening' else {'adjustment'})
 if set(value)!=expected:raise ValueError('Unexpected batch fields, including supplied score/winner')
 if value['previous_state_sha256']!=digest(before):raise ValueError('Batch prior state mismatch')
 s=json.loads(json.dumps(before));name=s['maps'][s['map_index']]['map'];mapctx=context['maps'][name];areas=mapctx['areas'];frames=[];round_receipts=[]
 if value['map']!=name:raise ValueError('Wrong selected map')
 if before['stage']=='opening':
  lineup=value['lineup']
  if set(lineup)!=set(IDS):raise ValueError('Exactly ten actors required')
  for side in [0,1]:
   ids=[id for id in IDS if actor_side(id)==side]
   if {lineup[id]['player'] for id in ids}!=set(pack['rosters'][before['teams'][side]]['players']) or len({lineup[id]['agent'] for id in ids})!=5:raise ValueError('Lineup duplication or wrong player')
  if any(v['agent'] not in agents for v in lineup.values()):raise ValueError('Unknown agent')
  s['lineup']=lineup;s['opening_plan']=value['opening_plan'];frames.append({'kind':'lineup','map':name,'lineup':lineup,'plan':value['opening_plan'],'series_score':s['series_score'][:],'round_score':s['round_score'][:]})
 for round_value in value['rounds']:
  if set(round_value)!={'number','buy_left','buy_right','start_areas','events','resolution','turning_point'}:raise ValueError('Unexpected round result fields')
  if s['stage']=='finished' or s['map_index']!=before['map_index']:raise ValueError('Extra round after map/series finished')
  n=s['round_number'];start_hash=digest(s)
  if round_value['number']!=n:raise ValueError(f'Noncontiguous round; expected {n}')
  if set(round_value['start_areas'])!=set(IDS) or any(a not in areas for a in round_value['start_areas'].values()):raise ValueError('Initial area set invalid')
  atk=attacker(s,n);alive=set(IDS);positions=round_value['start_areas'].copy();plant=None;defused=False;last_time=-1
  buys=[round_value['buy_left'],round_value['buy_right']]
  if any(b not in ['pistol','eco','force','half','full'] for b in buys):raise ValueError('Unknown economy tier')
  if n in [1,13]:s['loss_streak']=[0,0]
  if n in [1,13] and buys!=['pistol','pistol']:raise ValueError('Half starts with pistol')
  if n>=25 and buys!=['full','full']:raise ValueError('Overtime loadout assumption is full')
  common={'map':name,'map_index':s['map_index'],'round_number':n,'attacking_team':s['teams'][atk],'lineup':s['lineup'],'series_score':s['series_score'][:],'round_score':s['round_score'][:],'buy':buys,'loss_streak':s['loss_streak'][:]}
  frames.append({**common,'kind':'round_start','positions':positions.copy(),'alive':sorted(alive),'copy':round_value['turning_point']})
  for event_index,e in enumerate(round_value['events']):
   if set(e)!={'at_s','kind','actor','target','area','route'}:raise ValueError(f'R{n} event{event_index}: event keys={sorted(e)}, required keys=at_s,kind,actor,target,area,route; every non-move must explicitly include route=[]')
   if e['at_s']<last_time or not 0<=e['at_s']<=160:raise ValueError('Nonmonotonic event time')
   last_time=e['at_s'];a=e['actor'];target=e['target'];area=e['area'];kind=e['kind'];route=e['route']
   if a not in alive or area not in areas:raise ValueError(f'R{n} event{event_index}: actor={a}, alive={sorted(alive)}, area={area}; dead actor or unavailable region')
   if kind=='move':
    if target is not None or len(route)<2 or route[0]!=positions[a] or route[-1]!=area or any(x not in areas for x in route):raise ValueError(f'R{n} event{event_index}: {a} current={positions[a]}, route={route}, destination={area}; move.route requires at least TWO region IDs (no one-element stay action), start=current, end=destination, all real IDs; kill does not move shooter')
    positions[a]=area
   elif kind=='kill':
    if route or target not in alive or actor_side(a)==actor_side(target):raise ValueError(f'R{n} event{event_index}: illegal kill actor={a}, target={target}, live actors={sorted(alive)}, route must be empty; cannot kill ally or already dead target')
    positions[target]=area;alive.remove(target)
   elif kind=='plant':
    if route or target is not None or plant or actor_side(a)!=atk or area not in mapctx['site_areas']:raise ValueError(f'R{n} event{event_index}: illegal plant actor={a}, ATK={s["teams"][atk]}, legal actors={[i for i in alive if actor_side(i)==atk]}, legal sites={mapctx["site_areas"]}, prior plant={plant}')
    plant=area;positions[a]=area
   elif kind=='defuse':
    if route or target is not None or not plant or actor_side(a)==atk or area!=plant or defused:raise ValueError(f'R{n} event{event_index}: invalid completed defuse actor={a}; live DEF actors={[i for i in alive if actor_side(i)!=atk]}, planted site={plant}, already defused={defused}; target=null, route=[] required')
    defused=True;positions[a]=area
   else:raise ValueError('Unsupported event')
   frames.append({**common,'kind':kind,'event':e,'event_index':event_index,'positions':positions.copy(),'alive':sorted(alive)})
  resolution=round_value['resolution']
  if defused and resolution!='defused':raise ValueError('Completed defuse already ends the round for DEF; another resolution is invalid')
  remaining=[sum(actor_side(id)==i for id in alive) for i in [0,1]]
  if resolution=='defused' and defused:win=1-atk
  elif resolution=='exploded' and plant and not defused:win=atk
  elif resolution=='timeout' and not plant and remaining[1-atk]>0:win=1-atk
  elif resolution=='elimination' and not remaining[1-atk] and remaining[atk]>0:win=atk
  elif resolution=='elimination' and not remaining[atk] and remaining[1-atk]>0 and not plant:win=1-atk
  else:raise ValueError(f'Round {n} resolution={resolution} inconsistent: survivors={sorted(alive)}, remaining left/right={remaining}, ATK={s["teams"][atk]}, plant={plant}, defused={defused}; completed defuse wins DEF, explosion needs plant and no defuse; elimination requires whole opponent team dead')
  s['round_score'][win]+=1;s['last_buy']=buys;s['loss_streak']=[0 if i==win else s['loss_streak'][i]+1 for i in [0,1]]
  s['history'].append({'round':n,'map':name,'winner':s['teams'][win],'score':s['round_score'][:],'buy':buys,'survivors':sorted(alive),'turning_point':round_value['turning_point']});s['history']=s['history'][-6:]
  frames.append({**common,'kind':'round_end','winner':s['teams'][win],'resolution':resolution,'round_score':s['round_score'][:],'positions':positions.copy(),'alive':sorted(alive),'copy':round_value['turning_point']})
  final_score=s['round_score'][:];s['round_number']+=1
  if max(final_score)>=13 and abs(final_score[0]-final_score[1])>=2:
   s['series_score'][win]+=1;s.setdefault('completed_maps',[]).append({'map':name,'score':final_score,'winner':s['teams'][win]});frames.append({**common,'kind':'map_end','winner':s['teams'][win],'round_score':final_score,'series_score':s['series_score'][:]})
   if s['series_score'][win]==3:s['stage']='finished';s['winner']=s['teams'][win];frames.append({**common,'kind':'series_end','winner':s['winner'],'series_score':s['series_score'][:],'round_score':final_score})
   else:s.update(stage='opening',map_index=s['map_index']+1,round_score=[0,0],round_number=1,loss_streak=[0,0],last_buy=['pistol','pistol'],lineup=None,history=[])
  else:s['stage']='continuation'
  round_receipts.append({'round':n,'map':name,'before_sha256':start_hash,'after_sha256':digest(s)})
 if not allow_incomplete and before['stage']=='opening' and len(value['rounds'])!=12:raise ValueError('Opening batch must contain exactly first half')
 if not allow_incomplete and before['stage']=='continuation' and s['map_index']==before['map_index'] and s['stage']!='finished' and s['round_number']<=24:raise ValueError('Continuation stopped before map end or overtime')
 return s,frames,round_receipts

def publish(out,pack):
 from paid_causal import publish_provider
 if out.resolve()!=(ROOT/'private/gpt-causal-bo5-20261016').resolve():raise ValueError('Use the shared causal runner and canonical output directory')
 publish_provider(out,pack,'codex')

def run_remaining(out,pack,max_rounds=None):
 context=json.loads((ROOT/'data/causal/map-context.json').read_text());agents=json.loads((ROOT/'data/causal/agents.json').read_text())['agents'];state_path=out/'state.json';s=json.loads(state_path.read_text());publish(out,pack)
 while s['stage']!='finished':
  stage=f'map{s["map_index"]+1}-{s["stage"]}-r{s["round_number"]}';extra=map_packet(s,pack,context,agents,max_rounds);sch=batch_schema(s,context,agents,pack,max_rounds)
  matching=[e for e in json.loads((out/'ledger.json').read_text())['entries'] if e['before_sha256']==digest(s) and e['stage']!='bp']
  if matching:
   last=matching[-1];previous=out/last['directory']/'validation.json'
   if last['status']=='reserved' and not (out/last['directory']/'response.json').exists():raise ValueError('Unfinished prior request; inspect before retry')
   if previous.exists():extra['previous_validation_error']=json.loads(previous.read_text()).get('error')
   else:
    response_path=out/last['directory']/'response.json'
    reason=json.loads(response_path.read_text()).get('choices',[{}])[0].get('finish_reason') if response_path.exists() else None
    extra['previous_validation_error']='Previous response exceeded output cap and produced no accepted answer; use the current smaller batch window and concise reasoning, generate JSON for only this window.' if reason=='length' else 'Previous completed response was malformed or invalid; generate a new valid batch from the unchanged state.'
   stage+='-retry'+str(len(matching))
  try:raw,d,att=call(stage,s,sch,extra,out,pack)
  except (json.JSONDecodeError,KeyError) as error:
   print('Completed malformed response: '+str(error),flush=True);continue
  validation={'status':'valid',**({'requested_batch_cap':max_rounds} if max_rounds else {})}
  try:
   if max_rounds and len(raw['rounds'])>max_rounds:raise ValueError('Output exceeds requested batch window')
   after,frames,receipts=apply_batch(s,raw,context,agents,pack,allow_incomplete=bool(max_rounds))
  except Exception as error:
   accepted=0
   for count in range(min(len(raw.get('rounds',[]))-1,max_rounds or 100),0,-1):
    candidate={**raw,'rounds':raw['rounds'][:count]}
    try:after,frames,receipts=apply_batch(s,candidate,context,agents,pack,allow_incomplete=True);accepted=count;break
    except ValueError:continue
   if not accepted:
    write(d/'validation.json',{'status':'invalid','error':str(error)});print('Invalid batch; budget-governed model retry: '+str(error),flush=True);continue
   validation={'status':'partial',**({'requested_batch_cap':max_rounds} if max_rounds else {}),'accepted_round_count':accepted,'original_round_count':len(raw['rounds']),'error':str(error),'raw_output_unchanged':True,'excluded_unvalidated_suffix':True}
   print('Accepted only '+str(accepted)+' validated prefix rounds; excluded invalid suffix: '+str(error),flush=True)
  write(d/'after.json',after);write(d/'frames.json',frames);write(d/'validation.json',{**validation,'after_sha256':digest(after),'round_receipts':receipts});write(state_path,after);s=after;publish(out,pack);print('Validated '+stage+'; series '+str(s['series_score'])+'; next '+s['stage']+' round '+str(s['round_number']),flush=True)

def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--bp-only',action='store_true');a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
 with (out/'run.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  pack=json.loads((ROOT/'data/evidence-v2.json').read_text());state_file=out/'state.json';s=json.loads(state_file.read_text()) if state_file.exists() else initial(pack)
  if s['stage']=='bp':
   v,d,att=call('bp',s,bp_schema(pack),out=out,pack=pack,extra={'task':'本次只预测10月17日VIT vs 100T一场BO5。VIT为败者组落入方优先选择A/B；普通BO5各ban一次；A/B/A/B选四图，剩余第五图；选边方B/A/B/A/B。输出先确定A/B身份、两ban、五图顺序及双方起始边（每图字段始终指teams[0]=VIT），不得给任何图或系列赛赢家。你的图序/起始边用于下游逐图推演。','frozen_evidence':pack})
   after=apply_bp(s,v,pack);write(d/'validation.json',{'status':'valid','after_sha256':digest(after)});write(d/'after.json',after);write(state_file,after);print('BP validated; next: '+after['maps'][0]['map'],flush=True)
  if not a.bp_only:run_remaining(out,pack)
if __name__=='__main__':main()
