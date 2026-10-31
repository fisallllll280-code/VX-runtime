import tempfile
import unittest
from pathlib import Path
from vxruntime.brain import VXBrain

BASE = {"mission_id":"m1","domain":"engineering","goal":"review",
        "source_ref":"repo/path","source_version":"commit-1"}

class BrainTests(unittest.TestCase):
    def test_missing_provenance(self):
        with tempfile.TemporaryDirectory() as d:
            b = VXBrain(Path(d)/"brain.db")
            with self.assertRaises(ValueError):
                b.evaluate({"domain":"research"})
            b.close()
    def test_local_evidence_and_idempotency(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/"brain.db"
            b = VXBrain(p)
            result = b.evaluate(dict(BASE,evidence_refs=["unit:fixture"]))
            self.assertEqual(result.status,"PROPOSED")
            self.assertTrue(result.evidence_hash)
            self.assertEqual(b.evaluate(dict(BASE,evidence_refs=["unit:fixture"])).status,"HOLD")
            self.assertTrue(b.verify_local())
            b.close()
            c = VXBrain(p)
            self.assertEqual(c.evaluate(BASE).status,"HOLD")
            self.assertTrue(c.verify_local())
            c.close()
    def test_no_evidence_is_hold(self):
        with tempfile.TemporaryDirectory() as d:
            b = VXBrain(Path(d)/"brain.db")
            self.assertEqual(b.evaluate(BASE).status,"HOLD")
            b.close()
    def test_financial_actions_blocked(self):
        with tempfile.TemporaryDirectory() as d:
            b = VXBrain(Path(d)/"brain.db")
            m = dict(BASE,domain="finance",action="transfer",simulation_only=True)
            self.assertEqual(b.evaluate(m).status,"BLOCK")
            m["action"]="analyze"
            self.assertEqual(b.evaluate(m).status,"HOLD")
            b.close()
    def test_spend_and_external_effect_blocked(self):
        with tempfile.TemporaryDirectory() as d:
            b = VXBrain(Path(d)/"brain.db")
            self.assertEqual(b.evaluate(dict(BASE,spend_sar=1)).status,"BLOCK")
            self.assertEqual(b.evaluate(dict(BASE,external_effect=True)).status,"BLOCK")
            b.close()
    def test_pr_evidence_gate(self):
        with tempfile.TemporaryDirectory() as d:
            b = VXBrain(Path(d)/"brain.db")
            m = dict(BASE,evidence_refs=["fixture"],pr_snapshot={"repo":"a/b"})
            decision=b.evaluate(m)
            self.assertEqual(decision.status,"HOLD")
            self.assertIn("PR_AUDIT_HOLD",decision.rationale)
            b.close()

if __name__=="__main__":
    unittest.main()
