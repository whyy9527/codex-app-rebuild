import tempfile
import unittest
from pathlib import Path
from capabilities.exploration.ledger import Ledger
from capabilities.exploration.replay import Replay


class Baseline(unittest.TestCase):
    def test_persistence(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "records.sqlite"
            ledger = Ledger(path)
            ledger.append({"id": "candidate", "parent": None})
            ledger.close()
            ledger = Ledger(path)
            self.assertEqual(ledger.records()[0]["id"], "candidate")
            ledger.close()

    def test_prefix_and_frozen_input(self):
        nodes = [{"id": "a", "parent": "root", "score": .4},
                 {"id": "b", "parent": "a", "score": .9}]
        replay = Replay(nodes)
        nodes[0]["score"] = 99
        self.assertEqual(len(replay.observation()), 1)
        self.assertEqual(replay.step(["root"])["revealed"][0]["score"], .4)
        self.assertEqual(len(replay.observation()), 2)
        self.assertEqual(replay.step(["a"])["revealed"][0]["score"], .9)
