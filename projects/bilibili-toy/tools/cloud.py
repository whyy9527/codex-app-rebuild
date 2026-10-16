"""Cloud Assistant transport; raw invocation diagnostics stay private."""
import base64
import json
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
AUTH = ['--profile', 'fenhezhishang', '--RegionId', 'cn-qingdao']
INSTANCE = 'i-m5e6lwafecags083ywqd'


def api(operation, args):
    result = subprocess.run(['aliyun', 'ecs', operation, *AUTH, *args], capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError('Aliyun API failed: ' + operation)
    return json.loads(result.stdout)


def remote(script, timeout=120):
    result = api('RunCommand', ['--InstanceId.1', INSTANCE, '--Type', 'RunShellScript',
        '--ContentEncoding', 'Base64', '--CommandContent', base64.b64encode(script.encode()).decode(),
        '--Name', 'bilibili-toy-s16', '--KeepCommand', 'false', '--Timeout', str(timeout)])
    for _ in range(timeout // 2 + 30):
        rows = api('DescribeInvocationResults', ['--InvokeId', result['InvokeId'], '--ContentEncoding', 'PlainText']).get('Invocation', {}).get('InvocationResults', {}).get('InvocationResult', [])
        if rows and rows[0].get('InvocationStatus') in ('Success', 'Failed', 'Timeout', 'Stopped', 'Terminated', 'Invalid', 'Aborted'):
            row = rows[0]
            folder = ROOT / 'private/deploy-invocations'
            folder.mkdir(parents=True, exist_ok=True)
            (folder / (result['InvokeId'] + '.json')).write_text(json.dumps(row, ensure_ascii=False, indent=2))
            if row.get('InvocationStatus') != 'Success' or row.get('ExitCode') != 0:
                raise RuntimeError('Remote command failed; private invocation ' + result['InvokeId'])
            return row.get('Output', '')
        time.sleep(2)
    raise RuntimeError('Cloud Assistant polling timed out')
