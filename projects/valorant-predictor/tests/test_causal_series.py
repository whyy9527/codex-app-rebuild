import sys,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from causal_series import initial,apply_bp,apply_batch,digest,IDS,batch_schema,map_packet
PACK=json.loads((ROOT/'data/evidence-v2.json').read_text());CONTEXT=json.loads((ROOT/'data/causal/map-context.json').read_text());AGENTS=json.loads((ROOT/'data/causal/agents.json').read_text())['agents']
class CausalTests(unittest.TestCase):
 def state(self):
  s=initial(PACK);pool=next(f['value']['pool'] for f in PACK['facts'] if f['id']=='official:rules');bp={'previous_state_sha256':digest(s),'priority_role':'B','bans':pool[:2],'maps':[{'map':m,'first_team_start_side':'DEF','reason':'Synthetic test fixture','evidence_refs':['official:rules']} for m in pool[2:]],'reason':'Synthetic test fixture'}
  return apply_bp(s,bp,PACK)
 def terminal(self):
  s=self.state();s.update(stage='continuation',round_number=13,round_score=[12,0],series_score=[2,0]);names=list(AGENTS)[:5];s['lineup']={id:{'player':PACK['rosters'][s['teams'][0 if id[0]=='L' else 1]]['players'][i%5],'agent':names[i%5]} for i,id in enumerate(IDS)}
  area=CONTEXT['maps'][s['maps'][0]['map']]['site_areas'][0]
  r={'number':13,'buy_left':'pistol','buy_right':'pistol','start_areas':{id:area for id in IDS},'events':[{'at_s':i+1,'kind':'kill','actor':'L1','target':f'R{i+1}','area':area,'route':[]} for i in range(5)],'resolution':'elimination','turning_point':'Synthetic test events, never published as prediction'}
  return s,{'previous_state_sha256':digest(s),'map':s['maps'][0]['map'],'adjustment':{'left':'fixture','right':'fixture'},'rounds':[r]}
 def test_events_derive_map_and_series_result(self):
  s,v=self.terminal();after,frames,receipts=apply_batch(s,v,CONTEXT,AGENTS,PACK);self.assertEqual(after['winner'],'VIT');self.assertEqual(after['series_score'],[3,0]);self.assertEqual(frames[-1]['kind'],'series_end');self.assertEqual(receipts[0]['before_sha256'],digest(s));self.assertEqual(s['round_score'],[12,0])
 def test_final_winner_or_score_cannot_be_injected(self):
  s,v=self.terminal();v['winner']='100T'
  with self.assertRaises(ValueError):apply_batch(s,v,CONTEXT,AGENTS,PACK)
  s,v=self.terminal();v['rounds'][0]['score']=[0,13]
  with self.assertRaises(ValueError):apply_batch(s,v,CONTEXT,AGENTS,PACK)
 def test_prior_state_and_order_fail_closed(self):
  s,v=self.terminal();v['previous_state_sha256']='0'*64
  with self.assertRaises(ValueError):apply_batch(s,v,CONTEXT,AGENTS,PACK)
  s,v=self.terminal();v['rounds'][0]['number']=14
  with self.assertRaises(ValueError):apply_batch(s,v,CONTEXT,AGENTS,PACK)
 def test_dead_actor_cannot_act_or_die_twice(self):
  s,v=self.terminal();v['rounds'][0]['events'][1]['actor']='R1'
  with self.assertRaises(ValueError):apply_batch(s,v,CONTEXT,AGENTS,PACK)
  s,v=self.terminal();v['rounds'][0]['events'][1]['target']='R1'
  with self.assertRaises(ValueError):apply_batch(s,v,CONTEXT,AGENTS,PACK)
 def test_score_is_not_generated_by_schema(self):
  s,v=self.terminal();sch=batch_schema(s,CONTEXT,AGENTS,PACK);self.assertNotIn('winner',sch['properties']);self.assertNotIn('score',sch['properties']);self.assertNotIn('winner',sch['properties']['rounds']['items']['properties'])
 def test_no_spike_explosion_without_plant(self):
  s,v=self.terminal();v['rounds'][0]['resolution']='exploded'
  with self.assertRaises(ValueError):apply_batch(s,v,CONTEXT,AGENTS,PACK)
 def test_next_map_starts_from_derived_prior_map_result(self):
  s,v=self.terminal();s['series_score']=[0,0];v['previous_state_sha256']=digest(s);after,_,_=apply_batch(s,v,CONTEXT,AGENTS,PACK);self.assertEqual(after['stage'],'opening');self.assertEqual(after['map_index'],1);self.assertEqual(after['series_score'],[1,0]);self.assertEqual(after['round_score'],[0,0])
 def test_grand_final_uses_dynamic_team_names(self):
  s,v=self.terminal();s['teams']=['LOUD','100T'];v['previous_state_sha256']=digest(s);after,frames,_=apply_batch(s,v,CONTEXT,AGENTS,PACK);self.assertEqual(after['winner'],'LOUD');self.assertEqual(frames[-1]['winner'],'LOUD')
 def test_short_batch_preserves_valid_round_without_inventing_terminal(self):
  s,v=self.terminal();s['round_score']=[3,2];s['series_score']=[0,0];v['previous_state_sha256']=digest(s)
  after,frames,_=apply_batch(s,v,CONTEXT,AGENTS,PACK,allow_incomplete=True);self.assertEqual(after['round_score'],[4,2]);self.assertEqual(after['round_number'],14);self.assertIsNone(after['winner']);self.assertNotIn('map_end',[f['kind'] for f in frames])
 def test_route_must_continue_actor_position_and_cannot_be_fabricated(self):
  s,v=self.terminal();areas=list(CONTEXT['maps'][s['maps'][0]['map']]['areas']);v['rounds'][0]['events'].insert(0,{'at_s':0,'kind':'move','actor':'L1','target':None,'area':areas[-1],'route':[areas[-1],areas[-1]]})
  with self.assertRaisesRegex(ValueError,'current='):apply_batch(s,v,CONTEXT,AGENTS,PACK)
 def test_prompt_and_schema_have_one_matching_batch_window(self):
  s=self.state();packet=map_packet(s,PACK,CONTEXT,AGENTS,3);schema=batch_schema(s,CONTEXT,AGENTS,PACK,3)
  self.assertIn('最多3回合',packet['task']);self.assertNotIn('恰好1-12',packet['task']);self.assertEqual(len(packet['round_schedule']),schema['properties']['rounds']['maxItems'])
  s.update(stage='continuation',round_number=24);packet=map_packet(s,PACK,CONTEXT,AGENTS,3);schema=batch_schema(s,CONTEXT,AGENTS,PACK,3)
  self.assertIn('最多2回合',packet['task']);self.assertEqual(len(packet['round_schedule']),schema['properties']['rounds']['maxItems'])
 def test_completed_defuse_cannot_flip_to_attacker_elimination(self):
  s,v=self.terminal();r=v['rounds'][0];area=r['events'][0]['area'];r['events']=[{'at_s':0,'kind':'plant','actor':'L1','target':None,'area':area,'route':[]},{'at_s':.5,'kind':'defuse','actor':'R1','target':None,'area':area,'route':[]}]+r['events']
  with self.assertRaisesRegex(ValueError,'Completed defuse'):apply_batch(s,v,CONTEXT,AGENTS,PACK)
 def test_terminal_outcomes_are_symmetric_across_roles_and_overtime(self):
  for n,first,atk in [(13,'DEF',0),(13,'ATK',1),(25,'DEF',0),(26,'ATK',1)]:
   for resolution,winning_role in [('elimination','ATK'),('elimination','DEF'),('timeout','DEF'),('exploded','ATK'),('defused','DEF')]:
    s,v=self.terminal();s.update(round_number=n,round_score=[0,0],series_score=[0,0]);s['maps'][0]['first_team_start_side']=first;area=v['rounds'][0]['events'][0]['area'];a='L' if atk==0 else 'R';d='R' if atk==0 else 'L'
    event=lambda kind,actor,target=None,t=1:{'at_s':t,'kind':kind,'actor':actor,'target':target,'area':area,'route':[]}
    if resolution=='elimination':actor=a if winning_role=='ATK' else d;target=d if winning_role=='ATK' else a;events=[event('kill',actor+'1',target+str(i),i) for i in range(1,6)]
    elif resolution=='timeout':events=[event('kill',d+'1',a+'1')]
    else:events=[event('plant',a+'1')]+([event('defuse',d+'1',t=2)] if resolution=='defused' else [])
    buy='full' if n>=25 else 'pistol';v['previous_state_sha256']=digest(s);v['rounds']=[{'number':n,'buy_left':buy,'buy_right':buy,'start_areas':{id:area for id in IDS},'events':events,'resolution':resolution,'turning_point':'Explicit synthetic role-symmetry test, never a forecast'}]
    _,frames,_=apply_batch(s,v,CONTEXT,AGENTS,PACK,allow_incomplete=True);expected=s['teams'][atk if winning_role=='ATK' else 1-atk];self.assertEqual(frames[-1]['winner'],expected)
if __name__=='__main__' :unittest.main()
