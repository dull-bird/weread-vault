from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from weread_vault import cli
from weread_vault.db import connect, initialize
from weread_vault.export import export_markdown, export_obsidian
from weread_vault.paper import import_paper_books, parse_paper_notes
from weread_vault.sync import SyncService
from tests.test_sync import FakeGateway


SAMPLE_TEXT = """
书名: 原则
作者: 瑞·达利欧
ISBN: 9787508684031      (可选)

p.12
> 划线原文，可多行，每行以 > 开头
> 第二行划线原文
想法: 我的想法，可多行，直到空行
第二行想法

P15
想法：只有想法没有划线（中文冒号）

第18页
> 第18页的划线
💭 emoji 开头的想法

> 没有页码的划线

书名：置身事内
作者：兰小欢

p.5
> 地方政府与经济发展
"""


class PaperImportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "vault.db"
        initialize(self.db_path)

    def tearDown(self):
        self.tmp.cleanup()

    def _run_cli(self, argv: list[str], stdin_text: str | None = None) -> str:
        out = io.StringIO()
        with redirect_stdout(out):
            if stdin_text is not None:
                with mock.patch("sys.stdin", io.StringIO(stdin_text)):
                    cli.main(argv)
            else:
                cli.main(argv)
        return out.getvalue()

    def test_parse_various_formats_and_multiple_books(self):
        books = parse_paper_notes(SAMPLE_TEXT)
        self.assertEqual(len(books), 2)
        b1, b2 = books[0], books[1]
        self.assertEqual(b1["title"], "原则")
        self.assertEqual(b1["author"], "瑞·达利欧")
        self.assertEqual(b1["isbn"], "9787508684031")
        self.assertTrue(b1["book_id"].startswith("PAPER_"))
        self.assertEqual(len(b1["notes"]), 4)

        self.assertEqual(b1["notes"][0]["page"], "12")
        self.assertEqual(b1["notes"][0]["highlight"], "划线原文，可多行，每行以 > 开头\n第二行划线原文")
        self.assertEqual(b1["notes"][0]["thought"], "我的想法，可多行，直到空行\n第二行想法")
        self.assertTrue(b1["notes"][0]["bookmark_id"].startswith("paper:"))
        self.assertTrue(b1["notes"][0]["review_id"].startswith("paper:"))

        self.assertEqual(b1["notes"][1]["page"], "15")
        self.assertIsNone(b1["notes"][1]["highlight"])
        self.assertEqual(b1["notes"][1]["thought"], "只有想法没有划线（中文冒号）")

        self.assertEqual(b1["notes"][2]["page"], "18")
        self.assertEqual(b1["notes"][2]["highlight"], "第18页的划线")
        self.assertEqual(b1["notes"][2]["thought"], "emoji 开头的想法")

        self.assertIsNone(b1["notes"][3]["page"])
        self.assertEqual(b1["notes"][3]["highlight"], "没有页码的划线")
        self.assertIsNone(b1["notes"][3]["thought"])

        self.assertEqual(b2["title"], "置身事内")
        self.assertEqual(b2["author"], "兰小欢")
        self.assertEqual(len(b2["notes"]), 1)
        self.assertEqual(b2["notes"][0]["page"], "5")

    def test_idempotent_import_and_status_count(self):
        parsed = parse_paper_notes(SAMPLE_TEXT)
        with connect(self.db_path) as conn:
            import_paper_books(conn, parsed)
            books_count_1 = conn.execute("SELECT count(*) FROM books WHERE source='paper'").fetchone()[0]
            hl_count_1 = conn.execute("SELECT count(*) FROM highlights WHERE source='paper'").fetchone()[0]
            th_count_1 = conn.execute("SELECT count(*) FROM thoughts WHERE source='paper'").fetchone()[0]
            self.assertEqual(books_count_1, 2)
            self.assertEqual(hl_count_1, 4)  # 3 in 原则 + 1 in 置身事内
            self.assertEqual(th_count_1, 3)  # 3 in 原则

            # 同一段有划线和想法时，想法的 abstract = 划线
            row_th = conn.execute(
                "SELECT content, abstract, page, source FROM thoughts WHERE page='12'"
            ).fetchone()
            self.assertEqual(row_th["abstract"], "划线原文，可多行，每行以 > 开头\n第二行划线原文")
            self.assertEqual(row_th["source"], "paper")

            # 再次导入完全相同内容 → 幂等，计数不变
            import_paper_books(conn, parsed)
            self.assertEqual(conn.execute("SELECT count(*) FROM books WHERE source='paper'").fetchone()[0], books_count_1)
            self.assertEqual(conn.execute("SELECT count(*) FROM highlights WHERE source='paper'").fetchone()[0], hl_count_1)
            self.assertEqual(conn.execute("SELECT count(*) FROM thoughts WHERE source='paper'").fetchone()[0], th_count_1)
            b1_row = conn.execute("SELECT bookmark_count, review_count, total_notes FROM books WHERE title='原则'").fetchone()
            self.assertEqual(b1_row["bookmark_count"], 3)
            self.assertEqual(b1_row["review_count"], 3)
            self.assertEqual(b1_row["total_notes"], 6)

        status_out = self._run_cli(["--db", str(self.db_path), "status"])
        self.assertIn("纸质书 2 本", status_out)

    def test_cli_stdin_and_file_and_dry_run(self):
        # 1) --dry-run via stdin does not write to DB
        dry_out = self._run_cli(["--db", str(self.db_path), "import-paper", "--dry-run"], stdin_text=SAMPLE_TEXT)
        self.assertIn("原则", dry_out)
        self.assertIn("dry-run", dry_out)
        with connect(self.db_path) as conn:
            self.assertEqual(conn.execute("SELECT count(*) FROM books").fetchone()[0], 0)

        # 2) Import via stdin (`-`)
        imp_out = self._run_cli(["--db", str(self.db_path), "import-paper", "-"], stdin_text=SAMPLE_TEXT)
        self.assertIn("已导入纸质书 2 本", imp_out)
        with connect(self.db_path) as conn:
            self.assertEqual(conn.execute("SELECT count(*) FROM books WHERE source='paper'").fetchone()[0], 2)

        # 3) Import via file path
        note_file = Path(self.tmp.name) / "notes.md"
        note_file.write_text(SAMPLE_TEXT, encoding="utf-8")
        imp_out2 = self._run_cli(["--db", str(self.db_path), "import-paper", str(note_file)])
        self.assertIn("已导入纸质书 2 本", imp_out2)

    def test_sync_never_deletes_paper_books_or_notes(self):
        parsed = parse_paper_notes(SAMPLE_TEXT)
        with connect(self.db_path) as conn:
            import_paper_books(conn, parsed)
            # Run a full mock sync (shelf + books + reconcile + progress + notes + stats + popular)
            SyncService(conn, FakeGateway(), report=lambda _: None).all(full_notes=True)
            paper_books = conn.execute("SELECT count(*) FROM books WHERE source='paper'").fetchone()[0]
            paper_hl = conn.execute("SELECT count(*) FROM highlights WHERE source='paper'").fetchone()[0]
            paper_th = conn.execute("SELECT count(*) FROM thoughts WHERE source='paper'").fetchone()[0]
            self.assertEqual(paper_books, 2)
            self.assertEqual(paper_hl, 4)
            self.assertEqual(paper_th, 3)

    def test_export_markdown_and_obsidian_include_paper_books(self):
        parsed = parse_paper_notes(SAMPLE_TEXT)
        md_dir = Path(self.tmp.name) / "md"
        obs_dir = Path(self.tmp.name) / "obs"
        with connect(self.db_path) as conn:
            import_paper_books(conn, parsed)
            md_count = export_markdown(conn, md_dir)
            obs_res = export_obsidian(conn, obs_dir)
            self.assertEqual(md_count, 2)
            self.assertEqual(obs_res.created, 2)

        md_text = (md_dir / "原则.md").read_text(encoding="utf-8")
        self.assertIn('source: "纸质书"', md_text)
        self.assertIn("地方政府与经济发展", (md_dir / "置身事内.md").read_text(encoding="utf-8"))

        obs_text = (obs_dir / "原则.md").read_text(encoding="utf-8")
        self.assertIn('source: "纸质书"', obs_text)
        self.assertIn('isbn: "9787508684031"', obs_text)
        self.assertIn("划线原文，可多行，每行以 > 开头", obs_text)
        self.assertIn("💭 我的想法，可多行，直到空行", obs_text)


if __name__ == "__main__":
    unittest.main()
