import json,os,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from paid_causal import Budget,usage_fields,cost,complete_bp,make_call,c,ROOT
class PaidBudgetTests(unittest.TestCase):
 def root(self,path):
  p=Path(path);(p/'approval.json').write_text(json.dumps({'approved':True,'max_total_cny':40,'models':['deepseek','doubao','mimo']}));return p
 def test_unknown_usage_is_unknown_and_keeps_reservation(self):
  with tempfile.TemporaryDirectory() as d:
   b=Budget(self.root(d));id=b.reserve('doubao','bp','one',10000,1000,0);e=b.settle(id,None,1,'HTTP failure');self.assertIsNone(e['usage']['input_tokens']);self.assertEqual(e['budget_charge_upper_cny'],e['reserved_cny']);self.assertIsNone(e['actual_invoice_cny'])
 def test_known_usage_releases_only_unused_conservative_reservation(self):
  with tempfile.TemporaryDirectory() as d:
   b=Budget(self.root(d));id=b.reserve('deepseek','bp','one',10000,1000,0);e=b.settle(id,{'id':'test','usage':{'prompt_tokens':100,'completion_tokens':10,'prompt_tokens_details':{'cached_tokens':50},'completion_tokens_details':{'reasoning_tokens':0}}},1);self.assertEqual(e['usage']['cached_input_tokens'],50);self.assertEqual(e['usage']['reasoning_tokens'],0);self.assertAlmostEqual(e['budget_charge_upper_cny'],cost('deepseek',100,10));self.assertLess(e['estimated_cny_from_reported_usage'],e['budget_charge_upper_cny'])
 def test_cap_and_duplicate_request_are_rejected_before_call(self):
  with tempfile.TemporaryDirectory() as d:
   b=Budget(self.root(d));b.reserve('mimo','bp','same',1000,1000,0)
   with self.assertRaises(ValueError):b.reserve('mimo','bp','same',1000,1000,0)
   with self.assertRaises(ValueError):b.reserve('doubao','big','other',10000000,10000000,0)
 def test_absent_metadata_is_not_reported_as_zero(self):
  u=usage_fields({'prompt_tokens':123,'completion_tokens':45});self.assertEqual(u['input_tokens'],123);self.assertIsNone(u['reasoning_tokens']);self.assertIsNone(u['cached_input_tokens'])
 def test_cap_increase_keeps_previous_charges_and_requires_ledger_migration(self):
  with tempfile.TemporaryDirectory() as d:
   root=self.root(d);b=Budget(root);c.write(root/'budget-ledger.json',{'cap_cny':40,'entries':[{'key':'historic','channel':'deepseek','reserved_cny':38.8963548,'budget_charge_upper_cny':38.8963548}]})
   approval=json.loads((root/'approval.json').read_text());approval['max_total_cny']=50;c.write(root/'approval.json',approval)
   with self.assertRaisesRegex(ValueError,'caps differ'):b.reserve('mimo','continue','new',1000,1000,0)
   ledger=json.loads((root/'budget-ledger.json').read_text());ledger['cap_cny']=50;c.write(root/'budget-ledger.json',ledger);b.reserve('mimo','continue','new',1000,1000,0)
   ledger=json.loads((root/'budget-ledger.json').read_text());self.assertEqual(ledger['entries'][0]['budget_charge_upper_cny'],38.8963548);self.assertEqual(len(ledger['entries']),2)
 def test_one_provider_budget_stop_blocks_other_provider_even_after_settlement(self):
  with tempfile.TemporaryDirectory() as d:
   root=self.root(d);b=Budget(root);pending=b.reserve('mimo','pending','one',1000,1000,0)
   with self.assertRaisesRegex(ValueError,'Budget stop'):b.reserve('deepseek','too-big','two',100000000,100000000,0)
   b.settle(pending,{'id':'test','usage':{'prompt_tokens':100,'completion_tokens':10}},1)
   with self.assertRaisesRegex(ValueError,'paused'):b.reserve('doubao','small','three',1,1,0)
   self.assertEqual(len(json.loads((root/'budget-ledger.json').read_text())['entries']),1)
 def test_unapproved_higher_cap_is_never_accepted(self):
  with tempfile.TemporaryDirectory() as d:
   root=self.root(d);approval=json.loads((root/'approval.json').read_text());approval['max_total_cny']=51;c.write(root/'approval.json',approval)
   with self.assertRaisesRegex(ValueError,'approval required'):Budget(root).reserve('mimo','bp','one',1,1,0)
 def test_mimo_uses_documented_json_mode_without_disabling_thinking(self):
  with tempfile.TemporaryDirectory() as d:
   root=self.root(d);out=root/'mimo';out.mkdir();response={'id':'test','model':'mimo-v2.6-pro','usage':{'prompt_tokens':100,'completion_tokens':5},'choices':[{'finish_reason':'stop','message':{'content':'{}'}}]}
   with patch.dict(os.environ,{'MIMO_API_KEY':'test-key'}),patch('paid_causal.request',return_value=response) as request:
    make_call('mimo',root)('map3-continuation-r3',{'stage':'continuation','teams':['LOUD','100T']},{'type':'object'},{},out,{})
   body=request.call_args.args[2];self.assertEqual(body['response_format'],{'type':'json_object'});self.assertEqual(body['thinking'],{'type':'enabled'});self.assertEqual(body['model'],'mimo-v2.6-pro')
 def test_completed_provider_is_frozen_before_any_reservation(self):
  with tempfile.TemporaryDirectory() as d:
   root=self.root(d);approval=json.loads((root/'approval.json').read_text());approval['active_models']=['mimo'];c.write(root/'approval.json',approval)
   with self.assertRaisesRegex(ValueError,'frozen'):Budget(root).reserve('deepseek','unexpected','one',1000,1000,0)
   self.assertFalse((root/'budget-ledger.json').exists());Budget(root).reserve('mimo','continue','two',1000,1000,0)
