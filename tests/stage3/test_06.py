import unittest
from capabilities.exploration.benchmark import split_cases,case_key

class ValidationSplit(unittest.TestCase):
    def test_reproducible_disjoint_instances_without_reordering_leak(self):
        first=split_cases(seed=41,count=8)
        self.assertEqual(first,split_cases(seed=41,count=8))
        train={case_key(c) for c in first['training']}
        validation={case_key(c) for c in first['validation']}
        self.assertFalse(train & validation)
        self.assertEqual(case_key(([2,3,4],10)),case_key(([4,2,3],10)))
        self.assertEqual(len(validation),8)
