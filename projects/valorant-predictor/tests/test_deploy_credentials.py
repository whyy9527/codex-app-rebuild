import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('valorant_deploy', Path(__file__).resolve().parents[1] / 'scripts/deploy.py')
deploy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(deploy)


class DeployCredentialTests(unittest.TestCase):
    def test_oauth_sts_session_reaches_private_oss_transport(self):
        profile = {'mode': 'OAuth', 'access_key_id': 'fixture-id', 'access_key_secret': 'fixture-secret', 'sts_token': 'fixture-session'}
        config = deploy.oss_credentials(profile)
        self.assertIn('stsToken=fixture-session\n', config)
        self.assertIn('accessKeyID=fixture-id\n', config)
        self.assertIn('accessKeySecret=fixture-secret\n', config)

    def test_existing_ak_profile_uses_no_sts_token(self):
        config = deploy.oss_credentials({'access_key_id': 'fixture-id', 'access_key_secret': 'fixture-secret'})
        self.assertNotIn('stsToken=', config)
