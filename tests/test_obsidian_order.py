from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from weread_vault.db import connect, initialize
from weread_vault.export import export_obsidian


class ObsidianOrderTests(unittest.TestCase):
    def test_numeric_order_and_thought_under_its_highlight(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "v.db"
            initialize(db)
            with connect(db) as conn:
                conn.execute("INSERT INTO books(book_id,title,total_notes,sort,synced_at) VALUES ('b','书',3,1,0)")
                for bid, rng, text in (("h1", "1096-1150", "后面"), ("h2", "914-936", "前面")):
                    conn.execute(
                        "INSERT INTO highlights(bookmark_id,book_id,chapter_uid,chapter_title,mark_text,text_range,updated_at)"
                        " VALUES (?,?,?,?,?,?,0)", (bid, "b", 1, "第一章", text, rng))
                conn.execute(
                    "INSERT INTO thoughts(review_id,book_id,chapter_uid,chapter_name,content,abstract,text_range,updated_at)"
                    " VALUES ('t1','b',1,'第一章','我的想法','前面','914-936',0)")
                export_obsidian(conn, Path(tmp) / "out")
            text = (Path(tmp) / "out" / "书.md").read_text(encoding="utf-8")
            self.assertLess(text.index("> 前面"), text.index("💭 我的想法"))
            self.assertLess(text.index("💭 我的想法"), text.index("> 后面"))
            self.assertEqual(text.count("> 前面"), 1)  # quote not duplicated under the paired thought
            self.assertEqual(text.count("### 第一章"), 1)


if __name__ == "__main__":
    unittest.main()
