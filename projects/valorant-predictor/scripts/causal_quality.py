"""Join reviewed quality notes to the exact immutable model-decision chain."""
import json
from causal_series import ROOT,digest

def quality_flags(channel,records):
 path=ROOT/'data/causal/quality-notes.json'
 if not path.exists():return []
 chain=digest([r['raw_output_sha256'] for r in records])
 return [n for n in json.loads(path.read_text())['notes'] if n['channel']==channel and n['record_chain_sha256']==chain]
