import copy,hashlib,importlib.util,json,sys,unittest,tempfile
from unittest.mock import patch
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from evidence_pack import digest,validate_pack
from forecast_contract import CASES,FACTORS,decision_prompt,validate_proposal
class EvidenceTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.pack=json.loads((ROOT/'data/evidence-v2.json').read_text())
 def proposal(self):
  pool=next(f['value']['pool'] for f in self.pack['facts'] if f['id']=='official:rules')
  return {'input_sha256':self.pack['content_sha256'],'limitations':'Synthetic contract fixture, never a model output','cases':{k:{'teams':teams,'factors':[{'id':f,'judgment':'Synthetic fixture','evidence_refs':['official:rules'],'limitations':'Synthetic fixture'} for f in FACTORS],'priority_role':'A','bans':pool[:2],'bp_reason':'Synthetic fixture','bp_evidence_refs':['official:rules'],'maps':[{'map':m,'a_start_side':'ATK','p_first':.5,'reason':'Synthetic fixture','evidence_refs':['official:rules'],'counterevidence_refs':[],'change_condition':'New verified evidence','missing_evidence':['No actual fixture model analysis']} for m in pool[2:]]} for k,teams in CASES.items()}}
 def test_pack_identity_time_and_arithmetic(self):
  self.assertTrue(validate_pack(self.pack));self.assertEqual(sum(f['type']=='completed_series' for f in self.pack['facts']),19);self.assertEqual(sum(f['type']=='map_result' for f in self.pack['facts']),46)
  for f in self.pack['facts']:
   if f['type']=='map_result':
    m=f['value'];self.assertEqual(len(m['players']),10)
    for i,s in enumerate(m['sides']):self.assertEqual(s['attack_wins']+s['defense_wins']+s['overtime_wins'],m['score'][i])
  self.assertTrue(all(r['upcoming_starting_lineup']=='unconfirmed' for r in self.pack['rosters'].values()))
 def test_future_evidence_and_tampering_rejected(self):
  p=copy.deepcopy(self.pack);p['facts'][0]['available_at']='2099-01-01T00:00:00Z';p['content_sha256']=digest({k:v for k,v in p.items() if k!='content_sha256'})
  with self.assertRaises(ValueError):validate_pack(p)
  p=copy.deepcopy(self.pack);p['facts'][0]['value']['score']=[99,0]
  with self.assertRaises(ValueError):validate_pack(p)
 def test_full_proposal_and_refs(self):
  p=self.proposal();self.assertTrue(validate_proposal(p,self.pack))
  for change in ['unknown_ref','nan','duplicate_map','wrong_input','gf_privilege','missing_case']:
   p=self.proposal();m=p['cases']['lf']['maps'][0]
   if change=='unknown_ref':m['evidence_refs']=['invented']
   elif change=='nan':m['p_first']=float('nan')
   elif change=='duplicate_map':m['map']=p['cases']['lf']['maps'][1]['map']
   elif change=='wrong_input':p['input_sha256']='old'
   elif change=='gf_privilege':p['cases']['gf_vit']['priority_role']='B'
   else:p['cases'].pop('gf_100t')
   with self.assertRaises(ValueError,msg=change):validate_proposal(p,self.pack)
 def test_legacy_predictions_are_unchanged_and_not_backfilled(self):
  receipts=json.loads((ROOT/'data/forecast-inputs.json').read_text())
  for r in receipts['models'].values():
   self.assertEqual(hashlib.sha256((ROOT/'data'/r['file']).read_bytes()).hexdigest(),r['sha256']);self.assertFalse(r['used_evidence_v2']);self.assertIsNone(r['historical_knowledge_cutoff']);self.assertNotEqual(r['input_snapshot_collected_at'],r['original_data_cutoff'])
 def test_single_analysis_inputs_have_no_persona_or_selector(self):
  p=decision_prompt(self.pack);self.assertIn(self.pack['content_sha256'],p);self.assertIn('不扮演人格',p);self.assertNotIn('selected_proposal_sha256',p)
 def test_prepare_is_free_and_old_approval_is_rejected(self):
  from run_evidence_models import prepare,approved,budget
  with tempfile.TemporaryDirectory() as temp,patch('run_evidence_models.request',side_effect=AssertionError('No external calls allowed')):
   out=Path(temp);prepare(self.pack,out)
   self.assertFalse((out/'ledger.json').exists());self.assertTrue((out/'analysis-prompt.txt').exists())
   a=out/'old-approval.json';a.write_text(json.dumps({'approved':True,'models':['codex','deepseek','doubao','mimo'],'max_calls_per_model':2,'max_total_cny':5,'authorization':'Earlier tactical batch authorization'}))
   with self.assertRaises(ValueError):approved(a,self.pack['content_sha256'])
   (out/'ledger.json').write_text('{}')
   with self.assertRaises(ValueError):prepare(self.pack,out)
  self.assertEqual(budget()['planned_calls_total'],8);self.assertLessEqual(budget()['api_max_reservation_cny'],10)
 def test_new_normalization_uses_collection_time_not_match_start(self):
  from run_models import normalize
  import itertools
  event=json.loads((ROOT/'data/event.json').read_text());teams=set(t for p in event['predecessors'] for t in p['teams'])
  value={'pairs':[{'team1':a,'team2':b,'p_first':.5,'reason':'Synthetic fixture'} for a,b in itertools.combinations(teams,2)],'limitations':'Synthetic fixture'}
  result=normalize(value,event,'fixture','fixture',{})
  self.assertEqual(result['data_cutoff'],event['fetched_at']);self.assertNotEqual(result['data_cutoff'],result['history_latest_start'])
 def test_only_known_nonsemantic_wrapper_can_be_unwrapped(self):
  from forecast_contract import unwrap_proposal
  p=self.proposal();wrapped={'type':'json_object',**p};value,trace=unwrap_proposal(wrapped)
  self.assertEqual(value,p);self.assertEqual(wrapped['type'],'json_object');self.assertTrue(trace[0]['semantic_fields_unchanged'])
  bad={'type':'change_probabilities',**p};value,trace=unwrap_proposal(bad)
  with self.assertRaises(ValueError):validate_proposal(value,self.pack)
 def test_outer_delimiter_repair_preserves_all_three_authored_cases(self):
  from forecast_contract import parse_completion
  p=self.proposal();raw=json.dumps({k:p[k] for k in ['input_sha256','cases','limitations']},separators=(',',':'));broken=raw.replace('},"gf_vit":','},{"gf_vit":').replace('},"gf_100t":','},{"gf_100t":')
  parsed,trace=parse_completion(broken);self.assertEqual(parsed,p);self.assertTrue(trace[0]['all_three_original_case_objects_identical']);self.assertTrue(trace[0]['probabilities_reasons_and_references_unchanged'])
  position=raw.rfind('},"limitations":');missing=raw[:position]+raw[position+1:];parsed2,trace2=parse_completion(missing);self.assertEqual(parsed2,p);self.assertTrue(trace2[0]['all_three_original_case_objects_identical'])
  with self.assertRaises(ValueError):parse_completion(broken.replace('"p_first":0.5','"p_first":',1))
if __name__=='__main__':unittest.main()
