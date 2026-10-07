from pathlib import Path
import tempfile
import unittest
from workflows.paper.validation import validate_programs

class ActualValidation(unittest.TestCase):
    def test_validation_executes_both_sources_and_keeps_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            paths={}
            for name,source in {'valid':'def pack(w,c):\n return [[i] for i in range(len(w))]\n','invalid':'def pack(w,c):\n return [[0]]\n'}.items():
                root=Path(folder)/name
                root.mkdir()
                (root/'pack.py').write_text(source)
                paths[name]=root
            report=validate_programs(paths,seeds=[41],count=1)
            self.assertFalse(report['selection_allowed'])
            self.assertEqual(report['programs']['valid']['failures'],0)
            self.assertEqual(report['programs']['invalid']['failures'],1)
            self.assertLess(report['programs']['invalid']['mean_score'],report['programs']['valid']['mean_score'])
