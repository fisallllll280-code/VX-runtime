"""Local, dependency-free tests for persistent VX memories."""
import tempfile
import unittest
from pathlib import Path
from vxruntime.memory import MemoryVault


class MemoryTests(unittest.TestCase):
    def test_persistence_dedup_and_tool_isolation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "memory.sqlite3"
            vault = MemoryVault(path)
            a = vault.remember("github", "finding", {"issue": 4}, "repo/a", "sha1")
            b = vault.remember("github", "finding", {"issue": 4}, "repo/b", "sha2")
            self.assertTrue(a["created"])
            self.assertTrue(b["duplicate"])
            self.assertEqual(b["original_source"], "repo/a")
            self.assertEqual(len(vault.recall("github")), 1)
            self.assertEqual(vault.recall("finance"), [])
            s = vault.generate_slice("github", "review", ["inspect"], [a["id"]])
            self.assertFalse(vault.generate_slice("github", "review", ["inspect"], [a["id"]])["created"])
            self.assertEqual(s["status"], "PROPOSED")
            with self.assertRaises(ValueError):
                vault.generate_slice("finance", "review", ["inspect"], [a["id"]])
            self.assertTrue(vault.integrity_check())
            vault.close()
            reopened = MemoryVault(path)
            self.assertEqual(len(reopened.recall("github")), 1)
            self.assertTrue(reopened.integrity_check())
            reopened.close()


if __name__ == "__main__":
    unittest.main()
