"""Evidence-bound decision proposals; scripts check structure, never invent weights."""
import json,math
from evidence_pack import digest,validate_pack
CASES={'lf':['VIT','100T'],'gf_vit':['LOUD','VIT'],'gf_100t':['LOUD','100T']}
FACTORS=['team_record','player_matchups','agent_pool','patch_and_rules','map_veto','recent_form','execution']
def schema(pack):
 ids=[f['id'] for f in pack['facts']]
 refs={'type':'array','items':{'type':'string','enum':ids},'minItems':1}
 row={'type':'object','properties':{'map':{'type':'string'},'a_start_side':{'type':'string','enum':['ATK','DEF']},'p_first':{'type':'number'},'reason':{'type':'string'},'evidence_refs':refs,'counterevidence_refs':{'type':'array','items':{'type':'string','enum':ids}},'change_condition':{'type':'string'},'missing_evidence':{'type':'array','items':{'type':'string'}}},'required':['map','a_start_side','p_first','reason','evidence_refs','counterevidence_refs','change_condition','missing_evidence'],'additionalProperties':False}
 factor={'type':'object','properties':{'id':{'type':'string','enum':FACTORS},'judgment':{'type':'string'},'evidence_refs':{'type':'array','items':{'type':'string','enum':ids}},'limitations':{'type':'string'}},'required':['id','judgment','evidence_refs','limitations'],'additionalProperties':False}
 case={'type':'object','properties':{'teams':{'type':'array','items':{'type':'string'},'minItems':2,'maxItems':2},'factors':{'type':'array','items':factor,'minItems':7,'maxItems':7},'priority_role':{'type':'string','enum':['A','B']},'bans':{'type':'array','items':{'type':'string'},'minItems':2,'maxItems':2},'bp_reason':{'type':'string'},'bp_evidence_refs':refs,'maps':{'type':'array','items':row,'minItems':5,'maxItems':5}},'required':['teams','factors','priority_role','bans','bp_reason','bp_evidence_refs','maps'],'additionalProperties':False}
 return {'type':'object','properties':{'input_sha256':{'type':'string'},'cases':{'type':'object','properties':{k:case for k in CASES},'required':list(CASES),'additionalProperties':False},'limitations':{'type':'string'}},'required':['input_sha256','cases','limitations'],'additionalProperties':False}
def validate_proposal(value,pack):
 validate_pack(pack)
 if not isinstance(value,dict) or set(value)!={'input_sha256','cases','limitations'} or value['input_sha256']!=pack['content_sha256']:raise ValueError('Proposal identity/input mismatch')
 if not isinstance(value['cases'],dict) or set(value['cases'])!=set(CASES):raise ValueError('Three exact conditional cases required')
 if not isinstance(value['limitations'],str) or not value['limitations'].strip():raise ValueError('Limitations required')
 ids={f['id'] for f in pack['facts']};pool=next(f['value']['pool'] for f in pack['facts'] if f['id']=='official:rules')
 def refs(v,nonempty=True):
  if not isinstance(v,list) or (nonempty and not v) or any(not isinstance(i,str) or i not in ids for i in v) or len(v)!=len(set(v)):raise ValueError('Unknown, duplicate or absent evidence reference')
 for key,teams in CASES.items():
  c=value['cases'][key]
  if set(c)!={'teams','factors','priority_role','bans','bp_reason','bp_evidence_refs','maps'} or c['teams']!=teams or c['priority_role'] not in ['A','B']:raise ValueError('Case identity/shape mismatch')
  if key.startswith('gf') and c['priority_role']!='A':raise ValueError('Upper finalist LOUD owns both GF bans')
  if not isinstance(c['bp_reason'],str) or not c['bp_reason'].strip():raise ValueError('BP reason missing')
  if not isinstance(c['factors'],list) or len(c['factors'])!=len(FACTORS) or {f.get('id') for f in c['factors']}!=set(FACTORS):raise ValueError('Seven exact factors required')
  for f in c['factors']:
   if set(f)!={'id','judgment','evidence_refs','limitations'} or any(not isinstance(f[k],str) or not f[k].strip() for k in ['judgment','limitations']):raise ValueError('Factor judgment and limitations required')
   refs(f['evidence_refs'],False)
  refs(c['bp_evidence_refs'])
  if len(c['bans'])!=2 or len(c['maps'])!=5 or sorted(c['bans']+[m['map'] for m in c['maps']])!=sorted(pool):raise ValueError('Seven unique maps must be exhausted by two bans and five played-order maps')
  for m in c['maps']:
   if set(m)!={'map','a_start_side','p_first','reason','evidence_refs','counterevidence_refs','change_condition','missing_evidence'}:raise ValueError('Map fields mismatch')
   if m['a_start_side'] not in ['ATK','DEF'] or type(m['p_first']) not in [int,float] or not math.isfinite(m['p_first']) or not 0<m['p_first']<1:raise ValueError('Invalid side or probability')
   if any(not isinstance(m[k],str) or not m[k].strip() for k in ['reason','change_condition']):raise ValueError('Reason and falsifying condition required')
   if not isinstance(m['missing_evidence'],list) or any(not isinstance(s,str) or not s.strip() for s in m['missing_evidence']):raise ValueError('Typed missing-evidence text required')
   refs(m['evidence_refs']);refs(m['counterevidence_refs'],False)
 return True