class BPRetryTests(unittest.TestCase):
 def setUp(self):self.pack=json.loads((ROOT/'data/evidence-v2.json').read_text());self.state=c.initial(self.pack,['LOUD','VIT'])
 def test_budget_rejection_before_first_request_propagates(self):
  with tempfile.TemporaryDirectory() as folder,patch('paid_causal.c.call',side_effect=ValueError('Budget stop')) as call:
   with self.assertRaisesRegex(ValueError,'Budget stop'):complete_bp('mimo',Path(folder),Path(folder),self.state,self.pack,True)
   call.assert_called_once()
 def test_old_response_does_not_turn_budget_rejection_into_retry(self):
  with tempfile.TemporaryDirectory() as folder,patch('paid_causal.c.call',side_effect=ValueError('Budget stop')) as call:
   out=Path(folder);d=out/'old';d.mkdir();c.write(d/'response.json',{'model':'mimo-v2.6-pro'});c.write(out/'ledger.json',{'entries':[{'key':'bp-'+c.digest(self.state)[:16],'before_sha256':c.digest(self.state),'directory':'old','status':'response_received'}]})
   with self.assertRaisesRegex(ValueError,'Budget stop'):complete_bp('mimo',out,out,self.state,self.pack,True)
   call.assert_called_once();self.assertFalse((d/'validation.json').exists())
 def test_unfinished_bp_is_never_duplicated(self):
  with tempfile.TemporaryDirectory() as folder,patch('paid_causal.c.call') as call:
   out=Path(folder);c.write(out/'ledger.json',{'entries':[{'key':'bp-'+c.digest(self.state)[:16],'before_sha256':c.digest(self.state),'directory':'pending','status':'reserved'}]})
   with self.assertRaisesRegex(ValueError,'unfinished'):complete_bp('mimo',out,out,self.state,self.pack,True)
   call.assert_not_called()
if __name__=='__main__':unittest.main()
