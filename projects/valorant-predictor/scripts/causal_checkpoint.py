"""Read-only model state summary; never generates or resumes requests."""
import json,time
from datetime import datetime,timezone
from causal_series import ROOT,write
from collect_causal_usage import collect

def main():
 collect();private=ROOT/'private';root=private/'causal-three-paid-20261016';b=json.loads((root/'budget-ledger.json').read_text());entries=b['entries'];used=sum(e.get('budget_charge_upper_cny',e['reserved_cny']) for e in entries)
 report={'asof_utc':datetime.now(timezone.utc).isoformat(),'asof_unix':time.time(),'paid_budget':{'used_or_reserved_upper_cny':used,'cap_cny':b['cap_cny'],'remaining_upper_cny':b['cap_cny']-used,'active_reserved_cny':sum(e['reserved_cny'] for e in entries if e['status']=='in_flight'),'invoice_available':False},'models':{}}
 for ch in ['codex','deepseek','doubao','mimo']:
  base=private/'gpt-causal-bo5-20261016' if ch=='codex' else root/ch;cases=[];calls=0
  for name,path in [('loser_final',base),('grand_final',base/'grand-final')]:
   if not (path/'state.json').exists():continue
   s=json.loads((path/'state.json').read_text());ledger=json.loads((path/'ledger.json').read_text()) if (path/'ledger.json').exists() else {'calls':0,'entries':[]};calls+=ledger['calls'];last=ledger['entries'][-1] if ledger['entries'] else {}
   cases.append({'match':name,'teams':s['teams'],'state_stage':s['stage'],'completed_maps':s.get('completed_maps',[]),'series_score':s['series_score'],'winner':s['winner'],'current_map':s['maps'][s['map_index']]['map'] if s['maps'] else None,'current_round_score':s['round_score'],'next_round':s['round_number'],'requests':ledger['calls'],'latest_stage':last.get('stage'),'latest_request_status':last.get('status')})
  rows=[e for e in entries if e['channel']==ch];usage={k:{'sum_known':sum(e['usage'][k] for e in rows if e['usage'][k] is not None),'unknown_requests':sum(e['usage'][k] is None for e in rows)} for k in ['input_tokens','output_tokens','cached_input_tokens','reasoning_tokens']} if ch!='codex' else {'per_category_unavailable':True}
  report['models'][ch]={'requests':calls,'cases':cases,'returned_usage':usage,'worker_status':json.loads((base/'worker-status.json').read_text()) if (base/'worker-status.json').exists() else None}
 write(private/'causal-checkpoint-latest.json',report);print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
