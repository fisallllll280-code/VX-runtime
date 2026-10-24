"""Unit tests for the VX Social Command local approval gate."""
import copy
from pathlib import Path
import tempfile
import unittest
from tools.vx_social_command import (
    PolicyError, load, save, register, draft, transition, publish, verify
)


class SocialCommandTests(unittest.TestCase):
    def setUp(self):
        self.data = load(Path("/path/that/does/not/exist/ledger.json"))
        self.account = register(self.data, "x", "@VAIXLNS", "owner")

    def test_account_is_not_marked_connected(self):
        self.assertEqual(self.data["accounts"][0]["status"], "UNCONNECTED")
        self.assertEqual(verify(self.data)["connected"], 0)

    def test_reject_unknown_platform_and_duplicate(self):
        with self.assertRaises(PolicyError):
            register(self.data, "unapproved", "@VAIXLNS", "owner")
        with self.assertRaises(PolicyError):
            register(self.data, "x", "@VAIXLNS", "owner")

    def test_approval_requires_distinct_reviewer(self):
        post = draft(self.data, self.account, "A product announcement draft", "writer")
        with self.assertRaises(PolicyError):
            transition(self.data, post, "approve", "reviewer")
        self.assertEqual(transition(self.data, post, "submit", "writer"), "REVIEW")
        with self.assertRaises(PolicyError):
            transition(self.data, post, "approve", "writer")
        self.assertEqual(transition(self.data, post, "approve", "reviewer"), "APPROVED")
        self.assertTrue(self.data["posts"][0]["approval_hash"])

    def test_publish_is_always_denied_even_after_approval(self):
        post = draft(self.data, self.account, "Hello", "writer")
        transition(self.data, post, "submit", "writer")
        transition(self.data, post, "approve", "owner")
        with self.assertRaisesRegex(PolicyError, "PUBLISH_DISABLED"):
            publish(self.data, post, "owner")
        self.assertEqual(self.data["posts"][0]["delivery"], "DISABLED")

    def test_event_tamper_detection(self):
        changed = copy.deepcopy(self.data)
        changed["events"][0]["actor"] = "attacker"
        with self.assertRaisesRegex(PolicyError, "integrity"):
            verify(changed)

    def test_roundtrip(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "ledger.json"
            save(path, self.data)
            restored = load(path)
            self.assertEqual(verify(restored)["events"], 1)


if __name__ == "__main__":
    unittest.main()
