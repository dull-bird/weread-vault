from __future__ import annotations

import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


SCHEMA_VERSION = 7

# Columns added after v1 (rich /book/info metadata). Added idempotently to existing
# databases via PRAGMA table_info so upgrading never drops data.
_BOOK_EXTRA_COLUMNS = {
    "rating": "REAL", "rating_count": "INTEGER", "word_count": "INTEGER",
    "publisher": "TEXT", "isbn": "TEXT", "translator": "TEXT",
    # 1 = currently on the main bookshelf, 0 = kept only because archived / has notes. Set during sync.
    "on_shelf": "INTEGER",
    "reader_link": "TEXT", "deep_link": "TEXT",
    "progress": "INTEGER", "finish_time": "INTEGER", "reading_seconds": "INTEGER",
    "read_update_time": "INTEGER", "progress_synced_at": "INTEGER",
}

_THOUGHT_EXTRA_COLUMNS = {
    "abstract": "TEXT",
    "chapter_idx": "INTEGER",
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_migrations (
  version INTEGER PRIMARY KEY,
  applied_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS books (
  book_id TEXT PRIMARY KEY,
  title TEXT,
  author TEXT,
  cover TEXT,
  intro TEXT,
  category TEXT,
  publish_time TEXT,
  review_count INTEGER NOT NULL DEFAULT 0,
  note_count INTEGER NOT NULL DEFAULT 0,
  bookmark_count INTEGER NOT NULL DEFAULT 0,
  total_notes INTEGER NOT NULL DEFAULT 0,
  reading_progress INTEGER,
  marked_status INTEGER,
  finished INTEGER,
  sort INTEGER,
  notes_synced_sort INTEGER,
  rating REAL,
  rating_count INTEGER,
  word_count INTEGER,
  publisher TEXT,
  isbn TEXT,
  translator TEXT,
  on_shelf INTEGER,
  reader_link TEXT,
  deep_link TEXT,
  progress INTEGER,
  finish_time INTEGER,
  reading_seconds INTEGER,
  read_update_time INTEGER,
  progress_synced_at INTEGER,
  synced_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS highlights (
  bookmark_id TEXT PRIMARY KEY,
  book_id TEXT NOT NULL REFERENCES books(book_id) ON DELETE CASCADE,
  chapter_uid INTEGER,
  chapter_title TEXT,
  mark_text TEXT,
  text_range TEXT,
  color_style INTEGER,
  create_time INTEGER,
  updated_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS thoughts (
  review_id TEXT PRIMARY KEY,
  book_id TEXT NOT NULL REFERENCES books(book_id) ON DELETE CASCADE,
  chapter_uid INTEGER,
  chapter_idx INTEGER,
  chapter_name TEXT,
  content TEXT,
  abstract TEXT,
  star INTEGER,
  text_range TEXT,
  is_book_review INTEGER NOT NULL DEFAULT 0,
  create_time INTEGER,
  updated_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS reading_stats (
  id INTEGER PRIMARY KEY,
  mode TEXT NOT NULL,
  base_time INTEGER NOT NULL DEFAULT 0,
  payload TEXT NOT NULL,
  fetched_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS sync_runs (
  id INTEGER PRIMARY KEY,
  started_at INTEGER NOT NULL,
  completed_at INTEGER,
  status TEXT NOT NULL,
  scope TEXT NOT NULL,
  detail TEXT
);
CREATE TABLE IF NOT EXISTS sync_state (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  updated_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS popular_highlights (
  book_id TEXT NOT NULL REFERENCES books(book_id) ON DELETE CASCADE,
  chapter_uid INTEGER,
  chapter_title TEXT,
  mark_text TEXT,
  text_range TEXT,
  count INTEGER,
  synced_at INTEGER NOT NULL,
  PRIMARY KEY (book_id, text_range)
);
CREATE TABLE IF NOT EXISTS obsidian_exported (
  book_id TEXT NOT NULL,
  item_id TEXT NOT NULL,
  exported_at INTEGER NOT NULL,
  PRIMARY KEY (book_id, item_id)
);
CREATE INDEX IF NOT EXISTS idx_pop_book ON popular_highlights(book_id);
CREATE INDEX IF NOT EXISTS idx_books_sort ON books(sort DESC);
CREATE INDEX IF NOT EXISTS idx_highlights_book ON highlights(book_id);
CREATE INDEX IF NOT EXISTS idx_thoughts_book ON thoughts(book_id);
CREATE INDEX IF NOT EXISTS idx_stats_mode_time ON reading_stats(mode, fetched_at DESC);
"""


@contextmanager
def connect(path: Path) -> Iterator[sqlite3.Connection]:
    """Open a vault connection as a context manager: commit on success, roll back on
    error, and always close. Closing matters on Windows, where a still-open connection
    keeps a lock on the db file (and its WAL sidecars) and blocks deletion."""
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 5000")
    try:
        yield conn
        conn.commit()
    except BaseException:
        conn.rollback()
        raise
    finally:
        conn.close()


BOOK_STATUS_VIEW_SQL = """
DROP VIEW IF EXISTS book_status;
CREATE VIEW book_status AS
SELECT
  book_id,
  title,
  author,
  COALESCE(progress, reading_progress) AS progress,
  reading_seconds,
  finish_time,
  read_update_time,
  CASE
    WHEN finished = 1 OR COALESCE(progress, reading_progress) = 100 THEN '已读'
    WHEN COALESCE(progress, reading_progress) BETWEEN 1 AND 99 THEN '在读'
    ELSE '未读'
  END AS status
FROM books;
"""


def _ensure_columns(conn: sqlite3.Connection) -> None:
    book_cols = {"author": "TEXT", "finished": "INTEGER", **_BOOK_EXTRA_COLUMNS}
    for table, extra in (("books", book_cols), ("thoughts", _THOUGHT_EXTRA_COLUMNS)):
        existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}
        for name, sqltype in extra.items():
            if name not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {sqltype}")  # name/type are internal constants


def initialize(path: Path) -> None:
    with connect(path) as conn:
        conn.executescript(SCHEMA)
        _ensure_columns(conn)
        conn.executescript(BOOK_STATUS_VIEW_SQL)
        conn.execute(
            "INSERT OR IGNORE INTO schema_migrations(version, applied_at) VALUES (?, ?)",
            (SCHEMA_VERSION, int(time.time())),
        )


def set_state(conn: sqlite3.Connection, key: str, value: str) -> None:
    now = int(time.time())
    updated = conn.execute(
        "UPDATE sync_state SET value=?, updated_at=? WHERE key=?", (value, now, key)
    )
    if updated.rowcount == 0:
        conn.execute("INSERT INTO sync_state(key, value, updated_at) VALUES (?, ?, ?)", (key, value, now))


def get_state(conn: sqlite3.Connection, key: str) -> str | None:
    row = conn.execute("SELECT value FROM sync_state WHERE key=?", (key,)).fetchone()
    return row["value"] if row else None


def summary(conn: sqlite3.Connection) -> dict[str, int | str | None]:
    values = dict(
        conn.execute(
            """SELECT
              (SELECT count(*) FROM books WHERE book_id NOT LIKE 'MP_%') AS books,
              (SELECT count(*) FROM highlights) AS highlights,
              (SELECT count(*) FROM thoughts) AS thoughts,
              (SELECT max(completed_at) FROM sync_runs WHERE status='success') AS last_success,
              (SELECT max(completed_at) FROM sync_runs WHERE status='failed') AS last_failure"""
        ).fetchone()
    )
    return values
