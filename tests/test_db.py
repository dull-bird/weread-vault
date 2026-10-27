from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from weread_vault.db import SCHEMA_VERSION, _BOOK_EXTRA_COLUMNS, _THOUGHT_EXTRA_COLUMNS, connect, initialize


class MigrationTests(unittest.TestCase):
    def test_initialize_adds_metadata_columns_to_legacy_db_without_losing_data(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        db_path = Path(tmp.name) / "legacy.db"

        # Simulate a legacy database: books and thoughts tables missing the new columns.
        legacy = sqlite3.connect(db_path)
        legacy.execute(
            "CREATE TABLE books (book_id TEXT PRIMARY KEY, title TEXT, sort INTEGER, synced_at INTEGER NOT NULL)"
        )
        legacy.execute(
            """CREATE TABLE thoughts (
              review_id TEXT PRIMARY KEY,
              book_id TEXT NOT NULL,
              chapter_uid INTEGER,
              chapter_name TEXT,
              content TEXT,
              star INTEGER,
              text_range TEXT,
              is_book_review INTEGER NOT NULL DEFAULT 0,
              create_time INTEGER,
              updated_at INTEGER NOT NULL
            )"""
        )
        legacy.execute("INSERT INTO books(book_id, title, sort, synced_at) VALUES('b1', '旧书', 1, 0)")
        legacy.execute(
            "INSERT INTO thoughts(review_id, book_id, content, updated_at) VALUES('r1', 'b1', '旧想法', 0)"
        )
        legacy.commit()
        legacy.close()

        initialize(db_path)  # should ALTER in the new columns idempotently

        with connect(db_path) as conn:
            columns = {row["name"] for row in conn.execute("PRAGMA table_info(books)")}
            for name in _BOOK_EXTRA_COLUMNS:
                self.assertIn(name, columns)
            thought_cols = {row["name"] for row in conn.execute("PRAGMA table_info(thoughts)")}
            for name in _THOUGHT_EXTRA_COLUMNS:
                self.assertIn(name, thought_cols)
            row = conn.execute("SELECT title, rating FROM books WHERE book_id='b1'").fetchone()
            self.assertEqual(row["title"], "旧书")  # existing data preserved
            self.assertIsNone(row["rating"])  # new column defaults to NULL
            trow = conn.execute("SELECT content, abstract, chapter_idx FROM thoughts WHERE review_id='r1'").fetchone()
            self.assertEqual(trow["content"], "旧想法")
            self.assertIsNone(trow["abstract"])
            self.assertIsNone(trow["chapter_idx"])
            ver = conn.execute("SELECT max(version) FROM schema_migrations").fetchone()[0]
            self.assertEqual(ver, SCHEMA_VERSION)
            tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            self.assertIn("obsidian_exported", tables)

        initialize(db_path)  # second run must not error (idempotent)


if __name__ == "__main__":
    unittest.main()
