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


def oss_credentials(profile):
    value = '[Credentials]\nlanguage=EN\nendpoint=' + OSS_ENDPOINT + '\naccessKeyID=' + profile['access_key_id'] + '\naccessKeySecret=' + profile['access_key_secret'] + '\n'
    if profile.get('sts_token'):
        value += 'stsToken=' + profile['sts_token'] + '\n'
    return value


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


def verify_public(checksums, browser_args=None):
    # Existing domestic sites work in Chromium while this Mac's urllib/curl
    # TLS connections reset. Verify through a real browser with normal TLS.
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path='/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge', headless=True, args=browser_args or [])
        try:
            page = browser.new_page();page.set_default_timeout(60000)
            # Edge's JSON document viewer rejects page-scope fetch even when
            # the same normal-TLS request succeeds from the application page.
            page.goto('https://' + DOMAIN + '/', wait_until='domcontentloaded')
            names = ['revision.json', 'index.html', 'app.js', 'engine.mjs', 'style.css', 'data/event.json']
            for name in ['fiction.mjs', 'tactical-replay.mjs', 'tactical.css', 'veto.mjs', 'veto.css', 'forecast-v2.mjs', 'forecast-v2.css', 'prediction-player.mjs', 'prediction-player.css', 'causal-player.mjs', 'current-data.mjs']:
                if name in checksums:names.append(name)
            names += [name for name in checksums if name.startswith('data/') and name.endswith('.json') and name not in names]
            names += [name for name in checksums if name.startswith(('assets/models/', 'assets/tactical/', 'assets/causal/'))]
            public = page.evaluate('''async names => Object.fromEntries(await Promise.all(names.map(async name => {
                const response = await fetch('/' + name, {cache:'no-store'});
                const body = await response.arrayBuffer();
                const sha256 = [...new Uint8Array(await crypto.subtle.digest('SHA-256', body))].map(n=>n.toString(16).padStart(2,'0')).join('');
                return [name, {status:response.status, sha256}];
            })))''', names)
            for name, row in public.items():
                if row['status'] != 200 or row['sha256'] != checksums[name]:raise RuntimeError('Public artifact differs: ' + name)
            shared = {}
            for host in ['https://landing.xinxiayiyan.com/', 'https://workflow.xinxiayiyan.com/api/health']:
                response = page.goto(host, wait_until='domcontentloaded')
                if response.status != 200:raise RuntimeError('Public shared service unhealthy')
                shared[host] = {'status': response.status}
            return {'files': public, 'shared': shared, 'browser_args': browser_args or []}
        finally:browser.close()


def main(out, profile=None):
    global PROFILE
    if profile is not None:PROFILE = profile
    output = REPO / out
    output.mkdir(parents=True, exist_ok=False)
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True).strip()
    dirty = subprocess.check_output(['git', 'status', '--porcelain', '--', str(PROJECT.relative_to(REPO))], cwd=REPO, text=True).strip()
    if dirty:raise RuntimeError('Commit and verify project deployment inputs before publishing')
    remote_tip = subprocess.check_output(['git', 'ls-remote', 'origin', 'refs/heads/main'], cwd=REPO, text=True).split()[0]
    if remote_tip != revision:raise RuntimeError('Publish only the verified, pushed main commit')
    causal_index = PROJECT / 'data/causal/models.json'
    if causal_index.exists():
        causal = json.loads(causal_index.read_text())
        if set(causal['models']) != {'codex','deepseek','doubao','mimo'} or any(v['status']!='ready' for v in causal['models'].values()):
            raise RuntimeError('Four-model final-two-match causal forecasts are incomplete; refusing publication')
        for row in causal['models'].values():
            bundle=json.loads((PROJECT/row['file']).read_text());cases=bundle.get('cases',[])
            if len(cases)!=2 or any(v['state']['stage']!='finished' for v in cases) or cases[1]['teams']!=['LOUD',cases[0]['state']['winner']]:
                raise RuntimeError('Publication requires both causal series and the model-derived finalist')
    instances = api('ecs', 'DescribeInstances', InstanceIds=json.dumps([INSTANCE])).get('Instances', {}).get('Instance', [])
    if len(instances) != 1 or instances[0].get('InstanceId') != INSTANCE or ADDRESS not in instances[0].get('PublicIpAddress', {}).get('IpAddress', []):
        raise RuntimeError('Selected credential profile does not resolve the exact authorized instance and public address')
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
        config.write_text(oss_credentials(profile))
        config.chmod(0o600)
        def oss(*args):
            result = subprocess.run(['aliyun', 'oss', *args, '-c', str(config), '-e', 'https://' + OSS_ENDPOINT], capture_output=True, text=True)
            if result.returncode:raise RuntimeError('Private artifact transport failed (details suppressed to protect signed URLs)')
            return result.stdout
        oss('cp', str(artifact), object_uri, '--acl', 'private')
        signed = next(line.strip() for line in oss('sign', object_uri, '--timeout', '1800').splitlines() if line.startswith('http'))
        print('Uploaded private artifact:', artifact.stat().st_size, 'bytes; SHA256', digest, flush=True)
        print(remote(f'''set -eu
STAGING={shlex.quote(stage)}
curl --connect-timeout 15 --max-time 420 -C - -fsS {shlex.quote(signed)} -o "$STAGING/site.tar.gz"
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
''', output, 'activate-origin', timeout=480), flush=True)
        ensure_dns(output)
        print(remote(f'''set -eu
STAGING={shlex.quote(stage)}
if ! docker exec nginx-app openssl x509 -checkend 2592000 -noout -in /etc/letsencrypt/live/valorant-predictor/fullchain.pem; then
    echo 'DNS certificate issuance/renewal required; run resume_domestic.py for this owned stage'
    exit 1
fi
cp -a {PROXY} "$STAGING/before-https-proxy.conf"
cp "$STAGING/unpacked/deploy/https.nginx.conf" {PROXY}
if ! docker exec nginx-app nginx -t; then
    cp "$STAGING/before-https-proxy.conf" {PROXY}
    exit 1
fi
docker exec nginx-app nginx -s reload
(cd /opt/valorant-predictor/current && sha256sum -c "$STAGING/unpacked/SHA256SUMS") > "$STAGING/verify-live.log"
curl -fsS https://{DOMAIN}/revision.json
curl -fsS -o /dev/null https://landing.xinxiayiyan.com/
curl -fsS -o /dev/null https://workflow.xinxiayiyan.com/api/health
docker inspect media-workflow-app-1 --format '{{{{.State.Health.Status}}}}'
sha256sum -c "$STAGING/protected-proxies.sha256" > "$STAGING/verify-protected-proxies.log"
''', output, 'https-and-shared-health', timeout=150), flush=True)
        public = verify_public(checksums)
        (output / 'publication.json').write_text(json.dumps({'domain': DOMAIN, 'git_revision': revision, 'artifact_sha256': digest, 'recovery_directory': stage, 'credential_profile': PROFILE, 'public': public}, indent=2) + '\n')
        oss('rm', object_uri)
        remote(f'rm -f -- {shlex.quote(stage)}/site.tar.gz\nrm -rf -- {shlex.quote(stage)}/unpacked\n', output, 'cleanup-owned-upload')
    print('Published https://' + DOMAIN + '/ at ' + revision, flush=True)


if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',required=True);parser.add_argument('--profile',help='Existing local Aliyun profile; target instance and address are verified before deployment');args=parser.parse_args();main(args.out,args.profile)
