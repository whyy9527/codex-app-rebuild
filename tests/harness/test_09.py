from pathlib import Path
import tempfile
import unittest
from runtime.codex_host import CodexHost
from workflows.harness.install import install

class NativeCodexDiscovery(unittest.TestCase):
    def test_real_host_discovers_registered_tools_and_hook_trust(self):
        with tempfile.TemporaryDirectory() as folder:
            install(Path(folder),Path.cwd())
            with CodexHost(codex_home=folder) as host:
                hooks=host.request('hooks/list',{'cwds':[str(Path.cwd())]})
                self.assertIn('data',hooks)
                own=[h for entry in hooks['data'] for h in entry['hooks'] if h.get('statusMessage')=='Exploration Lab']
                self.assertEqual({h['eventName'] for h in own},{'sessionStart','stop','userPromptSubmit'})
                self.assertTrue(all(h['trustStatus']=='untrusted' for h in own))
                thread=host.request('thread/start',{'cwd':str(Path.cwd()),'ephemeral':True})['thread']['id']
                status=host.request('mcpServerStatus/list',{'threadId':thread})
                server=next(s for s in status['data'] if s['name']=='exploration-lab')
                self.assertIn('exploration_verify',server['tools'])
