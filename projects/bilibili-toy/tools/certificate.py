"""Issue DNS-01 locally and install only the S16 certificate on the owned ECS."""
import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tarfile

from .cloud import ROOT, remote
from .deploy import command


def main(install=False):
    folder = ROOT / 'private/certbot'
    folder.mkdir(parents=True, exist_ok=True)
    folder.chmod(0o700)
    hook = shlex.quote(sys.executable) + ' ' + shlex.quote(str(ROOT / 'tools/dns_hook.py'))
    args = ['uvx', 'certbot', 'certonly', '--manual', '--preferred-challenges', 'dns',
        '--manual-auth-hook', hook + ' auth', '--manual-cleanup-hook', hook + ' cleanup',
        '--config-dir', str(folder / 'config'), '--work-dir', str(folder / 'work'),
        '--logs-dir', str(folder / 'logs'), '--cert-name', 'bilibili-toy-s16', '-d', 's16.xinxiayiyan.com',
        '--non-interactive', '--agree-tos', '--register-unsafely-without-email', '--keep-until-expiring']
    env = {k:v for k,v in os.environ.items() if k.lower() not in ('http_proxy','https_proxy','all_proxy')}
    subprocess.run(args, env=env, check=True)
    if not install:
        return
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    archive = folder / ('tls-' + stamp + '.tar.gz')
    with tarfile.open(archive, 'w:gz') as tar:
        for name in ('cert.pem', 'chain.pem', 'fullchain.pem', 'privkey.pem'):
            data = (folder / 'config/live/bilibili-toy-s16' / name).read_bytes()
            entry = tarfile.TarInfo(name); entry.size = len(data); entry.mode = 0o600
            tar.addfile(entry, io.BytesIO(data))
    archive.chmod(0o600)
    stage = '/var/tmp/bilibili-toy-s16-tls-' + stamp
    remote('set -eu\nfilesystem=$(stat -f -c %T /var/tmp)\ncase "$filesystem" in tmpfs|ramfs) exit 1;; esac\nmkdir -m 700 ' + shlex.quote(stage))
    key = 'oss://clawaether-ai-personality/bilibili-toy-deploy/tls-' + stamp + '.tar.gz'
    endpoint = 'https://oss-cn-hongkong.aliyuncs.com'
    command('aliyun', 'oss', 'cp', str(archive), key, '--acl', 'private', '--endpoint', endpoint)
    signed = command('aliyun', 'oss', 'sign', key, '--timeout', '600', '--endpoint', endpoint)
    urls = re.findall(r'https?://\S+', signed)
    if len(urls) != 1:
        raise RuntimeError('Expected one private TLS transfer URL')
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    script = 'set -eu\ncurl --fail --silent --show-error --max-time 60 ' + shlex.quote(urls[0].replace('http://','https://',1)) + ' -o ' + stage + '/tls.tar.gz\n'
    script += "printf '%s  %s\\n' " + digest + ' ' + stage + '/tls.tar.gz | sha256sum -c -\n'
    script += 'docker cp ' + stage + '/tls.tar.gz nginx-app:/data/s16-tls-' + stamp + '.tar.gz\n'
    script += "docker exec nginx-app sh -c " + shlex.quote('set -eu\nmkdir -p /etc/letsencrypt/live/bilibili-toy-s16 /etc/letsencrypt/s16-backups/' + stamp + '\nif [ -f /etc/letsencrypt/live/bilibili-toy-s16/privkey.pem ]; then cp -L /etc/letsencrypt/live/bilibili-toy-s16/*.pem /etc/letsencrypt/s16-backups/' + stamp + '/; fi\ntar -xzf /data/s16-tls-' + stamp + '.tar.gz -C /etc/letsencrypt/live/bilibili-toy-s16\nchmod 600 /etc/letsencrypt/live/bilibili-toy-s16/*.pem\nrm /data/s16-tls-' + stamp + '.tar.gz') + '\n'
    print(remote(script), flush=True)
    command('aliyun','oss','rm',key,'--endpoint',endpoint)
    remote('rm -f ' + stage + '/tls.tar.gz')
    (folder / 'installation.json').write_text(json.dumps({'installed_at':stamp,'staging':stage,'certificate':'bilibili-toy-s16','method':'dns-01'},indent=2))
    print('Installed S16 certificate; test and reload the owned proxy configuration.', flush=True)


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('--install',action='store_true');main(p.parse_args().install)