def decision_prompt(pack):
 return ('证据引用只允许facts数组里的id原样字符串；team_summaries、rosters是汇总字段名，不能当evidence_refs；map引用必须含完整图号，如map:754736:1。不要省略、编造或改写ID。\n你是瓦洛兰特赛前分析员。只进行一次完整独立分析，不扮演人格、不辩论、不知道其他模型答案。对每个条件对阵逐项判断：战队战绩、选手对位、实际特工使用、版本规则、地图BP、近期状态、执行表现。FACTORS七个固定ID各一项；每项给具体判断、证据引用和局限。操作/执行只可用现有回合与选手统计作有限观察，不能声称看过录像或推断枪法心理。没有证据的因素明确无法判断，引用可为空，不编造权重。'+'''\n只使用冻结证据包。官方与VLR二级来源不能混称；最近已出场阵容不等于未来确认首发。不得把缺失的伤病、训练赛、心理状态当事实。逐图样本少，解释局限；不从博彩赔率取胜率，不声称统计校准。证据引用证明可追溯，不证明因果。\n比赛范围仅17日VIT vs 100T败决，以及18日LOUD分别对VIT/100T两种总决赛条件。不得沿用旧剧情决定对阵，不预先指定赢家或比分。每案先给合规地图veto和起始边，再由你判断五张图各自单图概率p_first。每图概率取决于该地图/起始边条件，不是系列赛概率；解释证据、最强反证、会改变判断的条件及缺口。双方选特工同时进行，不是LoL轮流英雄BP。总决赛LOUD为A并拥有两ban；普通BO5的A/B优先权可假设但须说明。按官方规则给五图顺序；进程与BO5结果由脚本在你的概率冻结后算。不要把所有地图都写成相同概率来回避分析；如证据不足以区分，诚实解释。可引用official:rules说明地图缺样本，不能编造该队该图表现。\n输出严格JSON，无工具、联网或文件操作。契约：'''+json.dumps(schema(pack),ensure_ascii=False,separators=(',',':'))+'\n证据包：'+json.dumps(pack,ensure_ascii=False,separators=(',',':')))

def unwrap_proposal(value):
 """Recognize one nonsemantic JSON-object wrapper; never repair decision fields."""
 if isinstance(value,dict) and set(value)=={'type','input_sha256','cases','limitations'} and value['type']=='json_object':
  return {k:v for k,v in value.items() if k!='type'},[{'field':'type','value':'json_object','action':'omit_transport_metadata','semantic_fields_unchanged':True}]
 return value,[]

def parse_completion(raw):
 """Recover only proven outer delimiters; preserve every authored case value."""
 import re
 from tactical_contract import strict_json
 try:return strict_json(raw),[]
 except (ValueError,json.JSONDecodeError):
  repaired=raw;changes=[]
  patterns=['},{"'+key+'":' for key in ['gf_vit','gf_100t']]
  if all(repaired.count(pattern)==1 for pattern in patterns):
   for key,pattern in zip(['gf_vit','gf_100t'],patterns):
    repaired=repaired.replace(pattern,'},"'+key+'":');changes.append({'case':key,'removed':'extra outer { before case key'})
  else:
   matches=list(re.finditer('"gf_100t":',raw))
   if len(matches)!=1:raise ValueError('Not a recognized outer delimiter defect')
   _,length=json.JSONDecoder().raw_decode(raw[matches[0].end():]);end=matches[0].end()+length
   if not raw[end:].lstrip().startswith(',"limitations":'):raise ValueError('Missing outer case delimiter cannot be proven')
   repaired=raw[:end]+'}'+raw[end:];changes.append({'inserted':'one missing cases closing } before top-level limitations'})
  value=strict_json(repaired)
  if set(value)!= {'input_sha256','cases','limitations'} or set(value['cases'])!=set(CASES):raise ValueError('Unexpected repaired object shape')
  for key in CASES:
   matches=list(re.finditer('"'+key+'":',raw))
   if len(matches)!=1:raise ValueError('Ambiguous original case')
   original,_=json.JSONDecoder().raw_decode(raw[matches[0].end():])
   if original!=value['cases'][key]:raise ValueError('A decision value changed during repair')
  return value,[{'action':'outer_json_delimiter_only','changes':changes,'all_three_original_case_objects_identical':True,'probabilities_reasons_and_references_unchanged':True}]
