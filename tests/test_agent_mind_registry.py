import unittest
from vxruntime.agent_mind_registry import VXAgent, VXMind, assess

class AgentMindRegistryTests(unittest.TestCase):
    def test_unconfigured_connector_holds(self):
        result = assess(VXAgent("agent-1", "mind-1", ("research",)), VXMind("mind-1", "RESEARCH"))
        self.assertEqual(result["decision"], "HOLD")
        self.assertFalse(result["execution_enabled"])

    def test_wrong_mind_holds(self):
        result = assess(VXAgent("agent-1", "wrong", ("research",)), VXMind("mind-1", "RESEARCH"))
        self.assertIn("MIND_BINDING_INVALID", result["reasons"])

    def test_high_impact_actions_denied(self):
        result = assess(VXAgent("agent-1", "mind-1", ("finance",), ("TRANSFER_FUNDS",), ("sha256:a",), "approval:1"),
                        VXMind("mind-1", "FINANCIAL", "connector", "probe:1"))
        self.assertIn("FORBIDDEN_OPERATION", result["reasons"])

    def test_proposed_binding_never_executes(self):
        agent = VXAgent("agent-1", "mind-1", ("research",), evidence_refs=("sha256:a",), approval_ref="approval:1")
        mind = VXMind("mind-1", "RESEARCH", "connector", "probe:1")
        first = assess(agent, mind)
        self.assertEqual(first["decision"], "ELIGIBLE_FOR_INDEPENDENT_VERIFICATION")
        self.assertFalse(first["execution_enabled"])
        self.assertEqual(first["manifest_sha256"], assess(agent, mind)["manifest_sha256"])

if __name__ == "__main__":
    unittest.main()
