"""Bounded real Codex worker; parent attests model from native startup header."""
import json
import hashlib
import os
from pathlib import Path
import re
import signal
import subprocess
import time
from replay import validate_policy


def call_worker(name, prompt, out, schema, codex_binary, expected_sha):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    cwd=out/'workspace';cwd.mkdir(exist_ok=True)
    result=out/(name+'-result.json')
    binary=Path(codex_binary).resolve()
    if hashlib.sha256(binary.read_bytes()).hexdigest()!=expected_sha:raise ValueError('Explicit registered CLI binary changed')
    version=subprocess.check_output([str(binary),'--version'],text=True).strip()
    args=[str(binary),'exec','--ephemeral','--color','never','--model','gpt-6.1-sol',
          '-c','model_reasoning_effort="medium"','--sandbox','read-only','--skip-git-repo-check',
          '--cd',str(cwd.resolve()),'--output-schema',str(Path(schema).resolve()),
          '--output-last-message',str(result.resolve()),'-']
    (out/(name+'-prompt.txt')).write_text(prompt)
    start=time.monotonic();process=subprocess.Popen(args,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True)
    timed_out=False
    try:stdout,stderr=process.communicate(prompt,timeout=180)
    except subprocess.TimeoutExpired:
        timed_out=True;os.killpg(process.pid,signal.SIGTERM)
        try:stdout,stderr=process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid,signal.SIGKILL);stdout,stderr=process.communicate()
    (out/(name+'-stdout.txt')).write_text(stdout)
    (out/(name+'-stderr.txt')).write_text(stderr)
    header=stderr[:4000]
    fields={k:re.search(r'^'+re.escape(k)+r':\s*(.+)$',header,re.M).group(1).strip() if re.search(r'^'+re.escape(k)+r':\s*(.+)$',header,re.M) else None for k in ['model','reasoning effort','provider']}
    usage=re.search(r'tokens used\s*\n\s*([\d,]+)',stdout+'\n'+stderr)
    receipt={'worker':name,'cli_version':version,'cli_binary_sha256':expected_sha,'exit_code':process.returncode,'timed_out':timed_out,'wall_seconds':time.monotonic()-start,'runtime_header':fields,
             'reported_tokens_used':int(usage.group(1).replace(',','')) if usage else None,'input_output_cache_breakdown':'unknown','fee':'unknown'}
    (out/(name+'-receipt.json')).write_text(json.dumps(receipt,indent=2)+'\n')
    actual_version=re.search(r'OpenAI Codex v([^\n]+)',header)
    if timed_out or process.returncode!=0 or not actual_version or 'codex-cli '+actual_version.group(1).strip()!=version or fields['model']!='gpt-6.1-sol' or fields['reasoning effort']!='medium':
        raise RuntimeError('Worker unavailable or native runtime attestation mismatch; preserve receipt, no replacement call')
    data=json.loads(result.read_text())
    if len(data['policies'])!=3 or len({p['id'] for p in data['policies']})!=3:raise ValueError('Exactly three unique candidate policies required')
    for policy in data['policies']:validate_policy(policy)
    return data['policies'],receipt
