import tempfile
import unittest
from pathlib import Path
from vxruntime.knowledge_graph import KnowledgeGraph


class KnowledgeGraphTests(unittest.TestCase):
    def test_provenance_dedup_conflict_and_reopen(self):
        with tempfile.TemporaryDirectory() as d:
            db = Path(d) / "graph.db"
            g = KnowledgeGraph(db)
            n = g.add_node("github","file","src/a.py","commit1",{"name":"a"})
            self.assertEqual(n,g.add_node("github","file","src/a.py","commit1",{"name":"a"}))
            with self.assertRaises(ValueError):
                g.add_node("github","file","src/a.py","commit1",{"name":"b"})
            m = g.add_node("obsidian","note","notes/a.md","commit1",{"title":"a"})
            edge = g.add_edge(n,m,"documents","commit1:note-link")
            self.assertEqual(edge,g.add_edge(n,m,"documents","commit1:note-link"))
            self.assertEqual(g.neighbors(n)[0]["state"],"PROPOSED")
            self.assertTrue(g.verify())
            g.close()
            h = KnowledgeGraph(db)
            self.assertEqual(len(h.neighbors(n)),1)
            self.assertTrue(h.verify())
            h.close()


if __name__ == "__main__":
    unittest.main()
