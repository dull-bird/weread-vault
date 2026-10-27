from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from weread_vault.db import connect, initialize
from weread_vault.export import BEGIN_NOTES, END_NOTES, _merge_highlights, export_markdown, export_obsidian


def _row(chapter_uid, title, text, text_range, count=0):
    return {"chapter_uid": chapter_uid, "chapter_title": title, "mark_text": text,
            "text_range": text_range, "count": count}


class MergeTests(unittest.TestCase):
    def test_overlapping_popular_folds_into_own_and_order_by_position(self):
        own = [_row(1, "C1", "我的后半句", "100-150"), _row(1, "C1", "我的前半句", "10-40")]
        popular = [_row(1, "C1", "热门重叠", "120-140", 900), _row(1, "C1", "热门独立", "200-230", 500)]
        merged = _merge_highlights(own, popular)
        entries = merged[1]["entries"]
        # ordered by position: 10-40, 100-150, 200-230
        self.assertEqual([e["text"] for e in entries], ["我的前半句", "我的后半句", "热门独立"])
        # the overlapping popular folded its count into the own highlight, not a separate entry
        self.assertEqual(entries[1]["kind"], "own")
        self.assertEqual(entries[1]["count"], 900)
        self.assertEqual(entries[2]["kind"], "pop")
        self.assertEqual(entries[2]["count"], 500)


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

    def test_thoughts_with_abstract_exported_as_pairs_and_deduplicated_on_same_range(self):
        with connect(self.db_path) as conn:
            # 1) Thought with abstract whose range is NOT in highlights -> paired `> 原文\n💭 想法`
            conn.execute(
                """INSERT INTO thoughts(review_id, book_id, chapter_uid, chapter_name, content, abstract,
                text_range, is_book_review, create_time, updated_at)
                VALUES('t-pair', 'book-1', 1, 'Chapter', '成对想法', '独立原文', '200-220', 0, 10, 10)"""
            )
            # 2) Thought whose range ('1') already appears in highlights -> attached under the highlight, not repeated
            conn.execute(
                """INSERT INTO thoughts(review_id, book_id, chapter_uid, chapter_name, content, abstract,
                text_range, is_book_review, create_time, updated_at)
                VALUES('t-same', 'book-1', 1, 'Chapter', '挂在划线下的想法', 'A highlight', '1', 0, 11, 11)"""
            )
            # 3) Plain chapter thought without abstract -> unchanged format
            conn.execute(
                """INSERT INTO thoughts(review_id, book_id, chapter_uid, chapter_name, content, abstract,
                text_range, is_book_review, create_time, updated_at)
                VALUES('t-plain', 'book-1', 1, 'Chapter', '普通章节点评', NULL, NULL, 0, 12, 12)"""
            )
            export_markdown(conn, self.out, force=True)
            md = self.md_path.read_text(encoding="utf-8")
            self.assertIn("> 独立原文\n💭 成对想法", md)
            self.assertIn("- A highlight\n💭 挂在划线下的想法", md)
            self.assertNotIn("> A highlight", md)
            self.assertIn("- 【Chapter】普通章节点评", md)

    def test_official_reader_and_deep_links_in_markdown_export(self):
        with connect(self.db_path) as conn:
            # 1) Neither reader_link nor deep_link -> no link generated at all
            export_markdown(conn, self.out, force=True)
            md = self.md_path.read_text(encoding="utf-8")
            self.assertNotIn("weread://", md)
            self.assertNotIn("[打开阅读]", md)
            self.assertNotIn("[查看详情]", md)

            # 2) Only deep_link -> [查看详情](deep_link)
            conn.execute("UPDATE books SET deep_link='https://weread.qq.com/web/bookDetail/d1' WHERE book_id='book-1'")
            export_markdown(conn, self.out, force=True)
            md = self.md_path.read_text(encoding="utf-8")
            self.assertIn("[查看详情](https://weread.qq.com/web/bookDetail/d1)", md)
            self.assertNotIn("[打开阅读]", md)

            # 3) Both reader_link and deep_link -> prefers [打开阅读](reader_link)
            conn.execute("UPDATE books SET reader_link='https://weread.qq.com/web/reader/r1' WHERE book_id='book-1'")
            export_markdown(conn, self.out, force=True)
            md = self.md_path.read_text(encoding="utf-8")
            self.assertIn("[打开阅读](https://weread.qq.com/web/reader/r1)", md)
            self.assertNotIn("[查看详情]", md)


class ObsidianExportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "vault.db"
        self.out = Path(self.tmp.name) / "obsidian"
        initialize(self.db_path)
        with connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO books(book_id, title, author, category, cover, isbn, publisher, rating,
                progress, reading_progress, finished, reading_seconds, finish_time, total_notes,
                reader_link, sort, synced_at)
                VALUES('book-1', 'Test Book', 'Author', '文学-小说', 'https://example.com/c.jpg',
                '9787000000001', '某出版社', 880, 100, 100, 1, 7200, 1700000000, 2,
                'https://weread.qq.com/web/reader/r1', 99, 0)"""
            )
            conn.execute(
                """INSERT INTO highlights(bookmark_id, book_id, chapter_uid, chapter_title, mark_text,
                text_range, create_time, updated_at)
                VALUES('m1', 'book-1', 1, '第一章', '第一条划线', '10-20', 1, 0)"""
            )
            conn.execute(
                """INSERT INTO thoughts(review_id, book_id, chapter_uid, chapter_name, content, abstract,
                text_range, is_book_review, create_time, updated_at)
                VALUES('t1', 'book-1', 1, '第一章', '我的想法内容', '划线原文摘要', '30-40', 0, 2, 0)"""
            )

    def tearDown(self):
        self.tmp.cleanup()

    @property
    def md_path(self) -> Path:
        return self.out / "Test Book.md"

    def test_first_export_creates_file_with_managed_frontmatter_and_blocks(self):
        with connect(self.db_path) as conn:
            res = export_obsidian(conn, self.out)
            self.assertEqual(res, 1)
            self.assertEqual(res.created, 1)
            self.assertEqual(res.appended, 0)
            self.assertEqual(res.new_items, 2)
            text = self.md_path.read_text(encoding="utf-8")
            for field in (
                'title: "Test Book"',
                'author: "Author"',
                'book_id: "book-1"',
                'source: "微信读书"',
                'category: "文学-小说"',
                'cover: "https://example.com/c.jpg"',
                'isbn: "9787000000001"',
                'publisher: "某出版社"',
                "rating: 880.0",
                "progress: 100",
                'status: "已读"',
                "reading_hours: 2.0",
                "highlights: 1",
                "thoughts: 1",
                'reader_link: "https://weread.qq.com/web/reader/r1"',
                "updated: ",
                "finish_date: ",
            ):
                self.assertIn(field, text)
            self.assertIn("# Test Book", text)
            self.assertIn("[打开阅读](https://weread.qq.com/web/reader/r1)", text)
            self.assertIn("## 我的笔记", text)
            self.assertIn(BEGIN_NOTES, text)
            self.assertIn(END_NOTES, text)
            self.assertIn("<!-- wv:m1 -->\n> 第一条划线", text)
            self.assertIn("<!-- wv:t1 -->\n> 划线原文摘要\n💭 我的想法内容", text)

    def test_unchanged_skips_write_and_preserves_mtime(self):
        with connect(self.db_path) as conn:
            export_obsidian(conn, self.out)
            mtime = self.md_path.stat().st_mtime_ns
            res2 = export_obsidian(conn, self.out)
            self.assertEqual(res2, 0)
            self.assertEqual(res2.created, 0)
            self.assertEqual(res2.appended, 0)
            self.assertEqual(res2.new_items, 0)
            self.assertEqual(self.md_path.stat().st_mtime_ns, mtime)

    def test_handwritten_outside_and_inside_block_preserved_and_only_new_items_appended(self):
        with connect(self.db_path) as conn:
            export_obsidian(conn, self.out)
            text = self.md_path.read_text(encoding="utf-8")
            # 用户在区块外（## 我的笔记 下、end 标记后）和区块内都加手写文字
            text = text.replace("## 我的笔记\n", "## 我的笔记\n\n这是我在区块外手写的读书总结。\n", 1)
            text = text.replace(
                "> 第一条划线\n",
                "> 第一条划线\n\n这是我在区块内手写的批注。\n",
                1,
            )
            text = text + "\n区块末尾外的尾注。\n"
            self.md_path.write_text(text, encoding="utf-8")

            # 新增一条划线
            conn.execute(
                """INSERT INTO highlights(bookmark_id, book_id, chapter_uid, chapter_title, mark_text,
                text_range, create_time, updated_at)
                VALUES('m2', 'book-1', 2, '第二章', '新增的第二条划线', '50-60', 3, 0)"""
            )
            res = export_obsidian(conn, self.out)
            self.assertEqual(res, 1)
            self.assertEqual(res.created, 0)
            self.assertEqual(res.appended, 1)
            self.assertEqual(res.new_items, 1)

            updated = self.md_path.read_text(encoding="utf-8")
            self.assertIn("这是我在区块外手写的读书总结。", updated)
            self.assertIn("这是我在区块内手写的批注。", updated)
            self.assertIn("区块末尾外的尾注。", updated)
            self.assertIn("### 第二章\n\n<!-- wv:m2 -->\n> 新增的第二条划线", updated)
            self.assertIn("highlights: 2", updated)
            # 原有条目只出现一次
            self.assertEqual(updated.count("<!-- wv:m1 -->"), 1)
            self.assertEqual(updated.count("<!-- wv:t1 -->"), 1)
            self.assertEqual(updated.count("<!-- wv:m2 -->"), 1)

    def test_deleted_item_does_not_return_and_user_frontmatter_preserved(self):
        with connect(self.db_path) as conn:
            export_obsidian(conn, self.out)
            text = self.md_path.read_text(encoding="utf-8")
            # 用户自加 frontmatter 字段，并删掉 m1 条目
            text = text.replace("---\n\n# ", 'my_tag: "精读"\naliases:\n  - 别名\n---\n\n# ', 1)
            text = text.replace("<!-- wv:m1 -->\n> 第一条划线\n\n", "", 1)
            self.md_path.write_text(text, encoding="utf-8")

            # 再次导出（无新条目）：不把被用户删掉的 m1 加回，且无变化不写文件
            mtime = self.md_path.stat().st_mtime_ns
            res = export_obsidian(conn, self.out)
            self.assertEqual(res, 0)
            self.assertEqual(self.md_path.stat().st_mtime_ns, mtime)
            after = self.md_path.read_text(encoding="utf-8")
            self.assertNotIn("<!-- wv:m1 -->", after)
            self.assertNotIn("第一条划线", after)
            self.assertIn('my_tag: "精读"', after)
            self.assertIn("  - 别名", after)

            # 即便之后同步了新条目 m3，已删除的 m1 依然不会回来，用户 frontmatter 依然保留
            conn.execute(
                """INSERT INTO highlights(bookmark_id, book_id, chapter_uid, chapter_title, mark_text,
                text_range, create_time, updated_at)
                VALUES('m3', 'book-1', 1, '第一章', '第三条划线', '70-80', 4, 0)"""
            )
            res2 = export_obsidian(conn, self.out)
            self.assertEqual(res2.appended, 1)
            self.assertEqual(res2.new_items, 1)
            after2 = self.md_path.read_text(encoding="utf-8")
            self.assertNotIn("<!-- wv:m1 -->", after2)
            self.assertIn("<!-- wv:m3 -->", after2)
            self.assertIn('my_tag: "精读"', after2)
            self.assertIn("  - 别名", after2)

    def test_renamed_book_updates_existing_file_by_frontmatter_book_id(self):
        with connect(self.db_path) as conn:
            export_obsidian(conn, self.out)
            conn.execute("UPDATE books SET title='Renamed Book' WHERE book_id='book-1'")
            res = export_obsidian(conn, self.out)
            self.assertEqual(res, 1)
            # 仍在原文件名下更新，不另建 Renamed Book.md
            self.assertTrue(self.md_path.exists())
            self.assertFalse((self.out / "Renamed Book.md").exists())
            self.assertIn('title: "Renamed Book"', self.md_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
