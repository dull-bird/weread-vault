from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from weread_vault import cli
from weread_vault.db import connect, initialize
from weread_vault.paper import import_paper_books, parse_paper_notes
from weread_vault.review import run_review, select_review_items


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "vault.db"
        initialize(self.db_path)
        with connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO books(book_id, title, author, total_notes, reader_link, sort, synced_at)
                VALUES('b1', '三体', '刘慈欣', 3, 'https://weread.qq.com/web/reader/r1', 100, 0)"""
            )
            conn.execute(
                """INSERT INTO highlights(bookmark_id, book_id, chapter_uid, chapter_title, mark_text, text_range, create_time, updated_at)
                VALUES('m1', 'b1', 1, '第一章', '给岁月以文明', '1-10', 1, 0)"""
            )
            conn.execute(
                """INSERT INTO highlights(bookmark_id, book_id, chapter_uid, chapter_title, mark_text, text_range, create_time, updated_at)
                VALUES('m2', 'b1', 2, '第二章', '不要回答', '20-30', 2, 0)"""
            )
            conn.execute(
                """INSERT INTO thoughts(review_id, book_id, chapter_uid, chapter_name, content, abstract, text_range, is_book_review, create_time, updated_at)
                VALUES('t1', 'b1', 3, '第三章', '黑暗森林法则的推演', '宇宙就是一座黑暗森林', '40-50', 0, 3, 0)"""
            )
            # Also import a paper book
            import_paper_books(
                conn,
                parse_paper_notes(
                    "书名: 原则\n作者: 瑞·达利欧\n\np.12\n> 痛苦+反思=进步\n"
                ),
            )

    def tearDown(self):
        self.tmp.cleanup()

    def _run_cli(self, argv: list[str]) -> str:
        out = io.StringIO()
        with redirect_stdout(out):
            cli.main(argv)
        return out.getvalue()

    def test_selects_n_items_and_no_repeat_on_same_day(self):
        now = 1_700_000_000
        with connect(self.db_path) as conn:
            items1 = select_review_items(conn, n=2, seed=42, now=now)
            self.assertEqual(len(items1), 2)
            ids1 = {(x["item_type"], x["item_id"]) for x in items1}

            # 同一天再次运行：已展示的条目 due_at 已推后到 +1 天，不会重复推同一条
            items2 = select_review_items(conn, n=2, seed=42, now=now + 60)
            self.assertEqual(len(items2), 2)
            ids2 = {(x["item_type"], x["item_id"]) for x in items2}
            self.assertTrue(ids1.isdisjoint(ids2))

            # 全部 4 条都已展示且未到期 → 同日第 3 次返回空
            items3 = select_review_items(conn, n=2, seed=42, now=now + 120)
            self.assertEqual(items3, [])

    def test_due_items_prioritized_in_due_at_order_and_intervals_progress(self):
        now = 1_700_000_000
        with connect(self.db_path) as conn:
            # 预设两条已到期记录：t1 (due_at=now-200) 比 m2 (due_at=now-100) 更早到期
            conn.execute(
                """INSERT INTO review_log(item_type, item_id, shown_count, interval_days, last_shown, due_at)
                VALUES('Highlight_unused', 'x', 1, 1, 0, ?)""",
                (now - 500,),
            )
            conn.execute(
                """INSERT INTO review_log(item_type, item_id, shown_count, interval_days, last_shown, due_at)
                VALUES('thought', 't1', 1, 1, ?, ?)""",
                (now - 86600, now - 200),
            )
            conn.execute(
                """INSERT INTO review_log(item_type, item_id, shown_count, interval_days, last_shown, due_at)
                VALUES('highlight', 'm2', 2, 3, ?, ?)""",
                (now - 259300, now - 100),
            )

            items = select_review_items(conn, n=3, seed=7, now=now)
            self.assertEqual(len(items), 3)
            # 前两条必然是按 due_at 升序排列的已到期条目 t1, m2；第三条从从未展示过的里补
            self.assertEqual(items[0]["item_id"], "t1")
            self.assertEqual(items[1]["item_id"], "m2")
            self.assertIn(items[2]["item_id"], {"m1", conn.execute("SELECT bookmark_id FROM highlights WHERE source='paper'").fetchone()[0]})

            # 检查间隔递增：1, 3, 7, 14, 30, 60, 120, 180（封顶 180）
            row_t1 = conn.execute("SELECT shown_count, interval_days, due_at FROM review_log WHERE item_type='thought' AND item_id='t1'").fetchone()
            self.assertEqual(row_t1["shown_count"], 2)
            self.assertEqual(row_t1["interval_days"], 3)
            self.assertEqual(row_t1["due_at"], now + 3 * 86400)

            row_m2 = conn.execute("SELECT shown_count, interval_days, due_at FROM review_log WHERE item_type='highlight' AND item_id='m2'").fetchone()
            self.assertEqual(row_m2["shown_count"], 3)
            self.assertEqual(row_m2["interval_days"], 7)
            self.assertEqual(row_m2["due_at"], now + 7 * 86400)

            # 测试封顶 180 天
            conn.execute("UPDATE review_log SET shown_count=10, due_at=? WHERE item_type='thought' AND item_id='t1'", (now - 10,))
            select_review_items(conn, n=1, now=now)
            capped = conn.execute("SELECT shown_count, interval_days FROM review_log WHERE item_type='thought' AND item_id='t1'").fetchone()
            self.assertEqual(capped["shown_count"], 11)
            self.assertEqual(capped["interval_days"], 180)

    def test_dry_run_does_not_write_review_log_and_seed_is_reproducible(self):
        with connect(self.db_path) as conn:
            md1 = run_review(conn, n=3, dry_run=True, seed=123)
            md2 = run_review(conn, n=3, dry_run=True, seed=123)
            self.assertEqual(md1, md2)
            count = conn.execute("SELECT count(*) FROM review_log").fetchone()[0]
            self.assertEqual(count, 0)

    def test_append_creates_and_appends_without_overwriting_and_book_filter(self):
        review_file = Path(self.tmp.name) / "daily-review.md"
        review_file.write_text("# 已有笔记标题\n\n原始手写内容。\n", encoding="utf-8")

        self._run_cli(["--db", str(self.db_path), "review", "-n", "2", "--book", "三体", "--append", str(review_file)])
        text1 = review_file.read_text(encoding="utf-8")
        self.assertIn("# 已有笔记标题\n\n原始手写内容。", text1)
        self.assertIn("## 每日回顾 ", text1)
        self.assertIn("—— 《三体》", text1)
        self.assertIn("[打开阅读](https://weread.qq.com/web/reader/r1)", text1)
        self.assertNotIn("《原则》", text1)

        # 再追加一次纸质书《原则》
        self._run_cli(["--db", str(self.db_path), "review", "-n", "1", "--book", "原则", "--append", str(review_file)])
        text2 = review_file.read_text(encoding="utf-8")
        self.assertIn("# 已有笔记标题\n\n原始手写内容。", text2)
        self.assertIn("—— 《三体》", text2)
        self.assertIn("—— 《原则》 p.12", text2)
        self.assertEqual(text2.count("## 每日回顾 "), 2)


if __name__ == "__main__":
    unittest.main()
