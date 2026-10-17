import unittest

from vxruntime.ai_identity_registry import AIIdentity, admit_identity, identity_public_card


class AIIdentityRegistryTests(unittest.TestCase):
    def test_complete_identity_enters_lobby_but_is_not_verified_without_evidence(self):
        result = admit_identity(AIIdentity(
            ai_name="Claude", company_name="Anthropic", agent_name="Claude Financial Agent",
            identity_source="provider-declared",
        ))
        self.assertTrue(result.admitted_to_lobby)
        self.assertEqual(result.identity_status, "DECLARED_PENDING_VERIFICATION")
        self.assertIn("VERIFICATION_EVIDENCE_REQUIRED_FOR_VERIFIED_STATUS", result.blockers)

    def test_missing_company_blocks_entry(self):
        result = admit_identity(AIIdentity(
            ai_name="Example AI", company_name="", agent_name="Example Agent",
            identity_source="provider-declared",
        ))
        self.assertFalse(result.admitted_to_lobby)
        self.assertIn("MISSING_COMPANY_NAME", result.blockers)

    def test_evidence_id_required_for_verified_label(self):
        result = admit_identity(AIIdentity(
            ai_name="GPT", company_name="OpenAI", agent_name="Financial Agent",
            identity_source="provider-declared", verification_evidence_id="EV-123",
        ))
        self.assertEqual(result.identity_status, "VERIFIED")

    def test_public_card_displays_company_and_status(self):
        result = admit_identity(AIIdentity(
            ai_name="Gemini", company_name="Google", agent_name="Gemini Finance",
            identity_source="provider-declared",
        ))
        card = identity_public_card(result)
        self.assertEqual(card["company_name"], "Google")
        self.assertEqual(card["identity_status"], "DECLARED_PENDING_VERIFICATION")

    def test_http_url_rejected(self):
        result = admit_identity(AIIdentity(
            ai_name="xAI", company_name="xAI", agent_name="Grok Agent",
            identity_source="provider-declared", official_url="http://example.com",
        ))
        self.assertFalse(result.admitted_to_lobby)
        self.assertIn("OFFICIAL_URL_MUST_USE_HTTPS", result.blockers)


if __name__ == "__main__":
    unittest.main()
