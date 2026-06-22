from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from weread_vault.db import connect, initialize
from weread_vault.export import export_markdown


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "vault.db"
        self.out = Path(self.tmp.name) / "md"
        initialize(self.db_path)
        with connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO books(book_id, title, author, category, total_notes, reading_progress, sort, synced_at)"
                " VALUES('book-1', 'Test Book', 'Author', '文学-小说', 1, 10, 99, 0)"
            )
            conn.execute(
                "INSERT INTO highlights(bookmark_id, book_id, chapter_uid, chapter_title, mark_text,"
                " text_range, create_time, updated_at) VALUES('m1','book-1',1,'Chapter','A highlight','1',1,0)"
            )

    def tearDown(self):
        self.tmp.cleanup()

    @property
    def md_path(self) -> Path:
        return self.out / "Test Book.md"

    def test_first_export_writes_then_skips_when_unchanged(self):
        with connect(self.db_path) as conn:
            self.assertEqual(export_markdown(conn, self.out), 1)
            mtime = self.md_path.stat().st_mtime_ns
            # 内容无变化 → 跳过，篇数 0，且 mtime 不变（不触发下游重新索引）
            self.assertEqual(export_markdown(conn, self.out), 0)
            self.assertEqual(self.md_path.stat().st_mtime_ns, mtime)

    def test_user_frontmatter_is_preserved_and_still_skipped(self):
        with connect(self.db_path) as conn:
            export_markdown(conn, self.out)
            text = self.md_path.read_text(encoding="utf-8")
            # 用户在 Obsidian 里手加一个属性
            self.md_path.write_text(text.replace("---\n\n# ", "rating: 5\n---\n\n# ", 1), encoding="utf-8")
            # 再次导出：保留用户字段，且因渲染结果与磁盘一致而跳过
            self.assertEqual(export_markdown(conn, self.out), 0)
            self.assertIn("rating: 5", self.md_path.read_text(encoding="utf-8"))
            # 但脚本管理字段仍以微信读书为准
            self.assertIn('book_id: "book-1"', self.md_path.read_text(encoding="utf-8"))

    def test_category_is_managed(self):
        with connect(self.db_path) as conn:
            export_markdown(conn, self.out)
            # category 来自微信读书，是受管字段而非用户字段
            self.assertIn('category: "文学-小说"', self.md_path.read_text(encoding="utf-8"))
            # 用户即便手改了 category，下次也以微信读书为准（不被当作用户字段保留）
            text = self.md_path.read_text(encoding="utf-8")
            self.md_path.write_text(text.replace('category: "文学-小说"', 'category: "瞎写的"'), encoding="utf-8")
            export_markdown(conn, self.out, force=True)
            result = self.md_path.read_text(encoding="utf-8")
            self.assertIn('category: "文学-小说"', result)
            self.assertNotIn("瞎写的", result)

    def test_content_change_triggers_rewrite(self):
        with connect(self.db_path) as conn:
            export_markdown(conn, self.out)
            conn.execute("UPDATE highlights SET mark_text='Edited' WHERE bookmark_id='m1'")
            self.assertEqual(export_markdown(conn, self.out), 1)
            self.assertIn("Edited", self.md_path.read_text(encoding="utf-8"))

    def test_force_rewrites_even_when_unchanged(self):
        with connect(self.db_path) as conn:
            export_markdown(conn, self.out)
            self.assertEqual(export_markdown(conn, self.out, force=True), 1)


if __name__ == "__main__":
    unittest.main()
