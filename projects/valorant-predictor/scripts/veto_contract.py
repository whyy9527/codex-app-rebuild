"""Shanghai event-specific veto facts, model-owned choices, deterministic protocol."""
from tactical_contract import ROOT,digest,strict_json,MODELS

def schema(context):
 row={'type':'object','properties':{'priority_role':{'type':'string','enum':['A','B']},'bans':{'type':'array','minItems':2,'maxItems':2,'items':{'type':'string','enum':context['pool']}},'maps':{'type':'array','minItems':5,'maxItems':5,'items':{'type':'string','enum':context['pool']}},'a_start_sides':{'type':'array','minItems':5,'maxItems':5,'items':{'type':'string','enum':['ATK','DEF']}},'reason':{'type':'string','minLength':12,'maxLength':160}},'required':['priority_role','bans','maps','a_start_sides','reason'],'additionalProperties':False}
 return {'type':'object','$defs':{'case':row},'properties':{'cases':{'type':'object','properties':{k:{'$ref':'#/$defs/case'} for k in context['cases']},'required':list(context['cases']),'additionalProperties':False}},'required':['cases'],'additionalProperties':False}
def inputs(context,channel):
 fiction=strict_json((ROOT/f'data/{channel}-fiction.json').read_text());rows={}
 for key,case in context['cases'].items():
  teams=fiction['cases'][key]['input']['series']['teams']
  if len(teams)!=2 or case['priority_team'] not in teams:raise ValueError('Frozen series teams differ')
  rows[key]={**case,'teams':teams}
 return rows

def validate(raw,context):
 errors=[]
 if not isinstance(raw,dict) or set(raw)!= {'cases'} or not isinstance(raw['cases'],dict) or set(raw['cases'])!=set(context['cases']):return ['Exact eight case IDs required']
 for key,row in raw['cases'].items():
  if not isinstance(row,dict) or set(row)!=set(['priority_role','bans','maps','a_start_sides','reason']):errors.append(key+': exact fields required');continue
  if row['priority_role'] not in ['A','B']:errors.append(key+': invalid priority role')
  if not isinstance(row['bans'],list) or not isinstance(row['maps'],list) or len(row['bans'])!=2 or len(row['maps'])!=5:errors.append(key+': two bans and five maps required');continue
  if any(not isinstance(m,str) for m in row['bans']+row['maps']) or set(row['bans']+row['maps'])!=set(context['pool']):errors.append(key+': exactly seven unique official pool maps required')
  if not isinstance(row['a_start_sides'],list) or len(row['a_start_sides'])!=5 or any(s not in ['ATK','DEF'] for s in row['a_start_sides']):errors.append(key+': five legal initial A sides required')
  if not isinstance(row['reason'],str) or not 12<=len(row['reason'].strip())<=160:errors.append(key+': reason length invalid')
 return errors

def prompt(context,rows):
 return '''为2026上海VALORANT冠军赛最后两场做条件化地图veto和起始边预测，非真实赛况。只输出严格JSON，不联网、不用工具、不读文件。不能照搬LOL英雄BP。每个案例的priority_team有权选择A/B身份；你通过priority_role选身份。普通BO5两个ban按A、B顺序；双败总决赛两个ban均由胜者组队priority_team执行。随后四次pick按A/B/A/B，最后一张剩余图为决胜图。每张图选边权依次B/A/B/A/B；a_start_sides是A队在该图的起始边（ATK/DEF），你据此规划，实际行使选边的队由固定规则展开。每案两张禁用图+五张顺序图必须恰好覆盖官方七图池，不能重名。保持已有系列赛的对阵，不重算冠军或比分。
没有队伍逐图胜率或近期地图偏好统计：reason只能写本方案的假设取舍，不得捏造真实战队地图数据、已进行的BP或已观看录像。特工是地图确定后双方同时85秒选择，不在这里写英雄ban或轮流选特工。Ascent走位是既有独立固定场景，不能为凑展示强行保证Ascent入选，也不能说其代表本次BP后的实况。覆盖全部八案，中文理由简短。
冻结官方事实：'''+__import__('json').dumps({k:context[k] for k in ['id','pool','patch','rules','limitations']},ensure_ascii=False,separators=(',',':'))+'\n本模型自身原有推演所绑定对阵：'+__import__('json').dumps(rows,ensure_ascii=False,separators=(',',':'))+'\n唯一输出契约：'+__import__('json').dumps(schema(context),ensure_ascii=False,separators=(',',':'))
