import unittest
from vxruntime.competence_lab import evaluate
class CompetenceTests(unittest.TestCase):
    def test_detects_improvement_but_not_verified(self):
        r=evaluate("vx",{"a":False,"b":True},{"a":True,"b":True},
                   {"a":"run:1","b":"run:2"},["b"])
        self.assertTrue(r.eligible)
        self.assertEqual(r.score,1.0)
    def test_missing_evidence_blocks(self):
        r=evaluate("vx",{"a":False},{"a":True},{})
        self.assertFalse(r.eligible)
    def test_regression_blocks(self):
        r=evaluate("vx",{"a":True,"b":False},{"a":False,"b":True},
                   {"a":"run:1","b":"run:2"},["a"])
        self.assertFalse(r.eligible)
    def test_requires_comparable_cases(self):
        with self.assertRaises(ValueError):
            evaluate("vx",{"a":True},{"b":True},{"b":"x"})
if __name__=="__main__":
    unittest.main()
