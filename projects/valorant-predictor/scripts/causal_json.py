"""Strict JSON decoding shared by worker transport and audit validation."""
import json
def unique_object(pairs):
 result={}
 for key,value in pairs:
  if key in result:raise ValueError('Duplicate JSON key rejected: '+key)
  result[key]=value
 return result
def reject_constant(value):raise ValueError('Non-finite JSON number rejected: '+value)
def decode_json(value):return json.loads(value,object_pairs_hook=unique_object,parse_constant=reject_constant)
