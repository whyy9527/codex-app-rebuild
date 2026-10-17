"""Only deterministic transport fixes; never add or alter a simulated event value."""
import json,re
from causal_json import decode_json,unique_object,reject_constant

def normalize(raw):
 value=raw;changes=[]
 for _ in range(8):
  try:return decode_json(value),changes
  except json.JSONDecodeError as error:
   if error.msg=='Extra data':
    decoded,end=json.JSONDecoder(object_pairs_hook=unique_object,parse_constant=reject_constant).raw_decode(value)
    if re.fullmatch(r'\s*}+\s*',value[end:]):changes.append({'action':'remove_extra_trailing_closing_brace','offset':end,'all_decoded_root_values_unchanged':True});return decoded,changes
   # A literal event discriminator was emitted without its fixed schema key.
   # Preserve the exact move/kill/plant/defuse value, actor, route and all other bytes.
   if error.msg=="Expecting ':' delimiter":
    match=re.search(r'"(move|kill|plant|defuse)"\s*$',value[:error.pos])
    if match and re.match(r'\s*,\s*"actor"\s*:',value[error.pos:]):
     value=value[:match.start()]+'"kind":'+value[match.start():];changes.append({'action':'restore_fixed_kind_key_before_existing_discriminator','offset':match.start(),'emitted_value_unchanged':match[1]});continue
   raise
 raise ValueError('Too many structural defects; no semantic repair allowed')
