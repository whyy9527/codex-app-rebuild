"""Canonical raw-plan schema, validation, graph projection and immutable provenance."""
from pathlib import Path
import base64,hashlib,json,math,zlib
ROOT=Path(__file__).resolve().parents[1]
MODELS={'codex':'gpt-6.1-sol','deepseek':'deepseek-flash','doubao':'doubao-seed-2-1-pro-260915','mimo':'mimo-v2.6-pro'}
LABELS={'codex':'GPT-6.1 sol','deepseek':'DeepSeek V4.1 Flash','doubao':'豆包','mimo':'MiMo V2.6 Pro'}

def digest(value):
 def numbers(v):
  if isinstance(v,float) and v.is_integer():return int(v)
  if isinstance(v,dict):return {k:numbers(x) for k,x in v.items()}
  if isinstance(v,list):return [numbers(x) for x in v]
  return v
 return hashlib.sha256(json.dumps(numbers(value),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def strict_json(text):
 def pairs(rows):
  d={}
  for k,v in rows:
   if k in d:raise ValueError('Duplicate JSON key: '+k)
   d[k]=v
  return d
 return json.loads(text,object_pairs_hook=pairs,parse_constant=lambda v:(_ for _ in ()).throw(ValueError('Non-finite JSON number: '+v)))
def schema(context):
 point={'type':'object','properties':{'at_s':{'type':'number','minimum':0,'maximum':context['duration_s']},'node':{'type':'string','enum':list(context['nodes'])}},'required':['at_s','node'],'additionalProperties':False}
 actor={'type':'object','properties':{'intent':{'type':'string','minLength':4,'maxLength':120},'waypoints':{'type':'array','minItems':2,'maxItems':8,'items':{'$ref':'#/$defs/point'}}},'required':['intent','waypoints'],'additionalProperties':False}
 return {'$defs':{'point':point,'actor':actor},'type':'object','properties':{'headline':{'type':'string','minLength':5,'maxLength':80},'attack_goal':{'type':'string','minLength':8,'maxLength':180},'defense_goal':{'type':'string','minLength':8,'maxLength':180},'actors':{'type':'object','properties':{key:{'$ref':'#/$defs/actor'} for key in context['actors']},'required':list(context['actors']),'additionalProperties':False}},'required':['headline','attack_goal','defense_goal','actors'],'additionalProperties':False}
def edge_for(context,a,b):
 if a==b:return {'a':a,'b':b,'length':0,'points':[context['nodes'][a]['xy'],context['nodes'][a]['xy']]}
 for edge in context['edges']:
  if edge['a']==a and edge['b']==b:return edge
  if edge['a']==b and edge['b']==a:return {**edge,'a':a,'b':b,'points':list(reversed(edge['points']))}
 raise ValueError('No permitted edge '+a+' -> '+b)
def validate_graph(context,root=ROOT):
 audit=context['geometry_audit'];w,h=audit['raster_size'];mask=zlib.decompress(base64.b64decode(audit['mask_zlib_base64']))
 if len(mask)!=w*h or hashlib.sha256(mask).hexdigest()!=audit['mask_sha256']:raise ValueError('Frozen floor mask digest mismatch')
 if hashlib.sha256((root/context['map']['image']).read_bytes()).hexdigest()!=context['map']['sha256']:raise ValueError('Map asset digest mismatch')
 def floor(point):
  x,y=point
  if not (0<=x<1000 and 0<=y<1000):return False
  return mask[min(h-1,round(y*h/1000))*w+min(w-1,round(x*w/1000))]==255
 for name,node in context['nodes'].items():
  if not floor(node['xy']):raise ValueError('Node outside frozen floor: '+name)
 for edge in context['edges']:
  if edge['points'][0]!=context['nodes'][edge['a']]['xy'] or edge['points'][-1]!=context['nodes'][edge['b']]['xy']:raise ValueError('Edge endpoints differ')
  length=0
  for a,b in zip(edge['points'],edge['points'][1:]):
   distance=math.dist(a,b);length+=distance
   for i in range(max(1,math.ceil(distance*2))+1):
    f=i/max(1,math.ceil(distance*2));p=[a[0]+(b[0]-a[0])*f,a[1]+(b[1]-a[1])*f]
    if not floor(p):raise ValueError('Edge leaves frozen floor: '+edge['a']+'/'+edge['b'])
  if abs(length-edge['length'])>.001:raise ValueError('Edge distance differs')
 return True

def validate(value,context):
 errors=[]
 def fields(v,keys,path):
  if not isinstance(v,dict) or set(v)!=set(keys):errors.append(path+': exact fields required '+','.join(keys));return False
  return True
 def text(v,lo,hi,path):
  if not isinstance(v,str) or not lo<=len(v.strip())<=hi:errors.append(path+': text length '+str(lo)+'..'+str(hi))
 if not fields(value,['headline','attack_goal','defense_goal','actors'],'root'):return errors
 text(value['headline'],5,80,'headline');text(value['attack_goal'],8,180,'attack_goal');text(value['defense_goal'],8,180,'defense_goal')
 if not fields(value['actors'],context['actors'],'actors'):return errors
 starts={'attack':[],'defend':[]}
 for key,actor in value['actors'].items():
  path='actors.'+key;side=context['actors'][key]['side']
  if not fields(actor,['intent','waypoints'],path):continue
  text(actor['intent'],4,120,path+'.intent');points=actor['waypoints']
  if not isinstance(points,list) or not 2<=len(points)<=8:errors.append(path+': 2..8 waypoints required');continue
  safe=[]
  for i,point in enumerate(points):
   if not fields(point,['at_s','node'],path+'.waypoints.'+str(i)):continue
   t=point['at_s'];node=point['node']
   if type(t) not in [int,float] or not math.isfinite(t) or not 0<=t<=context['duration_s']:errors.append(path+': invalid timestamp');continue
   if not isinstance(node,str) or node not in context['nodes']:errors.append(path+': unknown node '+str(node));continue
   safe.append(point)
  if len(safe)!=len(points):continue
  if points[0]['at_s']!=0 or points[-1]['at_s']!=context['duration_s']:errors.append(path+': first/last timestamps must be 0/'+str(context['duration_s']))
  if points[0]['node'] not in context['start_nodes'][side]:errors.append(path+': initial node not permitted for '+side)
  starts[side].append(points[0]['node'])
  for a,b in zip(points,points[1:]):
   dt=b['at_s']-a['at_s']
   if dt<=0:errors.append(path+': timestamps must strictly increase');continue
   try:edge=edge_for(context,a['node'],b['node'])
   except ValueError as e:errors.append(path+': '+str(e));continue
   if edge['length']/dt>context['max_speed_units_s']+1e-6:errors.append(path+': insufficient travel time '+a['node']+' -> '+b['node']+' (need >= '+str(round(edge['length']/context['max_speed_units_s'],2))+'s)')
 for side,nodes in starts.items():
  if len(nodes)==5 and len(set(nodes))!=5:errors.append(side+': five distinct initial positions required')
 return errors

def public_plan(raw,context,channel,attestation,attempts,created_at):
 errors=validate(raw,context)
 if errors:raise ValueError('; '.join(errors))
 if attestation.get('model')!=MODELS[channel]:raise ValueError('Runtime model identity differs')
 return {'schema_version':1,'kind':'model_tactical_plan','channel':channel,'label':'真实模型生成的战术方案 · 非真实赛况','scenario_id':context['id'],'context_sha256':digest(context),'raw_plan_sha256':digest(raw),'created_at':created_at,'runtime_attestation':attestation,'attempts':attempts,'plan':raw}

def prompt(context):
 graph={'id':context['id'],'duration_s':context['duration_s'],'max_speed_units_s':context['max_speed_units_s'],'scenario':context['scenario'],'assumptions':context['assumptions'],'actors':context['actors'],'start_nodes':context['start_nodes'],'nodes':context['nodes'],'edges':[{k:e[k] for k in ['a','b','length']} for e in context['edges']]}
 return '''你独立为指定 VALORANT 假设场景规划双方的30秒站位与移动。不是赛事事实或胜负预测。不要联网、调用工具或读写文件；只输出严格JSON，不用围栏或schema元字段。不要虚构模型对话或真实选手表现。
按给定图谱选择节点与时间，不输出自造x/y坐标，不使用未列出的边。每个人覆盖0到30秒，时间严格递增；可在相同节点停留。每次移动必须是给定的一条边，时间差至少为length/max_speed_units_s。必须覆盖十个固定角色键、每侧五人，起点从各自start_nodes选择且同侧五个起点不同。假设阵容已固定，不能改特工。允许把人留在原位，优先可执行的合理分工。headline、attack_goal、defense_goal以及每人intent用简短中文说明取舍。模型选择位置和时间；坐标与合法通路由图谱确定性展开。不得声称已运行FPS物理、模拟枪械技能或保证真实比赛走位。
冻结共同输入：\n'''+json.dumps(graph,ensure_ascii=False,separators=(',',':'))+'\n唯一输出契约：\n'+json.dumps(schema(context),ensure_ascii=False,separators=(',',':'))
