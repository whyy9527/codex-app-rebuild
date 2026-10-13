"""Export a framework-only snapshot from committed Git objects, without publishing."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import tomllib

ROOT_FILES = {'README.md', 'AGENTS.md', 'CHANGELOG.md', 'THIRD_PARTY_NOTICES.md',
              'LICENSE', '.gitignore', 'pyproject.toml', 'tests/__init__.py'}
CASE_TESTS = {'test_enrollment_choices.py', 'test_exploration_replay.py',
              'test_guide_replay04.py', 'test_exploration_tree.py'}
SKILLS = {'exploration-lab', 'lottie-svg-dom-rendering', 'macos-owned-app-audio-output'}
FIXTURE = 'projects/dream-rsi-check/'


def selected(name):
    path = PurePosixPath(name)
    if any(part in {'private', 'artifacts', 'node_modules', '__pycache__'} for part in path.parts):
        return False
    if name in ROOT_FILES or name == 'scripts/package_framework.py':
        return True
    if name.startswith(('capabilities/', 'runtime/', 'workflows/')):
        return path.suffix in {'.py', '.md'}
    if name.startswith('docs/'):
        return path.suffix == '.md' and name != 'docs/ORG-SYNC.md'
    if name.startswith(('tests/harness/', 'tests/rebuild/')):
        return path.suffix == '.py' and path.name not in CASE_TESTS
    if name.startswith('tests/release/'):
        return path.suffix == '.py'
    if name.startswith(FIXTURE):
        return path.suffix in {'.py', '.json', '.md'}
    return (len(path.parts) == 4 and path.parts[:2] == ('.codex', 'skills')
            and path.parts[2] in SKILLS and path.name == 'SKILL.md')


def git(root, *argv):
    return subprocess.check_output(['git', '-C', str(root), *argv])


def adapt(name, text, source):
    if name == 'README.md':
        start, end = text.find('## Duolingo 实践'), text.find('## 文档与验证')
        if start >= 0 and end > start:
            text = text[:start] + ('## 发行范围\n\n本发行版不包含Duolingo或校管家App、原版素材与私有历史。'
                    '`projects/`保留合成的Dream-RSI协议夹具，用于独立验证真实发现／评价、全池回放和再次部署。'
                    '新App按项目入口建立自己的配置。案例复盘见[校管家](docs/XIAOGJ-LESSONS.md)及'
                    '[Duolingo](docs/DUOLINGO-LESSONS.md)。\n\n') + text[end:]
        text = text.replace('projects/duolingo-web/rebuild.json', 'projects/my-app/rebuild.json')
        text += ('\n框架来源和逐文件摘要见 `FRAMEWORK-SOURCE.json`。原始源码：'
                 f'[{source}]({source})。\n')
    elif name == 'CHANGELOG.md':
        text = text.replace('- 保存校管家收尾结论、普通速度可视E2E巡演和可重新生成的ECharts探索树；私有数据、素材和历史不随代码提交。',
                            '- 源仓库保留校管家案例收尾、可视E2E巡演与探索树；本框架发行包仅附带复盘和方法修订。')
    elif name == 'AGENTS.md':
        text = re.sub(r'先遵循用户当前要求。.*?(?=\n\n)',
                      '先遵循用户当前要求。结束案例后不自动恢复探索。本发行版只附带框架协议夹具，'
                      '不包含历史App案例；复盘引用源仓库的固定提交，不能当作本仓库当前产品交付。', text)
    elif name == 'docs/ARCHITECTURE.md':
        text = text.split('## 案例实现')[0] + ('## 发行边界\n\n本快照包含框架代码、测试和'
               '`projects/dream-rsi-check`合成协议夹具。App实现、观察器、私有历史和媒体由消费项目拥有，'
               '不在此快照内。历史反例见[校管家复盘](XIAOGJ-LESSONS.md)和[Duolingo复盘](DUOLINGO-LESSONS.md)。\n')
    elif name == 'workflows/rebuild/PROJECT.md':
        text = text.replace('[Duolingo 配置](../../projects/duolingo-web/rebuild.json)是完整已有案例。',
                            '本发行版不包含历史App案例；新项目从上面的最小配置开始。')
        text = text.replace('projects/duolingo-web/rebuild.json', 'projects/my-app/rebuild.json')
    elif name == 'THIRD_PARTY_NOTICES.md':
        start, end = text.find('## Duolingo 案例'), text.find('## 依赖与研究来源')
        text = text[:start] + ('## 案例与素材\n\n本发行版不包含App案例的第三方媒体、授权账号或私有观察。'
                '源仓库历史案例的内容归其权利人；框架MIT许可不授予再分发第三方素材的权利。\n\n') + text[end:]
        case_only = ('| Rive iOS ', '| Lottie ', '| Apache ECharts ', '| @nestjs/jwt ',
                     '| bcryptjs ', '| cookie-parser ', '| pinyin-pro ')
        text = '\n'.join(line for line in text.splitlines() if not line.startswith(case_only)) + '\n'
        text = text.replace('当前案例引用：', '框架按需使用的依赖：')
    return text


def export(root, ref, output, source_repo):
    root, output = Path(root).resolve(), Path(output).resolve()
    if output.exists():
        raise ValueError('choose a new output directory')
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', source_repo):
        raise ValueError('source repository must be owner/name')
    commit = git(root, 'rev-parse', '--verify', ref + '^{commit}').decode().strip()
    paths = git(root, 'ls-tree', '-r', '--name-only', commit).decode().splitlines()
    names = {name for name in paths if selected(name)}
    source = f'https://github.com/{source_repo}/tree/{commit}'
    files = {}
    for name in sorted(names):
        raw = git(root, 'show', commit + ':' + name)
        text = raw.decode('utf-8')
        if name.endswith('.md'):
            text = adapt(name, text, source)
            def link(match):
                label, target = match.groups()
                if re.match(r'^[a-zA-Z]+:', target) or target.startswith(('#', '/')):
                    return match.group(0)
                path, _, anchor = target.partition('#')
                resolved = (root / PurePosixPath(name).parent / path).resolve()
                if not resolved.is_relative_to(root):
                    return match.group(0)
                relative = resolved.relative_to(root).as_posix()
                if relative in names or any(n.startswith(relative + '/') for n in names):
                    return match.group(0)
                if relative in paths:
                    url = f'https://github.com/{source_repo}/blob/{commit}/{relative}'
                    return f'[{label}]({url}' + (('#' + anchor) if anchor else '') + ')'
                return f'{label}（历史或私有证据，发行版未附带）'
            text = re.sub(r'\[([^\]\n]+)\]\(([^)\s]+)\)', link, text)
        files[name] = text.encode('utf-8')
    version = tomllib.loads(files['pyproject.toml'].decode())['project']['version']
    manifest = {'schema_version': 1, 'kind': 'framework_release_snapshot', 'version': version,
                'source_repository': source_repo, 'source_commit': commit,
                'scope': 'framework, documentation, tests and synthetic protocol fixture; no App cases or private inputs',
                'adapted': [name for name, data in files.items() if data != git(root, 'show', commit + ':' + name)],
                'files': {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}}
    output.mkdir(parents=True)
    for name, data in files.items():
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    (output / 'FRAMEWORK-SOURCE.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', default='.')
    parser.add_argument('--ref', default='HEAD')
    parser.add_argument('--source-repo', default='whyy9527/codex-app-rebuild')
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    result = export(args.workspace, args.ref, args.out, args.source_repo)
    print(json.dumps({'source_commit': result['source_commit'], 'version': result['version'],
                      'files': len(result['files']), 'out': args.out}))


if __name__ == '__main__':
    main()
