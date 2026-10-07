import json
from pathlib import Path
import tempfile
import tomllib
import unittest
from workflows.harness.install import install

class PreserveConfiguration(unittest.TestCase):
    def test_registration_preserves_other_hooks_and_mcp_servers(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            existing={'hooks':{'SessionStart':[{'hooks':[{'type':'command','command':'echo existing'}]}]}}
            (root/'hooks.json').write_text(json.dumps(existing))
            (root/'config.toml').write_text('[mcp_servers.other]\ncommand="other"\n')
            result=install(root,Path.cwd())
            hooks=json.loads((root/'hooks.json').read_text())
            self.assertEqual(hooks['hooks']['SessionStart'][0],existing['hooks']['SessionStart'][0])
            self.assertIn('Stop',hooks['hooks'])
            config=tomllib.loads((root/'config.toml').read_text())
            self.assertEqual(config['mcp_servers']['other']['command'],'other')
            self.assertIn('exploration-lab',config['mcp_servers'])
            self.assertEqual(result['hook_trust'],'requires_native_review')
            install(root,Path.cwd())
            self.assertEqual(len(json.loads((root/'hooks.json').read_text())['hooks']['SessionStart']),2)
