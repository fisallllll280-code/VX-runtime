import unittest
from vxruntime.agent_assurance import AgentPrincipal, TaskGrant, AgentReceipt, authorize, admit

class AgentAssuranceTests(unittest.TestCase):
    def setUp(self):
        self.producer=AgentPrincipal("a","IMPLEMENTER",frozenset({"build"}))
        self.verifier=AgentPrincipal("b","INDEPENDENT_VERIFIER",frozenset())
        self.grant=TaskGrant("task","a","build","rev1",10,20)
        self.receipt=AgentReceipt("task","a","b","rev1","a"*64,True)

    def test_authorized_only_eligible(self):
        self.assertEqual(authorize(self.producer,self.grant,11,"rev1")["decision"],"ELIGIBLE_TO_DISPATCH")
    def test_expiry_denied(self):
        self.assertEqual(authorize(self.producer,self.grant,20,"rev1")["decision"],"HOLD")
    def test_revocation_denied(self):
        g=TaskGrant("task","a","build","rev1",10,20,True)
        self.assertEqual(authorize(self.producer,g,11,"rev1")["decision"],"HOLD")
    def test_capability_mismatch(self):
        p=AgentPrincipal("a","IMPLEMENTER",frozenset())
        self.assertEqual(authorize(p,self.grant,11,"rev1")["decision"],"REJECT")
    def test_revision_drift(self):
        self.assertEqual(authorize(self.producer,self.grant,11,"rev2")["decision"],"HOLD")
    def test_distinct_verifier(self):
        r=AgentReceipt("task","a","a","rev1","a"*64,True)
        self.assertNotEqual(admit(r,self.producer,self.producer,self.grant,11,policy_approved=True)["decision"],"ELIGIBLE_FOR_GOVERNANCE")
    def test_policy_denial(self):
        self.assertEqual(admit(self.receipt,self.producer,self.verifier,self.grant,11,policy_approved=False)["decision"],"HOLD")
    def test_fake_digest(self):
        r=AgentReceipt("task","a","b","rev1","invalid",True)
        self.assertEqual(admit(r,self.producer,self.verifier,self.grant,11,policy_approved=True)["decision"],"HOLD")
    def test_eligible_not_approved(self):
        self.assertEqual(admit(self.receipt,self.producer,self.verifier,self.grant,11,policy_approved=True)["decision"],"ELIGIBLE_FOR_GOVERNANCE")

if __name__=="__main__":
    unittest.main()
