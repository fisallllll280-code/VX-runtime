import tempfile
import unittest
from pathlib import Path
from vxruntime.cognitive_fabric import CognitiveFabric, INDEX_KEYS

class FabricTests(unittest.TestCase):
    def test_omega_28_and_recall_acl(self):
        self.assertEqual(len(INDEX_KEYS),28)
        with tempfile.TemporaryDirectory() as d:
            f=CognitiveFabric(Path(d)/"fabric.sqlite3")
            f.register("research","research",["analyze"],"write_proposed")
            f.register("engineer","engineering",["read"])
            a=f.publish("research","repo/notes","commit1","innovation_index",{"idea":"test"})
            self.assertEqual(a,f.publish("research","repo/notes","commit1","innovation_index",{"idea":"test"}))
            self.assertEqual(len(f.recall("research")),1)
            self.assertEqual(f.recall("engineer"),[])
            f.grant("research","engineer",a)
            self.assertEqual(f.recall("engineer")[0]["state"],"PROPOSED")
            self.assertTrue(f.verify())
            f.close()
            g=CognitiveFabric(Path(d)/"fabric.sqlite3")
            self.assertEqual(len(g.recall("engineer")),1)
            g.close()

    def test_fail_closed_writes(self):
        with tempfile.TemporaryDirectory() as d:
            f=CognitiveFabric(Path(d)/"fabric.sqlite3")
            f.register("reader","knowledge",["read"])
            with self.assertRaises(PermissionError):
                f.publish("reader","x","c","source_index",{"x":1})
            f.register("writer","knowledge",["save"],"write_proposed")
            with self.assertRaises(ValueError):
                f.publish("writer","x","c","not-an-index",{"x":1})
            with self.assertRaises(PermissionError):
                f.recall("unknown")
            f.close()

    def test_version_conflict_and_grant(self):
        with tempfile.TemporaryDirectory() as d:
            f=CognitiveFabric(Path(d)/"fabric.sqlite3")
            f.register("a","knowledge",["save"],"write_proposed")
            f.register("b","knowledge",["read"])
            with self.assertRaises(ValueError):
                f.register("a","finance",["save"],"write_proposed")
            item=f.publish("a","s","v","evidence_index",{"x":1})
            with self.assertRaises(PermissionError):
                f.grant("b","a",item)
            self.assertTrue(f.verify())
            f.close()
if __name__=="__main__":
    unittest.main()
