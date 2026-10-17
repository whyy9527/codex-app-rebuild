import json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from repair_causal_transport import normalize
class TransportTests(unittest.TestCase):
 def test_extra_closing_brace_preserves_root_values(self):
  expected={'events':[{'kind':'kill','actor':'L1','target':'R1'}]};value,changes=normalize(json.dumps(expected)+'}')
  self.assertEqual(value,expected);self.assertEqual(changes[0]['action'],'remove_extra_trailing_closing_brace')
 def test_known_key_omission_preserves_emitted_discriminator(self):
  value,changes=normalize('{"event":{"at_s":5,"move","actor":"L1","route":["A","B"]}}')
  self.assertEqual(value['event'],{'at_s':5,'kind':'move','actor':'L1','route':['A','B']});self.assertTrue(changes)
 def test_ambiguous_or_conflicting_values_are_not_repaired(self):
  for raw in ['{"actor":"L1","actor":"R1"}','{"at_s":NaN}','{"kind":}', '{"event":{"unknown","actor":"L1"}}']:
   with self.assertRaises((ValueError,json.JSONDecodeError)):normalize(raw)
if __name__=='__main__':unittest.main()
