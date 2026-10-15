"""Publish only valorant.xinxiayiyan.com using existing Aliyun credentials.

Private, short-lived OSS transport avoids large Cloud Assistant chunks and SSH
key changes. Never prints credentials or signed URLs. Retains recovery releases.
"""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import tarfile
import tempfile
import time
import urllib.request

REPO = Path(__file__).resolve().parents[3]
PROJECT = Path(__file__).resolve().parents[1]
PROFILE = 'fenhezhishang'
REGION = 'cn-qingdao'
INSTANCE = 'i-m5e6lwafecags083ywqd'
DOMAIN = 'valorant.xinxiayiyan.com'
ADDRESS = '47.104.152.169'
PROXY = '/clouddream/nginx-proxy-manage/data/nginx/proxy_host/valorant-predictor.conf'
BUCKET = 'clawaether-ai-personality'
OSS_ENDPOINT = 'oss-cn-hongkong.aliyuncs.com'


def api(service, operation, **args):
    command = ['aliyun', service, operation, '--profile', PROFILE]
    if service == 'ecs':command += ['--RegionId', REGION]
    for key, value in args.items():command += ['--' + key, str(value)]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode:raise RuntimeError('Aliyun operation failed: ' + service + '/' + operation)
    return json.loads(result.stdout)


def remote(script, output, name, timeout=90):
    result = api('ecs', 'RunCommand', **{'InstanceId.1': INSTANCE, 'Type': 'RunShellScript', 'ContentEncoding': 'Base64', 'CommandContent': base64.b64encode(script.encode()).decode(), 'Name': 'valorant-predictor', 'KeepCommand': 'false', 'Timeout': timeout})
    deadline = time.monotonic() + timeout + 60
    while time.monotonic() < deadline:
        rows = api('ecs', 'DescribeInvocationResults', InvokeId=result['InvokeId'], ContentEncoding='PlainText').get('Invocation', {}).get('InvocationResults', {}).get('InvocationResult', [])
        if rows and rows[0].get('InvocationStatus') in ['Success', 'Failed', 'Timeout', 'Stopped', 'Terminated', 'Invalid', 'Aborted']:
            row = rows[0]
            (output / (name + '.json')).write_text(json.dumps(row, ensure_ascii=False, indent=2) + '\n')
            if row.get('InvocationStatus') != 'Success' or row.get('ExitCode') != 0:
                raise RuntimeError('Remote step ' + name + ' failed; inspect ' + result['InvokeId'])
            return row.get('Output', '')
        time.sleep(2)
    raise TimeoutError('Cloud Assistant step ' + name)


def ensure_dns(output):
    records = api('alidns', 'DescribeDomainRecords', DomainName='xinxiayiyan.com', PageSize=500).get('DomainRecords', {}).get('Record', [])
    own = [r for r in records if r['RR'] == 'valorant']
    if own:
        if len(own) != 1 or own[0]['Type'] != 'A' or own[0]['Value'] != ADDRESS or own[0]['Status'] != 'ENABLE':
            raise RuntimeError('Existing valorant DNS differs; refusing to overwrite another destination')
        receipt = {'existing_record': own[0]['RecordId']}
    else:
        receipt = api('alidns', 'AddDomainRecord', DomainName='xinxiayiyan.com', RR='valorant', Type='A', Value=ADDRESS, TTL=600)
    (output / 'dns.json').write_text(json.dumps(receipt, indent=2) + '\n')


