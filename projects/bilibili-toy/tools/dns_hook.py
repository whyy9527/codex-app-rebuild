"""Certbot DNS-01 hooks, limited to the S16 challenge and owned TXT records."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
RR = '_acme-challenge.s16'


def api(operation, *args):
    result = subprocess.run(['aliyun', 'alidns', operation, '--profile', 'fenhezhishang', *args], capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError('DNS API failed: ' + operation)
    return json.loads(result.stdout)


def main(action):
    if os.environ.get('CERTBOT_DOMAIN') != 's16.xinxiayiyan.com':
        raise ValueError('Hook is limited to the S16 subdomain')
    value = os.environ['CERTBOT_VALIDATION']
    if not re.fullmatch(r'[A-Za-z0-9_-]{30,100}', value):
        raise ValueError('Invalid challenge value')
    folder = ROOT / 'private/certbot'
    folder.mkdir(parents=True, exist_ok=True)
    state = folder / ('challenge-' + hashlib.sha256(value.encode()).hexdigest() + '.json')
    if action == 'auth':
        result = api('AddDomainRecord', '--DomainName', 'xinxiayiyan.com', '--RR', RR, '--Type', 'TXT', '--Value', value, '--TTL', '600')
        state.write_text(json.dumps({'id': result['RecordId'], 'value': value}))
        for _ in range(30):
            matched = 0
            for nameserver in ('dns13.hichina.com', 'dns14.hichina.com'):
                response = subprocess.run(['dig', '+short', '+time=2', '+tries=1', 'TXT', RR + '.xinxiayiyan.com', '@' + nameserver], capture_output=True, text=True)
                matched += ('"' + value + '"') in response.stdout.splitlines()
            if matched == 2:
                return
            time.sleep(2)
        raise RuntimeError('Owned TXT challenge is not visible at both authoritative DNS servers')
    elif action == 'cleanup':
        if not state.exists():
            return
        owned = json.loads(state.read_text())
        record = api('DescribeDomainRecordInfo', '--RecordId', owned['id'])
        if record['RR'] != RR or record['Type'] != 'TXT' or record['Value'] != value or record['DomainName'] != 'xinxiayiyan.com':
            raise RuntimeError('Refusing to remove a DNS record that differs from this challenge')
        api('DeleteDomainRecord', '--RecordId', owned['id'])
        state.unlink()
    else:
        raise ValueError('Expected auth or cleanup')


if __name__ == '__main__':
    main(sys.argv[1])
