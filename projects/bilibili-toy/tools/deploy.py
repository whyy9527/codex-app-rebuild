"""Publish a checksummed preview through a private, temporary OSS artifact."""
import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import shlex
import subprocess
import tarfile

from .cloud import ROOT, remote

DOMAIN = 's16.xinxiayiyan.com'


def command(*args):
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError('Command failed: ' + ' '.join(args[:3]))
    return result.stdout


def package():
    revision = command('git', '-C', str(ROOT), 'rev-parse', 'HEAD').strip()
    status = command('git', '-C', str(ROOT), 'status', '--porcelain', '--untracked-files=no', '--', str(ROOT))
    if status.strip():
        raise RuntimeError('Commit the reviewed project inputs before deployment')
    release_time = datetime.now(timezone.utc)
    release = revision[:12] + '-' + release_time.strftime('%Y%m%dT%H%M%SZ')
    folder = ROOT / 'private/deploy' / release
    folder.mkdir(parents=True, exist_ok=False)
    files = {}
    for directory in ('app', 'deploy'):
        for path in (ROOT / directory).rglob('*'):
            if path.is_file():
                files[str(path.relative_to(ROOT))] = path.read_bytes()
    files['tools/serve.py'] = (ROOT / 'tools/serve.py').read_bytes()
    for path in (ROOT / 'private/site').rglob('*'):
        if path.is_file() and not path.is_symlink():
            relative = path.relative_to(ROOT / 'private/site')
            if '.original.' not in path.name and path.name != 'provenance.json' and not path.name.startswith('_x_'):
                files['private/site/' + str(relative)] = path.read_bytes()
    for required in ('private/site/assets/local-index.js', 'private/site/host/responses.json'):
        if required not in files:
            raise RuntimeError('Missing prepared baseline: ' + required)
    prepared_build = json.loads((ROOT / 'private/site/source-build.json').read_text())
    expected_build = json.loads((ROOT / 'source-build.json').read_text())
    if prepared_build != expected_build:
        raise RuntimeError('Prepared source build differs from reviewed configuration')
    manifest = {'release': release, 'revision': revision, 'channel': 'preview',
                'source_build': prepared_build['id'], 'full_fidelity_acceptance': 'pending',
                'resource_origin': 'Original publicly published application reused; third-party rights remain with their owners.'}
    files['release.json'] = (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode()
    hashes = {name: hashlib.sha256(data).hexdigest() for name, data in sorted(files.items())}
    files['checksums.txt'] = ''.join(digest + '  ' + name + '\n' for name, digest in hashes.items()).encode()
    archive = folder / 'site.tar.gz'
    with tarfile.open(archive, 'w:gz') as tar:
        for name, data in sorted(files.items()):
            entry = tarfile.TarInfo(name)
            entry.size = len(data)
            entry.mode = 0o644
            entry.mtime = int(release_time.timestamp())
            tar.addfile(entry, io.BytesIO(data))
    manifest.update(archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(), files=hashes)
    (folder / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    return folder, manifest


def publish(folder, manifest):
    release = manifest['release']
    if not re.fullmatch(r'[a-f0-9]{12}-\d{8}T\d{6}Z', release):
        raise ValueError('Invalid release ID')
    stage = '/var/tmp/bilibili-toy-s16-' + release
    print(remote('set -eu\nfilesystem=$(stat -f -c %T /var/tmp)\ncase "$filesystem" in tmpfs|ramfs) exit 1;; esac\nmkdir -m 700 -p ' + shlex.quote(stage) + '\nfree -m\nuptime\n'), flush=True)
    # One owned temporary object, private ACL, short-lived download URL; never printed.
    key = 'oss://clawaether-ai-personality/bilibili-toy-deploy/' + release + '.tar.gz'
    endpoint = 'https://oss-cn-hongkong.aliyuncs.com'
    command('aliyun', 'oss', 'cp', str(folder / 'site.tar.gz'), key, '--acl', 'private', '--endpoint', endpoint)
    signed = command('aliyun', 'oss', 'sign', key, '--timeout', '1800', '--endpoint', endpoint)
    urls = re.findall(r'https?://\S+', signed)
    if len(urls) != 1:
        raise RuntimeError('Expected a single private artifact download URL')
    download_url = urls[0].replace('http://', 'https://', 1)
    digest = manifest['archive_sha256']
    script = 'set -eu\n' + 'curl --fail --silent --show-error --max-time 300 ' + shlex.quote(download_url) + ' -o ' + shlex.quote(stage + '/site.tar.gz') + '\n'
    script += "printf '%s  %s\\n' " + shlex.quote(digest) + ' ' + shlex.quote(stage + '/site.tar.gz') + ' | sha256sum -c -\n'
    print(remote(script, timeout=360), flush=True)
    records = json.loads(command('aliyun', 'alidns', 'DescribeDomainRecords', '--profile', 'fenhezhishang', '--DomainName', 'xinxiayiyan.com', '--RRKeyWord', 's16'))['DomainRecords']['Record']
    exact = [r for r in records if r['RR'] == 's16']
    if not exact:
        command('aliyun', 'alidns', 'AddDomainRecord', '--profile', 'fenhezhishang', '--DomainName', 'xinxiayiyan.com', '--RR', 's16', '--Type', 'A', '--Value', '47.104.152.169', '--TTL', '600')
    elif len(exact) != 1 or exact[0]['Type'] != 'A' or exact[0]['Value'] != '47.104.152.169' or exact[0]['Status'] != 'ENABLE':
        raise RuntimeError('Existing s16 DNS differs; refusing to overwrite it')
    gateway = remote("docker network inspect nginx-proxy-manage_default --format '{{(index .IPAM.Config 0).Gateway}}'").strip()
    import ipaddress
    ipaddress.ip_address(gateway)
    install = (ROOT / 'deploy/install.sh').read_text()
    # Script passed through stdin keeps the downloaded release immutable until verified.
    script = 'sh -s -- ' + ' '.join(map(shlex.quote, (stage, release, gateway))) + " <<'S16_INSTALL'\n" + install + '\nS16_INSTALL\n'
    print('Recovery directory: ' + stage, flush=True)
    print(remote(script, timeout=360), flush=True)
    (folder / 'activation.json').write_text(json.dumps({'release': release, 'staging': stage, 'artifact_object': key}, indent=2))
    print('Activated; verify public HTTPS and UI before cleanup.', flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--publish', action='store_true', help='Explicitly deploy the packaged preview')
    args = parser.parse_args()
    folder, manifest = package()
    print(json.dumps({'release': manifest['release'], 'archive_bytes': (folder / 'site.tar.gz').stat().st_size, 'archive_sha256': manifest['archive_sha256']}), flush=True)
    if args.publish:
        publish(folder, manifest)


if __name__ == '__main__':
    main()
