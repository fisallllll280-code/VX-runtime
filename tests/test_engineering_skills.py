import unittest
from vxruntime.engineering_skills import route, WORKFLOWS

class EngineeringSkillsTests(unittest.TestCase):
    def test_deterministic_routing(self):
        a=route("implement",source_ref="mattpocock/skills",source_version="sha-1")
        b=route("implement",source_ref="mattpocock/skills",source_version="sha-1")
        self.assertEqual(a,b)
        self.assertEqual(a.state,"PROPOSED")
        self.assertEqual(a.steps,("tdd","review","pr"))
    def test_unsupported_fails_closed(self):
        with self.assertRaises(ValueError):
            route("send-money",source_ref="repo",source_version="sha")
        with self.assertRaises(ValueError):
            route("review",source_ref="repo",source_version="")
    def test_no_commands(self):
        self.assertTrue(all(isinstance(s,str) and "/" not in s for steps in WORKFLOWS.values() for s in steps))

if __name__=="__main__":
    unittest.main()
