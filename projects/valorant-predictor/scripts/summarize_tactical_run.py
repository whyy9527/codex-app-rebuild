"""Summarize retained provider usage without treating a token estimate as a bill."""
import argparse,json,re
from pathlib import Path
from run_tactical_models import RATES

def summarize(out):
 ledger=json.loads((out/'ledger.json').read_text());rows=[]
 for entry in ledger['entries']:
  channel=entry['channel'];directory=out/channel/f'attempt-{entry["attempt"]}';row={**entry,'generation_status':'no_response_receipt','provider_usage':None,'estimated_cny_at_uncached_rates':None}
  response=directory/'response.json';failure=directory/'failure.json';validation=directory/'validation.json'
  if response.exists():
   value=json.loads(response.read_text());usage=value.get('usage');row.update(response_id=value.get('id'),runtime_model=value.get('model'),provider_usage=usage,generation_status='response_received')
   rate=RATES[channel]
   if usage and type(usage.get('prompt_tokens')) is int and type(usage.get('completion_tokens')) is int:
    native=(usage['prompt_tokens']*rate['input_per_million']+usage['completion_tokens']*rate['output_per_million'])/1e6
    row.update(estimated_native_cost_at_uncached_rates=round(native,8),native_currency=rate['currency'],estimated_cny_at_uncached_rates=round(native*rate['budget_cny_per_unit'],8),within_reserved_token_bounds=usage['prompt_tokens']<=entry['input_token_upper_bound'] and usage['completion_tokens']<=entry['output_token_cap'])
  if channel=='codex':
   log=directory/'stderr.log';tokens=re.findall(r'tokens used\s*\n([\d,]+)',log.read_text()) if log.exists() else []
   row.update(payment='Existing ChatGPT quota; no OpenAI API charge',generation_status='cli_returned' if log.exists() else 'no_cli_receipt',cli_reported_total_tokens=int(tokens[-1].replace(',','')) if tokens else None,input_bound_scope='Prompt/schema payload only; CLI adds its own system context. This is not a bound on total ChatGPT quota tokens.')
  if validation.exists():row['validation']=json.loads(validation.read_text())
  if failure.exists():row['failure']=json.loads(failure.read_text())
  rows.append(row)
 return {'authorized_api_cap_cny':5,'max_calls_per_model':2,'ledger_reserved_cny':ledger['reserved_cny'],'estimated_cny_from_reported_tokens_at_uncached_rates':round(sum(r['estimated_cny_at_uncached_rates'] or 0 for r in rows),8),'provider_invoice_available':False,'pricing_note':'Usage is copied from actual provider responses. Cost is an estimate at uncached rates, not an invoice; USD uses budget reserve coefficient 8, not quoted FX. Missing usage is unknown, never claimed free. All attempted calls remain reserved in ledger.','calls':ledger['calls'],'attempts':rows}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('out',type=Path);a=p.parse_args();value=summarize(a.out);(a.out/'fee-receipt.json').write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:value[k] for k in ['calls','ledger_reserved_cny','estimated_cny_from_reported_tokens_at_uncached_rates']},ensure_ascii=False))
