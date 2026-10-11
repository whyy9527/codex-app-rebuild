import importlib.util,json,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('guide_replay',Path(__file__).resolve().parents[2]/'projects/exploration-ablation/replay04.py');r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
class GuideReplay(unittest.TestCase):
 def test_geometry_noise_does_not_create_reward_but_enabled_change_does(self):
  a=dict(snapshot='- img\n- button "word"',text_runs=[dict(text='word',rect=[0,0,10,10])],actions=[dict(role='button',test='hint-token',name='word',enabled=True,rect=[0,0,10,10],css={'color':'red'})]);b=json.loads(json.dumps(a));b['actions'][0].update(rect=[0,200,10,10],css={'color':'blue'});b['text_runs'][0]['rect']=[0,200,10,10]
  self.assertEqual(r.atoms(a),r.atoms(b));b['actions'][0]['enabled']=False;self.assertNotEqual(r.atoms(a),r.atoms(b))
 def test_unrevealed_successor_and_repetition_cannot_inflate_score(self):
  w=dict(actions=[dict(id='a',label='click word'),dict(id='b',label='hover word')],outcomes={'a':dict(atoms=['known']), 'b':dict(atoms=['future'])});p=dict(rules=[],repeat_penalty=0)
  before=r.replay(w,p);w['outcomes']['b']['atoms']=['future']*100;self.assertEqual(before,r.replay(w,p));self.assertEqual(before['score'],1);self.assertEqual([x['new_atoms']for x in before['trace']],[1,0])
