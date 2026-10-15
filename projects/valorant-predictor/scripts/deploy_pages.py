"""Publish the verified runtime to an isolated GitHub Pages branch."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

from deploy import api, DOMAIN, PROJECT, REPO

REPOSITORY = 'whyy9527/rebuild-any-web'
BRANCH = 'valorant-site'


def gh(*args, payload=None):
    result = subprocess.run(['gh', 'api', *args] + (['--input', '-'] if payload is not None else []), input=json.dumps(payload) if payload is not None else None, capture_output=True, text=True, check=True)
    return json.loads(result.stdout) if result.stdout.strip() else {}


def main(out):
    output = REPO / out
    output.mkdir(parents=True, exist_ok=False)
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    if subprocess.check_output(['git', 'status', '--porcelain', '--', str(PROJECT.relative_to(REPO))], text=True).strip():
        raise RuntimeError('Commit project inputs before publication')
    if subprocess.check_output(['git', 'ls-remote', 'origin', 'refs/heads/main'], text=True).split()[0] != revision:
        raise RuntimeError('Publish only pushed main')
    subprocess.run(['python3', str(PROJECT / 'scripts/build.py')], check=True)
    dist = PROJECT / 'dist'
    (dist / 'revision.json').write_text(json.dumps({'git_revision': revision, 'domain': DOMAIN}) + '\n')
    (dist / 'CNAME').write_text(DOMAIN + '\n')
    (dist / '.nojekyll').touch()
    manifest = {str(p.relative_to(dist)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(dist.rglob('*')) if p.is_file()}
    with tempfile.TemporaryDirectory(prefix='valorant-pages-') as directory:
        work = Path(directory)
        def git(*args):return subprocess.check_output(['git', '-C', str(work), *args], text=True).strip()
        git('init', '-b', BRANCH)
        git('remote', 'add', 'origin', 'git@github.com:' + REPOSITORY + '.git')
        existing = subprocess.check_output(['git', 'ls-remote', 'origin', 'refs/heads/' + BRANCH], cwd=REPO, text=True).strip()
        if existing:
            git('fetch', '--depth=1', 'origin', BRANCH)
            git('reset', '--hard', 'FETCH_HEAD')
            for child in work.iterdir():
                if child.name == '.git':continue
                if child.is_dir():shutil.rmtree(child)
                else:child.unlink()
        shutil.copytree(dist, work, dirs_exist_ok=True)
        git('add', '--all')
        if git('status', '--porcelain'):git('commit', '-m', 'Publish VALORANT runtime ' + revision)
        git('push', 'origin', BRANCH)
        pages_revision = git('rev-parse', 'HEAD')
    endpoint = 'repos/' + REPOSITORY + '/pages'
    try:site = gh(endpoint)
    except subprocess.CalledProcessError as exc:
        if '404' not in exc.stderr:raise
        site = gh('-X', 'POST', endpoint, payload={'source': {'branch': BRANCH, 'path': '/'}})
    if site.get('cname') not in [None, DOMAIN] or site.get('source', {}).get('branch') != BRANCH:
        raise RuntimeError('Refusing to replace an unrelated Pages site')
    site = gh('-X', 'PUT', endpoint, payload={'cname': DOMAIN, 'source': {'branch': BRANCH, 'path': '/'}})
    records = api('alidns', 'DescribeDomainRecords', DomainName='xinxiayiyan.com', PageSize=500)['DomainRecords']['Record']
    own = [r for r in records if r['RR'] == 'valorant']
    if len(own) != 1 or (own[0]['Type'], own[0]['Value']) not in [('A', '47.104.152.169'), ('CNAME', 'whyy9527.github.io')]:
        raise RuntimeError('Refusing to overwrite an unrelated DNS destination')
    dns = api('alidns', 'UpdateDomainRecord', RecordId=own[0]['RecordId'], RR='valorant', Type='CNAME', Value='whyy9527.github.io', TTL=600)
    receipt = {'git_revision': revision, 'pages_revision': pages_revision, 'domain': DOMAIN, 'repository': REPOSITORY, 'branch': BRANCH, 'files': manifest, 'dns': dns, 'pages': site}
    (output / 'submitted.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print('Submitted Pages release; HTTPS and browser checks still required:', revision)


if __name__ == '__main__':
    parser = argparse.ArgumentParser();parser.add_argument('--out', required=True);main(parser.parse_args().out)
