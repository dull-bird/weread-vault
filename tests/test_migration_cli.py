from __future__ import annotations

import io
import sqlite3
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from weread_vault.cli import main


class ReadCommandsMigrateOldDatabaseTests(unittest.TestCase):
    def test_query_on_pre_v6_database_sees_book_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "old.db"
            conn = sqlite3.connect(db)
            conn.executescript(
                """CREATE TABLE books (book_id TEXT PRIMARY KEY, title TEXT, author TEXT,
                total_notes INTEGER NOT NULL DEFAULT 0, reading_progress INTEGER, finished INTEGER,
                sort INTEGER, synced_at INTEGER NOT NULL);
                INSERT INTO books(book_id,title,reading_progress,synced_at) VALUES ('1','在读书',40,0);
                INSERT INTO books(book_id,title,finished,synced_at) VALUES ('2','读完书',1,0);"""
            )
            conn.commit()
            conn.close()
            out = io.StringIO()
            with redirect_stdout(out):
                main(["--db", str(db), "query", "SELECT book_id,status FROM book_status ORDER BY book_id"])
            text = out.getvalue()
            self.assertIn("在读", text)
            self.assertIn("已读", text)


if __name__ == "__main__":
    unittest.main()
