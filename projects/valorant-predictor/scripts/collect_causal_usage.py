"""Report only returned usage; local reference tokenization is never provider usage."""
import hashlib,json,re,time
from pathlib import Path
from causal_series import ROOT,write

def collect():
 roots=[ROOT/'private/gpt-causal-bo5-20261016',ROOT/'private/gpt-causal-bo5-20261016/grand-final'];rows=[]
 for root in roots:
  if not (root/'ledger.json').exists():continue
  ledger=json.loads((root/'ledger.json').read_text())
  for i,e in enumerate(ledger['entries'],1):
   d=root/e['directory'];log=d/'stderr.log';text=log.read_text() if log.exists() else '';m=re.search(r'(?m)^tokens used\s*\n([\d,]+)',text);result=d/'result.json'
   value={'match':'grand_final' if root.name=='grand-final' else 'loser_final','request':i,'provider':'openai_chatgpt_cli','model':'gpt-6.1-sol','stage':e['stage'],'status':e['status'],'input_tokens':None,'output_tokens':None,'cached_input_tokens':None,'reasoning_tokens':None,'cli_tokens_used_label':int(m[1].replace(',','')) if m else None,'cli_label_semantics':'CLI aggregate label; per-category provider usage unavailable','started_at_unix':e['started_at'],'elapsed_seconds':round(result.stat().st_mtime-e['started_at'],3) if result.exists() else None,'duration_basis':'result file timestamp minus local request start' if result.exists() else 'not available','timeout_limit_seconds':900 if e['status']=='timeout' else None,'retry':bool('repair' in e['stage'] or 'retry' in e['stage']),'api_cny':0,'actual_invoice_cny':None,'log_sha256':hashlib.sha256(log.read_bytes()).hexdigest() if log.exists() else None}
   if e['status']!='reserved':write(d/'usage-returned.json',value)
   rows.append(value)
 report={'generated_at':time.time(),'gpt':rows,'gpt_api_cny':0,'paid_invoice_available':False};paid=ROOT/'private/causal-three-paid-20261016/budget-ledger.json'
 if paid.exists():report['paid_budget']=json.loads(paid.read_text())
 write(ROOT/'private/causal-token-usage-report.json',report);print('Usage report: GPT attempts',len(rows),'; paid attempts',len(report.get('paid_budget',{}).get('entries',[])))
if __name__=='__main__':collect()
