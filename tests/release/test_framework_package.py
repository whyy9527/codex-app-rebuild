import hashlib
from pathlib import Path
import tempfile
import unittest

from scripts.package_framework import export, git, selected

class FrameworkPackage(unittest.TestCase):
    def test_scope_keeps_runtime_fixture_but_excludes_cases_private_and_case_tests(self):
        for name in ('runtime/dream.py', 'capabilities/rebuild/frontend.py',
                     'tests/rebuild/test_dream.py', 'projects/dream-rsi-check/worker.py'):
            self.assertTrue(selected(name))
        for name in ('projects/xiaogj-web/private/local-auth.json', 'projects/duolingo-web/image.png',
                     'projects/education-swift/Sources/LingoSeed/LearningView.swift',
                     'tests/rebuild/test_exploration_tree.py', 'projects/dream-rsi-check/private/key.json'):
            self.assertFalse(selected(name))

    def test_committed_snapshot_preserves_framework_bytes_and_rejects_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'source'
            source.mkdir()
            git(source, 'init', '-q')
            samples = {'pyproject.toml': '[project]\nversion = "0.2.0"\n',
                       'README.md': '# Fixture framework\n',
                       'runtime/dream.py': '# committed runtime\n',
                       'capabilities/rebuild/frontend.py': '# committed comparator\n',
                       'projects/dream-rsi-check/worker.py': '# synthetic fixture\n'}
            for name, text in samples.items():
                path = source / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text)
            git(source, 'add', '--', *samples)
            git(source, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                'commit', '-qm', 'fixture')
            (source / 'runtime/dream.py').write_text('# unrelated dirty work\n')
            output = Path(directory) / 'snapshot'
            manifest = export(source, 'HEAD', output, 'whyy9527/codex-app-rebuild')
            for name in manifest['files']:
                self.assertEqual(hashlib.sha256((output / name).read_bytes()).hexdigest(), manifest['files'][name])
                if name.startswith(('capabilities/', 'runtime/')):
                    self.assertEqual((output / name).read_bytes(), git(source, 'show', 'HEAD:' + name))
            self.assertTrue(all(name.startswith('projects/dream-rsi-check/') for name in manifest['files'] if name.startswith('projects/')))
            self.assertNotIn('projects/xiaogj-web', (output / 'README.md').read_text())
            with self.assertRaisesRegex(ValueError, 'new output'):
                export(source, 'HEAD', output, 'whyy9527/codex-app-rebuild')
