"""Finish the already staged Qingdao release with DNS-validated HTTPS.

Only the owned subdomain and certificate change. Aliyun credentials stay local;
Cloud Assistant transports a public DNS challenge, never certificate keys.
"""
import argparse
import json
from pathlib import Path
import shlex
import time

from deploy import api, remote, REPO, DOMAIN, ADDRESS, PROXY


def main(out, stage):
    if not stage.startswith('/var/tmp/valorant-predictor-') or '/' in stage[len('/var/tmp/'):]:raise ValueError('Invalid owned staging path')
    output = REPO / out;output.mkdir(parents=True, exist_ok=False)
    records = api('alidns', 'DescribeDomainRecords', DomainName='xinxiayiyan.com', PageSize=500)['DomainRecords']['Record']
    own = [r for r in records if r['RR'] == 'valorant']
    if len(own) != 1 or (own[0]['Type'], own[0]['Value']) not in [('A', ADDRESS), ('CNAME', 'whyy9527.github.io')]:raise RuntimeError('Unrelated subdomain destination')
    dns = api('alidns', 'UpdateDomainRecord', RecordId=own[0]['RecordId'], RR='valorant', Type='A', Value=ADDRESS, TTL=600)
    (output / 'dns.json').write_text(json.dumps(dns, indent=2))
    hook = '''#!/bin/sh
set -eu
umask 077
printf '%s' "$CERTBOT_VALIDATION" > /data/valorant-acme/challenge
for attempt in $(seq 1 180); do
  if test -f /data/valorant-acme/ready; then exit 0; fi
  sleep 1
done
exit 1
'''
    issue = f'''#!/bin/sh
umask 077
certbot certonly --config /etc/letsencrypt.ini --non-interactive --agree-tos --manual --preferred-challenges dns --manual-public-ip-logging-ok --manual-auth-hook /data/valorant-acme/auth.sh --manual-cleanup-hook /bin/true --cert-name valorant-predictor -d {DOMAIN} > /data/valorant-acme/issue.log 2>&1
code=$?
printf '%s' "$code" > /data/valorant-acme/done
exit "$code"
'''
    print(remote(f'''set -eu
docker exec nginx-app mkdir -p /data/valorant-acme
docker exec nginx-app sh -c 'rm -f /data/valorant-acme/challenge /data/valorant-acme/ready /data/valorant-acme/done'
docker exec nginx-app sh -c {shlex.quote('printf %s ' + shlex.quote(hook) + ' > /data/valorant-acme/auth.sh')}
docker exec nginx-app sh -c {shlex.quote('printf %s ' + shlex.quote(issue) + ' > /data/valorant-acme/issue.sh')}
docker exec nginx-app chmod 700 /data/valorant-acme/auth.sh /data/valorant-acme/issue.sh
docker exec -d nginx-app sh /data/valorant-acme/issue.sh
''', output, 'start-dns-certificate'), flush=True)
    token = None
    for attempt in range(15):
        token = remote('docker exec nginx-app sh -c "cat /data/valorant-acme/challenge 2>/dev/null || true"', output, 'challenge-' + str(attempt)).strip()
        if token:break
        time.sleep(2)
    if not token:raise RuntimeError('Certificate challenge unavailable; inspect owned issue log')
    record = api('alidns', 'AddDomainRecord', DomainName='xinxiayiyan.com', RR='_acme-challenge.valorant', Type='TXT', Value=token, TTL=600)
    (output / 'challenge-record.json').write_text(json.dumps({'RecordId': record['RecordId']}))
    try:
        # Verify independently from the issuing server before releasing the hook.
        import subprocess
        for attempt in range(20):
            actual = subprocess.run(['dig', '+short', 'TXT', '_acme-challenge.' + DOMAIN, '@1.1.1.1'], capture_output=True, text=True, check=True).stdout
            if token in actual:break
            time.sleep(2)
        else:raise RuntimeError('Public DNS challenge not visible')
        remote('docker exec nginx-app touch /data/valorant-acme/ready', output, 'release-dns-hook')
        print(remote('''set -eu
for attempt in $(seq 1 90); do
  if docker exec nginx-app test -f /data/valorant-acme/done; then
    code=$(docker exec nginx-app cat /data/valorant-acme/done)
    docker exec nginx-app cat /data/valorant-acme/issue.log
    test "$code" = 0
    exit
  fi
  sleep 1
done
exit 1
''', output, 'certificate-result', timeout=100), flush=True)
    finally:
        api('alidns', 'DeleteDomainRecord', RecordId=record['RecordId'])
    print(remote(f'''set -eu
STAGING={shlex.quote(stage)}
cp -a {PROXY} "$STAGING/before-dns-https-proxy.conf"
cp "$STAGING/unpacked/deploy/https.nginx.conf" {PROXY}
if ! docker exec nginx-app nginx -t; then cp "$STAGING/before-dns-https-proxy.conf" {PROXY}; exit 1; fi
docker exec nginx-app nginx -s reload
(cd /opt/valorant-predictor/current && sha256sum -c "$STAGING/unpacked/SHA256SUMS") > "$STAGING/verify-live.log"
docker exec nginx-app openssl x509 -in /etc/letsencrypt/live/valorant-predictor/fullchain.pem -noout -dates -subject
curl -fsS --resolve {DOMAIN}:443:127.0.0.1 https://{DOMAIN}/revision.json
curl -fsS -o /dev/null https://landing.xinxiayiyan.com/
curl -fsS https://workflow.xinxiayiyan.com/api/health
sha256sum -c "$STAGING/protected-proxies.sha256"
''', output, 'activate-https-and-health'), flush=True)
    print('Domestic origin HTTPS ready. Independent public browser verification remains required.', flush=True)


if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out', required=True);parser.add_argument('--stage', required=True);args=parser.parse_args();main(args.out,args.stage)
