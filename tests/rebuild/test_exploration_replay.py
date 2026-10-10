"""Counterexamples for empirical replay isolation, not evidence of RSI gains."""
import importlib.util
from pathlib import Path
import tempfile
import shutil
import json
import unittest

spec=importlib.util.spec_from_file_location('case_replay',Path(__file__).resolve().parents[2]/'projects/exploration-ablation/replay.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)

class EmpiricalReplay(unittest.TestCase):
    def test_future_outcome_cannot_change_policy_action_and_repeats_do_not_gain(self):
        world={'actions':[{'id':'a','label':'visible A'},{'id':'b','label':'visible B'}],
               'outcomes':{'a':{'atoms':['one'],'evidence':'actual-a','receipt_sha256':'a'},
                           'b':{'atoms':['hidden'],'evidence':'actual-b','receipt_sha256':'b'}}}
        policy={'rules':[],'repeat_penalty':0}
        first=r.replay(world,policy)
        world['outcomes']['b']['atoms']=['huge future reward']*100
        again=r.replay(world,policy)
        self.assertEqual(first,again)
        self.assertEqual(first['score'],1)
        self.assertEqual([x['new_atoms'] for x in first['trace']],[1,0])
        with self.assertRaises(ValueError):r.replay(world,policy,budget=0)
        world['outcomes'].pop('a')
        with self.assertRaises(ValueError):r.replay(world,policy)

    def test_actual_world_recomputes_root_identity_instead_of_trusting_flag(self):
        source=Path(__file__).resolve().parents[2]/'projects/exploration-ablation/evidence/training01'
        world=r.load_world(source)
        self.assertEqual(len(world['actions']),4)
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp)/'world';shutil.copytree(source,dest)
            p=dest/'gems-before.json';d=json.loads(p.read_text());d['snapshot']+='\nunknown changed root';p.write_text(json.dumps(d))
            with self.assertRaises(ValueError):r.load_world(dest)
