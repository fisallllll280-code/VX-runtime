import unittest
from vxruntime.pr_auditor import audit_pr

GOOD = {"repo":"owner/repo","head_sha":"abc123","checks":[
    {"name":"unit","url":"https://github.com/example/check/1","conclusion":"success"}],
    "independent_review":True,"source_access_confirmed":True}

class PRAuditorTests(unittest.TestCase):
    def test_good_advisory_pass(self):
        self.assertEqual(audit_pr(GOOD).verdict,"PASS")

    def test_missing_evidence_holds(self):
        self.assertEqual(audit_pr({}).verdict,"HOLD")

    def test_failed_ci_blocks(self):
        bad = dict(GOOD,checks=[{"name":"unit","url":"https://github.com/example/check/2","conclusion":"failure"}])
        self.assertEqual(audit_pr(bad).verdict,"BLOCK")

    def test_protected_change_blocks(self):
        self.assertEqual(audit_pr(dict(GOOD,protected_files_changed=True)).verdict,"BLOCK")

    def test_requested_merge_holds(self):
        self.assertEqual(audit_pr(dict(GOOD,merge_requested=True)).verdict,"HOLD")

if __name__ == "__main__":
    unittest.main()
