import tempfile
import unittest
from pathlib import Path
from vxruntime.agents import AgentRunner, AGENTS

class AgentTests(unittest.TestCase):
    def test_all_agents_persist_and_deduplicate(self):
        with tempfile.TemporaryDirectory() as d:
            db = Path(d) / "memory.db"
            runner = AgentRunner(db)
            for i, agent in enumerate(AGENTS):
                result = runner.run(agent, f"task-{i}", {"source": "fixture"})
                self.assertEqual(result.status.value, "success")
                self.assertEqual(result.output["mode"], "LOCAL_SIMULATION")
                self.assertEqual(len(runner.memory.recall(agent, "result")), 1)
            self.assertTrue(runner.runtime.verify())
            self.assertTrue(runner.memory.integrity_check())
            with self.assertRaises(ValueError):
                runner.run("graphify", "task-0", {"source": "fixture"})
            runner.close()
            reopened = AgentRunner(db)
            self.assertEqual(len(reopened.memory.recall("graphify", "result")), 1)
            reopened.close()

if __name__ == "__main__":
    unittest.main()
