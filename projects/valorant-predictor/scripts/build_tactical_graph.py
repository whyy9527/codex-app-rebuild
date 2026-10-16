"""Build the frozen Ascent planning graph from the existing unmodified minimap.

The mask is a 2D planning aid, not a Riot navmesh. Plant-zone boundary markings
may be crossed where yellow and gray floor meet; solid outlines/void stay blocked.
"""
from pathlib import Path
import base64,hashlib,json,math,zlib
from collections import deque
from PIL import Image,ImageFilter
ROOT=Path(__file__).resolve().parents[1]

def build(root=ROOT):
 image=root/'assets/tactical/ascent.png';im=Image.open(image).convert('RGBA');w,h=im.size;px=im.load()
 def floor(c):r,g,b,a=c;return a==255 and 100<=r<=160 and r==g==b
 def zone(c):r,g,b,a=c;return a==255 and max(abs(r-152),abs(g-152),abs(b-118))<=4
 mask=Image.new('L',im.size);m=mask.load()
 for y in range(h):
  for x in range(w):m[x,y]=255 if floor(px[x,y]) or zone(px[x,y]) else 0
 for y in range(4,h-4):
  for x in range(4,w-4):
   r,g,b,a=px[x,y]
   if a==255 and min(r,g,b)>190:
    for dx,dy in [(1,0),(0,1)]:
     if any((zone(px[x-dx*k,y-dy*k]) and floor(px[x+dx*j,y+dy*j])) or (floor(px[x-dx*k,y-dy*k]) and zone(px[x+dx*j,y+dy*j])) for k in range(1,5) for j in range(1,5)):
      m[x,y]=255;break
 mask=mask.filter(ImageFilter.MinFilter(5));step=4
 free={(x,y) for y in range(2,h,step) for x in range(2,w,step) if mask.getpixel((x,y))==255}
 def neighbors(p):
  x,y=p
  for n in [(x-step,y),(x+step,y),(x,y-step),(x,y+step)]:
   if n in free and all(mask.getpixel((round(x+(n[0]-x)*i/step),round(y+(n[1]-y)*i/step)))==255 for i in range(step+1)):yield n
 seed=min(free,key=lambda p:(p[0]-836)**2+(p[1]-583)**2);component={seed};q=deque([seed])
 while q:
  for n in neighbors(q.popleft()):
   if n not in component:component.add(n);q.append(n)
 anchors={
 'atk_spawn':('进攻出生区',817,569),'a_lobby':('A 大厅',603,259),'a_main':('A 入口',484,201),
 'a_tree':('A 树房',398,295),'a_site':('A 包点',310,150),'a_garden':('A 花园',285,309),
 'def_spawn':('防守出生区',132,434),'mid_courtyard':('中路庭院',493,488),'mid_top':('中路上段',665,380),
 'mid_market':('中路市场',298,497),'mid_link':('中路连接',514,617),'b_lobby':('B 大厅',717,678),
 'b_main':('B 入口',405,712),'b_site':('B 包点',285,790)}
 nodes={};raw_nodes={}
 for key,(label,x,y) in anchors.items():
  raw=(x*w/1000,y*h/1000);point=min(component,key=lambda p:(p[0]-raw[0])**2+(p[1]-raw[1])**2)
  if math.dist(raw,point)>16:raise ValueError('Anchor outside reviewed floor: '+key)
  raw_nodes[key]=point;nodes[key]={'label':label,'xy':[round(point[0]*1000/w,4),round(point[1]*1000/h,4)]}
 pairs=[('atk_spawn','a_lobby'),('atk_spawn','mid_top'),('atk_spawn','b_lobby'),('a_lobby','a_main'),('a_lobby','mid_top'),('a_main','a_tree'),('a_tree','a_site'),('a_tree','a_garden'),('a_garden','def_spawn'),('mid_top','mid_courtyard'),('mid_courtyard','a_tree'),('mid_courtyard','mid_market'),('mid_courtyard','mid_link'),('mid_link','b_lobby'),('mid_link','b_main'),('b_lobby','b_main'),('b_main','b_site'),('b_site','mid_market'),('mid_market','def_spawn')]
 edges=[]
 for start,end in pairs:
  source,target=raw_nodes[start],raw_nodes[end]
  parents={source:None};q=deque([source])
  while q and target not in parents:
   current=q.popleft()
   for n in neighbors(current):
    if n not in parents:parents[n]=current;q.append(n)
  if target not in parents:raise ValueError('Disconnected route '+start+'/'+end)
  path=[];node=target
  while node is not None:path.append(node);node=parents[node]
  path.reverse();compact=[path[0]]
  for i in range(1,len(path)-1):
   if (path[i][0]-path[i-1][0],path[i][1]-path[i-1][1])!=(path[i+1][0]-path[i][0],path[i+1][1]-path[i][1]):compact.append(path[i])
  compact.append(path[-1]);points=[[round(x*1000/w,4),round(y*1000/h,4)] for x,y in compact]
  edges.append({'a':start,'b':end,'length':round(sum(math.dist(a,b) for a,b in zip(points,points[1:])),4),'points':points})
 lineup={'attack':[('wushu','捷风','决斗'),('hunter','猎枭','先锋'),('wraith','幽影','控场'),('killjoy','奇乐','哨卫'),('grenadier','K/O','先锋')],'defend':[('clay','雷兹','决斗'),('breach','铁臂','先锋'),('gumshoe','零','哨卫'),('pandemic','蝰蛇','控场'),('guide','斯凯','先锋')]}
 actors={prefix+str(i+1):{'side':side,'number':i+1,'icon':icon,'agent':name,'role':role} for side,prefix in [('attack','A'),('defend','D')] for i,(icon,name,role) in enumerate(lineup[side])}
 value={'schema_version':1,'id':'ascent-default-control-30s-v1','map':{'id':'ascent','name':'亚海悬城','english':'ASCENT','image':'assets/tactical/ascent.png','sha256':hashlib.sha256(image.read_bytes()).hexdigest(),'sites':[['A',310,155],['B',285,800]]},'duration_s':30,'max_speed_units_s':35,'title':'同阵容 · 亚海悬城 30 秒默认控图方案','scenario':'假设的5v5标准回合控图决策。回放0秒为双方进入基础控图区的分析起点，不是开局出生时刻。红方选择进攻A/B或继续控图，蓝方选择守点与轮转。双方均为给定假设阵容，不绑定真实战队或选手。','assumptions':['可操作门均视为已打开；不模拟技能改地形、穿墙、跳跃、高低差与射击。','仅检查此二维规划图谱上的连通性、边界、时间和数量；不是FPS物理模拟器，也不保证真实比赛走位可复现。','模型独立选择节点、时间与理由；坐标和节点间通路由冻结地图图谱确定性展开，不静默修复模型路线。'],'actors':actors,'start_nodes':{'attack':['atk_spawn','a_lobby','a_main','mid_top','mid_courtyard','mid_link','b_lobby','b_main'],'defend':['a_site','a_tree','a_garden','def_spawn','mid_market','b_site']},'nodes':nodes,'edges':edges,'geometry_audit':{'source':'Existing Riot game minimap via Valorant-API; conservative raster floor plus plant-zone marking interpretation','source_sha256':hashlib.sha256(image.read_bytes()).hexdigest(),'raster_size':[w,h],'grid_step_px':step,'clearance_px':2,'mask_zlib_base64':base64.b64encode(zlib.compress(mask.tobytes(),9)).decode(),'mask_sha256':hashlib.sha256(mask.tobytes()).hexdigest()}}
 return value
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--out',type=Path);a=p.parse_args();value=build(a.root);dest=a.out or a.root/'data/tactical/context.json';dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'nodes':len(value['nodes']),'edges':len(value['edges']),'context_bytes':dest.stat().st_size}))