def main(out):
    output = REPO / out
    output.mkdir(parents=True, exist_ok=False)
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True).strip()
    dirty = subprocess.check_output(['git', 'status', '--porcelain', '--', str(PROJECT.relative_to(REPO))], cwd=REPO, text=True).strip()
    if dirty:raise RuntimeError('Commit and verify project deployment inputs before publishing')
    remote_tip = subprocess.check_output(['git', 'ls-remote', 'origin', 'refs/heads/main'], cwd=REPO, text=True).split()[0]
    if remote_tip != revision:raise RuntimeError('Publish only the verified, pushed main commit')
    subprocess.run(['python3', str(PROJECT / 'scripts/build.py')], check=True, cwd=REPO)
    stage = '/var/tmp/valorant-predictor-' + revision[:12]
    print(remote(f'''set -eu
filesystem=$(stat -f -c %T /var/tmp)
case "$filesystem" in tmpfs|ramfs) echo 'Refusing memory-backed staging'; exit 1;; esac
df -h /var/tmp
uptime
docker image inspect goharbor/nginx-photon:v2.10.0 --format '{{{{.Id}}}}'
docker inspect media-workflow-app-1 --format '{{{{.State.Health.Status}}}}'
curl -fsS -o /dev/null https://workflow.xinxiayiyan.com/api/health
curl -fsS -o /dev/null https://landing.xinxiayiyan.com/
mkdir -p {shlex.quote(stage)}
find /clouddream/nginx-proxy-manage/data/nginx/proxy_host -maxdepth 1 -type f -name '*.conf' ! -name 'valorant-predictor.conf' -exec sha256sum {{}} + > {shlex.quote(stage)}/protected-proxies.sha256
''', output, 'preflight'), flush=True)
    (PROJECT / 'dist/revision.json').write_text(json.dumps({'git_revision': revision, 'domain': DOMAIN}) + '\n')
    checksums = {str(p.relative_to(PROJECT / 'dist')): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((PROJECT / 'dist').rglob('*')) if p.is_file()}
    manifest = ''.join(f'{digest}  {name}\n' for name, digest in checksums.items())
    (output / 'SHA256SUMS').write_text(manifest)
    artifact = output / 'site.tar.gz'
    with tarfile.open(artifact, 'w:gz') as archive:
        archive.add(PROJECT / 'dist', arcname='dist')
        archive.add(PROJECT / 'deploy', arcname='deploy')
        archive.add(output / 'SHA256SUMS', arcname='SHA256SUMS')
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    object_uri = f'oss://{BUCKET}/deployments/valorant/{revision}-{digest[:12]}.tar.gz'
    profiles = json.loads((Path.home() / '.aliyun/config.json').read_text())['profiles']
    profile = next(p for p in profiles if p['name'] == PROFILE)
    with tempfile.TemporaryDirectory(prefix='private-oss-', dir=output) as private:
        config = Path(private) / 'oss.config'
        config.write_text('[Credentials]\nlanguage=EN\nendpoint=' + OSS_ENDPOINT + '\naccessKeyID=' + profile['access_key_id'] + '\naccessKeySecret=' + profile['access_key_secret'] + '\n')
        config.chmod(0o600)
        def oss(*args):
            result = subprocess.run(['aliyun', 'oss', *args, '-c', str(config)], capture_output=True, text=True)
            if result.returncode:raise RuntimeError('Private artifact transport failed (details suppressed to protect signed URLs)')
            return result.stdout
        oss('cp', str(artifact), object_uri, '--acl', 'private')
        signed = next(line.strip() for line in oss('sign', object_uri, '--timeout', '1800').splitlines() if line.startswith('http'))
        print('Uploaded private artifact:', artifact.stat().st_size, 'bytes; SHA256', digest, flush=True)
        print(remote(f'''set -eu
STAGING={shlex.quote(stage)}
curl --connect-timeout 15 --max-time 180 -fsS {shlex.quote(signed)} -o "$STAGING/site.tar.gz"
printf '%s  %s/site.tar.gz\n' {shlex.quote(digest)} "$STAGING" | sha256sum -c -
mkdir -p "$STAGING/unpacked"
tar -xzf "$STAGING/site.tar.gz" -C "$STAGING/unpacked"
(cd "$STAGING/unpacked/dist" && sha256sum -c ../SHA256SUMS) > "$STAGING/verify-staged.log"
mkdir -p /opt/valorant-predictor/releases
cd /opt/valorant-predictor
if [ -e current ]; then readlink -f current > "$STAGING/previous-release"; fi
if [ -e {revision} ]; then echo 'Unexpected path collision'; exit 1; fi
if [ -d releases/{revision} ]; then
    (cd releases/{revision} && sha256sum -c "$STAGING/unpacked/SHA256SUMS") > "$STAGING/verify-existing.log"
else cp -a "$STAGING/unpacked/dist" releases/{revision}; fi
cp "$STAGING/unpacked/deploy/compose.yaml" compose.yaml
if [ -f static.nginx.conf ]; then cp -a static.nginx.conf "$STAGING/previous-static.conf"; fi
cp "$STAGING/unpacked/deploy/static.nginx.conf" static.nginx.conf
ln -s releases/{revision} current.next
mv -Tf current.next current
docker compose -f compose.yaml config --quiet
docker compose -f compose.yaml up -d --force-recreate web
for attempt in $(seq 1 20); do
    if docker exec valorant-predictor curl -fsS -o /dev/null http://127.0.0.1:8080/; then break; fi
    sleep 1
done
docker exec valorant-predictor curl -fsS http://127.0.0.1:8080/revision.json
docker exec valorant-predictor curl -fsSI http://127.0.0.1:8080/engine.mjs | grep -i 'Content-Type: application/javascript'
docker exec nginx-app curl -fsS -o /dev/null http://valorant-predictor:8080/
if ! docker exec nginx-app test -f /etc/letsencrypt/live/valorant-predictor/fullchain.pem; then
    if [ -f {PROXY} ]; then cp -a {PROXY} "$STAGING/previous-proxy.conf"; fi
    cp "$STAGING/unpacked/deploy/http.nginx.conf" {PROXY}
    docker exec nginx-app nginx -t
    docker exec nginx-app nginx -s reload
fi
''', output, 'activate-origin', timeout=240), flush=True)
        ensure_dns(output)
        for attempt in range(12):
            try:
                with urllib.request.urlopen('http://' + DOMAIN + '/revision.json', timeout=10) as response:
                    if json.load(response)['git_revision'] == revision:break
            except Exception:
                if attempt == 11:raise RuntimeError('Public DNS/HTTP readiness not established; origin and recovery retained')
                time.sleep(5)
        print(remote(f'''set -eu
STAGING={shlex.quote(stage)}
docker exec nginx-app certbot certonly --config /etc/letsencrypt.ini --non-interactive --agree-tos --authenticator webroot --preferred-challenges http --webroot-path /data/letsencrypt-acme-challenge --cert-name valorant-predictor -d {DOMAIN}
cp -a {PROXY} "$STAGING/before-https-proxy.conf"
cp "$STAGING/unpacked/deploy/https.nginx.conf" {PROXY}
if ! docker exec nginx-app nginx -t; then
    cp "$STAGING/before-https-proxy.conf" {PROXY}
    exit 1
fi
docker exec nginx-app nginx -s reload
cp "$STAGING/unpacked/deploy/renew-certificate.sh" /opt/valorant-predictor/
chmod 750 /opt/valorant-predictor/renew-certificate.sh
cp "$STAGING/unpacked/deploy/valorant-renew.service" /etc/systemd/system/
cp "$STAGING/unpacked/deploy/valorant-renew.timer" /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now valorant-renew.timer
(cd /opt/valorant-predictor/current && sha256sum -c "$STAGING/unpacked/SHA256SUMS") > "$STAGING/verify-live.log"
curl -fsS https://{DOMAIN}/revision.json
curl -fsS -o /dev/null https://landing.xinxiayiyan.com/
curl -fsS -o /dev/null https://workflow.xinxiayiyan.com/api/health
docker inspect media-workflow-app-1 --format '{{{{.State.Health.Status}}}}'
sha256sum -c "$STAGING/protected-proxies.sha256" > "$STAGING/verify-protected-proxies.log"
''', output, 'https-and-shared-health', timeout=150), flush=True)
        public = {}
        for name in ['revision.json', 'index.html', 'app.js', 'engine.mjs', 'style.css']:
            with urllib.request.urlopen('https://' + DOMAIN + '/' + name, timeout=30) as response:
                actual = hashlib.sha256(response.read()).hexdigest()
                if actual != checksums[name]:raise RuntimeError('Public artifact differs: ' + name)
                public[name] = {'sha256': actual, 'status': response.status}
        (output / 'publication.json').write_text(json.dumps({'domain': DOMAIN, 'git_revision': revision, 'artifact_sha256': digest, 'recovery_directory': stage, 'public': public}, indent=2) + '\n')
        oss('rm', object_uri)
        remote(f'rm -f -- {shlex.quote(stage)}/site.tar.gz\nrm -rf -- {shlex.quote(stage)}/unpacked\n', output, 'cleanup-owned-upload')
    print('Published https://' + DOMAIN + '/ at ' + revision, flush=True)


if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',required=True);args=parser.parse_args();main(args.out)
