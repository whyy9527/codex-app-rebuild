"""Prevent the certificate hook from altering unrelated DNS records."""
import importlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import hashlib

hook = importlib.import_module('projects.bilibili-toy.tools.dns_hook')


class DnsOwnership(unittest.TestCase):
    def test_other_domains_fail_before_any_api_call(self):
        with patch.dict(os.environ, {'CERTBOT_DOMAIN': 'landing.xinxiayiyan.com', 'CERTBOT_VALIDATION': 'a' * 43}), patch.object(hook, 'api') as api:
            with self.assertRaises(ValueError): hook.main('auth')
            api.assert_not_called()

    def test_cleanup_preserves_changed_record_and_removes_only_owned_id(self):
        value = 'a' * 43
        with tempfile.TemporaryDirectory() as tmp, patch.object(hook, 'ROOT', Path(tmp)), patch.dict(os.environ, {'CERTBOT_DOMAIN':'s16.xinxiayiyan.com','CERTBOT_VALIDATION':value}):
            folder = Path(tmp) / 'private/certbot'; folder.mkdir(parents=True)
            state = folder / ('challenge-' + hashlib.sha256(value.encode()).hexdigest() + '.json')
            state.write_text(json.dumps({'id':'owned-id','value':value}))
            record = {'RR':hook.RR,'Type':'TXT','Value':'different-value','DomainName':'xinxiayiyan.com'}
            with patch.object(hook,'api',return_value=record) as api:
                with self.assertRaises(RuntimeError): hook.main('cleanup')
                self.assertEqual(api.call_count,1)
                self.assertTrue(state.exists())
            record['Value']=value
            with patch.object(hook,'api',side_effect=[record,{}]) as api:
                hook.main('cleanup')
                api.assert_any_call('DeleteDomainRecord','--RecordId','owned-id')
                self.assertFalse(state.exists())
