from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from weread_vault.db import _BOOK_EXTRA_COLUMNS, connect, initialize


class MigrationTests(unittest.TestCase):
    def test_initialize_adds_metadata_columns_to_legacy_db_without_losing_data(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        db_path = Path(tmp.name) / "legacy.db"

        # Simulate a v1 database: a books table missing the new metadata columns.
        legacy = sqlite3.connect(db_path)
        legacy.execute(
            "CREATE TABLE books (book_id TEXT PRIMARY KEY, title TEXT, sort INTEGER, synced_at INTEGER NOT NULL)"
        )
        legacy.execute("INSERT INTO books(book_id, title, sort, synced_at) VALUES('b1', '旧书', 1, 0)")
        legacy.commit()
        legacy.close()

        initialize(db_path)  # should ALTER in the new columns idempotently

        with connect(db_path) as conn:
            columns = {row["name"] for row in conn.execute("PRAGMA table_info(books)")}
            for name in _BOOK_EXTRA_COLUMNS:
                self.assertIn(name, columns)
            row = conn.execute("SELECT title, rating FROM books WHERE book_id='b1'").fetchone()
            self.assertEqual(row["title"], "旧书")  # existing data preserved
            self.assertIsNone(row["rating"])  # new column defaults to NULL

        initialize(db_path)  # second run must not error (idempotent)


if __name__ == "__main__":
    unittest.main()
