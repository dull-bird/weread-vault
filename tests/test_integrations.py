from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from weread_vault.db import connect, initialize
from weread_vault.integrations import export_flomo, export_notion


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db_path = Path(self.tmp.name) / "vault.db"
        initialize(self.db_path)
        with connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO books(book_id,title,author,category,total_notes,reading_progress,sort,synced_at)"
                " VALUES('b1','三体','刘慈欣','科幻-小说',2,50,99,0)"
            )
            conn.execute(
                "INSERT INTO highlights(bookmark_id,book_id,chapter_uid,chapter_title,mark_text,text_range,create_time,updated_at)"
                " VALUES('h1','b1',1,'第一章','一句划线','0',1,1)"
            )
            conn.execute(
                "INSERT INTO thoughts(review_id,book_id,chapter_uid,chapter_name,content,is_book_review,create_time,updated_at)"
                " VALUES('t1','b1',1,'第一章','一条想法',0,1,1)"
            )
            # A book without notes must be skipped by both exporters.
            conn.execute(
                "INSERT INTO books(book_id,title,author,category,total_notes,reading_progress,sort,synced_at)"
                " VALUES('b2','空书','某人','',0,0,98,0)"
            )

    def test_flomo_sends_one_memo_per_book_with_notes(self):
        calls = []
        with connect(self.db_path) as conn:
            sent = export_flomo(conn, "https://flomoapp.com/iwh/xxx", poster=lambda u, p, h: calls.append((u, p, h)) or {})
        self.assertEqual(sent, 1)
        url, payload, _ = calls[0]
        self.assertEqual(url, "https://flomoapp.com/iwh/xxx")
        self.assertIn("《三体》 刘慈欣", payload["content"])
        self.assertIn("- 一句划线", payload["content"])
        self.assertIn("💭 一条想法", payload["content"])
        self.assertIn("#微信读书", payload["content"])
        self.assertIn("#科幻", payload["content"])

    def test_notion_creates_page_with_auth_and_blocks(self):
        calls = []
        with connect(self.db_path) as conn:
            created = export_notion(conn, "secret_tok", "db123", poster=lambda u, p, h: calls.append((u, p, h)) or {})
        self.assertEqual(created, 1)
        url, payload, headers = calls[0]
        self.assertEqual(url, "https://api.notion.com/v1/pages")
        self.assertEqual(headers["Authorization"], "Bearer secret_tok")
        self.assertEqual(payload["parent"], {"database_id": "db123"})
        self.assertEqual(payload["properties"]["Name"]["title"][0]["text"]["content"], "三体")
        kinds = [block["type"] for block in payload["children"]]
        self.assertIn("heading_2", kinds)
        self.assertIn("quote", kinds)
        self.assertIn("callout", kinds)

    def test_limit_is_respected(self):
        with connect(self.db_path) as conn:
            self.assertEqual(export_flomo(conn, "u", limit=1, poster=lambda *a: {}), 1)


if __name__ == "__main__":
    unittest.main()
