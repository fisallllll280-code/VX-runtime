import unittest
from vxruntime.operator import SovereignOperator

class OperatorTests(unittest.TestCase):
    def test_dry_run_no_effect_and_approval(self):
        o=SovereignOperator()
        calls=[]
        receipt=o.simulate("m1","analyze",{"value":42})
        self.assertEqual(receipt.decision,"READY")
        self.assertEqual(calls,[])
        held=o.execute("m1","analyze",{"value":42},lambda p:calls.append(p))
        self.assertEqual(held.decision,"HOLD")
        o.approve(receipt)
        result=o.execute("m1","analyze",{"value":42},lambda p:calls.append(p) or "ok")
        self.assertEqual(result.decision,"EXECUTED")
        self.assertEqual(len(calls),1)
        self.assertTrue(o.runtime.verify())
        self.assertEqual(o.execute("m1","analyze",{"value":42},lambda p:"ok").decision,"BLOCK")

    def test_denies_sensitive_and_spend(self):
        o=SovereignOperator()
        self.assertEqual(o.simulate("p","publish",{}).decision,"BLOCK")
        self.assertEqual(o.simulate("q","draft",{"spend_sar":1}).decision,"BLOCK")
        with self.assertRaises(ValueError):
            SovereignOperator({"merge"})

    def test_changed_payload_invalidates_approval(self):
        o=SovereignOperator()
        rec=o.simulate("task","draft",{"text":"first"})
        o.approve(rec)
        self.assertEqual(o.execute("task","draft",{"text":"changed"},lambda _:True).decision,"BLOCK")

if __name__=="__main__":
    unittest.main()
