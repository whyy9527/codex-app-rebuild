"""Mechanical fixtures only; these are never published as model outputs."""
import copy,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from tactical_contract import MODELS,digest,strict_json,validate,validate_graph,public_plan
from run_tactical_models import approval,prepare,reserve

class TacticalContractTests(unittest.TestCase):
 def setUp(self):
  self.context=strict_json((ROOT/'data/tactical/context.json').read_text());self.raw={'headline':'测试夹具禁止发布','attack_goal':'测试边界与时序，不对应模型方案','defense_goal':'固定站位验证，不对应真实赛况','actors':{}}
  for side,prefix in [('attack','A'),('defend','D')]:
   for i,node in enumerate(self.context['start_nodes'][side][:5],1):self.raw['actors'][prefix+str(i)]={'intent':'仅用于机械测试的站位','waypoints':[{'at_s':0,'node':node},{'at_s':30,'node':node}]}
 def test_frozen_graph_matches_asset_and_floor(self):
  self.assertTrue(validate_graph(self.context));bad=copy.deepcopy(self.context);bad['edges'][0]['points'][1]=[0,0]
  with self.assertRaises(ValueError):validate_graph(bad)
 def test_valid_plan_keeps_original_and_runtime_provenance(self):
  before=copy.deepcopy(self.raw);self.assertEqual(validate(self.raw,self.context),[])
  result=public_plan(self.raw,self.context,'codex',{'model':MODELS['codex']},[{'status':'valid'}],'test-only')
  self.assertEqual(self.raw,before);self.assertEqual(result['raw_plan_sha256'],digest(before))
  with self.assertRaises(ValueError):public_plan(self.raw,self.context,'codex',{'model':'wrong'},[],'test-only')
 def test_invalid_paths_are_rejected_without_repair(self):
  self.raw['actors']['A1']['waypoints'][1]['node']='b_site';before=copy.deepcopy(self.raw)
  self.assertTrue(any('No permitted edge' in e for e in validate(self.raw,self.context)));self.assertEqual(self.raw,before)
 def test_timing_count_and_duplicate_initial_positions(self):
  for mutate,expected in [(lambda v:v['actors'].pop('A5'),'exact fields'),(lambda v:v['actors']['A2']['waypoints'][0].update(node=v['actors']['A1']['waypoints'][0]['node']),'distinct'),(lambda v:v['actors']['A1']['waypoints'][1].update(at_s=0),'strictly increase'),(lambda v:v['actors']['A1']['waypoints'][1].update(node=[]),'unknown node')]:
   value=copy.deepcopy(self.raw);mutate(value);self.assertTrue(any(expected in e for e in validate(value,self.context)))
  edge=self.context['edges'][0];self.raw['actors']['A1']['waypoints']=[{'at_s':0,'node':edge['a']},{'at_s':.1,'node':edge['b']},{'at_s':30,'node':edge['b']}]
  self.assertTrue(any('insufficient travel time' in e for e in validate(self.raw,self.context)))
 def test_json_duplicate_and_nonfinite_values_rejected(self):
  for text in ['{"A1":1,"A1":2}','{"at_s":NaN}']:
   with self.assertRaises(ValueError):strict_json(text)
  self.assertEqual(digest({'t':30.0}),digest({'t':30}))
 def test_prepare_has_no_generation_and_explicit_approval_required(self):
  with tempfile.TemporaryDirectory() as temp:
   out=Path(temp);prepare(self.context,out);self.assertFalse((out/'ledger.json').exists())
   with self.assertRaises(ValueError):approval(None)
   file=out/'approval.json';file.write_text(json.dumps({'approved':False}))
   with self.assertRaises(ValueError):approval(file)
 def test_budget_reserves_before_calls_and_stops_at_cap(self):
  with tempfile.TemporaryDirectory() as temp:
   out=Path(temp);prepare(self.context,out);allowed={'max_total_cny':5}
   for _ in range(2):reserve(out,'doubao',[{'content':'test fixture'}],allowed)
   with self.assertRaisesRegex(ValueError,'Per-model'):reserve(out,'doubao',[],allowed)
   with self.assertRaisesRegex(ValueError,'Total API'):reserve(out,'mimo',[],{'max_total_cny':.00001})
   self.assertEqual(json.loads((out/'ledger.json').read_text())['calls'],{'doubao':2})
   with self.assertRaisesRegex(ValueError,'input token bound'):reserve(out,'deepseek',['x'*25000],allowed)
